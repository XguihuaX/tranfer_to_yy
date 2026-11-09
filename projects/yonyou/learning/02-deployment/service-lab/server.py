import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DATA_FILE = Path(__file__).resolve().parent / "data" / "balances.json"
logger = logging.getLogger("query-service")


class QueryHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if not path.startswith("/receivables/"):
            self.send_json(404, {"error": "route_not_found"})
            return
        customer_id = path.removeprefix("/receivables/")
        # 每次读取使文件故障可复现；真实项目按业务需要选择存储方式。
        try:
            balances = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.exception("event=data_read_failed")
            self.send_json(500, {"error": "data_unavailable"})
            return
        if customer_id not in balances:
            self.send_json(404, {"error": "customer_not_found"})
            return
        self.send_json(200, {
            "customer_id": customer_id,
            "amount": balances[customer_id],
            "currency": "CNY",
        })

    def log_message(self, fmt, *args):
        logger.info("client=%s %s", self.client_address[0], fmt % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if os.environ.get("QUERY_CURRENCY") != "CNY":
        raise SystemExit("配置错误：请设置 QUERY_CURRENCY=CNY")
    host = os.environ.get("HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PORT", "8028"))
        if not 1 <= port <= 65535:
            raise ValueError("port out of range")
    except ValueError:
        raise SystemExit("配置错误：PORT 必须是 1–65535 的整数")
    # 绑定失败会在启动阶段报错；不要把它混同为请求返回 500。
    server = HTTPServer((host, port), QueryHandler)
    logger.info("event=start host=%s port=%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("event=stop reason=keyboard_interrupt")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
