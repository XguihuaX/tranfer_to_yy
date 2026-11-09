from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from business import get_balance

mcp = MCPServer("Synthetic receivables")


@mcp.tool(structured_output=True)
def lookup_balance(customer_id: Annotated[str, Field(pattern=r"^C\d{3}$")]) -> dict[str, object]:
    """查询合成客户余额；not_found表示客户不存在。"""
    return get_balance(customer_id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
