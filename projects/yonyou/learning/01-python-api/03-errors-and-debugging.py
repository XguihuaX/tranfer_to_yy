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
