# 03-04 工具调用：模型提出请求以后，谁真正干活？

> 教材已准备，2026-11-08。本章的重点是执行过程，手写循环用于看清框架随后会接管的步骤。

## 本章问题、目标与前置

AI返回了`lookup_balance(C001)`，为什么账目仍没有被查询？本章把工具定义、模型请求、Python执行和结果回填连起来。读完应能找到真正执行函数的位置，解释tool_call_id的用途，检查AI代码有没有漏掉校验、执行或回填。

前置为[结构化输出](03-structured-output.md)，约40–50分钟，可先读§1–4，完整代码按需看。这里是只读合成数据；真实ERP接入与权限在04模块继续。

## 1. 先把“请求查询”和“完成查询”分开

销售输入“查C001余额”。应用把可用工具的名称、说明和参数结构交给模型。模型可能返回一个工具请求，大意是：

```json
{"name": "lookup_balance", "args": {"customer_id": "C001"}, "id": "call_demo_1"}
```

这是一份模型生成的数据。此时Python还需要找到对应函数、校验输入、执行函数、拿到结果，再发回模型。工具请求的JSON不是账目结果。

完整路线是：

```text
用户问题 + 工具描述
    → 模型返回工具请求
    → 应用按白名单找工具并校验参数
    → 执行业务函数，得到带状态的结果
    → 生成ToolMessage，关联原调用ID
    → 再调用模型，生成回答或下一次工具请求
```

你可以先把它理解为“模型提建议，程序按明确定义的入口执行”，再看每段代码。

## 2. 先认识真正的数据来源

`business.py`完整内容如下。它只处理本地合成数据，不使用模型，不需要Key。

??? note "展开完整业务文件 business.py"

    ```python
    """合成业务数据：有效应收减已核销收款；同一组织、同一币种。"""
    AS_OF = "2026-11-08"
    CUSTOMERS = {
        "C001": {"name": "海星商贸（北京）", "receivable": 20000, "settled": 7200},
        "C002": {"name": "海星商贸（上海）", "receivable": 8000, "settled": 8000},
        "C003": {"name": "星河制造", "receivable": 500, "settled": 0},
    }


    def get_balance(customer_id: str) -> dict:
        row = CUSTOMERS.get(customer_id)
        if row is None:
            return {"status": "not_found", "customer_id": customer_id}
        return {
            "status": "ok", "customer_id": customer_id, "customer_name": row["name"],
            "amount": row["receivable"] - row["settled"], "currency": "CNY",
            "as_of": AS_OF, "source": "synthetic_receivables_v1",
        }


    def search_customers(query: str) -> dict:
        query = query.strip()
        if not query:
            return {"status": "invalid_query", "matches": []}
        matches = [
            {"customer_id": cid, "name": row["name"]}
            for cid, row in CUSTOMERS.items() if query in row["name"]
        ]
        return {"status": "ok" if matches else "not_found", "matches": matches}


    if __name__ == "__main__":
        print(get_balance("C001"))
        print(get_balance("C002"))
        print(get_balance("C999"))
    ```

读这段代码只需知道：它按编号查字典，再用receivable减settled得到结果。C001=12800，C002=0，C003=500；找不到编号则返回not_found。这里重点看函数怎样接收输入和返回结果。

样本中receivable表示应收金额，settled表示已核销收款；均为同一模拟组织、同一币种CNY，日期2026-11-08，无汇兑和调整，用整数元简化。具体财务口径不作为本章学习要求。

`get_balance`先查客户是否存在；成功时返回status、客户、金额、日期和来源。缺客户时返回not_found，没有amount。这里显式保留了“客户存在但欠款为零”和“根本找不到客户”的区别。

`search_customers`供下一章按名称找编号。“海星”会匹配北京、上海两家公司，“星河”只有一个候选。名称不是天然唯一键。

## 3. 普通函数怎样变成LangChain工具？

当前按用户已熟悉prompt与function选择的基础，只补LangChain写法：`@tool`整理工具信息，`bind_tools`让模型请求携带定义，`response.tool_calls`读取返回的调用请求。先看这三处；真正执行和ToolMessage回填在§4再展开。若要对照另一种模型调用库，先看[03-01 §2.1：LiteLLM](01-model-call.md#21-litellm)。

`query_tools.py`给业务函数加上模型和框架能理解的描述：

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

from business import get_balance, search_customers


class BalanceArgs(BaseModel):
    customer_id: str = Field(pattern=r"^C\d{3}$", description="明确的客户编号，例如C001")


@tool(args_schema=BalanceArgs)
def lookup_balance(customer_id: str) -> dict:
    """按明确客户编号查询合成应收未收余额；不存在返回not_found，不得解释为零。"""
    return get_balance(customer_id)


@tool
def find_customers(query: str) -> dict:
    """按客户名称片段查候选编号；多个候选需请用户选择，不能自行猜测。"""
    return search_customers(query)
```

`@tool`是装饰器，把函数包装为工具对象。函数名、docstring和参数类型构成工具信息；`args_schema=BalanceArgs`明确输入规则。模型据此选择工具和生成参数，应用执行前再按规则验证。

`lookup_balance.invoke({"customer_id": "C001"})`是实际执行工具的入口，内部再调用get_balance。工具对象的invoke与模型对象的invoke同名，但调用对象不同，做的事也不同。

`model.bind_tools([lookup_balance])`只是让后续模型请求携带工具定义，返回一个可调用的模型包装对象。它不查询账目，也不保证模型一定调用工具。把这一步误当执行，是读AI代码时最常见的缺口之一。

工具描述要说明何时使用、需要什么输入、结果状态怎样解释。真实系统中，用户身份、组织和可见范围来自可信的应用会话及后端校验，不能让模型靠填一个user_id就获得权限。本例数据没有多租户认证实现。

### 3.1 已经会在prompt里写功能，为什么还用`langchain.tools`？

**咖啡查价的具体例子（示例价格）：**

```python
from langchain.tools import tool

def get_price(drink: str) -> int:
    """查询咖啡价格，单位是元。"""
    prices = {"美式": 15, "拿铁": 20}
    return prices[drink]

print(get_price("拿铁"))  # 普通函数，返回20

price_tool = tool(get_price)

print(price_tool.name)                         # get_price
print(price_tool.description)                  # 查询咖啡价格，单位是元。
print(price_tool.invoke({"drink": "拿铁"}))     # 仍然返回20
```

咖啡价格仍由get_price函数查询。tool(get_price)把这项功能整理成一个工具条目：名字是get_price，用途是查询咖啡价格，输入是名为drink的文字，执行入口关联原函数。框架因而可以从同一个条目取得功能说明，也可以接收参数字典来执行它。本机实际核对输出依次为20、get_price、用途说明、20，无模型请求。

先把“包装”落实到具体对象。下面不用装饰器语法，保留原函数，再创建一个新对象；可以在已有环境直接运行，无需模型或Key：

```python
from langchain.tools import tool

def count_characters(text: str) -> int:
    """统计输入文本的字符数量。"""
    return len(text)

wrapped = tool(count_characters)

print(wrapped.name)                       # count_characters
print(wrapped.description)                # 统计输入文本的字符数量。
print(wrapped.args)                       # text参数的结构描述
print(wrapped.func is count_characters)   # True，本例保存的就是原函数
print(wrapped.invoke({"text": "OpenAI"}))  # 6
```

本机核对：原函数类型为function，wrapped类型为StructuredTool，args为 `{'text': {'title': 'Text', 'type': 'string'}}`。所以“包装”在这个例子中，是创建一个StructuredTool对象，里面保留原函数，并添加名称、说明、参数结构及统一调用方法。`wrapped.invoke`处理传入的参数字典，按参数规则校验后调用原函数；真正统计字符的仍是原来的 `len(text)`。

`@tool`写在函数上方，是将同类操作写成装饰器形式。在这个简单例子中，相当于先定义函数，再执行 `count_characters = tool(count_characters)`；此后这个名字指向工具对象。初读时用wrapped这个不同变量名，更容易看清原函数与新对象。

用户熟悉的路线可以继续使用：在prompt里描述函数和选择条件，让模型输出约定格式，再由Python解析名称、参数并执行。LangChain工具封装的用途，是把函数的名称、说明、参数规则和执行入口组织成框架能处理的工具对象。

`@tool`默认从函数名、docstring和类型标注生成名称、描述和输入结构；工具对象仍关联实际Python函数，并提供参数验证与调用接口。配合 `bind_tools`，适配器将定义放入模型API的工具声明中。以OpenAI兼容接口为例，通常是与 `messages` 并列的 `tools` 请求字段，函数体不会被上传让模型自行执行。模型返回工具请求后，运行程序仍需调用真实入口；手动循环或Agent框架负责这一部分。

因此，prompt里可以写何时使用某功能，工具定义提供可用名称及参数格式，两者可以一起使用。直接写prompt并自行解析分发也可行，区别在于代码中的协议与执行接口由谁维护，不是增加一层“意图判断能力”。

Skill、MCP与tool可以同时出现：Skill通常提供任务步骤、说明和可选脚本；MCP提供发现及调用外部能力的协议；通过MCP公布的函数也可以作为模型可用工具。若应用已连接MCP工具，可由适配器转成框架工具，通常无需给远端每个函数重新写一份Python实现。已有Agent产品会提供其中的运行机制；自行编写应用时则需要代码或框架完成连接。

来源：[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)、[MCP服务能力](https://modelcontextprotocol.io/docs/learn/server-concepts)、[Agent Skills格式](https://agentskills.io/what-are-skills)。当前只解释关系，MCP传输与Skill加载的实现按后续需要展开。

2026-11-09延伸答疑：Codex的Skill采用渐进加载，开始提供名称、描述等目录信息用于选择，选中后加载SKILL.md，引用资料和脚本按需读取或执行。用户也可明确指定Skill。读取Skill正文与执行其提到的工具是两个步骤，不是把所有Skill全文和函数实现预先塞进模型输入。工具则需要名称、用途和参数定义供选择；本会话可观察到部分工具先发现接口再调用，但不据此断言所有Codex客户端都采用同一种延迟加载方式。MCP服务负责描述能力、接收调用和返回结果，其初始化也可提供服务器级instructions。官方依据：[Codex Skills加载机制](https://learn.chatgpt.com/docs/customization/overview#skills)、[Codex MCP](https://learn.chatgpt.com/docs/extend/mcp)。

**如果有多个工具：** 每个工具都需要名字、用途、参数结构和实际执行入口。已有函数时，为函数写清docstring及参数类型，再用tool包装；用 `llm.bind_tools([price_tool, stock_tool, menu_tool])` 提供工具列表。这里假设三个工具对象都已创建。模型请求会携带这些工具定义，通常不用再将完整定义复制进prompt；prompt可以保留“问价格时查询价格，问库存时查询库存”等应用规则。模型看到的是工具说明及参数结构，Python函数体留在执行端。工具很多时，全部定义也会占用输入上下文，可以先筛选当前任务相关工具，再提供那组工具的详细定义；不要求每次提供整个工具库。

**`llm_with_tools = llm.bind_tools(TOOLS)`具体做什么？** 用户已将tool理解为“包装后有固定用法”，下一步是把这些工具提供给模型。bind_tools创建一个绑定了工具定义的调用对象，保存在llm_with_tools；此行不发送请求，也不执行咖啡查询。随后 `llm_with_tools.invoke(messages)` 才把消息和这些工具的名称、说明、参数结构一起交给模型。对照本例，普通 `llm.invoke(messages)` 没有提供这三个本地工具的定义。模型不会因此自动看到所有Python函数或函数实现。`HumanMessage(content=question)`则把用户本次问题组织为用户角色消息；messages中还可以有SystemMessage和历史回复。

**绑定以后，原来的ChatOpenAI配置还在吗？** 还在。`llm = ChatOpenAI(...)`创建的客户端负责服务地址、Key、模型名、超时和重试；`llm_with_tools = llm.bind_tools(TOOLS)`建立一个使用该客户端、附带工具定义的调用对象。调用llm_with_tools时继续使用原客户端的连接配置，不需要重新填写。原变量llm也仍可用于不带这组工具定义的普通调用。可以把二者的关系理解为 `llm_with_tools → 原llm + 此次绑定的工具定义`，并没有把咖啡函数加载进模型权重。

### 3.2 收到工具请求后，怎样执行并回填？

按用户最新偏好，Field只需了解，后续可以继续采用prompt要求和程序检查，不以显式Field写法为前置。当前先理解一次工具结果回填。

沿用前面用 `@tool` 包装的 `count_characters(text: str)`。假设本轮 `response.tool_calls` 中包含名称count_characters、参数 `{"text": "OpenAI"}` 和调用ID `call_001`，需要在已有messages中保留完整模型回复，然后执行请求并添加结果消息：

```python
from langchain.messages import ToolMessage

available_tools = {"count_characters": count_characters}
messages.append(response)

for call in response.tool_calls:
    selected_tool = available_tools[call["name"]]
    tool_result = selected_tool.invoke(call["args"])
    messages.append(ToolMessage(
        content=str(tool_result),
        tool_call_id=call["id"],
    ))
```

这段是接在模型返回之后的局部代码，不是独立脚本。`response`是模型本次完整回复，`messages`是此前发送的消息列表，`count_characters`是已定义的工具。例中本机函数返回6，回填消息的正文是字符串“6”，调用ID沿用call_001，用来匹配请求与结果。这个for循环处理同一条模型回复中的各个工具请求；`selected_tool.invoke`才是真正执行本地函数的位置。

随后再调用 `next_response = llm_with_tools.invoke(messages)`，模型就能看到“问题→工具请求→工具结果”的顺序。若此次返回普通回答，就可读取正文；若仍有工具请求，继续执行与回填。完整循环和次数限制放在§4，当前不要求一次读完。

**咖啡完整脚本有没有第二轮汇总？** 有。执行当前 `response.tool_calls` 的内层for结束后，会返回外层 `for _ in range(max_rounds)` 的下一轮，再执行 `llm_with_tools.invoke(messages)`。此时messages已包含用户问题、模型的工具请求和各个ToolMessage结果。模型可以据此生成汇总回答，随后 `if not response.tool_calls: return response.text` 返回正文。两层for用途不同：外层推进模型调用轮次，内层处理同一次模型回复中的各个工具请求。执行工具那一小段单独看没有第二次模型请求，但完整脚本有。

### 3.3 完整咖啡代码 { #coffee-complete }

用户要求将三个工具合成完整代码，新增 `learning/03-llm-tools/lab/04_coffee_tools.py`。这份单文件示例不显式使用Field：普通函数→tool包装→bind_tools列表→模型返回请求→本机执行→ToolMessage回填→最终回答。每次运行处理一个问题；价格与库存均为本地示例，不连接真实店铺。

运行条件：Python3.12、lab已有requirements.txt依赖；本机设置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL。入口必须支持Chat Completions工具调用，脚本明确使用此协议。可在PyCharm CE选择已有验证解释器，再运行该文件；运行会产生真实模型用量。本次仅做模拟HTTP验证，没有读取用户Key或调用真实服务。

示例问题为“菜单有哪些咖啡？拿铁多少钱一杯？还剩多少杯？”。预期使用get_menu/get_price/get_stock获取菜单、美式/拿铁/摩卡名称、拿铁20元/杯、库存6杯，再生成回答；模型实际调用次序与措辞可不同。程序会打印工具名、参数和结果。读代码时先看编号1–4，再看循环中的工具执行和结果追加，不必一次记住全部语法。

缺少环境变量会报KeyError；缺少依赖时先检查解释器；服务报不支持tools时核对型号/入口。非法工具参数或未知工具名会停止并报错；工具持续被请求时，最多5轮后报错。菜单没有的饮品与库存为0分别返回不同数据。max_rounds是本例循环次数，SDK重试还可能增加实际HTTP尝试。

??? note "展开完整代码：04_coffee_tools.py"

    ```python
    """咖啡店工具调用完整例子，价格和库存均为本地示例数据。
    
    Python 3.12，依赖沿用本目录requirements.txt。
    运行前设置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL。
    入口需支持Chat Completions工具调用；运行将访问真实模型服务。
    """
    
    import json
    import os
    
    from langchain.messages import HumanMessage, SystemMessage, ToolMessage
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
    
    
    # 1. 本地示例数据：price单位为元/杯，stock表示可售杯数。
    COFFEE = {
        "美式": {"price": 15, "stock": 10},
        "拿铁": {"price": 20, "stock": 6},
        "摩卡": {"price": 25, "stock": 0},
    }
    
    
    # 2. 三个普通函数。三引号里的说明会成为工具描述。
    def get_price(drink: str) -> dict:
        """查询一种咖啡的单杯价格，单位元。drink填写菜单中的饮品名称。"""
        if drink not in COFFEE:
            return {"error": "菜单中没有这种饮品", "drink": drink}
        return {"drink": drink, "price": COFFEE[drink]["price"], "unit": "元/杯"}
    
    
    def get_stock(drink: str) -> dict:
        """查询一种咖啡还可售多少杯，0表示售罄。drink填写菜单中的饮品名称。"""
        if drink not in COFFEE:
            return {"error": "菜单中没有这种饮品", "drink": drink}
        return {"drink": drink, "stock": COFFEE[drink]["stock"], "unit": "杯"}
    
    
    def get_menu() -> list[str]:
        """获取菜单中的全部饮品名称；不返回价格或库存。"""
        return list(COFFEE)
    
    
    # 3. 包装函数：原函数保留，另建包含名称、说明、参数和执行入口的工具对象。
    price_tool = tool(get_price)
    stock_tool = tool(get_stock)
    menu_tool = tool(get_menu)
    TOOLS = [price_tool, stock_tool, menu_tool]
    
    # 工具名称来自函数名，例如price_tool.name是get_price，不是price_tool。
    TOOLS_BY_NAME = {item.name: item for item in TOOLS}
    
    
    def answer_question(llm, question: str, max_rounds: int = 5) -> str:
        # 4. 将三个工具的定义提供给模型。
        llm_with_tools = llm.bind_tools(TOOLS)
        messages = [
            SystemMessage(content=(
                "你是咖啡店助手。菜单、价格和库存必须查询工具后再回答。"
                "饮品名称不明确时先询问；工具报告饮品不存在时如实说明。"
                "只处理查询，不下单或扣减库存。用中文简洁回答，并注明是示例数据。"
            )),
            HumanMessage(content=question),
        ]
    
        # 5. 模型可能先请求工具，拿到结果后再回答，因此需要循环。
        for _ in range(max_rounds):
            response = llm_with_tools.invoke(messages)
            messages.append(response)  # 保存完整模型回复，包括其中的工具请求。
    
            if response.invalid_tool_calls:
                raise ValueError("模型返回了无法解析的工具参数")
            if not response.tool_calls:
                return response.text  # 没有工具请求，本次回答结束。
    
            # 一条模型回复可能请求多个工具，逐一执行并回填。
            for call in response.tool_calls:
                name = call["name"]
                args = call["args"]
                if name not in TOOLS_BY_NAME:
                    raise ValueError(f"未知工具：{name}")
    
                print(f"[模型请求] {name}，参数：{args}")
                result = TOOLS_BY_NAME[name].invoke(args)  # 真正执行本地函数。
                print(f"[工具结果] {result}")
    
                messages.append(ToolMessage(
                    content=json.dumps(result, ensure_ascii=False),
                    tool_call_id=call["id"],  # 使用原请求ID，关联请求与结果。
                    name=name,
                ))
            # 下一轮invoke会把刚才添加的工具结果一起发给模型。
    
        raise RuntimeError("达到本例调用轮数上限，尚未获得最终回答")
    
    
    def main():
        # 6. 从本机运行配置读取接入信息，明确使用Chat Completions接口。
        llm = ChatOpenAI(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ["LLM_BASE_URL"],
            model=os.environ["LLM_MODEL"],
            use_responses_api=False,
            timeout=15,
            max_retries=1,
        )
        question = "菜单有哪些咖啡？拿铁多少钱一杯？还剩多少杯？"
        print("用户：", question)
        print("助手：", answer_question(llm, question))
    
    
    if __name__ == "__main__":
        main()
    ```

## 4. 完整手动循环：逐段读

配套`04_tool_loop.py`可在模型配置好后运行。先读下面的段落说明，再展开文件：

1. 建立`tools`字典，名称只对应明确注册的工具。应用不执行模型返回的任意Python字符串，也不使用eval。
2. 用bind_tools得到能提出工具请求的模型；准备系统消息和问题。
3. 每轮invoke，先把完整AIMessage追加到历史；它包含工具请求，不能只保存文本。
4. 没有tool_calls时返回回答；无法解析的工具参数则停止，避免假装执行成功。
5. 有tool_calls时逐个找工具、校验并执行；未知名称和格式错误返回明确状态。
6. 为每个请求补一条ToolMessage，并使用同一个调用ID，再进入下一轮。

??? note "展开完整手动循环 04_tool_loop.py"

    ```python
    """手动展示工具循环；最多调用模型4次。"""
    import json

    from langchain.messages import HumanMessage, SystemMessage, ToolMessage
    from pydantic import ValidationError

    from model_config import make_model
    from query_tools import lookup_balance


    def run_tool_loop(model, question: str, max_calls: int = 4):
        tools = {lookup_balance.name: lookup_balance}
        bound_model = model.bind_tools(list(tools.values()))
        messages = [
            SystemMessage(content="查询余额必须使用工具；编号不明确先问。按工具结果回答并说明币种和日期。"),
            HumanMessage(content=question),
        ]
        for _ in range(max_calls):
            response = bound_model.invoke(messages)
            messages.append(response)
            if response.invalid_tool_calls:
                raise ValueError("模型返回了无法解析的工具参数，停止本轮")
            if not response.tool_calls:
                return response, messages
            for call in response.tool_calls:
                print("准备执行工具：", call["name"], call["args"])
                selected = tools.get(call["name"])
                if selected is None:
                    payload = {"status": "unknown_tool"}
                else:
                    try:
                        payload = selected.invoke(call["args"])
                    except ValidationError:
                        payload = {"status": "invalid_arguments", "hint": "客户编号必须是C加3位数字"}
                messages.append(ToolMessage(
                    content=json.dumps(payload, ensure_ascii=False),
                    tool_call_id=call["id"],
                ))
        raise RuntimeError("超过本例模型调用次数上限，请检查消息和工具结果")


    if __name__ == "__main__":
        answer, _ = run_tool_loop(make_model(), "查客户C001的未收余额。")
        print(answer.text)
    ```

对成功的C001查询，典型历史是HumanMessage→AIMessage工具请求→ToolMessage金额12800→AIMessage回答；实际列表前面还包含SystemMessage。最后一次模型调用需要看到先前AIMessage及对应ToolMessage，这样才知道结果属于哪次请求。

`tool_call_id`像回执上的关联号。同一轮可能请求多个工具，不能只按“第一个结果”猜对应关系。这里的ID用于关联消息，不自动提供写操作的幂等保证；真实登记收款还需要业务请求号、事务或幂等机制。

本例最多调用模型四次。达到上限仍在请求工具，就抛出RuntimeError，供人检查。限制用于防止循环无限继续，不证明四次一定足够，也不代替总时间或金额预算。

## 5. 工具失败后，怎样读程序的处理？

| 情况 | 本例结果 | 应当怎样理解 |
| --- | --- | --- |
| C002余额为零 | status=ok，amount=0 | 确认对象存在且查询成功，才可说余额零 |
| C999不存在 | status=not_found | 说明未找到，不补零 |
| 参数不是C加三位数字 | invalid_arguments | 模型可纠正参数或向用户澄清 |
| 工具名不在字典里 | unknown_tool | 没有执行任意函数 |
| 模型持续要求重查 | 达到调用上限 | 检查工具结果、提示词与历史是否完整 |

本例捕获了预期的参数校验错误，没有用`except Exception: return 0`吞掉一切。真实数据库断连应记录并返回可识别的失败，不与无欠款混在一起。错误文本也不要随意包含密钥或原始凭据。

只读查询通常较容易重试；写操作是否可重试要看业务幂等性。不能因为Agent“还想再做一次”就重复登记业务单据。

## 6. PyCharm操作步骤与断点

1. 先运行`07_review.py`，确认纯业务和参数校验；然后准备模型配置。
2. 打开`04_tool_loop.py`，在`response = ...`之后打断点，观察tool_calls，而不只看response.text。
3. 在`payload = selected.invoke(...)`前后打断点，比较args与业务返回。
4. 再观察messages里新追加的ToolMessage，核对调用ID，最后看第二次模型请求的输入。
5. 若看不到tool_calls，核对所选模型是否支持、工具说明是否合适、问题是否需要工具；若第二次API报消息顺序错误，检查是否保留了工具请求并一一回填。

不要求你闭卷写出循环。目标是拿到AI生成的版本后，能找到这些关键步骤，并看出遗漏。

## 7. 可选练习

A. 代码只有bind_tools和一次model.invoke，输出了tool_calls，查询完成了吗？B. 为什么不能把C999结果改成amount=0方便显示？C. AI删除messages.append(response)，只补ToolMessage，会有什么问题？

??? note "参考答案与推理"
    A：还没有，缺实际执行与结果回填。B：将不存在与成功零余额混淆，用户会得到错误事实。C：历史中缺少发起工具请求的AIMessage，关联关系和协议顺序可能失效，后续模型也无法可靠知道工具结果对应什么。

## 本章回顾与检查清单

工具调用有两次边界：模型生成结构化请求，应用执行可信入口。结果要带着状态与关联ID回到历史，模型才继续处理。

- [ ] 能区分bind_tools、模型invoke与工具invoke。
- [ ] 能找到参数校验、白名单执行、结果回填和结束条件。
- [ ] 能用实际工具结果检查最终回答。

## 阅读中产生的答疑

暂无。阅读重点是§3及§4六个步骤，源码用于对照这些位置。

## 来源与后续

核对日期2026-11-08：[工具定义](https://docs.langchain.com/oss/python/langchain/tools)、[消息与工具结果](https://docs.langchain.com/oss/python/langchain/messages)、[模型工具调用](https://docs.langchain.com/oss/python/langchain/models)。下一章：[LangChain Agent](05-agent.md)；[目录](index.md)。
