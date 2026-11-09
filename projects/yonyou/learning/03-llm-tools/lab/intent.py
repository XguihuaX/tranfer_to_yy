"""格式校验与业务执行是两步。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from business import get_balance


class QueryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["query_balance", "clarify"]
    customer_id: str | None = Field(default=None, pattern=r"^C\d{3}$")


def execute_intent(intent: QueryIntent) -> dict:
    if intent.action == "clarify":
        return {"status": "need_clarification", "question": "请提供明确的客户编号。"}
    if intent.customer_id is None:
        raise ValueError("查询余额需要客户编号；应先澄清")
    return get_balance(intent.customer_id)
