# 01-02 教材完整示例：类型与函数参数约定
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
