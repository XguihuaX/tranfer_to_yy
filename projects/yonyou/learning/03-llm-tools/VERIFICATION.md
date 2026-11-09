# 03 教材作者核对

日期：2026-11-08（Asia/Shanghai）。作者及核对：总对话。本次授权为先完成整个03的知识正文、代码阅读和操作步骤，未自动创建新对话。

## 交付

- docs/03-llm-tools：目录、显式导航、8章完整正文；每章有前置、解释、完整例子、操作步骤、误区、可选练习及折叠答案、回顾和官方来源。
- learning/03-llm-tools/lab：共享模型配置、合成业务、意图与工具；01–07脚本、MCP客户端/服务端、依赖与配置示意、README。
- PLAN.md与PROGRESS.md分别记录框架和学习状态。用户阅读、练习、掌握均待实际反馈。
- 在模块.venv-verify创建独立作者环境，未改共享文档环境、用户PyCharm设置或系统Python；完整依赖为requirements-verified.lock.txt。

## 实际环境

Python3.12.14（macOS arm64）；LangChain1.4.9、langchain-core1.7.6、langchain-openai1.7.4、LangGraph1.2.20、Pydantic2.14.3、HTTPX0.28.1、OpenAI客户端3.46.0、MCP2.3.0。均从公开包仓库安装，pip check通过。

## 20类程序检查

原始结果：VERIFICATION-results.json。复现：

```sh
learning/03-llm-tools/.venv-verify/bin/python learning/03-llm-tools/verify_examples.py
```

| 范围 | 实际结果 |
| --- | --- |
| 合成业务 | C001=12800、C002=0、C003=500；C999无amount；名称歧义/唯一候选、币种和日期符合约定 |
| 参数和意图 | 工具格式/类型错误被拒绝；非法action/额外amount被拒绝；查询缺编号被执行前置拦下 |
| 配置 | 缺变量失败；协议显式设置；实际make_model工厂在模拟传输下分别走/v1/chat/completions与/v1/responses，并解析文本 |
| 01–03实际main | 通过本地HTTP模拟依次执行，核对响应、第二轮4条消息、模板填充、QueryIntent解析与余额执行 |
| 手动工具循环 | 成功、未知客户、参数错误、未知工具四分支；请求和回填ID对应，消息顺序正确；调用次数上限生效 |
| 实际Agent框架 | 预设模型请求驱动find_customers→lookup_balance→最终回答；状态可读；歧义路线结束于澄清；持续工具请求触发图步数限制 |
| 运行控制 | 异步成功与超时分类；流中断保留异常且不标正常；SDK max_retries=1在一次503后实际产生2次模拟HTTP尝试 |
| MCP | 真实本机stdio子进程：发现工具、C001结构化成功、C999业务not_found、错误编号is_error；退出连接清理子进程 |

模型相关HTTP由httpx.MockTransport处理，使用固定假凭据和fixture.invalid域名，无真实上游请求；Agent确实使用当前安装的LangChain/LangGraph执行，模型选择序列为预设。澄清路线检查因此不证明真实Qwen/HeyRoute会做出相同选择。

## 编写中发现并解决

1. MCP2.3的通用dict返回未自动提供structured_content：改为显式structured_output与可描述返回类型，重查真实stdio结果通过。正文同步给出当前SDK2 API，未混用旧FastMCP。
2. langchain-openai当前版本的默认连接选项在本机提示可能改变代理自动识别：共享工厂显式http_socket_options=()，保留HTTPX默认路径；工厂的chat/responses模拟请求均通过。测试辅助模型仍可能发出该上游提示，不涉及真实网络。
3. 文本流自然结束可能仍是模型预算截断：提示修改为“传输正常结束，请另核对截断与业务结果”，正文区分传输、截断与业务完成，避免错误保证。
4. 原8765预览进程仍返回旧03占位目录：核实PID命令与cwd均为本项目MkDocs后重启；新目录内容及全部9页HTTP200已确认。

## 发布检查

PUBLICATION-results.json记录：全站mkdocs build --strict退出0；03目录加八章共9页；1208个页面内本地链接及锚点目标存在；10个折叠块；14个Python代码块通过语法分析；13处完整源码摘录与实际文件逐字一致。所有lab Python文件也通过语法检查。

网页视觉抽查已完成：目录显示八章新内容；03-04完整工具循环可展开并正常显示代码；03-01正文、链接、标题与两侧导航排版正常。记录已写入PUBLICATION-results.json，浏览器保留03-01阅读入口。严格构建与静态链接不代替真实模型验收。

## 未执行范围

- 未读取或索取用户密钥；未调用Qwen、HeyRoute或其他真实/付费模型。具体Key分组、模型可用性、协议及工具/结构化能力待接入。
- 模拟的Responses只核对基本调用路由与文本解析；真实模型的Responses工具、结构化与流式需另测。
- PyCharm步骤核对JetBrains文档，未代用户改变IDE运行配置；Windows cmd说明没有实机执行。
- 未接真实ERP、生产数据库或多租户授权；数据为同组织合成口径，错误与状态的机制有对应例子。
- MCP本机工具已验证；LangChain beta MCPAdapter只解释接入步骤，未安装其额外FastMCP适配器，未宣称模型已通过它调用MCP。
- 未安装DSH或养鱼插件。没有将作者检查记成用户掌握。

## 官方资料

2026-11-08核对LangChain的Models、Messages、Tools、Agents、Structured output、Runtime、Streaming、ChatOpenAI和MCP文档，MCP Python SDK2客户端/传输文档，PyCharm Run/Debug配置，以及Qwen/HeyRoute接入资料。各章末尾给出支持对应内容的直接链接。

## 03模块对话新增 MVP 核对（2026-11-08）

- 新增 mvp/main.py、settings.py、requirements.txt、README.md 和模块内导读；直接复用已有 .venv-verify，未安装依赖。
- 实际执行默认 local 入口：multiply(12, 3)=36，add(36, 8)=44；清空环境变量且替换模型工厂为禁止调用后仍通过，确认 local 不创建模型客户端。
- 缺少模型环境变量时，实际 settings.make_model 在请求前报出需要配置的字段。
- 使用 httpx.MockTransport、fixture.invalid 假地址与假Key，执行实际 main 的 model/agent 两种入口和实际 settings 工厂：model 发出1次模拟HTTP请求且未注册工具；agent 发出3次，注册 add/multiply，真实执行两个本地工具，并按 mul_1/add_1 回填36/44。实际输出包含工具请求、返回和最终文本。
- 模型选择序列为预设，未调用真实 Qwen/HeyRoute；实际模型行为尚待接入验证。作者运行不记为用户实操。
- `.venv-docs/bin/mkdocs build --strict` 通过。实现与运行字段核对 LangChain Quickstart 及 PyCharm Python Run Configuration 官方文档，来源见 MVP 导读。

## 咖啡工具完整例子（2026-11-09）

- 新增lab/04_coffee_tools.py，使用已有环境，无新增依赖；单文件包含示例菜单、价格/库存函数、tool对象、bind_tools、工具执行与ToolMessage回填。无显式Field写法。
- httpx.MockTransport配合假Key和fixture.invalid，运行实际main：分别检查同轮3工具（2次模拟模型请求）和依次3工具（4次模拟模型请求）。实际工具定义包含get_menu/get_price/get_stock，回填ID分别匹配menu_1/price_1/stock_1，结果为菜单列表、拿铁20元/杯及库存6杯。
- 直接核对摩卡库存0与不存在饮品的error区别；模型持续请求工具时，answer_question按指定max_rounds抛出RuntimeError。
- 模型选择及最终文本是预设响应，未调用真实模型。教材完整源码从实际文件生成，严格构建通过。用户实操未验证。
