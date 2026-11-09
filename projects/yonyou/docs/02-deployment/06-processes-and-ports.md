# 02-06 服务、进程与端口：把“访问不到”拆开检查

> 教材已准备，2026-10-31。本机实操使用标准库查询服务；Linux 命令单独标注。

## 本章怎么读 { #reading-guide }

**主线 2／3。** 已知道进程号、端口和前台运行时，§1–2可快速略过；当前从§3的后台运行与日志继续，再看§4怎样定位失败。每次讲一个操作，先说明作用和结果，命令细节按需展开。§5–6的资源观察与Linux服务管理留作查阅，完整例子和练习均保留。

本章需要理解后台运行、日志重定向和端口检查的作用；不要求默写所有参数。使用AI辅助操作时，适量练习说清目标和检查输出，例如要求保留日志并验证一次业务请求，而非仅看到PID就认定启动成功。

下一步：[02-08 综合交付练习](08-delivery-lab.md#reading-guide)。SSH 按需查 [02-07](07-ssh-and-transfer.md#quick-read)。

## 本章问题、目标与前置

程序启动后，浏览器却访问不到，究竟是没启动、地址不对，还是业务处理失败？本章沿一个服务建立“进程 → 监听地址与端口 → HTTP 请求 → 数据”的排查路线。前置为 [02-05 的环境配置](05-environment-and-permissions.md) 和 01 的 HTTP 基础。约 35–45 分钟。

配套服务在 `learning/02-deployment/service-lab`，Python 3.9+，无第三方依赖。完整源码和交接流程在 [02-08](08-delivery-lab.md)，本章先聚焦运行行为。

**Windows cmd差异：** 本章主线在Mac运行。Windows可用 `netstat -ano` 查看端口及PID、`tasklist` 查看进程；若要筛选示例端口，可用 `netstat -ano | findstr :8028` 并核对地址及状态列。Mac的lsof、ps参数不直接搬到cmd。前台服务在两边都可用Ctrl+C中断。


## 1. 文件变成运行中的进程

`server.py` 是磁盘上的代码；执行它后，操作系统创建一个**进程**，即一次运行中的程序实例。每个进程有 **PID**（进程编号）、用户、内存等属性。同一个文件可以启动多次，形成不同进程。

Web 服务要接收请求，还要监听网络地址和端口。地址决定在哪个网络入口接收，端口区分同一机器上的不同服务。本例默认 `127.0.0.1:8028`。

- `127.0.0.1` 是当前机器的回环地址，只供本机访问。
- `0.0.0.0` 用在服务绑定时，表示监听本机全部 IPv4 接口；客户端通常仍使用具体 IP 或域名访问。
- 监听全部接口不自动解决防火墙、路由或访问权限问题。我们的无认证练习服务默认只绑定回环地址。

## 2. 两个本机终端，一条请求路线

**终端 A：Mac 本机，服务端。起始目录不限：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/service-lab"
QUERY_CURRENCY=CNY python3 server.py
```

应看到 `event=start host=127.0.0.1 port=8028`，终端暂时不返回提示符。这叫**前台运行**：当前终端正在等待服务结束。

**终端 B：同一台 Mac，HTTP 客户端，任意目录：**

```sh
curl -i --max-time 3 http://127.0.0.1:8028/health
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C001
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C999
```

`curl` 是发送请求的命令行客户端；`-i` 同时显示响应头，`--max-time 3` 限制总等待时间。预期状态分别是 200、200、404；C001 的正文为 `{"customer_id": "C001", "amount": 12800, "currency": "CNY"}`，C999 为 `{"error": "customer_not_found"}`。Date 等响应头会随运行时间变化。

请求路线始终是：**B 的 curl → 本机 8028 的 Python 服务 → 数据文件 → HTTP 响应回 B**。终端 A 同时出现访问记录。`/health` 只说明该进程能响应，不检查数据文件；后面会看到它健康时，业务查询仍可能失败。

完成前台观察后，在 **终端 A 按 Ctrl-C** 停止服务；Python 捕获中断、关闭监听，回到 Shell。

## 3. 前台、后台与 PID 怎么联系？

**终端 A，仍在 service-lab；先确认刚才前台服务已停止：**

```sh
mkdir -p logs
QUERY_CURRENCY=CNY python3 server.py > logs/service.log 2>&1 &
service_pid=$!
ps -p "$service_pid" -o pid,ppid,%cpu,%mem,command
```

这组命令先理解三件事：创建日志目录；启动服务并把两路输出写到日志、放到后台；记录PID并查看进程。`>`会覆盖同名日志文件，`2>&1`让错误输出跟随正常输出写入该文件，末尾独立的`&`表示后台运行。需要逐个符号解释时再展开，不必先背整条命令。后台运行本身不保证关闭终端后仍继续运行，远程会话与长期托管在后续章节讨论。

结尾的 `&` 让命令在后台运行，Shell 马上返回提示符。`$!` 是刚启动的后台作业对应 PID，本例直接启动 Python，记录后用于检查和停止。`ps` 显示 PID、父进程 PPID、CPU/内存比例和启动命令。

但得到 PID 不等于启动成功：程序可能随后因缺配置或端口冲突退出。还要看日志和请求结果：

```sh
tail -n 10 logs/service.log
curl -i --max-time 3 http://127.0.0.1:8028/health
```

**终端 B，Mac 本机任意目录：**

```sh
lsof -nP -iTCP:8028 -sTCP:LISTEN
```

`lsof` 列出打开的文件与网络端点，这里按 TCP 8028 和监听状态筛选；`-nP` 保留数字 IP/端口，避免额外名称解析。应能看到 Python 和 PID。PID 应与 A 记录的进程一致。

**如果是在 Linux 服务器终端，使用当地可用工具：**

```sh
ss -ltnp 'sport = :8028'
```

`ss` 查看套接字，`-l` 监听、`-t` TCP、`-n` 数字、`-p` 进程信息；权限不足时部分进程信息可能不可见。此命令不是让你在 Mac 上照抄。

## 4. 三种常见故障的发生位置

### 4.1 配置缺失：服务还没监听就退出

**终端 A，在 service-lab；已有后台服务仍可保留。启动一个故意缺配置的新实例：**

```sh
env -u QUERY_CURRENCY python3 server.py
```

`env -u` 只从这一次命令的环境移除指定变量。预期立即报告配置错误，新进程不会进入监听阶段。因此此时 curl 若仍成功，可能请求到的是之前的后台进程，不能用它证明刚才的新实例启动成功。

### 4.2 端口占用：两个服务争用同一入口

**终端 A，保留 §3 的后台实例，再启动第二个：**

```sh
QUERY_CURRENCY=CNY python3 server.py
```

应报告 `Address already in use`，错误编号在 macOS 和 Linux 上可能不同。先用 lsof 确认占用者，而不是直接终止所有 Python。若确实需要两个实例，可给第二个不同端口，例如命令前加 `PORT=8030`，客户端也相应改地址。本章不要求额外启动它。

### 4.3 服务已停止：连接失败，尚无 HTTP 状态

**终端 A，确认 ps 显示的仍是自己的练习进程后停止：**

```sh
ps -p "$service_pid" -o pid,command
kill -TERM "$service_pid"
wait "$service_pid"
```

TERM 请求目标进程终止，`wait` 等待这个子进程结束；因信号终止时 wait 返回非零是正常现象。本例未自定义 TERM 清理处理，操作系统会回收监听端口。与 Ctrl-C 路径不同，不保证出现 `event=stop` 日志。不要把强制 KILL 当作普通首选。

**终端 B：**

```sh
curl -i --max-time 3 http://127.0.0.1:8028/health
echo $?
```

若该端口没有别的服务，应连接失败（curl 常见退出码 7），没有 HTTP 200/404/500。相反，404 是已连上并收到 HTTP 响应，只是资源未找到。curl 默认收到 404 也可能退出码为 0；加 `--fail` 可让 HTTP 错误对应非零退出码，但会改变正文显示行为。

<details markdown="1">
<summary>按需展开：资源观察与 Linux 服务管理（§5–6）</summary>

## 5. CPU、内存和磁盘先看什么？

进程存在但响应慢时，先做小范围观察。**本机任意目录，目标 PID 仍有效时：** `ps -p "$service_pid" -o pid,%cpu,%mem,command` 查看该服务；`top` 动态查看全机进程，按 q 退出；`df -h .` 看当前目录所在磁盘可用空间；`du -sh logs` 要在 service-lab 中执行，看日志目录占用。

CPU 高、内存大或磁盘紧张都需要与时间和请求对照。一次数值不能直接证明泄漏或性能瓶颈。本例请求很短，CPU 接近 0 正常；日志写不进磁盘可能导致新的诊断问题。

## 6. Linux 上谁负责长期管理服务？

后台 `&` 只是 Shell 启动方式，不负责开机启动或失败重启。很多 Linux 发行版使用 **systemd** 管理长期服务；一个 `.service` 文件定义执行用户、工作目录、命令、环境和重启策略。它相当于把手工启动所需条件写成可管理配置。

例如部署负责人已配置名为 `receivable-demo.service` 的系统服务时，**在对应 Linux 机器**可查询：

```sh
systemctl status receivable-demo.service
journalctl -u receivable-demo.service -n 50 --no-pager
```

journalctl 读取 systemd 日志；访问可能需要该机器授予的日志权限。这里没有远程主机，也没有安装这个服务单元，不能将这些命令当成本机已可执行的操作。配置和启动由目标环境的部署流程决定；macOS 的服务管理机制不同。

</details>

## 7. 可选练习与排错顺序

A. curl 返回 404，是否表示端口没监听？B. 新启动命令报缺配置，但 curl 成功，最可能漏查什么？C. 0.0.0.0 是客户应该输入的固定访问地址吗？

??? note "参考答案与推理"
    A：不是，已收到 HTTP 响应，应继续判断路由或客户是否存在。B：可能旧进程仍在监听，核对 PID、启动日志和端口对应关系。C：它主要表达服务绑定所有 IPv4 接口；客户端使用实际可达的 IP 或域名，本机练习用 127.0.0.1。

排查主线为：启动命令有没有退出 → 日志有什么 → 目标进程是否还在 → 地址与端口是否监听 → 客户端是否连上 → HTTP 状态和业务数据是否正确。

## 本章回顾与检查清单

- [ ] 能用两个终端说清一次请求的客户端和服务端。
- [ ] 能把端口、PID、启动日志对应起来，只停止自己的实例。
- [ ] 能区分连接失败、404、500，以及 health 与业务查询的范围。

## 阅读中产生的答疑

暂无；建议先完成 §2，再读后台运行和故障部分。

## 来源与后续

[Python HTTPServer](https://docs.python.org/3/library/http.server.html)用于本机教学服务；该标准库服务没有本例所需之外的生产托管能力。[systemd.service 官方说明](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)对应 Linux 管理概念，2026-10-31 核对。ps/lsof/kill 依据本机手册和运行结果。主线下一步：[02-08 综合交付练习](08-delivery-lab.md#reading-guide)。远程操作按需查 [02-07 SSH 与传输](07-ssh-and-transfer.md#quick-read)；[目录](index.md)。
