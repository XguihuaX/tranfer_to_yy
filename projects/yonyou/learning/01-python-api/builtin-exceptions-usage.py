def parse_limit(raw) -> int:
    limit = int(raw)  # 不可转换的字符串自动产生 ValueError；None 产生 TypeError
    if limit < 1:
        raise ValueError("查询条数至少为 1")  # 主动检查业务条件
    return limit


for raw in ["abc", "0", None, "5"]:
    try:
        print("查询条数：", parse_limit(raw))
    except (TypeError, ValueError) as error:
        print("无效参数：", type(error).__name__)
