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
