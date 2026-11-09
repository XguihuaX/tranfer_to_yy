from langchain.messages import HumanMessage, SystemMessage

from model_config import make_model


def main():
    model = make_model()
    messages = [
        SystemMessage(content="你是应收查询助手。没有查询结果时，不编造客户余额。"),
        HumanMessage(content="客户C001还欠多少钱？"),
    ]
    response = model.invoke(messages)
    print(response.text)
    print("本次用量：", response.usage_metadata)


if __name__ == "__main__":
    main()
