import os

import httpx


def main():
    base_url = os.getenv("ERP_BASE_URL", "http://127.0.0.1:8001")
    # 一批查询共用客户端；离开 with 后关闭连接池。
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        for customer_id in ["C001", "C002", "C999"]:
            try:
                response = client.get(f"/customers/{customer_id}/receivable")
                response.raise_for_status()  # 先检查 HTTP 状态，再读取业务数据。
                print(customer_id, response.json())
            # 已收到错误响应，与尚未完成请求的网络故障分别处理。
            except httpx.HTTPStatusError as error:
                print(customer_id, "HTTP 错误", error.response.status_code)
            except httpx.RequestError:
                print(customer_id, "网络请求失败")


if __name__ == "__main__":
    main()
