# 01-09 流式响应与 SSE：持续发送进度

> 教材状态：已准备。学习位置与练习状态见模块进度。更新：2026-10-22。

## 本章问题、目标与前置

一次批量查询包含多个客户，页面希望先显示“正在查谁”，再逐条显示结果。若等所有工作完成后才 return 一个列表，用户在等待期间看不到进度。本章改为在一个 HTTP 响应里持续发送事件。

读完应能解释 yield 与异步迭代，读懂 SSE 事件边界，处理完成、单项失败和连接中断。前置：[异步任务](05-async-and-tasks.md)、[HTTP](06-http-and-json.md)、[HTTPX 取数与客户端生命周期](08-httpx-and-upstream.md)。约 25–35 分钟，环境沿用 [07 §2](07-fastapi-and-pydantic.md#environment)。固定三项合成查询，不调用真实模型。

## 1. 流式到底改变了什么

普通 JSON 接口在计算完后交出一个完整 JSON 值。流式响应允许服务端边处理边输出响应体，客户端也边接收边处理。一次响应中可以有多个片段，它们不意味着多个 HTTP 请求。

“流式”描述逐步传送；**SSE（Server-Sent Events）** 在 HTTP 响应体里规定文本事件格式，让客户端能区分进度、结果和完成。模型 SDK 也可能逐步产生文本，但模型输出、HTTP 传输和浏览器事件处理是连续的三层工作。当前用客户查询模拟逐步产生的数据，不用模型 SDK 掩盖这几层的区别。

## 2. 用 yield 逐步交出内容

先看与网络无关的最小例子：

```python
def customer_ids():
    yield "C001"  # 交出第一项并暂停，下一次取值从这里继续。
    yield "C002"

for customer_id in customer_ids():
    print(customer_id)
```

包含 yield 的函数调用后返回生成器。for 每次向它取下一项，执行到 yield 时交出这一项并暂停；下次取值从暂停处继续。因此 yield 能多次交出内容，return 则结束本次函数执行。

如果每项内容之间要 await 网络调用，就使用异步生成器：

```python
async def amounts(client):
    for customer_id in ["C001", "C002"]:
        result = await fetch_receivable(client, customer_id)  # 等这一项取数完成。
        yield result  # 每完成一项就交出，不必先等整批完成。

# 放在一个已经运行的 async 函数中：
# async for result in amounts(client):
#     print(result)
```

`async for` 等待异步迭代器的下一项。异步生成器不能直接当作 `await amounts(client)` 求出整个列表；它是一项项产生内容。下面 StreamingResponse 会负责消费生成器，把每次 yield 的文本发送到响应体；不需要你先收集成列表再 return。

## 3. SSE 怎样划分一条事件

响应的 Content-Type 为 `text/event-stream`，文本用 UTF-8。这个事件包含两行，再由空行结束：

```text
event: result
data: {"customer_id":"C001","amount":12800}

```

`event` 是应用约定的事件名，`data` 是文本，本例用 JSON 表达字段。结尾 `\n\n` 很关键；客户端以空行识别一条完整事件。省略 event 时，浏览器通常将它交给默认 message 事件；命名事件则用 addEventListener 对应名称监听。[SSE 格式与浏览器行为](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)可用于速查。

一次网络读取不保证刚好对应一个 yield 或一个事件：网络和服务器可能合并、拆分字节。应按 SSE 的空行边界解析，不能把每个 TCP 片段直接当成完整 JSON。

本例定义四类事件：

| 名称 | 内容与用途 |
| --- | --- |
| progress | 当前准备查询的客户编号 |
| result | 一项成功结果，data 字段保存结果对象 |
| failed | 一项失败的客户编号和说明 |
| done | 本批已处理三项，包含成功与失败 |

done 只表示本批处理结束，不代表每项都查询成功。当前每项不设置最低门槛，C002 应返回金额 0，而非 null。

## 4. 将已有取数函数接进事件流

`app_stream.py` 共用 08 章的 lifespan、客户端和 fetch_receivable。下面是完整服务端逻辑；文件末尾还带一个浏览器演示页，点击按钮即可接收事件。

```python
import asyncio
import json
import logging
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from app_gateway import get_client, lifespan
from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable

app = FastAPI(title="应收进度 SSE", lifespan=lifespan)
logger = logging.getLogger("receivable.stream")



# 一条事件由空行结束；data 内部的内容用 JSON 编码。
def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/events")
async def events(
    request: Request,
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
):
    async def generate():
        try:
            for customer_id in ["C001", "C999", "C002"]:
                # 对端已经离开时，不再开始下一项查询。
                if await request.is_disconnected():
                    return
                # 先交出进度事件，再等待取数，不必等整批完成。
                yield sse("progress", {"customer_id": customer_id})
                await asyncio.sleep(0.2)
                try:
                    result = await fetch_receivable(client, customer_id)
                    # Pydantic 模型先转字典，再由 sse 编码成事件文本。
                    yield sse("result", {"data": result.model_dump() if result else None})
                # 已知单项失败发为事件，继续下一项；不吞掉取消信号。
                except (CustomerNotFoundError, UpstreamError, UpstreamTimeoutError) as error:
                    yield sse("failed", {"customer_id": customer_id, "detail": str(error)})
            # processed 是尝试处理的项数，并不表示三项全部成功。
            yield sse("done", {"processed": 3})
        finally:
            # 正常结束、异常或取消时均收尾；共享客户端由应用关闭。
            logger.info("SSE 查询生成器已结束")

    # 框架逐步读取生成器，持续发送响应体，不先收集成完整列表。
    return StreamingResponse(
        generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )
```

`sse` 将数据字典编码为单行 JSON，再加 event/data 和事件结束空行。`generate` 每轮先发进度，模拟等待 0.2 秒，再调用已有 ERP 客户端。已知单项失败变为 failed，循环继续 C002；没有把无法取数伪装成 0。`StreamingResponse(generate(), ...)` 把生成器交给框架持续消费。

这次 yield 的用途与 [08 章 lifespan](08-httpx-and-upstream.md#3) 不同：这里每次 yield 是响应内容的一部分；lifespan 的 yield 划分启动与停止阶段。两处都利用暂停/恢复机制，但消费它们的对象不同。

### 4.1 已经开始响应后，错误怎样表达

流式响应通常先发送状态与响应头，再消费生成器。开始发送后，不能把同一个响应从 200 改成 404。需要在流开始前拒绝的输入或权限，应在返回 StreamingResponse 前检查；执行中发生的已知单项失败则用流内事件表达。未知代码错误仍应查日志，连接提前结束且没有 done，不能当成本批成功结束。

### 4.2 完成或断开时怎样收尾

本例在每轮开始检查 `request.is_disconnected()`；StreamingResponse 也会在发送/断开过程中结束相关迭代。生成器的 finally 用来统一收尾，本例只有结束日志，没有独立后台任务需要取消。事件里捕获的类型不包含 CancelledError，因此取消信号能继续传播，遵循 05 章的处理方式。

共享 AsyncClient 仍由应用 lifespan 关闭，不能在单次流的 finally 中关闭，否则会影响同一应用的其他请求。如果以后给单条流创建了专属资源，则在那条流的 finally 中释放。

浏览器 EventSource 默认会尝试重连，但本例没有保存事件历史，也未实现 Last-Event-ID 续传。演示页在 done 后主动 close，在网络错误时也 close，让用户手动重开一批，避免将重新执行误认为断点续传。标准 SSE 可携带 id，实际恢复还需要服务端保存并根据编号补发，不能只添加 id 字段就认为完成了恢复。

## 5. 启动、读取与观察

保持 8001 模拟 ERP 运行；8002 与这一章无运行依赖，可以停止。新终端从项目根目录启动：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_stream:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8003 --log-level info
```

在浏览器打开 `http://127.0.0.1:8003/`，点击“开始一批查询”。页面使用原生 EventSource，其关键代码是：

```javascript
// 连接同一服务的 SSE 入口，浏览器负责按事件边界解析文本。
const source = new EventSource('/events');
source.addEventListener('result', event => {
  console.log(JSON.parse(event.data)); // event.data 仍是字符串，先解析 JSON。
});
// 收到业务结束事件后关闭，防止默认重连再次启动一批查询。
source.addEventListener('done', () => source.close());
```

完整页面还监听 progress/failed，并提供停止按钮。页面由同一个 8003 服务提供，`/events` 指向同一服务，避免从教材站 8765 误发请求。原生 EventSource 使用 GET，不方便自定义请求体或任意请求头；复杂 POST 流可用 fetch 读取流，但流解析需要自己负责，当前不另加一套客户端。

终端也能查看事件原文：

```sh
curl -N 'http://127.0.0.1:8003/events'
```

`-N` 关闭 curl 自己的输出缓冲。顺序应为：C001 progress→result(12800)，C999 progress→failed，C002 progress→result(0)，最后 done(processed=3)。总计 7 条事件。停止 8001 后再开始一批，三项各得到 failed，仍会得到 done，因为本批三项都已尝试完成。

若长时间看不到逐步输出，先用 curl -N 区分是否是客户端或代理缓冲；每次只 yield 文本也不保证中间代理立即展示。本机演示不经过反向代理，部署与代理配置放到 02 模块。

## 6. 可选练习

条件：沿用固定客户顺序 C001、C999、C002，不改变单项失败继续执行的规则。

1. 为什么 C999 的事件叫 failed，但 HTTP 状态仍可能为 200？
2. 浏览器接到 done 后不关闭 EventSource，是否就能保证不再发请求？
3. 改成“第一次失败就结束批次”，应修改哪里，done 的 processed 还能固定写 3 吗？

??? note "参考答案与依据"
    1. HTTP 响应已开始，后来的业务状态由事件承载；HTTP 200 不等于每个事件都成功。
    2. 不能保证。服务端结束流后，原生 EventSource 通常会尝试重连。本演示在 done 时 close。
    3. 在单项 except 中发 failed 后结束或退出循环，并用实际处理计数生成终止事件；不能仍宣称处理三项。客户端还需能区分提前结束与正常处理全部项。

## 本章回顾与检查清单

异步生成器逐步产生内容，StreamingResponse 持续发送，SSE 为内容补上事件边界与类型，客户端按事件更新页面，并明确处理完成和断开。

- [ ] 能说明 yield、async for 与流式响应之间怎样连接。
- [ ] 能从空行判断 SSE 事件边界。
- [ ] 能区分 HTTP 状态、单项成功/失败、批次结束和意外断开。

## 阅读中产生的答疑

暂无。网络客户端和取消原理分别回查 08、05，当前只讨论持续输出增加的机制。

## 资料与后续

事件序列、逐步到达、未知客户、上游停止与提前断开均有验证记录。资料核实：2026-10-22。[Python yield](https://docs.python.org/3.12/reference/expressions.html#yield-expressions) · [StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse) · [SSE 格式](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)。当前 FastAPI 也提供 [SSE 专用接口](https://fastapi.tiangolo.com/tutorial/server-sent-events/)，本章使用通用 StreamingResponse 显式展示事件格式，便于理解发送边界。

[上一章：HTTPX](08-httpx-and-upstream.md) · [下一章：WebSocket 与方式选择](10-websocket-and-selection.md) · [返回目录](index.md)
