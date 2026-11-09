from pathlib import Path
import json
import sqlite3

db_path = Path(__file__).resolve().with_name("erp_ch01.db")
org_id = "ORG-SH"
customer_id = "C001"

sql = """
WITH paid AS (
    SELECT ar_id, SUM(amount) AS paid_amount
    FROM receipt
    WHERE status = 'POSTED'
    GROUP BY ar_id
)
SELECT a.ar_id,
       a.order_id,
       a.amount AS receivable_amount,
       COALESCE(p.paid_amount, 0) AS paid_amount,
       a.amount - COALESCE(p.paid_amount, 0) AS balance
FROM receivable AS a
JOIN order_header AS h ON h.doc_id = a.order_id
LEFT JOIN paid AS p ON p.ar_id = a.ar_id
WHERE h.org_id = ? AND h.customer_id = ?
ORDER BY a.ar_id;
"""

con = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
try:
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, (org_id, customer_id)).fetchall()
    items = [dict(row) for row in rows]
finally:
    con.close()

result = {
    "org_id": org_id,
    "customer_id": customer_id,
    "currency": "CNY",
    "amount_unit": "元",
    "items": items,
    "total_receivable": sum(item["receivable_amount"] for item in items),
    "total_paid": sum(item["paid_amount"] for item in items),
    "total_balance": sum(item["balance"] for item in items),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
