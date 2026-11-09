from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Query

from domain import CustomerNotFoundError, query_receivable
from models import QueryInput, Receivable

app = FastAPI(title="合成 ERP 应收接口")



# GET 与 POST 共用业务调用，只在接口边界把业务异常映射为 HTTP。
def resolve(customer_id: str, min_amount: int | None):
    try:
        return query_receivable(customer_id, min_amount=min_amount)
    except CustomerNotFoundError as error:
        # from error 保留原始原因；404 和 detail 交给框架生成响应。
        raise HTTPException(status_code=404, detail=str(error)) from error



# 注册 GET 入口；response_model 约束成功结果，也允许未命中的 null。
@app.get("/customers/{customer_id}/receivable", response_model=Receivable | None)
def get_receivable(
    # 编号来自 URL 路径；门槛来自问号后的查询参数。
    customer_id: Annotated[str, Path(pattern=r"^C[0-9]{3}$")],
    min_amount: Annotated[int | None, Query(ge=0)] = None,
):
    return resolve(customer_id, min_amount)


@app.post("/receivables/query", response_model=Receivable | None)
def post_receivable(query: QueryInput):
    # JSON 请求体先按 QueryInput 校验，成功后才执行这里的业务调用。
    return resolve(query.customer_id, query.min_amount)
