# Windows 下载与账号准备清单

更新：2026-11-09。以下是待在公司电脑核对的清单；已经下载、已经安装、已经登录和实际可用分别记录。现有软件可以直接复用。

## 首批软件与文件

| 内容 | 官方入口或获取方式 | 完成标准 |
| --- | --- | --- |
| ChatGPT/Codex 桌面应用 | [x64 MSIX](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-x64.msix) / [ARM64 MSIX](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-arm64.msix)；设备级离线部署另需 [XML 许可证](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-License.xml) | 选择实际架构，安装后打开并登录；安装方法见 WINDOWS.md |
| PyCharm | [Windows 下载页](https://www.jetbrains.com/pycharm/download/?section=windows)；统一版使用免费核心功能 | 能打开用友项目，并用项目 `.venv` 运行示例 |
| Git for Windows | [官方下载入口](https://git-scm.com/install/windows) | `git --version` 正常，能访问迁移仓库 |
| uv | [官方安装页](https://docs.astral.sh/uv/getting-started/installation/) | `uv --version` 正常；用于获取 Python 和创建环境 |
| Python 3.12 | 复用合适的已有安装，或执行 `uv python install 3.12` | 记录完整版本，创建项目环境 |
| XMind（需要看笔记时） | [官方下载页](https://xmind.com/download) | 能打开项目中的 `.xmind` 文件 |
| 迁移仓库 | [tranfer_to_yy](https://github.com/XguihuaX/tranfer_to_yy)，克隆或下载 ZIP | 用友文件、Skills、全局规则片段和 setup 文件均存在 |
| Python 依赖 | 本仓库 `setup/requirements-base-windows.lock.txt`；文档依赖见 `projects/yonyou/requirements-docs.lock.txt` | 安装、依赖检查和本地示例验证通过 |

这里记录下载安装来源，不把安装程序、虚拟环境或模型权重上传到迁移仓库。安装细节和命令见 [WINDOWS.md](WINDOWS.md)。

## 账号和公司提供的入口

- GitHub：确认新电脑能登录并访问此私有仓库；验证器由用户操作，恢复码留在私密备份位置，不提交到仓库。
- ChatGPT/Codex：确认使用的是个人工作区还是公司提供的工作区，以及公司允许的使用范围。
- 模型调用：记录允许使用的服务、地址、模型名和配置变量名称；Key 在本机配置，不记录到本清单。
- 公司代码仓库、VPN/网络客户端、办公通信、邮箱和内部 AI 平台：使用公司实际提供的安装包、网址和账号；具体名称、权限及规则尚待公司说明。

需要 MCP/代码理解插件时再准备它的运行依赖，例如 Node.js、pnpm；Docker、WSL、GPU 驱动与训练框架按实际项目需要补充，不作为教材恢复的前置条件。

## 公司代码与外部 AI 的使用范围

目前未获得用友对当前岗位、项目和客户代码使用外部 AI 的具体规定。先确认允许的工具、工作区、模型服务和资料范围；未经明确允许，不将非公开公司源码、客户数据、内部文档或日志发送到个人外部 AI 账号，也不上传到此个人迁移仓库。

若公司已批准特定企业工作区、API 网关或内部模型，就按其授权范围使用。OpenAI 的 Business、Enterprise 及 API 默认不使用业务数据训练模型，但这项产品条款不代替公司的授权。[官方企业隐私说明](https://openai.com/enterprise-privacy/)

个人 ChatGPT 工作区可在数据控制中关闭模型改进；Codex 的环境上下文另有 `Include environments` 设置。关闭训练用途仍会把任务所需内容交给服务处理，不应据此认为公司资料可以任意上传。[官方数据控制说明](https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt)

使用云端模型分析本机项目时，读取的代码片段和工具输出可能进入模型上下文。本地执行与离线模型推理是不同配置；不能仅因安装在公司电脑、文件保存在本机或只读访问，就判断资料不会传出。[官方本地执行数据说明](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security)

在范围尚未确认时，可以继续询问通用技术问题、阅读公开代码，或者自行用虚构数据写一个独立的最小复现。仅更改公司名或变量名不一定消除源码中的内部业务信息；日志和截图也应检查具体内容。

可以向负责人或 IT 询问：

> 我想使用 AI 辅助开发。公司允许哪些工具和账号？非公开源码、错误日志、内部文档及客户数据分别能否提供给这些工具？是否有统一的企业工作区或内部模型入口？

## 本机记录模板

将实际结果写入本机 `MIGRATION-STATUS.md`，不要把此空模板当作已完成：

| 软件或服务 | 实际版本/架构 | 已下载 | 已安装 | 已登录/配置 | 已验证 | 待处理 |
| --- | --- | --- | --- | --- | --- | --- |
| ChatGPT/Codex | 待填 | 待核对 | 待核对 | 待核对 | 待核对 | 使用范围 |
| PyCharm | 待填 | 待核对 | 待核对 | 项目解释器待核对 | 待核对 | |
| Git | 待填 | 待核对 | 待核对 | 仓库访问待核对 | 待核对 | |
| Python/uv | 待填 | 待核对 | 待核对 | 虚拟环境待核对 | 待核对 | |
| XMind | 按需 | 待核对 | 待核对 | 按需 | 待核对 | |
| 公司内部工具 | 待提供 | 待核对 | 待核对 | 待核对 | 待核对 | 公司入口 |
