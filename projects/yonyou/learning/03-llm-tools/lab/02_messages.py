from langchain.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from model_config import make_model


def main():
    model = make_model()
    history = [SystemMessage(content="你是查询助手，只根据给定信息回答。")]
    history.append(HumanMessage(content="我接下来要查的客户编号是C001。"))
    first = model.invoke(history)
    history.append(first)
    history.append(HumanMessage(content="我刚才说的客户编号是什么？"))
    print(model.invoke(history).text)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你负责把提问改写清楚，不查询或猜测余额。"),
        ("human", "把这句话改写成明确查询：{question}"),
    ])
    chain = prompt | model | StrOutputParser()
    print(chain.invoke({"question": "帮我看一下C001的欠款"}))


if __name__ == "__main__":
    main()
