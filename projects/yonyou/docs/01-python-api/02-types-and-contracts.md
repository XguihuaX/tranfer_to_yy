# 01-02 类型与函数参数约定

> 教材状态：已准备。学习位置与实际练习记录见本模块进度。更新：2026-10-20。

## 本章问题、目标与前置

上一章的应收查询能运行，但协作时还需要说明：客户编号必须是什么类型？筛选条件能否不传？成功时有哪些字段？不合条件和查询失败分别怎样表示？这些共同构成函数的**调用约定**。

本章围绕“怎样把调用约定写进代码”展开。默认你已知函数参数、字典、`return` 和 `print`，只在发生变化的地方解释。读完应能读懂带类型的函数签名，区分可空值与默认值，并写出必要的输入检查。

阅读约 15–25 分钟，可边读边问。完整例子仅需 Python 3.10+，本机使用 Python 3.12.14 核对；没有第三方依赖。前置案例见 [01-01](01-reading-python.md)，异常处理的系统整理放在下一章。

## 1. 从“查询应收”加一个筛选条件开始

沿用合成记录：C001 应收 12800 元，C002 应收 0 元。现在增加一个要求：调用者可以设置最低金额，只返回金额**大于或等于**门槛的客户结果。

本章暂用 `balances` 字典模拟数据源，便于聚焦函数约定。它可以替换为数据库或 ERP 接口取数，返回结果仍可组织成字典。具体解释见 [查阅笔记：字典与数据库](python-reference.md#dictionary-and-database)。

约定如下：

| 情况 | 行为 |
| --- | --- |
| 不传最低金额 | 不做金额筛选 |
| 最低金额为 `0` | 执行筛选，0 元也符合 |
| 客户存在且符合条件 | 返回客户编号和金额 |
| 客户存在但金额低于门槛 | 返回 `None`，表示本次未命中筛选条件 |
| 编号为空、客户不存在、门槛不合法 | 抛出异常，交给调用者处理 |

这里的 `None` 有一个明确含义：客户存在，但没通过筛选。它不会替代未知客户的异常。金额继续使用整数元，不引入小数或币种计算。

我们先写清类型，再增加运行时检查，最后把两者合在完整例子里。

## 2. 类型提示能说明什么

### 2.1 读懂参数与返回类型

从一个只返回金额的最小版本开始：

```python
balances: dict[str, int] = {"C001": 12800, "C002": 0}

def lookup_amount(customer_id: str) -> int:
    return balances[customer_id]
```

`customer_id: str` 表达参数应当是字符串；`-> int` 表达正常返回整数；`dict[str, int]` 表达字典的键是字符串、值是整数。标注让读代码的人和开发工具更容易检查函数之间能否接上。

这个函数已经从外部读取 `balances`，调用时传入要查的客户编号即可：

```python
print(lookup_amount("C001"))  # 12800
```

如果写成 `lookup_amount(balances)`，参数 `customer_id` 就接到了整个字典，函数随后尝试执行相当于 `balances[balances]` 的操作。字典不能作为字典的键，因此报 `TypeError: unhashable type: 'dict'`。`: str` 没有在调用入口自动拦截这个值，具体原因见下一节。

后续常见写法可按下面理解，不必记住整套类型系统：

| 写法 | 含义 | 当前案例中的用途 |
| --- | --- | --- |
| `str` / `int` | 字符串 / 整数 | 客户编号 / 整数元金额 |
| `list[str]` | 元素为字符串的列表 | 后续批量查询的客户编号 |
| `dict[str, int]` | 字符串键、整数值的字典 | 客户到金额的映射 |
| `int \| None` | 整数或 `None` | 可以不设置的最低金额 |

### 2.2 标注本身不执行输入检查

下面的代码故意违反了标注，直接运行仍会打印 `123`：

```python
def echo_customer(customer_id: str) -> str:
    return customer_id

print(echo_customer(123))
```

原因是函数只是原样返回传入值，Python 不会仅凭这里的 `: str` 自动拒绝整数或把整数转成字符串。编辑器或静态类型检查器可以提前提示这种问题；“静态检查”指在不执行这次业务调用时分析代码。

因此，需要实际拒绝的输入，要在函数中写检查，或使用后面章节的数据校验工具。本章先用普通 Python 写明检查规则。这里不要求安装类型检查器。关于标注的运行行为，见 [Python 官方 typing 文档](https://docs.python.org/zh-cn/3.12/library/typing.html)。

## 3. 可空、默认值与关键字参数各负责什么

### 3.1 单独的 *：后面的参数按名字传

先暂时拿掉类型标注和查询逻辑，只观察怎样传参。这个例子可以独立运行：

```python
def show_filter(customer_id, *, min_amount=None):
    print(customer_id, min_amount)

show_filter("C001", min_amount=1000)  # C001 1000
show_filter("C001")                   # C001 None
```

单独的 `*` 像一条分隔线，本身不接收值：它后面的 `min_amount` 如果要传，就必须写出 `min_amount=`。前面的 `customer_id` 可以按位置传，也可以写成 `customer_id="C001"`。

所以以下调用会报错，函数里的 `print` 也不会执行：

```python
show_filter("C001", 1000)
# TypeError: show_filter() takes 1 positional argument but 2 were given
```

调用中 `"C001"`、`1000` 都没带名字，属于两个位置参数；定义只允许星号前的那个参数按位置传。写上 `min_amount=1000` 就符合约定。这适合筛选条件较多的函数，读调用处即可知道每个值的含义。

对比：如果去掉定义中的 `*,`，变成 `def show_filter(customer_id, min_amount=None):`，则 `show_filter("C001", 1000)` 也能调用。**`*` 规定传参方式，不决定参数能否为空、能否省略。**

### 3.2 int | None = None：类型与默认值分开看

回到本章的写法：

```python
min_amount: int | None = None
```

- `int | None`：允许的值包括整数与 `None`。这里 `None` 表示未设置门槛。
- `= None`：调用者省略这个参数时，默认取 `None`。

因此下面三种调用都成立：

```python
show_filter("C001", min_amount=1000)  # 显式传整数
show_filter("C001", min_amount=None)  # 显式传 None
show_filter("C001")                   # 省略，采用默认的 None
```

如果只有可空标注而没有默认值，情况就不同：

```python
def required_filter(customer_id, *, min_amount: int | None):
    print(customer_id, min_amount)

required_filter("C001", min_amount=None)  # 可以，显式传 None
required_filter("C001")                  # TypeError：缺少必传参数 min_amount
```

**允许传 `None` 与允许省略参数，是两个独立要求。** 旧代码中的 `Optional[int]` 表达的也是 `int | None`，不会自行添加默认值。

本章完整签名就是把这几项合在一起，完整实现见 §6：

```python
def query_receivable(
    customer_id: str,
    *,
    min_amount: int | None = None,
) -> ReceivableResult | None:
    ...
```

筛选时应写 `if min_amount is not None:`，不要写 `if min_amount:`。后者会把整数 `0` 也当作假，导致设置了 0 门槛却没有进入该分支。默认值与关键字参数见 [Python 官方函数教程](https://docs.python.org/zh-cn/3.12/tutorial/controlflow.html#special-parameters)。

## 4. 用 TypedDict 说明结果有哪些字段

现在把“只返回金额”扩展为“返回客户编号和金额”。`dict[str, str | int]` 能说明值大体是哪几种类型，但没有说明每个字段的名字和对应类型。可以使用标准库 `typing` 中的 `TypedDict`：

```python
from typing import TypedDict

class ReceivableResult(TypedDict):
    customer_id: str
    amount: int
```

这里用 `class` 语法声明一个字典结构，并给它起名 `ReceivableResult`。这几行描述的是“这一类查询结果应有哪些字段”，还没有放入 C001 的具体数据。可以把它读成一张字段说明表：

| 字段名 | 预期类型 |
| --- | --- |
| `customer_id` | `str`：客户编号 |
| `amount` | `int`：本例中的整数元金额 |

接下来才创建一份具体数据，并注明它按这份结构说明组织：

```python
result: ReceivableResult = {"customer_id": "C001", "amount": 12800}
```

把它与熟悉的 `customer_id: str = "C001"` 对照：冒号两边的关系相同，左边是变量，右边是类型提示。`str` 是内置的字符串类型；这里的 `ReceivableResult` 是我们命名的字典结构，能进一步说明各个字段。

三个名字各有位置：`TypedDict` 是用来声明结构的工具，`ReceivableResult` 是声明好的结构名称，`result` 是保存实际数据的变量。因此函数写 `-> ReceivableResult` 时，就是说明它预期返回这种字段结构的字典。

函数返回时仍然写普通字典：

```python
return {"customer_id": customer_id, "amount": amount}
```

调用方也仍然使用 `result["amount"]`，不是 `result.amount`。`TypedDict` 主要帮助开发工具检查字段名、缺失字段与字段类型，运行时的结果依旧是 `dict`；它不自动执行字段校验。

因为本章还允许“未命中筛选条件”，完整返回标注会写成 `-> ReceivableResult | None`。这使调用者知道，取字段之前需要处理无结果的分支：

```python
result = query_receivable("C002", min_amount=1)
if result is None:
    print("未命中筛选条件")
else:
    print(result["amount"])
```

后面学习 Pydantic 时会看到另一个能力：按模型在运行时校验输入。到时会结合接口任务介绍。当前 `TypedDict` 已足以描述本例的结果形状，见 [官方 TypedDict 说明](https://docs.python.org/zh-cn/3.12/library/typing.html#typing.TypedDict)。

### 4.1 与 defaultdict、collections 的区别

`TypedDict` 声明结果字段的类型，`collections.defaultdict` 则在按键读取缺失值时生成默认值。完整对比、汇总与分组示例已移到 [Python 查阅笔记：字典](python-reference.md#dictionaries)。

看完查阅笔记可回到这里，继续 §5 的运行时检查。

### 4.2 为什么不直接用普通 class？ {#typed-dict-vs-class}

可以使用普通类。选择 `TypedDict` 的主要意义是：当数据原本就以字典传递时，可以为它补充精确的字段说明，并继续使用原来的字典表示。

前面 `result: ReceivableResult = {...}` 中，`result` 是普通字典，用 `result["amount"]` 读取。普通类则会创建这个类的实例，通常用属性访问：

```python
class ReceivableRecord:
    def __init__(self, customer_id: str, amount: int):
        self.customer_id = customer_id
        self.amount = amount

record = ReceivableRecord("C001", 12800)
print(record.amount)  # 12800
```

`__init__` 在创建实例时初始化它，`self` 代表当前实例；这里把两个参数保存为实例的属性。只在普通类中写 `amount: int` 等字段标注，不会自动生成上面这个接收参数并保存属性的初始化方法。

何时需要自己编写或沿用父类的初始化，集中查阅 [初始化与运行入口](python-reference.md#class-init-and-entry)，本节继续比较数据表示。

| 比较项 | 本章的 TypedDict 写法 | 上面的普通类写法 |
| --- | --- | --- |
| 实际数据 | 普通 `dict` | `ReceivableRecord` 的实例 |
| 读取金额 | `result["amount"]` | `record.amount` |
| 接到已有字典处理代码 | 可继续直接使用字典 | 需要代码读取属性或按需要转换 |
| 主要新增价值 | 字段结构的类型说明 | 自定义对象，可组织属性与方法 |

例如 Python 标准库的 `json.dumps(result)` 可以编码这里包含字符串与整数的字典。直接执行 `json.dumps(record)`，默认会因不认识这个自定义对象而抛 `TypeError`，需要先转换或指定编码方式。JSON 的具体转换放到 01-06，本节只借此说明两种运行时表示有实际差别。

当前练习要把查询结果按字段交给后续接口，所以继续返回字典，并用 `TypedDict` 说明结构。若业务需要一个包含操作方法、封装自身状态的对象，普通类也很合适。两种写法里的类型标注本身都不自动执行运行时类型校验。

## 5. 把约定落实到运行时

在完整代码前，先明确检查顺序和修改原因：

1. 客户编号先检查字符串类型，再调用 `.strip()` 去掉两端空白；否则整数没有这个字符串方法。只包含空白的编号在整理后应报错。
2. 门槛为 `None` 时不做门槛检查；传了门槛，就要求是非负整数。类型不对用 `TypeError`，类型对但值不符合要求用 `ValueError`。
3. 检查客户是否存在，再读取金额、执行筛选。这样未知客户保持上一章的失败行为。

本例用 `isinstance(customer_id, str)` 判断是否为字符串；门槛则用 `type(min_amount) is int` 要求恰好是整数类型。这个写法还排除了 `True` / `False`：Python 的 `bool` 是 `int` 的子类，单用 `isinstance(True, int)` 会得到 `True`。我们不把布尔值接受为金额门槛，见 [官方 bool 说明](https://docs.python.org/zh-cn/3.12/library/functions.html#bool)。

字符串 `"1000"` 不会在这里自动转成整数，调用者要传 `1000`。将来接收 HTTP 参数时，数据解析规则交给接口层统一说明，本章函数保持明确的输入约定。

## 6. 完整示例与运行

下面把标注、参数规则、结果结构和校验合在一起。相比上一章，新增了门槛筛选、类型声明与输入检查；成功结果字段保持一致。

```python
from typing import TypedDict


class ReceivableResult(TypedDict):
    customer_id: str
    amount: int


balances: dict[str, int] = {"C001": 12800, "C002": 0}


def query_receivable(
    customer_id: str,
    *,
    min_amount: int | None = None,
) -> ReceivableResult | None:
    if not isinstance(customer_id, str):
        raise TypeError("customer_id 必须是字符串")
    customer_id = customer_id.strip()
    if not customer_id:
        raise ValueError("customer_id 不能为空")

    if min_amount is not None:
        if type(min_amount) is not int:
            raise TypeError("min_amount 必须是整数或 None")
        if min_amount < 0:
            raise ValueError("min_amount 不能为负数")

    if customer_id not in balances:
        raise ValueError("客户不存在")
    amount = balances[customer_id]
    if min_amount is not None and amount < min_amount:
        return None
    return {"customer_id": customer_id, "amount": amount}


print(query_receivable(" C001 "))
print(query_receivable("C002", min_amount=0))
print(query_receivable("C002", min_amount=1))
```

已提供相同内容的练习文件 `learning/01-python-api/02-types-and-contracts.py`。在项目根目录运行：

```sh
python3 learning/01-python-api/02-types-and-contracts.py
```

预期输出：

```text
{'customer_id': 'C001', 'amount': 12800}
{'customer_id': 'C002', 'amount': 0}
None
```

第一行整理编号两端空白后成功查询；第二行金额等于门槛，符合条件；第三行客户存在但未达到门槛。无需再逐行推演函数的基本执行过程，关注新增条件如何改变结果即可。

想观察失败路径时，可以在末尾单独添加一次 `print(query_receivable("C999"))`：它会抛出 `ValueError: 客户不存在`。本例末尾未捕获该异常，因此会显示 traceback 并结束。异常怎样捕获、在哪一层处理，下一章集中讲。

完整示例的三行输出，以及空编号、错误类型、负门槛、未知客户和位置参数错误，均已在本机检查。没有运行静态类型检查器，关于提示的描述来自官方文档。

## 7. 常见误区速查

| 写法或现象 | 应关注的区别 |
| --- | --- |
| 只加 `: str` 就期待拒绝整数 | 类型标注提供说明，实际检查由代码或校验工具执行 |
| `min_amount: int | None` 却省略实参 | 允许 `None` 不等于有默认值；还需要 `= None` |
| `if min_amount:` | 会把 `0` 与 `None` 一起跳过；本例需用 `is not None` |
| 直接执行 `result["amount"]` | 返回值可能是 `None`，先处理未命中分支 |
| 用 `result.amount` 读取 TypedDict | 运行时是字典，按键读取 |

文件找不到时检查运行目录；`int | None` 相关语法或类型错误时先确认 `python3 --version`。本章使用 Python 3.10+ 写法，不需要为此安装额外库。

## 8. 小练习

可以先读再问，也可以选择练习；不要求先完成才能继续。

### 练习 1：解释可空与默认值

针对完整示例回答：

1. 删除 `= None` 后，`query_receivable("C001")` 还能运行吗？为什么？
2. 删除输入类型检查，但保留标注，调用 `query_receivable(123)` 会在哪个操作失败？
3. 为什么门槛判断用 `is not None`，而不直接用 `if min_amount`？

??? note "参考答案与推理"
    1. 不能。`min_amount` 会成为必须提供的关键字参数；调用时因缺少它而抛出 `TypeError`。`int | None` 仍允许显式传入 `None`，但不提供省略时的默认值。
    2. 标注本身不会拦截整数，会在 `customer_id.strip()` 处抛出 `AttributeError`。保留检查则会更早得到明确的 `TypeError`。
    3. `0` 是有效门槛，也会在布尔判断中被视为假。`is not None` 明确区分“未设置”和“设置为 0”。本例金额都非负，门槛 0 时最终结果可能碰巧相同，但筛选分支的执行含义已经不同。

### 练习 2：给返回结果添加明确的币种字段

在 `ReceivableResult` 中增加 `currency: str`，并让成功返回的结果包含 `"currency": "CNY"`。不要改变未命中或失败行为。运行例子，检查 C002 配合门槛 0 时也返回币种字段。

??? note "参考答案与推理"
    结构声明新增一行：

    ```python
    class ReceivableResult(TypedDict):
        customer_id: str
        amount: int
        currency: str
    ```

    成功返回处改为：

    ```python
    return {"customer_id": customer_id, "amount": amount, "currency": "CNY"}
    ```

    既更新给开发工具看的结构约定，也更新运行时实际生成的数据。只改结构不会让字典自动长出这个字段。C002 配合门槛 0 时返回 `{"customer_id": "C002", "amount": 0, "currency": "CNY"}`；门槛 1 时仍返回 `None`。

## 本章回顾与检查清单

函数的约定可以分成几部分：标注描述预期类型，默认值决定省略时取什么，`*` 决定怎样传参，检查语句落实运行时规则。返回类型还应提醒调用者有哪些正常分支。本章用 `TypedDict` 命名结果字段，并用 `None` 明确表达未命中筛选。

- [ ] 能读懂完整示例的参数和返回标注。
- [ ] 能解释 `int | None` 与 `= None` 分别负责什么。
- [ ] 能区分类型提示、参数绑定和运行时输入检查。
- [ ] 能处理 `ReceivableResult | None` 的两个正常分支。
- [ ] 能同时修改结果结构声明与实际返回数据。

## 阅读中产生的答疑

解释已合并到对应正文或查阅主题。这里作为定位索引，避免再次复制相同答案：

| 问题 | 完整解释位置 |
| --- | --- |
| 为什么 `lookup_amount(balances)` 报错？ | [§2：读懂参数、类型与实际调用](#2) |
| 单独的 `*` 怎样用？可空与默认值有什么关系？ | [§3：独立运行的对比例子](#3) |
| TypedDict、ReceivableResult 和实际的 result 分别是什么？ | [§4：字段说明与实际数据](#4-typeddict) |
| 为什么不直接用普通 class？ | [§4.2：字典表示与类实例的选择](#typed-dict-vs-class) |
| TypedDict、defaultdict 和 collections 有什么关系？ | [查阅笔记：字典](python-reference.md#dictionaries) |
| 为什么当前先用字典，不直接查数据库？ | [查阅笔记：字典与数据库](python-reference.md#dictionary-and-database) |

## 资料与后续

官方资料于 2026-10-16 核实，用于查阅，不要求逐页学习：

- [Python typing：类型提示与 TypedDict](https://docs.python.org/zh-cn/3.12/library/typing.html)。
- [Python 函数：默认值与特殊参数](https://docs.python.org/zh-cn/3.12/tutorial/controlflow.html#special-parameters)。
- [Python 内置函数：isinstance](https://docs.python.org/zh-cn/3.12/library/functions.html#isinstance)。

下一章 [01-03 异常处理与排错](03-errors-and-debugging.md) 的精简正文已准备，集中处理异常的传播、捕获位置和排错线索。

[上一章：跟着数据读懂 Python 函数](01-reading-python.md) · [返回模块目录](index.md)
