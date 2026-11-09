"""无需Key：先核对业务函数与参数，不调用模型。"""
from pydantic import ValidationError

from business import get_balance, search_customers
from query_tools import lookup_balance


def main():
    for customer_id in ("C001", "C002", "C003", "C999"):
        print(customer_id, get_balance(customer_id))
    print("重名候选：", search_customers("海星"))
    try:
        lookup_balance.invoke({"customer_id": "随便一个客户"})
    except ValidationError:
        print("格式错误已被拦下，业务函数没有被调用。")


if __name__ == "__main__":
    main()
