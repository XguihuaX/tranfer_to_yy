import asyncio
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def main():
    server_file = Path(__file__).with_name("mcp_server.py")
    parameters = StdioServerParameters(command=sys.executable, args=[str(server_file)])
    async with Client(parameters) as client:
        catalog = await client.list_tools()
        print("已发现工具：", [item.name for item in catalog.tools])
        result = await client.call_tool("lookup_balance", {"customer_id": "C001"})
        print("是否工具错误：", result.is_error)
        print("结构化结果：", result.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
