balances = {"C001": 12800, "C002": 0}


def fetch_amount(customer_id: str) -> int | None:
    # 缺少客户返回 None；已有客户的金额 0 正常保留。
    return balances.get(customer_id)
