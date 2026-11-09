# 配套 MVP：在 PyCharm CE 里读懂一个计算助手

> 2026-11-08：按用户希望用“有充分注释的 MVP + 手册”学习的反馈新增。代码已准备；实际阅读和操作按用户反馈记录。

## 这份代码解决什么问题？

本模块要理解的是：**用户用自然语言提出要求后，模型怎样请求调用我们写的 Python 函数，程序怎样执行并把结果交回模型。** 这直接对应 LLM 应用中的工具调用与 Agent。计算只是一个结果容易检查的例子；换成天气查询、文件读取或数据库查询，仍然需要连接这几步。

例如用户问“每盒有12支笔，买3盒，又单独买8支，共多少支？”我们把乘法、加法工具交给 Agent。模型根据问题产生工具名称与参数，LangChain 执行对应函数并回填结果，模型再继续请求工具或回答。关键代码在 `run_agent()` 的 `create_agent(model=model, tools=[multiply, add], ...)` 和 `agent.invoke(...)`；它们分别负责组装流程与开始任务。

2026-11-08教学调整：用户指出单讲本地计算看不出与学习目标的关系。当前先读上面的完整用途和下文§3，再结合03-01理解模型调用；§2作为本地运行检查和按需查阅，不再逐项讲变量赋值和普通传参。`local` 的默认设置保留，方便不接模型时检查环境。

本页是现有八章的代码导读。当前只需能辨认函数调用和字典；不熟悉的语法可以结合实际语句再问。学习目标是找到程序入口、跟踪一次返回值，以及在模型接入后分清工具请求和工具执行。多轮聊天、界面、数据库和持久化留待后续需要时展开。

## 1. 在 PyCharm 中打开哪一个目录？

使用用户指定的 **PyCharm CE（社区版）**。选择 **File → Open**，打开：

```text
/Users/liujunhong/Documents/ChatGPT/用友/learning/03-llm-tools/mvp
```

这个小项目主要读两个文件：

| 文件 | 负责什么 | 什么时候看 |
| --- | --- | --- |
| `main.py` | 问题、工具、运行入口和 Agent 流程，有中文注释 | 首先看它 |
| `settings.py` | 从环境变量取得服务地址、Key 和型号，创建模型客户端 | 接模型时看 |
| `README.md` | PyCharm 操作和运行说明 | 配置时查 |
| `requirements.txt` | 两个直接依赖的版本 | 换环境时用 |

在 Python Interpreter 设置中选择已有的本机解释器：

```text
/Users/liujunhong/Documents/ChatGPT/用友/learning/03-llm-tools/.venv-verify/bin/python
```

该环境已有教材使用的依赖，可以直接复用。如果 PyCharm 没有列出它，选择添加本地解释器中的“已有环境”，定位这个可执行文件。不同版本菜单名称可能不同，核心是选对 Python 路径。本轮不需要另装包；将来要独立环境时，README 有创建步骤。

打开 `main.py`，保留 `MODE = "local"`，右键运行。先确认 Run 配置的脚本是本项目的 `main.py`，工作目录是上述 `mvp` 目录，解释器是上面的已有环境。

## 2. 先跟踪一次本地计算

第一次运行预期输出：

```text
当前运行方式：local
本地工具演示（没有请求模型）：
multiply(12, 3) → 36
add(36, 8) → 44
```

先读 `main()`：它检查 `MODE`，选择 `run_local()`。然后只看这两句：

```python
subtotal = multiply.invoke({"a": 12, "b": 3})
total = add.invoke({"a": subtotal, "b": 8})
```

`multiply` 是乘法工具，`invoke` 是执行工具的方法。参数字典中的 `a`、`b` 对应工具函数的两个参数。第一句执行 `12 * 3`，把返回值36保存到 `subtotal`；第二句把36和8交给加法工具，得到44。

函数上的 `@tool` 将普通 Python 函数包装为 LangChain 工具，整理函数名、说明和参数结构。当前仍是我们在代码中明确写好了调用次序，模型没有参与。在后面的 Agent 方式里，这些工具说明会提供给模型，工具函数体继续由本机 Python 执行。

在 `subtotal = ...` 左侧点一下打断点，选择 Debug。停住时这行尚未执行；单步执行后观察 `subtotal`，再执行下一行观察 `total`。也可在 `return a * b` 打断点，直接看到工具收到的数字。

**当前特别注意：** `local` 方式使用函数中写死的12、3、8，不读取 `QUESTION`。修改自然语言问题不会改变本地结果。这个明确的固定过程用于先看懂数据怎么传递。

## 3. 在同一文件里切换模型与 Agent

后面按需要改 `main.py` 顶部的 `MODE`，每次重新运行即可：

| MODE | 输入来自哪里 | 谁决定计算步骤 | 观察什么 |
| --- | --- | --- | --- |
| `"local"` | `run_local()` 的固定参数 | Python 代码 | 36怎样成为下一步参数 |
| `"model"` | `QUESTION` | 本次没有注册工具，模型直接回答 | messages、response.text |
| `"agent"` | `QUESTION` | 模型发出工具请求，框架执行与回填 | 工具名称、参数、返回值、最终文本 |

后两种方式先在 **Run → Edit Configurations → Environment variables** 设置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`，以及默认值为 `chat` 的 `LLM_API_PROTOCOL`。含义及排错见 [03-01 §3](01-model-call.md#3)。Key 留在本机。`settings.py` 直接读取进程环境；放一个 `.env` 文件不会自动生效。

实际服务与模型确定后，再填写对应值。运行 `model` 或 `agent` 会调用服务并产生用量；本次准备代码没有调用真实服务。

`model` 方式看 `run_model()`：创建消息列表，调用 `model.invoke(messages)`，取得 `AIMessage`。即使模型算出了44，代码也没有向它提供我们的工具。它的回答和本机工具执行记录是两种不同的证据。

`agent` 方式看 `run_agent()`：`create_agent` 将模型、工具、提示词组装起来，`agent.invoke` 开始本次任务。典型路径是：

```text
用户问题
  → 模型请求 multiply(a=12, b=3)
  → Python 执行工具，结果36回填给模型
  → 模型请求 add(a=36, b=8)
  → Python 执行工具，结果44回填给模型
  → 模型生成最终回答
```

代码会在任务完成后打印消息记录。模型实际请求的参数、顺序与措辞需以运行结果为准；提示词不会强制每个模型采用同一条路线。打印的 `[模型请求工具]` 表示生成了调用指令，`[工具返回]` 才是执行后回填的消息。每次点击运行都开始新任务，不保留上一次对话。

## 4. 代码与手册怎样配合？

不必现在读懂 Agent 的全部实现。先运行并看懂第一个数据流，再用章节逐步补足机制。

| 当前关注点 | 对应代码 | 对应手册 |
| --- | --- | --- |
| 调用谁、发什么、返回什么 | `settings.py`、`run_model()` | [03-01 §2–4](01-model-call.md#2) |
| 一条消息和历史消息是什么 | `HumanMessage`、`SystemMessage`、`messages` | [03-02](02-messages-context.md) |
| 输出和参数怎样成为可校验数据 | 工具的参数类型，后续结构化例子 | [03-03](03-structured-output.md) |
| 模型怎样请求工具，谁真正执行 | `@tool`、工具参数、`ToolMessage` | [03-04](04-tools-loop.md) |
| 框架怎样接管循环 | `create_agent`、`agent.invoke` | [03-05](05-agent.md) |
| 为什么会失败或多次请求 | `timeout`、`max_retries`、步数限制 | [03-06](06-runtime-debugging.md) |

本 MVP 不必装下每章所有能力。已有 `lab` 仍保留结构化输出、异步、流式和 MCP 的专门例子，需要时再对照。

## 5. 常见问题与定位

| 现象 | 原因与下一步 |
| --- | --- |
| local 模式报找不到 langchain | 文件顶部也需要导入依赖；检查选中的解释器是否为已有验证环境 |
| 改了 QUESTION，local 仍输出44 | local 使用固定参数；改它的参数，或接好服务后切换 model/agent |
| model/agent 提示缺少配置 | 检查当前运行 main 的那份 Run 配置，不只检查终端变量 |
| model 能回答，agent 返回不支持工具 | 核对具体型号与接口的工具调用支持，参见03-04 |
| 只看到当前方式，暂时没有后续输出 | Agent 轨迹是结束后打印；可在工具函数体打断点观察执行 |
| Agent 未调用工具就回答 | 查看消息记录和模型能力；提示词是引导，需用实际调用验证 |

保留完整异常是为了能定位文件、行号与失败原因。401/403、404和参数不支持等接入问题继续看 [03-01 §6](01-model-call.md#6)。

## 6. 一个可选的小改动

把本地例子的盒数从3改为4，先推演两次返回值，再按需运行。输入仍是每盒12支、额外8支；只改 `run_local()` 的调用参数，不修改工具函数。

??? note "参考结果与原因"
    将 `multiply.invoke` 的 `b` 从3改成4，第一次返回48。第二次调用读取新的 `subtotal`，所以返回56；无需把第二次参数另写成48。`run_local()` 中第一条打印的标签也要同步改为 `multiply(12, 4)`，使展示与实际输入一致。

## 本页回顾与阅读位置

核心是追踪“参数进入函数，返回值进入下一步”。模型接入后，增加了由模型生成工具名称和参数的过程；计算函数仍然在 Python 中执行。

- [ ] 找到 MODE、main 和 run_local 的关系。
- [ ] 解释 subtotal 怎样传给 add。
- [ ] 接入后能从消息记录区分模型回答与工具执行。

当前按用户最新要求回到 [03-01](01-model-call.md)，以快速跑通一次模型调用为目标。本 MVP 作为配套代码使用：将 `MODE` 改为 `"model"`，阅读 `settings.py` 和 `run_model()`。用户已表示理解模型与工具协作的总体流程，不重复讲解；本页各节保留供按需查阅。

## 答疑与来源

2026-11-08：用户希望用注释充分的 PyCharm MVP 配合手册，已增加本入口和代码；没有因此记录用户已掌握。

实现参考 [LangChain 官方 Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)；IDE 字段参考 [PyCharm Python 运行配置](https://www.jetbrains.com/help/pycharm/run-debug-configuration-python.html)。本机使用既有 Python3.12.14、LangChain1.4.9、langchain-openai1.7.4；作者核对与真实模型接入情况分别记录于模块的 VERIFICATION.md 和 PROGRESS.md。
