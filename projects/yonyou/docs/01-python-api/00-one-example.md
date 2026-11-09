# 01 整合项目：客户欠款查询，从函数到接口

> 已整合 01–10 的运行代码、关键注释和阅读顺序。2026-10-28。运行检查与用户掌握状态分别记录。

这个项目只做一件事：查询客户欠款。先在同一程序中直接调用，再让另一个程序通过 HTTP 查询，最后在同一业务之上观察并发、SSE 和 WebSocket。用到的库单独见 [LIBRARIES.md](00-project-libraries.md)。

先按下表运行一段、读对应几行，再向后走。原来的分章用于查阅，不需要重新逐页串读。

## 1. 数据、文件与完整路线 {#files}

合成金额单位为人民币整数元：C001=12800，C002=0，C999 不存在。客户存在且达到最低金额才返回结果；门槛未命中返回 None，省略门槛或传 None 就不筛选。

```text
whole-example/
├── business.py       [S1] 数据、业务类、类型和业务异常
├── models.py         [S2] Pydantic 输入输出模型
├── local.py          直接调用业务，不需要启动服务
├── server.py         [S3–S7] HTTP、SSE、WebSocket 与启动入口
├── client.py         [C1–C10] Python 客户端的各个演示模式
├── page.html         同一个服务的浏览器客户端
├── pydantic_basics.py  单独观察模型校验的小例子
├── requirements.txt  依赖版本
├── README.md         现在这份项目主讲
├── LIBRARIES.md      每个库的用途、关键调用与易错点
├── sync_docs.py      将项目说明与实际源码同步到教材
├── verify.py         作者使用的真实 HTTP / SSE / WS 检查
└── .venv/            PyCharm 已选中的 Python 3.12 环境
```

`minimal_server.py`、`minimal_client.py`、`minimal_post_client.py` 是前面学过的短例，回查 GET/POST 时可以继续使用。当前完整主线使用上表这些文件，服务端统一监听 8010。

```text
client.py / 浏览器发出请求
    ↓
server.py 根据方法与路径找到处理函数
    ↓
models.py 检查输入 → business.py 查询同一份业务数据
    ↓
server.py 生成普通响应、SSE 事件或 WebSocket 消息
    ↓
客户端收到并使用结果
```

“读取哪个文件”和“程序执行哪条路线”不同：业务定义放在 business.py，不代表网络请求先到这个文件；请求先到服务端入口，再由路由调用导入的业务函数。

## 2. 先确认环境和运行方式 {#run}

PyCharm CE 已选中 `Python 3.12 (whole-example)`，解释器为项目内 `.venv/bin/python`。已装 FastAPI 0.159.1、Pydantic 2.14.1、HTTPX 0.28.1、Uvicorn 0.54.0、websockets 17.3。依赖锁定在 requirements.txt 引用的文件中，当前无需重装。

**下面所有终端命令都从 whole-example 目录执行。** 在 PyCharm 中可直接右键运行相应文件；给 client.py 加模式时，在 Run Configuration 的 Parameters 中填写 `get`、`query` 等。直接运行 client.py，默认执行 query。

```sh
# 不需要服务端的两个入口，可先运行。
.venv/bin/python local.py
.venv/bin/python pydantic_basics.py
```

之后打开两个终端：

```sh
# 终端 A：保持运行；结束时 Ctrl+C。
.venv/bin/python server.py

# 终端 B：向终端 A 的程序发请求。
.venv/bin/python client.py get
```

8010 上已有本例运行时，先结束旧的那次服务，再启动当前代码。更改业务或模型后也需重启；只有服务端在运行，网络查询才能收到响应。教材站仍使用 8765。

浏览器可以打开 http://127.0.0.1:8010/ 看同样的三种通信效果；http://127.0.0.1:8010/docs 可查看接口。`PORT` 可改变服务端监听端口；改端口时给客户端设置对应 `BASE_URL`。默认值已经配好，不需要为正常阅读改配置。

## 3. 第一步：先读一份普通业务 {#local}

运行 local.py，先看 business.py 的 [S1]。ReceivableBook 保存数据来源，query 接编号与命名参数 min_amount，返回字典、None 或抛业务异常：

```python
from business import book

result = book.query("C001", min_amount=1000)
print(result["amount"])  # 12800
```

这里没有发 HTTP，也没有 JSON 转换。TypedDict 说明返回字典有哪些字段；`__init__` 初始化对象；单独的 `*` 要求门槛按名字传。未知客户抛 CustomerNotFoundError，它继承 LookupError。

local.py 把 C001、C999、C002 放在同一个循环中：C999 的失败被捕获并记录，后面 C002 仍能查询到 0。末尾再显示 C002 门槛为 1 时返回 None。这里把函数、字典、类型、类、异常、导入、入口和 logger 接在一次执行中，不重新拆成多个练习。

## 4. 第二步：输入模型先把约定检查清楚 {#models}

先运行 pydantic_basics.py，再看 models.py 的 [S2]：

```python
from models import QueryInput

query = QueryInput(customer_id="C001", min_amount=1000)
print(query.customer_id, query.min_amount)  # C001 1000
```

项目的 QueryInput 要求编号为 C 后三位数字；门槛为非负整数或 None，拒绝字符串数字和布尔值；拼错或额外字段也会失败。合法输入成为模型对象，按 `query.customer_id` 读取。

普通类型标注主要描述约定，Pydantic 创建模型时实际校验。客户编号格式正确仍可能没有这个客户，例如 C999；是否存在由 business.py 判断。校验输入与查询业务是连续的两步。

## 5. 第三步：把 GET 请求和处理函数对起来 {#first-request}

服务运行后执行 `client.py get`，先看 client.py [C7] 与 server.py [S4]：

```text
[C7] GET /customers/C001/receivable?min_amount=1000
    ↓ 路径中的 C001、查询参数中的 1000
[S4] 取出参数 → [S2] 建立模型
    ↓
[S3] 模拟等待 → answer → [S1] book.query
    ↓
HTTP 200，JSON 内容：{"customer_id":"C001","amount":12800}
    ↓
[C7] response.json() → 客户端自己的字典
```

`@app.get(...)` 登记“这个 GET 地址交给紧接着定义的函数”。HTTPX 的 get 发出请求，服务端收到后按规则调用函数。`response.json()` 只解析已经收到的内容，不额外发请求。

在业务函数返回字典后，框架将它组织成 HTTP 响应。地址、方法和状态属于 HTTP；JSON 是响应内容的数据格式。通信双方在自己的进程里分别持有数据对象。

## 6. 第四步：POST、字段校验和业务错误 {#cases}

执行 `client.py query`，看 client.py 的 [C1/C2/C3]，以及 server.py [S3]：

```python
response = await client.post(
    "/receivables/query",
    json={"customer_id": "C001", "min_amount": None},
    params={"delay": 0.4},
)
```

json 把字典编码到请求体，params 把 delay 放到 URL 问号后。FastAPI 按 QueryInput 检查请求体，再调用 query_api。典型输出依次显示目标地址、实际请求 JSON、状态 200、响应文本、解析后的字典和金额 12800。

```sh
.venv/bin/python client.py cases
.venv/bin/python client.py validation
```

| 输入 / 情况 | 可观察结果 | 哪一步决定 |
| --- | --- | --- |
| C001，无门槛 | 200，金额 12800 | business.py 查询成功 |
| C002，门槛 0 | 200，金额 0 | 零金额仍是合法结果 |
| C002，门槛 1 | 200，JSON null；客户端为 None | 客户存在，未达到筛选条件 |
| C999 | 404，客户不存在 | 自定义异常由 answer 映射为 HTTPException |
| 负门槛、字符串金额、漏编号 | 422，字段错误说明 | Pydantic 检查失败，未执行查询 |
| 服务没有运行 | RequestError 等连接错误 | 尚未拿到 HTTP 响应 |

HTTPX 的 raise_for_status 在错误状态时抛 HTTPStatusError。业务程序据此选择处理失败，logger 负责留下记录。`validation` 模式为了显示字段原因，直接观察错误响应，不调用 raise_for_status 中断展示。

GET 和 POST 都能查询和返回结果。本例 GET 的编号在地址中，POST 的编号在 JSON 中；方法、路径与输入位置需按接口约定配对。`json=...` 负责发送数据，`.json()` 负责解析收到的数据。

## 7. 第五步：同一查询怎样顺序等待或并发 {#extensions}

```sh
.venv/bin/python client.py concurrent
.venv/bin/python client.py timeout
.venv/bin/python client.py cancel
.venv/bin/python client.py json
```

看 [C4]：先连续 await 两次，再用 gather 安排相同两项查询并发执行。服务器模拟等待 0.6 秒与 0.2 秒；典型总时间约从 0.8 秒变为 0.6 秒，另有网络与调度开销。C002 通常先完成，但 gather 返回的列表仍按 C001、C002 的传入顺序排列。

await 是当前任务等待结果；尚未完成时，它可以让事件循环安排其他就绪任务。它不会跳过当前等待去执行本任务的下一行。异步函数也不会仅因写了 async 就自动并发。

[C5] 用 wait_for 演示超时，用 create_task、cancel、await 演示主动取消。它们结束的是客户端这项等待，不保证服务器同时停止已经开始的处理。服务端只查询合成数据。

[C6] 的 json 模式独立演示 dict → JSON 文本 → UTF-8 字节 → Python 数据；这几步本身没有网络传输。新项目的异步操作分别在客户端和服务端的事件循环中发生，不能把两个程序看成同一条线程中的一个函数。

## 8. 第六步：一批查询逐步返回 SSE 事件 {#sse}

```sh
.venv/bin/python client.py sse
```

看 server.py [S5] 与 client.py [C9]。服务端按 C001、C999、C002 查询，逐条 yield 事件，客户端通过 HTTPX stream 和 aiter_lines 读取同一次响应：

```text
progress C001 → result 金额 12800
progress C999 → failed 客户不存在
progress C002 → result 金额 0
done processed=3
```

共 7 条事件。event 是事件名，data 是事件内容，空行结束一条 SSE 事件。本例在 data 中使用 JSON。最后的 done 是我们设计的事件名，不是 SSE 强制要求的名字。

C999 失败后，事件流继续处理 C002。响应已开始时，用 failed 事件表达单项失败；不能指望改写已经发出的 HTTP 状态。客户端看到 done 后退出流上下文，关闭本次读取；浏览器版也主动关闭 EventSource，避免自动重连重复执行。

## 9. 第七步：同一 WebSocket 连接，多次发送查询 {#websocket}

```sh
.venv/bin/python client.py websocket
```

看 server.py [S6] 与 client.py [C10]。连接到 ws://127.0.0.1:8010/ws 后，依次发送 C001、C999、C002；每条消息都按 QueryInput 检查并复用 book.query。客户端收到 result、failed、result，再发 quit，最后显示关闭码 1000。

服务端 accept → receive_text → 模型检查 → 业务查询 → send_json → 等下一条。当前循环顺序处理一条消息后再读下一条；双向连接本身不会自动让业务并发。重连只建立新连接，消息或任务恢复需要另行设计。

普通 HTTP 适合一次查询一个完整结果；SSE 适合一次请求后持续接收进度；需要双方反复发送业务消息时可用 WebSocket。浏览器 page.html 与 Python client.py 使用同一个服务，浏览器分别使用 fetch、EventSource 和 WebSocket，Python 分别使用 HTTPX 和 websockets。

## 10. 全模块覆盖与库的阅读位置 {#map}

| 原章 | 项目位置 | 串起来看什么 |
| --- | --- | --- |
| 01 函数 | business.py、local.py | 输入、返回、字典取值和调用者使用结果 |
| 02 类型与参数 | business.py、models.py | TypedDict、可空、默认值、命名参数、运行检查 |
| 03 异常 | business.py、server.py answer、client.py | 业务异常 → HTTP 状态 → 客户端处理、日志 |
| 04 工程组织 | 所有模块的 import、入口、配置与 async with | 文件分工、启动、环境变量、关闭资源 |
| 05 异步 | [C4/C5]、[S3] | await、并发、超时、取消与收尾 |
| 06 HTTP / JSON | [C1/C2/C6/C7] | 方法、地址、请求体、状态、JSON 与字节 |
| 07 FastAPI / Pydantic | models.py、[S3/S4] | 登记路由、提取参数、检查模型、组织响应 |
| 08 HTTPX | client.py 的 ask 与 AsyncClient | 主动请求、复用客户端、解析与异常 |
| 09 SSE | [S5/C9] | yield、逐条读取、事件格式与结束 |
| 10 WebSocket | [S6/C10] | 连接、多条消息、业务失败与正常关闭 |

单独的 [库用法说明](00-project-libraries.md)按 FastAPI、Pydantic、HTTPX、Uvicorn、websockets 和标准库展开，每项给本项目位置、关键调用、例子与常见误区。HTTP、JSON、SSE 等概念也在开头定位，避免把协议或数据格式当成同一类库。

## 11. 两个小练习与回顾 {#practice}

条件固定：C001=12800、C002=0、C999 不存在，服务端在 8010。可以先手动推演，不要求先运行。

1. 改成查询 C002 且门槛为 1：经过哪些文件？为什么收到 200 但解析后是 None？
2. 想让 C001 的合成金额变成 15000，改哪个文件？如果希望结果再包含 currency 字段，哪些数据约定要同步？

??? note "参考判断"

    第一题走 client → server → models → business → server → client，业务判断金额低于门槛，所以成功响应内容为 null。

    第二题的数据在 business.py 的 book 初始化处；增加结果字段时同步业务返回、TypedDict 与 models.py 的 Receivable，并核对客户端如何使用。

确认自己能指出发请求、检查输入、查询金额、解析结果各在哪一段，就可以继续该项目下一阶段。遇到具体疑问时，用文件名和 S/C 标记提问即可，不用重新背整章名词。

## 12. 运行、验证与维护

```sh
# 按顺序看全部网络演示；本地业务另运行 local.py。
.venv/bin/python client.py all

# 复核已启动服务的业务、HTTP、SSE、WebSocket 与各模式。
.venv/bin/python verify.py

# 更新项目说明后，同步到网页教材。
.venv/bin/python sync_docs.py
```

verify.py 默认核对 8010，也可用 BASE_URL 指向独立验证服务；不会结束你启动的服务。最新验证在 VERIFICATION.json，环境核对在 ENVIRONMENT-VERIFICATION.json。作者运行检查不计为用户掌握。

PyCharm CE 的包管理组件已在此 .venv 中准备：setuptools 80.10.2、wheel 0.48.0、packaging 26.3。旧版 IDE 的包列表通过 pkg_resources 读取；重建环境时，在安装 requirements.txt 后额外安装上述工具即可。原共享 .venv-api 仍可使用，当前新命令默认使用项目自己的 .venv。

本项目使用内存中的合成数据和模拟等待，数据库取数沿用后续数据库模块。先解释数据与程序如何衔接，再接真实数据来源。


## 完整源码（按需展开） {#code}

以下内容直接取自可运行文件。

??? note "完整 business.py"

    ```python
    """01–04：普通 Python 业务；数据、类、参数、返回与异常。"""
    from typing import TypedDict


    # [S1] 普通 Python：数据、类型、类初始化和业务函数。
    class ReceivableResult(TypedDict):
        customer_id: str
        amount: int


    class CustomerNotFoundError(LookupError):
        pass


    class ReceivableBook:
        def __init__(self, balances: dict[str, int]):
            self.balances = balances  # 每个对象保存自己的数据来源。

        def query(
            self, customer_id: str, *, min_amount: int | None = None
        ) -> ReceivableResult | None:
            # 这一步只是查本机字典，没有发 HTTP，也没有做 JSON 编码。
            if customer_id not in self.balances:
                raise CustomerNotFoundError("客户不存在")
            amount = self.balances[customer_id]
            if min_amount is not None and amount < min_amount:
                return None  # 客户存在，但没有达到本次筛选门槛。
            return {"customer_id": customer_id, "amount": amount}


    # 合成数据：人民币整数元。0 是合法金额，C999 没有记录。
    book = ReceivableBook({"C001": 12800, "C002": 0})
    ```

??? note "完整 models.py"

    ```python
    """02 / 07：接口输入输出约定；创建模型时执行校验。"""
    from pydantic import BaseModel, ConfigDict, Field


    # [S2] 接口约定：收到 JSON 后，Pydantic 按这些字段检查并创建模型。
    class QueryInput(BaseModel):
        model_config = ConfigDict(extra="forbid")  # 拒绝拼错或多余的字段。
        customer_id: str = Field(pattern=r"^C[0-9]{3}$")
        min_amount: int | None = Field(default=None, ge=0, strict=True)


    class Receivable(BaseModel):
        customer_id: str
        amount: int
    ```

??? note "完整 local.py"

    ```python
    """第一步：先在同一程序里直接调用业务，不需要启动服务。"""
    import logging

    from business import CustomerNotFoundError, book


    def main():
        # logging 是标准库；配置一次，业务失败时保留可读记录。
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
        for customer_id in ["C001", "C999", "C002"]:
            try:
                result = book.query(customer_id, min_amount=None)
                print("本地查询：", result)
            except CustomerNotFoundError as error:
                logging.warning("%s 查询失败：%s", customer_id, error)

        print("C002 门槛为 1：", book.query("C002", min_amount=1))


    if __name__ == "__main__":
        main()  # import local 时不执行本轮查询。
    ```

??? note "完整 server.py"

    ```python
    """服务端入口：路由 → 输入模型 → 同一业务 → HTTP / SSE / WebSocket 响应。"""
    import asyncio
    import json
    import logging
    import os
    from pathlib import Path
    from typing import Annotated

    from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, StreamingResponse
    from pydantic import ValidationError

    # 导入各自负责的定义；import 不会启动业务查询或监听端口。
    from business import CustomerNotFoundError, ReceivableBook, ReceivableResult, book
    from models import QueryInput, Receivable


    app = FastAPI(title="01 综合例子：客户欠款查询")
    logger = logging.getLogger("uvicorn.error")


    def answer(query: QueryInput) -> ReceivableResult | None:
        try:
            result = book.query(query.customer_id, min_amount=query.min_amount)
            logger.info("[S1 业务结果] %s", result)
            return result
        except CustomerNotFoundError as error:
            # 业务异常在 HTTP 接口边界映射成状态码，原始原因继续保留。
            raise HTTPException(status_code=404, detail=str(error)) from error


    # [S3] 服务器收到 POST /receivables/query 后，FastAPI 调用这个函数。
    @app.post("/receivables/query", response_model=Receivable | None)
    async def query_api(
        query: QueryInput,  # 来自 JSON 请求体，已由框架按 [S2] 校验。
        delay: Annotated[float, Query(ge=0, le=5)] = 0.4,
    ):
        logger.info("[S3 收到查询] %s，门槛=%s", query.customer_id, query.min_amount)
        await asyncio.sleep(delay)  # 只模拟接口耗时；等待时可处理其他请求。
        return answer(query)  # 返回 Python 数据；框架将其编码成 JSON 响应。


    # [S4] 同一查询的 GET 入口：编号放在路径里，门槛放在查询字符串里。
    @app.get("/customers/{customer_id}/receivable", response_model=Receivable | None)
    async def query_get(
        customer_id: str,
        min_amount: Annotated[int | None, Query(ge=0)] = None,
    ):
        try:
            query = QueryInput(customer_id=customer_id, min_amount=min_amount)
        except ValidationError as error:
            raise HTTPException(status_code=422, detail="客户编号格式不合法") from error
        return await query_api(query, delay=0.4)


    # [S5] SSE：在一次 HTTP 响应内，逐条发送同一批客户的进度与结果。
    def event_text(name: str, data: dict) -> str:
        # JSON 在 data 行中表达字段；两个换行结束一条 SSE 事件。
        return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


    @app.get("/events")
    async def events(request: Request):
        async def generate():
            try:
                for customer_id in ["C001", "C999", "C002"]:
                    if await request.is_disconnected():
                        return  # 页面离开后，不继续开始新的查询。
                    yield event_text("progress", {"customer_id": customer_id})
                    await asyncio.sleep(0.4)
                    try:
                        result = book.query(customer_id)  # 仍是 [S1]，没有另一套业务。
                        yield event_text("result", {"data": result})
                    except CustomerNotFoundError as error:
                        yield event_text("failed", {"customer_id": customer_id, "detail": str(error)})
                yield event_text("done", {"processed": 3})  # 三项已尝试，不代表全成功。
            finally:
                logger.info("[S5 SSE] 本次事件流结束；没有遗留后台任务")

        return StreamingResponse(
            generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
        )


    # [S6] WebSocket：同一连接中，多次接收查询并返回消息。
    @app.websocket("/ws")
    async def socket_queries(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                text = await websocket.receive_text()  # 等下一条消息，当前任务暂停。
                if text == "quit":
                    await websocket.close(code=1000)
                    return
                try:
                    query = QueryInput.model_validate_json(text)  # 每条消息单独校验。
                except ValidationError:
                    await websocket.send_json({"type": "failed", "detail": "查询消息格式不合法"})
                    continue
                try:
                    await asyncio.sleep(0.4)
                    result = book.query(query.customer_id, min_amount=query.min_amount)
                    await websocket.send_json({"type": "result", "data": result})
                except CustomerNotFoundError as error:
                    # 连接已建立，业务失败用消息表达，之后仍可接收下一次查询。
                    await websocket.send_json({"type": "failed", "detail": str(error)})
        except WebSocketDisconnect:
            logger.info("[S6 WebSocket] 客户端已离开")
        finally:
            logger.info("[S6 WebSocket] 本次消息循环结束")


    # 浏览器页面只是另一个客户端；Python 客户端见同目录 client.py。
    @app.get("/")
    def page():
        return FileResponse(Path(__file__).with_name("page.html"))


    # [S7] 运行入口：直接运行启动监听；import server 不会启动服务器。
    if __name__ == "__main__":
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8010")))
    ```

??? note "完整 client.py"

    ```python
    """01 综合例子的 Python 客户端：和 server.py 是两个独立程序。"""
    import asyncio
    import json
    import os
    import sys
    from time import perf_counter

    import httpx
    from websockets.asyncio.client import connect


    # [C1] Python 发 HTTP 请求；服务器里的 balances 不在这个程序的内存里。
    async def ask(
        client: httpx.AsyncClient,
        customer_id: str,
        *,
        min_amount: int | None = None,
        delay: float = 0.4,
        show_wire: bool = False,
    ) -> dict | None:
        body = {"customer_id": customer_id, "min_amount": min_amount}
        response = await client.post(
            "/receivables/query",
            json=body,  # HTTPX 将字典编码为 JSON 请求体，再发送出去。
            params={"delay": delay},  # 放入 URL 问号后；只控制演示等待时长。
        )
        if show_wire:
            print("[C1 发往地址]", response.request.url)
            print("[C1 发出 JSON]", response.request.content.decode("utf-8"))
            print("[C2 HTTP 状态]", response.status_code)
            print("[C2 收到文本]", response.text)
        response.raise_for_status()  # 先判断 HTTP 状态，错误响应交给调用者捕获。
        data = response.json()  # [C2] JSON → 本客户端的 Python 字典或 None。
        print("[C2 解析结果]", customer_id, data)
        return data


    async def demo_query(client):
        # 第一轮只看这次正常查询；终端日志会显示请求和响应的实际内容。
        result = await ask(client, "C001", show_wire=True)
        print("[C3 继续使用] 金额：", result["amount"])


    async def demo_cases(client):
        # 对照零金额、未命中门槛与未知客户；三种含义保持分开。
        await ask(client, "C002", min_amount=0)
        await ask(client, "C002", min_amount=1)
        try:
            await ask(client, "C999", show_wire=True)
        except httpx.HTTPStatusError as error:
            print("[C3 业务失败] HTTP", error.response.status_code)


    async def demo_get(client):
        # [C7] GET：编号在路径中，门槛在 URL 问号后的查询参数中。
        response = await client.get(
            "/customers/C001/receivable", params={"min_amount": 1000}
        )
        response.raise_for_status()
        print("[C7 GET 地址]", response.request.url)
        print("[C7 GET 结果]", response.json())


    async def demo_validation(client):
        # [C8] 这里只观察错误响应，不调用 raise_for_status 中断演示。
        for body in [
            {"customer_id": "C001", "min_amount": -1},
            {"customer_id": "C001", "min_amount": "1000"},
            {"min_amount": 1000},
        ]:
            response = await client.post("/receivables/query", json=body)
            print("[C8 输入校验]", body, "HTTP", response.status_code)
            print("[C8 字段原因]", response.json()["detail"][0]["type"])


    async def demo_concurrent(client):
        start = perf_counter()
        await ask(client, "C001", delay=0.6)
        await ask(client, "C002", delay=0.2)
        print("[C4 顺序耗时]", round(perf_counter() - start, 2))

        start = perf_counter()
        results = await asyncio.gather(
            ask(client, "C001", delay=0.6), ask(client, "C002", delay=0.2)
        )
        print("[C4 并发耗时]", round(perf_counter() - start, 2))
        print("[C4 gather 返回顺序]", results)  # 输入顺序，不是完成顺序。


    async def demo_timeout(client):
        try:
            # 服务器模拟等 1 秒；客户端只给本次操作 0.1 秒的总等待时间。
            await asyncio.wait_for(ask(client, "C001", delay=1), timeout=0.1)
        except TimeoutError:
            print("[C5 超时] 本次等待已结束，不会得到本次的金额结果")


    async def demo_cancel(client):
        task = asyncio.create_task(ask(client, "C001", delay=1))
        await asyncio.sleep(0.05)  # 让任务先开始等待，再模拟用户不需要结果。
        task.cancel()
        try:
            await task  # 请求取消后，仍等待它响应取消并收尾。
        except asyncio.CancelledError:
            print("[C5 取消] 客户端任务已取消")


    def demo_json():
        # [C6] 单独观察格式转换。这几行本身没有执行任何网络传输。
        result = {"customer_id": "C001", "amount": 12800}
        text = json.dumps(result, ensure_ascii=False)
        payload = text.encode("utf-8")
        restored = json.loads(payload)
        print("[C6 类型]", type(result).__name__, type(text).__name__, type(payload).__name__)
        print("[C6 恢复结果]", restored)


    async def demo_sse(client):
        # [C9] 同一个 HTTP 响应逐步读取；空行表示一条 SSE 事件结束。
        name, data_lines = "message", []
        async with client.stream("GET", "/events") as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    name = line[6:].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[5:].lstrip(" "))
                elif line == "" and data_lines:
                    data = json.loads("\n".join(data_lines))
                    print("[C9 SSE]", name, data, flush=True)
                    if name == "done":
                        break  # 退出上下文，关闭这次事件流。
                    name, data_lines = "message", []


    async def demo_websocket(client):
        # [C10] HTTP 服务对应 ws / wss 地址；连接中多次发送消息。
        url = str(client.base_url).replace("http", "ws", 1).rstrip("/") + "/ws"
        async with connect(url) as websocket:
            for customer_id in ["C001", "C999", "C002"]:
                message = {"customer_id": customer_id, "min_amount": None}
                await websocket.send(json.dumps(message))
                reply = json.loads(await websocket.recv())
                print("[C10 WebSocket]", customer_id, reply, flush=True)
            await websocket.send("quit")  # 使用本项目约定，请求服务端正常关闭。
            await websocket.wait_closed()
            print("[C10 连接结束]", websocket.close_code)


    async def main():
        # 命令行第二项选择演示，例如 client.py concurrent；不写则 query。
        mode = sys.argv[1] if len(sys.argv) > 1 else "query"
        if mode == "json":
            demo_json()
            return
        demos = {
            "query": demo_query, "cases": demo_cases, "concurrent": demo_concurrent,
            "timeout": demo_timeout, "cancel": demo_cancel,
            "get": demo_get, "validation": demo_validation,
            "sse": demo_sse, "websocket": demo_websocket,
        }
        if mode not in demos and mode != "all":
            print("可选演示：", " / ".join([*demos, "json", "all"]))
            return
        base_url = os.getenv("BASE_URL", "http://127.0.0.1:8010")
        # 一次演示共用客户端；离开上下文关闭它及连接池。
        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            if mode == "all":
                for name, demo in demos.items():
                    print("\n当前演示：", name, flush=True)
                    await demo(client)
                demo_json()
            else:
                await demos[mode](client)


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except httpx.RequestError as error:
            print("[网络失败] 检查 server.py 是否运行、地址端口是否正确：", type(error).__name__)
        except httpx.HTTPStatusError as error:
            print("[HTTP 失败]", error.response.status_code, error.response.text)
    ```

??? note "完整 page.html"

    ```html
    <!doctype html>
    <html lang="zh-CN">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>01 综合例子：客户欠款查询</title>
    <style>
    body { max-width: 900px; margin: 28px auto; padding: 0 18px; font: 16px/1.6 system-ui; color: #203035; }
    section { border-top: 1px solid #ccd5d8; margin-top: 24px; padding-top: 12px; }
    button, input { padding: 6px 10px; margin: 4px; font: inherit; }
    pre { background: #f2f5f6; padding: 14px; white-space: pre-wrap; overflow-wrap: anywhere; min-height: 40px; }
    </style>
    <h1>同一次查询，三种通信方式</h1>
    <p>合成数据：C001 欠款 12800 元，C002 欠款 0 元，C999 不存在。</p>
    <p>先只看第一块。这个页面用浏览器 fetch 发 HTTP 请求；client.py 则用 HTTPX，二者访问同一个服务。</p>
    <label>客户编号 <input id="customer" value="C001"></label>
    <label>最低金额 <input id="minimum" type="number" min="0" step="1" placeholder="留空不筛选"></label>

    <section>
    <h2>1. 普通 HTTP：一次查询，一次结果</h2>
    <button id="query">发送查询</button><pre id="http-output">等待发送。</pre>
    </section>
    <section>
    <h2>2. SSE：一次请求，逐条收到进度和结果</h2>
    <p>固定顺序：C001、C999、C002，不使用上方筛选条件。</p>
    <button id="start-events">开始一批</button><button id="stop-events">停止接收</button><pre id="event-output"></pre>
    </section>
    <section>
    <h2>3. WebSocket：连接保留，可以多次发送查询</h2>
    <button id="connect">连接 / 重连</button><button id="send" disabled>发送上方查询</button><button id="close" disabled>正常关闭</button><pre id="socket-output"></pre>
    </section>
    <script>
    const field = id => document.getElementById(id);
    function queryBody() {
      const value = field('minimum').value;
      return {customer_id: field('customer').value, min_amount: value === '' ? null : Number(value)};
    }

    // 浏览器也是客户端；先发送 JSON，再显示收到的文本和解析后的对象。
    field('query').onclick = async () => {
      const out = field('http-output');
      const body = JSON.stringify(queryBody());
      out.textContent = '[浏览器发送] POST /receivables/query\n' + body + '\n';
      try {
        const response = await fetch('/receivables/query', {method: 'POST', headers: {'Content-Type': 'application/json'}, body});
        const text = await response.text();
        out.textContent += '[收到状态] ' + response.status + '\n[收到 JSON 文本] ' + text;
        out.textContent += '\n[解析后的数据]\n' + JSON.stringify(JSON.parse(text), null, 2);
      } catch (error) { out.textContent += '\n[连接失败] ' + error.message; }
    };

    // 命名事件按 SSE 格式分开；done 后主动关闭，避免自动重连重复查询。
    let source;
    field('start-events').onclick = () => {
      if (source) source.close();
      field('event-output').textContent = '';
      source = new EventSource('/events');
      for (const name of ['progress', 'result', 'failed', 'done']) {
        source.addEventListener(name, event => {
          field('event-output').textContent += name + ': ' + event.data + '\n';
          if (name === 'done') source.close();
        });
      }
      source.onerror = () => { source.close(); field('event-output').textContent += '连接中断，可手动重开一批。\n'; };
    };
    field('stop-events').onclick = () => { if (source) source.close(); };

    // 新连接建立后才能发送；重新连接不会自动重发上次的业务消息。
    let socket;
    field('connect').onclick = () => {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(scheme + '://' + location.host + '/ws');
      field('connect').disabled = true;
      socket.onopen = () => { field('send').disabled = field('close').disabled = false; field('socket-output').textContent += '已连接\n'; };
      socket.onmessage = event => { field('socket-output').textContent += event.data + '\n'; };
      socket.onerror = () => { field('socket-output').textContent += '连接错误，检查服务。\n'; };
      socket.onclose = event => {
        field('send').disabled = field('close').disabled = true; field('connect').disabled = false;
        field('socket-output').textContent += '已关闭，code=' + event.code + '\n';
      };
    };
    field('send').onclick = () => socket.send(JSON.stringify(queryBody()));
    field('close').onclick = () => { socket.send('quit'); field('send').disabled = field('close').disabled = true; };
    </script>
    </html>
    ```
