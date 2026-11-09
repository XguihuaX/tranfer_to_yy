# 02 教材作者验证记录

批量备课与作者核对完成：2026-11-01（Asia/Shanghai）。总对话独立二次复核于同日通过。本记录说明教材检查，不代表用户阅读或掌握。

## 交付范围

- docs/02-deployment/01–09 九章完整正文，index.md 与显式 .pages 导航。
- 保留 terminal-lab 原例；新增 log-lab 固定日志、env-lab 配置/权限例、service-lab 标准库服务及 Docker/Compose 文件。
- 每章含问题/前置、递进正文、命令环境说明、示例/预期结果、排错、可选练习和折叠答案、回顾、来源与后续入口。
- 01 只增加已完成下一章的链接，不改变原始示例和练习题意。

## 复现命令与证据

在项目根目录运行：

```sh
.venv-docs/bin/python learning/02-deployment/verify_examples.py
.venv-docs/bin/mkdocs build --strict
```

第一条只在本模块内创建 author-check 临时目录，提取 02-02 至 02-05 正文的 sh 块按顺序重放，并在独立服务副本验证 02-06/08。Git 设置仅在临时练习仓库，本次检查环境忽略全局 Git 配置；不操作主仓库分支或提交。服务使用操作系统分配的空闲本机端口，不占用教材约定的 8028，验证请求随之使用该端口；结束时仅终止脚本创建的 PID 并清理自己的副本。

完整检查输出保存于 `VERIFICATION-results.json`，含 Shell 输出、预期错误、服务日志以及未执行项目。共 11 类检查全部通过。

| 类别 | 实际检查与结果 |
| --- | --- |
| 02-01 | 既有核对：Python 3.14.4/3.9.6 正确目录输出12800，data目录运行触发FileNotFoundError；正文与main.py一致。此次未改代码 |
| 文件与日志 | 全部sh块重放；C001三行、WARN/ERROR按原序两行；stdout空、stderr有错误；grep无匹配/读失败的退出码符合教材 |
| Git暂存提交 | 3次提交、工作区干净；MM状态体现暂存后再次编辑；忽略文件未纳入提交 |
| Git协作 | bare + Alice/Bob副本；快进、fetch后合并、分叉时pull拒绝、同一行冲突、balanced解决、push、Alice快进；restore两层、普通提交revert、stash -u/pop均通过 |
| 环境与权限 | 未export/单次赋值/.env未自动加载分别复现配置错误；export和指定环境成功；u-r触发PermissionError，u+r恢复；实际Python3.12.14 venv、pip check、activate/deactivate通过 |
| 完整文件一致性 | 08内完整server.py与运行文件一致；09内Dockerfile、compose.yaml、.dockerignore与配套文件一致 |
| 交付副本 | 新仓库初始提交、增加C003=500提交、JSON语法检查、独立venv与pip check成功 |
| HTTP正常分支 | health200；C001=12800、C002=0、C003=500；C999404、未知路由404 |
| 启动故障 | lsof PID与子进程一致；第二实例端口占用失败；缺币种启动失败；非法端口启动失败 |
| 数据故障与停止 | 临时改名数据后health仍200、查询500；日志含data_read_failed与FileNotFoundError；恢复后查询200且Git干净；TERM后curl退出7 |
| Compose静态配置 | 默认宿主8029/容器8028；HOST_PORT=8039只改宿主端口；HOST=0.0.0.0、币种CNY、只读bind mount解析符合正文 |

## 发现并修正的具体问题

1. 总对话反馈 Git 最低版本：`git init -b` 需要2.28+；02-03已修正整套命令的最低版本说明，本机为2.39.2。
2. 总对话独立复核发现本机默认Homebrew Python3.14.4创建venv的ensurepip失败，`pyexpat`加载系统`libexpat`时缺`_XML_SetAllocTrackerActivationThreshold`符号。作者按反馈改用现有项目`.venv-docs/bin/python`（3.12.14）在练习副本创建独立venv并通过实测。正文先单独创建、成功后再使用；未修系统Python或全局库。
3. 本机Compose实际为v5.0.2，使用`docker compose`插件命令；正文不把“必须v2”当作版本限制。

## 平台与未执行范围

- Mac本机zsh5.9、Git2.39.2、OpenSSH10.0p2；共享文档环境Python3.12.14；Docker客户端29.2.1、Compose5.0.2。
- 本轮`docker info`退出1：当前socket不存在、引擎无法连接。没有启动Docker、切换上下文或安装服务。
- SSH登录、scp、端口转发、远程venv、Linux ss/systemd/journalctl、tmux、远程nohup生命周期均未实测。正文明确示意主机与先决条件。
- Docker build/up/ps/logs/exec/down未执行；仅成功解析Compose配置，不称为容器部署成功。
- less交互翻页、tail跟随按键以及系统top界面未作GUI交互验证；说明依据本机手册。文件筛选、重定向、进程/端口/请求的关键路径已实际运行。
- 官方依据包括Git restore/pull、OpenSSH ssh/scp、Python venv/http.server、systemd.service、Docker端口与Compose插值/服务配置；GNU重定向网页请求超时，Shell语义用本机zshmisc、grep/chmod手册与实际重放核对，未记为成功读到GNU网页。

## 发布检查

- 全站 `.venv-docs/bin/mkdocs build --strict` 成功，退出码0。
- 本模块10个页面（目录+9章）均HTTP200；956个模块链接及锚点检查通过；每章至少1个折叠答案（02-01有3个），显式导航覆盖九章。

## 用户状态

教材批量准备完成。用户当前仍无本模块已阅读或练习反馈；建议阅读起点02-01 §1。练习可选，可自行推进，不要求补交01题目。

## 总对话独立二次复核（2026-11-01，通过）

本节依据总对话发回的复核结果同步，不是本模块再次执行的测试。正式报告：[reviews/02-textbook-review.md](../../reviews/02-textbook-review.md)；独立原始记录：[reviews/02-independent-checks.json](../../reviews/02-independent-checks.json)。

- 47项已通过记录，另有02-01早期路径手动核对。
- 02-05修正后全部Shell块重放通过；02-08本机操作在临时副本重放，C003、404、缺数据500、恢复与TERM停止均通过；Git暂存/提交/撤销/冲突等独立验证通过。
- SSH仅以`ssh -G`核对配置语法；Compose默认与覆盖端口、只读挂载解析通过。远程连接、Linux实际部署和Docker容器运行仍保留未实测标记。
- 全站严格构建退出0，10页HTTP200；1290个本模块页面内的本地链接/锚点目标存在。该计数范围包含页面中的本地目标，区别于作者先前956个模块内链接/锚点计数。
- 浏览器抽查模块目录和02-08，排版与折叠答案展开正常。
- 本轮仅更新PROGRESS.md与本记录，不改正文，不重跑已完成检查；用户学习状态未变。

## 阅读组织整合检查（2026-11-01）

依用户“内容保留、重新整合”要求调整首页、侧栏、九章阅读指南和折叠展示。此轮不改运行代码：105个围栏代码块逐字保留，70个原编号小节标题/顺序不变，记录见READING-INTEGRATION.json。严格构建退出0；10页HTTP200，1010个模块内链接/锚点检查通过。此处为作者对新导航与展示的检查，不把此前总对话二次复核当作新布局已独立复核。用户学习状态未变。
