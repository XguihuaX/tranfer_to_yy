import os
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable
from models import QueryInput, Receivable



# 应用启动时创建共享客户端，停止时通过 async with 关闭它。
@asynccontextmanager
async def lifespan(app: FastAPI):
    base_url = os.getenv("ERP_BASE_URL", "http://127.0.0.1:8001")
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        app.state.erp_client = client  # 保存给本应用的各次请求复用。
        yield  # 应用在这里运行；关闭应用时才继续离开资源上下文。



# 依赖函数读取应用上的客户端；它不是用户请求体中的一个字段。
def get_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.erp_client


app = FastAPI(title="应收查询调用方", lifespan=lifespan)


@app.post("/receivables/query", response_model=Receivable | None)
async def query_remote(
    query: QueryInput,
    # FastAPI 调用 get_client，再把得到的对象作为 client 参数传入。
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
):
    try:
        return await fetch_receivable(
            client, query.customer_id, min_amount=query.min_amount
        )
    # 在当前 HTTP 边界决定怎样向调用者表达不同失败。
    except CustomerNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UpstreamTimeoutError as error:
        # 上游等待超时，与客户不存在分别处理。
        raise HTTPException(status_code=504, detail=str(error)) from error
    except UpstreamError as error:
        # 上游连接、状态或格式失败，不能伪装成金额 0。
        raise HTTPException(status_code=502, detail=str(error)) from error
