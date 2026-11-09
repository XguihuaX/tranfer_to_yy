# 03-01 从业务问题到第一次模型调用

> 教材已准备，2026-11-08。可以先阅读和推演；操作按步骤选做。用户阅读、练习和掌握情况单独记录。

**当前学习方式：** 先用下面的总览把本章涉及的对象、联系、代码和学习目标完整串起来，再实操。不将“快速上手”理解成省略概念直接填配置。配套 [MVP](mvp-walkthrough.md) 留作代码参照，本章仍围绕一次模型调用展开。

## 本章问题、目标与前置

你拿到一段AI写出的LangChain代码，怎样判断它在调用谁、发了什么，以及返回了什么？本章建立整条路线，再给PyCharm操作步骤。读完应能指出模型、服务地址、凭据、消息和返回值的位置，说明一次模型回答能证明什么，并能按说明运行最小文件。

前置是[01的HTTP与JSON](../01-python-api/06-http-and-json.md)及[02的解释器与环境变量](../02-deployment/05-environment-and-permissions.md)。约30–45分钟，可分次读。工具执行放在03-04，本章模型还不能查到业务数据。

## 本章总览：LLM 调用与 LangChain 怎样连起来

本章完成一件事：写一个 Python 程序，把消息发给已经部署好的大语言模型，再取得回答。以“把一句中文翻译成英文”为例，输入是中文，模型在服务端生成翻译，我们的程序接收并展示文本。这就是本章所说的模型调用。

LLM 是大语言模型，Qwen 是模型系列的例子。模型服务把运行中的模型通过 API 提供给程序使用；API 就是程序访问服务的接口。调用时，服务地址决定请求送到哪里，API Key 用于认证，模型名决定使用哪个可用型号。模型可以部署在本机或服务器，本章使用远程服务。

LangChain 是用于编写 LLM 应用的框架，提供模型调用、消息、工具和 Agent 等组件。本章先使用它的模型客户端和消息对象。直接发送 HTTP 请求或使用服务商 SDK 也能调用模型；SDK 是服务商提供的客户端开发包，帮助处理请求与响应。选用 LangChain，是为了后续仍能用同一套模型和消息接口接工具、结构化输出与 Agent。单次调用已经可以使用 LangChain，无需先创建 Agent。

`langchain-openai` 是 LangChain 的一个模型集成包，`ChatOpenAI` 是其中用来创建客户端的类。它将 LangChain 消息转换为相应 API 请求，并把响应整理成消息对象。服务提供兼容的标准接口时，可通过 `base_url` 指向该服务；使用这个类不等于模型必须是 GPT。PyCharm CE 则负责编辑代码、选择 Python 解释器、启动和调试脚本。

```text
PyCharm CE 启动 Python 脚本
    → 脚本组织消息，调用 LangChain 模型客户端
    → 客户端向指定 API 服务发请求
    → 服务运行所选模型，返回生成结果
    → 客户端把结果整理为 AIMessage，脚本取出文本
```

把全过程放进一个文件，核心代码如下。这里是阅读示例，地址、Key和型号均为占位值，不能原样请求真实模型；实际项目从本机环境变量读取它们，见§3。

```python
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage

# 1. 创建客户端，说明请求发到哪里、用什么凭据、选哪个模型。
llm = ChatOpenAI(
    base_url="https://example.invalid/v1",
    api_key="本机填写的API_KEY",
    model="服务商提供的模型名",
)

# 2. 组织消息：应用规则 + 当前输入。
messages = [
    SystemMessage(content="你是翻译助手，只输出英文翻译。"),
    HumanMessage(content="今天下午三点开会。"),
]

# 3. 发出请求并等待；拿到的是包含回答信息的消息对象。
response = llm.invoke(messages)

# 4. 从消息对象中取出文本。
print(response.text)
```

这里的 `llm` 变量保存模型客户端，模型权重没有被加载到这个变量里。创建客户端准备连接配置；执行 `invoke` 才开始本次模型请求。`SystemMessage` 放应用给模型的规则，`HumanMessage` 放用户输入；返回的 `AIMessage` 可以包含正文及用量等信息，`response.text` 取出可读文本。示例可能输出 `The meeting is at three this afternoon.`，措辞由实际模型决定。

本章学习内容按四件事组织：

| 要学会的事情 | 对应位置 | 可观察的结果 |
| --- | --- | --- |
| 分清模型、服务、框架、客户端与 IDE | 本总览及§2 | 能解释每个对象在一次调用中做什么 |
| 看懂连接配置 | §3 | 能指出地址、Key、模型名各控制什么 |
| 看懂一次输入和输出 | §4 | 能找到消息、实际请求语句、回答正文 |
| 在 PyCharm 中运行并定位基本错误 | §5–6 | 能核对解释器/运行配置，区分缺包、缺配置和服务返回错误 |

后续03-02展开消息历史与上下文，03-03讲结构化输出，03-04/05讲工具与 Agent。本章先建立上面的完整调用路线；无需此时逐个掌握重试、异步或 Agent 的实现细节。

## 1. 先看为什么“能回答”还不够

用户问“北京现在多少度”，模型能生成一句回答，但当前天气需要从天气服务获取。这里有两件事：调用模型得到回答，以及让程序取得回答所需的数据。先分清它们，后面才容易理解工具调用。

配套代码用“C001还欠多少钱”作连续例子：本地样本记录的余额是12800元。你只需把它看成按编号读取一个数值，无需先学应收或核销。模型没有自动访问这份记录，只有实际读取后才有查询依据。这与查实时天气是相同的机制。

第一步先接通模型，是为了学清通信与代码。后面再把业务函数接成工具。这样看到错误时，能判断是“模型没连上”，还是“工具没执行”，还是“结果解释错了”。

## 2. 这些名称分别属于哪一层？

| 对象 | 负责什么 | 本模块的位置 |
| --- | --- | --- |
| Qwen等模型 | 根据输入生成回答或工具调用请求 | 服务商提供的模型 |
| 服务商或中转 | 提供模型API、认证、路由与计费 | 你已有的Qwen入口或HeyRoute |
| SDK/模型集成 | 把Python对象转换成API请求，再解析响应 | `langchain-openai`中的`ChatOpenAI` |
| LangChain | 消息、模型、工具与Agent等应用组件 | 03主线框架 |
| LangGraph | 管理显式状态与任务流程 | 05深入；LangChain Agent内部使用它 |
| PyCharm | 编辑、运行、观察变量、调试 | 开发环境 |
| FastAPI | 对外提供HTTP服务 | 后面需要接口时复用01；本章脚本不依赖它 |

模型名是请求参数，Python包名是你安装的程序库。使用`ChatOpenAI`不等于一定访问OpenAI官网：它可以对接兼容的标准接口。本模块只使用共同的消息、文本、工具调用能力；第三方专有字段可能不被保留，需要时再选专属集成。

2026-11-09答疑：当前示例里的 `ChatOpenAI` 连接OpenAI格式的兼容接口；LangChain本身也提供其他服务的集成，并不要求所有服务都采用OpenAI协议。服务支持普通聊天，不自动意味着同一入口支持前面用到的结构化输出或工具调用；需按具体型号和接口支持选择。这决定能否直接沿用 `with_structured_output` 等写法。来源：[ChatOpenAI集成](https://docs.langchain.com/oss/python/integrations/chat/openai)、[模型集成说明](https://docs.langchain.com/oss/python/langchain/models)。

LiteLLM也能统一调用模型，但本次先用LangChain自己的集成，减少一层转换。DSH与养鱼已延后，不是运行本章的条件。

### 2.1 LiteLLM在这里是什么位置？

LiteLLM提供统一的多服务模型调用接口，也可以作为独立网关运行。当前教材的路线是 `应用 → LangChain ChatOpenAI → 模型服务`，因此没有使用LiteLLM。若使用LiteLLM的Python SDK，路线可以是 `应用 → LiteLLM completion → 模型服务`；两种都能完成模型请求。LangChain还组织模板、解析器和工具流程，和LiteLLM有部分能力重叠，不必把两者都加进每个应用。

下面是使用LiteLLM访问OpenAI兼容入口的阅读示例，沿用本地三个环境变量；本次未安装LiteLLM或请求真实服务，具体可用型号由服务决定：

```python
import os
from litellm import completion

response = completion(
    model="openai/" + os.environ["LLM_MODEL"],
    api_base=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    messages=[{"role": "user", "content": "把今天下午开会翻译成英文。"}],
)
print(response.choices[0].message.content)
```

`openai/`选择兼容接口的调用方式，后半部分才是实际模型名；不表示实际模型必须是GPT。本例地址参数为 `api_base`，和前面ChatOpenAI示例中的 `base_url` 名称不同。LiteLLM这里返回兼容OpenAI的响应结构，因此正文读取方式也和 `AIMessage.text` 不同。

若将LiteLLM部署成网关，则可形成 `LangChain ChatOpenAI → LiteLLM网关 → 多个模型服务`，客户端填网关地址、网关凭据和配置的模型别名。网关可用于集中管理模型接入、用量和路由；这是部署选择，当前只理解它的位置，不需要搭建。SDK可以直接用，无需先部署网关。

用户追问“两者是否实际上没区别”：两者在调用多种模型服务这一部分有重叠，但常用抽象与使用重点不同。LiteLLM SDK/Router/网关侧重统一模型接入和请求管理；LangChain侧重用消息、提示词模板、解析器、工具和Agent等组件组织应用。前面 `ChatOpenAI(...).invoke(...)` 与 `completion(...)` 都能承担模型请求；`ChatPromptTemplate`、`prompt | llm`、`with_structured_output(MeetingInfo)` 则是LangChain这套组件的写法，不能仅替换import就当成LiteLLM接口使用。

若自己已有prompt组织、函数路由、JSON解析和字段校验代码，使用LiteLLM处理模型调用即可保留这些逻辑。若希望使用现成组件连接这些步骤，可以用LangChain。这是选择代码组织方式，并非使用LangChain才可以实现对应功能。二者也能通过网关或适配集成配合使用；实际功能仍取决于具体模型与服务支持。

来源：[LiteLLM入门](https://docs.litellm.ai/docs/)、[OpenAI兼容入口](https://docs.litellm.ai/docs/providers/openai_compatible)。理解后回到[03-04 §3](04-tools-loop.md#3-langchain)，看已有工具怎样提供给模型。

## 3. 读代码先找这五个位置

先确认入口；再找配置从哪里来；随后追踪传入消息；接着找真正发请求的语句；最后看结果怎样被使用。不要从第一行开始背每个参数。

本章配置集中在`model_config.py`：

```python
"""唯一的模型接入位置；导入本文件不会发起请求。"""
import os

from langchain_openai import ChatOpenAI


def make_model() -> ChatOpenAI:
    required = ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise ValueError("缺少运行配置：" + ", ".join(missing))
    protocol = os.environ.get("LLM_API_PROTOCOL", "chat")
    if protocol not in {"chat", "responses"}:
        raise ValueError("LLM_API_PROTOCOL只能是chat或responses")
    return ChatOpenAI(
        model=os.environ["LLM_MODEL"],
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
        use_responses_api=(protocol == "responses"),
        timeout=15.0,
        max_retries=1,
        max_tokens=1024,
        http_socket_options=(),
    )
```

`make_model`是工厂函数：调用它得到一个模型客户端对象。`required`列出必须配置的三个名称；`missing`逐项读取当前进程环境，缺失就在发请求之前报错。`os.environ`读取的是这个Python进程继承的环境，不会自动读取某个`.env`文件。

`model`选择服务上实际可用的型号，`base_url`决定请求送到哪个服务入口，`api_key`用于认证。三者必须一起核对；模型名正确但地址/Key所属分组不匹配仍可能失败。

`LLM_API_PROTOCOL`区分Chat Completions与Responses两种API格式；它们都能传模型请求，但字段与响应形状不同。示例默认`chat`；若服务文档要求Responses，选`responses`，不是把协议当成模型名称。切换协议后工具和结构化输出也要逐项验证。

`timeout=15`约束底层请求等待，`max_retries=1`表示初始尝试失败后至多再试一次，`max_tokens=1024`限制本例请求的生成预算。它们不是整个Agent任务的总时间/总费用上限。03-06解释这些限制如何叠加。这里没有设置temperature，避免把不支持该参数的模型当成通用情形。`http_socket_options=()`保留HTTPX默认代理识别，避免该版本底层连接选项改变代理路径；它不属于业务逻辑，连接有问题时再核对代理和服务地址。

## 4. 最小调用怎样走完？

```python
from langchain.messages import HumanMessage, SystemMessage

from model_config import make_model


def main():
    model = make_model()
    messages = [
        SystemMessage(content="你是应收查询助手。没有查询结果时，不编造客户余额。"),
        HumanMessage(content="客户C001还欠多少钱？"),
    ]
    response = model.invoke(messages)
    print(response.text)
    print("本次用量：", response.usage_metadata)


if __name__ == "__main__":
    main()
```

`main()`先调用配置函数。`SystemMessage`表达应用规则；`HumanMessage`表达当前问题。列表顺序就是送进本次请求的消息顺序。`model.invoke(messages)`才是模型请求发生的位置，返回`AIMessage`对象，而不是直接返回一个字符串。

`response.text`取可读文本。`response.content`还可能包含内容块；`usage_metadata`是集成规范化后的用量字段，服务未提供时可能为空。打印出回答表示调用取得了响应，不表示它查过账。预期是说明缺少数据或需要查询；不同模型措辞可以不同，如果它编造金额，正是下一步需要纠正的行为。

`if __name__ == "__main__"`使你直接运行文件时执行main，其他文件导入它时不自动发请求。这对于读懂AI写出的多文件程序很有用。

## 5. 用PyCharm操作，需要哪些步骤？

先读完整流程，需要时再做。配套目录是项目内的`learning/03-llm-tools/lab/`，后面各章复用它。

1. 用PyCharm打开这个lab目录，或在已有项目中定位它。创建Python运行环境时选择Python3.12；本机文档环境的3.12.14已可用。此前默认3.14存在venv问题，具体情况见02-05。
2. 为lab创建独立`.venv`，选择它作为Project Interpreter。以下Mac命令提供可复现方式；工作目录为lab，先确认创建成功，再安装依赖。

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/03-llm-tools/lab"
"/Users/liujunhong/Documents/ChatGPT/用友/.venv-docs/bin/python" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

3. 在`Run → Edit Configurations`选择Python配置，脚本设为`01_call.py`，工作目录设为lab，解释器选lab的`.venv/bin/python`。不同PyCharm版本按钮位置可能不同，核对这三个字段即可。
4. 在该运行配置的Environment variables中加入`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`及`LLM_API_PROTOCOL`。Key只在本机填写。`.env.example`用于说明字段，不能把它存在目录里就当成已加载。
5. 先运行`07_review.py`检查本地业务例子，再运行`01_call.py`观察模型响应。前者无需Key，后者会产生服务商调用和用量。
6. 在`model.invoke`前打一处断点，用Debug运行，观察messages；执行完这行，再观察response的类型、正文和用量。单步进入第三方库不是当前必需。

HeyRoute的兼容地址为`https://heyroute.ai/v1`，型号以Key可用清单为准；Qwen按实际地域、业务空间与官方说明填写地址和模型名，不照搬中转配置。API兼容不表示每个模型都支持工具、结构化输出或相同参数。

**Windows cmd补充：**解释器通常为`.venv\Scripts\python.exe`，终端环境变量写`set LLM_MODEL=...`；PyCharm运行配置字段的含义相同。终端里设置的变量不一定进入已经启动的Run配置，优先核对实际运行配置。Mac步骤已做作者环境核对，Windows未实机执行。

## 6. 从现象定位到哪一层

| 现象 | 先检查什么 |
| --- | --- |
| 缺少运行配置 | 这份Run配置是否真的设置了变量 |
| ModuleNotFoundError | 当前解释器与安装依赖的解释器是否相同 |
| 401/403 | Key、所属地域/分组、权限与地址 |
| 404或返回HTML | base_url是否正确，是否缺少或重复`/v1`，模型名是否可用 |
| 400不支持参数 | 协议、具体模型和不支持的选项 |
| 请求成功却编余额 | 输入没提供数据，代码也没有查询步骤 |

配置错误不需要反复改提示词；提示词也不能修复认证问题。

## 7. 可选练习：读懂AI写出的修改

A. AI把`base_url`删掉了，会影响哪一步？B. 为什么先创建model对象不会得到余额？C. 运行返回“C001欠12800元”，要再看到什么才能确认它来自账目？

??? note "参考答案与推理"
    A：可能改为集成默认地址，模型请求目的地会变化；应保留已确认入口。B：客户端尚未发请求，更没执行业务查询。C：需要工具/业务函数的实际执行结果与数据口径，核对customer_id、金额、币种和日期；只看自然语言回答不足以确认来源。

## 本章回顾与检查清单

一次调用由运行环境提供配置，代码构造消息，模型集成发出请求，再把响应交回应用。框架减少协议细节，但业务数据不会自动出现。

- [ ] 能找到配置、消息、请求和结果使用的位置。
- [ ] 知道PyCharm解释器、脚本、目录、环境变量分别控制什么。
- [ ] 能解释调用成功与查账成功的关系。

## 阅读中产生的答疑

2026-11-08：用户要求以注释代码配合手册，但明确反馈，拆讲基础传参、反复复述 Agent 流程，以及直接跳到配置都没有帮助建立本章认识。最新安排是先读本章总览，一次讲清 LLM、服务、LangChain、客户端、消息和执行过程，再对照§3–5实际运行；MVP只作配套代码。此前对总体流程表示熟悉，不推断成已掌握本章。

## 来源与后续

核对日期2026-11-08：[LangChain模型](https://docs.langchain.com/oss/python/langchain/models)、[ChatOpenAI集成](https://docs.langchain.com/oss/python/integrations/chat/openai)、[PyCharm运行配置](https://www.jetbrains.com/help/pycharm/run-debug-configuration.html)、[Qwen兼容接口](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)、[HeyRoute SDK说明](https://heyroute.ai/help?collection=developers&page=sdk-quickstart)。代码版本与作者验证范围见[模块目录](index.md)。下一章：[消息、提示词与上下文](02-messages-context.md)。
