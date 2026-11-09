# 03-06 超时、重试、流式输出与排障

> 教材已准备，2026-11-08。围绕读懂控制范围与识别失败原因，不要求背异常类或所有参数。

## 本章问题、目标与前置

代码设置了15秒超时，为什么整个Agent还可能运行更久？流式已经显示了文字，为什么仍可能失败？本章把模型请求、任务执行和显示过程分开。读完应能在AI生成的代码里找到等待、重试、结束和日志位置，判断这些设置是否解决当前问题。

前置为[基本Agent](05-agent.md)，约35–45分钟；[01的async](../01-python-api/05-async-and-tasks.md)与[流式/SSE](../01-python-api/09-streaming-and-sse.md)可按需回查。生产监控平台和LangGraph恢复在后续模块。

## 1. 先分清三种限制

| 限制 | 约束什么 | 没有直接约束什么 |
| --- | --- | --- |
| 请求timeout | 单次底层网络请求的等待阶段 | 整个多步任务的总耗时 |
| max_retries | 符合重试条件的请求额外尝试次数 | Agent调用模型的轮数 |
| Agent步数限制 | 图执行继续推进的步数 | 每一步HTTP请求的等待或费用 |

本例max_retries=1表示初始尝试加至多一次重试；多个Agent轮次还可能各自重试。再在外层套一个“失败就重来3次”的循环，会叠加更多请求。读AI代码时把各层乘积和等待位置标出来，再决定需不需要外层重试。

超时也可能区分连接、读取、写入和连接池等待，具体由底层客户端处理。timeout=15不是一个能覆盖所有模型轮次、工具、退避等待的总倒计时。

## 2. 哪些错误值得重试？

| 情况 | 应对方向 |
| --- | --- |
| 缺少本地变量、认证失败 | 改配置；重复原请求通常无效 |
| 参数格式错误、模型不支持参数 | 改输入或接入方式 |
| 暂时限流、部分服务端错误、临时连接故障 | 有上限地等待或重试，核对SDK是否已重试 |
| 业务返回not_found | 保留业务状态，不靠重试制造结果 |
| 写操作后断线，不知是否成功 | 先按请求号查询业务状态，再决定是否重发 |

本模块只读查询，仍要学会分辨“请求没成功”和“业务返回失败”。不要写`except: return {"amount": 0}`，也不要让异常无限循环。

## 3. 用异步外层等待表达本地总时限

配套`06_runtime.py`包含异步等待与文本流两个函数：

```python
import asyncio
import time

from langchain.messages import HumanMessage
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from model_config import make_model


async def ask_with_deadline(model, question):
    started = time.perf_counter()
    try:
        response = await asyncio.wait_for(
            model.ainvoke([HumanMessage(content=question)]), timeout=20.0
        )
        print(response.text)
        print("用量：", response.usage_metadata)
        return response
    except AuthenticationError:
        print("认证失败：核对本次运行的Key、服务地址与所属分组。")
    except RateLimitError:
        print("触发限流：检查限额和并发；不要再叠加无限重试。")
    except (TimeoutError, APITimeoutError):
        print("本地等待超时：本轮未取得完整回答。")
    except APIConnectionError:
        print("连接失败：检查地址、网络和证书错误。")
    finally:
        print(f"本地耗时：{time.perf_counter() - started:.2f}s")
    return None


def stream_text(model, question):
    complete = False
    try:
        for chunk in model.stream([HumanMessage(content=question)]):
            print(chunk.text, end="", flush=True)
        complete = True
    finally:
        print("\n流状态：", "传输正常结束，请另核对截断与业务结果" if complete else "中途结束，文字可能不完整")


if __name__ == "__main__":
    asyncio.run(ask_with_deadline(make_model(), "用一句话解释应收余额。"))
```

`ask_with_deadline`记录本地开始时间，用`asyncio.wait_for`等待一次ainvoke，20秒是本地对该协程的等待范围。本例SDK内部timeout、退避与重试都处于这次调用之内。超时会请求取消本地协程，等待取消清理可能使返回略晚于设定时间；它不保证远端推理立即停止，也不能保证不计费。

这里是模型级调用。如果要限制整个Agent，应对`agent.ainvoke(...)`的协程施加任务级范围，并另外检查工具执行、重试和业务状态。取消网络请求和撤销一笔已登记收款是不同动作；后者需要业务系统流程。

异常分支分别说明认证、限流、等待和连接问题。未列出的错误继续抛出，保留调用位置，供你查看；不能把未知失败一律包装成“没查到客户”。finally无论成功失败都输出耗时，便于比较。

## 4. 流式不是另一个Agent，也不代表已经成功

`model.stream`逐段给出AIMessageChunk。chunk是增量，可能很短甚至没有正文，不等于一条完整业务事件。`chunk.text`只显示文本；工具参数也可能分片传输，不能在半个JSON刚出现时执行工具。

`stream_text`只有迭代自然结束才标记传输正常；网络错误时已有文字可以留在屏幕上，但必须知道它没有完成。传输正常也可能是模型达到输出上限后截断；还要看服务提供的finish_reason或完成状态，并核对业务任务是否完成。本例提示你另查这些信息，没有自动判定业务成功。函数没有吞掉异常，仍会显示错误。模型流通过何种服务端接口转给网页，是01的HTTP/SSE/WebSocket设计；模型生成、Python迭代与前端通信是三个环节。

Agent运行还可能产生工具开始、工具结果、状态更新等事件。当前先会读模型文本流；更细的Agent事件流在需要做界面时按固定版本补充，不要求在开课时掌握所有流模式。

## 5. 日志至少能回答哪几个问题？

一次任务给一个run_id，模型请求/工具执行再记录关联信息。能定位问题的日志通常包括：调用时间、模型/入口、耗时、结果状态、工具名、必要参数、关联ID和可获得的用量。只打印“执行成功”无法区分哪一步。

前章ToolMessage的tool_call_id用于关联工具消息，自己的run_id用于整次业务任务；服务商request_id又用于查询上游请求，它们不必相同。记录时保留各自含义，不把一个随机字符串到处混用。

查询结果包含来源和日期，最终回答要能对上它。生产日志中的业务数据按实际需要保留；Key、认证头和密码不进入日志。LangSmith等追踪平台可以后续选用，本课不要求开账号或自动上传完整轨迹。

## 6. 排障时按调用路线缩小范围

```text
能否启动Python？
 → 配置是否进入本次进程？
 → 模型请求是否收到合格响应？
 → 是否提出了正确工具请求？
 → 工具是否真正执行并返回合格状态？
 → 最终回答是否忠实使用该结果？
```

例如用户看到“没查到”，先看工具是否实际返回not_found。如果根本没连上模型，却被一层except改成同样文字，应该修正异常分类。模型用了正确工具、参数是错客户，则检查客户识别；业务结果正确、文字错误，则检查结果解释。

这样检查也适用于AI Coding生成的长项目：先沿一个输入找关键边界，不必立刻读完每个文件。

## 7. 操作步骤与代码修改练习

1. 先读model_config.py里的timeout/max_retries，再找到Agent的recursion_limit，写出各自范围。
2. 在PyCharm运行06，观察成功/异常分支及耗时；可先用作者离线验证记录理解，不必主动制造付费重试。
3. 要观察文本流，可以在同一文件main中改为调用stream_text；用同一配置对照。不要同时跑两条路径后误以为只有一次请求。
4. 遇到400、401时先改配置与参数；429先看SDK与服务限额。错误原文用于定位，分享时去掉凭据。

可选推演：每个请求最多额外重试1次，一个Agent任务实际调用模型3轮，最多可能有几次HTTP尝试？

??? note "参考答案与推理"
    在每轮都触发一次重试且没有更早结束的情况下，3×(1+1)=6次HTTP尝试。还要另看工具是否访问外部API，不能把这个数字当作整个任务所有网络请求总数。

## 本章回顾与检查清单

限制需要对应对象：网络请求、模型轮次、Agent执行或整个任务。日志把这些对象连起来，流式则改变呈现时机，不改变业务结果必须验证的要求。

- [ ] 能解释timeout、重试、Agent步数与外层截止时间。
- [ ] 能说明流中断时为什么已有文字不是完整结果。
- [ ] 能按失败层次选择检查点，不用统一空值掩盖错误。

## 阅读中产生的答疑

暂无。返回§1确认范围，再看§3函数；流式问题回到§4。

## 来源与后续

核对日期2026-11-08：[模型调用](https://docs.langchain.com/oss/python/langchain/models)、[ChatOpenAI配置](https://docs.langchain.com/oss/python/integrations/chat/openai)、[官方流式说明](https://docs.langchain.com/oss/python/langchain/streaming)、[asyncio超时](https://docs.python.org/3/library/asyncio-task.html#asyncio.wait_for)。下一章：[读代码与核查结果](07-review-delivery.md)；[目录](index.md)。
