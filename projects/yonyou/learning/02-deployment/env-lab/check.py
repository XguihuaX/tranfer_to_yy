import os
from pathlib import Path

currency = os.environ.get("QUERY_CURRENCY")
if currency != "CNY":
    raise SystemExit("配置错误：请设置 QUERY_CURRENCY=CNY")
data = Path(__file__).resolve().parent / "balance.txt"
print(f"读取结果：{data.read_text(encoding='utf-8').strip()} {currency}")
