# 03-08 MCP：把工具提供给另一个程序

> 教材已准备，2026-11-08。本章为基础认知与可选本机实验，使用MCP Python SDK 2.3.0。无需模型Key。

## 本章问题、目标与前置

查询函数写在当前项目里，另一个Agent程序怎样发现并使用它？本章讲MCP中的Host、Client、Server，沿用余额函数做发现与调用。读完应能区分工具协议、模型API和Agent框架，并知道接入所需步骤。

前置为[工具调用](04-tools-loop.md)与02的进程/标准输入输出。约30–40分钟。远程服务认证、多用户授权和正式部署留到实际接入；不要求现在学习整个协议实现。

## 1. 从本地函数到跨程序工具

03-04直接import业务函数，调用发生在同一个Python进程。另一个程序可能不是Python写的，也不知道你的模块路径。MCP提供共同的协议，让工具提供者说明有哪些工具、输入需要什么，以及怎样请求执行和返回结果。

它没有把模型训练成查账模型，也不替你做客户权限。Server仍要调用业务系统或函数，Host仍要决定让哪个模型看到哪些工具。

## 2. Host、Client、Server各在什么位置？

| 角色 | 职责 | 本章例子 |
| --- | --- | --- |
| Host | 使用模型和工具的应用，管理整体交互 | 实际Agent应用；本例用小客户端代替其中的连接部分 |
| MCP Client | 与一个Server建立协议连接、列工具、调用工具 | mcp_client.py中的Client |
| MCP Server | 暴露工具定义并执行请求 | mcp_server.py |

一次模型工具调用和一次MCP调用是相邻但不同的步骤：模型先生成工具请求，Host的执行器再通过MCP Client发给Server，拿到结果后继续回填给模型。MCP本身不会要求你使用LangChain或某个模型。

## 3. Skill、MCP、HTTP API和框架如何区分？

Skill主要提供做事说明与资源；MCP是发现和调用外部能力的协议；普通HTTP API也能执行查询，但调用方需知道约定的路径、参数和响应；LangChain把模型与工具组织进应用。

同一个业务函数可以包成FastAPI接口，也可以包成MCP工具；还可以让MCP Server内部再调用现有ERP HTTP接口。选择取决于消费者和集成方式，不需要为了MCP重写所有业务逻辑。

## 4. stdio与Streamable HTTP是什么？

stdio指用子进程的标准输入、标准输出传协议消息：客户端启动服务进程，双方通过管道通信，不需要监听端口。这与02学过的输出通道相连。服务的stdout应保留给协议，调试日志写stderr。

Streamable HTTP通过HTTP地址连接Server，适用于独立运行或远程部署。它需要网络可达、认证与服务管理；不是把stdio的命令名换成一个URL就完成部署。旧教程中的SSE传输和当前HTTP用法可能不同，要与SDK版本对应。

MCP工具结果还区分供模型阅读的content和供程序读取的structured_content；业务返回not_found也可能是一次协议调用成功的结果。不要只看连接没报错就说余额查询成功。

## 5. 完整Server：复用原业务函数

先安装可选依赖，Mac本机Terminal、工作目录为lab，使用你为lab准备的解释器：

```sh
.venv/bin/python -m pip install -r requirements-mcp.txt
```

`mcp_server.py`：

```python
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
```

`MCPServer`建立服务，`@mcp.tool`注册函数；这里显式启用结构化结果，返回类型也提供了可描述的字典。`Annotated`把前章Field模式附在字符串类型上，用于检查客户编号；它在这里不是新增的一套业务规则。

Server只调用原来的get_balance，数据与C001=12800保持一致。启动时用stdio，不打开HTTP端口，也不访问模型服务。

## 6. 完整Client：先发现，再调用

`mcp_client.py`：

```python
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
```

`sys.executable`指当前运行客户端的Python解释器，保证子进程也用同一套依赖；Path跟随当前脚本定位Server，避免启动目录变化找不到文件。

构造StdioServerParameters描述要启动的命令。`async with Client(...)`才建立连接并协商协议；退出块时释放连接与子进程。list_tools取得目录，call_tool提交工具名和参数，客户端此时不需要模型参与。

运行时只需启动客户端，不必先手动启动另一个stdio服务进程。它会启动自己那份Server。预期发现lookup_balance，is_error为False，并在structured_content中看到status=ok、amount=12800等数据。

本例只证明外部程序能通过MCP调用该能力。若把它接给模型，还需要Host将发现的工具适配成模型可用定义，并把调用结果回填，机制回到03-04。

## 7. 如果要接回LangChain，需要哪些步骤？

1. 确认MCP Server能独立被列出和调用。
2. 在应用里选择兼容的MCP适配器，维护连接生命周期。
3. 将发现的工具转换为LangChain工具，传给create_agent。
4. 验证模型提出请求→适配器→Server→结果回填的完整路线，核对参数与业务状态。

当前LangChain 1.4提供`langchain.mcp.MCPAdapter`，依赖额外的FastMCP且标为beta；旧教程常用`langchain-mcp-adapters`，API不相同。本章固定使用官方MCP SDK做最小独立实验，不把两套例子混在一个脚本里。正式接回时按所选适配器版本补齐连接代码并实际验证。

## 8. 操作步骤与常见误区

在PyCharm创建mcp_client.py的Run配置，解释器仍是lab环境；安装可选依赖后运行。查看列出的工具名与返回结构；把参数换成C999，应得到not_found，不能显示0；换成错误编号，应观察工具错误。

若ModuleNotFoundError，核对安装可选依赖的解释器；若Server提前退出，看stderr；若协议解析失败，看是否有普通print污染stdout。对stdio程序按Web服务习惯用curl查端口没有意义。

只添加MCP连接不会自动获得真实ERP权限。连接器能做什么、谁能调用、数据范围与写操作控制，仍要在实际服务端设计。

## 9. 可选练习

A. 本例谁负责计算12800？B. is_error=False且业务status=not_found，能说无欠款吗？C. 只有一个SKILL.md写“查询ERP”，为什么还不一定能查？

??? note "参考答案与推理"
    A：business.py的业务函数，MCP负责把调用和结果传过去。B：不能，协议/工具调用成功与客户存在是不同层次，应说明未找到。C：技能说明没有自动提供接口、凭据、工具执行器和权限；需要实际可调用能力。

## 本章回顾与检查清单

MCP把工具能力跨程序提供，模型选择和Agent控制仍属于Host。先验证目录与调用，再接模型，能把集成失败分成较清楚的层次。

- [ ] 能指出Host、Client、Server和原业务函数。
- [ ] 能说明stdio为何不需要端口，以及stdout为何不能随意输出。
- [ ] 知道接回Agent还缺适配和结果回填。

## 阅读中产生的答疑

暂无。先理解§2与§4，再对照§5–6两个文件。

## 来源与后续

核对日期2026-11-08：[MCP架构](https://modelcontextprotocol.io/docs/learn/architecture)、[Python SDK客户端](https://py.sdk.modelcontextprotocol.io/client/)、[传输](https://py.sdk.modelcontextprotocol.io/client/transports/)、[LangChain MCP接入](https://docs.langchain.com/oss/python/langchain/mcp)。后续04模块学习RAG与业务数据接入，05深入LangGraph流程。[返回03目录](index.md)。
