"""模型接入配置。先用 local 模式时，可以暂时不读这个文件。"""

import os

from langchain_openai import ChatOpenAI


def make_model() -> ChatOpenAI:
    # 环境变量由 PyCharm 的 Run 配置传给 Python 进程。
    # os.environ 不会自动读取 .env；本例直接在 IDE 中配置即可。
    required = ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise ValueError(
            "请在 PyCharm 的运行配置中填写：" + ", ".join(missing)
            + "。暂不接模型时，可先把 main.py 的 MODE 设为 local。"
        )

    # 与教材保持一致：默认使用 Chat Completions 接口。
    # 仅当你的服务明确提供 Responses 接口时，才把此环境变量设为 responses。
    protocol = os.environ.get("LLM_API_PROTOCOL", "chat")
    if protocol not in {"chat", "responses"}:
        raise ValueError("LLM_API_PROTOCOL 只能是 chat 或 responses")

    # ChatOpenAI 是兼容接口的客户端类；请求目的地由 base_url 决定。
    # 可以连接提供相应兼容接口的 Qwen 服务或中转，并非固定访问 OpenAI。
    return ChatOpenAI(
        model=os.environ["LLM_MODEL"],            # 服务商允许当前 Key 使用的型号
        api_key=os.environ["LLM_API_KEY"],        # 凭据，仅在本机 Run 配置里填写
        base_url=os.environ["LLM_BASE_URL"],      # 模型 API 的入口地址
        use_responses_api=(protocol == "responses"),
        timeout=15.0,       # 底层请求等待限制，不是整个 Agent 任务的总时长
        max_retries=1,      # 可重试错误出现后，至多增加一次请求尝试
        max_tokens=1024,    # 每次模型请求的输出预算
        # 沿用教材已验证版本的连接设置，保留 HTTPX 默认连接/代理路径。
        # 初读时跳过这个参数；它不参与计算工具或 Agent 的业务流程。
        http_socket_options=(),
    )
