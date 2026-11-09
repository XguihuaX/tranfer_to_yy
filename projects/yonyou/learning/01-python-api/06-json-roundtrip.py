import json

result = {"customer_id": "C001", "amount": 12800, "note": "合成应收", "matched": True}

# Python 字典 → JSON 字符串；保留可直接阅读的中文。
text = json.dumps(result, ensure_ascii=False)
# 字符串 → UTF-8 字节，模拟传输前的编码。
payload = text.encode("utf-8")
# JSON 字节 → Python 数据；直接解析上一步的 payload，没有进行网络传输。
restored = json.loads(payload)

print(type(result).__name__, type(text).__name__, type(payload).__name__)
print(text)
print(restored == result)  # 检查往返后的数据是否一致。
print(json.loads("null") is None)  # JSON null 对应 Python None。


# 故意使用单引号字段名，观察非法 JSON 的失败路径。
try:
    json.loads("{'amount': 12800}")
except json.JSONDecodeError:
    print("JSON 格式不合法：字段名要使用双引号")
