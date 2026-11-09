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
