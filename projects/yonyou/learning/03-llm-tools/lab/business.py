"""合成业务数据：有效应收减已核销收款；同一组织、同一币种。"""
AS_OF = "2026-11-08"
CUSTOMERS = {
    "C001": {"name": "海星商贸（北京）", "receivable": 20000, "settled": 7200},
    "C002": {"name": "海星商贸（上海）", "receivable": 8000, "settled": 8000},
    "C003": {"name": "星河制造", "receivable": 500, "settled": 0},
}


def get_balance(customer_id: str) -> dict:
    row = CUSTOMERS.get(customer_id)
    if row is None:
        return {"status": "not_found", "customer_id": customer_id}
    return {
        "status": "ok", "customer_id": customer_id, "customer_name": row["name"],
        "amount": row["receivable"] - row["settled"], "currency": "CNY",
        "as_of": AS_OF, "source": "synthetic_receivables_v1",
    }


def search_customers(query: str) -> dict:
    query = query.strip()
    if not query:
        return {"status": "invalid_query", "matches": []}
    matches = [
        {"customer_id": cid, "name": row["name"]}
        for cid, row in CUSTOMERS.items() if query in row["name"]
    ]
    return {"status": "ok" if matches else "not_found", "matches": matches}


if __name__ == "__main__":
    print(get_balance("C001"))
    print(get_balance("C002"))
    print(get_balance("C999"))
