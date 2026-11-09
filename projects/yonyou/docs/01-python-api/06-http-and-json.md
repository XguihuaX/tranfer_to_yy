# 01-06 HTTP 与 JSON：一次请求怎样完成

> 教材状态：已准备。学习位置与练习状态见模块进度。更新：2026-10-27，新增 06–08 连贯解释；原节号与练习保持。

## 本章问题、目标与前置

前面是在一个 Python 程序里调用函数。现在销售页面与应收程序各自运行，页面怎样把“查 C001、最低金额 1000”送过去，又怎样拿到结果？本章建立一次 HTTP 请求的完整路线，并解释字典如何变成 JSON。

读完应能指出 URL、方法、请求头、请求体、状态码和响应体，区分 Python 数据与传输文本，并判断失败发生在连接、HTTP 还是数据层。前置是 [函数结果](01-reading-python.md#4-return-print) 与 [异常处理](03-errors-and-debugging.md)；约 15–20 分钟。本章可先手动推演，JSON 例子只用标准库；服务端代码下一章集中写。

## 先把 06–08 连起来：同一次查询的两端 {#six-to-eight}

先只看一件事：**你的 Python 程序想知道 C001 欠款多少，数据在另一个正在运行的程序里。**

在自己程序里，你可以直接调用函数；数据在另一台电脑的程序里时，需要把查询要求送过去，让对方处理，再把结果送回来。两端各自执行自己的代码。

```text
你的程序                         保存欠款数据的程序
    ───── 请求：查询 C001 ────────→
    ←──── 响应：金额 12800 ────────
```

**06 先看双方交换的东西。** HTTP 规定怎样组织请求与响应，例如请求中写访问哪个路径，响应中写状态码与内容。JSON 是这些内容可以采用的一种数据格式，例如 `{"amount":12800}`。HTTP 不要求所有内容都必须是 JSON；本例约定用它表示查询结果。

**07 再写接收查询的程序。** 下面片段只演示已知客户 C001 的正常路线；保存了 C002=0 便于后续对照。暂不加门槛、模型或异常分支：

```python
from fastapi import FastAPI

app = FastAPI()
balances = {"C001": 12800, "C002": 0}  # 只有服务端保存这份合成数据。

@app.get("/customers/{customer_id}/receivable")
def get_receivable(customer_id: str):
    # 请求路径中的 C001 交给 customer_id，再执行这次查询。
    return {"customer_id": customer_id, "amount": balances[customer_id]}
```

这里的关键是 `@app.get(...)`：它登记“收到这个 GET 地址，就调用下面的函数”。当路径是 `/customers/C001/receivable` 时，框架让函数接到 `customer_id="C001"`，函数返回字典，再由框架生成 JSON 响应。FastAPI 是帮助编写这部分处理逻辑的工具。真正监听端口、把网络请求交给应用的是 Uvicorn，运行入口在 07 章展开。

**08 最后写主动查询的程序。** 假设服务已通过 Uvicorn 运行在本机 8010，下面是另一个程序中的代码：

```python
import httpx

# 发出请求，等待并拿到响应；服务端在另一份程序中处理。
response = httpx.get("http://127.0.0.1:8010/customers/C001/receivable")
response.raise_for_status()  # 先确认本次 HTTP 状态成功。
result = response.json()  # 将响应里的 JSON 解析成此程序自己的字典。
print(result["amount"])  # 12800
```

HTTPX 帮这个 Python 程序发 HTTP 请求、接收响应。这行 `get` 不会把服务端的函数导入过来；它根据地址发请求，服务端根据路由调用自己的函数。`response.json()` 解析收到的内容，不会额外再发一次请求。用法对照 [FastAPI 最小路由](https://fastapi.tiangolo.com/tutorial/first-steps/)和 [HTTPX 请求与响应](https://www.python-httpx.org/quickstart/)。

```text
HTTPX 发 GET → HTTP 请求 → FastAPI 找到函数 → 查出 12800
HTTPX 收响应 ← HTTP 响应（内容为 JSON）← 框架组织返回值
```

| 原章 | 本轮只抓住的问题 | 后续再展开 |
| --- | --- | --- |
| 06 HTTP / JSON | 请求和响应怎样表达，数据长什么样？ | 方法、头、体、状态码和编码 |
| 07 FastAPI / Pydantic | 怎样让自己的函数接到外部查询？ | Pydantic 检查字段、错误与返回模型 |
| 08 HTTPX | 怎样在 Python 中向对方查询并使用结果？ | 异步、连接复用、超时与上游转接 |

这轮先用直接请求两端的路线。08 原文的“浏览器 → 查询服务 → 模拟 ERP”多了一次转接，等直接请求清楚后再读。这里的片段不替换原章完整示例；已有综合例子在 8010 提供相同 GET 入口，环境与启动见[完整例子 §2](00-one-example.md#run)。

### 两份可直接运行的小程序 {#two-programs}

把“登记地址”和“访问地址”并排看：服务端的 `@app.get("/customers/{customer_id}/receivable")` 与客户端的 GET `/customers/C001/receivable` 对应。前者登记规则，后者发出请求；服务端收到匹配请求后执行函数。

本对小程序统一使用本机 8011 端口。Python 3.12 及 FastAPI、Uvicorn、HTTPX 依赖复用已准备的 `.venv-api` 环境，不用重新安装；环境信息见[完整例子运行说明](00-one-example.md#run)。文件在 `learning/01-python-api/whole-example/`。

??? note "程序 A：服务端，登记地址并执行查询（minimal_server.py）"
    ```python
    """程序 A：运行后等待请求；与 minimal_client.py 配合阅读。"""
    from fastapi import FastAPI, HTTPException
    import uvicorn
    
    app = FastAPI()
    balances = {"C001": 12800, "C002": 0}  # 合成金额，单位为人民币元。
    
    
    # ① 登记规则：这个 GET 地址由下面的函数处理。
    @app.get("/customers/{customer_id}/receivable")
    def get_receivable(customer_id: str):
        print("服务端执行函数，收到编号：", customer_id, flush=True)
        if customer_id not in balances:
            raise HTTPException(status_code=404, detail="客户不存在")
        # ② 返回 Python 字典；框架把它组织成 JSON 响应。
        return {"customer_id": customer_id, "amount": balances[customer_id]}
    
    
    # ⑤ POST 入口：本例把查询条件放进 JSON 请求体。
    @app.post("/receivables/query")
    def query_receivable(data: dict):
        customer_id = data["customer_id"]  # 客户端 JSON 中的同名字段。
        # 复用上面的普通函数完成查询；这里没有再发一次 HTTP 请求。
        return get_receivable(customer_id)
    
    
    if __name__ == "__main__":
        # 启动服务，监听本机 8011 端口；保持运行，等待客户端请求。
        uvicorn.run(app, host="127.0.0.1", port=8011)
    ```

??? note "程序 B：客户端，用 HTTPX 请求这个地址（minimal_client.py）"
    ```python
    """程序 B：主动发起一次请求；先运行 minimal_server.py。"""
    import httpx
    
    
    if __name__ == "__main__":
        # ③ 用 GET 请求这个地址；C001 对应服务端的 {customer_id}。
        response = httpx.get("http://127.0.0.1:8011/customers/C001/receivable")
        response.raise_for_status()  # 检查响应状态；错误状态在这里抛异常。
        # ④ 服务端返回的 JSON，在这里解析成客户端自己的字典。
        result = response.json()
        print("客户端收到结果：", result)
        print("欠款金额：", result["amount"])
    ```

从项目根目录打开两个终端，先在终端 A 启动服务并保持运行，再在终端 B 执行客户端：

```sh
# 终端 A
learning/01-python-api/.venv-api/bin/python learning/01-python-api/whole-example/minimal_server.py

# 终端 B
learning/01-python-api/.venv-api/bin/python learning/01-python-api/whole-example/minimal_client.py
```

服务端收到请求时打印 `服务端执行函数，收到编号： C001`。客户端输出：

```text
客户端收到结果： {'customer_id': 'C001', 'amount': 12800}
欠款金额： 12800
```

将客户端地址中的 C001 改成 C002，仍执行服务端同一个函数，参数变成 C002，金额为 0。若改为 C999，本例服务端返回 404，客户端在 `raise_for_status()` 处抛 HTTPStatusError；服务未启动则是连接失败。读懂这一往返后，再展开模型校验或异步。

这条链路也可先手动推演，不要求立即运行。运行结束后，在服务端终端按 Ctrl+C 停止。

### GET 与 POST：方法和参数怎样对应 {#get-and-post}

`@app.get(...)` 登记 GET 请求的处理函数；`@app.post(...)` 登记 POST 请求的处理函数。客户端分别用 `httpx.get(...)`、`httpx.post(...)` 发起对应方法的请求。服务端按**方法与路径一起**匹配入口，只有 GET 入口时，对同一路径发 POST 通常会得到 405。

GET 通常用于获取信息，POST 通常用于提交一份数据让目标处理。两者都能传参数，也都能返回结果。本例的 POST 仍然只是查询，不写入数据库。

| 本例入口 | 客户端发送 | 服务端读取 |
| --- | --- | --- |
| GET `/customers/C001/receivable` | 编号放在 URL 路径中 | 函数参数 `customer_id` |
| POST `/receivables/query` | 请求体 JSON 为 `{"customer_id":"C001"}` | `data["customer_id"]` |

在 `minimal_server.py` 的启动判断之前，已加上下面的 POST 入口；已有 `app`、`balances`、GET 查询函数和启动代码沿用：

```python
@app.post("/receivables/query")
def query_receivable(data: dict):
    # FastAPI 将 JSON 对象请求体解析为这里的字典。
    customer_id = data["customer_id"]
    return get_receivable(customer_id)  # 直接复用刚才的查询函数。
```

`data: dict` 让这个参数读取 JSON 对象请求体；当前演示假设 JSON 含有字符串字段 customer_id。字段缺失或具体类型检查在 07 的 Pydantic 模型中展开，这里先看一份完整请求怎样到达函数。[FastAPI 请求体说明](https://fastapi.tiangolo.com/tutorial/body/)

对应客户端 `minimal_post_client.py`：

```python
import httpx

response = httpx.post(
    "http://127.0.0.1:8011/receivables/query",
    json={"customer_id": "C001"},  # 编码为 JSON 请求体并发送。
)
response.raise_for_status()
result = response.json()  # 与 GET 一样，解析返回结果。
print(result["amount"])  # 12800
```

本例 `json=...` 传的是 Python 字典，HTTPX 会编码 JSON 并设置相应内容类型；不用自己先 dumps。`params=...` 则是放到 URL 问号后，POST 也可按接口约定使用查询参数。选择数据放在哪里由接口约定决定，不能把方法简单等同于数据位置。[HTTPX JSON 请求](https://www.python-httpx.org/quickstart/#sending-json-encoded-data)

若最小服务端已运行，修改后要重启它，再运行：

```sh
learning/01-python-api/.venv-api/bin/python learning/01-python-api/whole-example/minimal_post_client.py
```

预期输出 `POST 客户端收到结果： {'customer_id': 'C001', 'amount': 12800}`，下一行 `欠款金额： 12800`。当前仍只看同一个查询业务，改变的是请求方法、地址和输入来源。

继续阅读时，先停在本节的两端与数据流；清楚后再读下面 §2 的请求细节，或回 [07 §1](07-fastapi-and-pydantic.md#1) 与 [08 §1](08-httpx-and-upstream.md#1)。

## 1. 从函数调用走到跨程序调用

同一程序里，`query_receivable("C001", min_amount=1000)` 直接传 Python 值。跨进程时，另一个程序拿不到这里的函数对象和内存字典，需要约定一个地址、怎样表达输入，以及怎样表达结果。HTTP 是组织这种请求和响应的应用层协议，JSON 是常用的数据格式，二者配合完成这次交流。

```text
浏览器或客户端 → HTTP 请求 → 接口程序 → 业务函数 → 结果
浏览器或客户端 ← HTTP 响应 ← 接口程序 ←───────────┘
```

客户端是发起本次请求的一方，服务端是接收请求并回应的一方。同一个 Python 程序可以接收浏览器请求，同时再作为客户端请求 ERP，08 章就会做这件事。

API 是程序间约定的调用入口；这里使用 HTTP 实现 API。后面用 FastAPI 写服务端，用 HTTPX 发请求，两者分别承担这条路线的不同部分。

## 2. 把一份请求拆开看

下面是下一章服务启动后可使用的地址：

```text
http://127.0.0.1:8001/customers/C001/receivable?min_amount=1000
```

| 部分 | 这里的值 | 用途 |
| --- | --- | --- |
| 协议 | `http` | 本地明文 HTTP；`https` 增加传输加密 |
| 主机与端口 | `127.0.0.1:8001` | 本机上监听 8001 的接口服务 |
| 路径 | `/customers/C001/receivable` | 选择查询入口，并携带客户编号 |
| 查询字符串 | `min_amount=1000` | 问号后面的筛选参数，多个参数用 `&` 分隔 |

`127.0.0.1` 指访问者自己的机器。本教材网页在 8765，练习接口在 8001，是两个服务；把接口路径接在 8765 后面不会自动调用 Python 业务代码。

用接近 HTTP/1.1 原文的形式表示请求：

```http
GET /customers/C001/receivable?min_amount=1000 HTTP/1.1
Host: 127.0.0.1:8001
Accept: application/json
```

第一行包含方法和目标。GET 用于读取；请求头是对这次请求的补充说明，`Accept` 表示客户端希望收到 JSON。这个 GET 没有请求体，参数已经在路径和查询字符串里。

当查询条件较多，也可以约定 POST 入口，将条件放入请求体：

```http
POST /receivables/query HTTP/1.1
Host: 127.0.0.1:8001
Content-Type: application/json
Accept: application/json

{"customer_id":"C001","min_amount":1000}
```

头部与请求体之间有一个空行。`Content-Type` 说明本次发送的内容是什么格式，`Accept` 说明希望收到什么。POST 表示交给目标处理一份数据，是否写入业务数据由接口约定决定；本例 POST 也只查询。常见的 PUT、PATCH、DELETE 分别常用于整体替换、局部修改和删除，本模块不再另造写接口。

不要默认给 GET 放 JSON 请求体：本例 GET 只读取路径与查询参数，POST 才读取上面的 JSON 模型。路径相同但方法不同，也可能是不同入口。

## 3. 响应既有状态，也有数据

成功响应可以写成：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"customer_id":"C001","amount":12800}
```

状态码先说明本次 HTTP 处理结果，响应体再给具体数据。下面是后续例子的约定：

| 情况 | 状态码与响应体 | 应怎样理解 |
| --- | --- | --- |
| C001 查询成功 | `200`，客户和金额对象 | 可继续取 `amount` |
| C002 存在且门槛为 0 | `200`，`amount` 为 `0` | 客户存在，金额为 0 元 |
| C002 存在但门槛为 1 | `200`，`null` | 沿用 02 章：未命中筛选，不等于客户不存在 |
| C999 不存在 | `404`，`{"detail":"客户不存在"}` | 本接口约定的业务失败 |
| 参数不符合接口模型 | `422`，包含字段错误的 `detail` | 下一章 FastAPI 默认输入校验响应 |
| 服务端代码发生未处理错误 | 通常 `500` | 根据服务端日志排错 |

`401` 常表示需要有效认证，`403` 表示服务器拒绝此操作；`502`、`504` 将在调用上游接口时使用。状态码的通用含义见 [HTTP 状态码参考](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)。具体错误字段由服务设计，不能只凭字段名猜成功。

连接被拒绝或无法连到主机时，可能连 HTTP 响应都没有，不能把它说成“收到了 500”。同样，拿到 200 后仍可能遇到无效 JSON 或字段不对，HTTP 成功与数据符合约定是两个需要依次检查的环节。

## 4. 字典、JSON 文本和字节怎样转换

JSON 使用对象、数组、字符串、数字、布尔值和 null 表达数据。它不是 Python 对象；字段名与字符串使用双引号，布尔值写 `true/false`，空值写 `null`。

| Python 中 | JSON 中 |
| --- | --- |
| `dict` / `list` | 对象 / 数组 |
| `str` / `int` | 字符串 / 数字 |
| `True` / `False` | `true` / `false` |
| `None` | `null` |

运行文件 `learning/01-python-api/06-json-roundtrip.py` 包含这个完整往返过程：

```python
import json

result = {"customer_id": "C001", "amount": 12800, "note": "合成应收", "matched": True}

# Python 字典 → JSON 字符串；保留可直接阅读的中文。
text = json.dumps(result, ensure_ascii=False)
# 字符串 → UTF-8 字节，模拟传输前的编码。
payload = text.encode("utf-8")
# JSON 字节 → Python 数据；直接解析上一步的 payload，没有进行网络传输。
restored = json.loads(payload)

print(type(result).__name__, type(text).__name__, type(payload).__name__)
print(text)
print(restored == result)  # 检查往返后的数据是否一致。
print(json.loads("null") is None)  # JSON null 对应 Python None。


# 故意使用单引号字段名，观察非法 JSON 的失败路径。
try:
    json.loads("{'amount': 12800}")
except json.JSONDecodeError:
    print("JSON 格式不合法：字段名要使用双引号")
```

在项目根目录运行：

```sh
python3 learning/01-python-api/06-json-roundtrip.py
```

预期输出：

```text
dict str bytes
{"customer_id": "C001", "amount": 12800, "note": "合成应收", "matched": true}
True
True
JSON 格式不合法：字段名要使用双引号
```

`dumps` 将 Python 数据编码成字符串，`encode` 得到 UTF-8 字节，`loads` 解析文本或受支持编码的字节，恢复 Python 数据。`ensure_ascii=False` 让中文直接显示；默认转成 Unicode 转义也能表达同样的数据。客户端和框架通常替你完成这些转换，理解过程是为了排查格式问题。[Python json 文档](https://docs.python.org/3.12/library/json.html)列出了支持的类型与异常。

`str(result)` 得到的单引号字典展示不是标准 JSON。日期、Decimal 和普通自定义类也不全能直接交给标准 `json.dumps`，需要约定转换方式；当前案例只用整数元，暂不增加日期或小数规则。

## 5. 一个请求应该怎样核对

依次问：是否连到正确主机和端口？请求方法和路径是否匹配？参数放对地方了吗？返回了哪个状态码？响应体是什么格式，字段和值是否符合业务约定？这个顺序能区分“服务没启动”“入口写错”“输入错误”“业务无结果”。

下一章启动服务后，可用终端工具 curl 查看原始响应：

```sh
curl -i 'http://127.0.0.1:8001/customers/C001/receivable?min_amount=1000'
```

`-i` 同时显示状态行和响应头；URL 用单引号包住，避免 shell 将 `?`、`&` 当作自己的语法。本章不要求提前启动服务，07 章提供完整安装和运行说明。

## 6. 可选练习

条件：仍是 C001=12800 元、C002=0 元，采用 §3 的状态与筛选约定。

1. 查询 C002，门槛分别为 0 和 1，响应体分别是什么？
2. 一次请求得到 `404`，另一次提示 connection refused，是否都拿到了 HTTP 响应？
3. `json.loads('{"amount":"12800"}')` 后，`amount` 的值是什么类型？

??? note "参考答案与依据"
    1. 门槛 0 时返回 `{"customer_id":"C002","amount":0}`；门槛 1 时返回 `null`。两者均为 200。
    2. 404 是已经得到的 HTTP 状态；connection refused 通常表示 TCP 连接未建立，尚无 HTTP 响应。
    3. 是字符串。JSON 解析保留输入表达的类型，不因为字段叫 amount 就自行改成整数。下一章才引入按模型校验与转换。

## 本章回顾与检查清单

一次 HTTP 交互先按地址和方法送达输入，再按状态与数据回应；JSON 负责表达数据，业务函数负责查询含义。

- [ ] 能在实例中指出方法、路径、查询参数、请求头和请求体。
- [ ] 能区分连接失败、HTTP 失败、JSON 或结构失败。
- [ ] 能解释 dict → JSON 字符串 → 字节 → Python 数据。

## 阅读中产生的答疑

06–08 仍难连起来时，从[两端的一次查询](#six-to-eight)开始：先观察发送要求、接收并调用函数、返回数据、解析使用这四步；HTTP/JSON 与 FastAPI/HTTPX 的职责放在同一条路线中解释。

## 资料与后续

JSON 脚本及预期输出已核对；HTTP 实例在下一章同名接口中运行。资料核实：2026-10-22。[HTTP 请求结构](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages) · [HTTP 状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status) · [Python json](https://docs.python.org/3.12/library/json.html)。

[上一章：async / await](05-async-and-tasks.md) · [下一章：FastAPI 与 Pydantic](07-fastapi-and-pydantic.md) · [返回目录](index.md)
