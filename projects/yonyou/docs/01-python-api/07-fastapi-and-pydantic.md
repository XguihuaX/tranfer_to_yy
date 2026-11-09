# 01-07 FastAPI 与 Pydantic：提供查询接口

> 教材状态：已准备。学习位置与练习状态见模块进度。更新：2026-10-22。

## 本章问题、目标与前置

本章把已有查询函数接到 HTTP：接收编号和门槛，校验输入，调用业务逻辑，返回 JSON 或明确错误。读完应能辨认路由、路径/查询/请求体参数，解释 Pydantic 与 TypedDict 的差别，并实际观察 200、404、422。

前置：[类型约定](02-types-and-contracts.md)、[异常](03-errors-and-debugging.md)、[模块组织](04-modules-and-project.md)、[HTTP 与 JSON](06-http-and-json.md)。约 25–35 分钟，可先读代码再运行。认证、数据库和部署分属后续模块，本章使用本机合成数据。

## 1. 三个工具各自负责哪一步

若还没看清 06–08 的关系，先读[同一次查询的两端](06-http-and-json.md#six-to-eight)。当前先看收到 GET 后怎样调用函数，模型与工程安排在这条路线清楚后展开。

**FastAPI** 按请求方法和路径选择 Python 函数，解析输入并组织响应。这样的“方法＋路径→处理函数”规则称为路由。**Pydantic** 根据字段声明创建模型对象，并在创建时校验数据。**Uvicorn** 负责监听端口、接入网络请求，再交给 FastAPI 应用处理；只创建 `FastAPI()` 不会自行开始监听。

```text
HTTP 请求 → Uvicorn → FastAPI 解析与校验 → 业务函数
HTTP 响应 ←──────── FastAPI 编码与响应模型 ← 查询结果
```

最小路由长这样（完整应用在 §4）：

```python
app = FastAPI()

# 把 GET 路径登记给这个函数，花括号中的编号传给同名参数。
@app.get("/customers/{customer_id}/receivable")
def get_receivable(customer_id: str):
    return query_receivable(customer_id)  # 框架将结果编码为响应。
```

`@app.get(...)` 把这个函数登记为 GET 入口；花括号部分是路径参数。函数名不会决定访问地址，装饰器里的路径才会。普通 `def` 适合这里的短业务调用；FastAPI 会在线程池执行同步路由。[同步与异步路由的运行安排](https://fastapi.tiangolo.com/async/#path-operation-functions)见官方说明。本例没有网络等待，改成 async 并不会多出查询能力；08 章有异步 HTTP 调用时再使用 `async def`。

## 2. 一次性准备 07–10 的运行环境 {#environment}

运行条件是 Python 3.12；本轮验证版本为 FastAPI 0.159.1、Pydantic 2.14.1、Uvicorn 0.54.0、HTTPX 0.28.1、websockets 17.3。HTTPX 到 08 章才使用，websockets 为 Uvicorn 提供 WebSocket 协议支持；现在一次安装，后面不再重复。

在项目根目录运行，所有命令都从该目录执行：

```sh
python3.12 -m venv learning/01-python-api/.venv-api
learning/01-python-api/.venv-api/bin/python -m pip install -r learning/01-python-api/api-lab/requirements.lock.txt
```

若本机没有 `python3.12` 命令，可用 `python3 --version` 核实版本；本项目已有的 `.venv-docs/bin/python` 是 Python 3.12，也可以用它执行上面第一条的 `-m venv`。07–10 共用这一套练习环境，文档站仍使用原来的文档环境。

文件都已准备在 `learning/01-python-api/api-lab/`。本章先看 `domain.py`、`models.py`、`app_api.py`；其余文件后面按章使用。数据始终是 C001=12800 元、C002=0 元，人民币整数元，不连接真实用友系统。

## 3. 运行时校验：模型怎样落实约定

### 先看一个小模型：字段、类型和条件 {#pydantic-basics}

你说“用来限制值的条件”是其中一部分。Pydantic 是一个数据校验库：先声明一份数据应有哪些字段、各是什么类型、有哪些值的限制，再在创建模型时实际检查输入。检查通过后，得到一个可以按属性读取的数据对象。

```python
from pydantic import BaseModel, Field

class CustomerQuery(BaseModel):
    customer_id: str  # 必须有编号，值应为字符串。
    min_amount: int | None = Field(default=None, ge=0, strict=True)

query = CustomerQuery(customer_id="C001", min_amount=1000)
print(query.customer_id, query.min_amount)  # C001 1000
```

这里 `customer_id: str` 约定字段及类型，`ge=0` 要求门槛不小于 0，`strict=True` 拒绝把字符串数字当整数接收，`default=None` 表示省略时不设置门槛。创建时传 -1、传字符串 "1000"，或漏掉必填 customer_id，都会抛 ValidationError。普通类型标注本身不做这种检查，Pydantic 模型创建时才实际落实这些约定。

独立运行例子是 `learning/01-python-api/whole-example/pydantic_basics.py`，包含成功和失败输出，可在 PyCharm CE 中直接运行。2026-10-28 已为 whole-example 创建项目内 `.venv`，安装本章依赖并切换项目解释器至 Python 3.12；原共享环境命令仍然有效。

接入接口时，FastAPI 按这个模型检查请求输入；输入不符合约定通常返回 422，合法模型再交给你的函数。客户编号是否真实存在则由业务查询判断。未开启严格模式的一些字段会进行兼容的类型转换，具体由字段配置决定。[Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/)与[严格模式](https://docs.pydantic.dev/latest/concepts/strict_mode/)说明了这些行为。

下面回到本章的完整模型，它还增加客户编号格式、额外字段处理和返回结构。

下面是完整 `models.py`：

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt


# 接口新增的编号格式：C 后恰好三位数字。
CustomerId = Annotated[str, Field(pattern=r"^C[0-9]{3}$")]

# 金额非负且必须是整数，拒绝字符串数字和布尔值。
Amount = Annotated[StrictInt, Field(ge=0)]


class QueryInput(BaseModel):
    # 拒绝多余字段，避免把 min_amout 之类的拼写错误静默忽略。
    model_config = ConfigDict(extra="forbid")
    customer_id: CustomerId
    min_amount: Amount | None = None  # 省略或传 null 时，不设置门槛。



# 成功结果的结构；供服务端输出和客户端解析共同使用。
class Receivable(BaseModel):
    customer_id: CustomerId
    amount: Amount
```

`BaseModel` 提供字段校验与数据转换能力。`QueryInput(customer_id="C001")` 创建一个模型实例，随后用 `query.customer_id` 读取属性。02 章的 TypedDict 仍返回普通字典、标注不自行执行检查；这里创建模型就会执行检查，校验失败抛 `ValidationError`。[Pydantic 模型文档](https://docs.pydantic.dev/latest/concepts/models/)解释了构造与转换行为。

`Annotated[类型, 规则]` 把类型和额外规则写在一起；`Field` 表达字段约束。`pattern` 是编号格式，本例要求 C 后恰好三位数字，这是本章接口**新增**的演示规则；02 章普通函数原来只去两端空白并拒绝空字符串。接口这里不自动去空白，所以 `" C001 "` 会被拒绝。

`ge=0` 表示大于或等于 0。`StrictInt` 让 JSON 请求体中的金额必须真的是整数，拒绝 `"1000"` 和 `true`，与 02 章函数的金额检查一致。一般 `int` 字段默认会尝试转换一些兼容输入，严格模式用于需要保留类型要求的字段。`extra="forbid"` 拒绝拼错或多余字段，比如 `min_amout`，避免误以为筛选已经生效。[严格模式说明](https://docs.pydantic.dev/latest/concepts/strict_mode/)给出了转换差别。

`model_dump()` 将模型转成 Python 字典，`model_dump_json()` 生成 JSON 字符串；`model_validate(data)` 校验已有 Python 数据，`model_validate_json(text)` 校验 JSON 文本。这里先创建输入模型，08 和 10 分别会使用后两种入口，不再另讲模型基础。

## 4. 业务逻辑怎样接进路由

业务文件 `domain.py` 沿用 02 章的校验、门槛和返回结构，只将“客户不存在”的 ValueError 改为 03 章的专用异常，供接口准确映射：

```python
"""沿用 01-02 的业务规则，未知客户改用 01-03 的专用异常。"""
from typing import TypedDict


class ReceivableResult(TypedDict):
    customer_id: str
    amount: int


class CustomerNotFoundError(LookupError):
    pass


balances = {"C001": 12800, "C002": 0}


def query_receivable(
    customer_id: str, *, min_amount: int | None = None
) -> ReceivableResult | None:
    # 先检查类型，再调用字符串方法；沿用 02 章的业务规则。
    if not isinstance(customer_id, str):
        raise TypeError("customer_id 必须是字符串")
    customer_id = customer_id.strip()
    if not customer_id:
        raise ValueError("customer_id 不能为空")
    # None 表示不筛选；整数 0 是一个有效的门槛，不能一起跳过。
    if min_amount is not None:
        if type(min_amount) is not int:
            raise TypeError("min_amount 必须是整数或 None")
        if min_amount < 0:
            raise ValueError("min_amount 不能为负数")
    # 未知客户明确失败，不能与已知客户的零金额混为一谈。
    if customer_id not in balances:
        raise CustomerNotFoundError("客户不存在")
    amount = balances[customer_id]
    if min_amount is not None and amount < min_amount:
        return None  # 客户存在，但本次未命中筛选条件。
    return {"customer_id": customer_id, "amount": amount}
```

完整 `app_api.py` 如下。它是本章唯一的 HTTP 应用，GET 和 POST 调用同一个业务入口：

```python
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query

from domain import CustomerNotFoundError, query_receivable
from models import QueryInput, Receivable

app = FastAPI(title="合成 ERP 应收接口")



# GET 与 POST 共用业务调用，只在接口边界把业务异常映射为 HTTP。
def resolve(customer_id: str, min_amount: int | None):
    try:
        return query_receivable(customer_id, min_amount=min_amount)
    except CustomerNotFoundError as error:
        # from error 保留原始原因；404 和 detail 交给框架生成响应。
        raise HTTPException(status_code=404, detail=str(error)) from error



# 注册 GET 入口；response_model 约束成功结果，也允许未命中的 null。
@app.get("/customers/{customer_id}/receivable", response_model=Receivable | None)
def get_receivable(
    # 编号来自 URL 路径；门槛来自问号后的查询参数。
    customer_id: Annotated[str, Path(pattern=r"^C[0-9]{3}$")],
    min_amount: Annotated[int | None, Query(ge=0)] = None,
):
    return resolve(customer_id, min_amount)


@app.post("/receivables/query", response_model=Receivable | None)
def post_receivable(query: QueryInput):
    # JSON 请求体先按 QueryInput 校验，成功后才执行这里的业务调用。
    return resolve(query.customer_id, query.min_amount)
```

输入来源由定义决定：

| 定义位置 | 来自哪里 | 例子 |
| --- | --- | --- |
| 路径中的 `customer_id`，用 `Path` 限制 | URL 路径 | `/customers/C001/receivable` |
| `min_amount`，用 `Query` 限制 | 查询字符串 | `?min_amount=1000` |
| `query: QueryInput` | JSON 请求体 | `{"customer_id":"C001","min_amount":1000}` |

URL 查询参数本来是文本，因此 GET 的 `1000` 由 FastAPI 解析为整数；本例没有对 Query 使用 StrictInt，否则正常的 URL 数字文本也可能被拒绝。POST 请求体本来能表达 JSON 数字，所以按 §3 的严格规则检查。这两个入口的业务筛选一致，输入表示的解析规则不同。

FastAPI 发现输入不合法时返回默认的 422，路由函数和业务查询不执行。合法输入进入 `resolve`，未知客户被转换成 `HTTPException(404, detail=...)`；它通知框架生成 HTTP 错误响应，不会直接暴露 Python 异常对象。

`response_model=Receivable | None` 声明成功结果可为模型或 null；FastAPI 会校验和过滤输出字段。若业务意外返回 `{"amount":"乱写"}`，那是服务端违反返回约定，通常产生 500，应查服务端日志，不能归为用户输入的 422。输出字段过滤也不代替业务授权；本例没有账号与权限流程。[响应模型](https://fastapi.tiangolo.com/tutorial/response-model/)与[错误映射](https://fastapi.tiangolo.com/tutorial/handling-errors/)是本节的官方参考。

## 5. 启动与核对完整结果

在项目根目录开一个终端：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_api:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8001
```

`app_api:app` 表示导入 app_api 模块并读取其中的 app；`--app-dir` 将示例目录加入导入位置。服务持续运行，终端里的 Ctrl+C 才结束。另一个终端发请求，或访问 `http://127.0.0.1:8001/docs`，点击接口、Try it out、Execute。这个自动接口页可查看模型字段与响应，8765 仍是教材站。

```sh
curl -i 'http://127.0.0.1:8001/customers/C001/receivable?min_amount=1000'
curl -i 'http://127.0.0.1:8001/customers/C002/receivable?min_amount=1'
curl -i 'http://127.0.0.1:8001/customers/C999/receivable'
curl -i -X POST 'http://127.0.0.1:8001/receivables/query' -H 'Content-Type: application/json' -d '{"customer_id":"C001","min_amount":1000}'
```

依次得到 200＋C001 的结果、200＋null、404＋客户不存在、200＋C001 的结果。JSON 空格与响应头顺序可能不同，关注值和状态。POST 中将金额改成 `"1000"`、`true` 或负数，都会得到 422；将客户改成 C999 则是 404。客户端输入校验与客户存在性检查发生在不同步骤。

| 运行现象 | 先检查哪里 |
| --- | --- |
| connection refused | 8001 服务是否仍运行、端口是否正确 |
| 404 | 路径拼错，还是正确路径返回的客户不存在；看响应体 |
| 405 Method Not Allowed | 路径存在，但 GET/POST 方法不匹配 |
| 422 | 响应 detail 中的字段位置、类型与约束 |
| address already in use | 该端口已有进程；不要重复启动同一服务 |

## 6. 可选练习

条件：服务保持运行，C001=12800、C002=0，使用本章 models.py。

1. POST `{"customer_id":"C002","min_amount":0}`，再把 0 改为 1，结果各是什么？
2. 把字段误写为 `min_amout`，会直接忽略它吗？
3. 希望成功结果多一个币种字段 CNY，应该同时改哪些位置？

??? note "参考答案与依据"
    1. 先得到 200 和金额 0 的对象，再得到 200 和 null。
    2. 不会，extra=forbid 导致 422；请求未进入业务函数。
    3. 业务成功结果与 Receivable 输出模型都增加 currency；如继续使用 TypedDict，也更新 ReceivableResult。若只加返回字典而不改响应模型，多余字段会被响应模型过滤。失败和未命中分支保持原约定。

## 本章回顾与检查清单

接口层确定输入来自哪里、怎样校验、怎样映射 HTTP；业务层保留客户查找与门槛含义。模型把字段约定变成运行时行为。

- [ ] 能沿 GET 和 POST 各追踪一次输入到业务再到响应。
- [ ] 能区分标注、Pydantic 输入校验和响应模型。
- [ ] 能解释 0、null、404 与 422 分别来自哪一步。

## 阅读中产生的答疑

### 常用写法与商业项目选择 {#practical-usage}

现在先学四个动作：用 `@app.get/post` 登记入口；从路径、查询参数或 Pydantic 请求体获取输入；`return` 返回结果；`raise HTTPException(...)` 返回明确的 HTTP 失败。前面的 §1、§3、§4 已有代码，按一次请求逐项看即可。完整库调用查[项目库用法](00-project-libraries.md)，暂不同时展开所有功能。

FastAPI 确实用于商业项目。官方首页收录了 Uber 的 Ludwig 预测接口、Netflix 的 Dispatch 等实际采用案例，说明它可以承担真实应用中的接口服务。[FastAPI 官方采用案例](https://fastapi.tiangolo.com/#opinions)（2026-10-29 核实）。

选框架要结合服务职责与现有工程。面向 Python 的模型预测、AI 应用或数据查询接口，FastAPI 是合理选择；若需要配套的用户管理、后台管理页面与数据库工具，可评估自带这些能力的 [Django](https://www.djangoproject.com/start/overview/)。已有项目通常还需考虑团队熟悉的框架和运维方式。商业系统可以让不同服务使用不同框架，通过 HTTP 等接口协作，无需整个系统只选一种。

商业化还需补上访问权限、真实数据连接、日志监控、测试与部署。本章先完成最小接口；这些要求随实际任务逐步加入。

TypedDict 的声明和类的选择仍以 [02 §4](02-types-and-contracts.md#4-typeddict) 为主要解释，本章只增加运行时模型的作用。

## 资料与后续

上述接口及代表性失败路径已验证，具体环境见 §2。资料核实：2026-10-22。[请求体](https://fastapi.tiangolo.com/tutorial/body/) · [路径参数](https://fastapi.tiangolo.com/tutorial/path-params/) · [查询校验](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/) · [Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/)。

[上一章：HTTP 与 JSON](06-http-and-json.md) · [下一章：HTTPX 调用接口](08-httpx-and-upstream.md) · [返回目录](index.md)
