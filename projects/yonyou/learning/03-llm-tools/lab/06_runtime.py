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
