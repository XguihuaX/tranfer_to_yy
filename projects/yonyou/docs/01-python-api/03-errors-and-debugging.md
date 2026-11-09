# 01-03 异常处理与排错

> 教材状态：精简正文已准备。更新：2026-10-22。

## 本章目标与前置

本章解决“查询失败后，谁来处理、如何找到原因”。沿用 [01-02](02-types-and-contracts.md) 的参数约定，不重复输入校验。阅读约 10 分钟；示例仅需 Python 3.10+，已在 Python 3.12 核对。

## 1. 抛出错误与处理错误分别在哪里

查不到客户时，查询函数知道发生了什么，但未必知道调用者想显示提示、换个客户继续查，还是结束任务。因此函数抛出异常，由有处理能力的调用方捕获。

`raise` 会中断当前正常执行路径，异常向调用者传播；匹配的 `except` 决定怎样处理。没有处理者时，脚本显示错误回溯并结束。回溯（traceback）列出经过哪些调用、在哪行出错，排错时先看最后一行的错误类型和说明，再向上找相关代码。

| 情况 | 本例处理方式 |
| --- | --- |
| 输入类型或值不符合约定 | 沿用上章的 TypeError / ValueError |
| 客户不存在 | 用独立异常类型，让调用者明确识别 |
| 把字段拼成 `amout` 等代码错误 | 根据回溯修复，不把它误当成客户不存在 |

## 2. 一个可运行的例子

这里的新增点是自定义异常和捕获位置。两条金额仍是合成的整数元数据。

```python
balances = {"C001": 12800, "C002": 0}


class CustomerNotFoundError(LookupError):
    pass


def lookup_amount(customer_id: str) -> int:
    if customer_id not in balances:
        raise CustomerNotFoundError("客户不存在")
    return balances[customer_id]


for customer_id in ["C001", "C999", "C002"]:
    try:
        print(customer_id, lookup_amount(customer_id))
    except CustomerNotFoundError as error:
        print(customer_id, "查询失败：", error)
print("本批查询结束")
```

`try` 放在循环内部，让每轮查询分别处理失败；它不会回到失败的函数内部继续运行，也不会自动重试。

在项目根目录运行已提供的文件：

```sh
python3 learning/01-python-api/03-errors-and-debugging.py
```

预期输出：

```text
C001 12800
C999 查询失败： 客户不存在
C002 0
本批查询结束
```

### 2.1 循环中的五行怎样执行 {#loop-execution}

1. **`for customer_id in ["C001", "C999", "C002"]:`**：按列表顺序执行三轮，每轮把当前编号交给 customer_id。
2. **`try:`**：尝试执行其内部代码。正常执行时跳过 except；发生匹配异常时转到 except。
3. **`print(customer_id, lookup_amount(customer_id))`**：先调用 lookup_amount 得到金额，再把客户编号与金额交给 print。例如第一轮输出 C001 12800。如果函数调用抛异常，参数尚未求值完成，这个 print 还没有被调用，不会先单独打印一部分客户编号。
4. **`except CustomerNotFoundError as error:`**：CustomerNotFoundError 是用来匹配的异常类型名；error 是引用本轮那个异常对象的变量名。这里引用的是本轮捕获到的那个异常，as 不会再创建第二个异常。写出 as error 是为了在下一行读取它的说明；不需要访问对象时，可以只写 `except CustomerNotFoundError:`。正常返回时不进入此分支。
5. **`print(customer_id, "查询失败：", error)`**：显示当前编号、提示文字和异常的说明。这里 error 是异常对象，print 会把它显示为“客户不存在”。本轮处理结束后，for 再进入下一轮。

对应三轮的执行情况：

| 本轮编号 | lookup_amount 的结果 | 走哪条分支 |
| --- | --- | --- |
| C001 | 正常返回 12800 | try 中的成功打印，跳过 except |
| C999 | 抛 CustomerNotFoundError，说明为“客户不存在” | 跳过未完成的成功打印，进入 except 的失败打印 |
| C002 | 正常返回 0 | try 中的成功打印，跳过 except |

### 2.2 LookupError 在声明中负责什么

`LookupError` 是 Python 内置的异常类，不需要导入。它的主要用途是把几种“查找失败”归成一组，方便统一捕获；它不提供查询客户的操作。

| 操作 | 实际抛出的异常 | 能否被 except LookupError 捕获 |
| --- | --- | --- |
| `{}["C001"]` | KeyError，字典中没有这个键 | 能 |
| `[12800][3]` | IndexError，列表没有这个位置 | 能 |

例如，实际抛出的是 KeyError，但捕获更上层的 LookupError 也能处理：

```python
try:
    amount = {}["C001"]
except LookupError as error:
    print(type(error).__name__)  # KeyError
```

原例的 `CustomerNotFoundError(LookupError)` 就把自定义的“客户不存在”也归入这个现成类别；除了专门捕获 CustomerNotFoundError，将来也能用 except LookupError 统一捕获它和其他查找错误。

**当前例子没有使用统一捕获 LookupError 的功能。** 因此这里选择它只是表达“属于查找失败”；直接继承 Exception，也能完成当前例子中同样的报错与处理。选择 LookupError 并没有自动查询或额外校验效果。

??? note "查阅：本例的异常归类"
    ```text
    Exception
    └── LookupError
        ├── KeyError
        ├── IndexError
        └── CustomerNotFoundError（本例自定义）
    ```

    统一捕获 LookupError 的范围比只捕获 CustomerNotFoundError 更大。是否采用这种分类，取决于调用方有没有按整组处理的需要。

## 3. 保留排错线索

### 3.1 可以直接主动抛出，不必先发生错误

代码判断业务条件不成立时，可以直接写 `raise ValueError("客户不存在")`，也能用更通用的 `raise Exception("客户不存在")`。不需要先触发一次别的错误，也不必先定义自己的异常类。

几种写法分别是：

| 写法 | 含义 |
| --- | --- |
| `raise ValueError("客户不存在")` | 创建一个异常对象，并立即抛出 |
| `error = ValueError("客户不存在")`，随后 `raise error` | 先把异常对象交给变量，再抛出这个对象；error 是变量名 |
| 单独的 `raise` | 重新抛出当前正在处理的异常，通常写在 except 内；没有正在处理的异常时会产生 RuntimeError |

抛出的需要是异常对象或异常类，普通字符串不是异常对象。异常类型按失败含义选择；本例如果要让调用者单独识别客户不存在，才使用 §2 的自定义类型。

### 3.2 logger 负责记录，raise 负责异常传播

以 Python 标准库 logging 为例：

| 调用 | 做什么 | 是否主动抛出业务异常 |
| --- | --- | --- |
| `logger.error("客户不存在")` | 记录 ERROR 级别日志 | 否，随后仍继续执行 |
| `logger.exception("查询失败")` | 记录 ERROR 日志并附当前异常回溯，通常在 except 中使用 | 否，不会自动重抛当前异常 |
| `raise ...` | 中断当前正常路径，把异常交给调用者 | 是 |

日志里的 ERROR 是严重程度，和异常对象的类型分别描述不同事情。下面可以独立运行：

```python
import logging

logger = logging.getLogger("receivable")
logger.error("记录一条失败消息")
print("写日志后，仍继续执行")

try:
    raise ValueError("客户不存在")
except ValueError:
    logger.exception("应收查询失败")
print("这次异常已处理")
```

运行后会有两条错误日志，第二条带异常回溯；两条 print 都会执行。示例中的异常已经被 except 处理。如果还需要上层调用者继续处理，在 logger.exception 后加单独的 `raise`，它就会继续传播；后面的 print 不会在这条路径执行。

因此，只需要留下运行记录时可以用 logger；需要让调用方接到失败信号时使用 raise。两者也可以配合，记录后继续抛出。若需要转换错误含义，可在 except 内写 `raise ValueError("金额无法解析") from error` 保留原始原因，error 是捕获到的原异常。

## 4. 易错点与一个小练习

`except CustomerNotFoundError` 不会接住无关的 KeyError；`except Exception` 范围更大，适合确实需要统一记录的边界，但捕获后仍要决定继续抛出或明确返回失败，不能直接当作成功。

**练习：** 把 §2 的 `try/except` 移到整个 `for` 外面，C999 出错后还会查询 C002 吗？说明处理结束后代码会到哪里。

??? note "参考答案"
    不会查询 C002。异常使程序离开整个 for，进入外层 except，处理后从 try/except 后面的语句继续，不会自动进入下一轮。要让每条记录各自失败、各自继续，应把捕获放在循环内部。

## 检查清单与答疑

- [ ] 能说明哪个函数负责抛出、哪个调用边界负责处理。
- [ ] 能根据错误类型和回溯定位失败。
- [ ] 能解释捕获放在循环内外对后续查询的影响。

答疑：循环、try、两条 print 和 except as 的逐行解释见 [§2.1](#loop-execution)；LookupError 的用途见 [§2.2](#22-lookuperror)。常见内置异常的触发场景、处理方向、自动/主动抛出与捕获用法，集中查阅 [Python 查阅笔记：常见异常类型与用法](python-reference.md#exceptions)。

## 资料与下一步

示例输出和循环内外的失败路线已核对；logger.exception 在异常处理分支中使用，记录与重抛的区别已通过示例核对。资料于 2026-10-20 核实：[Python 异常教程](https://docs.python.org/zh-cn/3.12/tutorial/errors.html)、[LookupError 与内置异常](https://docs.python.org/zh-cn/3.12/library/exceptions.html#LookupError)、[raise 语句](https://docs.python.org/zh-cn/3.12/reference/simple_stmts.html#the-raise-statement)、[logging](https://docs.python.org/zh-cn/3.12/library/logging.html#logging.Logger.exception)。

[下一章：模块与小型工程组织](04-modules-and-project.md) · [返回模块目录](index.md)
