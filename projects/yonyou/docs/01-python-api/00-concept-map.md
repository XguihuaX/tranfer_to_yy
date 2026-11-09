# 01 概念地图：先看关系，再看代码

> 整个 01 模块的 XMind 概念图已准备。更新：2026-10-27。学习状态见模块进度。

[打开或下载 XMind 概念地图](assets/01-Python-API-概念地图.xmind)

这是一个可以用 XMind 编辑的文件，覆盖原 01–10 章，共有六张可以切换的图。第一张先建立全貌，其余图按问题展开；详细分支默认折叠，避免一次看到全部内容。

| 图页 | 集中回答什么 | 对应原章 |
| --- | --- | --- |
| 00 先看全貌 | Python、异步、网络和各工具怎样合作完成查询？ | 整体关系 |
| 01 Python | 查询函数、数据、参数、异常和文件怎样组织？ | 01–04 |
| 02 异步 | 当前任务在等什么，其他任务什么时候能执行？ | 05 |
| 03 请求响应 | 两个程序怎样发请求、传数据、收结果？ | 06 |
| 04 接口工具 | HTTPX、FastAPI、Pydantic、Uvicorn 各负责什么？ | 07–08 |
| 05 持续通信 | 什么时候用普通 HTTP、SSE 或 WebSocket？ | 09–10 |

先打开 **00 先看全貌**，只看六条主分支。之后按当前疑问切换图页、展开一个概念。节点中的短句解释职责，备注补充条件与易错点，带链接的节点可以回到相应教材。无需先做完练习才能继续。

贯穿案例仍是合成客户欠款查询：C001 为 12800 元，C002 为 0 元，C999 不存在。当前先教概念；等概念之间的关系清楚后，再对照[统一代码例子](00-one-example.md#first-request)寻找实际位置。

原章正文和练习继续作为完整讲解与查阅，不需要重新从第一章逐页读起。

## 用来核对概念的直接来源

导图内容结合本模块现有教材与代码，框架和异步关键行为已对照官方资料：

- [Python 3.12：协程与任务](https://docs.python.org/3.12/library/asyncio-task.html)
- [FastAPI：请求体与 Pydantic 模型](https://fastapi.tiangolo.com/tutorial/body/)
- [HTTPX：请求、JSON、响应与状态检查](https://www.python-httpx.org/quickstart/)
- [FastAPI：StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [FastAPI：WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)

XMind 文件结构参考 [XMind 官方 SDK 的数据模型](https://github.com/xmindltd/xmind-sdk-js/blob/master/src/common/model.ts)与[打包方式](https://github.com/xmindltd/xmind-sdk-js/blob/master/src/utils/zipper.ts)。

[返回模块目录](index.md)
