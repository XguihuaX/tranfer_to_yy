# 08-01 从样例表到 SQLite：查出客户未收余额

> 教材已准备。用户已读、已练习和已验证的状态单独记录于本模块进度。更新日期：2026-10-16。

## 本章问题、目标与前置

**已经会写 SQL，怎样把眼前的业务表存到本机，并让 Python 查询同一份数据？**

本章只完成一条链：看懂样例数据 → 建立 SQLite 数据库文件 → 导入并核对记录 → 查询未收余额 → 用 Python 返回相同结果。完成后，你应能定位数据库文件，核对两笔应收的余额，并指出 Python 在哪里传入客户、在哪里取得查询结果。

前置是你已有的 SQL 筛选、关联和汇总知识，以及能阅读简单 Python 代码。表头与明细的业务背景见 [00-03 §2](../00-products/03-documents-and-status.md#header-and-lines)；这里直接使用，不重讲主键或函数定义。正文与运行约 30–45 分钟，可以先读 §1–4，下次再读 Python 部分；不运行也能先按表推算。

事务的详细控制、回滚练习和索引分析留到后续。本章使用本机已有的 Python 和 SQLite，直接完成查询。

## 1. 先看要放进数据库的四张表 {#sample-tables}

销售问：“上海公司对 C001 客户，现在还有多少钱没收回来？把对应应收单也列出来。”

下面就是本章全部业务数据。沿用 SO101 的商品与金额，再新增 SO105，专门观察“尚无收款”的情况。

### 1.1 `order_header`：订单表头，确定订单属于哪个客户和公司

| doc_id（订单号） | org_id（公司） | customer_id（客户） | business_date（业务日期） | total_amount（整单金额/元） |
| --- | --- | --- | --- | ---: |
| SO101 | ORG-SH | C001 | 2026-10-15 | 10000 |
| SO105 | ORG-SH | C001 | 2026-10-16 | 2000 |

### 1.2 `order_line`：订单明细，用来核对商品与整单金额

| doc_id（所属订单） | line_no（行号） | material_id（商品） | quantity（数量/台） | unit_price（单价/元） | line_amount（行金额/元） |
| --- | ---: | --- | ---: | ---: | ---: |
| SO101 | 1 | M001 | 8 | 1000 | 8000 |
| SO101 | 2 | M002 | 1 | 2000 | 2000 |
| SO105 | 1 | M002 | 1 | 2000 | 2000 |

### 1.3 `receivable`：应收记录，表示已经确认要向客户收取的金额

| ar_id（应收单号） | order_id（来源订单） | business_date（应收业务日期） | amount（应收金额/元） |
| --- | --- | --- | ---: |
| AR101 | SO101 | 2026-10-15 | 10000 |
| AR102 | SO105 | 2026-10-16 | 2000 |

### 1.4 `receipt`：收款记录，标明本次收款对应哪笔应收

| receipt_id（收款单号） | ar_id（对应应收单） | business_date（收款业务日期） | amount（收款金额/元） | status（处理状态） |
| --- | --- | --- | ---: | --- |
| RC101 | AR101 | 2026-10-15 | 3000 | POSTED（已入账） |
| RC102 | AR101 | 2026-10-16 | 1000 | POSTED（已入账） |
| RC103 | AR101 | 2026-10-16 | 500 | DRAFT（草稿） |

这里“已入账”约定为：收款已经确认，并已对应到这笔应收，可以冲减未收余额。RC103 只是草稿，暂不能冲减。AR102 没有收款记录，所以应保留全部 2000 元未收余额。

!!! note "本次查询的统一约定"
    这是截至 2026-10-16 12:00 的固定教学快照，表中记录均已存在；两张订单和两笔应收均已确认且有效。所有金额为人民币整数元，不涉及小数、税费拆分、退款、折让和其他调整。每条收款只对应一笔应收；客户与公司沿来源订单取得，本章单号全局唯一。查询当前余额，不按月份截取，也不判断逾期。

    四张表是合成练习结构，未假定任何用友产品的内部数据库。现实中一笔收款可能分配给多笔应收，那时还需要表达分配关系；本章先固定一笔收款对应一笔应收，保证可以逐行核对。

先手算得到本章的验收结果：

| ar_id（应收单号） | 应收金额（元） | 已确认收款（元） | 未收余额（元） |
| --- | ---: | ---: | ---: |
| AR101 | 10000 | 3000 + 1000 = 4000 | 6000 |
| AR102 | 2000 | 0 | 2000 |
| 合计 | 12000 | 4000 | **8000** |

订单明细帮助核对商品金额；实际余额计算取应收金额减去已确认收款。即使本例订单额恰好等于应收额，查询仍应沿着应收与收款记录计算。

## 2. 数据库文件、命令行和 Python 怎样连接 {#database-file}

现在四张表还只是教材中的文字。SQLite 负责把表结构和数据存进文件，并执行查询。本章将文件命名为 `erp_ch01.db`，放在项目的 `learning/08-database/ch01/` 目录内。

你会通过两个入口访问它：

```text
终端中的 sqlite3 程序 ──打开──┐
                            ├── erp_ch01.db（包含四张表）
Python 的 sqlite3 模块 ──打开──┘
```

这里的“连接”是程序打开数据库、执行操作并读取结果时使用的对象。SQLite 在调用它的程序内部工作，因此本次无需启动独立数据库服务，也无需填写服务器地址、端口和数据库账号。文件路径决定访问哪一份数据。[SQLite 官方用途说明](https://www.sqlite.org/whentouse.html)

`setup.sql` 是可阅读的建表和插入指令；`erp_ch01.db` 是执行后产生的数据库文件，不能当作普通文本编辑。`sqlite3` 命令与 Python 中的 `sqlite3` 模块是两个操作入口。两者只要打开相同路径，就能查询同一份已保存的数据。

之前 ERP 章中的 `:memory:` 只保留当前连接的临时数据；本章改用磁盘文件，退出程序再打开仍能查询。首次创建和后续查询也要区分：普通打开方式在路径不存在时可能创建新库，所以“没有报连接错误”不一定说明打开了正确的库。后面的查询使用只读方式打开，路径不存在会直接报错。

### 2.1 本机环境已具备，不需要安装

2026-10-16 实测：Python **3.14.4**；Python 使用的 SQLite **3.53.0**；系统 `sqlite3` 命令使用 SQLite **3.51.0**。两者版本不同是因为各自使用的 SQLite 库不同，本章语句均已在两者中核对。只使用 Python 标准库，无需 `pip install`。

本章文件已备好，你可以直接查看和运行。下面命令在 macOS 终端执行，先定位到练习目录：

```sh
cd /Users/liujunhong/Documents/ChatGPT/用友/learning/08-database/ch01
pwd
ls
```

你会看到 `setup.sql`、`balance.sql`、`peek.py` 和 `query_balance.py` 等文件。教材验证还已生成 `erp_ch01.db`，所以**现在可以直接进入 §3.2**；想亲自体验从空文件建库时，按 §3.1 使用另一个文件名。

## 3. 建表、导入，再确认保存了什么 {#create-and-inspect}

### 3.1 用 SQL 文件建立一份数据库

本章不要求手敲整段初始化代码。展开下面完整脚本可看到：它先创建四张已展示的表，再插入同样的记录。`TEXT` 存放单号、状态与日期文本，`INTEGER` 存放本章整数数量和金额；日期统一写成 `YYYY-MM-DD`。

??? note "完整 setup.sql：与上面的四张样例表对应"
    ```sql
    PRAGMA foreign_keys = ON;
    BEGIN;

    CREATE TABLE order_header (
        doc_id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        business_date TEXT NOT NULL,
        total_amount INTEGER NOT NULL
    );
    CREATE TABLE order_line (
        doc_id TEXT NOT NULL REFERENCES order_header(doc_id),
        line_no INTEGER NOT NULL,
        material_id TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price INTEGER NOT NULL,
        line_amount INTEGER NOT NULL,
        PRIMARY KEY (doc_id, line_no)
    );
    CREATE TABLE receivable (
        ar_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL REFERENCES order_header(doc_id),
        business_date TEXT NOT NULL,
        amount INTEGER NOT NULL
    );
    CREATE TABLE receipt (
        receipt_id TEXT PRIMARY KEY,
        ar_id TEXT NOT NULL REFERENCES receivable(ar_id),
        business_date TEXT NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('POSTED', 'DRAFT'))
    );

    INSERT INTO order_header VALUES
        ('SO101', 'ORG-SH', 'C001', '2026-10-15', 10000),
        ('SO105', 'ORG-SH', 'C001', '2026-10-16', 2000);
    INSERT INTO order_line VALUES
        ('SO101', 1, 'M001', 8, 1000, 8000),
        ('SO101', 2, 'M002', 1, 2000, 2000),
        ('SO105', 1, 'M002', 1, 2000, 2000);
    INSERT INTO receivable VALUES
        ('AR101', 'SO101', '2026-10-15', 10000),
        ('AR102', 'SO105', '2026-10-16', 2000);
    INSERT INTO receipt VALUES
        ('RC101', 'AR101', '2026-10-15', 3000, 'POSTED'),
        ('RC102', 'AR101', '2026-10-16', 1000, 'POSTED'),
        ('RC103', 'AR101', '2026-10-16', 500, 'DRAFT');

    COMMIT;
    ```

只补充几处直接影响运行的约束：`NOT NULL` 表示该字段必须有值；`REFERENCES` 要求来源单号在被关联表中存在；`CHECK` 限定本例收款状态的取值。`PRAGMA foreign_keys = ON` 为当前 SQLite 连接启用外键检查，否则仅写 `REFERENCES` 不足以保证当前连接执行检查。[SQLite 外键文档](https://sqlite.org/foreignkeys.html#fk_enable)

`BEGIN` 与 `COMMIT` 把这批建表和插入放在一个事务里。事务可以先理解为“一组一起确认的修改”：执行到 `COMMIT` 才提交整组操作。本章初始化命令遇错即退出，未提交的事务随连接关闭回滚，避免留下半批已提交数据。后续会专门用 Python 学习提交与回滚。

想自己创建时，在 §2.1 的目录下执行下面命令，使用尚不存在的文件名：

```sh
sqlite3 -bail erp_try.db < setup.sql
```

终端的 `<` 把 `setup.sql` 内容交给 `sqlite3` 执行；`-bail` 表示出错立即停止。成功时通常没有输出，接下来通过查询确认。初次建教材库所用的命令也是同样形式，只是文件名为 `erp_ch01.db`。

不要在已经导入的同一文件上重复执行初始化：`CREATE TABLE` 会报告表已存在。查询可以反复执行，初始化只对新库执行一次。需要重做时换一个新文件名即可。

### 3.2 打开库，检查表与文件路径

使用已经准备的教材库：

```sh
sqlite3 -readonly erp_ch01.db
```

进入 `sqlite>` 提示符后，逐行执行下面内容。若检查你刚创建的练习库，将打开命令中的文件名改成 `erp_try.db` 即可。

```text
.databases
.tables
.schema receivable
.headers on
.mode column
```

`.databases` 显示当前打开的完整路径，先确认末尾是你想要的文件。`.tables` 应包含 `order_header`、`order_line`、`receivable`、`receipt`；显示顺序不重要。`.schema receivable` 显示应收表的建表语句，便于核对字段。

这些以点开头的命令由命令行工具处理，各占一行，不加分号。接下来才是交给数据库执行的 SQL：

```sql
SELECT 'order_header' AS table_name, COUNT(*) AS row_count FROM order_header
UNION ALL
SELECT 'order_line', COUNT(*) FROM order_line
UNION ALL
SELECT 'receivable', COUNT(*) FROM receivable
UNION ALL
SELECT 'receipt', COUNT(*) FROM receipt;
```

预期结果：

| table_name（表名） | row_count（记录数） |
| --- | ---: |
| order_header | 2 |
| order_line | 3 |
| receivable | 2 |
| receipt | 3 |

此处用 `UNION ALL` 把四个计数放在一个结果里，便于一次核对。收款表的三行包括草稿；“记录已经导入”和“金额应该计入余额”是两个判断，后者还需要状态条件。

输入 `.quit` 退出。重新执行 `sqlite3 -readonly erp_ch01.db`，还能看到这些表，说明数据已保存在文件中。命令行使用方式见 [SQLite CLI 文档](https://www.sqlite.org/cli.html)。

## 4. 写出能和手算结果对上的查询 {#balance-query}

### 4.1 先把收款汇总到每笔应收

在刚才打开的 SQLite 命令行中执行：

```sql
SELECT ar_id, SUM(amount) AS paid_amount
FROM receipt
WHERE status = 'POSTED'
GROUP BY ar_id;
```

| ar_id（应收单号） | paid_amount（已确认收款/元） |
| --- | ---: |
| AR101 | 4000 |

这一步先排除 RC103，再合并 RC101 和 RC102。同一笔应收可能有多条收款；先汇总，下一步关联时就只有一行收款合计。AR102 尚无收款，不会出现在这个中间结果中。

### 4.2 关联应收，并保留没有收款的记录

完整查询如下，也已保存为 `balance.sql`：

```sql
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
WHERE h.org_id = 'ORG-SH' AND h.customer_id = 'C001'
ORDER BY a.ar_id;
```

`WITH paid AS (...)` 给刚才的汇总结果取名 `paid`，让后半段查询可以引用它。它只在这一条 SQL 中生效，不会在数据库里新建一张永久表。[SQLite WITH 文档](https://sqlite.org/lang_with.html)

这段查询的处理路线是：先得到每笔应收的已收金额；再从应收出发，沿来源订单筛选公司和客户；最后接上收款合计并计算余额。`LEFT JOIN` 保留没有匹配收款的 AR102；它的 `paid_amount` 此时是空值，`COALESCE(..., 0)` 将其作为 0 参与减法。否则 `2000 - NULL` 得到空值，无法给出正确余额。

| ar_id（应收单号） | order_id（来源订单） | receivable_amount（应收/元） | paid_amount（已收/元） | balance（未收/元） |
| --- | --- | ---: | ---: | ---: |
| AR101 | SO101 | 10000 | 4000 | 6000 |
| AR102 | SO105 | 2000 | 0 | 2000 |

本次不需要商品维度，所以没有关联 `order_line`。把两条已入账收款直接关联到 AR101，会让同一笔 10000 元应收展开成两行；如果再把应收金额求和就会重复。本章的 `paid` 先汇总到应收粒度，避免这种展开。

若已退出 SQLite，也可在终端一次性执行保存好的查询：

```sh
sqlite3 -readonly -header -column erp_ch01.db < balance.sql
```

预期就是上面的两行。这里应核对单号与逐笔金额，之后再核对合计 8000；只有一个总数相同，还不足以说明各笔来源正确。

## 5. 让 Python 取得同样的结果 {#python-query}

### 5.1 最小例子：打开文件，读取两行应收

SQL 已经能查对，Python 接下来负责打开同一个文件、提交查询并接收数据。先看完整的 `peek.py`：

```python
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
```

在终端运行：

```sh
python3 peek.py
```

预期输出：

```text
[('AR101', 10000), ('AR102', 2000)]
```

`db_path` 根据当前脚本的位置找到同目录的数据库，而不依赖终端从哪里启动。`as_uri()` 把路径转换成 SQLite 能识别的文件地址，`mode=ro` 要求只读打开；因此写错路径不会悄悄得到一个新空库。

`con.execute(...)` 执行查询并返回游标，可以把游标理解为这次查询的结果读取入口；`fetchall()` 将全部结果取到 Python 列表，每行默认是一个元组。本例仅两行，适合一次取完。`finally` 保证无论查询成功还是报错，最后都关闭连接。具体接口见 [Python sqlite3 文档](https://docs.python.org/3.14/library/sqlite3.html)。

### 5.2 加入实际要求：客户从变量传入，结果保留字段名

最小例子只能读固定字段。现在要回答销售的问题，需要两处变化：将 §4 查询接入 Python，并让公司与客户从变量传入；将结果按字段名组织，后续程序才能清楚地取得余额和来源单号。

关键修改是把 SQL 中固定的两个字符串改为 `?`：

```python
rows = con.execute(sql, (org_id, customer_id)).fetchall()
```

其中 `sql` 的条件写作 `WHERE h.org_id = ? AND h.customer_id = ?`。两个问号分别对应后面元组中的两个值，由数据库接口绑定；不要把值拼进 SQL 文本，也不要给问号加引号。这样客户编号里的引号仍作为数据处理，不会改变语句结构。[Python 参数绑定说明](https://docs.python.org/3.14/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries)

再设置 `con.row_factory = sqlite3.Row`，使每一行可以通过字段名取值，随后用 `dict(row)` 转为普通字典。完整 `query_balance.py` 如下：

```python
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
```

运行方式：

```sh
python3 query_balance.py
```

预期输出：

```json
{
  "org_id": "ORG-SH",
  "customer_id": "C001",
  "currency": "CNY",
  "amount_unit": "元",
  "items": [
    {
      "ar_id": "AR101",
      "order_id": "SO101",
      "receivable_amount": 10000,
      "paid_amount": 4000,
      "balance": 6000
    },
    {
      "ar_id": "AR102",
      "order_id": "SO105",
      "receivable_amount": 2000,
      "paid_amount": 0,
      "balance": 2000
    }
  ],
  "total_receivable": 12000,
  "total_paid": 4000,
  "total_balance": 8000
}
```

数据库完成关联、筛选和逐笔余额计算，Python 把每行转换成字典，再累加三项金额。`json.dumps` 将结果转换为 JSON 文本，便于观察，也为后续接口返回结果做准备；本章尚未启动 HTTP 服务。保留 `items` 中的应收单号，能让 8000 元这个总数追溯到 AR101 的 6000 和 AR102 的 2000。

将来接到接口时，公司和客户可以由参数传入，但访问范围仍需由后端按实际权限确定。这里使用的是预先约定可查的合成数据，两个查询条件本身不构成账号权限系统。

### 5.3 如果查不到记录，结果说明什么

本例只存了 C001 的订单。把 `customer_id` 改成 `C999`，输出将是 `items: []`，三项合计都是 0。这是空结果的计算表现，能说明“在本次数据和筛选范围内，没有匹配的应收记录”。

如果还要回答“客户是否存在”，需要另查客户资料；本章没有客户主数据表，不能仅从空应收列表判断客户不存在。保留明细列表，也能把“存在一笔已结清应收，余额为 0”和“没有匹配应收”区分开。

## 6. 遇到错误时先定位哪一层 {#troubleshooting}

本章先检查路径，再检查表与记录，最后检查查询结果。这样可以逐步缩小问题范围。

| 看到的现象 | 本章中的常见原因 | 下一步检查 |
| --- | --- | --- |
| `unable to open database file` | 只读打开的路径不存在，或目录不可访问 | 终端用 `pwd`、`ls` 核对；Python 临时打印 `db_path`，确认是否打开了教材库 |
| `no such table: receivable` | 打开了别的库，或库尚未初始化 | 在命令行运行 `.databases` 和 `.tables`；确认路径后检查导入是否成功 |
| `table order_header already exists` | 对已经初始化的文件再次执行 `setup.sql` | 已有库直接查询；重新体验建库时换一个新文件名 |
| `FOREIGN KEY constraint failed` | 写入的来源单号不存在 | 检查订单、应收、收款的插入顺序与关联编号 |
| `Incorrect number of bindings supplied` | SQL 中问号数量与参数数量不一致 | 本例两个问号要对应 `(org_id, customer_id)` 两个值 |
| 只返回 AR101 | 将保留应收的 `LEFT JOIN` 改成了内关联等 | 对照 §4.2，检查 AR102 是否因没有收款被排除 |
| 合计未收为 7500 | 把 RC103 草稿的 500 元也扣除了 | 检查收款汇总中的 `status = 'POSTED'` |
| SQLite 一直显示 `...>` | 语句还没结束，常见是少分号或引号未闭合 | 补齐当前语句；不确定时按 Ctrl+C 取消当前输入后重输 |

另外，`.tables` 属于命令行工具，不是 SQL。把它传给 Python 的 `execute()` 会报语法错误。终端启动命令、SQLite 点命令和 SQL 分别在对应环境执行，避免把三种输入混到一起。

## 7. 少量练习：检查操作与结果理解 {#practice}

可以先读答案、手动推演，或实际修改后运行；练习不作为继续阅读的门槛。若修改了示例，记得在反馈时说明修改内容，以便解释结果。

### 练习 1：为什么“查不到表”，却没有连接失败

有人把连接改成 `sqlite3.connect("erp_ch01.db")`，随后从另一个目录启动脚本，收到 `no such table: receivable`。最可能发生了什么？怎样确认？

??? note "参考答案 1：相对路径可能指向另一份文件"
    普通连接使用的相对路径以当前工作目录为起点。若那里没有这个文件，SQLite 可能创建一个新的空库，于是连接成功，但查询找不到表。先打印实际路径或在命令行运行 `.databases` 核对，再看 `.tables`。本章按脚本位置定位文件，并只读打开，让路径错误更早暴露。

### 练习 2：把草稿也算进去，哪个结果会变

如果删掉收款汇总中的状态筛选，AR101、AR102 和总余额分别是多少？SQL 能成功执行是否足以判断结果正确？

??? note "参考答案 2：运行成功与符合指标要分别核对"
    AR101 已收被算为 4500 元，余额为 5500 元；AR102 仍为 2000 元，总余额 7500 元。语法合法、程序可运行，但把尚未确认的草稿算成已收，不符合本章口径。正确结果仍为 6000、2000、合计 8000 元。

### 练习 3：只显示未收余额超过 3000 元的应收

在 `query_balance.py` 中，已得到 `items` 之后，怎样生成筛选后的明细？哪些单据应该保留？如果对筛选后的明细计算合计，它表达什么？

??? note "参考答案 3：先明确合计的范围"
    可以写 `selected = [item for item in items if item["balance"] > 3000]`，保留 AR101，其余额为 6000 元；AR102 被排除。这是一个合理的 Python 实现，也可以改 SQL 完成筛选。

    若对 selected 汇总，所得 6000 元表示“余额超过 3000 元的应收单的未收合计”。客户全部应收的未收合计仍为 8000 元。展示时应写明合计对应的筛选范围，避免用筛选后的小计回答客户总余额。

## 本章回顾与检查清单 {#checklist}

这次完成的是从文件到业务结果的闭环：初始化脚本把四张表存入 SQLite 文件；SQL 先汇总有效收款，再计算两笔应收余额；Python 打开同一文件，用参数绑定传入公司与客户，将带来源单号的结果组织成 JSON。

- [ ] 能找到实际打开的数据库文件，并区分它和 `setup.sql`。
- [ ] 能核对四张表的行数 2、3、2、3，以及两笔余额 6000、2000。
- [ ] 能指出 Python 的连接、传参、取结果和关闭连接分别在哪里。
- [ ] 能解释草稿为何不计入、无收款应收为何仍须保留。

到这里本章小目标完成。教材代码跑通的记录由编写者维护；你的阅读和实操按实际反馈另记，不因为示例验证通过而认定你已经掌握。

## 阅读中产生的答疑 {#reading-questions}

暂无本章新问题。即时提问会先在对话中直接解答；按你的偏好，不因每个问题自动修改教材。你可以用“08-01 §3.2”或自然语言定位，答疑结束再回到原阅读位置。

## 资料、验证与后续 {#sources}

官方资料核对日期：2026-10-16。

- [SQLite：适用场景](https://www.sqlite.org/whentouse.html)，支持 §2 的运行方式说明。
- [SQLite：命令行](https://www.sqlite.org/cli.html)，支持 §3 的文件打开、点命令和脚本输入。
- [SQLite：外键检查](https://sqlite.org/foreignkeys.html#fk_enable)，支持初始化连接显式启用检查。
- [SQLite：WITH](https://sqlite.org/lang_with.html)，支持 §4 的单条语句中间结果命名。
- [Python 3.14：sqlite3](https://docs.python.org/3.14/library/sqlite3.html)，支持连接、结果读取、参数绑定和行对象用法。

本章样例数据和查询由本模块设计。验证范围包括建库导入、重新打开查询、四表行数、逐笔金额、Python JSON、空结果和草稿误计情况；详细证据保存在本模块 `learning/08-database/VERIFICATION.md`。这些是教材检查，不是用户练习记录。

后续准备围绕同一份数据学习写入、事务和回滚；还未开始下一章。MySQL 阶段以后再展开服务、连接和部署。

[返回数据库模块目录](index.md) · [业务参考：单据、明细和状态](../00-products/03-documents-and-status.md)
