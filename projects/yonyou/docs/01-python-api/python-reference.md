# Python 查阅笔记

> 按主题收录学习中需要回看的概念、库与易混点，随答疑更新。更新：2026-10-22。

这里用于查阅和复习。已有主教材完整讲解的内容，只保留简短结论和回查链接；补充工具及分类在本页展开。当前阅读入口见 [模块目录](index.md#reading-position)，主教材已准备至 01-10。

目前已收录：[字典](#dictionaries)、[函数参数](#function-parameters)、[常见异常类型](#exceptions)、[API 工具与通信方式](#api-tools)、[初始化与运行入口](#class-init-and-entry)。

## 1. 字典：dict、TypedDict 与 defaultdict {#dictionaries}

### 1.1 先分清对象、类型工具和模块

| 名字 | 从哪里使用 | 主要用途 | 运行时的关键行为 |
| --- | --- | --- | --- |
| `dict` | Python 内置，无须导入 | 保存键值对应关系 | `d[key]` 读取缺失键时抛 `KeyError` |
| `TypedDict` | `from typing import TypedDict` | 为字典声明字段名与字段类型 | 标注后的普通字典仍是 `dict`，不自动校验或补字段 |
| `defaultdict` | `from collections import defaultdict` | 用指定规则为缺失键生成默认值 | 用 `d[key]` 读取缺失键时，调用默认值生成函数并保存结果 |
| `typing` | Python 标准库模块 | 提供类型提示相关工具 | 本页用到其中的 `TypedDict` |
| `collections` | Python 标准库模块 | 提供专门的容器工具 | 包含 `defaultdict`、`Counter`、`deque` 等 |

`TypedDict` 关注“结果应该长什么样”，`defaultdict` 关注“这个键还没有值时怎样处理”。两者按用途选择。

### 1.2 dict：已知客户编号，查询对应金额

本页金额均为合成的整数元金额。普通字典适合保存客户编号与金额的映射：

```python
balances = {"C001": 12800, "C002": 0}

print(balances["C001"])       # 12800
print(balances.get("C999"))   # None
print("C999" in balances)     # False
```

`balances["C999"]` 会抛 `KeyError`；`.get("C999")` 则返回 `None`，也可以用 `.get("C999", 默认值)` 指定缺失时的返回值。`.get()` 不会把缺失键添加到字典。

当前应收查询需要区分“客户不存在”和“客户存在、金额为 0”，因此先用 `in` / `not in` 判断客户，再读取金额。不要直接把两种情况都转换成 0。

字典不能作为另一个字典的键。传错查询参数的具体排错过程见 [01-02 §2.1](02-types-and-contracts.md#2)，本页不重复调用示例。

### 1.3 TypedDict：描述查询结果的字段

速查：`TypedDict` 描述字段名及类型，不自动校验、转换或补字段；用它标注的普通字典仍按 `result["amount"]` 读取，缺少键时仍可能抛 `KeyError`。

完整声明、返回类型与币种字段修改练习统一放在 [01-02 §4](02-types-and-contracts.md#4-typeddict)，这里不复制同一套例子。下节集中解释它与 `defaultdict` 在运行行为上的区别。

与普通类的选择：需要保持数据为字典时，可用 TypedDict 补充字段说明；希望创建自定义对象、使用属性和方法时，可使用普通类。完整比较及例子见 [01-02 §4.2](02-types-and-contracts.md#typed-dict-vs-class)。

### 1.4 defaultdict：汇总时给新客户一个起始值

假设要把两条 C001 的合成记录累加，可以让尚未出现的客户先得到 0：

```python
from collections import defaultdict

totals = defaultdict(int)
totals["C001"] += 10000
totals["C001"] += 2800
print(totals["C001"])  # 12800
```

第一次读取 `totals["C001"]` 时还没有这个键。容器调用 `int()` 得到 `0` 并保存，再完成累加。因此不用先手动给每个客户初始化 0。

`defaultdict(int)` 传入的是生成默认值的函数或类型。这里传 `int`，由容器在需要时调用；不要写成 `defaultdict(int())`，后者把已经算出的 `0` 传进去，构造时会因它不可调用而报错。

常见起始值规则：

| 写法 | 缺失键的初始值 | 常见用途 |
| --- | --- | --- |
| `defaultdict(int)` | `0` | 累加数量或整数金额 |
| `defaultdict(list)` | 一个新的空列表 | 按客户收集多条记录 |
| `defaultdict(set)` | 一个新的空集合 | 按组保存不重复的项目 |

例如按客户收集单据编号：

```python
from collections import defaultdict

documents = defaultdict(list)
documents["C001"].append("AR001")
documents["C001"].append("AR002")
print(documents["C001"])  # ['AR001', 'AR002']
```

### 1.5 读取缺失键时，字典可能发生变化

`defaultdict` 的默认生成规则由 `[...]` 取值触发。`.get()` 与 `in` 不触发它：

```python
from collections import defaultdict

totals = defaultdict(int)
print(totals.get("C999"))  # None，没有生成默认值
print("C999" in totals)    # False
print(totals["C999"])     # 0，这次生成并保存了默认值
print("C999" in totals)    # True
```

在本项目中，按客户汇总时可用这个机制简化初始化；查询客户是否存在时则要保留“未知客户”的含义。当前查询函数继续使用普通 `dict`，返回结果用 `TypedDict` 描述字段。

### 1.6 字典与数据库：为什么当前练习先用字典 {#dictionary-and-database}

当前的 `balances = {"C001": 12800, "C002": 0}` 是预先写在代码里的模拟数据源。这样能直接观察类型、参数、返回值与异常的关系，不必同时准备数据表和连接代码。用户已有 SQL 基础，后续可以把这里的取数步骤替换成 SQL 查询。

例子中有两种用途不同的字典：

```python
balances = {"C001": 12800, "C002": 0}                  # 模拟数据源
result = {"customer_id": "C001", "amount": 12800}     # 一次查询的结果
```

接上数据库后，第一份模拟数据可以移入表中，第二份结果仍然可以在 Python 中组织成字典：

```text
当前：客户编号 → 从 balances 取金额 → 组装结果字典 → 返回
接库：客户编号 → 执行 SQL 取得金额 → 组装结果字典 → 返回
```

数据库承担数据存储、关联和查询；字典则用于组织程序当前正在处理的数据。因此使用数据库后，Python 代码中仍经常出现字典，`TypedDict` 对结果字段的说明也仍然有用。

对于当前函数，最直接的变化是把 `amount = balances[customer_id]` 替换成数据库取数，并在没有查询到记录时执行相应处理。调用者可以继续接收 `{"customer_id": ..., "amount": ...}`。具体取数还可能通过 ERP 接口完成，要根据实际数据入口决定。

并不需要为了开始数据库练习先安装一个数据库服务。Python 标准库提供 `sqlite3`，可以使用本地文件数据库，模块调用方法见 [官方 sqlite3 文档](https://docs.python.org/zh-cn/3.12/library/sqlite3.html)。项目已有 [08-01 SQLite 实操](../08-database/01-sqlite-first-query.md)，其中给出建表、查询与 Python 取数的完整案例。

### 1.7 返回课程与资料

- 返回 [01-02 §4：用 TypedDict 说明结果有哪些字段](02-types-and-contracts.md#4-typeddict)。
- [Python 官方教程：字典](https://docs.python.org/zh-cn/3.12/tutorial/datastructures.html#dictionaries)。
- [Python 官方文档：TypedDict](https://docs.python.org/zh-cn/3.12/library/typing.html#typing.TypedDict)。
- [Python 官方文档：collections 与 defaultdict](https://docs.python.org/zh-cn/3.12/library/collections.html#collections.defaultdict)。

## 2. 函数参数：星号、可空与默认值 {#function-parameters}

### 2.1 单独的 * 规定传参方式

速查：单独的 `*` 后面的参数，传值时要写 `形参名=值`；有默认值时仍可省略。`*` 前的普通参数既可按位置传，也可按名字传。可运行的成功、失败与去掉星号的对比例子统一见 [01-02 §3](02-types-and-contracts.md#3)。

这里讨论的是单独的 `*`；`*args`、`**kwargs` 等参数收集写法在需要时单独补充。

### 2.2 允许 None 与允许省略分别由什么决定

```python
min_amount: int | None = None
```

| 部分 | 负责什么 |
| --- | --- |
| `: int \| None` | 类型提示，预期传入整数或 `None` |
| `= None` | 默认值，省略参数时采用 `None` |

可空类型不提供省略时的默认值；旧写法 `Optional[int]` 同样如此。显式传 None、缺少默认值及省略参数的完整对比见 [01-02 §3](02-types-and-contracts.md#3)。

### 2.3 返回课程与资料

- 返回 [01-02 §3：可空、默认值与关键字参数](02-types-and-contracts.md#3)。
- [Python 官方函数教程：默认值与特殊参数](https://docs.python.org/zh-cn/3.12/tutorial/controlflow.html#special-parameters)。

## 3. 常见异常类型速查 {#exceptions}

### 3.1 先认识常见的具体错误

下面是当前工程学习中常遇到的内置异常。可以根据实际操作和错误类型查阅，不必一次记完。

| 异常类型 | 触发情况或例子 | 常见处理方向 |
| --- | --- | --- |
| `TypeError` | 类型不合适，例如 `1 + "2"` | 修正传入类型；入口检查类型时也可主动抛出 |
| `ValueError` | 类型可接受但值不合法，例如 `int("abc")` | 提示重新输入；业务值不符合要求时可主动抛出 |
| `KeyError` | 字典中没有键，例如 `{}["C001"]` | 按业务决定先检查键、用 get，或捕获缺失情况 |
| `IndexError` | 序列中没有位置，例如 `[12800][3]` | 检查索引范围和列表内容 |
| `AttributeError` | 对象没有属性或方法，例如 `None.strip()` | 检查实际对象类型、是否为 None、属性名是否正确 |
| `NameError` | 使用了尚未定义的名字 | 修正变量名、赋值位置或作用域 |
| `ZeroDivisionError` | 除数为 0，例如 `10 / 0` | 明确分母为 0 时的业务处理，或在运算前检查 |
| `FileNotFoundError` | 指定文件或目录不存在 | 核对路径；可选文件缺失时使用约定的默认值，必需文件则明确报错 |
| `PermissionError` | 没有所需的文件或目录访问权限 | 检查目标位置与权限，向调用方说明失败 |
| `ModuleNotFoundError` | 找不到要导入的模块 | 核对模块名、文件位置、当前 Python 环境及依赖是否已安装 |
| `TimeoutError` | 等待操作超过期限，例如 01-05 中 wait_for 超时 | 结束本次等待并明确处理失败；具体例子见异步任务章 |

语法方面还会见到 `SyntaxError` 和它的子类 `IndentationError`，分别对应代码语法不合法和缩进问题。同一文件里的语法错误通常会在执行前的解析阶段暴露，不能靠给那段错误语法外面套 try 来正常运行。

### 3.2 LookupError 等名字是更大的类别

| 类别 | 包含的常见类型 | 统一捕获时的含义 |
| --- | --- | --- |
| `LookupError` | KeyError、IndexError | 处理这组键或索引查找错误 |
| `OSError` | FileNotFoundError、PermissionError、TimeoutError 等 | 处理这组系统及 I/O 操作错误 |
| `ImportError` | ModuleNotFoundError | 处理模块导入相关错误 |
| `Exception` | 上述这些普通异常及其子类 | 捕获范围更广，后续仍需明确如何处理 |

例如，本例的 CustomerNotFoundError 自定义为 LookupError 的子类，因此也可被 except LookupError 捕获。具体声明、用途和捕获差异统一见 [01-03 §2](03-errors-and-debugging.md#2)，这里不再展开相同例子。

Exception 并不包含所有异常信号，例如用户中断时的 KeyboardInterrupt，以及 01-05 使用的 asyncio.CancelledError，都不属于 Exception。后者在 [异步任务章](05-async-and-tasks.md#3) 解释。

### 3.3 内置异常与自己定义的业务异常

上面的类型由 Python 提供，不需要自己定义；CustomerNotFoundError 则是本例新定义的业务异常。第三方库也可以定义它们自己的异常类型，使用时看对应库的说明与实际异常，不仅凭名字里是否包含 Error 判断。

内置类型也可以直接用于主动报错，不需要先创建自己的异常类；若需要独立的业务类型，通常从 Exception 或语义合适的子类继承。LookupError 的具体选择与代码见 [01-03 §2](03-errors-and-debugging.md#2)。

### 3.4 用法：自动抛出、主动抛出与捕获

下面假设查询条数要能转换成整数，且至少为 1。这个条件仅用于展示异常用法。

```python
def parse_limit(raw) -> int:
    limit = int(raw)  # 不可转换的字符串自动产生 ValueError；None 产生 TypeError
    if limit < 1:
        raise ValueError("查询条数至少为 1")  # 主动检查业务条件
    return limit


for raw in ["abc", "0", None, "5"]:
    try:
        print("查询条数：", parse_limit(raw))
    except (TypeError, ValueError) as error:
        print("无效参数：", type(error).__name__)
```

预期输出：

```text
无效参数： ValueError
无效参数： ValueError
无效参数： TypeError
查询条数： 5
```

这里体现三种用法：

- `"abc"` 和 None 在调用 int 时自动触发异常；不必先手动 raise。
- `"0"` 可以转换成整数，但不符合本例的条数要求，由代码主动 raise。
- 调用方用 `except (TypeError, ValueError)` 接受这两种失败后继续下一项。若两种错误需要不同处理，就分成两个 except 分支。

同样类型的异常可以有不同说明。要看具体是哪次错误，读取 error；要看它的类型，可以像示例一样使用 type(error).__name__。保存的运行文件为 `learning/01-python-api/builtin-exceptions-usage.py`，在项目根目录执行：

```sh
python3 learning/01-python-api/builtin-exceptions-usage.py
```

### 3.5 用法：捕获范围、重抛与日志

| 需要做什么 | 写法或入口 |
| --- | --- |
| 只处理某个具体类型 | `except ValueError as error:` |
| 两种类型执行同一段处理 | `except (TypeError, ValueError) as error:` |
| 处理某一类别及其子类 | `except LookupError:`；具体比较回查 [01-03 §2](03-errors-and-debugging.md#2) |
| 主动抛出一次新异常 | `raise ValueError("查询条数至少为 1")` |
| 抛出已放在变量里的异常对象 | `raise error`；error 需引用一个异常对象 |
| 继续抛出正在处理的异常 | except 内单独写 `raise` |
| 只记录日志，或记录后再重抛 | 回查 [01-03 §3](03-errors-and-debugging.md#3)，不复制相同的 logger 示例 |

多个 except 分支按顺序匹配：如果既写具体类型又写它的父类，具体类型放前面，否则更宽的父类分支会先接住它。比如要分别处理 FileNotFoundError 与其余 OSError，应先写 FileNotFoundError，再写 OSError。

单独 raise 需要当前有正在处理的异常；直接写一段字符串给 raise 也不符合要求。主动抛出、变量抛出、重抛与 logger 的完整解释统一在 [01-03 §3](03-errors-and-debugging.md#3)。

完整内置列表及关系见 [Python 官方内置异常文档](https://docs.python.org/zh-cn/3.12/library/exceptions.html#exception-hierarchy)，抛出和捕获规则见 [Python 异常教程](https://docs.python.org/zh-cn/3.12/tutorial/errors.html)，核实日期为 2026-10-20。上面的查询条数示例输出已运行核对。

本页普通 Python 示例使用 Python 3.10+，异步超时与取消对应章节使用 Python 3.11+；运行核对使用 Python 3.12。后续按问题归入主题，合并重复解释。

## 4. API 工具与通信方式速查 {#api-tools}

这里只保留职责与主讲入口，完整代码和机制放在对应章节。

| 工具或方式 | 负责什么 | 主讲位置 |
| --- | --- | --- |
| TypedDict | 普通字典的字段类型说明，不执行运行时校验 | [02 §4](02-types-and-contracts.md#4-typeddict) |
| Pydantic BaseModel | 创建模型时校验数据，提供模型与字典/JSON 转换 | [07 §3](07-fastapi-and-pydantic.md#3) |
| FastAPI | 将方法、路径、参数与 Python 处理函数连接起来 | [07 §1–4](07-fastapi-and-pydantic.md#1) |
| Uvicorn | 监听端口，将网络请求交给应用 | [07 §1](07-fastapi-and-pydantic.md#1) |
| HTTPX | Python 客户端发 HTTP 请求，管理连接、超时和响应 | [08](08-httpx-and-upstream.md) |
| asyncio | 组织异步等待、任务、并发、超时和取消 | [05](05-async-and-tasks.md) |
| 普通 HTTP JSON | 每次请求得到一个完整结果 | [06](06-http-and-json.md) |
| SSE | 在 HTTP 响应里持续从服务端发送文本事件 | [09](09-streaming-and-sse.md) |
| WebSocket | 连接上的双方持续消息通信 | [10 §5](10-websocket-and-selection.md#selection) |

前面 `None` 的筛选语义在 HTTP/JSON 中表现为 `null`；0 元仍为成功结果，客户不存在仍走明确失败。异步、流式传输和模型逐步生成各有位置，不能仅凭用了 async 或 WebSocket 就认定实现了模型流式输出。

## 5. 类的初始化与文件运行入口 {#class-init-and-entry}

`__init__` 和 `__name__` 都是前后各两个下划线。它们分别出现在对象初始化与模块入口判断中。

| 名字 | 属于什么 | 何时用到 |
| --- | --- | --- |
| `__init__` | 实例初始化方法 | 对象创建时，要按传入参数设置初始属性或完成初始化 |
| `__name__` | Python 自动设置的模块变量；类和函数也有同名属性 | 本节用模块变量判断文件是直接运行还是被导入 |

### 5.1 什么时候自己写 __init__

希望创建对象时就保存每个对象自己的客户编号，可以这样写：

```python
class Customer:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id


customer = Customer("C001")
print(customer.customer_id)  # C001
```

`Customer("C001")` 创建实例，初始化时把编号交给 `__init__`；`self` 引用这个实例，赋值将编号保存在它的属性中。再创建 `Customer("C002")`，会初始化另一个对象，各自保存自己的编号。`__init__` 不需要返回这个对象，应正常返回 None。

并非每个类都要自己定义 `__init__`。没有自定义初始化要求时可以不写；继承时也可能已经有合适的初始化方法。例如本课程的 `CustomerNotFoundError(LookupError)` 没写 `__init__`，仍可以接收“客户不存在”这条说明，因为继承了异常类已有的初始化行为。若重写初始化而又需要父类完成它原有的工作，再按父类接口调用 `super().__init__(...)`，不需要给每个类机械加上。

TypedDict 是字段结构声明，沿用 [02 §4](02-types-and-contracts.md#4-typeddict)；Pydantic 等工具也可提供模型初始化能力，具体用法见 [07 §3](07-fastapi-and-pydantic.md#3)。

### 5.2 什么时候写 if __name__ == "__main__"

一个文件既要让别处导入类或函数，又希望直接运行时执行演示或启动逻辑，可以这样组织。完整运行文件为 `learning/01-python-api/class_init_and_entry.py`：

```python
class Customer:
    def __init__(self, customer_id: str):
        self.customer_id = customer_id


if __name__ == "__main__":
    customer = Customer("C001")
    print(customer.customer_id)
```

在项目根目录直接运行它，会输出 C001：

```sh
python3 learning/01-python-api/class_init_and_entry.py
```

其他文件写 `import class_init_and_entry` 时（需让 Python 能找到该目录），模块变量为 `"class_init_and_entry"`，不会执行下面创建和打印的演示；但 Customer 类仍可被导入使用。模块入口变量由 Python 提供，无须自己定义或赋值。

入口判断不是每个文件必写。仅提供函数、类和数据的模块，可以只放这些定义；想直接运行的演示、命令入口或启动动作，才按需要放入条件块。完整模块入口说明主讲于 [04 §3](04-modules-and-project.md#3)。

[返回模块目录](index.md)
