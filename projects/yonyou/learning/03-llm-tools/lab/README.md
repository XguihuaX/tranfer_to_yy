# 03 连续代码例子

配套网页从03-01开始。可先读代码，操作按需选择；业务数据均为合成，不连接真实ERP。

Python3.12，主要依赖见requirements.txt，MCP选读另装requirements-mcp.txt。完整作者环境见上级requirements-verified.lock.txt。

PyCharm选lab独立.venv解释器，工作目录为lab，脚本为对应文件。Run配置设置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、LLM_API_PROTOCOL。字段见.env.example；代码不自动加载.env。具体服务、模型访问与工具能力在真实接入时核对，不预设账户可用型号。

| 文件 | 用途 | 模型调用 |
| --- | --- | --- |
| business.py | 本地合成业务 | 无 |
| 01_call.py | 第一次调用 | 1轮，可能SDK重试 |
| 02_messages.py | 两轮历史加模板 | 3轮 |
| 03_structured.py | 意图提取再执行 | 1轮 |
| 04_tool_loop.py | 手动循环 | 最多4轮 |
| 04_coffee_tools.py | 完整咖啡例子：菜单/价格/库存、工具包装、执行与回填 | 最多5轮，SDK可能重试；支持工具的Chat Completions入口 |
| 05_agent.py | 两工具Agent | 受图步数限制，不等于精确API次数 |
| 06_runtime.py | 异步等待；另有流函数 | 默认只运行异步路径 |
| 07_review.py | 业务与参数检查 | 无 |
| mcp_client.py | 启动本机MCP服务并调用 | 无，需MCP依赖 |

导入课程文件不会自动请求模型。作者的.venv-verify仅用于核对，不替代你自己的PyCharm运行配置。从项目根运行作者检查：

```sh
learning/03-llm-tools/.venv-verify/bin/python learning/03-llm-tools/verify_examples.py
```

检查用本地模拟HTTP、固定假凭据和fixture.invalid地址，MCP实际启动本机子进程。它验证程序与框架，不验证真实模型的选择质量。
