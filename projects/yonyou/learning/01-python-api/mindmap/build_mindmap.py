"""生成 01 全模块的概念地图；仅用标准库，直接写入现代 XMind JSON 包。"""
import json
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/01-python-api/assets/01-Python-API-概念地图.xmind"
BASE = "http://127.0.0.1:8765/01-python-api/"


def node(title, *children, note=None, link=None, folded=False):
    item = {"id": uuid.uuid4().hex, "class": "topic", "title": title}
    if children:
        item["children"] = {"attached": [node(c) if isinstance(c, str) else c for c in children]}
    if note:
        item["notes"] = {"plain": {"content": note}}
    if link:
        item["href"] = BASE + link
    if folded:
        item["branch"] = "folded"
    return item


def chapter(title, *children, file):
    return node(title, *children, link=file, folded=True)


sheets = []


def sheet(title, root_title, branches, note):
    root = node(root_title, *branches, note=note)
    root["structureClass"] = "org.xmind.ui.map.unbalanced"
    colors = ["#287D8E", "#5363A4", "#BC7840", "#56815B", "#8B6097", "#B25D68", "#54788F"]
    root["style"] = {"id": uuid.uuid4().hex, "type": "topic", "properties": {
        "svg:fill": "#243B53", "fo:color": "#FFFFFF", "fo:font-family": "PingFang SC",
        "fo:font-size": "22pt", "fo:font-weight": "bold", "shape-class": "org.xmind.topicShape.roundedRect"}}
    for index, branch in enumerate(branches):
        branch["style"] = {"id": uuid.uuid4().hex, "type": "topic", "properties": {
            "svg:fill": colors[index % len(colors)], "fo:color": "#FFFFFF",
            "fo:font-size": "16pt", "fo:font-weight": "bold", "fo:font-family": "PingFang SC",
            "shape-class": "org.xmind.topicShape.roundedRect", "line-color": colors[index % len(colors)]}}
    item = {"id": uuid.uuid4().hex, "class": "sheet", "title": title, "rootTopic": root,
            "theme": {"id": uuid.uuid4().hex, "title": "清晰概念",
                      "map": {"type": "map", "properties": {"svg:fill": "#FFFFFF"}},
                      "subTopic": {"type": "topic", "properties": {
                          "fo:font-family": "PingFang SC", "fo:font-size": "13pt", "fo:color": "#243B53"}}}}
    sheets.append(item)


sheet("00 先看全貌", "01 Python / API\n让另一个程序查到客户欠款", [
    node("① Python：把业务写出来", "输入 C001 → 查询 → 返回 12800", "函数、字典、类型、异常、模块｜详见图 01"),
    node("② 分清两端：谁找谁办事", "客户端主动请求；服务端接收并处理", "HTTPX 发请求；FastAPI 组织服务端处理｜详见图 04"),
    node("③ HTTP + JSON：怎样沟通", "HTTP 约定请求和响应；JSON 表达数据", "字典 → JSON → 传输 → 解析为数据｜详见图 03"),
    node("④ asyncio：等待时怎样安排任务", "await 等当前工作；并发需安排多项任务", "async 不自动并发；gather 组织并发｜详见图 02"),
    node("⑤ 结果怎样到达", "普通 HTTP：一次结果；SSE：逐条推送", "WebSocket：保留连接，双方多次发消息｜详见图 05"),
    node("⑥ 先沿一条线理解", "发请求 → 检查输入 → 查金额 → 返回 → 使用结果", "整套图共 6 页；先看本页，再按疑问展开"),
], "本图覆盖整个大 01 的 01–10 章。节点讲职责与关系，详细例子在其余五页；加号表示可展开，带链接的节点可回教材。合成数据：C001=12800 元、C002=0 元、C999 不存在。导图用于讲概念，不表示用户已经掌握。")


sheet("01 Python｜01–04", "在一个 Python 程序里\n把查询、数据与失败写清楚", [
    chapter("01 函数：输入 → 处理 → 输出",
        node("函数接收实际传入的值", 'query("C001")：传客户编号', "传 balances 整个字典，就不是在传某个编号"),
        node("return：把结果交给调用者", '{"customer_id": "C001", "amount": 12800}', "print：显示信息；不替代返回结果"),
        node("字典：在内存中保存键值对应", 'balances["C001"] → 12800', "字典可保存模拟数据，也可保存从数据库查到的结果"),
        file="01-reading-python.html"),
    chapter("02 类型与参数：约定能传什么",
        node("customer_id: str → 编号应为字符串", "-> int → 返回值应为整数", "普通类型标注本身不自动执行输入校验"),
        node("min_amount: int | None = None", "int | None：允许整数或空值", "= None：省略参数时默认为空；本例表示不筛选"),
        node("单独的 *：后面按参数名传值", 'query("C001", min_amount=1000)', "有默认值的参数仍可省略"),
        node("业务分支由代码决定", "达到门槛 → 返回结果；未达到 → None", "零金额合法；未知客户 → 抛异常"),
        file="02-types-and-contracts.html"),
    chapter("02 字典、类型工具与普通类",
        node("dict：真正保存数据", "使用 result[\"amount\"] 取值", "d[key] 缺键 → KeyError；d.get(key) 默认返回 None"),
        node("TypedDict：描述字典字段", "来自 typing；标注后仍是普通 dict", "字段说明供编辑器与类型检查器使用，不自动校验"),
        node("defaultdict：缺键时生成并保存默认值", "来自 collections；适合汇总与分组", "defaultdict(int) 用 [] 访问缺键 → 保存 0；get 不触发", note="客户查询需要区分未知客户与零金额，不能随意用默认 0 吞掉缺失。collections 是模块，其中还有 Counter、deque 等容器工具。"),
        node("普通 class：组织对象的属性与方法", "__init__：创建实例时初始化属性", "只保存数据也可用类；选择看想使用字典还是对象"),
        file="python-reference.html#dictionaries"),
    chapter("03 异常：失败怎样传到调用者",
        node("异常类 → 某次异常对象", "ValueError：值不合适；TypeError：类型不合适", "LookupError：查找失败的大类；KeyError、IndexError 属于它"),
        node("自定义异常：给业务失败一个名字", "CustomerNotFoundError(LookupError)", "定义新的异常子类；不是创建某次错误对象"),
        node("raise → 抛出；try/except → 捕获", 'raise CustomerNotFoundError("客户不存在")', "except CustomerNotFoundError as error：把这次异常对象命名为 error"),
        node("logger：记录发生了什么", "logger.error 不会自动抛异常或停止函数", "logger.exception 在 except 中记录堆栈；raise 可继续传播"),
        node("保留线索与清理", "raise 新异常 from 原异常：保留原因链", "finally：正常或异常退出时收尾"),
        file="03-errors-and-debugging.html"),
    chapter("04 工程：文件与运行环境",
        node("文件按职责组织", "数据：从哪里取；业务：怎样判断", "入口：怎样启动；import：使用其他模块的定义"),
        node("__name__ == \"__main__\"", "直接运行该文件时，进入启动代码", "被 import 时，这个判断块不执行"),
        node("运行命令", "python file.py：运行文件", 'python -c "代码"：直接执行短代码'),
        node("虚拟环境与依赖", "解释器决定使用哪套 Python 与已安装包", "requirements：列出需要安装的依赖"),
        node("配置与资源", "环境变量：传地址、端口等配置", "with / async with：按约定打开、退出时关闭资源"),
        file="04-modules-and-project.html"),
    node("在统一例子里找位置", "server.py [S1]：业务、字典、类、异常", "client.py / server.py：两份程序各有入口", link="00-one-example.html#first-request"),
], "对应原 01–04 章。带加号的大分支默认收起，可一次只展开一个问题。函数、return/print 等已知内容只做定位。")


sheet("02 异步｜05", "等待时让其他任务有机会执行\n先分清当前任务与其他任务", [
    chapter("① async：定义一种可等待的工作",
        "async def 定义协程函数",
        "调用 f() 通常先得到协程对象，函数体尚未执行",
        "await f() 或安排为任务，才能推进这项工作",
        file="05-async-and-tasks.html"),
    node("② await：本任务等结果", "操作尚未完成时，当前任务暂停", "事件循环可安排其他已就绪的任务", "完成后，本任务恢复并执行 await 后面的语句", note="await 只能等待可等待对象。若操作已经完成，await 可以直接继续，不保证每次都切换。await 不会自行创建另一项工作，也不会让当前任务跳过等待去执行下一行。", folded=True),
    node("③ asyncio：运行和安排这些工作",
        node("事件循环：安排就绪任务继续执行", "本例在一个线程中交替推进多个任务", "多核并行要用其他机制；本例未使用"),
        node("asyncio.run(main())", "脚本入口创建事件循环，运行并收尾", "FastAPI 异步路由里已有循环，直接 await 即可"),
        node("asyncio.sleep(1)", "模拟等网络回复；不阻塞事件循环", "time.sleep(1) 在循环线程里会阻塞其他任务"), folded=True),
    node("④ 顺序与并发：看怎样安排",
        node("顺序：await A(); await B()", "B 在 A 完成后才开始", "A 等 2 秒，B 等 1 秒 → 约 3 秒"),
        node("并发：await gather(A(), B())", "两项被安排执行，等待可重叠", "同样两项 → 约 2 秒，另有少量开销"),
        node("create_task(A())：持有任务对象", "先安排 A，当前任务可继续安排 B", "需要结果时 await task；也可通过 task 请求取消"),
        node("gather 的结果次序", "全部成功时，等齐结果再返回列表", "按传入顺序排列；B 先完成也不自动排第一", note="默认某项失败时，gather 可先传播异常，不自动取消其他仍在执行的项。不能把 gather 概括成任何情况下都等全部结束。"), folded=True),
    node("⑤ 正常、失败、超时、取消",
        "正常完成 → 返回值；执行失败 → 异常",
        node("wait_for(work(), timeout=...)", "到时会请求取消所等待的工作", "等待其响应取消后，本例向调用者抛 TimeoutError"),
        node("task.cancel() → 请求取消", "再 await task，等待其响应与收尾", "通常在等待处收到 CancelledError；它不属于 Exception"),
        "取消客户端的等待，不保证远端服务器同步停止", folded=True),
    node("⑥ 回到实际查询", "client.py [C1] 的 await：等 HTTP 响应", "server.py [S3] 的 await：模拟服务端等待", "client.py [C4/C5]：并发、超时与取消", link="00-one-example.html#extensions", folded=True),
], "对应 05 章。示例假设工作主要耗时在可让出的等待上。短字典取值无需套线程；同步阻塞 I/O 可按需使用 asyncio.to_thread，但那会实际用到线程。")


sheet("03 请求响应｜06", "两个程序怎样交换一次查询\nHTTP 是规则，JSON 是数据格式", [
    node("① 谁发起、谁处理", "客户端：主动发出请求，使用结果", "服务端：接收请求，处理并回复", "同一程序访问上游时，也可以成为客户端", note="客户端和服务端是本次通信里的角色，可以运行在同一台电脑，也可以在不同电脑。浏览器并不是唯一的客户端。", folded=True),
    chapter("② 找到服务，再找到功能",
        node("http://127.0.0.1:8010/receivables/query", "http：通信协议；127.0.0.1：本机地址", "8010：服务监听端口；/receivables/query：功能路径"),
        "同一端口可提供很多路径；只找对端口还不够",
        "?delay=0.4：URL 查询参数，本例只用于模拟等待",
        file="06-http-and-json.html"),
    node("③ 请求：我需要你做什么",
        "方法：例如 GET 查询、POST 提交请求数据",
        "路径参数：/customers/C001 中的 C001",
        "查询参数：?min_amount=1000",
        "请求头：Content-Type 说明请求体格式",
        '请求体：例如 {"customer_id":"C001","min_amount":null}', folded=True),
    node("④ 响应：处理结果是什么",
        "状态码：200 成功；404 未找到；422 输入不符合约定",
        "响应头：说明内容类型等信息",
        '响应体：例如 {"customer_id":"C001","amount":12800}',
        "本例零金额、无筛选结果与客户不存在含义不同", folded=True),
    node("⑤ JSON 与 Python 数据怎样转换",
        node("dict → str → bytes", "json.dumps(result)：得到 JSON 文本", 'text.encode("utf-8")：文本编码为字节'),
        node("str / bytes → Python 数据", "json.loads(payload)：解析 JSON", "JSON 对象 → dict；数组 → list；null → None"),
        "这些转换函数本身没有发送网络请求",
        'type(result) → <class \'dict\'>；type(result).__name__ → dict', folded=True),
    node("⑥ 一次真实往返", "客户端字典 → 编码 JSON → HTTP 请求", "服务端解析、校验 → 查业务数据 → HTTP 响应", "客户端解析 JSON → 自己程序中的新数据", link="00-one-example.html#first-request", note="双方不会跨网络共享同一个 Python 字典对象。网络收发由 HTTP 客户端与服务器软件等配合完成；JSON 只规定数据表示。", folded=True),
], "对应 06 章。GET/POST 的实际业务语义以接口约定为准；POST 并不意味着一定新增数据。教材站是 8765，综合示例服务是 8010。")


sheet("04 接口工具｜07–08", "谁发送、谁接收、谁校验\n把工具放回请求路线", [
    node("① 先认职责", "HTTP：请求与响应的规则", "JSON：请求体、响应体可采用的数据格式", "HTTPX：Python 客户端库，主动发 HTTP 请求", "FastAPI：服务端框架，组织路由与处理", "Pydantic：创建模型时检查字段；Uvicorn：运行服务", folded=True),
    chapter("07 FastAPI：把地址接到函数",
        node('@app.post("/receivables/query")', "登记 HTTP 方法 + 路径 → 处理函数", "请求到达后，框架提取参数并调用路由函数"),
        "路径、查询字符串、请求体：参数的不同来源",
        "路由调用普通业务函数；框架把返回数据生成响应",
        "response_model：声明并校验、筛选成功响应的结构",
        file="07-fastapi-and-pydantic.html"),
    node("07 Pydantic：把约定变成检查",
        "QueryInput：客户编号、最低金额的模型",
        "Field：声明格式、下限等限制",
        "本例 strict=True 拒绝字符串数字与布尔值",
        "extra=forbid 拒绝拼错或多余的字段",
        "本例非法输入 → FastAPI 返回 422，尚未进入业务查询",
        "TypedDict 只说明字典字段；Pydantic 创建模型时执行校验", folded=True),
    chapter("08 HTTPX：主动请求并读取响应",
        node("AsyncClient：持有客户端与连接池", "async with：复用客户端并在退出时关闭", "长运行应用可在 lifespan 创建、退出时关闭"),
        node("await client.post(...)：发请求并等响应", "json=字典：编码为 JSON 请求体", "params=字典：放入 URL 查询字符串"),
        node("response：包含状态、头和内容的响应对象", "response.status_code：读状态", "response.text：读文本；response.json()：解析为 Python 数据"),
        "response.raise_for_status()：错误状态转为 HTTPStatusError",
        "httpx.Client：同步用法；httpx.AsyncClient：配合 await",
        file="08-httpx-and-upstream.html"),
    node("失败在哪一层", "连不上服务 → RequestError / ConnectError 等网络异常", "已收到 404 → HTTP 响应；raise_for_status 后成为客户端异常", "收到 JSON 但字段不合约定 → 解析后还需结构检查", "本例业务异常 → HTTPException(404) → 客户端按状态处理", note="HTTPX 的超时可分别限制连接、读取、写入和等待连接池的阶段；不是当然的整个请求总时限。需要总时限可另用 wait_for 等管理。", folded=True),
    node("前面那条路线怎样接起来", "HTTPX 发 C001 → FastAPI 选路由", "Pydantic 检查 → 业务函数查到 12800", "框架返回 JSON → HTTPX 解析 → 调用方使用", "后端访问 ERP 时：本次后端是客户端，ERP 是服务端", link="00-one-example.html#first-request", note="旧 08 章的 Depends 用于把已有客户端交给路由；它是组织代码依赖的方法，不是新的网络协议。综合示例先用独立 client.py 直接调用服务，以便理解两端。", folded=True),
], "对应 07–08 章。先明确各自职责，再展开路由、模型与客户端。依赖注入和生命周期是客户端复用的工程做法，可在普通请求路线理解后回原章。")


sheet("05 持续通信｜09–10", "一次完整结果，还是持续交互\n按需要选择返回方式", [
    node("普通 HTTP：一次查询，一次完整结果", "例如：查 C001 → 收到金额 12800", "适合本次需求只要一个完整结果", "HTTP 连接可以复用；不等于每次响应后都断开 TCP", folded=True),
    chapter("09 流式与 SSE：逐步把内容交出来",
        node("yield：每次交出一项，保留后续执行位置", "return：结束函数，交回最终结果", "async for：逐项读取异步产生的内容"),
        node("StreamingResponse：逐块产生响应内容", "数据在同一次 HTTP 响应中逐步到达", "SSE 是一种有明确事件格式的流式响应"),
        node("SSE 事件格式", "Content-Type: text/event-stream", "event: progress → 事件名；data: ... → 内容", "空行结束一条事件；本例 data 内再使用 JSON"),
        node("本例：一批查询的进度与结果", "progress → result / failed → 下一项 → done", "C999 失败用 failed 事件表达，之后仍查询 C002"),
        node("结束与断开", "本例 done 后客户端主动 close，避免自动重连重复查询", "服务端 finally 清理；断开时管理自己启动的后台任务"),
        file="09-streaming-and-sse.html"),
    chapter("10 WebSocket：同一连接反复双向发消息",
        "建立连接 → 接收消息 → 处理 → 发送消息 → 等下一条",
        "accept / receive_text / send_json / close：本例的基本操作",
        "客户端可反复查询；服务端也可主动推送消息",
        "每条业务消息自己约定字段和成功、失败含义",
        "本例顺序处理消息；双向连接不自动让业务并发",
        file="10-websocket-and-selection.html"),
    node("按需求选一种", "只查一次欠款 → 普通 HTTP", "发起一批后，只需服务端逐步给进度 → SSE", "需要保持连接、双方反复发送业务消息 → WebSocket", "模型流式输出是内容逐步产生；可以用 SSE 或 WebSocket 承载", folded=True),
    node("三个容易混淆的结束动作", "关闭连接：结束这条通信通道", "取消任务：请求停止某项异步工作", "重新连接：新建通道；任务与消息恢复需要另行设计", "关网页或重连，不自动证明远端业务已取消或恢复", folded=True),
    node("在统一例子里观察", "同一个 book.query 负责查金额", "普通 HTTP：[S3]；SSE：[S5]；WebSocket：[S6]", "业务没换，主要变化是结果与消息怎样收发", link="00-one-example.html#extensions"),
], "对应 09–10 章。SSE 的事件流主要是服务端向客户端发送，客户端仍可另外发送 HTTP 请求。WebSocket 通常通过 HTTP 握手建立，随后按 WebSocket 消息通信；不是 HTTPX 的一种写法。")


def walk(topic):
    yield topic
    for child in topic.get("children", {}).get("attached", []):
        yield from walk(child)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    entries = {
        "content.json": sheets,
        "metadata.json": {"creator": {"name": "01 Python/API 教材", "version": "2026-10-27"},
                          "dataStructureVersion": "3", "layoutEngineVersion": "5"},
    }
    manifest = {"file-entries": {name: {} for name in entries}}
    entries["manifest.json"] = manifest
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name, json.dumps(value, ensure_ascii=False, indent=2))
    # 直接回读最终文件，检查标识、结构、全部章链接以及包内清单。
    with zipfile.ZipFile(OUT) as archive:
        assert archive.testzip() is None
        loaded = json.loads(archive.read("content.json"))
        assert len(loaded) == 6
        topics = [topic for page in loaded for topic in walk(page["rootTopic"])]
        assert len({topic["id"] for topic in topics}) == len(topics)
        assert all(topic["title"].strip() for topic in topics)
        links = [topic["href"] for topic in topics if "href" in topic]
        for number in range(1, 11):
            assert any(f"/{number:02}-" in link for link in links), number
        for name in json.loads(archive.read("manifest.json"))["file-entries"]:
            assert name in archive.namelist()
    outline = ["# 01 Python / API：XMind 同步文字提纲", "", "生成日期：2026-10-27。与 XMind 同源；完整讲解仍以教材为准。", ""]
    def describe(topic, depth):
        outline.append("  " * depth + "- " + topic["title"].replace("\n", "："))
        if topic.get("notes"):
            outline.append("  " * (depth + 1) + "- 说明：" + topic["notes"]["plain"]["content"])
        if topic.get("href"):
            outline.append("  " * (depth + 1) + "- 教材：" + topic["href"])
        for child in topic.get("children", {}).get("attached", []):
            describe(child, depth + 1)
    for page in loaded:
        outline.extend(["## " + page["title"], ""])
        describe(page["rootTopic"], 0)
        outline.append("")
    (Path(__file__).parent / "概念地图-文字提纲.md").write_text("\n".join(outline) + "\n")
    report = {"date": "2026-10-27", "sheets": len(loaded), "topics": len(topics),
              "chapter_coverage": list(range(1, 11)), "zip_readback": "passed",
              "unique_topic_ids": True, "ui_open": "pending"}
    (Path(__file__).parent / "VERIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(OUT)
    print(f"PASS：{len(loaded)} 张图，{len(topics)} 个节点，01–10 章链接齐全，ZIP 回读有效")


if __name__ == "__main__":
    build()
