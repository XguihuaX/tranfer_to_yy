from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt


# 接口新增的编号格式：C 后恰好三位数字。
CustomerId = Annotated[str, Field(pattern=r"^C[0-9]{3}$")]

# 金额非负且必须是整数，拒绝字符串数字和布尔值。
Amount = Annotated[StrictInt, Field(ge=0)]


class QueryInput(BaseModel):
    # 拒绝多余字段，避免把 min_amout 之类的拼写错误静默忽略。
    model_config = ConfigDict(extra="forbid")
    customer_id: CustomerId
    min_amount: Amount | None = None  # 省略或传 null 时，不设置门槛。



# 成功结果的结构；供服务端输出和客户端解析共同使用。
class Receivable(BaseModel):
    customer_id: CustomerId
    amount: Amount
