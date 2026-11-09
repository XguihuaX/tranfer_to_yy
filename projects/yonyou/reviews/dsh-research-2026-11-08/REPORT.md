# DeepSeek Harness 能力、技能与“养大肥鱼”调研

调研日期：2026-11-08（Asia/Shanghai）。本轮为公开文档、源码目录和项目README核查，没有安装插件、授权账号或发起付费模型调用。

## 结论

DSH已经具备本地Agent工作台的能力面：文件与终端操作、网页工具、技能、MCP、子Agent、持久任务与定时执行。官方仓库还包含桌面客户端、Office技能和实验性的浏览器/电脑操作组件。社区在此基础上扩展长期Bot、记忆、即时通信、远程访问和陪伴角色。

“养大肥鱼”主要指给Agent配置DeepSeek同人角色，再加持续记忆、关系/情绪状态、日记、定时活动和聊天入口。各家的实现不同，不对应一个唯一的官方功能或安装包。从下述开源实现看，“养”的主要对象是角色设定、外部记忆和工具环境，并不是聊天时持续训练模型权重。

官方项目仍标为developer preview。以下表述分别标明官方组件与社区扩展；仓库有实现不等于所有发布载体已经默认启用。没有据此给出稳定性或任务成功率排名。[官方仓库](https://github.com/deepseek-ai/deepseek-harness)

## 官方能力地图

| 能力 | 当前证据与用法 | 需要确认的条件 |
| --- | --- | --- |
| 本地编程与文件任务 | Web向导说明Agent可读取/编辑项目、执行命令、委派任务、维护计划 | 模型、工作区、执行权限与项目依赖 |
| 多模型与中转 | 自定义模型API支持Chat Completions、Responses、Anthropic Messages | 按实际服务选择协议、模型名与Key；每个provider配置一种协议 |
| 网络检索 | web_search与web_fetch工具 | 可用的搜索/抓取后端及其鉴权；不能把模型Key当作所有工具的通用凭据 |
| 浏览器操作 | browser-use能力层，实验后端包括Playwright MCP、Chrome DevTools MCP等 | 选择并配置具体后端 |
| macOS电脑操作 | 观察应用、辅助功能树、截图、点击与输入 | 实验性组件；macOS14+及辅助功能/屏幕录制权限 |
| 子Agent与团队 | 子Agent可委派/继续/通信；Team增加持久共享任务板与任务归属 | Team默认关闭；成员共享checkout，不自动隔离工作目录 |
| 长任务 | Goal保存跨轮目标；独立驱动组件负责继续执行 | 目标存储组件本身不启动任务，不等于无人值守可靠完成 |
| 定时任务 | Web提供Automation tasks，支持一次/重复执行与会话投递 | Host必须运行；退出后暂停调度，重启按规则处理错过的执行 |
| 技能 | SKILL.md发现、目录摘要与按需加载正文 | 技能目录、名称及所需工具/依赖可用 |
| Office | 官方Office路由与Word/PPT/Excel、渲染、重算、PDF导出技能 | 技能提供者不自动安装所有库；渲染和导出依赖对应运行时 |
| MCP | stdio与Streamable HTTP客户端，发现并暴露外部工具 | MCP服务本身需安装或运行；其数据和认证由服务负责 |
| Python集成 | 发布的Python SDK可从Python启动/复用Harness运行时 | Python3.10+及文档列出的平台；与Python手写Agent或LangChain属于不同抽象层 |

依据：[Web使用向导](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.md)、[模型配置](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md)、[网页工具](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/web/tool-web/README.md)、[浏览器能力层](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/browser-use/README.md)、[macOS组件](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/cua-macos/README.md)、[子Agent](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/subagent/README.md)、[Team](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/team/agent-team/README.md)、[Goal](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/goal/goal/README.md)、[定时任务](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/schedule.md)、[Python SDK](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/python-sdk.md)。

## Skill、工具与插件分别是什么

- Skill：描述什么时候做、怎样做、如何检查的说明材料，可以带脚本与资源。加载Skill不是训练模型，也不会凭空获得新的执行工具。
- 工具：真正可调用的执行入口，例如读文件、运行命令、查询外部系统。
- 插件：装入Harness的程序组件，可以提供工具、服务、界面、技能或连接器。
- MCP：外部工具与上下文服务的连接协议；安装一个Skill并不自动建立MCP连接。

官方技能系统可发现项目的`.dsh/skills`、`.agents/skills`及用户级目录，目录摘要与完整正文分开加载。迁移现有SKILL.md时仍须核对名称、目录和所依赖的工具。官方仓库自身的代码评审/文档规范技能是维护该仓库的材料，不应统称为安装DSH后就有的用户技能。[技能系统](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)

已核对的官方Office技能为七个：`office`、`office-docx`、`office-pptx`、`office-xlsx`、`office-render`、`office-recalculate`、`office-export-pdf`。它们对应任务路由、三类文档编辑以及渲染/公式重算/PDF导出。技能提供者与依赖运行时分开装配，不能仅凭列表存在就保证某台机器可立即渲染。[Office组件](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-office/README.md)

## 社区扩展抽查

以下七个项目均读取当前README，属于维护者公开描述，本机未实测。没有以插件市场的评分或下载量替代兼容性验证。

| 项目 | 主要能力 | 选择时的实际区别 |
| --- | --- | --- |
| [Fei2411/DS-Bot](https://github.com/Fei2411/DS-Bot) | 长期Bot、人设与记忆、主管Bot、群聊与转交、MCP/Skill能力库、连接器、IM入口 | 团队与长期助手产品；与官方Team任务板不是同一组件，另有独立桌面载体 |
| [haitang1/dsh-memory](https://github.com/haitang1/dsh-memory) | 跨会话记忆、摘要注入、会话总结、搜索/合并/导入导出/回滚 | 摘要与整合会使用模型；同名memory项目很多，安装时必须写明作者 |
| [keepview/dsh-lark](https://github.com/keepview/dsh-lark) | 飞书/私聊或话题映射到本机DSH会话 | 单一消息入口，需要飞书应用配置与可运行的本机Host |
| [liguobao/ds-harness-remote](https://github.com/liguobao/ds-harness-remote) | 从手机、Web或另一台设备继续访问运行中的工作区 | 远程入口，不替代运行Host的机器；客户端与服务兼容性需核对 |
| [yuyu520fish/dsh-fishtank](https://github.com/yuyu520fish/dsh-fishtank) | 鱼缸界面、事实记忆、心情/精力、关系、私语、日记、导入导出 | 轻量角色陪伴；核心状态存在JSON文件 |
| [1838601405/dsh-fish-world](https://github.com/1838601405/dsh-fish-world) | 人设、记忆摘要、心情、聊天与内容平台组件的整合面板 | 组合包，依赖多插件；项目明确抖音部分外发未真实验证，不能承诺全部功能可用 |
| [xxccdl/deepseek-harness-desktop](https://github.com/xxccdl/deepseek-harness-desktop) | 社区桌面分支，包含Windows电脑控制、浏览器、记忆、通知等扩展 | README明确为社区fork；不能把它的全部能力归到官方桌面版或Mac版本 |

官方也提供第三方记忆MCP参考配置：Memorix、MCP Reference Memory和Engram，默认不启用；可选取一种记忆方案验证跨会话召回，不必叠装多个。[官方记忆接入示例](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/mcp-memory.md)

官方插件索引机制需要启用实验选项并自行添加索引源，未预置一个唯一官方市场。市场列表可以用来发现项目，安装判断回到作者仓库、当前版本与实测。[插件索引说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/plugin-market.md)

## “养大肥鱼”的组成与真实含义

作者的第一人称教程把养鱼描述为将角色接到QQ、微信、飞书，再扩展到B站和抖音；这说明该用语同时包含陪伴、角色扮演与账号自动化，而不只指桌面动画。[数字生命卡兹克教程转载](https://www.panewslab.com/zh/articles/01a19fc1-c3e1-739d-9415-db74099477ce)

从fishtank与fish-world的实现可以拆出五层：

1. 人设：名字、形象、称呼、表达习惯和行为规则。
2. 记忆：用户偏好、共同经历、事实、关系，写入文件或数据库后在后续请求读取。
3. 状态：情绪、精力、关系数值，影响角色表达；这些是程序状态。
4. 行动：浏览、查资料、写代码或收发消息等工具调用。
5. 持续运行：定时触发、主动问候、日记，以及保留跨会话身份的消息入口。

因此，“越养越熟悉”可以来自更合适的人设、更多相关记忆、更准确的工具配置与经过验证的工作规则。不是每次聊天都更新基础模型参数。给模型更多Token也不直接等于更好用；日记、主动活动、多Bot讨论及记忆整合会产生额外调用。

刷视频、发布内容、直播还依赖具体平台桥接、登录与插件实现，不能由“有鱼缸插件”推出全部具备。fish-world明确将一些平台开关默认关闭，并标记部分抖音外发缺少真实验证。本次不登录或自动发消息。

## 对之前安装建议的修正

上一轮核对的npm包`@deepseek-ai/dsh@0.2.2-rc.1`要求Node>=24.9.0；本机当前Node22.15.1。这个要求适用于该npm路线。

但官方仓库还提供：

- Desktop：使用Electron及捆绑的pnpm/运行时，不要求用户先安装系统Node来运行桌面应用。具体发行包及平台资格以官方当前下载为准。
- Python SDK：普通SDK运行自带匹配的原生运行时wheel，文档明确不需要系统Node；须满足Python与平台前提。

所以“先升级Node”不是所有路线共通的前置。选择桌面体验、Web/CLI研究或Python嵌入后，再执行对应安装步骤。[Desktop运行时](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.md)、[Python SDK](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/python-sdk.md)

## 对本项目的建议

03继续用PyCharm与LangChain学习自己的Agent实现；DSH用于辅助工作与观察现成Agent。可先用同一个小任务对照模型、工具、记忆、技能在两种实现中的职责，不为使用DSH另开一套框架课程。

建议装配顺序：一个已验证模型入口 → 一个独立学习工作区 → 一项小任务 → 一个项目Skill → 一种记忆方案 → 按实际需求加Office或浏览器。若想体验陪伴，另加轻量鱼缸；需要长期多Bot管理再考虑DS Bot。外部IM、远控、内容平台随后逐项验证，不预装所有插件。

面向FDE的可行试验是：记住已核实的项目约定，读取合成应收数据，运行课程代码，输出带数据口径的交付说明。以上是建议实验，不是本轮已完成的实际能力测试。真实ERP权限、指标、接口与审计仍由具体接入设计负责。

## 调研记录与限制

- 已保存17份官方文档与7个社区项目README；索引为`official-source-index.json`和`community-source-index.json`，记录URL、文件名及SHA256。
- 官方目录扫描由GitHub API返回，未被截断；筛选结果及tree SHA见`official-tree-selection.json`。仓库里的测试fixture技能未计为用户可用技能。
- 原始公开材料位于`sources/`。默认分支和发布包可能不同，正式安装再固定版本并做小任务验证。
- 搜索中的第三方目录只作发现线索。一个推测的`linxin666/dsh-pet`仓库返回404，未列入推荐；GitHub DS-Bot页面读取失败后改读作者raw README成功。
- 本轮没有实际安装、收费调用、跨平台交互或外部账号连接，也没有改写02教材。
