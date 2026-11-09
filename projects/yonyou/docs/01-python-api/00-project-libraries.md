# 这个项目用到的库：各自做什么，怎么调用

建议对照[整合项目](00-one-example.md)阅读：先看一次请求如何走完，再按这里查调用。不需要一次记住所有名字。

## 先分清几个名字

| 名字 | 属于什么 | 在例子里负责什么 |
| --- | --- | --- |
| HTTP | 通信协议 | 规定请求、响应、状态码等交互方式 |
| GET / POST | HTTP 请求方法 | 与路径一起决定服务端匹配哪个入口 |
| JSON | 数据格式 | 用文本表达客户编号、金额等字段 |
| FastAPI | Python 库、Web 框架 | 接收请求、匹配函数、组织响应 |
| HTTPX | Python 库、HTTP 客户端 | 向服务端发送 HTTP 请求、读取响应 |
| SSE | 基于 HTTP 的事件流格式 | 在一次响应里逐条发送进度和结果 |
| WebSocket | 通信协议 | 建立连接后，双方可以持续发送消息 |
| `async` / `await` / `yield` | Python 语法 | 定义异步函数、等待结果、逐项产生内容 |

`app.get` 中的 `get` 登记服务端入口；`httpx.get` 中的 `get` 发出客户端请求。它们在请求的两端。

## 需要安装的五个库

当前项目环境：Python 3.12；具体依赖固定在 `requirements.txt`。这些版本已在本机项目环境运行核对。

| 库及当前版本 | 用在哪里 | 先记住的调用 |
| --- | --- | --- |
| FastAPI 0.159.1 | `server.py` | `FastAPI()`、`@app.get`、`@app.post` |
| Pydantic 2.14.1 | `models.py` | `BaseModel`、`Field`、`model_validate` |
| HTTPX 0.28.1 | `client.py` | `AsyncClient`、`get/post`、`response.json()` |
| Uvicorn 0.54.0 | `server.py` 最后 | `uvicorn.run(app, host=..., port=...)` |
| websockets 17.3 | `client.py` WebSocket 演示 | `connect`、`send`、`recv` |

在项目目录补装时使用 `.venv/bin/python -m pip install -r requirements.txt`。PyCharm 已选择这个 `.venv` 作为项目解释器。

## 1. FastAPI：给业务函数安排对外入口

`business.py` 的 `book.query()` 本来只是 Python 函数。FastAPI 让另一个程序可以通过地址来调用这里安排的处理逻辑。

下面是理解用的缩略代码，完整入口见 `server.py` 的 `[S3]`、`[S4]`：

```python
from fastapi import FastAPI

app = FastAPI()  # 创建应用对象，保存接口配置。

@app.get("/hello")  # 登记：GET /hello 由紧接着的函数处理。
def hello():
    return {"message": "你好"}  # 框架组织成 JSON 响应。
```

执行装饰器时登记关系；服务运行后，收到匹配的请求才调用处理函数。调用 `hello()` 本身仍然是普通 Python 调用。

本项目再用这些功能处理实际要求：

| 调用 | 项目中的作用 |
| --- | --- |
| `@app.post(..., response_model=Receivable \| None)` | 接收查询，按输出模型检查和组织返回数据 |
| `query: QueryInput` | 将 JSON 请求体交给 Pydantic 创建输入对象；失败返回 422 |
| `Query(ge=0, le=5)` | 限制 URL 查询参数 `delay` 的范围 |
| `HTTPException(status_code=404, detail="客户不存在")` | 将业务查询失败转换成 HTTP 错误响应 |
| `StreamingResponse(generate(), media_type="text/event-stream")` | 将异步生成器逐条产生的内容作为 SSE 响应发出 |
| `@app.websocket("/ws")` | 登记 WebSocket 入口 |
| `await websocket.accept()` / `receive_text()` / `send_json(...)` | 接受连接、接收文字、发送 JSON 消息 |
| `WebSocketDisconnect` | 客户端离开时结束服务端消息循环 |
| `FileResponse(...)` | 返回 `page.html`，让浏览器显示演示页面 |

`fastapi.responses` 是 FastAPI 提供的导入位置，不需要另装一个叫 responses 的库。

## 2. Pydantic：把收到的数据变成经过校验的对象

你说的“限制值的条件”是它的一部分。它还负责必填字段、类型、默认值，以及将数据整理成方便使用的对象。

项目的完整约定在 `models.py`：

```python
from pydantic import BaseModel, ConfigDict, Field

class QueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 多余或拼错的字段也拒绝。
    customer_id: str = Field(pattern=r"^C[0-9]{3}$")
    min_amount: int | None = Field(default=None, ge=0, strict=True)

query = QueryInput.model_validate({"customer_id": "C001", "min_amount": 1000})
print(query.customer_id)  # C001：现在可以用属性访问。
print(query.model_dump())  # 转成 Python 字典。
print(query.model_dump_json())  # 转成 JSON 字符串；没有发送网络请求。
```

`min_amount` 允许整数或 `None`；不提供时使用 `None`；提供整数时必须大于等于零。这里的 `strict=True` 会拒绝字符串 `"1000"`，也拒绝布尔值。Pydantic 默认允许部分类型转换，所以需要严格整数时应明确声明。

| 调用 | 输入 → 结果 |
| --- | --- |
| `QueryInput(customer_id="C001")` | 关键字参数 → 已校验的模型对象 |
| `QueryInput.model_validate(data)` | Python 字典等数据 → 已校验的模型对象 |
| `QueryInput.model_validate_json(text)` | JSON 文本 → 已校验的模型对象；WebSocket 每条消息用它 |
| `query.model_dump()` | 模型 → Python 字典 |
| `query.model_dump_json()` | 模型 → JSON 字符串 |

直接创建模型遇到不合要求的数据会抛出 `ValidationError`。FastAPI 的请求体入口会替你处理这类输入错误，返回 422；本项目 WebSocket 入口自己捕获它，再发送失败消息。

格式合法的 `C999` 仍然可能查不到客户：Pydantic 检查这里声明的数据约定，`business.py` 再判断客户是否存在。

与 `TypedDict` 联系起来看：`TypedDict` 为字典提供字段类型提示，运行时仍是字典；Pydantic 的 `BaseModel` 会在创建对象时实际校验。普通类还可以组织状态与方法；本项目的 `ReceivableBook` 就负责业务查询。

单独观察这个过程，可运行 `.venv/bin/python pydantic_basics.py`。

## 3. HTTPX：作为客户端，真正把请求发出去

`client.py` 的 `[C1]` 负责发出请求，`[C2]` 负责检查并解析响应。下面的同步小例子需要先运行服务端：

```python
import httpx

# GET：编号在路径中，门槛在问号后的查询字符串中。
response = httpx.get(
    "http://127.0.0.1:8010/customers/C001/receivable",
    params={"min_amount": 1000},
    timeout=5,
)
response.raise_for_status()  # 错误状态转成异常，交给调用者处理。
print(response.json())  # 将响应 JSON 解析为本程序的 Python 数据。

# POST：json= 会把字典编码成 JSON 请求体，再发出去。
response = httpx.post(
    "http://127.0.0.1:8010/receivables/query",
    json={"customer_id": "C001", "min_amount": 1000},
    timeout=5,
)
response.raise_for_status()
print(response.json())
```

项目使用异步客户端，以便继续演示并发：

```python
async with httpx.AsyncClient(base_url="http://127.0.0.1:8010", timeout=5) as client:
    response = await client.post("/receivables/query", json={"customer_id": "C001"})
    response.raise_for_status()
    data = response.json()  # 解析已收到的内容；这里不用 await。
```

这段放在 `async def` 中运行，完整版本见 `client.py`。`async with` 退出时关闭客户端；共用客户端可以复用连接。

| 写法 | 含义 |
| --- | --- |
| `params={...}` | URL 问号后的参数，例如 `?min_amount=1000` |
| `json={...}` | 请求体中的 JSON 数据 |
| `response.status_code` | HTTP 状态码，例如 200、404、422 |
| `response.text` | 响应正文的字符串形式 |
| `response.json()` | 解析正文 JSON，得到字典、列表、`None` 等 Python 数据 |
| `response.raise_for_status()` | 对错误 HTTP 状态抛出 `HTTPStatusError` |
| `client.stream(...)` 与 `response.aiter_lines()` | 打开流式响应，逐行读取；项目 `[C9]` 据此识别 SSE 事件 |

连不上服务器、连接中断、网络超时等通常捕获 `httpx.RequestError`；已经收到 404 等错误响应，调用 `raise_for_status()` 后捕获 `httpx.HTTPStatusError`。

HTTPX 的超时包含连接、读、写、连接池等待等阶段；`timeout=5` 不等于给整个多阶段操作统一设置五秒总时限。本项目 `[C5]` 用 `asyncio.wait_for(..., timeout=0.1)` 演示整个等待操作的超时。

## 4. Uvicorn：启动服务，监听端口

FastAPI 对象保存接口规则；Uvicorn 运行它，等待网络请求。

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)
```

这是 `server.py` 末尾的启动方式。`127.0.0.1` 表示本机地址，`8010` 是选定端口，可以修改，但客户端地址也要对应。

直接运行 `server.py` 时进入这个启动分支；`import server` 时只加载定义和配置，不进入启动分支。看到 `Uvicorn running on ...` 后，再运行客户端。报端口被占用时，检查已有服务或选择其他空闲端口。

## 5. websockets：Python 客户端建立长连接

服务端用 FastAPI 的 WebSocket 接口；Python 客户端用 `websockets` 库连接它。两端并不需要使用同名框架。

下面放在异步函数中，完整版本见 `client.py` 的 `[C10]`：

```python
import json
from websockets.asyncio.client import connect

async with connect("ws://127.0.0.1:8010/ws") as ws:
    await ws.send(json.dumps({"customer_id": "C001"}))  # 发一条 JSON 文本。
    reply = json.loads(await ws.recv())  # 等一条回复，再解析 JSON。
    print(reply)
    await ws.send("quit")  # 本项目约定的结束消息。
    await ws.wait_closed()
    print(ws.close_code)  # 正常关闭为 1000。
```

连接内可以重复发送和接收；`send` 与 `recv` 的对应规则由业务约定。`quit` 是本项目自定的消息内容。`ws://` 用于这里的本机连接；`wss://` 表示加密连接。

`async with` 会收尾关闭连接。收到客户不存在的失败消息后仍可以查下一个客户；连接本身关闭时，后续收发就不能继续使用它。

## Python 自带的库：不用 pip 安装

### asyncio：组织异步任务

项目 `[C4]`、`[C5]` 使用这些操作：

| 操作 | 用途 |
| --- | --- |
| `asyncio.run(main())` | 从普通程序入口运行异步主函数 |
| `await asyncio.sleep(0.4)` | 模拟等待；当前任务暂停，让其他已安排的任务有机会运行 |
| `await asyncio.gather(ask(...), ask(...))` | 并发安排多个查询，成功时等待全部完成，按传入顺序返回结果 |
| `asyncio.create_task(ask(...))` | 创建并安排一个任务，保存任务对象以便稍后等待或取消 |
| `task.cancel()`，随后 `await task` | 请求取消，再等待任务响应取消并收尾 |
| `await asyncio.wait_for(ask(...), timeout=0.1)` | 限定等待时间；超时取消被等待任务并抛出 `TimeoutError` |

`await` 等待结果，后面的代码等结果可用才继续；等待期间，事件循环可以运行其他已安排的任务。连续两次 `await ask(...)` 仍然是先后查询。`gather` 默认某项失败会向等待者抛出异常，其他已安排任务不因此自动全部取消。

这里的并发主要重叠网络等待，默认事件循环在一个线程里调度任务。`async` 不会自动把普通阻塞代码变成异步操作。

### json：转换数据格式

```python
import json

result = {"customer_id": "C001", "amount": 12800}
text = json.dumps(result, ensure_ascii=False)  # 字典 → JSON 字符串。
payload = text.encode("utf-8")  # 字符串 → 字节：encode 是字符串方法。
restored = json.loads(payload)  # JSON 字符串或字节 → Python 数据。
```

这几行只处理数据格式。HTTPX 的 `json=` 会替你完成请求体编码，再执行网络发送。

### 其余实际用到的标准库

| 标准库 | 项目中的用途 |
| --- | --- |
| `typing.TypedDict` | `business.py` 声明返回字典的字段提示 |
| `typing.Annotated` | `server.py` 将参数类型与 `Query(...)` 配置放在一起 |
| `logging` | `local.py` 与 `server.py` 记录失败或运行过程；记录日志本身不会抛异常 |
| `pathlib.Path` | 找到与 `server.py` 同目录的页面，不依赖终端当前目录 |
| `os.getenv` | 读取 `BASE_URL`、`PORT` 等环境配置 |
| `sys.argv` | 读取命令行演示名，例如 `client.py sse` 中的 `sse` |
| `time.perf_counter` | 比较顺序查询和并发查询的耗时 |

你问过的 `collections.defaultdict` 也属于标准库。它用于访问缺失键时自动产生默认值，例如 `defaultdict(list)` 配合 `groups[key].append(...)` 分组。本项目查询未知客户需要明确报错，因此这里使用普通字典。`TypedDict` 和 `defaultdict` 的详细对照保留在[Python 参考页](http://127.0.0.1:8765/01-python-api/python-reference.html#dictionaries)。

## 安装时自动出现的其他包

`pip` 会自动安装间接依赖。当前先理解上面的直接调用即可：

- Starlette、AnyIO：提供 FastAPI 使用的 Web 与异步基础能力。
- pydantic-core 等：支撑 Pydantic 的数据校验。
- httpcore、h11、certifi、idna 等：支撑 HTTPX 的连接、HTTP、证书或域名处理。
- typing-extensions 等：提供依赖包需要的类型工具。
- setuptools、wheel、packaging：环境内的安装与打包工具；本机旧版 PyCharm 的包管理辅助脚本也用到它们。

`verify.py` 是作者核对示例的工具，额外使用标准库 `subprocess` 调起客户端并检查结果。它不是请求经过的一层。

## 对照项目阅读

第一次只记住这条路线：`client.py` 用 HTTPX 发请求 → Uvicorn 接住网络通信 → FastAPI 找到处理函数 → Pydantic 校验输入 → `business.py` 查询 → FastAPI 组织响应 → HTTPX 解析。

随后读并发演示时查 asyncio；读 SSE 时看 HTTPX 的逐行读取；读 WebSocket 时再看 websockets 的连接和消息收发。回到[项目主讲](00-one-example.md)按步骤运行即可。

## 官方资料

- [FastAPI：第一个接口](https://fastapi.tiangolo.com/tutorial/first-steps/)、[请求体模型](https://fastapi.tiangolo.com/tutorial/body/)、[WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [Pydantic：模型及校验](https://docs.pydantic.dev/latest/concepts/models/)、[严格模式](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [HTTPX：快速入门](https://www.python-httpx.org/quickstart/)、[异步客户端](https://www.python-httpx.org/async/)、[超时](https://www.python-httpx.org/advanced/timeouts/)
- [Uvicorn：启动配置](https://www.uvicorn.org/settings/)
- [websockets：异步客户端](https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html)
- [Python 3.12：异步任务](https://docs.python.org/3.12/library/asyncio-task.html)、[JSON](https://docs.python.org/3.12/library/json.html)、[TypedDict](https://docs.python.org/3.12/library/typing.html#typing.TypedDict)
