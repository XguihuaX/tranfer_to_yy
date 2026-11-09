import httpx
from domain import CustomerNotFoundError
from models import Receivable


class UpstreamTimeoutError(TimeoutError):
    pass


class UpstreamError(Exception):
    pass


async def fetch_receivable(
    client: httpx.AsyncClient, customer_id: str, *, min_amount: int | None = None
) -> Receivable | None:
    # 不传 None 给查询参数；设置为 0 时则确实发送门槛 0。
    params = {} if min_amount is None else {"min_amount": min_amount}
    try:
        # 复用传入的客户端，异步等待上游响应，不在每次调用时新建连接池。
        response = await client.get(
            f"/customers/{customer_id}/receivable", params=params
        )
        response.raise_for_status()  # 收到 404/500 等响应后，显式转成 HTTP 异常。
    # 超时属于 RequestError，先捕获它以便上层单独返回 504。
    except httpx.TimeoutException as error:
        raise UpstreamTimeoutError("ERP 查询超时") from error
    except httpx.RequestError as error:
        raise UpstreamError("无法连接 ERP 接口") from error
    except httpx.HTTPStatusError as error:
        # 此处的业务解释依据本教材固定端点的约定。
        if error.response.status_code == 404:
            raise CustomerNotFoundError("客户不存在") from error
        raise UpstreamError(f"ERP 返回 HTTP {error.response.status_code}") from error

    try:
        # 先解析 JSON，再核对字段；HTTP 200 不保证数据符合模型。
        data = response.json()
        return None if data is None else Receivable.model_validate(data)
    # JSON 解析错误和 Pydantic 校验错误均属于 ValueError。
    except ValueError as error:
        raise UpstreamError("ERP 响应不符合约定") from error
