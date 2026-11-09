# 01-05 async / await 与任务生命周期

> 教材状态：精简正文已准备。更新：2026-10-22。

## 本章目标与前置

本章解决“多个查询在等待时，怎样安排执行、超时和取消”。沿用前文的函数、异常和入口知识。阅读约 15–20 分钟，示例仅用标准库 `asyncio`；使用 Python 3.11+，已在 Python 3.12 核对。

## 1. async 与 await 分别做什么

请求接口、读写网络等操作会花时间等待。异步程序可以在某个任务等待时，让其他就绪任务继续执行。负责安排这些任务的机制称为事件循环。

`async def` 定义异步函数。调用它首先得到一个**协程对象**，可以理解为一份尚待执行的异步工作；写 `await` 才在当前协程中等待它的结果，等待过程中可以让出执行机会。异步函数的 `-> int` 描述 await 完成后得到的结果类型。

```python
async def fetch_amount(customer_id: str) -> int:
    # 模拟等待网络；不占着事件循环空等。
    await asyncio.sleep(0.2)
    return balances[customer_id]
```

这段是下面完整示例的函数定义，`asyncio.sleep` 用来模拟接口等待，不会真的访问服务器。若连续写两个 `await fetch_amount(...)`，仍然是第一个完成后才执行第二个；需要显式组织并发。

## 2. 顺序、并发、超时和取消放在一起看

下面只新增异步调度，合成客户与金额沿用前文。`gather` 将多个协程安排为并发工作，并按传入顺序收集结果。`create_task` 则把一个协程安排成可持有、可取消的任务对象。

```python
import asyncio

balances = {"C001": 12800, "C002": 0}


async def fetch_amount(customer_id: str) -> int:
    # 模拟网络等待；等待时让其他就绪任务有机会执行。
    await asyncio.sleep(0.2)
    return balances[customer_id]


async def main():
    # 两次 await 依次完成，第二次查询在第一次结束后才开始。
    sequential = [await fetch_amount("C001"), await fetch_amount("C002")]
    print("顺序结果：", sequential)

    # 同时安排两项工作；收集结果时仍按传入顺序排列。
    concurrent = await asyncio.gather(fetch_amount("C001"), fetch_amount("C002"))
    print("并发结果：", concurrent)

    # 查询模拟等待 0.2 秒，这里只允许等待 0.05 秒，演示超时。
    try:
        await asyncio.wait_for(fetch_amount("C001"), timeout=0.05)
    except TimeoutError:
        print("查询超时")

    # 保存任务对象，才能在后面主动请求取消。
    task = asyncio.create_task(fetch_amount("C001"))
    await asyncio.sleep(0)  # 让刚安排的任务先获得一次执行机会。
    task.cancel()  # 发出取消请求；不是强行终止任意代码。
    try:
        await task  # 等任务响应取消，并在这里接到取消信号。
    except asyncio.CancelledError:
        print("查询已取消")


if __name__ == "__main__":
    asyncio.run(main())  # 为脚本建立事件循环，结束后收尾。
```

`asyncio.run(main())` 为脚本建立事件循环，运行 main 并在结束后收尾。`await asyncio.sleep(0)` 让已安排的查询任务有机会开始执行，然后演示主动取消。

在项目根目录运行已提供的文件：

```sh
python3 learning/01-python-api/05-async-and-tasks.py
```

预期输出：

```text
顺序结果： [12800, 0]
并发结果： [12800, 0]
查询超时
查询已取消
```

两组正常结果相同，区别是等待怎样安排：顺序部分包含两段依次发生的约 0.2 秒等待，并发部分把两段等待重叠起来。时间取决于调度与环境，这里不把它作为性能测试。

## 3. 任务怎样结束

| 路径 | 调用者看到什么 | 本例中的位置 |
| --- | --- | --- |
| 正常完成 | 返回值 | sequential、concurrent |
| 执行失败 | 异常传播 | 例如传入未知客户会在字典取值时出错 |
| 等待超时 | 本例中的 TimeoutError | wait_for 分支 |
| 主动取消 | 被等待的任务抛 CancelledError | task.cancel 后的 await |

本例的 `wait_for` 超时会请求取消被等待的查询，并等待它响应取消。`task.cancel()` 同样是发出取消请求，任务需要有机会运行才能处理它；不能把取消当作强行结束任意代码的开关。需要关闭文件、连接时，可沿用上一章的资源管理方式，或在 `finally` 清理；处理取消时完成必要清理后通常继续传播取消信号。

`CancelledError` 不会被普通的 `except Exception` 捕获。这里在管理任务的 main 中专门捕获，是为了展示取消后的处理结果。

`gather` 默认在某项失败时向调用者传播该异常，但不会自动取消其他仍在执行的项。需要一并收尾时应明确管理任务；本章正常批量示例中的两项都成功，不能从这个输出推断失败时也会得到完整结果列表。

## 4. 易错点与一个小练习

- 只写 `fetch_amount("C001")` 而不 await 或调度，不会执行这次查询，常会看到“协程未被等待”的提示。
- 把函数改成 async 不会自动并发；本例使用 gather 明确组织多个查询。
- 在这里使用 `time.sleep` 或直接执行长时间阻塞调用，会阻塞事件循环。已有同步 I/O 代码可按需用 `await asyncio.to_thread(...)` 移到线程执行；它不保证 CPU 密集计算会因此加速，也不应在每次短字典查询外机械套线程。

取消对线程工作的等待，也不等于能强行终止线程中已经开始的同步操作。

**练习：** 将顺序部分的两个 await 改为 gather，并说明为什么结果顺序仍与客户传入顺序一致。再把超时门槛从 0.05 改为 0.5，哪条输出预计消失？

??? note "参考答案"
    可写 `sequential = await asyncio.gather(fetch_amount("C001"), fetch_amount("C002"))`。gather 的结果按传入顺序排列，不按完成先后排列。

    超时门槛改为 0.5 秒后，模拟的 0.2 秒等待通常能正常完成，“查询超时”不再打印。主动取消是后面的独立操作，“查询已取消”仍会打印。

## 检查清单与答疑

- [ ] 能区分调用异步函数、await 和创建任务。
- [ ] 能解释两个连续 await 与 gather 的执行差异。
- [ ] 能区分正常返回、失败、超时与主动取消。

答疑：暂无。真实 HTTP 调用在 01-08 接入，这里先确认任务的执行与结束方式。

## 资料与后续

完整输出、未知客户失败、超时与取消分支已核对。原示例于 2026-10-20 核实，gather 失败传播说明于 2026-10-22 复核：[asyncio 协程与任务](https://docs.python.org/zh-cn/3.12/library/asyncio-task.html)。

[下一章：HTTP 与 JSON](06-http-and-json.md) 已准备，将这里的异步机制逐步接到真实 HTTP 调用。

[上一章：模块与小型工程组织](04-modules-and-project.md) · [返回模块目录](index.md)
