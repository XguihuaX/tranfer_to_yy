"""运行真实本地 HTTP/WebSocket，并用故障响应核对接口的失败映射。"""
import asyncio
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
from websockets.asyncio.client import connect

import app_gateway
import app_stream
from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent / "verification-logs"
REPORT = HERE.parent / "API-VERIFICATION.json"
checks = []
processes = []
handles = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)
    print("PASS", name, flush=True)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start(module, upstream=None):
    port = free_port()
    env = os.environ.copy()
    if upstream:
        env["ERP_BASE_URL"] = upstream
    handle = (LOGS / f"{module}.log").open("w")
    handles.append(handle)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", f"{module}:app", "--app-dir", str(HERE),
         "--host", "127.0.0.1", "--port", str(port)],
        stdout=handle, stderr=subprocess.STDOUT, env=env,
    )
    processes.append(process)
    base = f"http://127.0.0.1:{port}"
    with httpx.Client(timeout=0.5, trust_env=False) as client:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"{module} 启动失败，见 {handle.name}")
            try:
                if client.get(base + "/openapi.json").status_code == 200:
                    return process, base
            except httpx.RequestError:
                pass
            time.sleep(0.05)
    raise RuntimeError(f"{module} 启动超时")


async def read_events(client, base):
    events, pending = [], {}
    began = time.monotonic()
    first = None
    async with client.stream("GET", base + "/events") as response:
        check("SSE 响应类型", response.headers["content-type"].startswith("text/event-stream"))
        async for line in response.aiter_lines():
            if not line and pending:
                if first is None:
                    first = time.monotonic() - began
                events.append(pending)
                pending = {}
            elif line.startswith("event: "):
                pending["event"] = line[7:]
            elif line.startswith("data: "):
                pending["data"] = json.loads(line[6:])
    return events, first, time.monotonic() - began


async def faults():
    def failure(kind):
        def handler(request):
            if kind == "timeout":
                raise httpx.ReadTimeout("synthetic timeout", request=request)
            if kind == "connection":
                raise httpx.ConnectError("synthetic refused", request=request)
            if kind == "404":
                return httpx.Response(404, json={"detail": "客户不存在"})
            if kind == "500":
                return httpx.Response(500, text="upstream failure")
            if kind == "invalid_json":
                return httpx.Response(200, text="not json")
            if kind == "invalid_model":
                return httpx.Response(200, json={"customer_id": "C001", "amount": "abc"})
            return httpx.Response(200, json=None)
        return handler

    # 传输故障注入，避免真的等待网络超时或修改教学业务端点。
    for kind, status in [("timeout", 504), ("connection", 502), ("404", 404),
                         ("500", 502), ("invalid_json", 502), ("invalid_model", 502)]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(failure(kind)), base_url="http://synthetic"
        ) as upstream:
            app_gateway.app.dependency_overrides[app_gateway.get_client] = lambda: upstream
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app_gateway.app), base_url="http://gateway"
                ) as caller:
                    response = await caller.post("/receivables/query", json={"customer_id": "C001"})
                    check(f"故障注入 {kind} → {status}", response.status_code == status)
            finally:
                app_gateway.app.dependency_overrides.clear()

    # 对生成器主动关闭/取消，核对 finally 确实被执行。
    records = []
    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())
    class Request:
        async def is_disconnected(self):
            return False
    capture = Capture()
    previous = app_stream.logger.level
    app_stream.logger.setLevel(logging.INFO)
    app_stream.logger.addHandler(capture)
    try:
        async with httpx.AsyncClient(base_url="http://unused") as client:
            response = await app_stream.events(Request(), client)
            iterator = response.body_iterator
            await anext(iterator)
            await iterator.aclose()
            check("SSE 提前关闭执行 finally", len(records) == 1)
            response = await app_stream.events(Request(), client)
            iterator = response.body_iterator
            await anext(iterator)
            task = asyncio.create_task(anext(iterator))
            await asyncio.sleep(0)
            task.cancel()
            cancelled = False
            try:
                await task
            except asyncio.CancelledError:
                cancelled = True
            check("SSE 取消信号传播并执行 finally", cancelled and len(records) == 2)
    finally:
        app_stream.logger.removeHandler(capture)
        app_stream.logger.setLevel(previous)


async def network(api, gateway, stream, ws):
    async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
        for cid, minimum, expected in [
            ("C001", 1000, {"customer_id": "C001", "amount": 12800}),
            ("C002", 0, {"customer_id": "C002", "amount": 0}),
            ("C002", 1, None),
        ]:
            direct = await client.get(api + f"/customers/{cid}/receivable", params={"min_amount": minimum})
            relayed = await client.post(gateway + "/receivables/query", json={"customer_id": cid, "min_amount": minimum})
            check(f"真实 HTTP GET 与转接结果一致 {cid}/{minimum}",
                  direct.status_code == relayed.status_code == 200 and direct.json() == relayed.json() == expected)
        for base in [api, gateway]:
            response = await client.post(base + "/receivables/query", json={"customer_id": "C999"})
            check(f"未知客户 404 {base}", response.status_code == 404 and response.json()["detail"] == "客户不存在")
            for value in ["1000", True, -1, 1.5]:
                response = await client.post(base + "/receivables/query", json={"customer_id": "C001", "min_amount": value})
                check(f"POST 非法门槛被拒绝 {base}/{value!r}", response.status_code == 422)
            for body in [{"customer_id": " C001 "}, {"customer_id": "abc"},
                         {"customer_id": "C001", "min_amout": 1}]:
                response = await client.post(base + "/receivables/query", json=body)
                check(f"输入模型拒绝 {base}/{body}", response.status_code == 422)
        response = await client.get(api + "/customers/C001/receivable", params={"min_amount": -1})
        check("GET 负门槛 422", response.status_code == 422)
        response = await client.post(api + "/customers/C001/receivable")
        check("方法不匹配 405", response.status_code == 405)

        events, first, duration = await read_events(client, stream)
        check("SSE 七条事件与顺序", [e["event"] for e in events] ==
              ["progress", "result", "progress", "failed", "progress", "result", "done"])
        check("SSE 保留金额零与批次统计", events[5]["data"]["data"]["amount"] == 0 and events[6]["data"]["processed"] == 3)
        check("SSE 第一条先于完整响应到达", first < duration - 0.3)
        async with client.stream("GET", stream + "/events") as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    break
        followup = await client.get(stream + "/openapi.json")
        check("真实流提前断开后服务可用", followup.status_code == 200)
        check("SSE/WS 演示 HTML 可访问", all([
            (await client.get(stream + "/")).status_code == 200,
            (await client.get(ws + "/")).status_code == 200,
        ]))

    uri = ws.replace("http://", "ws://") + "/ws"
    async with connect(uri) as socket:
        for message, kind, amount in [
            ({"customer_id": "C001"}, "result", 12800),
            ({"customer_id": "C999"}, "failed", None),
            ({"customer_id": "C002"}, "result", 0),
            ({"customer_id": "C002", "min_amount": 1}, "result", None),
            ({"customer_id": "C001", "min_amount": True}, "failed", None),
        ]:
            await socket.send(json.dumps(message))
            data = json.loads(await socket.recv())
            condition = data["type"] == kind
            if kind == "result":
                condition &= data["data"] is None if amount is None else data["data"]["amount"] == amount
            check(f"WebSocket 消息 {message}", condition)
        await socket.send("not json")
        check("WebSocket 非 JSON 失败消息", json.loads(await socket.recv())["type"] == "failed")
        await socket.send('{"customer_id":"C002"}')
        check("WebSocket 输入失败后继续查询", json.loads(await socket.recv())["data"]["amount"] == 0)
        await socket.send("quit")
        await socket.wait_closed()
        check("WebSocket 正常关闭 1000", socket.close_code == 1000)
    async with connect(uri) as socket:
        await socket.send('{"customer_id":"C001"}')
        check("WebSocket 新连接可重新查询", json.loads(await socket.recv())["data"]["amount"] == 12800)
    await faults()


def main():
    LOGS.mkdir(exist_ok=True)
    try:
        upstream_process, api = start("app_api")
        _, gateway = start("app_gateway", api)
        _, stream = start("app_stream", api)
        _, ws = start("app_ws", api)
        env = {**os.environ, "ERP_BASE_URL": api}
        sync = subprocess.run([sys.executable, str(HERE / "sync_client.py")], env=env,
                              text=True, capture_output=True, check=True)
        check("同步脚本完整运行", "C999 HTTP 错误 404" in sync.stdout and "12800" in sync.stdout)
        asyncio.run(network(api, gateway, stream, ws))
        upstream_process.terminate()
        upstream_process.wait(timeout=5)
        with httpx.Client(timeout=5, trust_env=False) as client:
            response = client.post(gateway + "/receivables/query", json={"customer_id": "C001"})
            check("真实上游停止 → 502", response.status_code == 502)
            events = asyncio.run(read_after_stop(stream))
            check("上游停止后 SSE 三项失败并结束", [e["event"] for e in events] ==
                  ["progress", "failed", "progress", "failed", "progress", "failed", "done"])
        REPORT.write_text(json.dumps({
            "date": "2026-10-22", "python": sys.version.split()[0],
            "packages": {name: importlib.metadata.version(name) for name in
                         ["fastapi", "pydantic", "uvicorn", "httpx", "websockets", "starlette"]},
            "passed": len(checks), "checks": checks,
            "scope": "教材合成数据与本机接口验证；不计为用户练习或真实 ERP 接入",
        }, ensure_ascii=False, indent=2) + "\n")
        print(f"完成 {len(checks)} 项检查：{REPORT}", flush=True)
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        for handle in handles:
            handle.close()


async def read_after_stop(base):
    async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
        events, _, _ = await read_events(client, base)
        return events


if __name__ == "__main__":
    main()
