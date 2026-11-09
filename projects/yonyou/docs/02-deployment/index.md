# 02 Linux、Git 与部署

本模块围绕一件事展开：**把一个 Python 服务运行起来，出错时找到原因，并能把运行方法交给别人。** 你已有一些 Git 和 SSH 基础，学习时优先补环境、日志和端口排查。

全部九章、完整示例、练习与答案均保留。下面用一张表统一阅读顺序：主线先读，基础操作和远程步骤按需查阅，Docker 后续选学。

## 讲解深度随学习反馈调整

继续按概念、执行过程、例子和排障学习。已经熟悉的基础可以略过；命令先讲用途、关键参数和结果，不要求背诵完整语法。某个细节影响当前理解或用户主动追问时，再逐步展开。完整示例与练习保留作查阅。

适量补充怎样向AI说明目标、约束和验收结果，以及怎样检查AI生成的命令或代码；这些是原有学习的补充，不替代必要机制、代码理解和实际操作。一轮围绕一个小问题，不强制每节都改成提示词模板或检查清单。

## 操作环境：Mac为主，Windows cmd按差异补充

自2026-11-05起，后续讲解与练习以 **Mac终端（默认zsh）** 为主。Windows只在命令、路径或行为有差异时单独标注 **Windows cmd** 的写法，不展开PowerShell。Git等共通命令只讲一遍。

涉及远程Linux时明确标注实际执行环境，不把Mac与Linux视为完全相同。既有Windows练习保留供查阅；02-03中的[Windows cmd完整流程](03-git-changes.md#windows-practice)仍可使用，Mac流程也已保留。

## 从这里开始

**当前页面（2026-11-07）：[02-06 进程与端口](06-processes-and-ports.md#reading-guide)，正在讨论§3后台运行与日志。** 按你的选择顺序阅读，熟悉内容略过即可。下面的精简路线保留作另一种阅读安排。

**[02-05 环境与权限](05-environment-and-permissions.md#reading-guide) → [02-06 进程与端口](06-processes-and-ports.md#reading-guide) → [02-08 综合交付练习](08-delivery-lab.md#reading-guide)**

先按 **2–3 小时**安排这条主线和少量复习，不含真实远程部署与 Docker 实践；按熟悉程度调整。05/06可先读执行过程，最后在08完整操作一次，不必重复运行所有基础练习。

## 全部内容与阅读安排

| 安排 | 章节 | 本次重点 | 完整内容放在哪里 |
| --- | --- | --- | --- |
| 主线 1 | [02-05 环境与权限](05-environment-and-permissions.md#reading-guide) | §1–5：export、解释器/venv、权限 | 正文与故障例全部保留 |
| 主线 2 | [02-06 进程与端口](06-processes-and-ports.md#reading-guide) | §1–4：启动、PID、监听、日志、连接失败 | 资源观察与Linux服务管理折叠保留 |
| 主线 3 | [02-08 综合交付练习](08-delivery-lab.md#reading-guide) | 修改→提交→启动→查询→故障恢复→停止与交接 | 完整源码折叠保留，Linux迁移步骤仍在§8 |
| 按需查阅 | [02-01 终端与路径](01-terminal-paths.md#reading-guide) | 当前目录与相对路径；需要时看§4、§6 | 完整入门示例、误区和练习保留 |
| 按需查阅 | [02-02 文件与日志](02-files-and-logs.md#reading-guide) | 管道、stdout/stderr、覆盖/追加、退出码 | 文件操作、固定日志与完整操作过程保留 |
| 快速复习 | [02-03 Git 修改与提交](03-git-changes.md#quick-read) | 两种diff、暂存后再编辑、忽略规则 | 完整建仓库与提交演示可展开 |
| 快速复习 | [02-04 Git 协作与撤销](04-git-collaboration.md#quick-read) | fetch/pull、冲突、restore/revert/stash | 双人副本、冲突解决、撤销流程可展开 |
| 远程查阅 | [02-07 SSH 与传输](07-ssh-and-transfer.md#quick-read) | 两端路径、localhost、会话断开 | 登录、公私钥、scp、隧道、nohup/tmux可展开 |
| 后续选学 | [02-09 Docker 与 Compose](09-docker-compose.md#reading-guide) | 镜像/容器、端口映射、环境与挂载 | 完整配置、启动、验证、排错步骤保留 |

章节编号保持不变，便于引用和查找。侧栏按同一阅读安排分组；各章开头的“本章怎么读”说明重点、前提与接下来去哪。

## 怎样使用完整例子

读概念时可以跳到相关小节；真正运行时，要从该例子的目录和环境准备开始。尤其Git双人演示依赖前面的分支状态，不能只复制冲突处理中间几行。

配套文件都在项目的 `learning/02-deployment/`：`terminal-lab` 对应路径，`log-lab` 对应日志，`env-lab` 对应配置与权限，`service-lab` 对应服务、综合交付和Docker。Git与交付练习使用独立副本，各章标明机器、目录和终端角色。

练习可选，不设通关门槛。熟悉的Git/SSH操作直接略过，遇到具体问题再展开；可在 [02学习对话](codex://threads/01a19181-cf52-78d2-9a73-567be283f7fc) 按章节或命令提问。

[返回学习手册首页](../index.md)
