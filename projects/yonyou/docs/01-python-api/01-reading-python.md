# 01-01 跟着数据读懂 Python 函数

> 教材状态：已准备。用户阅读与练习状态见本模块进度记录，教材完成不代表已经掌握。更新：2026-10-22。

## 本章目标与前置知识

本章作为应收查询案例的简短复习，重点保留成功结果与异常处理的衔接。已知函数参数、`return` 与 `print` 的读者，可略过 §2–4 和 §6，按需看 §5 的异常说明；§7–8 供运行与排错时速查。

本章不需要第三方依赖，使用合成数据。快速浏览约 5–10 分钟，练习可选。后续重点转向类型约定、异常与模块组织，再进入异步和 API 工程。

## 1. 从一次应收查询开始

假设同事问：“客户 C001 现在还有多少应收？”我们先用两条合成记录回答：C001 应收 12800 元，C002 应收 0 元。这里假设每个客户只有一个以人民币元计的汇总金额，不涉及组织、日期、单据或多币种计算。

程序要完成三个动作：接收客户编号，查找金额，交回带有客户编号的结果。如果编号不在数据里，就明确说明查询失败。

先沿着这条路线阅读：

```text
客户编号 "C001" → 查询函数 → 结果字典 → 取出 amount → 显示 12800
```

后面会把数据来源换成接口或数据库，但本章先把这条执行路线读清楚。所有数据均为合成数据，代码不连接任何外部服务。

## 2. 字典：用客户编号找到金额

```python
balances = {"C001": 12800, "C002": 0}
```

`balances["C001"]` 得到 `12800`；`"C002" in balances` 为 `True`。这里仅提醒一个业务边界：检查字典里的客户键是否存在，与检查金额是否为 0 不同。字典操作可按需查阅 [Python 官方教程](https://docs.python.org/zh-cn/3/tutorial/datastructures.html#dictionaries)。

## 3. 函数与参数：把一次查询组织起来

本例函数签名为 `query_receivable(customer_id)`，调用时传入客户编号，例如 `query_receivable("C001")`。完整代码集中放在 §6，避免重复展开。

目前函数从外面的 `balances` 读取数据；[04 章](04-modules-and-project.md#2) 将取数封装到模块，[08 章](08-httpx-and-upstream.md#2) 展示将客户端对象显式传入调用函数。这里的关注点是：参数决定“查谁”，数据源决定“能查到什么”。

## 4. return 与 print：结果交到哪里

### 4.1 return 把结果交回调用处

成功时返回 `{"customer_id": "C001", "amount": 12800}`，由 `result = query_receivable("C001")` 接收。后面的程序可以继续处理这个字典。

### 4.2 print 把内容显示出来

`print(result["amount"])` 只显示 `12800`，不改变返回结果。后续接口需要的是可继续处理的数据，函数保持返回结果，显示逻辑放在调用处。本节基础区别不再展开。

## 5. raise 与 try-except：失败时走哪条路

### 5.1 用 raise 中断失败的查询

本例在客户不在数据中时 `raise ValueError("客户不存在")`，本次调用不会继续到 return。§6 保留原始完整代码；异常类型选择与主动抛出统一见 [01-03 §2–3](03-errors-and-debugging.md#2)。

### 5.2 用 try-except 处理预期失败

调用处用 `except ValueError as error` 接住这次异常并显示说明；成功时跳过 except，失败时跳过 try 中尚未执行的正常语句。捕获范围、变量 error、循环位置与逐行执行统一见 [01-03 §2.1](03-errors-and-debugging.md#loop-execution)。本章只保留读懂原例所需的这条路线。

## 6. 完整示例（参考）

### 6.1 原始短代码

这是第一轮聊天中使用的原始示例，保留原题的行为：

```python
balances = {"C001": 12800, "C002": 0}

def query_receivable(customer_id):
    if customer_id not in balances:
        raise ValueError("客户不存在")
    return {"customer_id": customer_id, "amount": balances[customer_id]}

try:
    result = query_receivable("C001")
    print(result["amount"])
except ValueError as error:
    print("查询失败：", error)
```

本节仅保留完整代码供查阅，不再按语句推演执行。正常与失败结果见 §7 的速查表。

## 7. 如何运行与核对输出

### 7.1 运行方式

可选：将 §6.1 代码保存到 `learning/01-python-api/receivable.py`，从项目根目录运行。仅需 Python 3，无额外依赖。

```sh
python3 learning/01-python-api/receivable.py
```

### 7.2 三次独立运行的预期结果

每次只修改调用处的客户编号，重新运行脚本：

| 参数 | 输出 | 含义 |
| --- | --- | --- |
| `"C001"` | `12800` | 查询成功 |
| `"C002"` | `0` | 客户存在，记录金额为 0 |
| `"C999"` | `查询失败： 客户不存在` | 抛出异常，跳过金额打印，进入 `except` |

三种情况已运行核对。未知客户不产生本次查询结果；交互环境中已有的旧 `result` 不能当成本次结果。

### 7.3 常见运行问题

遇到文件找不到先查路径；`NameError` 查变量名与代码是否完整；`KeyError` 查访问的键。报错时保留错误原文和对应代码即可，不再逐项讲编辑器与复制操作。

## 8. 容易混淆的地方

### 8.1 "customer_id" 与 customer_id

返回字典中，左边的 `"customer_id"` 是字段名，右边的 `customer_id` 是参数值。

### 8.2 客户存在，与金额非零

`if not balances[customer_id]` 不能判断客户不存在：它会把 0 当成假，未知键还会先抛 `KeyError`。本例用 `not in` 检查键。

### 8.3 返回字典，与修改原字典

给返回字典添加 `currency`，不会自动修改 `balances`。

### 8.4 抛异常，与返回一个错误字符串

`raise` 进入异常处理；`return "客户不存在"` 则正常返回字符串，调用者继续执行 `result["amount"]` 会产生 `TypeError`。成功结果的结构应保持一致，失败通过约定的方式处理。

## 9. 动手练习

以下保留原来的三题，供需要时自查；熟悉这些基础可略过，不作为进入后续内容的门槛。允许借助 AI，实际提交的解释、修改与排错再单独记录验证情况。

### 练习 1：区分打印内容与返回值

针对 §6.1 的原代码，写出屏幕输出，以及执行完后 `result` 保存的完整内容。再用一句话解释这两者为什么不一样。

??? note "完成练习 1 后查看：参考答案与推理"
    屏幕输出 `12800`。`result` 的完整内容是 `{"customer_id": "C001", "amount": 12800}`。

    函数用 `return` 交回字典，赋值语句保存它；`print(result["amount"])` 只读取其中的金额并显示。打印一个字段不改变整个字典。

### 练习 2：跟踪成功与失败路径

分别把调用处的客户编号改成 `"C002"`、`"C999"`，写出各自的输出。对于 C999，`print(result["amount"])` 是否执行？请用“条件判断 → 返回或异常 → 调用处”的顺序解释。

??? note "完成练习 2 后查看：参考答案与推理"
    C002 输出 `0`。编号存在，`not in` 条件不成立，返回 `{"customer_id": "C002", "amount": 0}`，再打印金额。

    C999 输出 `查询失败： 客户不存在`。编号不存在，条件成立，抛出 `ValueError`。函数没有执行 `return`，调用处这次赋值没有完成；`try` 中剩余的金额打印被跳过，进入匹配的 `except`。因此 `print(result["amount"])` 不执行。

### 练习 3：修改返回结果

让成功返回的字典增加 `"currency": "CNY"`，贴出修改后的函数，说明你修改的是查询数据还是交回的结果。用 C001 核对完整结果，并解释为什么原来的屏幕输出仍只有金额。

??? note "完成练习 3 后查看：参考答案与推理"
    ```python
    def query_receivable(customer_id):
        if customer_id not in balances:
            raise ValueError("客户不存在")
        return {
            "customer_id": customer_id,
            "amount": balances[customer_id],
            "currency": "CNY",
        }
    ```

    修改的是返回结果字典，`balances` 没有变化。本章数据统一按人民币元计，因此可以使用固定的币种说明。多行书写只是为了便于阅读。

    C001 的结果为 `{"customer_id": "C001", "amount": 12800, "currency": "CNY"}`。调用者仍然只执行 `print(result["amount"])`，所以原输出仍是 `12800`。要检查新字段，可以在成功路径暂时增加 `print(result)` 或 `print(result["currency"])`。

如选择提交练习，按 1 / 2 / 3 回复即可；运行不一致时附代码和报错原文。参考答案供自查，不把浏览答案计为练习验证。

## 本章检查清单

- [ ] 能指出 `balances` 的键和值，以及结果字典的字段。
- [ ] 能指出函数定义、调用、参数及这次传入的值。
- [ ] 能分别写出原代码的返回结果与屏幕输出。
- [ ] 能解释 C002 为什么成功、C999 为什么失败。
- [ ] 能解释异常发生后哪条语句被跳过。
- [ ] 能独立添加币种字段，并核对完整结果。

勾选用于自查。实际掌握状态以你提交的解释、修改和排错证据为准，记录在模块进度中。

## 阅读中产生的答疑

### 问：Python 是不是还有一些“进阶库”？

有，可按用途区分：[标准库](https://docs.python.org/zh-cn/3/library/)中的 `collections`、`functools` 等通用工具，接口开发中的 [FastAPI](https://fastapi.tiangolo.com/)、Pydantic、[HTTPX](https://www.python-httpx.org/)，以及 [pandas](https://pandas.pydata.org/docs/getting_started/overview.html) 等数据处理库。

后续在任务需要时一起说明库的用途、关键调用和容易出错的地方；已有基本认识的内容简要带过，不单独从库的定义开始讲。

## 资料与后续

本章示例由本项目编写，使用合成数据并在本机 Python 3 核对；不依赖最新语言特性。官方参考于 2026-10-15 核实，阅读本章不要求先读完这些文档：

- [Python 官方教程：字典](https://docs.python.org/zh-cn/3/tutorial/datastructures.html#dictionaries)。
- [Python 官方教程：定义函数](https://docs.python.org/zh-cn/3/tutorial/controlflow.html#defining-functions)。
- [Python 官方教程：错误和异常](https://docs.python.org/zh-cn/3/tutorial/errors.html)。

后续沿类型与参数约定、异常和模块组织，进入异步与 HTTP；已知内容简要带过，库结合任务介绍。[下一章：01-02 类型与函数参数约定](02-types-and-contracts.md) 已准备，可以直接继续阅读。

[返回模块目录](index.md)
