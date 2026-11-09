# 08-01 实操文件

先读网页：http://127.0.0.1:8765/08-database/01-sqlite-first-query.html

在本目录运行。已生成的 erp_ch01.db 可直接查询：

```sh
sqlite3 -readonly -header -column erp_ch01.db < balance.sql
python3 peek.py
python3 query_balance.py
```

预期：AR101 未收 6000 元，AR102 未收 2000 元，总未收 8000 元。

亲自体验导入时，选择尚不存在的新文件名：

```sh
sqlite3 -bail erp_try.db < setup.sql
sqlite3 -readonly -header -column erp_try.db < balance.sql
```

Python 示例默认仍读取脚本同目录的 erp_ch01.db；如要查询 erp_try.db，修改脚本中 with_name 的文件名。不要对已有库重复初始化；没有自动删除或重置逻辑。

- setup.sql：四表结构与全量合成数据。
- balance.sql：固定 ORG-SH/C001 的 SQL 查询。
- peek.py：最小 Python 读取例子。
- query_balance.py：参数绑定、逐笔来源和 JSON 合计。
- erp_ch01.db：教材验证生成的 SQLite 文件。

完整验证范围见上一层 VERIFICATION.md；教材已运行不代表用户已完成练习。
