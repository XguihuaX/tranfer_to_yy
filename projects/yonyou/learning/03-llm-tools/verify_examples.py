"""作者核对：本地HTTP模拟传输 + 真正本机stdio；不调用外部模型。"""
import asyncio
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
MODULE = Path(__file__).resolve().parent
LAB = MODULE / "lab"
sys.path.insert(0, str(LAB))

import httpx
from langchain.messages import AIMessage, AIMessageChunk, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from pydantic import ValidationError

from business import get_balance, search_customers
from intent import QueryIntent, execute_intent
from model_config import make_model
from query_tools import lookup_balance

checks = []


def passed(name):
    checks.append(name)
    print("PASS", name, flush=True)


def load_script(name):
    spec = importlib.util.spec_from_file_location("lesson_" + name[:2], LAB / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reply(text="", tool=None):
    message = {"role": "assistant", "content": text}
    if tool:
        name, args = tool
        message["tool_calls"] = [{"id": "call_fixture", "type": "function", "function": {
            "name": name, "arguments": json.dumps(args, ensure_ascii=False),
        }}]
    return {"id": "fixture", "object": "chat.completion", "created": 0,
            "model": "fixture-model", "choices": [{"index": 0, "message": message,
            "finish_reason": "tool_calls" if tool else "stop"}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}}


def simulated_model(sequence, retries=0):
    requests = []
    iterator = iter(sequence)

    def handler(request):
        requests.append(json.loads(request.content))
        result = next(iterator)
        if isinstance(result, int):
            return httpx.Response(result, json={"error": {"message": "fixture error", "type": "fixture"}})
        return httpx.Response(200, json=result)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = ChatOpenAI(model="fixture-model", api_key="fixture-not-a-real-key",
                       base_url="https://fixture.invalid/v1", http_client=client,
                       use_responses_api=False, max_retries=retries, stream_usage=False)
    return model, requests, client


for cid, amount in [("C001", 12800), ("C002", 0), ("C003", 500)]:
    row = get_balance(cid)
    assert row["amount"] == amount and row["currency"] == "CNY" and row["as_of"] == "2026-11-08"
assert "amount" not in get_balance("C999")
assert len(search_customers("海星")["matches"]) == 2
assert search_customers("星河")["matches"][0]["customer_id"] == "C003"
passed("business:balances_zero_missing_ambiguity_source_date")

for payload in [{"customer_id": "bad"}, {"customer_id": 1}]:
    try:
        lookup_balance.invoke(payload)
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid tool argument accepted")
assert execute_intent(QueryIntent(action="clarify"))["status"] == "need_clarification"
for payload in [dict(action="bad"), dict(action="query_balance", customer_id="bad"),
                dict(action="query_balance", customer_id="C001", amount=12)]:
    try:
        QueryIntent(**payload)
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid intent accepted")
try:
    execute_intent(QueryIntent(action="query_balance"))
except ValueError:
    pass
else:
    raise AssertionError("missing customer accepted")
passed("validation:tool_schema_intent_extra_fields_execution_precondition")

with patch.dict(os.environ, {}, clear=True):
    try:
        make_model()
    except ValueError as exc:
        assert "LLM_API_KEY" in str(exc)
    else:
        raise AssertionError("missing settings accepted")
with patch.dict(os.environ, {"LLM_API_KEY": "fixture", "LLM_MODEL": "fixture-model",
                           "LLM_BASE_URL": "https://fixture.invalid/v1", "LLM_API_PROTOCOL": "responses"}, clear=True):
    model = make_model()
    assert model.use_responses_api is True and model.max_retries == 1
passed("configuration:missing_settings_and_explicit_protocol")

for protocol, expected_path in [("chat", "/v1/chat/completions"), ("responses", "/v1/responses")]:
    seen = []

    def connection_handler(request):
        seen.append(request.url.path)
        if protocol == "chat":
            payload = reply("fixture connected")
        else:
            payload = {
                "id": "resp_fixture", "object": "response", "created_at": 0,
                "status": "completed", "model": "fixture-model",
                "output": [{"id": "msg_fixture", "type": "message", "status": "completed",
                            "role": "assistant", "content": [{"type": "output_text",
                            "text": "fixture connected", "annotations": []}]}],
                "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30,
                          "input_tokens_details": {"cached_tokens": 0},
                          "output_tokens_details": {"reasoning_tokens": 0}},
            }
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(connection_handler)) as client:
        settings = {"LLM_API_KEY": "fixture", "LLM_MODEL": "fixture-model",
                    "LLM_BASE_URL": "https://fixture.invalid/v1", "LLM_API_PROTOCOL": protocol}
        with patch.dict(os.environ, settings, clear=True), patch(
            "model_config.ChatOpenAI", side_effect=lambda **kwargs: ChatOpenAI(http_client=client, **kwargs)
        ):
            assert make_model().invoke("fixture").text == "fixture connected"
        assert seen == [expected_path]
    passed("configuration:" + protocol + ":actual_factory_and_simulated_transport")

for filename, sequence in [
    ("01_call.py", [reply("需要查询数据")]),
    ("02_messages.py", [reply("收到C001"), reply("C001"), reply("请查询C001的未收余额")]),
    ("03_structured.py", [reply(tool=("QueryIntent", {"action": "query_balance", "customer_id": "C001"}))]),
]:
    script = load_script(filename)
    model, requests, client = simulated_model(sequence)
    try:
        with patch.object(script, "make_model", return_value=model), contextlib.redirect_stdout(io.StringIO()) as output:
            script.main()
        if filename.startswith("01"):
            assert "需要查询数据" in output.getvalue() and len(requests) == 1
        if filename.startswith("02"):
            assert len(requests[1]["messages"]) == 4 and requests[2]["messages"][-1]["content"].endswith("帮我看一下C001的欠款")
        if filename.startswith("03"):
            assert "12800" in output.getvalue() and requests[0]["tools"]
    finally:
        client.close()
    passed(filename + ":actual_main_with_simulated_HTTP")

manual = load_script("04_tool_loop.py")
for call, expected in [(("lookup_balance", {"customer_id": "C001"}), "ok"),
                       (("lookup_balance", {"customer_id": "C999"}), "not_found"),
                       (("lookup_balance", {"customer_id": "bad"}), "invalid_arguments"),
                       (("unknown", {}), "unknown_tool")]:
    model, requests, client = simulated_model([reply(tool=call), reply("fixture final")])
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            answer, messages = manual.run_tool_loop(model, "fixture question")
        result = next(m for m in messages if isinstance(m, ToolMessage))
        assert json.loads(result.content)["status"] == expected and result.tool_call_id == "call_fixture"
        assert requests[1]["messages"][-2]["role"] == "assistant" and requests[1]["messages"][-1]["role"] == "tool"
    finally:
        client.close()
    passed("tool_loop:" + expected + ":execution_and_matching_return")

model, requests, client = simulated_model([reply(tool=("lookup_balance", {"customer_id": "C001"}))] * 2)
try:
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            manual.run_tool_loop(model, "fixture", max_calls=2)
        except RuntimeError:
            assert len(requests) == 2
        else:
            raise AssertionError("loop not bounded")
finally:
    client.close()
passed("tool_loop:model_call_limit")

agents = load_script("05_agent.py")
model, requests, client = simulated_model([
    reply(tool=("find_customers", {"query": "星河制造"})),
    reply(tool=("lookup_balance", {"customer_id": "C003"})),
    reply("500 CNY，2026-11-08，合成数据"),
])
try:
    with patch.object(agents, "make_model", return_value=model), contextlib.redirect_stdout(io.StringIO()) as output:
        agents.main()
    assert len(requests) == 3 and "500 CNY" in output.getvalue()
    assert any(m.get("role") == "tool" and "C003" in str(m.get("content")) for m in requests[1]["messages"])
finally:
    client.close()
passed("agent:real_framework_two_tools_and_final_state")

model, requests, client = simulated_model([reply(tool=("find_customers", {"query": "海星"})), reply("请选择北京或上海")])
try:
    state = agents.make_agent(model).invoke({"messages": [{"role": "user", "content": "查海星"}]})
    assert "请选择" in state["messages"][-1].text and len(requests) == 2
finally:
    client.close()
passed("agent:scripted_ambiguity_clarification_route")

model, requests, client = simulated_model([reply(tool=("lookup_balance", {"customer_id": "C001"}))] * 10)
try:
    try:
        agents.make_agent(model).invoke({"messages": [{"role": "user", "content": "fixture"}]}, config={"recursion_limit": 3})
    except GraphRecursionError:
        pass
    else:
        raise AssertionError("agent recursion not bounded")
finally:
    client.close()
passed("agent:graph_step_limit")

runtime = load_script("06_runtime.py")


class AsyncFixture:
    async def ainvoke(self, messages):
        return AIMessage(content="fixture async")


class TimeoutFixture:
    async def ainvoke(self, messages):
        raise TimeoutError("fixture timeout")


with contextlib.redirect_stdout(io.StringIO()) as output:
    assert asyncio.run(runtime.ask_with_deadline(AsyncFixture(), "fixture")).text == "fixture async"
    assert asyncio.run(runtime.ask_with_deadline(TimeoutFixture(), "fixture")) is None
assert "等待超时" in output.getvalue()
passed("runtime:async_success_and_timeout_classification")


class StreamFixture:
    def stream(self, messages):
        yield AIMessageChunk(content="部分文字")
        raise RuntimeError("fixture stream broke")


with contextlib.redirect_stdout(io.StringIO()) as output:
    try:
        runtime.stream_text(StreamFixture(), "fixture")
    except RuntimeError:
        pass
    else:
        raise AssertionError("stream error swallowed")
assert "中途结束" in output.getvalue()
passed("runtime:partial_stream_not_marked_complete")

model, requests, client = simulated_model([503, reply("recovered")], retries=1)
try:
    assert model.invoke("fixture").text == "recovered" and len(requests) == 2
finally:
    client.close()
passed("runtime:one_sdk_retry_means_two_attempts")


async def verify_mcp():
    parameters = StdioServerParameters(command=sys.executable, args=[str(LAB / "mcp_server.py")])
    async with Client(parameters) as client:
        assert "lookup_balance" in [item.name for item in (await client.list_tools()).tools]
        ok = await client.call_tool("lookup_balance", {"customer_id": "C001"})
        assert not ok.is_error and ok.structured_content["amount"] == 12800
        missing = await client.call_tool("lookup_balance", {"customer_id": "C999"})
        assert not missing.is_error and missing.structured_content["status"] == "not_found"
        invalid = await client.call_tool("lookup_balance", {"customer_id": "bad"})
        assert invalid.is_error


asyncio.run(verify_mcp())
passed("mcp:actual_stdio_discovery_success_missing_invalid_and_cleanup")

versions = {}
from importlib.metadata import version
for package in ["langchain", "langchain-core", "langchain-openai", "langgraph", "pydantic", "mcp", "openai"]:
    versions[package] = version(package)
report = {"date": "2026-11-08", "python": sys.version.split()[0], "versions": versions,
          "checks": checks, "paid_model_requests": 0,
          "scope": "Local scripted HTTP transport and actual local MCP stdio; not real provider/model acceptance."}
(MODULE / "VERIFICATION-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print("All", len(checks), "checks passed; no external model calls.")
