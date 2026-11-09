# 01-10 WebSocket：双向交互与通信方式选择

> 教材状态：已准备。学习位置与练习状态见模块进度。更新：2026-10-22。

## 本章问题、目标与前置

SSE 适合一次发起后持续接收进度。现在页面希望保持连接，随时发送新的客户编号，并收到对应结果。WebSocket 允许双方在建立的连接上持续发送消息。

读完应能跟踪建立连接、收发消息、关闭与重新连接，解释消息校验与普通 HTTP 输入校验的不同，并在普通 HTTP、SSE 和 WebSocket 之间选择。前置：[接口模型](07-fastapi-and-pydantic.md)、[异步 HTTP 客户端](08-httpx-and-upstream.md)、[持续输出](09-streaming-and-sse.md)。约 25–35 分钟，环境继续使用 [07 §2](07-fastapi-and-pydantic.md#environment)。

## 1. 从“一次请求”走到“连接上的多条消息”

WebSocket 的建立通常从 HTTP 握手开始，接受连接后进入消息通信。地址使用 `ws://`；加密连接用 `wss://`。客户端可以发送 C001、等待结果、再发送 C002，不需要每条查询都重新组织一个 HTTP 请求。

SSE 连接上的事件方向是服务端到客户端；WebSocket 连接上双方均可发送消息。双方能发送不意味着业务代码自动并发。本章服务端每条查询处理完成后才接收下一条消息，先保持消息与结果的顺序对应。

```text
浏览器                 WebSocket 服务 8004       模拟 ERP 8001
  ├── 建立连接 ──────────►│
  ├── JSON 查询 C001 ─────►├── HTTPX 查询 ─────────►│
  │◄──── result 12800 ────┤◄──── JSON 结果 ───────┤
  ├── JSON 查询 C002 ─────►├── HTTPX 查询 ─────────►│
  │◄──── result 0 ────────┤◄──── JSON 结果 ───────┤
  └── quit ──────────────►│── 正常关闭
```

WebSocket 负责浏览器到 8004 的外层通信；8004 到 ERP 仍然用已经写好的 HTTPX，不需要把整条链都换成 WebSocket。

## 2. 定义最小消息约定

客户端发送一条 JSON 文本：

```json
{"customer_id":"C001","min_amount":1000}
```

输入仍按 QueryInput 校验。服务端成功回复 `{"type":"result","data":{"customer_id":"C001","amount":12800}}`；未命中门槛时 data 为 null；客户不存在或已知上游失败回复 `{"type":"failed","detail":"..."}`。本例中一次业务失败不关闭整个连接，用户可以接着查其他客户。

额外约定纯文本 `quit` 表示请求正常关闭，它不参与 JSON 解析。这是本演示的应用消息约定，WebSocket 协议本身并没有规定必须发送 quit。浏览器也可以直接调用 socket.close() 发起关闭。

普通 HTTP 路由可以在请求入口由 FastAPI 自动解析 QueryInput；WebSocket 中的每条消息只是传来的文本，需在消息循环里显式调用模型校验。不能因为连接建立成功，就认为后面的每条 JSON 都符合字段约定。

## 3. 服务端的接收与发送循环

`app_ws.py` 的完整通信逻辑如下，文件末尾另有可直接使用的浏览器页面。客户端资源沿用 08 章 lifespan，输入与结果沿用 07 章模型。

```python
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app_gateway import lifespan
from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable
from models import QueryInput

app = FastAPI(title="应收 WebSocket", lifespan=lifespan)
logger = logging.getLogger("receivable.websocket")


@app.websocket("/ws")
async def query_socket(websocket: WebSocket):
    await websocket.accept()  # 接受连接后，才开始收发业务消息。
    try:
        while True:
            # 本例顺序处理：这一项查完并回复后，才接收下一条。
            text = await websocket.receive_text()
            # quit 是本例约定的正常关闭命令，不参与 JSON 解析。
            if text == "quit":
                await websocket.close(code=1000)
                return
            try:
                # 连接建立不代表消息合法，每条 JSON 都要单独校验。
                query = QueryInput.model_validate_json(text)
            except ValidationError:
                await websocket.send_json({"type": "failed", "detail": "请发送合法的查询 JSON"})
                continue  # 本条输入失败，不关闭连接；仍可继续发合法查询。
            try:
                # 继续复用 08 章的客户端与错误分类，不重复实现取数。
                result = await fetch_receivable(
                    websocket.app.state.erp_client,
                    query.customer_id,
                    min_amount=query.min_amount,
                )
                await websocket.send_json({
                    "type": "result", "data": result.model_dump() if result else None
                })
            # 已建立连接后，业务失败用消息表达，不再修改 HTTP 状态。
            except (CustomerNotFoundError, UpstreamError, UpstreamTimeoutError) as error:
                await websocket.send_json({"type": "failed", "detail": str(error)})
    # 收发时发现对端断开，退出当前连接的循环。
    except WebSocketDisconnect:
        logger.info("浏览器已断开 WebSocket")
    finally:
        # 当前连接的收尾；共享客户端继续留给其他连接使用。
        logger.info("WebSocket 消息循环结束")
```

`@app.websocket("/ws")` 注册 WebSocket 入口；`accept` 接受连接；`receive_text` 等下一条文本消息；`send_json` 把 Python 数据编码成 JSON 消息发回去。`QueryInput.model_validate_json(text)` 将一条消息解析并校验成模型；失败时回复 failed 并 continue，仍能继续接收。

连接已经接受后，单条输入错误不会自动变成 HTTP 422；本例以 failed 消息表达。业务异常也映射为 failed，而不是抛 HTTPException 期待修改已经建立的连接。

`WebSocketDisconnect` 表示接收或发送时发现连接断开，退出循环。`finally` 做连接对应的收尾，本例不额外创建后台任务。共享 HTTPX 客户端仍由整个应用关闭。

### 3.1 关闭、取消与重连各是什么

正常关闭使用 `close(code=1000)`，1000 是正常结束的关闭码。页面关闭、网络掉线等情况也会结束连接，但不保证对方收到了最后一条业务结果，浏览器会收到相应 close/error 事件。

当前循环处理一次上游查询时正在 await HTTPX，直到它返回或超时，才会进入下一次接收；因此在查询过程中发送 quit，不能立即打断正在等待的上游调用。若产品确实需要“查询时同时接收取消命令”，需将接收与查询组织为独立任务，保存 task 引用，并在断开时 cancel 后 await 清理，机制见 [05 章](05-async-and-tasks.md#3)。本章不将当前顺序消息循环描述为已实现这种取消控制。

WebSocket 原生对象不自动提供业务恢复。演示页允许点击“连接 / 重连”新建连接，但不会自动重发上次查询。重连得到的是新连接，想恢复任务需要额外的任务编号与服务端状态；有写入效果的消息更不能在不知道执行结果时盲目重放。

## 4. 启动并在页面发送两条查询

保持模拟 ERP 在 8001，8002/8003 可以停止。本章从项目根目录运行：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_ws:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8004
```

打开 `http://127.0.0.1:8004/`。点击连接，客户编号 C001 点击查询；改成 C999 再查询；改成 C002 再查询。页面应依次显示 result(12800)、failed(客户不存在)、result(0)，连接仍保持。最后点击正常关闭，显示关闭码 1000。再点连接/重连，可开始新的查询。

页面中负责收发的最小 JavaScript 是：

```javascript
// 创建连接后需要等 onopen，不能立刻假设已经可以发送。
const socket = new WebSocket('ws://127.0.0.1:8004/ws');
// 客户编号先编码成 JSON 文本，再作为一条消息发送。
socket.onopen = () => socket.send(JSON.stringify({customer_id: 'C001'}));
// 逐条接收服务端消息，恢复为可读取字段的对象。
socket.onmessage = event => console.log(JSON.parse(event.data));
socket.onclose = event => console.log('已关闭', event.code); // 查看关闭码。
```

send 应在 onopen 后使用，连接仍在建立时不能立即发送。配套页面根据连接状态启用和禁用按钮，并根据当前网页协议选择 ws 或 wss。JavaScript 只负责演示页面通信，不作为 Python 模块的新主线。

Swagger 的普通 HTTP Try it out 不能当作 WebSocket 消息测试器，本章直接使用演示页。若启动提示缺少 WebSocket 支持，检查是否使用 07 章虚拟环境及其中的 websockets 包；不要只给 URL 加上 ws 就认为普通 GET 路由已支持 WebSocket。

## 5. 普通 HTTP、SSE、WebSocket 怎样选 {#selection}

| 需求 | 合适的起点 | 原因 |
| --- | --- | --- |
| 查一次 C001 欠款，拿到结果即可 | 普通 HTTP JSON | 输入与完整结果一次对应，易于调用和排错 |
| 发起一批查询，持续显示进度与结果 | HTTP + SSE | 一个响应持续从服务端向页面发送事件 |
| 连接期间持续提交消息、接收主动通知，双方频繁交流 | WebSocket | 建立连接后双方均可持续发送消息 |

模型逐字输出不必然需要 WebSocket：输入一次、输出持续到结束的场景，HTTP 流式响应或 SSE 都能承载。聊天也可以由每次 POST 提交问题，再以流返回回答；只有需求需要同一连接持续双向通信时，WebSocket 的特征才直接对应需求。

SSE 的客户端若要追加操作，可以另发普通 HTTP 请求；“一个连接单向”不等于整个应用无法提交数据。反过来，仅为重复查两次金额也可以连续发送两次普通 HTTP 请求，不能据此断定必须使用 WebSocket。

选型还要看客户端能力、现有网关和恢复需求；本模块先按上述数据流选择，部署参数与接入约束到对应模块处理。

## 6. 可选练习

条件：连接已经建立，客户数据和 QueryInput 不变。

1. 发送 `{"customer_id":"C001","min_amount":true}` 后，还能再发送合法 C002 查询吗？
2. 查询没有完成时直接关页面，服务端能否保证最后一条结果已经被用户收到？
3. “用户提交一个问题，服务端逐步生成回答，直到结束”优先尝试哪种通信？解释依据。

??? note "参考答案与依据"
    1. 可以。本条输入因 StrictInt 校验失败收到 failed，continue 回到接收循环；C002 仍可得到金额 0。
    2. 不能保证。连接断开不等于业务确认收到，若需要确认语义，应单独定义确认消息及状态。
    3. 可先用 HTTP 流式或 SSE。提交后主要是服务端持续输出，尚未出现必须在同一连接双向交互的要求。

整套 01 读完后，可按[客户端与服务端两遍复习](00-client-server-review.md)重新串起代码角色。

## 本章回顾与检查清单

WebSocket 将交互组织成连接上的多条消息；模型校验仍要逐条执行，失败消息与关闭连接也要分别约定。完成本章后，01 的主线已从普通函数走到可提供、调用和持续交互的接口。

- [ ] 能解释 accept → receive → 校验 → 调用 → send → 下一条消息。
- [ ] 能区分业务失败、连接关闭、查询取消与重连恢复。
- [ ] 能为一次查询、进度推送和持续双向交流选择通信方式。

## 阅读中产生的答疑

暂无。需要时回查 [03 的异常](03-errors-and-debugging.md)、[05 的取消](05-async-and-tasks.md)、[09 的事件结束](09-streaming-and-sse.md)，不在这里重讲同一套基础机制。

## 资料与模块后续

连接内多次查询、错误消息后继续、正常关闭与重新建立连接已验证。资料核实：2026-10-22。[FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/) · [浏览器 WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)。

这一模块的配套小工程和复核记录见本模块学习目录。教材准备完整后仍按实际阅读位置推进；完成阅读可再进入 [02 Linux、Git 与部署](../02-deployment/index.md)，模型调用与工具执行在 [03 LLM 模块](../03-llm-tools/index.md)，SQL 实操沿用 [08 数据库模块](../08-database/index.md)。

[上一章：流式与 SSE](09-streaming-and-sse.md) · [返回模块目录](index.md)
