# 01-04 模块与小型工程组织

> 教材状态：精简正文与代码注释已准备。更新：2026-10-22。

## 本章目标与前置

将查询拆成数据、业务、入口三个文件，读懂它们怎样连接和启动。前置：[01-03 异常处理](03-errors-and-debugging.md)。阅读约 5–8 分钟，仅需 Python 3.10+；已在 Python 3.12 核对。

## 1. 将取数、业务和入口分开

示例位于 §4 运行命令对应的目录，调用关系为 **main → service → repository**：

```text
04-mini-project/
├── repository.py   取数据
├── service.py      业务处理
└── main.py         运行入口
```

入口调用业务，业务再调用取数函数。以后改接数据库或 ERP 接口，优先替换 repository 的取数实现。

## 2. 三个文件怎样连接

**repository.py：取数据。** 两条合成金额按人民币整数元计。

```python
balances = {"C001": 12800, "C002": 0}


def fetch_amount(customer_id: str) -> int | None:
    # 缺少客户返回 None；已有客户的金额 0 正常保留。
    return balances.get(customer_id)
```

**service.py：决定查不到客户时怎样处理。**

```python
from repository import fetch_amount


class CustomerNotFoundError(LookupError):
    pass


def query_receivable(customer_id: str) -> dict:
    amount = fetch_amount(customer_id)  # 调用取数模块，业务规则留在本层。
    if amount is None:  # 只将缺失视为失败，不把零金额判成失败。
        raise CustomerNotFoundError("客户不存在")
    return {"customer_id": customer_id, "amount": amount}
```

**main.py：读取配置，调用业务，展示结果并记录查询结束。**

```python
import os
from pathlib import Path

from service import CustomerNotFoundError, query_receivable


def main():
    # 从程序外读取客户编号；未设置时使用 C001。
    customer_id = os.getenv("CUSTOMER_ID", "C001")
    try:
        print(query_receivable(customer_id))  # 入口调用业务并展示结果。
    except CustomerNotFoundError as error:
        print("查询失败：", error)

    # __file__ 是当前代码文件；日志固定写到它旁边。
    log_path = Path(__file__).with_name("query.log")
    with log_path.open("a", encoding="utf-8") as stream:  # 追加写入，退出时关闭文件。
        stream.write(f"本次查询结束：{customer_id}\n")


# 仅直接运行时启动；被 import main 时不调用 main()。
if __name__ == "__main__":
    main()
```

本例沿用前章的异常思路；完整输入校验与筛选可放入 service，规则回查 [02 §6](02-types-and-contracts.md#6)。

## 3. 入口、配置与资源各负责什么

关键用途已写在代码注释中。补充两点：

- 入口判断只控制其下的代码；条件块外的顶层代码首次导入时仍会执行。
- 环境变量读取为字符串；以后需要数字配置时，再做转换与检查。

`__init__` 的初始化用途与 `__name__` 的入口判断，集中回查 [初始化与运行入口](python-reference.md#class-init-and-entry)。本章只用标准库，无需额外安装。

## 4. 运行与一个小练习

在项目根目录运行：

```sh
python3 learning/01-python-api/04-mini-project/main.py
```

默认输出 `{'customer_id': 'C001', 'amount': 12800}`，并向脚本同目录的 query.log 追加一条记录。只对本次运行指定客户：

```sh
CUSTOMER_ID=C002 python3 learning/01-python-api/04-mini-project/main.py
```

| 编号 | 预期输出 |
| --- | --- |
| C002 | `{'customer_id': 'C002', 'amount': 0}` |
| C999 | 查询失败： 客户不存在 |

若报 ModuleNotFoundError，先检查三个文件是否同目录、文件名是否正确。

命令 `python3 -c 'import main'` 中，-c 表示执行后面的代码字符串；这里执行的是导入语句，main.py 中的 `__name__` 为 "main"。引号让终端将整段代码交给 Python。

**练习：** 在该示例目录执行 `python3 -c 'import main'`，是否会查询和写日志？若改用真实接口取数，优先改哪个文件？

??? note "参考答案"
    不会查询或写日志：导入不执行受入口判断保护的 main()。

    优先替换 repository.py 的 fetch_amount，保持“找到返回金额、缺失返回 None”的约定；接口故障应明确失败，不当作客户不存在。

## 检查清单与答疑

- [ ] 能指出三个文件的职责及调用关系。
- [ ] 能区分直接运行与导入。
- [ ] 能解释配置来源、日志路径和文件关闭时机。

答疑：`__name__` 回查 §3，`__init__` 回查 [笔记](python-reference.md#class-init-and-entry)，-c 见 §4。练习可选。

## 资料与下一步

三个客户的输出及导入不触发查询已核对；本轮仅补注释和精简正文，代码逻辑未改。[Python 模块教程](https://docs.python.org/zh-cn/3.12/tutorial/modules.html) · [文件与 with](https://docs.python.org/zh-cn/3.12/tutorial/inputoutput.html#reading-and-writing-files)（资料于 2026-10-20 核实）。

[下一章：async / await 与任务生命周期](05-async-and-tasks.md) · [返回模块目录](index.md)
