import asyncio
import json
import logging
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from app_gateway import get_client, lifespan
from domain import CustomerNotFoundError
from erp_client import UpstreamError, UpstreamTimeoutError, fetch_receivable

app = FastAPI(title="应收进度 SSE", lifespan=lifespan)
logger = logging.getLogger("receivable.stream")



# 一条事件由空行结束；data 内部的内容用 JSON 编码。
def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/events")
async def events(
    request: Request,
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
):
    async def generate():
        try:
            for customer_id in ["C001", "C999", "C002"]:
                # 对端已经离开时，不再开始下一项查询。
                if await request.is_disconnected():
                    return
                # 先交出进度事件，再等待取数，不必等整批完成。
                yield sse("progress", {"customer_id": customer_id})
                await asyncio.sleep(0.2)
                try:
                    result = await fetch_receivable(client, customer_id)
                    # Pydantic 模型先转字典，再由 sse 编码成事件文本。
                    yield sse("result", {"data": result.model_dump() if result else None})
                # 已知单项失败发为事件，继续下一项；不吞掉取消信号。
                except (CustomerNotFoundError, UpstreamError, UpstreamTimeoutError) as error:
                    yield sse("failed", {"customer_id": customer_id, "detail": str(error)})
            # processed 是尝试处理的项数，并不表示三项全部成功。
            yield sse("done", {"processed": 3})
        finally:
            # 正常结束、异常或取消时均收尾；共享客户端由应用关闭。
            logger.info("SSE 查询生成器已结束")

    # 框架逐步读取生成器，持续发送响应体，不先收集成完整列表。
    return StreamingResponse(
        generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"}
    )


@app.get("/", response_class=HTMLResponse)
def page():
    # 演示页接收事件；done 时主动关闭，避免自动重连后重复执行整批。
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
    <title>SSE 应收演示</title><h1>SSE 应收演示</h1>
    <button id="start">开始一批查询</button><button id="stop">停止接收</button><pre id="out"></pre>
    <script>
    let source;
    const out = document.querySelector('#out');
    document.querySelector('#start').onclick = () => {
      if (source) source.close();
      out.textContent = '';
      source = new EventSource('/events');
      for (const name of ['progress', 'result', 'failed', 'done']) {
        source.addEventListener(name, event => {
          out.textContent += name + ': ' + event.data + '\\n';
          if (name === 'done') source.close();
        });
      }
      source.onerror = () => {
        out.textContent += '连接中断，可点击开始重新查询\\n';
        source.close();
      };
    };
    document.querySelector('#stop').onclick = () => { if (source) source.close(); };
    </script></html>"""
