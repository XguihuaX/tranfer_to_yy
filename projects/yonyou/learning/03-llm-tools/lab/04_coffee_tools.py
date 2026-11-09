"""咖啡店工具调用完整例子，价格和库存均为本地示例数据。

Python 3.12，依赖沿用本目录requirements.txt。
运行前设置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL。
入口需支持Chat Completions工具调用；运行将访问真实模型服务。
"""

import json
import os

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI


# 1. 本地示例数据：price单位为元/杯，stock表示可售杯数。
COFFEE = {
    "美式": {"price": 15, "stock": 10},
    "拿铁": {"price": 20, "stock": 6},
    "摩卡": {"price": 25, "stock": 0},
}


# 2. 三个普通函数。三引号里的说明会成为工具描述。
def get_price(drink: str) -> dict:
    """查询一种咖啡的单杯价格，单位元。drink填写菜单中的饮品名称。"""
    if drink not in COFFEE:
        return {"error": "菜单中没有这种饮品", "drink": drink}
    return {"drink": drink, "price": COFFEE[drink]["price"], "unit": "元/杯"}


def get_stock(drink: str) -> dict:
    """查询一种咖啡还可售多少杯，0表示售罄。drink填写菜单中的饮品名称。"""
    if drink not in COFFEE:
        return {"error": "菜单中没有这种饮品", "drink": drink}
    return {"drink": drink, "stock": COFFEE[drink]["stock"], "unit": "杯"}


def get_menu() -> list[str]:
    """获取菜单中的全部饮品名称；不返回价格或库存。"""
    return list(COFFEE)


# 3. 包装函数：原函数保留，另建包含名称、说明、参数和执行入口的工具对象。
price_tool = tool(get_price)
stock_tool = tool(get_stock)
menu_tool = tool(get_menu)
TOOLS = [price_tool, stock_tool, menu_tool]

# 工具名称来自函数名，例如price_tool.name是get_price，不是price_tool。
TOOLS_BY_NAME = {item.name: item for item in TOOLS}


def answer_question(llm, question: str, max_rounds: int = 5) -> str:
    # 4. 将三个工具的定义提供给模型。
    llm_with_tools = llm.bind_tools(TOOLS)
    messages = [
        SystemMessage(content=(
            "你是咖啡店助手。菜单、价格和库存必须查询工具后再回答。"
            "饮品名称不明确时先询问；工具报告饮品不存在时如实说明。"
            "只处理查询，不下单或扣减库存。用中文简洁回答，并注明是示例数据。"
        )),
        HumanMessage(content=question),
    ]

    # 5. 模型可能先请求工具，拿到结果后再回答，因此需要循环。
    for _ in range(max_rounds):
        response = llm_with_tools.invoke(messages)
        messages.append(response)  # 保存完整模型回复，包括其中的工具请求。

        if response.invalid_tool_calls:
            raise ValueError("模型返回了无法解析的工具参数")
        if not response.tool_calls:
            return response.text  # 没有工具请求，本次回答结束。

        # 一条模型回复可能请求多个工具，逐一执行并回填。
        for call in response.tool_calls:
            name = call["name"]
            args = call["args"]
            if name not in TOOLS_BY_NAME:
                raise ValueError(f"未知工具：{name}")

            print(f"[模型请求] {name}，参数：{args}")
            result = TOOLS_BY_NAME[name].invoke(args)  # 真正执行本地函数。
            print(f"[工具结果] {result}")

            messages.append(ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=call["id"],  # 使用原请求ID，关联请求与结果。
                name=name,
            ))
        # 下一轮invoke会把刚才添加的工具结果一起发给模型。

    raise RuntimeError("达到本例调用轮数上限，尚未获得最终回答")


def main():
    # 6. 从本机运行配置读取接入信息，明确使用Chat Completions接口。
    llm = ChatOpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        model=os.environ["LLM_MODEL"],
        use_responses_api=False,
        timeout=15,
        max_retries=1,
    )
    question = "菜单有哪些咖啡？拿铁多少钱一杯？还剩多少杯？"
    print("用户：", question)
    print("助手：", answer_question(llm, question))


if __name__ == "__main__":
    main()
