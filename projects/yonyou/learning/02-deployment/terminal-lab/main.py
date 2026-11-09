from pathlib import Path

# 相对数据路径从当前工作目录出发，便于观察启动位置的影响。
print(f"当前工作目录：{Path.cwd()}", flush=True)
text = Path("data/balance.txt").read_text(encoding="utf-8")
customer_id, amount = text.strip().split(",")
print(f"客户 {customer_id} 的未收余额：{amount} 元")
