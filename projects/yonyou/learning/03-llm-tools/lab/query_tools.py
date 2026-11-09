from langchain.tools import tool
from pydantic import BaseModel, Field

from business import get_balance, search_customers


class BalanceArgs(BaseModel):
    customer_id: str = Field(pattern=r"^C\d{3}$", description="明确的客户编号，例如C001")


@tool(args_schema=BalanceArgs)
def lookup_balance(customer_id: str) -> dict:
    """按明确客户编号查询合成应收未收余额；不存在返回not_found，不得解释为零。"""
    return get_balance(customer_id)


@tool
def find_customers(query: str) -> dict:
    """按客户名称片段查候选编号；多个候选需请用户选择，不能自行猜测。"""
    return search_customers(query)
