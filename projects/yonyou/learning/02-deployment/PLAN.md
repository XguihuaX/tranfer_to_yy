# 02 Linux、Git 与部署：总体规划与编写任务

规划者：学习总对话。日期：2026-10-31。执行对话：codex://threads/01a19181-cf52-78d2-9a73-567be283f7fc。

## 本次用户要求

用户明确要求：总对话先调研和规划模块整体框架，将任务交给 02 对话完成教材，完成后再由总对话二次核对。

因此，本次授权一次准备整个 02 的教材，不再受早前“后续逐章准备”的默认安排限制。用户阅读仍按自己的进度进行；批量备课不表示已读或已掌握。先保留已完成的 02-01 与 terminal-lab，再编写后续章节。

## 模块目标

面对一个 Python AI 服务，能在本机或 Linux 服务器上确认文件与执行环境，用 Git 保存和协作修改，启动并验证服务，通过日志、进程与端口定位常见故障，说明部署和交接步骤。

当前基础：用户自述已读完 01，熟悉查询服务的例子；需明确标注客户端/服务端，以及本机/远程/容器角色，避免无提示切换。不会 Linux 服务器部署与 Docker，Git 熟练度按实际练习反馈调整。不重讲 Python 语法，不要求先补前章练习。

## 教材结构

| 编号与文件 | 核心问题 | 必须覆盖与递进成果 |
| --- | --- | --- |
| 02-01 `01-terminal-paths.md` | 在哪里执行，怎样找到并启动项目？ | 保留已有正文和示例；终端/Shell/Python，pwd/ls/cd/cat，绝对/相对路径、引号、当前目录与脚本位置；正常和错误目录运行 |
| 02-02 `02-files-and-logs.md` | 怎样从文件和日志找到证据？ | 文件复制/移动/创建、find、grep（rg 可选）、less/head/tail、管道、stdin/stdout/stderr、`>` 与 `>>`、退出码；提供固定小日志与可预期筛选结果；长运行 follow 如何退出 |
| 02-03 `03-git-changes.md` | 一组修改怎样保存并追溯？ | 仓库/工作区/暂存区/提交/HEAD；status/diff/diff --staged/add/commit/log/show；tracked/untracked、.gitignore 对已跟踪文件的限制；仅在独立练习仓库演示 |
| 02-04 `04-git-collaboration.md` | 怎样协作、解决冲突和撤销？ | switch/branch/merge、fast-forward 与冲突；restore --staged、restore 文件、revert 的对象和影响；stash 的适用情境；remote/fetch/pull/push、upstream；本地 bare 仓库加两个 clone 演示，无需真实账号；以 pull --ff-only 明确当前教学策略，解释不能快进时的下一步；不默认 force push 或 reset --hard |
| 02-05 `05-environment-and-permissions.md` | 程序为何读不到配置、依赖或文件？ | Shell 变量与 export、父子进程继承、PATH/command -v、单/双引号、python -m pip 与 venv、.env 不会凭空载入进程、ls -l 的用户/组/rwx、目录 x 权限、chmod 常用最小更改；同一小例复现并修复至少两种故障 |
| 02-06 `06-processes-and-ports.md` | 服务没起来或访问不到，怎样定位？ | PID/进程/监听地址/端口/前台后台、Ctrl-C/kill TERM、ps/lsof、Linux ss、curl/HTTP状态；127.0.0.1 与 0.0.0.0 的含义及其在本机/远程场景中的位置；日志重定向、请求状态与连接失败区分；服务未启动、端口占用、配置缺失案例；CPU/内存/磁盘最小观察；systemd/journalctl 作为 Linux 管理方式介绍，不作为Mac命令 |
| 02-07 `07-ssh-and-transfer.md` | 如何连接另一台机器并操作服务？ | SSH 用户/主机/端口、身份认证与主机身份验证、公钥/私钥、known_hosts 意义；ssh -p 与 scp -P；上传/下载与两端路径、退出回本机、远程 localhost；会话断开后进程的影响，nohup/tmux 与正式服务管理的区别；示意主机明确标占位，不执行未知服务器连接 |
| 02-08 `08-delivery-lab.md` | 怎样完成一次可交接的小变更？ | 用小型查询服务将“Git修改/检查/提交→环境/配置→启动→curl验证→日志排障→停止→交接说明”连起来；给文件树、完整必要文件、端口及目录、正常输出、故障和修复；Mac完整路径可运行，Linux迁移步骤单独标明 |
| 02-09 `09-docker-compose.md`（选学） | 怎样把服务放进容器并看懂运行条件？ | image/container/Dockerfile/Compose/volume、build/up/ps/logs/exec/down、端口映射、容器内部监听与宿主映射；宿主与容器localhost；环境注入与Compose .env插值的区别；最小Dockerfile/.dockerignore/compose.yaml；复用服务例子，不额外加入数据库或缓存；说明安装与引擎前提，按实际条件验证 |

Git 提前放在第 3–4 章，避免学完所有 Linux 内容才开始版本管理。Docker 最后备好供选读，不阻碍前面学习。

## 示例与执行约定

- 同一应收查询小案例逐步展开。02-01 保持现有文件和行为；后续日志/服务案例从短小文件开始，在模块自己的练习目录存放。
- 每组命令先注明“在哪台机器、哪个目录、哪个终端”及前置状态；A/B终端用途固定。不把Mac命令和Linux命令无标识混用。
- 标准库小服务或少量已有 FastAPI 依赖均可，由 02 选择最简单且可解释的实现；不得重复教学 01 的 HTTP 框架全部知识。
- Git 演示必须位于模块内独立练习仓库或临时目录；局部身份配置，仅作用于练习；不提交、切换或重置主项目，不更改全局Git配置。
- 非必要的删除、sudo、递归权限更改、全局进程终止等不放进默认一键操作。撤销命令要展示将影响哪一层和哪份练习文件。
- 运行验证启动的服务只操作自己掌握的PID，结束后清理；不停止用户原有服务或改变Docker上下文。
- SSH、公网服务器和 Docker 引擎缺少条件时，正文仍应完整，实测记录明确写哪些未运行及如何在正确环境验证。不能将Mac运行标为Linux远程部署验证。
- 每章按 AGENTS.md 编写完整正文、例子、误区、可选练习与折叠答案、回顾、来源和导航；短答/提纲不算完成。

## 当前环境检查

- Git：2.39.2（Apple Git-143）。
- OpenSSH：10.0p2（本机客户端）。
- Docker 客户端存在，但尝试连接当前 Docker socket 失败，未发现运行中的引擎。本次不以运行 Docker 为教材完成的前置条件，不自动安装或启动系统服务。
- tmux 命令未发现；可完整解释使用方式并给前提，不要求安装才开始教学。

这些是2026-10-31检查时的结果，后续实践前可重查，不能作为永久环境结论。

## 官方资料与调研结论

官方资料核对日期：2026-10-31。

- Git 工作区/暂存/提交：https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository
- Git 分支和合并：https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
- git restore：https://git-scm.com/docs/git-restore
- git fetch：https://git-scm.com/docs/git-fetch
- OpenSSH 客户端：https://man.openbsd.org/ssh
- scp：https://man.openbsd.org/scp
- systemd 服务：https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- Docker 概念：https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/
- Docker 端口：https://docs.docker.com/engine/network/port-publishing/
- Compose 入门：https://docs.docker.com/compose/gettingstarted/
- Compose 插值：https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/

基于上述资料，教材分别建立版本保存、远程登录、服务管理与容器运行的概念，不把这些工具混为一套操作。Shell 重定向应结合本机手册与实际小例核对；本轮 GNU 在线手册请求超时，POSIX页面返回403，未将其记为成功读取来源。

## 作者交付与二次复核

02 对话完成：

1. 9 章完整教材、模块 index/.pages，以及必要练习文件；不改其他模块或根配置。
2. `learning/02-deployment/VERIFICATION.md`：逐类说明执行的命令、核对的结果、未运行条件，能重现检查；不过度开发专用测试框架。
3. 一次严格构建，检查本模块章间链接、锚点、折叠答案和必要代码与文件一致性。
4. 更新 PROGRESS.md，真实区分批量备课完成与用户学习进度；本对话给完成摘要和入口，主对话读取即可，无需自动跨对话发消息。

总对话随后：

1. 通读章节结构和关键说明，检查知识递进、角色、平台差异和新术语是否清楚。
2. 独立重跑关键案例：目录故障、日志筛选、Git暂存/提交/撤销/冲突/远端演示、环境继承、服务正常与失败路径。
3. 复核 SSH/Docker/Linux 专用步骤的前提与实际验证范围，核实命令语义，不以未运行冒充实测。
4. 检查导航和构建，将具体问题反馈给02修正；修正后只重查受影响内容。
5. 在 `reviews/02-textbook-review.md` 保存结果与限制，向用户交付入口。
