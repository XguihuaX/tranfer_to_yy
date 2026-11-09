# PyCharm CE 计算助手 MVP

先打开 `main.py`。注释按工具、入口、Agent 三个位置组织；模型接入放在 `settings.py`。

配套阅读：[MVP 动手导读](http://127.0.0.1:8765/03-llm-tools/mvp-walkthrough.html)。

## 第一次运行

1. PyCharm CE → Open，打开本 README 所在的 `mvp` 文件夹。
2. 选择已有 Python 解释器：
   `/Users/liujunhong/Documents/ChatGPT/用友/learning/03-llm-tools/.venv-verify/bin/python`。
   这是现有教材验证环境，Python 3.12，已经装好本例依赖；本次直接复用，不需要安装新包。
3. 打开 `main.py`，保留 `MODE = "local"`，右键 → Run 'main'。
4. 应看到两次计算：`multiply(12, 3) → 36`、`add(36, 8) → 44`。本模式不请求模型，不读取 QUESTION。

## 接入模型时

在 Run → Edit Configurations 的 Environment variables 填写：

| 名称 | 填什么 |
| --- | --- |
| `LLM_API_KEY` | 自己的 Key，留在本机 |
| `LLM_BASE_URL` | 服务商给出的兼容 API 入口 |
| `LLM_MODEL` | 当前 Key 实际可用的模型名 |
| `LLM_API_PROTOCOL` | 默认 `chat`；按服务文档选择 |

脚本选择本目录 `main.py`，工作目录选择本目录，解释器用上面的 Python。

把 MODE 改为 `model`：发送一次模型请求，观察回答；改为 `agent`：允许模型使用加法/乘法工具，运行后打印消息轨迹。后两种模式访问真实服务并产生相应用量。模型须支持所用协议；agent 模式还需支持工具调用。

每次运行是一个新任务，不保留上次对话。Agent 模式一次任务可能请求模型多轮。本例尚未接入用户的真实 Qwen/HeyRoute。

## 换机器或需要独立环境时

准备 Python 3.12，在本目录执行：

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

然后在 PyCharm 选择新环境。此为 macOS/Linux 命令；当前本机无需执行。完整作者环境版本记录在上级目录的 `requirements-verified.lock.txt`。

## 读代码顺序

`main.py` 的 MODE → main() → run_local() → 两个工具函数。接着配合手册 03-01 看 settings.py / run_model()，再用 03-04、03-05 理解 run_agent()。

这一轮先观察 `subtotal` 怎样变成下一次工具调用的参数；不用一次读完所有函数。
