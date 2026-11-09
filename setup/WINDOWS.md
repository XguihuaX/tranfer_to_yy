# Windows 软件与基础 Python 环境

更新：2026-11-09。用户已确认公司电脑为 Windows。本文供新电脑上的 Codex 执行；当前还没有在目标 Windows 电脑安装软件。

软件下载与账号状态统一记录在 [DOWNLOADS.md](DOWNLOADS.md)，其中也列出公司代码使用外部 AI 需要确认的范围。

## 安装哪些软件

| 程序 | 用途 | 本次安排 |
| --- | --- | --- |
| ChatGPT 桌面应用（包含 Codex） | 继续迁移、阅读与开发 | 用户要求不经过 Microsoft Store；使用下方官方 MSIX 路线 |
| PyCharm 免费核心功能 | 阅读、运行和调试 Python | 安装当前统一版，使用免费功能 |
| Git for Windows | 下载迁移仓库、版本管理 | 已有可用版本就复用 |
| Python 3.12 | 运行现有课程 | 复用合适的现有版本，或用 uv 安装 3.12 |
| uv | 获取 Python、创建环境和安装依赖 | 没有合适 Python 时采用；不需要 Anaconda |
| XMind | 打开现有思维导图 | 需要阅读笔记时安装，使用公司已有许可或可用免费功能 |

这一轮先完成教材、API 和 LLM 应用环境。Docker、WSL、数据库服务器和 GPU 训练工具等，进入相应任务后再配置。SQLite 已随 Python 提供，无需单独安装数据库服务器。

### PyCharm 下载与免费版本

使用 [JetBrains PyCharm 下载页](https://www.jetbrains.com/pycharm/download/?section=windows) 下载 Windows 安装程序，选择与设备架构匹配的版本。

从 2025.1 起 PyCharm 合并社区版与专业版；统一版的核心功能继续免费，Pro 试用结束后可继续免费使用。现有课程以脚本、终端和浏览器运行 FastAPI，不依赖付费 Web 框架专用功能。公司已经装有可用社区版时，可以先复用。[官方版本说明](https://www.jetbrains.com/help/pycharm/unified-pycharm.html)

安装完成后先打开项目，再按后面的说明选择解释器。不要把 IDE 安装目录当成 Python 环境。

### Git 与 Python

Git 可从 [Git for Windows 官方入口](https://git-scm.com/install/windows)下载安装。WinGet 可用时也可执行：

```bat
winget install --id Git.Git -e --source winget
```

Python 采用 3.12，与已有课程一致。Python 3.12 后续安全版本没有传统 Windows 安装程序，3.12.10 是最后一个带传统二进制安装程序的完整维护版本，因此这里不把旧安装程序作为新电脑默认方案。[Python 官方说明](https://www.python.org/downloads/release/python-31216/)

如果当前电脑没有合适的 Python 3.12，可通过 uv 使用其维护的 python-build-standalone 构建。先安装 uv：

```bat
winget install --id astral-sh.uv -e --source winget
```

重开终端，确认 `uv --version`，再执行：

```bat
uv python install 3.12
```

uv 会安装当前 uv 版本支持的 3.12 补丁版本；若版本清单较旧，先更新 uv。若 WinGet 不可用，使用 [uv 官方安装页](https://docs.astral.sh/uv/getting-started/installation/)列出的 Windows 安装方式或官方 GitHub 发布包。该操作不需要打开 Microsoft Store。[Python 管理说明](https://docs.astral.sh/uv/guides/install-python/)

## ChatGPT 不经过 Microsoft Store 的安装方式

来源：[OpenAI 官方 Windows 部署说明](https://learn.chatgpt.com/docs/enterprise/windows-deployment)，其中的 “Install from an offline package”。

按“设置 → 系统 → 系统信息/关于”中的处理器架构选择一个包：

- Intel/AMD x64：[ChatGPT-x64.msix](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-x64.msix)
- ARM64（如 ARM 版 Windows 设备）：[ChatGPT-arm64.msix](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-arm64.msix)
- 采用下述设备级离线部署时，另需：[ChatGPT-License.xml](https://persistent.oaistatic.com/codex-app-prod/ChatGPT-License.xml)

这是官方文档直接提供的 MSIX 与离线许可证链接，不需要经过商店界面或使用 `winget --source msstore`。

如果只为当前 Windows 用户安装，可先尝试双击 MSIX，或在文件所在文件夹运行 `Add-AppxPackage -Path .\ChatGPT-x64.msix`（ARM64 使用对应文件名）。这是 Windows 的[单用户安装方式](https://learn.microsoft.com/en-us/powershell/module/appx/add-appxpackage)；本轮未在目标电脑验证此包的安装、许可和启动结果。若安装并正常启动，无需另走设备级预配。下列两文件流程是 OpenAI 文档给出的设备级离线部署方案。

将选中的 MSIX 改名为 `ChatGPT.msix`，与 `ChatGPT-License.xml` 放在同一文件夹；许可证若被浏览器直接显示，可用“另存为”保留 XML 扩展名。

在该文件夹中以管理员身份打开 **Windows PowerShell**，执行：

```powershell
Add-AppxProvisionedPackage -Online `
    -PackagePath .\ChatGPT.msix `
    -LicensePath .\ChatGPT-License.xml `
    -Regions all
```

这是设备级预配安装，需管理员权限。如果开始菜单暂时没出现应用，注销 Windows 再登录。安装后的应用仍需要网络和账号登录；这份安装包的获取方式不处理网络访问问题。若报缺少依赖或策略阻止，保留完整错误码交给新电脑 Codex/IT 判断，不通过关闭证书验证解决。

官方说明目前没有独立 MSI 或不依赖商店分发的 EXE 安装包；用户要避免商店分发服务时，采用这里的 MSIX 离线路线。下载链接随官方更新提供最新版，本文只核对了链接与文档，没有在目标电脑执行安装或验证签名。

## 建立共用基础环境

以下命令以 **Windows cmd** 为准，当前目录为迁移仓库根目录，也就是可以看到 `README.md`、`setup`、`projects` 的目录。带空格的绝对路径需加双引号。软件安装与 Python 包安装是两件事，requirements 文件只管理 Python 包。

目录安排：

```text
tranfer_to_yy/
  setup/requirements-base.txt                  基础直接依赖
  setup/requirements-base-windows.lock.txt     Windows x64 完整版本快照
  setup/verify_base.py                         本地验证
  projects/yonyou/.venv/                       Python/API/LLM 共用环境
  projects/yonyou/.venv-docs/                  教材网页环境
```

`requirements-base.txt` 包含 FastAPI、Uvicorn、WebSockets、HTTPX、Pydantic、LangChain、LangChain Core、LangChain OpenAI 和 OpenAI SDK。版本来自课程已有验证环境；Pydantic 统一采用 03 模块的 2.14.3，避免把旧 01 与 03 的完整锁文件叠加导致版本冲突。

如果 `.venv` 已存在，先检查解释器，不要盲目重建。首次创建并安装（Windows x64）：

```bat
uv venv --python 3.12 --seed projects\yonyou\.venv
projects\yonyou\.venv\Scripts\python.exe -m pip install -r setup\requirements-base-windows.lock.txt
projects\yonyou\.venv\Scripts\python.exe -m pip check
projects\yonyou\.venv\Scripts\python.exe setup\verify_base.py
```

已经通过 Python Launcher 安装了合适的 Python 3.12 时，第一条可换成 `py -3.12 -m venv projects\yonyou\.venv`，后续不变。无需激活环境，也不必修改 PowerShell 执行策略。

ARM64 Windows 应根据实际解释器架构使用 `requirements-base.txt` 重新解析和验证，不能把 x64 解析结果记为 ARM64 已验证。安装失败时先保留错误，核对 Python 版本、包源和缺失包，不自动换成任意新版本。

验证脚本检查真实课程的本地工具计算、FastAPI 查询、模拟模型响应及 SQLite 文件，不请求外部模型、不需要 Key。全部通过时输出 `Base environment check passed`。

MCP 按需安装：

```bat
projects\yonyou\.venv\Scripts\python.exe -m pip install -r setup\requirements-mcp.txt
projects\yonyou\.venv\Scripts\python.exe -m pip check
```

原课程各模块的依赖清单保留，供独立复现使用；本共用环境采用 setup 下的基础清单，不再依次安装所有旧锁文件。

## 教材网页环境

首次建立：

```bat
uv venv --python 3.12 --seed projects\yonyou\.venv-docs
projects\yonyou\.venv-docs\Scripts\python.exe -m pip install -r projects\yonyou\requirements-docs.lock.txt
projects\yonyou\.venv-docs\Scripts\python.exe -m mkdocs build --strict -f projects\yonyou\mkdocs.yml
projects\yonyou\.venv-docs\Scripts\python.exe -m mkdocs serve -f projects\yonyou\mkdocs.yml --dev-addr 127.0.0.1:8765
```

打开 `http://127.0.0.1:8765/`。服务持续运行，其他操作使用新终端，Ctrl+C 停止。

## PyCharm 选择哪个解释器

1. 用 PyCharm 打开迁移仓库中的 `projects/yonyou` 文件夹。
2. 打开 Settings，找到 Python Interpreter，选择添加本地已有解释器；不同版本设置入口名称可能略有差异。
3. 选择该项目的 `.venv\Scripts\python.exe`。这是刚建立的基础环境。
4. 打开 `learning/03-llm-tools/mvp/main.py`，保留 `MODE = "local"`，运行。
5. 运行配置中的工作目录设为 `learning/03-llm-tools/mvp` 的实际绝对路径；应显示 36 和 44。

不要选择 `.venv-docs` 运行 LLM/API 示例。后续真实模型接入时，在运行配置设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、LLM_API_PROTOCOL；现有示例不自动读取 `.env`。[PyCharm 官方解释器配置说明](https://www.jetbrains.com/help/pycharm/configuring-python-interpreter.html)

## 新电脑验收记录

在本地 `MIGRATION-STATUS.md` 记录软件版本、Python 完整版本、解释器路径、`pip check` 结果、验证脚本结果、教材网页能否打开，以及 PyCharm 实际运行结果。通过终端验证和完成 IDE 配置分别记录。

本仓库准备与验证范围见 [VALIDATION.md](VALIDATION.md)。Windows 软件安装、管理员权限和 IDE 操作最终在目标电脑核对。
