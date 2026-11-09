# 01-08 HTTPX：调用外部接口

> 教材状态：已准备。学习位置与练习状态见模块进度。更新：2026-10-22。

## 本章问题、目标与前置

07 章提供了接口；这一章让另一个 Python 服务调用它。浏览器只向“查询服务”提问，查询服务再向模拟 ERP 取数，最后把结果交回。

读完应能用 HTTPX 发送参数并读取响应，复用和关闭客户端，区分超时、连接失败、HTTP 失败与数据错误。前置：[HTTP/JSON](06-http-and-json.md)、[接口与模型](07-fastapi-and-pydantic.md)、[异步任务](05-async-and-tasks.md)。约 25–35 分钟，依赖与环境沿用 [07 §2](07-fastapi-and-pydantic.md#environment)。

## 1. 让两个程序各做一件事

第一次阅读可先读[同一次查询的两端](06-http-and-json.md#six-to-eight)，看一个 Python 脚本怎样直接请求服务。下面新增的转接服务是再向前走一步，先不用同时理解三端。

```text
curl/浏览器 → 8002 查询服务 → HTTPX → 8001 模拟 ERP
            ← 结果或失败响应 ←───────┘
```

这里把 07 章的 app_api 当成模拟 ERP，用来观察真实本机 HTTP 往返；它仍只读那两条合成金额。新增的 app_gateway 是调用方，英文 gateway 在这里表示转接请求的服务。没有引入数据库、模型或真实用友账号。

如果只想写脚本，可以先看同步调用：

```python
import httpx

# 同一上下文内复用连接，离开 with 后关闭客户端。
with httpx.Client(base_url="http://127.0.0.1:8001", timeout=5.0) as client:
    response = client.get("/customers/C001/receivable", params={"min_amount": 1000})
    response.raise_for_status()  # 先检查是否收到成功的 HTTP 状态。
    print(response.json())  # 再将响应体解析为 Python 数据。
```

这段按顺序等待请求完成，`params` 被编码到 URL，`raise_for_status()` 检查非成功状态，`json()` 将响应体解析成 Python 数据。HTTPX 收到 404 时通常先给你一个响应对象，调用 raise_for_status 才抛 HTTPStatusError；只调用 json 并不会替你判断 HTTP 成功。

POST JSON 用 `client.post("/receivables/query", json={...})`，HTTPX 会编码数据并设置相应 Content-Type。不要把 Python 字典交给 `str()` 后当成 JSON，也不要把 `data=` 的表单编码误认为 JSON。

文件 `sync_client.py` 是带错误处理的同步脚本。启动 8001 后运行：

```sh
learning/01-python-api/.venv-api/bin/python learning/01-python-api/api-lab/sync_client.py
```

预期依次打印 C001 的 12800、C002 的 0，以及 `C999 HTTP 错误 404`。这是认识客户端的短入口，下面服务端处理请求时使用 AsyncClient。

### 先认识这里出现的异常名字 {#exception-basics}

异常可以来自三个地方：Python 内置的、库定义的、项目自己定义的。机制都是异常类，`except` 按类及其继承关系匹配；名字包含 Timeout 并不意味着属于同一个类。

| 名字 | 谁提供 | 当前怎样理解 |
| --- | --- | --- |
| `TimeoutError` | Python 内置，不用导入 | 超时异常；本项目 Python 3.12 中，05 章 `asyncio.wait_for` 超时抛它 |
| `httpx.TimeoutException` | HTTPX | HTTPX 各种请求超时的父类，先用它统一捕获请求超时 |
| `httpx.ConnectError` | HTTPX | 连接建立失败，例如本地目标端口没有服务监听；失败不一定需要等满超时时间 |
| `httpx.RequestError` | HTTPX | 请求过程的较大类，包含超时、连接失败等情况 |
| `httpx.HTTPStatusError` | HTTPX | 已收到响应，调用 `raise_for_status()` 后，因非成功状态而抛出 |
| `UpstreamTimeoutError` | 本项目在下一节定义 | 将 HTTPX 的超时转换成项目自己的“ERP 查询超时”异常 |

**`TimeoutError` 和 `httpx.TimeoutException` 是不同的类。** HTTPX 的超时不属于内置 TimeoutError；要接住 HTTPX 请求超时，写 `except httpx.TimeoutException`。05 章对整个异步等待设置的 `asyncio.wait_for` 超时，则写 `except TimeoutError`。两者都可以最终被 `except Exception` 捕获。

先给同一个同步查询加上错误处理：

```python
import httpx

try:
    with httpx.Client(base_url="http://127.0.0.1:8001", timeout=5.0) as client:
        response = client.get("/customers/C001/receivable")
        response.raise_for_status()
        print(response.json())
except httpx.TimeoutException as error:
    print("请求超时：", error)
except httpx.RequestError as error:
    print("其他请求故障，例如连接失败：", error)
except httpx.HTTPStatusError as error:
    print("收到非成功状态：", error.response.status_code)
```

这些 except 分支按顺序匹配，本次异常只进入第一个匹配的分支。超时属于 RequestError，单独的超时处理要放在它前面。`as error` 仍是给本次异常对象取变量名。

若要看更细的超时原因，HTTPX 还区分 ConnectTimeout（连接）、ReadTimeout（接收数据）、WriteTimeout（发送数据）、PoolTimeout（等待客户端可用连接）；它们都能被 TimeoutException 接住，当前不要求分别写处理分支。读取超时是等待下一块数据超时，不是限定整个响应必须在五秒内接收完。

无需提前背全每个库的所有异常；引入一个操作时，同时认识该操作常见的失败和捕获方式。先读懂上面这段，再往下看项目怎样把 HTTPX 异常转成自己的异常。

依据：[HTTPX 异常分类](https://www.python-httpx.org/exceptions/)、[HTTPX 超时阶段](https://www.python-httpx.org/advanced/timeouts/)、[Python 3.12 wait_for](https://docs.python.org/3.12/library/asyncio-task.html#asyncio.wait_for)。2026-10-30 核实。

## 2. 一个异步调用函数怎样明确成功与失败

`erp_client.py` 是之后 09/10 继续复用的取数边界。相比上面的短代码，它增加异常分类与返回模型校验，调用方式不再复制到每个路由里：

```python
import httpx
from domain import CustomerNotFoundError
from models import Receivable


class UpstreamTimeoutError(TimeoutError):
    pass


class UpstreamError(Exception):
    pass


async def fetch_receivable(
    client: httpx.AsyncClient, customer_id: str, *, min_amount: int | None = None
) -> Receivable | None:
    # 不传 None 给查询参数；设置为 0 时则确实发送门槛 0。
    params = {} if min_amount is None else {"min_amount": min_amount}
    try:
        # 复用传入的客户端，异步等待上游响应，不在每次调用时新建连接池。
        response = await client.get(
            f"/customers/{customer_id}/receivable", params=params
        )
        response.raise_for_status()  # 收到 404/500 等响应后，显式转成 HTTP 异常。
    # 超时属于 RequestError，先捕获它以便上层单独返回 504。
    except httpx.TimeoutException as error:
        raise UpstreamTimeoutError("ERP 查询超时") from error
    except httpx.RequestError as error:
        raise UpstreamError("无法连接 ERP 接口") from error
    except httpx.HTTPStatusError as error:
        # 此处的业务解释依据本教材固定端点的约定。
        if error.response.status_code == 404:
            raise CustomerNotFoundError("客户不存在") from error
        raise UpstreamError(f"ERP 返回 HTTP {error.response.status_code}") from error

    try:
        # 先解析 JSON，再核对字段；HTTP 200 不保证数据符合模型。
        data = response.json()
        return None if data is None else Receivable.model_validate(data)
    # JSON 解析错误和 Pydantic 校验错误均属于 ValueError。
    except ValueError as error:
        raise UpstreamError("ERP 响应不符合约定") from error
```

沿执行顺序看：先 await 发请求，检查状态，再解析 JSON，最后用已学的 Receivable 模型核对字段。成功对象转成模型，JSON null 转成 None，0 元保留为合法结果。JSONDecodeError 与 Pydantic ValidationError 都属于 ValueError，因此解析/校验一段统一捕获它。遇到错误向上层抛专用异常，由调用方决定用 HTTP 状态或流内消息表达。

| 失败位置 | HTTPX / 解析层表现 | 本例向上层交出的异常 |
| --- | --- | --- |
| 等待超过 HTTPX 配置 | TimeoutException | UpstreamTimeoutError |
| 连接拒绝、网络等请求故障 | 其他 RequestError | UpstreamError |
| 收到非成功响应 | raise_for_status 抛 HTTPStatusError | 约定 404 为 CustomerNotFoundError，其余 UpstreamError |
| 成功状态但 JSON 或字段错误 | JSON 解析或模型校验失败 | UpstreamError |

TimeoutException 属于 RequestError，所以先捕获它，才不会被更大的类别提前接住。`raise ... from error` 保留原始原因，机制回查 [03 §3](03-errors-and-debugging.md#3)，这里不重复异常语法。[HTTPX 异常文档](https://www.python-httpx.org/exceptions/)列出了这些类别。

本例将固定查询端点的 404 解释为客户不存在，依据是我们自己在 07 章定义的接口契约。接其他服务时先核对其文档，错误路径、权限隐藏等原因也可能返回 404，不能把所有上游 404 都机械解释为同一种业务失败。

## 3. 客户端由谁创建、怎样复用和关闭

如果每次查询都创建一个新客户端，就无法充分利用连接池。连接池保留可复用的网络连接，多次请求时不必每次重新建立连接。因此本例在应用启动时创建 AsyncClient，同一进程的多次查询共用它，在应用停止时关闭。[HTTPX 客户端](https://www.python-httpx.org/advanced/clients/)与[异步用法](https://www.python-httpx.org/async/)是这项安排的依据。

完整的 `app_gateway.py`：

```python
import os
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable
from models import QueryInput, Receivable



# 应用启动时创建共享客户端，停止时通过 async with 关闭它。
@asynccontextmanager
async def lifespan(app: FastAPI):
    base_url = os.getenv("ERP_BASE_URL", "http://127.0.0.1:8001")
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        app.state.erp_client = client  # 保存给本应用的各次请求复用。
        yield  # 应用在这里运行；关闭应用时才继续离开资源上下文。



# 依赖函数读取应用上的客户端；它不是用户请求体中的一个字段。
def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.erp_client


app = FastAPI(title="应收查询调用方", lifespan=lifespan)


@app.post("/receivables/query", response_model=Receivable | None)
async def query_remote(
    query: QueryInput,
    # FastAPI 调用 get_client，再把得到的对象作为 client 参数传入。
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
):
    try:
        return await fetch_receivable(
            client, query.customer_id, min_amount=query.min_amount
        )
    # 在当前 HTTP 边界决定怎样向调用者表达不同失败。
    except CustomerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UpstreamTimeoutError as error:
        # 上游等待超时，与客户不存在分别处理。
        raise HTTPException(status_code=504, detail=str(error)) from error
    except UpstreamError as error:
        # 上游连接、状态或格式失败，不能伪装成金额 0。
        raise HTTPException(status_code=502, detail=str(error)) from error
```

先看 lifespan：它描述应用的启动和关闭阶段。`@asynccontextmanager` 让异步函数成为资源上下文，yield 前执行启动工作，应用运行期间暂停在 yield，关闭时离开 async with，关闭客户端。这个 yield 在这里划分资源的生命周期，不向浏览器发送进度。

`app.state.erp_client` 是在应用对象上保存共享客户端。`get_client(request)` 读取它；`Depends(get_client)` 告诉 FastAPI：处理这次请求前调用这个函数，并把返回值交给 client 参数。这就是这里的依赖注入，先理解为“由框架取得并传入需要的对象”。客户端不是从用户的 JSON 中传来的。后面多个入口复用这套资源安排，不再各建一个客户端。

服务调用结果映射为：客户不存在→404，上游超时→504，上游连接/HTTP/格式失败→502。输入模型仍会在进入路由前检查，422 的机制沿用 07 章。

### 3.1 5 秒超时到底限制什么

`timeout=5.0` 设置 HTTPX 各类网络等待的超时，包含连接、读取、写入和等待连接池。它不等于整次业务请求严格只能运行 5 秒，例如连续读到数据的长响应可以持续更久。需要整个操作的总时限时，再用 [05 章的 wait_for](05-async-and-tasks.md#3) 包住调用；客户端网络超时和任务总时限各自控制不同的等待范围。[HTTPX 超时说明](https://www.python-httpx.org/advanced/timeouts/)给出了这些类别。

本例不自动重试。一旦增加重试，需要明确哪些错误可重试、次数和总时限；具有写入效果的操作还要检查是否可能重复执行。当前查询可以先用明确失败学会定位，无需先搭建通用重试框架。

## 4. 两个终端跑通一次完整查询

以下均在项目根目录。终端 A 保持 07 章接口运行：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_api:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8001
```

终端 B 启动调用方：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_gateway:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8002
```

第三个终端请求 8002，或在 `http://127.0.0.1:8002/docs` 试 POST 接口：

```sh
curl -i -X POST 'http://127.0.0.1:8002/receivables/query' -H 'Content-Type: application/json' -d '{"customer_id":"C001","min_amount":1000}'
```

得到 `200` 与 `{"customer_id":"C001","amount":12800}`。8002 先校验输入，再经 HTTPX 请求 8001，8001 计算结果；回复沿原路返回。两个端口各自的访问日志能看到这次调用。

然后将编号改为 C999，得到 404。将编号改为 C002 并设置门槛 1，得到 200 与 null。最后在终端 A 按 Ctrl+C 停止模拟 ERP，再请求 8002 的 C001，此时 8002 仍能回应，但应返回 502 和“无法连接 ERP 接口”。这与直接访问停止的 8001 时连接被拒绝不同：前者还有调用方服务替你生成 HTTP 响应。

要更换模拟 ERP 地址，在启动 8002 的命令前加 `ERP_BASE_URL=http://127.0.0.1:新端口`，并保证对应服务在新端口启动。环境变量由启动时读取，改动后需重启调用方。

## 5. 排错与可选练习

在 async 路由里用 `await client.get(...)` 等待异步网络调用；`response.json()` 与 `raise_for_status()` 本身不用 await。不要在每次请求里调用 asyncio.run，事件循环已经由服务管理。同步 HTTPX Client 可以用于普通脚本；在 async 函数里直接调用同步网络方法会阻塞事件循环，参见 [05 章](05-async-and-tasks.md#4)。

**练习条件：** 仍使用 8001 与 8002 两个服务，客户与门槛规则不变。

1. 8001 未启动，8002 是否应该返回 `{"amount":0}`？解释这会错误表达什么。
2. 上游返回 200，但 amount 为 `"abc"`，失败发生在哪一步，本例最终返回什么 HTTP 状态？
3. 希望同时查 C001/C002，应复用一个 AsyncClient 还是各建一个？如何用 05 章知识组织调用？

??? note "参考答案与依据"
    1. 不应该。无法取数不能说明存在这个客户且金额为 0，本例返回 502。
    2. Receivable.model_validate 校验失败，转成 UpstreamError，8002 映射为 502。
    3. 在同一生命周期内复用一个客户端，可将两次 fetch_receivable 放入 asyncio.gather。结果按参数顺序收集；批量规模大时再限制并发数，当前不增加大量任务。

## 本章回顾与检查清单

本章将“取数据”换成真实 HTTP 往返：客户端负责请求与连接，模型核对返回数据，调用方将明确失败映射成自己的响应。

- [ ] 能从 8002 的一次请求追踪到 8001，再追踪回来。
- [ ] 能区分 RequestError、HTTPStatusError 与结构校验失败。
- [ ] 能说明客户端创建、复用与关闭的时机。

## 阅读中产生的答疑

暂无。依赖注入和应用生命周期的最小解释集中在本章 §3，09/10 直接复用。

## 资料与后续

同步脚本、真实 HTTP 往返、错误映射及模型失败已核对，故障注入方法见配套 verification.py 与验证报告。资料核实：2026-10-22。[HTTPX 客户端](https://www.python-httpx.org/advanced/clients/) · [异步调用](https://www.python-httpx.org/async/) · [超时](https://www.python-httpx.org/advanced/timeouts/) · [FastAPI 生命周期](https://fastapi.tiangolo.com/advanced/events/) · [依赖注入](https://fastapi.tiangolo.com/tutorial/dependencies/)。

[上一章：FastAPI 与 Pydantic](07-fastapi-and-pydantic.md) · [下一章：流式与 SSE](09-streaming-and-sse.md) · [返回目录](index.md)
