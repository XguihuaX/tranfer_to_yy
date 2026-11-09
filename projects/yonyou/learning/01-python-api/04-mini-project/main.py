import os
from pathlib import Path

from service import CustomerNotFoundError, query_receivable


def main():
    # 从程序外读取客户编号；未设置时使用 C001。
    customer_id = os.getenv("CUSTOMER_ID", "C001")
    try:
        print(query_receivable(customer_id))  # 入口调用业务并展示结果。
    except CustomerNotFoundError as error:
        print("查询失败：", error)

    # __file__ 是当前代码文件；日志固定写到它旁边。
    log_path = Path(__file__).with_name("query.log")
    with log_path.open("a", encoding="utf-8") as stream:  # 追加写入，退出时关闭文件。
        stream.write(f"本次查询结束：{customer_id}\n")


# 仅直接运行时启动；被 import main 时不调用 main()。
if __name__ == "__main__":
    main()
