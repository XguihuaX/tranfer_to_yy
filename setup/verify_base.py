"""Check the actual course in the shared environment; no external model requests."""
import asyncio
import importlib.metadata
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "yonyou"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)
    print("PASS", message, flush=True)


async def check_api():
    import httpx

    sys.path.insert(0, str(PROJECT / "learning" / "01-python-api" / "api-lab"))
    from app_api import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://course.invalid",
        trust_env=False,
    ) as client:
        response = await client.get("/customers/C001/receivable")
        require(response.status_code == 200 and response.json()["amount"] == 12800,
                "course FastAPI endpoint returns C001 amount 12800")
        response = await client.get("/customers/C999/receivable")
        require(response.status_code == 404, "course endpoint handles a missing customer")


def check_model_adapter():
    import httpx
    from langchain_openai import ChatOpenAI

    def reply(request):
        return httpx.Response(200, json={
            "id": "local-check", "object": "chat.completion", "created": 0,
            "model": "local-check", "choices": [{"index": 0,
                "message": {"role": "assistant", "content": "local-ok"},
                "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    with httpx.Client(transport=httpx.MockTransport(reply), trust_env=False) as client:
        model = ChatOpenAI(
            model="local-check", api_key="fixture-not-a-real-key",
            base_url="https://fixture.invalid/v1", http_client=client,
            use_responses_api=False, max_retries=0,
        )
        require(model.invoke("check").text == "local-ok",
                "LangChain and OpenAI adapter accept a local simulated response")


def main():
    require(sys.version_info[:2] == (3, 12), "Python version is 3.12")
    print("Interpreter:", sys.executable)
    for line in (ROOT / "setup" / "requirements-base.txt").read_text().splitlines():
        if "==" in line and not line.startswith("#"):
            name, expected = line.split("==", 1)
            actual = importlib.metadata.version(name)
            require(actual == expected, f"{name} == {expected} (installed {actual})")

    # Disable optional tracing for this local environment check.
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    mvp = PROJECT / "learning" / "03-llm-tools" / "mvp"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    # Call run_local explicitly: a user's later MODE change must not cause an API call here.
    result = subprocess.run(
        [sys.executable, "-B", "-c", "from main import run_local; run_local()"],
        cwd=mvp, env=env, text=True, encoding="utf-8", capture_output=True, check=True,
    )
    require("multiply(12, 3) → 36" in result.stdout and "add(36, 8) → 44" in result.stdout,
            "course MVP local tool results are 36 and 44")
    asyncio.run(check_api())
    check_model_adapter()

    database = PROJECT / "learning" / "08-database" / "ch01" / "erp_ch01.db"
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        require(connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
                "course SQLite database is readable and intact")
    finally:
        connection.close()
    print("Base environment check passed. No external model API was called.")


if __name__ == "__main__":
    main()
