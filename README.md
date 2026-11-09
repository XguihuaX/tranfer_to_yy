# 迁移到公司电脑：Codex 执行入口

更新：2026-11-09（Asia/Shanghai）

仓库：https://github.com/XguihuaX/tranfer_to_yy

## 当前状态

用户计划将用友学习资料、其他个人代码项目及 AI 工具配置迁移到公司电脑，并让新电脑上的 Codex 阅读本文后协助执行。

本仓库已包含用友教材、代码和学习进度快照、75 个 AI Skills，以及用户指定的两段全局 AGENTS.md 规则。其他个人项目、MCP 账号及模型凭据尚未迁移；公司电脑上的安装与验证仍待执行。

- [用友项目与验证说明](YONYOU.md)：文件位于 `projects/yonyou/`。
- [AI Skills 清单及恢复方法](SKILLS.md)：文件位于 `skills/`。
- [全局 AGENTS.md 规则合并说明](configs/codex/README.md)：原文位于 `configs/codex/AGENTS-fragment.md`。

| 项目 | 已确认情况 | 下一步 |
| --- | --- | --- |
| 用友学习项目 | 199 个教材、代码、进度及配套文件已包含 | 下载 projects/yonyou/ 并重建环境 |
| 其他代码项目 | 用户希望纳入，具体名单待补 | 补充名称、来源仓库或文件包、所需数据 |
| AI 工具配置 | 75 个工程与应用 Skills 已上传；其他配置待盘点 | 按 SKILLS.md 恢复 Skills，按目标系统调整其他配置 |
| 全局 AGENTS.md | 用户指定的两段原文已包含 | 按 configs/codex/README.md 合并到用户级文件 |
| 公司电脑 | 已拿到，系统和安装权限待确认 | 在目标电脑检测 |
| 新电脑恢复验证 | 尚未执行 | 按下文执行并记录结果 |

## 给新电脑上的 Codex

用户可复制以下文字发起迁移：

> 请阅读 https://github.com/XguihuaX/tranfer_to_yy 中的 README.md，协助我完成公司电脑迁移。先检查这台电脑的系统、已有软件和本地项目，再恢复仓库中的用友项目、非科研 AI Skills，并将 configs/codex/AGENTS-fragment.md 的两段规则合并到全局 AGENTS.md，重建环境、调整路径并验证。已有可用环境尽量复用；必要的安装和常规可逆配置直接执行。缺少文件来源、登录或权限时，说明具体缺项，并继续不受影响的步骤。请把实际结果写入本地 MIGRATION-STATUS.md，不要把尚未执行的步骤记为完成。

这是私有仓库。若当前 Codex 无法读取，先通过浏览器或 GitHub 登录访问，或由用户下载 README.md 到本地再交给 Codex。不要要求用户把登录令牌粘贴到聊天中。

执行时：

1. 检测系统、CPU 架构、Python、Git、IDE 和项目目录；只询问无法从环境确定的必要信息。
2. 下载或克隆本仓库，用友项目已经位于 `projects/yonyou/`；可直接在该目录使用，或复制到选定工作目录。对其他未列明的项目，只记录缺项，不阻塞已包含项目的恢复。
3. 进入具体项目后先读该项目的 AGENTS.md。用友项目还要读 LEARNING-HUB.md、TEACHING-GUIDE.md 和当前模块的 PROGRESS.md。
4. 按项目建立虚拟环境、恢复依赖和运行配置。遇到已存在的配置先检查并保留，再做有针对性的修改。
5. 先运行不需要外部账号的本地示例，再完成需要用户登录的接入。真实模型调用使用用户确定的服务和账号。
6. 按 [SKILLS.md](SKILLS.md) 恢复所选 Skills；按 [全局规则说明](configs/codex/README.md) 合并两段 AGENTS.md 原文，保留目标文件其他内容。
7. 持续记录已完成、失败原因、缺失资料与下一步；重复执行时跳过已验证且未变化的步骤。

迁移工作不要求新建其他 Codex 对话。若用户另外要求在本机已有项目创建新对话，选择 local 环境；仅在用户明确要求时使用 worktree。

## 已打包的用友学习项目

旧电脑为 macOS。旧路径为 `/Users/liujunhong/Documents/ChatGPT/用友`，该路径仅用于定位旧文件，目标电脑应使用实际目录。

旧项目目录本身在盘点时没有 Git 提交及远程地址。本次已将筛选后的快照提交到当前迁移仓库的 `projects/yonyou/`，新电脑可以直接通过本仓库取得。文件清单与校验值见 [project-manifest.json](project-manifest.json)。

### 已包含的文件

- `docs/`：教材正文、导航、素材与部分 XMind 文件；保留隐藏的 `.pages` 文件。
- `learning/`：示例代码、依赖清单、各模块 PROGRESS.md、核对记录、XMind 笔记与教学数据库；排除内部虚拟环境和缓存。
- 根目录的 `AGENTS.md`、`LEARNING-HUB.md`、`TEACHING-GUIDE.md`、`mkdocs.yml`、`requirements-docs.txt`、`requirements-docs.lock.txt`、`.gitignore`。
- `scripts/`、`templates/`、`reviews/`。

关键笔记与数据包括：

- `docs/01-python-api/assets/01-Python-API-概念地图.xmind`
- `learning/02-deployment/学习笔记-含02-06整理.xmind`
- `learning/02-deployment/学习笔记-整理前备份.xmind`
- `learning/08-database/ch01/erp_ch01.db`（教学示例数据库）

不必传输 `.venv*` 虚拟环境、`__pycache__/`、`site/` 生成网页和 `tmp/` 临时目录。IDE 配置可能包含旧路径或环境变量，应检查后迁移必要设置，不直接整目录覆盖。

通过克隆本仓库或下载仓库 ZIP 获取文件，注意保留 `.pages`、`.env.example` 等隐藏文件。此次未打包真实凭据和 IDE 工作区；根 `.gitignore` 已补充虚拟环境、真实 `.env` 与缓存等排除规则。

### 重建运行环境

项目示例使用 Python 3.12。目标电脑先确认可用的 Python 3.12 解释器，再执行对应系统的命令；以下所有命令均从用友项目根目录运行。若刚克隆迁移仓库，先执行 `cd projects/yonyou`；若已将项目复制到其他工作目录，则进入该实际目录。

Windows 命令使用 cmd；如使用 PowerShell，按其语法调整。以下命令不需要激活虚拟环境。若 `py` 或 `python3.12` 不存在，先定位或安装 Python，不要反复执行同一失败命令。

**教材环境——Windows cmd：**

```bat
py -3.12 -m venv .venv-docs
.venv-docs\Scripts\python.exe -m pip install -r requirements-docs.lock.txt
.venv-docs\Scripts\python.exe -m mkdocs build --strict
.venv-docs\Scripts\python.exe -m mkdocs serve --dev-addr 127.0.0.1:8765
```

**教材环境——macOS/zsh：**

```sh
python3.12 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.lock.txt
.venv-docs/bin/python -m mkdocs build --strict
.venv-docs/bin/python -m mkdocs serve --dev-addr 127.0.0.1:8765
```

访问 `http://127.0.0.1:8765/` 验证教材。serve 会持续运行，其他操作另开终端；Ctrl+C 停止。原 `scripts/serve-docs.sh` 使用 macOS/Linux 环境路径，Windows 可直接使用上面的命令。

**03 计算助手 MVP——Windows cmd：**

```bat
py -3.12 -m venv learning/03-llm-tools/mvp/.venv
learning\03-llm-tools\mvp\.venv\Scripts\python.exe -m pip install -r learning/03-llm-tools/mvp/requirements.txt
learning\03-llm-tools\mvp\.venv\Scripts\python.exe learning/03-llm-tools/mvp/main.py
```

**03 计算助手 MVP——macOS/zsh：**

```sh
python3.12 -m venv learning/03-llm-tools/mvp/.venv
learning/03-llm-tools/mvp/.venv/bin/python -m pip install -r learning/03-llm-tools/mvp/requirements.txt
learning/03-llm-tools/mvp/.venv/bin/python learning/03-llm-tools/mvp/main.py
```

执行前确认 `main.py` 的 `MODE = "local"`，预期出现 `multiply(12, 3) → 36` 和 `add(36, 8) → 44`；此模式无需模型 Key。若源码已变化，先核对当前运行入口。

PyCharm 打开相应示例目录，选择新建环境的解释器，工作目录选择该示例目录。旧 MVP README 中指向 Mac 验证环境的绝对路径应替换成新电脑的环境路径。

其他示例按需要恢复，不必一次安装全部：

| 用途 | 依赖或说明位置 |
| --- | --- |
| 01 API 示例 | `learning/01-python-api/api-lab/README.md` 与 `requirements.lock.txt` |
| 03 连续 LLM 示例 | `learning/03-llm-tools/lab/README.md` 与 `requirements.txt` |
| 03 MCP 示例 | `learning/03-llm-tools/lab/requirements-mcp.txt` |
| 03 作者完整环境记录 | `learning/03-llm-tools/requirements-verified.lock.txt` |

这些依赖文件来自旧电脑项目；本次尚未在目标系统重新安装验证。如果版本或包源不可用，记录具体错误后核对版本和兼容性，不直接批量升级全部依赖。

### 模型服务配置

现有示例读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_PROTOCOL` 环境变量。代码不自动加载 `.env`；在 PyCharm 的运行配置或本地进程环境中设置。

用户曾提到 Qwen/HeyRoute，实际服务入口、型号及目标电脑是否继续使用尚待确认。密钥由用户在目标电脑本地设置，不写入本文或迁移状态文件。

### 学习衔接

教材、阅读进度和实操完成情况分别记录。最新位置以迁移时的 `learning/03-llm-tools/PROGRESS.md` 为准；2026-11-09已有模型调用、消息、结构化输出和工具循环答疑，不应仅依据总览中较早的“尚未开始”描述重开课程。

迁移验证通过表示环境能运行，不改变用户的掌握记录。

## 其他项目与 AI 配置清单

名单确定后逐项填充以下字段：

| 对象 | 文件来源/仓库地址 | 分支或版本 | 运行依赖 | 配置变量名称 | 验证方法 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 用友学习项目 | 本仓库 projects/yonyou/ | 2026-11-09 快照 | Python 3.12、各依赖清单 | LLM_* | 教材构建、MVP 本地结果 | 已打包，目标未恢复 |
| 其他代码项目 | 待用户补充 | 待盘点 | 待盘点 | 仅记名称 | 待项目核对 | 未盘点 |
| AI Skills | 本仓库 skills/，详见 SKILLS.md | 2026-11-09 快照 | 部分需要框架或完整插件 | 不包含凭据 | 文件校验、发现与按需功能验证 | 75 个已上传，目标未安装 |
| 全局规则 | configs/codex/AGENTS-fragment.md | 2026-11-09 原文 | 目标用户级 AGENTS.md | 无 | 合并后回读核对 | 已打包，目标未合并 |
| 其他 AI 工具配置 | 待用户指定工具 | 待盘点 | 待盘点 | 仅记名称 | 工具可用性检查 | 未盘点 |

用户已明确排除论文和科研 Skills。已打包内容及恢复方式见 [SKILLS.md](SKILLS.md) 和 [skills-manifest.json](skills-manifest.json)。

AI 配置按实际工具整理：

- 个人规则和提示词：本次已包含“决策与执行原则”“主张、边界与预设质疑”两段；按全局规则说明合并，不用项目级文件覆盖全局文件。
- Skills：记录所选 Skill 来源、正文与依赖脚本，检查是否使用 macOS 专用命令；插件安装内容优先按目标电脑支持的方式重新安装。
- MCP：记录服务用途、启动命令、依赖和环境变量名称；本地路径和可执行文件重新定位，账号重新连接。
- 模型配置：保留服务地址、模型名等必要非秘密配置，凭据在本地设置。
- 聊天与历史记录：单独核对所用工具的实际同步或导出能力；不把复制项目文件记为聊天迁移完成。当前工作衔接优先依赖项目内落盘的进度和交接文档。

不要整目录覆盖新电脑的 AI 工具配置或复制旧机器的登录凭据。遇到工具版本差异时，先检查目标电脑可用的配置格式，再合并必要设置。

## 验收与状态记录

在本地建立 `MIGRATION-STATUS.md`，只记录实际完成情况：

- [ ] 已记录目标系统、项目路径与可用解释器。
- [ ] 已取得用友项目文件，教材、笔记、代码和进度均存在。
- [ ] 教材 `mkdocs build --strict` 通过，浏览器可阅读。
- [ ] MVP 本地模式结果为 36 和 44。
- [ ] PyCharm 已选择新解释器并能运行示例（若本轮包含 IDE 配置）。
- [ ] 所选其他项目分别完成各自验证。
- [ ] 两段全局规则已合并并回读核对。
- [ ] 所选 Skills 完成恢复检查；MCP 账号配置仅在本轮实际纳入时验证。
- [ ] 模型账号已配置并验证，或明确记录为待用户接入。

状态文件应记录检查日期、命令或操作、实际结果、失败原因和下一步，不记录密钥。只有此次选定范围内的项目均有结果后，才报告整体迁移完成。

打包端已对用友副本完成严格教材构建、XMind 与 SQLite 完整性检查，具体见 [YONYOU.md](YONYOU.md)。Windows/macOS 恢复命令尚未在新电脑执行；其他个人项目及聊天记录尚未迁移。
