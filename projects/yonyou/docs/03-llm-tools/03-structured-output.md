# 03-03 把模型回答变成可校验的数据

> 教材已准备，2026-11-08。先理解格式、语义和事实三层检查；代码可以先读后跑。

## 本章问题、目标与前置

模型说“去查C001吧”，程序怎样可靠地知道要调用什么？本章把问句转换成查询意图，解释JSON、Pydantic和结构化输出如何合作。读完应能看懂字段定义、模型提取与业务执行三段，并指出校验能拦住哪些问题。

前置为[消息与模板](02-messages-context.md)和01的类型/参数知识。约35分钟。此处演示“模型提取、应用决定执行”，下一章再讲模型原生工具调用。

## 1. 先确定我们希望得到什么

对“查C001的欠款”，需要的是动作与客户编号，而不是模型填写一个余额。约定如下：

```json
{"action": "query_balance", "customer_id": "C001"}
```

对“查那个客户”，允许：

```json
{"action": "clarify", "customer_id": null}
```

金额继续由业务数据计算。输入问题、提取结果、查询结果是三个不同对象，分开后更容易定位错误：编号抽错是提取问题，金额算错是业务问题。

## 2. JSON语法、字段约束与业务事实

JSON只规定数据怎样表达，例如对象、字符串、数字和null。`{"customer_id": "火星"}`完全可以是合法JSON，但不符合本例客户编号格式。`C999`符合格式，却可能在账目里不存在。

| 检查层 | 本例问题 | 谁负责 |
| --- | --- | --- |
| 可解析 | 是合法JSON吗？ | JSON解析器/协议解析 |
| 结构与字段 | action属于允许值吗，编号格式对吗？ | Schema和Pydantic |
| 业务条件 | query_balance时是否有编号？客户存在吗？ | 业务函数与数据 |
| 结果解释 | not_found是否被错说成零？ | 应用输出与验证 |

Schema是“数据允许长什么样”的规则描述。Pydantic模型是用Python定义并验证这种结构的方式。格式正确会让后面的程序更容易处理，但它不能查询事实。

## 3. 最小结构和执行函数

配套`intent.py`完整内容：

```python
"""格式校验与业务执行是两步。"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from business import get_balance


class QueryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["query_balance", "clarify"]
    customer_id: str | None = Field(default=None, pattern=r"^C\d{3}$")


def execute_intent(intent: QueryIntent) -> dict:
    if intent.action == "clarify":
        return {"status": "need_clarification", "question": "请提供明确的客户编号。"}
    if intent.customer_id is None:
        raise ValueError("查询余额需要客户编号；应先澄清")
    return get_balance(intent.customer_id)
```

`Literal`把action限制为两个字符串。`str | None`允许编号暂时为空；`pattern`约束非空编号是C加三位数字。`extra="forbid"`拒绝额外字段，例如模型擅自返回amount；这是我们选择的协议规则。

字段校验后仍有执行条件：action是query_balance却没有编号时，`execute_intent`拒绝查询；action是clarify时先返回澄清问题。这个版本把跨字段业务判断放在执行函数里，方便你看到它发生在哪里。以后可以重构为模型级校验，但不能把这层判断删掉。

`get_balance`读取的是合成样本，不访问真实ERP。C001=20000−7200=12800，C002余额为0；客户不存在返回not_found。每个成功结果包含币种、日期和来源。

### 3.1 `Field` 是什么意思？先用会议提取看写法

先明确为什么要定义这个结构。假设程序收到“会议在北京举行，共有8人参加”，希望把信息放入会议登记表，后面能分别读取地点与人数。我们先约定表中有两个栏目：location存地点，people存人数；此时尚未填写具体内容。`MeetingInfo` 就相当于这张表的填写规格。

| 栏目 | 要填什么 | 填写要求 |
| --- | --- | --- |
| location | 会议地点 | 字符串 |
| people | 参会人数 | 整数，至少1人 |

下面的类把这张规格表写成Python能使用的定义。字段名称供后续代码访问，类型和Field提供说明及校验要求；实际的“北京”和8来自本次输入的提取结果。

```python
from pydantic import BaseModel, Field

class MeetingInfo(BaseModel):
    location: str = Field(description="会议地点")
    people: int = Field(ge=1, description="参会人数")
```

`MeetingInfo` 定义要接收的数据结构。`location: str` 声明地点是字符串，`people: int` 声明人数按整数校验。`Field(...)` 给字段补充说明和规则；`description` 说明字段含义，`ge=1` 表示值必须大于等于1。这些是字段定义，尚未把北京或8填进去，`Field(...)` 也不是字段的实际取值。

单写 `location: str` 也能定义字符串字段；这里加 `description`，是为了让生成的结构描述说明该字段要提取什么。`description` 不自动检查“地点是否真实”；`ge` 才是可执行的数值约束。来源：[Pydantic字段](https://docs.pydantic.dev/latest/concepts/fields/)。

用户问“等于是固定提取哪几个要素”：对，这个结构先规定要提取地点和人数，Field再为每个要素提供说明或约束。可读完整文件已放在 `learning/03-llm-tools/lab/03_meeting_extract.py`，从字段定义、创建客户端、配置结构化返回一直到读取结果均有注释。它沿用lab依赖，运行需在本机设置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL，并使用支持所用结构化输出方式的入口；阅读无需先运行。

## 4. 模型怎样输出这个结构？

配套`03_structured.py`：

```python
from intent import QueryIntent, execute_intent
from model_config import make_model


def main():
    model = make_model()
    extractor = model.with_structured_output(QueryIntent, method="function_calling")
    intent = extractor.invoke(
        "提取查询意图。客户编号不明确就选clarify，不能猜编号。问题：查C001的欠款。"
    )
    print("结构化意图：", intent.model_dump())
    print("业务执行结果：", execute_intent(intent))


if __name__ == "__main__":
    main()
```

`with_structured_output(QueryIntent, method="function_calling")`创建一个包装后的模型调用组件，要求返回符合QueryIntent的对象。这里明确选择工具调用方式来表达结构，不依赖服务商原生JSON Schema模式。

这仍需要所选模型和入口支持工具调用。若返回ValidationError，应检查原问题、Schema和实际输出；若服务报“不支持tools”，应核对接入能力，不把字段改松来掩盖协议问题。某些原生结构模式更严格，属于后续按模型选择的方案。

`extractor.invoke`发请求并解析结果，得到QueryIntent对象；`model_dump()`转成Python字典方便显示。随后`execute_intent`才处理业务。注意本章用于约束输出的“形式工具”不等于已经运行真实余额查询；真正查询发生在你调用业务函数时。

### 4.1 `with_structured_output` 和 `result.location` 连起来怎样理解？

以上面的 `MeetingInfo` 为例，假设 `llm` 是已配置好并支持所用结构化方式的客户端：

```python
extractor = llm.with_structured_output(MeetingInfo)
result = extractor.invoke("提取会议信息：会议在北京举行，共有8人参加。")
print(result.location)
print(result.people)
```

第一行创建一个使用 `MeetingInfo` 输出结构的调用组件，还没有发出提取请求。第二行才调用模型，并由组件解析、校验结果。这里传入的是 Pydantic 类，使用默认返回设置，成功返回的 `result` 是该类的实例；本例预期形如 `MeetingInfo(location="北京", people=8)`。后两行读取其中两个字段，分别打印北京和8。

用登记表来对应：`MeetingInfo` 定义表有哪些栏目；`with_structured_output(MeetingInfo)` 配置接下来按这张表提取；`invoke(会议通知)` 才提供要读取的原文；`result` 是填好的一份记录。模型得到字段要求并生成提取结果，LangChain再解析、校验成Python对象，所以代码能用 `result.location` 和 `result.people` 取值。若下一次原文变成“会议在上海举行，共有12人参加”，仍用同一个结构，预期得到上海和12。无需重新定义类，也不用在字段定义中写死这些值。

`extractor` 是我们取的变量名，`MeetingInfo` 是数据结构，`result` 是本次拿到的数据。原来的 `llm` 仍可继续用于普通调用。当前先理解“定义结构→配置提取→调用→读取字段”，具体协议选择、缺字段和错误处理按后续疑问展开。

### 4.2 直接在 prompt 中要求返回这些字段可以吗？

可以。例如要求“提取location和people，只返回JSON，不要Markdown”，普通模型调用也可以完成提取。若成功返回合法JSON，应用可用 `json.loads(response.text)` 得到字典，再通过 `result["location"]` 取值。此路线完全可用；是否要用结构化封装取决于后续程序需要。

区别在于代码中的解析与检查如何安排。prompt表达输出要求，普通 `llm.invoke` 仍返回AIMessage；文字里即使要求人数至少1，也不会自动让Python拒绝0。若程序需要这项约束，要另写校验代码，或将解析后的字典交给 `MeetingInfo.model_validate(data)`。

`llm.with_structured_output(MeetingInfo)` 将结构声明用于模型请求，并组合对应的解析、Pydantic校验；默认设置下成功返回MeetingInfo对象，可直接访问字段。具体请求可能利用服务支持的结构化输出或工具调用协议，而不仅是向正文追加一句格式要求；模型/入口需支持选用方式。解析失败或不满足约束仍可能报错。Field校验不证明提取值符合原文。

因此，临时提取或已有JSON解析与校验代码时，可以继续用prompt。若希望多个调用复用同一字段规格、解析及校验，结构化封装能减少重复代码。原有instruction和few-shot仍可保留在输入中，提示词与结构定义可以一起使用。

## 5. 不调用模型也能检查这一层

如果你只想先读懂代码，可手动构造对象：

```python
from intent import QueryIntent, execute_intent

intent = QueryIntent(action="query_balance", customer_id="C001")
print(execute_intent(intent))
```

预期得到status=ok、amount=12800、currency=CNY及日期。把C001换成“客户一”，构造时就触发字段校验；换成C999，构造成功、执行返回not_found；把编号换成None且action仍为query_balance，进入执行函数后触发ValueError。三种失败的层次不同。

金额采用整数元只是为了简化读代码；真实ERP金额精度、汇率和核销口径要按其接口设计，不能从这个例子外推。

## 6. 看AI代码时，沿三条线核查

先看Schema是否包含完成任务所需信息，是否让模型猜了不应该生成的事实；再看解析之后有没有继续做业务校验；最后看失败怎样向用户表达。

例如AI写出`amount = result.get("amount", 0)`，会在not_found没有amount时静默得到0。程序没有崩溃，但结论错了。正确路线先判断status，只有ok才读amount。

另外，Pydantic默认对部分类型允许转换，不要把“有类型注解”当成所有字段都严格不转换。本例编号有明确模式、动作有明确枚举；新增字段时要按要求选择strict约束，并核对边界输入。

若需求是“输出JSON”，还应问清后面的消费者需要哪些字段、空值怎么表示、允许哪些动作和错误状态。这样才能指导AI写出可维护的结构，而不只是一句“返回标准JSON”。

## 7. 操作步骤与常见失败

1. 先在PyCharm读`intent.py`，分别找到数据定义与执行条件。
2. 可运行§5手动例子或`07_review.py`，不需要Key。
3. 准备模型后运行`03_structured.py`，在intent产生后打断点，核对其类型和字段。
4. 依次用明确编号、无编号、格式错误编号提问；模型选择可能变化，记录实际输出，不把一次样例当成所有输入都会正确。

如果遇到带Markdown围栏的JSON导致解析失败，先检查是否实际走了结构化接口。直接从文本截取一对大括号可能吞掉多余内容，不应成为默认修复。

## 8. 可选练习

A. C999通过模式校验，能证明什么？B. 为什么不让模型一并生成amount？C. AI删了execute_intent里的None检查，程序会缺少哪项保证？

??? note "参考答案与推理"
    A：只证明编号形状符合要求，存在性需查数据。B：没有账目时生成金额会引入无依据事实，金额应由查询和口径计算。C：字段允许空值是为了澄清场景，查询动作本身仍需要编号；删掉检查会把不完整意图送进业务流程。

## 本章回顾与检查清单

结构化输出把语言变成可检查对象；业务函数把合格输入变成带状态的数据。两者之间的条件判断必须能在代码里找到。

- [ ] 能读懂Literal、可空字段、pattern与额外字段规则。
- [ ] 能区分解析错误、字段错误和客户不存在。
- [ ] 知道结构化提取之后哪一行才执行查询。

## 阅读中产生的答疑

2026-11-08：用户已表示理解消息历史，要求放慢节奏，当前只讲到结构化输出，不进入工具调用。`Field` 的会议例子见§3.1，`with_structured_output` 与字段访问见§4.1；`prompt | llm` 的展开执行见03-02 §4.1。

## 来源与后续

核对日期2026-11-08：[模型结构化输出](https://docs.langchain.com/oss/python/langchain/models)、[Agent结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)、[Pydantic模型](https://docs.pydantic.dev/latest/concepts/models/)。本章用模型级包装；Agent的`structured_response`是另一种返回位置，不混用字段。下一章：[工具调用循环](04-tools-loop.md)；[目录](index.md)。
