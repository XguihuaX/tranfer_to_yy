from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().with_name("erp_ch01.db")
con = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
try:
    rows = con.execute(
        "SELECT ar_id, amount FROM receivable ORDER BY ar_id"
    ).fetchall()
    print(rows)
finally:
    con.close()
