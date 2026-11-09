# 03-02 模型收到的上下文是什么？

> 教材已准备，2026-11-08。重点是消息怎样组织、代码怎样传递信息；可以手动推演，不必立即调用模型。

## 本章问题、目标与前置

为什么界面上看起来“聊了两轮”，模型却不知道上一轮内容？本章说明消息角色、历史、提示词模板和Token预算。读完应能画出本次请求里实际包含的信息，并读懂`prompt | model | parser`。前置为[第一次调用](01-model-call.md)，约30–40分钟。长期记忆与跨会话恢复留到05；RAG数据检索在04。

## 1. 聊天框中的历史与API请求中的历史

你先说“我要查C001”，再问“它还欠多少”。人会沿用上文，但独立API调用只看你传入的内容。如果第二次只传“它还欠多少”，应用没有把C001带过去，模型就缺少指代依据。

本模块显式维护消息列表。列表是应用内存中的Python对象，进程退出就丢失；客户端对象通常不等于一个自动保存所有对话的会话。某些服务支持服务端会话状态，但要按其接口管理，本例没有开启。

## 2. 四类消息怎样协作

| 类型 | 谁提供、起什么作用 | 示例 |
| --- | --- | --- |
| SystemMessage | 应用规则 | 金额必须来自查询结果 |
| HumanMessage | 用户问题或补充 | 我要查C001 |
| AIMessage | 模型返回，可能是正文或工具请求 | 提出lookup_balance调用 |
| ToolMessage | 应用把工具执行结果交回模型 | C001，12800 CNY |

角色是通信中的结构信息，不是靠正文开头写“系统：”得到的。用户粘贴的文档里即使有“忽略规则”，仍是用户提供的资料；工具返回的客户备注也仍是数据。不要因为其中包含命令式文字，就把它提升为应用规则。

SystemMessage为模型提供行为约束，实际权限仍要由工具端和后端执行。模型是否遵循指令，需要通过具体输入验证。

## 3. 完整例子：把上一轮带回来

配套`02_messages.py`先演示两轮历史，再演示模板。运行条件与01相同，真实运行会调用模型三次。

```python
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from model_config import make_model


def main():
    model = make_model()
    history = [SystemMessage(content="你是查询助手，只根据给定信息回答。")]
    history.append(HumanMessage(content="我接下来要查的客户编号是C001。"))
    first = model.invoke(history)
    history.append(first)
    history.append(HumanMessage(content="我刚才说的客户编号是什么？"))
    print(model.invoke(history).text)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "你负责把提问改写清楚，不查询或猜测余额。"),
        ("human", "把这句话改写成明确查询：{question}"),
    ])
    chain = prompt | model | StrOutputParser()
    print(chain.invoke({"question": "帮我看一下C001的欠款"}))


if __name__ == "__main__":
    main()
```

第一次invoke时，history中有系统规则与“C001”。返回的first要追加到history；再追加第二个问题。第二次请求因此包含四条消息：规则→第一次问题→第一次回答→第二次问题。

如果AI写出的代码忘了`history.append(first)`，上一轮用户信息仍可能在，但对话顺序不完整；如果它每次重建只有当前问题的列表，上轮编号就丢了。调试时直接查看列表内容，比猜测“模型记性不好”更快。

这里第二轮只验证客户编号能否延续，没有查余额。历史里曾出现某个金额也不表示它仍然有效：数据有截止时间，后续真实查账仍需查询工具。

## 4. 提示词模板与`|`各做什么？

`ChatPromptTemplate`保留固定的应用表达，把变化的位置写为`{question}`。调用时传入字典，框架把question填进去，再形成消息。模板帮助保持输入一致，不负责从数据库取数据。

`prompt | model | StrOutputParser()`称为可运行组件的组合。它依次把前一步的输出交给后一步：

```text
{"question": "帮我看一下C001的欠款"}
        ↓ 模板填入question
消息列表
        ↓ 模型调用
AIMessage
        ↓ 字符串解析器
字符串
```

`|`在这里调用LangChain组件定义的组合行为，不是02的Shell管道，也不表示并行运行。`chain`创建组合，`chain.invoke(...)`才执行它。你可以不用这条简写，先分别调用模板、模型、解析器，看中间变量；理解后再读组合形式。

解析器只提取可读文本，不会证明句子正确，也不能把未经验证的金额变成数据库事实。含工具调用的AIMessage也不应直接交给字符串解析器后就结束，否则工具请求可能被丢在流程外。

### 4.1 长 prompt、instruction 和 few-shot 怎样放进模板？

`from_messages` 中每个二元组的第一项是角色，第二项是该角色消息的正文模板。正文可以是一句话，也可以是包含 instruction、要求、few-shot 的长文本。模板只填入你指定的变量，不会自动重写或拆解这些段落。

例如 `("system", "你是翻译助手，请翻译成{language}，只输出译文。")` 和 `("human", "{text}")`，调用时传 `{"language": "英文", "text": "今天下午开会。"}`，实际得到：

```text
system：你是翻译助手，请翻译成英文，只输出译文。
human：今天下午开会。
```

`chain = prompt | llm` 组装两个步骤。`chain.invoke(values)` 的数据流相当于下面的展开写法：

```python
prompt_value = prompt.invoke(values)  # 本地填变量，得到包含消息的 ChatPromptValue
response = llm.invoke(prompt_value)  # 将填好后的输入发给模型
```

如果已经有长 prompt，可以直接保留它。例如下面把翻译目标固定为英文，只有每次的输入变化；假设 `llm` 已按03-01创建：

```python
from langchain_core.prompts import ChatPromptTemplate

LONG_PROMPT = """
# Instruction
把用户输入的中文翻译成英文。

# Requirements
- 保留原文的时间、数字和语气。
- 只输出译文，不添加解释。

# Few-shot
输入：请明天上午联系我。
输出：Please contact me tomorrow morning.

输入：会议推迟了半小时。
输出：The meeting has been delayed by half an hour.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", LONG_PROMPT),
    ("human", "{text}"),
])
chain = prompt | llm
response = chain.invoke({"text": "今天下午开会。"})
```

这里仍是两条消息：一条包含完整 instruction、要求和示例，另一条是本次输入。`# Instruction`、`# Few-shot` 是正文中的标题，并非 LangChain 的特殊参数。

另一种写法是把示例组织成明确的输入/回答消息对：

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "把中文翻译成英文，只输出译文。"),
    ("human", "请明天上午联系我。"),
    ("ai", "Please contact me tomorrow morning."),
    ("human", "会议推迟了半小时。"),
    ("ai", "The meeting has been delayed by half an hour."),
    ("human", "{text}"),
])
```

这些 `ai` 消息是开发者提供的示例回答，不会因此触发额外模型请求。已有长 prompt 可先整体放入，只有需要把示例作为多条消息组织时再拆开；没有必要仅因使用 LangChain 就重写有效的提示词。

检查模板最直接的方法是先打印实际消息，无需请求模型：

```python
messages = prompt.format_messages(text="今天下午开会。")
for message in messages:
    print(message.type, message.content)
```

长 prompt 含 JSON 示例时，默认模板中的字面大括号要写成 `{{` 和 `}}`，例如 `输出示例：{{"answer": "示例"}}`；真正的变量继续写 `{text}`。通过变量值传入的文字不会再递归作为模板解析。若整段系统提示词完全固定，也可以用 `SystemMessage(content=LONG_PROMPT)` 放入 `from_messages`，此消息正文不参与变量替换，因此无需转义其原有 JSON 大括号。

作者已在现有环境验证变量替换、长文本保留与字面括号处理，无模型请求。来源：[ChatPromptTemplate 官方参考](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)。

## 5. 提示词应该表达哪些内容？

从业务任务出发，写清目标、可用信息、规则、缺信息时怎么做、输出给谁使用。例如：

```text
你负责应收查询。先确认唯一客户，再使用查询工具。
金额使用工具结果中的amount和currency，说明as_of。
多个同名客户时询问用户；not_found不能当成余额为零。
没有工具结果就说明当前无法查询。
```

这比只写“你是资深专家，务必准确”更容易检查。没有客户编号时，合理行为可以是澄清；不能用一句“自动完成”把缺失数据变出来。输出格式要求在03-03进一步变成可校验的结构。

提示词可以要求简洁说明判断依据和数据来源；检查业务过程主要看可观察的工具记录，不依赖模型输出其内部推理文本。

## 6. Token、上下文与生成长度

Token是模型处理文本的计量单位，不与汉字数、英文单词数严格一一对应。一次请求的输入包括系统规则、历史、工具描述、工具结果和当前问题；这些共同占用上下文。

上下文窗口是一次处理能容纳的信息容量；最大生成长度控制这次允许生成多少。增加输出上限不会自动扩展输入容量。具体模型如何分配输入、输出和推理预算，以服务说明为准。

历史越长不一定越好：无关旧问题会占用预算，旧金额可能混入当前回答，长工具结果也可能遮住关键字段。处理时先去掉明显无关的历史，保留身份、任务约束、关键澄清和必要结果；需要压缩时保留来源与日期。后面的记忆、检索和状态管理分别解决不同层次的问题，不把所有材料一直追加到列表。

用量字段缺失应记录“未提供”，不能记成消耗零。比较两版代码的成本时，除模型单次输出，还要数调用次数、重试次数和被传入的历史。

## 7. 操作步骤与代表性排错

1. 在PyCharm打开`02_messages.py`，先在第二次invoke前打断点。
2. 检查history的消息类型、内容与顺序，预测模型能知道哪个编号。
3. 用同一份Run配置运行；再单独观察模板的question如何替换。不要为了读模板先安装更多框架。
4. 若出现缺少question的KeyError，核对模板变量名和invoke字典；若“记不住”，核对实际发送的历史；若成本过高，检查是否每次拼入重复全文。

本例没有持久化，也没有浏览器会话。关掉程序后重跑不会自动恢复上一轮。

## 8. 可选练习

A. 第二次只传“它的编号是什么”，是否还能保证指向C001？B. 把客户备注放在SystemMessage里会带来什么问题？C. prompt/model/parser三段里，哪一步会访问模型服务？

??? note "参考答案与推理"
    A：不能，缺少指代信息，模型只能澄清或猜测。B：把外部业务数据放进规则位置，容易混淆其优先级与职责；数据应作为被处理的内容，并由后端落实权限。C：model执行时访问服务，模板在本地组织输入，解析器处理返回。

## 本章回顾与检查清单

上下文由应用选择和传递，角色表达信息职责，模板让构造过程可重复。追踪列表和中间变量，就能检查AI是否遗漏历史、混淆规则或重复传入材料。

- [ ] 能说出第二轮请求中有哪些消息。
- [ ] 能解释模板、模型、解析器和`|`。
- [ ] 能区分上下文容量、输出预算和长期记忆。

## 阅读中产生的答疑

2026-11-09：用户问Codex的agent.md是否就是prompt部分。如果指标准文件 `AGENTS.md`，它是持久保存的项目/工作指令，Codex按适用范围读取并纳入指令上下文；可以将其理解为整体prompt中的一部分。它不等于全部请求，也不负责实现工具函数。当前项目其中的“先读教材”“只维护本模块”等就是此类指令。这里是职责对应，不假定Codex内部把文件逐字装入某个LangChain SystemMessage。来源：[OpenAI官方AGENTS.md说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

2026-11-08：用户询问 `from_messages`、`prompt | llm` 和 `chain.invoke` 的具体含义，以及如何接入包含 instruction、few-shot 的长 prompt。解释与完整写法已合并到§4.1；当前返回该节查看实际消息和两种示例组织方式。

## 来源与后续

核对日期2026-11-08：[官方消息说明](https://docs.langchain.com/oss/python/langchain/messages)、[模型说明](https://docs.langchain.com/oss/python/langchain/models)。后续：[结构化输出与业务校验](03-structured-output.md)；[模块目录](index.md)。
