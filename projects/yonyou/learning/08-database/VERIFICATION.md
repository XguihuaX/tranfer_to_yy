# 08-01 教材验证记录

日期：2026-10-16（Asia/Shanghai）。以下为编写者检查，不计为用户已读、练习或掌握。

## 环境

- Python：/opt/homebrew/bin/python3，3.14.4；sqlite3 模块底层 SQLite 3.53.0。
- CLI：/usr/bin/sqlite3，SQLite 3.51.0。
- 无新增依赖，复用已有 .venv-docs 和 127.0.0.1:8765 预览服务。

## 代码与数据检查

- 按正文命令，用 sqlite3 -bail 和 setup.sql 生成 ch01/erp_ch01.db；退出后重新打开查询成功。
- 在模块内临时目录另建空库验证初始化，临时目录在检查完成后清理；教材库保留供阅读与运行。
- order_header/order_line/receivable/receipt 的记录数分别为 2/3/2/3；PRAGMA integrity_check 返回 ok，foreign_key_check 返回空列表。
- balance.sql 结果精确等于 (AR101, SO101, 10000, 4000, 6000) 和 (AR102, SO105, 2000, 0, 2000)。CLI 和 Python 均核对通过。
- peek.py 输出 [('AR101', 10000), ('AR102', 2000)]。
- query_balance.py 的完整 JSON 与正文 JSON 逐项相等；应收合计 12000，已收合计 4000，未收合计 8000。
- 去掉 POSTED 筛选时得到 5500/2000，总余额 7500；改 LEFT JOIN 为 JOIN 时仅余 AR101，符合正文排错说明。
- 以 C999 及含引号的 `C001' OR 1=1 --` 作为绑定值，均返回空明细与 0 合计；未改变 SQL 筛选结构。
- 筛选余额大于 3000 的明细后，小计 6000，符合练习 3。
- 从 /tmp 运行完整查询脚本，与项目内运行得到相同结果；脚本按自身位置定位数据库。
- 临时库重复初始化按预期失败并提示表已存在；已提交的 receipt 仍为三行。
- 从 Markdown 提取代码块，确认四个完整源文件均与教材展示一致；其余展示的 SQL 均执行成功。

## 构建与网页

- `.venv-docs/bin/mkdocs build --strict` 退出码 0。Material 包输出其未来版本公告；本次构建成功，没有新增文档构建错误。
- 首页、08 模块入口和 08-01 章节 HTTP 200。
- 章节 10 个稳定锚点齐全，4 个折叠区（初始化脚本与 3 个参考答案）已在生成 HTML 中核对。
- 根侧栏没有 08：根 docs/.pages 是显式 00–07 列表。本模块 index 和章节直链有效；待总对话增加导航条目，详见 PROGRESS.md。
- 没有修改其他模块、根配置、总纲或 Skyler；没有执行 MySQL 安装或外部账号操作。
