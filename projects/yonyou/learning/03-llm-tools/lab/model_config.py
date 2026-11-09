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
