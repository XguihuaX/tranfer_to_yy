from repository import fetch_amount


class CustomerNotFoundError(LookupError):
    pass


def query_receivable(customer_id: str) -> dict:
    amount = fetch_amount(customer_id)  # 调用取数模块，业务规则留在本层。
    if amount is None:  # 只将缺失视为失败，不把零金额判成失败。
        raise CustomerNotFoundError("客户不存在")
    return {"customer_id": customer_id, "amount": amount}
