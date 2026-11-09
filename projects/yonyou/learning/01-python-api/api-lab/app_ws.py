import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app_gateway import lifespan
from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable
from models import QueryInput

app = FastAPI(title="应收 WebSocket", lifespan=lifespan)
logger = logging.getLogger("receivable.websocket")


@app.websocket("/ws")
async def query_socket(websocket: WebSocket):
    await websocket.accept()  # 接受连接后，才开始收发业务消息。
    try:
        while True:
            # 本例顺序处理：这一项查完并回复后，才接收下一条。
            text = await websocket.receive_text()
            # quit 是本例约定的正常关闭命令，不参与 JSON 解析。
            if text == "quit":
                await websocket.close(code=1000)
                return
            try:
                # 连接建立不代表消息合法，每条 JSON 都要单独校验。
                query = QueryInput.model_validate_json(text)
            except ValidationError:
                await websocket.send_json({"type": "failed", "detail": "请发送合法的查询 JSON"})
                continue  # 本条输入失败，不关闭连接；仍可继续发合法查询。
            try:
                # 继续复用 08 章的客户端与错误分类，不重复实现取数。
                result = await fetch_receivable(
                    websocket.app.state.erp_client,
                    query.customer_id,
                    min_amount=query.min_amount,
                )
                await websocket.send_json({
                    "type": "result", "data": result.model_dump() if result else None
                })
            # 已建立连接后，业务失败用消息表达，不再修改 HTTP 状态。
            except (CustomerNotFoundError, UpstreamError, UpstreamTimeoutError) as error:
                await websocket.send_json({"type": "failed", "detail": str(error)})
    # 收发时发现对端断开，退出当前连接的循环。
    except WebSocketDisconnect:
        logger.info("浏览器已断开 WebSocket")
    finally:
        # 当前连接的收尾；共享客户端继续留给其他连接使用。
        logger.info("WebSocket 消息循环结束")


@app.get("/", response_class=HTMLResponse)
def page():
    # 按连接状态启停按钮；重新连接时不会自动重发旧查询。
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
    <title>WebSocket 应收演示</title><h1>WebSocket 应收演示</h1>
    <button id="connect">连接 / 重连</button><input id="customer" value="C001" aria-label="客户编号">
    <button id="send" disabled>查询</button><button id="close" disabled>正常关闭</button>
    <pre id="out"></pre><script>
    let socket;
    const out = document.querySelector('#out');
    const send = document.querySelector('#send');
    const close = document.querySelector('#close');
    const connect = document.querySelector('#connect');
    connect.onclick = () => {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(scheme + '://' + location.host + '/ws');
      connect.disabled = true;
      socket.onopen = () => { send.disabled = close.disabled = false; out.textContent += '已连接\\n'; };
      socket.onmessage = event => { out.textContent += event.data + '\\n'; };
      socket.onerror = () => { out.textContent += '连接错误，检查服务是否启动\\n'; };
      socket.onclose = event => {
        send.disabled = close.disabled = true; connect.disabled = false;
        out.textContent += '已关闭，code=' + event.code + '\\n';
      };
    };
    send.onclick = () => socket.send(JSON.stringify({customer_id: document.querySelector('#customer').value}));
    close.onclick = () => { socket.send('quit'); send.disabled = close.disabled = true; };
    </script></html>"""
