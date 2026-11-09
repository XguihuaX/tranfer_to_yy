# 用友 AI FDE 入职学习总览

更新日期：2026-11-08（Asia/Shanghai）

## 目标与分工

- 2026-11-08 入职用友数据应用服务运营部算法工程师，方向为基于 ERP 的 AI FDE，可能出差。
- 本对话负责学习分类、进度、评估和调整；模块对话负责具体教学与练习。
- 共用教材首页为 `docs/index.md`，本地网页地址 `http://127.0.0.1:8765/`（需启动预览服务）。教学主线以章节正文为准，聊天负责答疑与练习反馈。
- 所有模块先读取 `TEACHING-GUIDE.md`；每开始一章，先写好完整章节，再让用户边读边问。每个模块共同维护教材中自己的章节目录。
- 先开启“00 用友产品与 ERP 业务”和“01 Python 与 API 工程基础”。后续模块到达时再开。
- 新对话属于本机“用友”项目，使用 local 环境。共用工作目录，不默认创建工作树。
- 每天可学习 5–8 小时；建议每日 45–60 分钟用于产品业务，其余时间推进技术主线。
- 下述 120 小时是初始核心预算，不代表全部内容可以达到熟练水平；按练习结果调整。

## 已知画像与待确认项

- 会 SQL 查询；复杂查询和业务口径能力通过练习验证。
- 有 Skyler 项目、LLM 应用、多跳检索、信息抽取和对照实验经历。
- 大量使用 AI Coding；FastAPI 等代码只能读懂一部分，工程独立维护能力需要补齐。
- 不会 Java；没有 Linux 服务器部署和 Docker 实践，没有驻厂经验。
- 学过 PyTorch，需恢复；做过音色训练的数据处理、loss 分析和效果验证，尚需学习 LLM LoRA/SFT。
- 公司具体产品、版本、内部 AI 平台、开发语言、首个客户场景均待确认。
- GPU、远程服务器及预算待确认。未确认前不租用资源，不开展付费训练。
- Skyler 技术栈已由原对话只读核实：FastAPI/Pydantic、HTTPX、LiteLLM、自研 ChatAgent/工具循环、SQLAlchemy/SQLite、sentence-transformers/NumPy、Python MCP SDK。当前未发现 LangChain/LangGraph/LlamaIndex/Dify 接入。
- 上述项目事实不等于学习者已独立掌握相应技术。

## 学习分类与先后顺序

| 编号 | 模块 | 内容与工具 | 完成证据 | 初始预算 |
| --- | --- | --- | --- | --- |
| 00 | 用友产品与 ERP 业务（持续并行） | 产品地图；YonBIP/YonSuite 等定位；iuap、数据、智能与集成平台；订单到回款流程；主数据、组织、单据状态、指标口径；OpenAPI/扩展入口 | 能用自己的话讲清一条业务链、解释关键单据和指标，说明一个 AI 场景的输入、输出与边界 | 12h |
| 01 | Python 与 API 工程基础 | 类型、函数、模块、异常、async/await；HTTP/JSON；FastAPI、Pydantic、HTTPX；流式响应、SSE、WebSocket | 能解释并修改小接口；实现参数校验和异常处理；理解连接与任务取消；跟踪一次调用 | 22h |
| 02 | Linux、Git 与部署 | 文件/权限、进程/端口、环境变量、日志、SSH；Git 基本操作；Docker/Compose | 能按说明启动服务和数据库，定位配置、端口和连接故障，写可复现部署说明 | 16h |
| 03 | LLM 调用与工具使用 | PyCharm实操，以LangChain为框架主线；消息与上下文、结构化输出、工具调用与基本Agent；用小型普通Python例子解释执行循环；超时、重试、取消；MCP基础；LiteLLM按需对照 | 跑通模型→查询工具→结果回填→回答，能调试LangChain实现并解释关键步骤与失败路径 | 14h |
| 04 | RAG 与业务数据接入 | 文档解析、切分、embedding、检索、重排、来源；sentence-transformers；SQL/SQLAlchemy 基础；ERP 接口、权限与指标口径 | 能区分检索错误、生成错误、数据错误；结果可追溯；能正确查询模拟业务数据 | 14h |
| 05 | 企业 Agent 工作流 | 承接03的LangChain基础；重点学习LangGraph状态、节点、分支、持久化和人工介入；权限、幂等、任务恢复、执行记录 | 用同一小任务对照普通 Python 与 LangGraph；验证澄清、确认、重试和重复请求行为 | 16h |
| 06 | Qwen 微调实践 | 恢复 PyTorch；Transformers/PEFT 概念；LLaMA-Factory；LoRA SFT，算力适配时选 QLoRA；数据划分和前后对照 | 有原模型基线、独立测试集、训练记录、训练后结果和适用性结论；loss 下降不等于业务收益 | 14h |
| 07 | 综合评估与 FDE 交付演练 | 固定测试集、错误分类、日志与基本指标；部署、演示、需求澄清、验收和交接；需要时接触 vLLM | 小型 ERP AI 助手可运行、可解释、可验证、可交接，并能处理几种故障 | 12h |

技术主线：01 → 02 → 03 → 04 → 05 → 06 → 07。00 全程并行。模块 06 的实际运行取决于算力；数据与评估准备可提前。评估与权限意识从前面模块即开始，07 负责整合。

## 共用练习主题

2026-11-08用户补充：技术主线先学通用知识、框架与代码理解，无需完全适配ERP。以下案例供连续示例和后续整合使用，不是每章必须完成的项目目标；不以ERP业务知识作为03的额外前置。

使用合成数据构建小型“ERP 应收查询助手”：

自然语言 → 结构化查询意图 → 参数化查询或模拟 ERP API → 金额与来源 → 流式呈现。

先从普通 Python/HTTP 小练习开始，逐步加模型、检索、工作流和部署，不一开始建设完整 ERP。第一版以只读查询为主；写操作通过模拟草稿/确认流程学习。真实业务权限由后端和业务系统执行。

微调可以选择“业务问句→结构化查询意图”任务；模型候选为 Qwen3-4B-Instruct-2507，最终型号、训练配置及框架版本在实践时重新核实。先测提示词基线，再决定训练实验；不保证微调必然改善结果。

## 教学与掌握标准

- 先用少量具体问题或短代码核实基础，不重复收集已有画像。
- 每章先准备完整的可阅读正文、示例、误区与练习；每轮围绕当前章的一个小目标答疑与反馈。
- 当前问题优先补回对应小节或章末答疑，并指明返回位置。跨章问题记录待后续解释，不因追问擅自跳章。
- 可以使用 AI Coding；通过能否解释、修改和排错确认掌握情况，不以复制运行作为唯一证据。
- 每个模块记录：已学内容、用户实际完成的证据、错误与薄弱点、下次起点。
- 后续模块读取本文件和前一模块记录；不默认拥有其他对话的完整记忆。
- 如需要修改本总览，先由总对话统一调整。各模块只编辑自己的 `docs/NN-*/` 教材和 `learning/NN-*/` 记录目录，避免共用工作区冲突；总对话维护首页、站点与公共规范。
- 不自动向其他对话发送消息；总对话需要时读取模块进展。需要另开对话时由总对话按用户已有授权和当前进度推进。
- 不擅自修改 Skyler 项目。其参考对话：codex://threads/01a0f7ba-dc1b-7b51-a974-dc84bf98014e。

## 暂缓深入

Java/Spring Boot（先确认岗位是否需要亲自修改）、多个同类 Agent 框架、大规模分布式训练、强化学习后训练、从零预训练。用友内部平台如为主要交付工具，则调整相应模块的工具比重。

## 对话与进度

- 总对话：codex://threads/01a13eb1-db3b-7f42-a028-7a29012362a2。
- 00：[00 用友产品与 ERP 业务](codex://threads/01a13f0f-fff7-78c0-b669-330ae4c325d9)；已创建，准备第一课；记录目录 learning/00-products/。
- 01：[01 Python 与 API 工程基础](codex://threads/01a13f10-43ef-7f31-873d-ac72a89cc67b)；已创建，准备第一课；记录目录 learning/01-python-api/。
- 02：[02 Linux 与 Git](codex://threads/01a19181-cf52-78d2-9a73-567be283f7fc)；用户已于 2026-10-31 创建。按用户授权完成总体调研规划、02批量编写与总对话独立二次复核，2026-11-01通过。8章核心与Docker选学章均已准备；规划：`learning/02-deployment/PLAN.md`；作者核对：`learning/02-deployment/VERIFICATION.md`；二次复核：`reviews/02-textbook-review.md`；详细进度：`learning/02-deployment/PROGRESS.md`。用户于2026-11-08在总对话自述“02已经学习完了”，据此推进03；该反馈不新增具体实操验收记录。远程Linux与Docker容器运行仍按既有实测记录判断。
- 03：2026-11-08用户授权先编写本模块完整教材，强调知识补充、知道操作步骤、能读懂AI代码与必要排障；以PyCharm和LangChain为主线，05深入LangGraph。八章正文、连续lab示例、依赖文件与作者验证已准备，入口 `docs/03-llm-tools/index.md`；学习状态 `learning/03-llm-tools/PROGRESS.md`，核对记录 `learning/03-llm-tools/VERIFICATION.md`。建议从03-01 §1开始；用户尚无03阅读或实操反馈。拥有Qwen/HeyRoute访问，具体型号、Key分组与协议尚待确认；本轮只用本地模拟响应验证模型代码，无真实付费调用。DSH与养鱼继续延后，调研保留于 `reviews/dsh-research-2026-11-08/REPORT.md`。用户随后明确授权创建03对话，已在本机同项目创建：[03 LLM、LangChain与工具使用](codex://threads/01a1ba6c-3f65-7a62-8095-6650b5e3b356)，负责后续教学、答疑、教材补充与进度维护。最新偏好：先学通用知识，无需完全适配ERP。
- 04–07：尚未开启，到达时创建。

## 公开资料入口

- 用友 ERP 产品：https://yonyou.com/yingxiao/erp/
- iuap 平台：https://www.yonyou.com/products/iuap
- 用友开发文档：https://developer.yonyou.com/developer/documentCenter
- FastAPI：https://fastapi.tiangolo.com/tutorial/
- LangChain：https://docs.langchain.com/oss/python/langchain/overview
- LangGraph：https://docs.langchain.com/oss/python/langgraph/overview
- LLaMA-Factory：https://github.com/hiyouga/LlamaFactory

公开产品定位与内部实际部署有区别，教学应使用官方资料核实，不把营销描述等同于岗位职责或已验证能力。
