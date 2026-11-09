# 01 复习：先站在客户端，再站在服务端

> 2026-10-31。用户已报告读完 01，本页按两端重新组织已有知识。它是复习路线，不增加新框架；阅读完成与独立实践验证分开记录。

本页解决的问题：面对一段代码，先判断它在哪一端，再跟踪数据怎样发送、接收和处理。前置为 01–10 的阅读；不需要先运行全部项目。金额仍为合成人民币整数元，C001=12800、C002=0；未知客户和未达到门槛分别处理。

固定角色：**客户端 A 主动访问；服务端 B 提供入口并接受访问。** 两者可以都用 Python，也可以是浏览器与 Python。服务端回消息时仍然是服务端，不因发送数据就改名为客户端。

```text
客户端 A ──请求或建立连接──→ 服务端 B
客户端 A ←──响应或消息──── 服务端 B
```

## 第一遍：我是客户端 A {#client}

### 1. 我想查客户欠款：普通 HTTP

我已经知道服务端 B 的地址和接口约定。我的任务是准备条件、发请求、检查响应，再读取结果。

**【客户端 A】下面片段从已启动的 07 章服务取数；完整脚本见 sync_client.py。**

```python
import httpx

with httpx.Client(base_url="http://127.0.0.1:8001", timeout=5.0) as client:
    response = client.get(
        "/customers/C001/receivable",
        params={"min_amount": 1000},
    )
    response.raise_for_status()  # 发现非成功状态时抛异常。
    data = response.json()      # JSON 响应正文 → 当前程序的 Python 数据。
    print(data)                 # {'customer_id': 'C001', 'amount': 12800}
```

`Client(...)` 创建访问工具，共用地址和连接配置；`get(...)` 才发请求。GET 的路径和 params 变成 URL；若接口约定用 POST 请求体，则用 `post(..., json={...})`。HTTPX 编码和发送 JSON，不能把 JSON 格式转换本身当作网络发送。

如果还要确认收到的数据符合约定，可以用 `Receivable.model_validate(data)`；它是 Pydantic 的校验方法。收到 null 并解析成 None 时，应按接口约定先处理这个分支。模型不仅可以检查服务端收到的输入，也可以检查客户端收到的结果。

失败处理也发生在客户端：TimeoutException 表示 HTTPX 操作超时，其他 RequestError 可表示连接等请求故障；HTTPStatusError 表示收到非成功响应并执行了 raise_for_status。详细分支回查 [08 异常说明](08-httpx-and-upstream.md#exception-basics)。

### 2. 我想边等边看到结果：接收 SSE

**【客户端 A】我请求服务端 B 的 SSE 入口，保持这次响应的读取。**

客户端读取的仍然是服务端返回的 HTTP 响应体，只是逐步读取，而不是等完整响应结束后再处理。

- Python 客户端：HTTPX 的 `client.stream(...)` 打开流，`response.aiter_lines()` 逐行读取。
- 浏览器客户端：可以用 EventSource 接收 SSE 事件。
- 内容中空行分隔事件；`data:` 是数据行，`event:` 可以指定事件名。一次网络读取或一次 yield 不等于一条事件。
- 读取到项目约定的 done 事件后结束并关闭；异常断流且没有完成标记，不当作成功完成。done 是本例业务约定。

在大模型例子中，客户端收到一段文字，就追加到当前回答中。长回答与短回答各有自己的请求和状态；若允许同时发起两次请求，分别更新各自的回答，不把不同回复拼在一起。

### 3. 我想持续发送多条消息：WebSocket 客户端

**【客户端 A】我主动连接服务端 B 的 WebSocket 地址。**

```text
连接 ws://127.0.0.1:8004/ws
    → 发送 C001 查询
    ← 收到 C001 结果
    → 发送 C002 查询
    ← 收到 C002 结果
    → 正常关闭连接
```

Python 客户端可以使用 `websockets` 库的 connect、send、recv；浏览器有自带的 WebSocket 对象。路径 `/ws` 是我们取的入口名字，前面的 `ws://` 则表示 WebSocket 协议；加密连接使用 wss://。

建立后，客户端和服务端都可以主动发送。当前最小例子是一问一答，协议本身不要求每次必须先问再回。

## 第二遍：我是服务端 B {#server}

### 1. 别人来查欠款：普通 HTTP

**【服务端 B】我提供地址和处理规则。** Uvicorn 监听端口，FastAPI 保存路由、解析输入并组织响应。

```text
收到 GET /customers/C001/receivable?min_amount=1000
    → FastAPI 按方法和路径找到 @app.get 对应函数
    → 取出 customer_id 与 min_amount，按声明校验
    → 业务函数查询合成数据
    → 返回字典
    → FastAPI 组织 JSON 响应，发给客户端 A
```

POST 的多字段输入使用 `query: QueryInput`，让 Pydantic 从请求体数据创建并校验模型。输入不合要求通常在进入业务函数前返回 422；客户不存在由业务判断，在接口边界转换成 404。

返回字典不是服务端用 HTTPX 再发一次请求；这是对客户端原来那次请求作出响应。业务函数仍是普通 Python：类型标注描述约定，类可以保存状态，raise 表达失败，try/except 决定怎样处理。

完整可运行入口与模型在本模块学习目录的 api-lab/app_api.py、models.py、domain.py，解释见 [07](07-fastapi-and-pydantic.md)。

### 2. 我想逐步给对方结果：提供 SSE

**【服务端 B】我保留一次 HTTP 响应，逐条产生并发送内容。**

```python
# 本段只展示服务端核心；app 与 StreamingResponse 的导入沿用 09 章。
def generate():
    yield "data: 正在查询\n\n"
    yield "data: 查询完成\n\n"

@app.get("/events")
def events():
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
```

- yield 交出一段内容并暂停，下一次取值时继续。
- StreamingResponse 消费生成器，把内容作为响应逐段发送；不用先收集完整内容。
- SSE 内容用 data 等字段和空行组织事件，text/event-stream 声明这种媒体类型。
- media_type 是 Python 参数；框架据此设置 HTTP 的 Content-Type 响应头。headers 字典可以补其他响应头。
- Cache-Control: no-cache 允许保存，但再次使用缓存前需要向服务器确认；它不是禁止存储的 no-store。

上面的两段会很快产生，没有模拟等待。实际接模型回复时，服务端可能用 `async for chunk in llm_stream` 接一段、再 yield 一段。这时它对前端提供 SSE，同时对模型提供方承担客户端角色；这个角色切换单独见下节，不改变前端看到的服务端身份。

SSE 是流式的一种；StreamingResponse 也能发送普通文本或音频。即使声明了媒体类型，内容也必须按对应格式产生。详细边界和断流处理回查 [09](09-streaming-and-sse.md)。

### 3. 对方想持续发消息：WebSocket 服务端

**【服务端 B】我登记入口并接受连接，然后在该连接上收发消息。**

```text
@app.websocket("/ws") 登记入口
    → websocket.accept() 接受客户端 A 的连接
    → receive_text() 等一条消息
    → 校验这条消息，调用业务函数
    → send_json(...) 回复
    → 继续接收下一条
    → 断开时退出并清理
```

这里不使用 StreamingResponse，也不要求 SSE 的 data 行和空行。WebSocket 有自己的消息边界；若消息内容采用 JSON，仍然需要编码、解析和逐条校验。已建立连接里的业务失败由约定的失败消息表达；连接断开、业务失败、任务取消分别处理。

WebSocketDisconnect 是框架提供的断开异常；库提供的异常和我们自己定义的异常一样，按类型用 except 匹配。参见 [10](10-websocket-and-selection.md)。

## 最后才加这一层：服务端 B 也可以成为客户端 {#role-switch}

```text
浏览器 A ──→ 我们的服务 B ──HTTPX──→ ERP 服务 C
```

- 看 A ↔ B：A 是客户端，B 是服务端。
- 看 B ↔ C：B 是客户端，C 是服务端。

B 内部写 `@app.get` 是为了接 A 的请求；在处理函数里写 `await client.get(...)` 是为了查询 C。前面教材经常在这两条通信之间切换，这是产生混淆的关键；以后每段代码都先标角色和通信对象。

## 两端共用的基础能力 {#shared}

| 内容 | 放回两端怎样理解 |
| --- | --- |
| HTTP / JSON | HTTP 约定通信方式；JSON 表达数据，两端分别编码与解析 |
| Pydantic | 服务端检查输入，客户端也可检查收到的结果 |
| 类型、类、函数 | 在两端各自组织数据和业务，不决定通信角色 |
| raise / try / except | 在本程序内表达和处理失败；异常对象不会自动传到另一程序，需转换成响应或消息 |
| async / await | 等网络或下一段内容时可让其他已安排任务运行；两端都可以使用 |
| async for | 逐项异步读取；不会自动把多项变成并发 |
| gather / create_task | 显式安排任务并发；同一回复流仍有自己的处理顺序 |
| 模块、环境、入口、with | 两端各自启动并管理资源；import 不等于启动监听 |

## 自查与回读

先按两遍顺序复述，不要求立即写完整项目：

1. 我看到 `client.post(..., json=...)`，它在当前通信的哪一端？
2. 我看到 `@app.post(...)` 后函数 return 字典，这是新发请求，还是回复已有请求？
3. 我们的 FastAPI 服务调用模型，再把模型片段转成 SSE，它对哪边是客户端、对哪边是服务端？

??? note "参考答案"

    1. 发请求的客户端。
    2. 对已有请求返回响应。
    3. 对模型服务是客户端，对前端是服务端。上游片段逐步接收，再逐步交给下游响应。

阅读位置：本页是 01 阅读后的双视角复习。遇到具体机制，再回到 [08 HTTPX](08-httpx-and-upstream.md)、[09 SSE](09-streaming-and-sse.md)、[10 WebSocket](10-websocket-and-selection.md) 的对应位置，无需重新串读整套章节。

[返回模块目录](index.md)
