# 01-07 至 01-10：应收接口练习

这是教材配套的本机合成示例。C001=12800 元、C002=0 元，未知客户失败；低于已设置的最低金额返回 None，HTTP JSON 中表现为 null。运行环境已经在本轮准备，复现时按下面安装。

## 环境与依赖

所有命令从“用友”项目根目录运行。验证使用 Python 3.12.14，完整依赖固定在 requirements.lock.txt。

```sh
python3.12 -m venv learning/01-python-api/.venv-api
learning/01-python-api/.venv-api/bin/python -m pip install -r learning/01-python-api/api-lab/requirements.lock.txt
```

已有项目的 `.venv-docs/bin/python` 也是 Python 3.12，可以用它替代第一条命令中的 python3.12。虚拟环境未激活也可直接使用下面的完整解释器路径。

## 文件与章节

| 文件 | 主讲章节 | 用途 |
| --- | --- | --- |
| domain.py | 07，沿用 02/03 | 原业务规则与客户不存在异常 |
| models.py | 07 | 输入/结果校验模型 |
| app_api.py | 07 | 本地接口，同时作为后章的模拟 ERP |
| sync_client.py | 08 | 同步调用脚本 |
| erp_client.py | 08 | 共用异步取数与错误分类 |
| app_gateway.py | 08 | 连接生命周期、依赖注入与 HTTP 错误映射 |
| app_stream.py | 09 | SSE 事件流与浏览器演示页 |
| app_ws.py | 10 | WebSocket 消息循环与浏览器演示页 |
| verification.py | 教材验证 | 本机集成检查和故障注入，结束后关闭自建服务 |
| audit_textbook.py | 教材验证 | 构建后的站内链接、锚点、示例与折叠内容核对 |

## 启动

07 的模拟 ERP 保持运行：

```sh
learning/01-python-api/.venv-api/bin/python -m uvicorn app_api:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8001
```

新终端按当前章节选择一个调用方，无需全开：

```sh
# 08，交互接口页：http://127.0.0.1:8002/docs
learning/01-python-api/.venv-api/bin/python -m uvicorn app_gateway:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8002

# 09，演示页：http://127.0.0.1:8003/
learning/01-python-api/.venv-api/bin/python -m uvicorn app_stream:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8003

# 10，演示页：http://127.0.0.1:8004/
learning/01-python-api/.venv-api/bin/python -m uvicorn app_ws:app --app-dir learning/01-python-api/api-lab --host 127.0.0.1 --port 8004
```

停止当前终端中的服务使用 Ctrl+C。启动失败先查端口占用、解释器、--app-dir。8001 的自动接口页在 http://127.0.0.1:8001/docs；8765 一直是教材站。

调用方默认读取 `ERP_BASE_URL=http://127.0.0.1:8001`，可在启动命令前设置为另一个本机模拟地址。变量由启动阶段读取，修改后重启调用方。

## 核对结果

```sh
curl -i 'http://127.0.0.1:8001/customers/C001/receivable?min_amount=1000'
curl -i -X POST 'http://127.0.0.1:8002/receivables/query' -H 'Content-Type: application/json' -d '{"customer_id":"C002","min_amount":1}'
curl -N 'http://127.0.0.1:8003/events'
```

依次预期为 200/C001=12800，200/null，七条 SSE 事件（其中 C999 失败、C002 成功为 0、最后 done）。WebSocket 页面可在一个连接内连续查询 C001/C999/C002，最后正常关闭。具体解释、故障场景和练习均在对应正文。

## 复现教材验证

```sh
learning/01-python-api/.venv-api/bin/python learning/01-python-api/api-lab/verification.py
.venv-docs/bin/mkdocs build --strict
learning/01-python-api/.venv-api/bin/python learning/01-python-api/api-lab/audit_textbook.py
```

verification.py 使用自动分配的本机端口，避免占用手工练习的 8001–8004，正常或失败退出时都会关闭它启动的进程。超时、错误 HTTP、非法 JSON 与模型错误使用 HTTPX MockTransport 注入；正常查询、上游停止、SSE 和 WebSocket 使用真实本地网络。

结果保存在上一层 API-VERIFICATION.json、TEXTBOOK-VERIFICATION.json；整合说明见上一层 REVIEW-2026-10-22.md。教材验证与用户阅读、练习证据分开记录。
