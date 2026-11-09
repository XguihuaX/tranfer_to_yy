"""03 教学 MVP：在 PyCharm 中运行本文件，从计算工具走到 LangChain Agent。

阅读顺序：① 两个工具 → ② main → ③ run_agent；settings.py 按需查看。
配套手册：http://127.0.0.1:8765/03-llm-tools/mvp-walkthrough.html
"""

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool

from settings import make_model


# 【首先只关注这里】每次修改 MODE 后重新运行 main.py。
# local：程序直接执行两次工具，不请求模型、不需要 Key。
# model：只发一次模型请求，观察 messages 和 AIMessage，需服务配置。
# agent：模型决定调用工具，框架执行并回填结果，需支持工具调用的模型。
MODE = "local"
QUESTION = "每盒有12支笔，买了3盒，又单独买8支，一共有多少支？请使用工具计算。"

# 提示词是给模型的指令，不是 Python 的执行语句。
# 它引导模型使用工具；实际有没有调用，要看下面打印的消息记录。
SYSTEM_PROMPT = """你是中文计算助手。
需要加法或乘法时，调用对应工具，以工具结果为依据回答。
先完成有依赖关系的中间计算，再把结果用于下一步。
缺少数字或题意不明确时，先询问。最后简洁说明计算过程和结果。
"""


# 【① 本机工具】函数体是 Python 真正执行的计算。
# @tool 把函数包装成 LangChain 工具：名称、说明、参数结构可提供给模型。
# a: int 表示整数参数，-> int 表示返回整数；本例只处理整数加法/乘法。
# 三引号里的说明也会成为工具描述，帮助模型判断何时使用它。
@tool
def multiply(a: int, b: int) -> int:
    """将两个整数相乘。用于计算每份数量乘以份数等乘法问题。"""
    return a * b  # 可在此打断点：看看程序实际收到的 a、b。


@tool
def add(a: int, b: int) -> int:
    """将两个整数相加。用于合并两个数量等加法问题。"""
    return a + b


def run_local():
    """先检查工具能执行：调用顺序和参数都由下面的代码直接指定。"""
    # 包装成工具后，通过 .invoke(参数字典) 调用。
    # 字典键 a、b 对应函数参数；第一次返回的 subtotal 是一个整数。
    subtotal = multiply.invoke({"a": 12, "b": 3})
    total = add.invoke({"a": subtotal, "b": 8})
    print("本地工具演示（没有请求模型）：")
    print(f"multiply(12, 3) → {subtotal}")
    print(f"add({subtotal}, 8) → {total}")
    # local 不读取 QUESTION。改变题目后，要相应改上面的固定参数。


def run_model(model):
    """仅调用模型：本次请求没有向模型提供工具。"""
    messages = [
        SystemMessage(content="你是中文助手，请简洁回答并说明计算过程。"),
        HumanMessage(content=QUESTION),
    ]
    # 建议断点 1：执行前看 messages，执行后看 response。
    response = model.invoke(messages)
    print("模型回答：", response.text)
    # 即便回答是 44，也可能是模型自己生成的；这里没有执行本地工具。
    print("本次用量：", response.usage_metadata)


def run_agent(model):
    """把同样的模型与本地工具连接起来，执行一次完整任务。"""
    # 【③ 组装 Agent】提供客户端、可用工具和应用规则。
    # create_agent 只组装流程；真正开始处理问题的是下一段 agent.invoke。
    agent = create_agent(
        model=model,
        tools=[multiply, add],
        system_prompt=SYSTEM_PROMPT,
    )

    # 输入是一个字典，其中 messages 保存本次对话消息。
    # 框架在内部循环：请求模型 → 如有工具请求则执行 → 回填 → 再请求模型。
    # 模型最终给出普通回答时，循环结束。我们不需要手写这个循环。
    # recursion_limit 限制图执行步数；并非精确的请求次数或费用上限。
    result = agent.invoke(
        {"messages": [HumanMessage(content=QUESTION)]},
        config={"recursion_limit": 12},
    )

    # 建议断点 2：看 result["messages"]，它记录本次任务的消息过程。
    # 下面是“完成后回看”的轨迹，不是实时流式输出。
    print("\n本次消息记录：")
    for message in result["messages"]:
        if isinstance(message, HumanMessage):
            print("[用户]", message.text)
        elif isinstance(message, AIMessage):
            for call in message.tool_calls:
                # 模型输出名称和参数；真正计算仍发生在上面的 Python 函数。
                print(f"[模型请求工具] {call['name']}，参数={call['args']}")
            if message.text:
                print("[模型文本]", message.text)
        elif isinstance(message, ToolMessage):
            # 工具结果回填后也成为消息；模型据此继续下一步。
            print(f"[工具返回] {message.name} → {message.text}")


def main():
    """【② 程序入口】先选运行方式，需要模型时才创建客户端。"""
    print(f"当前运行方式：{MODE}")
    if MODE == "local":
        run_local()
    elif MODE in {"model", "agent"}:
        model = make_model()  # 读取配置并创建客户端，此行还未发送模型请求。
        if MODE == "model":
            run_model(model)
        else:
            run_agent(model)
    else:
        raise ValueError("MODE 只能是 local、model 或 agent")


# 点击运行 main.py 时进入 main；被其他文件导入时，不自动执行任务。
# 学习版保留原始异常，便于在 PyCharm 看到出错文件、行号与错误类型。
if __name__ == "__main__":
    main()
