# 基础环境准备与验证

日期：2026-11-09。

- 已根据 01/API 与 03/LLM 现有依赖整理 9 项直接依赖，统一 Pydantic 为 2.14.3。
- 使用 uv 为 Python 3.12、Windows x64 解析依赖，要求只使用预编译 wheel，成功生成含 50 个包的 `requirements-base-windows.lock.txt`。
- MCP 选装清单也完成相同 Windows x64 条件下的解析；未将 MCP 纳入基础必装项。
- 在当前 Mac 上新建独立 Python 3.12.14 环境，从 `requirements-base.txt` 安装成功；uv pip check 检查 50 个已安装包，未发现依赖冲突。
- `verify_base.py` 通过：直接依赖版本、课程 MVP 本地结果 36/44、真实 FastAPI 应用的内存 HTTP 查询与未知客户处理、LangChain/OpenAI 本地模拟响应、只读 SQLite 完整性。
- 未发送真实模型请求。安装和验证使用临时环境，未更改原课程解释器和文件。

Windows 依赖解析成功不等于 Windows 运行已验证。目标电脑还需实际安装、执行 pip check 和 verify_base.py，并完成 PyCharm 和教材网页验证。ARM64 Windows 需另按实际解释器解析和检查。

ChatGPT MSIX 下载地址已从 OpenAI 官方部署文档核对；未在目标电脑执行安装。PyCharm 免费功能和 uv 安装方式已核对官方说明，来源见 WINDOWS.md。
