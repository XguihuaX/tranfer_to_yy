"""手动展示工具循环；最多调用模型4次。"""
import json

from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from model_config import make_model
from query_tools import lookup_balance


def run_tool_loop(model, question: str, max_calls: int = 4):
    tools = {lookup_balance.name: lookup_balance}
    bound_model = model.bind_tools(list(tools.values()))
    messages = [
        SystemMessage(content="查询余额必须使用工具；编号不明确先问。按工具结果回答并说明币种和日期。"),
        HumanMessage(content=question),
    ]
    for _ in range(max_calls):
        response = bound_model.invoke(messages)
        messages.append(response)
        if response.invalid_tool_calls:
            raise ValueError("模型返回了无法解析的工具参数，停止本轮")
        if not response.tool_calls:
            return response, messages
        for call in response.tool_calls:
            print("准备执行工具：", call["name"], call["args"])
            selected = tools.get(call["name"])
            if selected is None:
                payload = {"status": "unknown_tool"}
            else:
                try:
                    payload = selected.invoke(call["args"])
                except ValidationError:
                    payload = {"status": "invalid_arguments", "hint": "客户编号必须是C加3位数字"}
            messages.append(ToolMessage(
                content=json.dumps(payload, ensure_ascii=False),
                tool_call_id=call["id"],
            ))
    raise RuntimeError("超过本例模型调用次数上限，请检查消息和工具结果")


if __name__ == "__main__":
    answer, _ = run_tool_loop(make_model(), "查客户C001的未收余额。")
    print(answer.text)
