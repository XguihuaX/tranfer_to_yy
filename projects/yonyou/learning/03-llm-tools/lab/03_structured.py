from intent import QueryIntent, execute_intent
from model_config import make_model


def main():
    model = make_model()
    extractor = model.with_structured_output(QueryIntent, method="function_calling")
    intent = extractor.invoke(
        "提取查询意图。客户编号不明确就选clarify，不能猜编号。问题：查C001的欠款。"
    )
    print("结构化意图：", intent.model_dump())
    print("业务执行结果：", execute_intent(intent))


if __name__ == "__main__":
    main()
