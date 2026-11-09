# 02-08 完成一次可交接的小变更

> 教材已准备。示例为本机学习服务，用户学习状态单独记录。

## 本章怎么读 { #reading-guide }

**主线 3／3。** 先看 §1 的目标与 §3 的执行路线，再按 §2、§4–7 操作；完整源码保留在 §3 折叠区，不要求逐行重学 HTTP。§8 是 Linux 迁移查阅。

完成后可回到 [模块目录](index.md)，或按需进入 [Docker 选学](09-docker-compose.md#reading-guide)。

## 本章问题、目标与前置

前几章的命令如何成为一项完整工作？本章任务是：给查询助手增加合成客户 C003 的余额，保存修改，启动服务验证，再模拟数据文件缺失并修复，最后交付能让别人复现的说明。

前置为 [Git](03-git-changes.md)、[环境](05-environment-and-permissions.md)、[服务排查](06-processes-and-ports.md)。约 40–50 分钟。Python 3.9+，仅标准库；Git 2.28+；无需数据库、网络账号或第三方包。先看 §1 的验收目标与 §3 的执行路线，再开始操作；完整源码可按需展开。

**Windows cmd差异：** 本章完整交付练习按Mac流程执行。Windows路径与虚拟环境改用实际项目位置和 `.venv\Scripts\python.exe`；环境变量用set，不能照抄Mac的 `变量=值 命令`、mktemp或cp。配置与解释器对照见[02-05](05-environment-and-permissions.md)，端口检查对照见[02-06](06-processes-and-ports.md)。


## 1. 先确定这次验收什么

数据沿用合成应收余额：C001=12800 元（20000 应收减 7200 已核销收款），C002=0。新增 C003=500 元，假设有效应收 500、尚未回款、无调整，币种 CNY，数据截止 2026-10-31。

验收应覆盖：C003 返回 200 与金额 500；C999 返回 404；文件缺失时业务查询返回 500，恢复后返回 200；停止后该实例不再监听。health 能响应只是其中一项，不能替代查询核对。

我们用一个标准库 HTTPServer 服务降低安装负担。它是单进程、顺序处理的教学程序，没有登录认证，适合观察启动与失败路径；实际业务服务会使用项目选定的框架和部署机制。

## 2. 从原样本复制出独立交付副本

**Mac 终端 A，起始目录不限，保留本终端的 delivery_root：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment"
delivery_root=$(mktemp -d "$PWD/delivery.XXXXXX")
cp service-lab/server.py service-lab/README.md service-lab/.gitignore service-lab/.env.example "$delivery_root/"
cp -R service-lab/data "$delivery_root/data"
cd "$delivery_root"
pwd
git init -b main
git config --local user.name "Delivery Learner"
git config --local user.email "delivery@example.invalid"
git config --local commit.gpgsign false
git add server.py README.md .gitignore .env.example data/balances.json
git commit -m "Add runnable query service"
```

目录形状如下，后续 venv 和 logs 是本地运行生成物：

```text
delivery.随机字符/
├── server.py
├── README.md
├── .gitignore
├── .env.example
└── data/
    └── balances.json
```

`.gitignore` 内容是 `.venv/`、`.env`、`logs/`、`__pycache__/`、`*.pyc`，每条独占一行；`.env.example` 记录 QUERY_CURRENCY、HOST、PORT 和后续 Docker 的 HOST_PORT 示例。本章用显式环境变量启动，不自动加载该文件。

初始 balances.json 完整内容：

```json
{"C001": 12800, "C002": 0}
```

## 3. 完整服务怎样走完一次请求？

代码的入口 main 先检查币种和端口，再绑定监听。GET 请求交给 do_GET：health 直接响应；查询路由读取数据，找到客户返回金额，找不到返回 404，文件读取失败返回 500。数据路径绑定脚本所在目录，解决 02-01 的启动位置问题。

`send_json` 统一把字典编码为 UTF-8 JSON，设置内容长度并写入响应；`log_message` 把访问记录交给 logging，默认输出到 stderr。这里不重讲 01 的全部 HTTP 机制，重点观察它们在启动、日志和文件故障中的作用。

<details markdown="1">
<summary>展开完整 server.py（与配套运行文件一致）</summary>

```python
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
```

</details>

## 4. 修改、检查和提交

**终端 A，当前在刚创建的 delivery 副本中：**

```sh
printf '{"C001": 12800, "C002": 0, "C003": 500}\n' > data/balances.json
python3 -m json.tool data/balances.json
git diff -- data/balances.json
git add data/balances.json
git diff --staged
git commit -m "Add synthetic C003 balance"
git log --oneline -2
```

json.tool 检查 JSON 语法并格式化显示；它不判断金额是否符合业务。diff 应只增加 C003=500，提交说明对应本次变更。不要因为程序能解析，就省略金额与业务假设核对。

## 5. 明确解释器、配置和启动位置

**终端 A，delivery 副本：**

本机按 02-05 已验证的 Python 3.12.14 创建独立环境，避开当前 Homebrew 3.14.4 的 ensurepip 错误。先单独创建；若失败，保存报错并停在此步，不能继续执行不存在的环境。

```sh
"/Users/liujunhong/Documents/ChatGPT/用友/.venv-docs/bin/python" -m venv .venv
```

创建成功后执行：

```sh
.venv/bin/python --version
.venv/bin/python -m pip check
mkdir -p logs
QUERY_CURRENCY=CNY HOST=127.0.0.1 PORT=8028 .venv/bin/python server.py > logs/service.log 2>&1 &
delivery_pid=$!
ps -p "$delivery_pid" -o pid,command
```

启动前应结束自己在 02-06 运行的服务，确认 8028 空闲；若被其他人的服务占用，换一个确认空闲的端口，并同步修改后续 curl 地址。不要终止未知占用者。

**终端 B，Mac 本机客户端，任意目录：**

```sh
curl -i --max-time 3 http://127.0.0.1:8028/health
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C003
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C999
```

预期分别为 200/ok、200/金额500、404/customer_not_found。服务使用 HTTP/1.0 响应，响应头版本不影响本章这次请求验证。

**终端 A，delivery 副本：**

```sh
tail -n 10 logs/service.log
git status --short
```

日志应包含启动、三个请求及其状态；status 应干净，虚拟环境和日志都被忽略。若 status 显示源码变化，先看 diff，别直接忽略它。

## 6. 主动制造一次可修复故障

**终端 A，仍在自己的 delivery 副本；不要对 service-lab 原样本执行：**

```sh
mv data/balances.json data/balances.json.saved
```

**终端 B，Mac 客户端：**

```sh
curl -i --max-time 3 http://127.0.0.1:8028/health
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C003
```

第一条仍是 200，第二条是 500/data_unavailable。说明进程和网络路径正常，但业务所需数据不可用。

**终端 A 查看证据并恢复：**

```sh
grep -n 'data_read_failed' logs/service.log
tail -n 20 logs/service.log
mv data/balances.json.saved data/balances.json
```

应看到数据读取失败及 FileNotFoundError 的调用位置。服务每次请求都读取文件，因此恢复后无需重启；B 再请求 C003 应返回 200/500元。最后 A 运行 `git status --short` 应仍干净。修复是否完成以业务请求结果判断，不能只看文件名改回来了。

## 7. 停止与交接

**终端 A，确认保存的 PID 仍对应自己的服务：**

```sh
ps -p "$delivery_pid" -o pid,command
kill -TERM "$delivery_pid"
wait "$delivery_pid"
lsof -nP -iTCP:8028 -sTCP:LISTEN
```

wait 因信号终止返回非零属于预期；最后若无其他服务接管该端口，应无监听记录。B 再 curl 应连接失败。若其他服务接管了端口，应核对 PID，不能把别人的响应记为本次进程仍运行。

交接说明应包含具体可复现信息，而不是只写“已经部署”。在副本中新建 HANDOFF.md，填写下表，实际值以本次操作为准：

| 内容 | 本例如何填写 |
| --- | --- |
| 变更与版本 | 增加合成 C003=500；`git rev-parse --short HEAD` 的实际输出 |
| 文件位置 | 本次 pwd 输出的绝对目录，关键入口 server.py |
| 环境 | 实际 Python 版本；仅标准库；venv 的重建命令 |
| 配置与启动 | QUERY_CURRENCY=CNY、HOST=127.0.0.1、PORT=8028；§5 启动命令 |
| 验收 | C003=200/500元、C999=404、缺数据=500、恢复=200；实际检查时间 |
| 日志与停止 | logs/service.log；识别本实例 PID 后 TERM 并检查端口 |
| 当前状态 | 已停止，或仍运行及其 PID；不能混写 |
| 已知范围 | 本机学习服务；不含认证或远程生产托管 |

填好后可 `git add HANDOFF.md` 并提交说明文档；说明中所记录的服务代码版本使用填写前的代码提交标识即可。原样本 README 仍描述 C001 等基础情况，不要把 README 当作已记录新增客户验收的凭据。

## 8. 迁移到 Linux 时，哪些必须重新确认？

本节独立于 Mac 实操。取得授权服务器后，按 [02-07](07-ssh-and-transfer.md) 上传源码和数据到远程 `~/receivable-lab`，在远程建立新的 .venv；不复制 Mac 的虚拟环境。

**已登录的 Linux Shell，目标源码已上传：**

```sh
cd ~/receivable-lab
python3 --version
python3 -m venv .venv
QUERY_CURRENCY=CNY HOST=127.0.0.1 PORT=8028 .venv/bin/python server.py
```

远程创建 venv 也需先确认命令成功，再启动；这里不能假定远程 Python 与 Mac 相同。再用另一个远程 Shell 发 curl，核对该机器的权限、端口和文件。如果需要从 Mac 请求，使用上一章的隧道。长期托管另按目标 systemd/平台配置工作目录、解释器、环境、日志和重启策略。本次没有远程主机，以上步骤未实际运行，不能把 Mac 验收记成 Linux 部署成功。

## 9. 可选练习

A. health=200，查询=500，先查端口还是数据日志？B. pip check 成功能证明 C003 金额正确吗？C. 交接时要保留哪个版本信息？

??? note "参考答案与推理"
    A：已收到响应，优先看业务查询日志与数据文件，除非证据表明请求到了错误实例。B：不能，它检查包依赖一致性，金额必须通过业务数据和请求核对。C：记录实际代码提交标识、配置、解释器及验收结果，才能让别人重现同一版本。

## 本章回顾与检查清单

一次交付把代码版本、运行条件和验证结果接起来；每个结论对应观察到的证据。

- [ ] 能在独立副本完成修改、提交、启动和请求验证。
- [ ] 能用日志解释缺文件故障并恢复，确认停止的实例。
- [ ] 能写出别人可照着执行的交接说明。

## 阅读中产生的答疑

暂无；实际操作从 §2 准备副本开始，§3 先看执行路线，源码按需展开。

## 来源与后续

[Python HTTPServer 文档](https://docs.python.org/3/library/http.server.html)与[venv 文档](https://docs.python.org/3/library/venv.html)支持本例运行方式；具体输出以作者验证记录为准。后续选学：[02-09 Docker 与 Compose](09-docker-compose.md)；[目录](index.md)。
