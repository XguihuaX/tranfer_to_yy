# 02-09 Docker 与 Compose：把运行条件写成文件（选学）

> 教材已准备。需要 Docker 客户端、Compose 插件（`docker compose` 命令）与可访问的引擎；本次引擎未运行，容器启动步骤未实测。

## 本章怎么读 { #reading-guide }

**后续选学。** 先读 §1、§3–5，建立镜像、容器、端口、环境和挂载的关系；§6–7 的启动流程等引擎可用时再做。全文及配置示例均保留。

本章不计入当前 2–3 小时主线；返回 [模块目录](index.md)。

## 本章问题、目标与前置

同一服务交给另一台机器，除了源码，还要告诉它 Python 版本、启动命令和配置。Docker 把一部分运行条件包装成镜像，Compose 把容器启动关系写成文件。本章只部署前面的查询服务，不额外引入数据库或缓存。

前置为 [02-06 监听与端口](06-processes-and-ports.md)、[02-08 完整服务](08-delivery-lab.md)。约 30–40 分钟，可先理解配置，再在具备引擎时执行。本章为选学，不是当前主线的前置条件。

**Windows cmd差异：** Docker引擎可用且处于Linux容器模式时，本章docker compose子命令共用；宿主机路径与变量语法按cmd改写。例如先执行 `set "HOST_PORT=8029"`，再执行 `docker compose config`；结束后用 `set "HOST_PORT="` 清除，不使用Mac的命令前赋值写法。


## 1. 镜像、容器、Dockerfile 与 Compose 怎样连接？

**镜像 image** 是包含基础环境和应用文件的模板。**容器 container** 是基于镜像启动的一次隔离运行实例，有自己的进程和网络环境。停止或删除容器与删除源代码是不同操作。

**Dockerfile** 写镜像如何构建，例如选择 Python 基础镜像、复制代码、指定默认命令。**Compose** 用 YAML 文件描述启动配置，例如用哪个构建目录、注入哪些环境变量、映射哪些端口和挂载哪些数据。

```text
server.py + data + Dockerfile → build → 镜像
镜像 + Compose 运行配置 → up → 容器里的 Python 服务
```

Mac 上 Linux 容器通常由 Docker Desktop 等提供的 Linux 虚拟化环境承载；只装一个 docker 命令行工具不代表引擎已启动。引擎负责真正构建和运行容器。

## 2. 先确认前提，再读配置

**Mac 本机终端，起始目录不限：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/service-lab"
docker --version
docker compose version
docker info
```

前两条检查客户端与 Compose；第三条需要连上当前 Docker 上下文指向的引擎。本次环境前两项可用，引擎连接失败，因此作者仅验证配置解析，没有运行 build/up。若你此时也没有引擎，先读完本章即可；后续按你选用的 Docker 安装方式启动引擎，再继续。不修改上下文来碰运气。

本章复用 service-lab 原样本（C001、C002），不是 02-08 随机副本中的 C003。若要部署新增客户版本，应将相同构建文件加入那个版本并明确构建目录。

## 3. Dockerfile 怎样装入服务？

service-lab 中完整 Dockerfile：

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY server.py ./server.py
COPY data/ ./data/
ENV PYTHONUNBUFFERED=1
EXPOSE 8028
CMD ["python", "server.py"]
```

FROM 指定 Python 3.12 的精简基础镜像；WORKDIR 设置后续镜像操作及默认运行目录；COPY 从构建目录复制文件到镜像。程序没有第三方依赖，所以无需 pip 安装。

ENV 设置镜像中的默认环境变量；PYTHONUNBUFFERED 让输出及时出现。EXPOSE 描述应用使用的端口，**它不会自动把端口发布到宿主机**。CMD 是默认启动命令，币种等应用配置在 Compose 中提供。

`python:3.12-slim` 标签可能随基础镜像更新变化，本章用它表达可读的学习配置；需要固定交付环境时，应记录实际镜像摘要和构建版本，而不是把标签当作永远不变的字节内容。

同目录的 `.dockerignore`：

```text
.git
.venv
.env
logs
__pycache__
*.pyc
```

它排除不需要送入构建上下文的文件。与 `.gitignore` 类似但用途不同：一个控制构建输入，一个控制 Git 未跟踪文件的提示与添加。环境中的本地 .venv 不应复制进 Linux 镜像。

## 4. Compose 怎样接通端口、环境和数据？

完整 compose.yaml：

```yaml
services:
  query:
    build: .
    ports:
      - "127.0.0.1:${HOST_PORT:-8029}:8028"
    environment:
      QUERY_CURRENCY: CNY
      HOST: 0.0.0.0
      PORT: "8028"
    volumes:
      - ./data:/app/data:ro
```

query 是服务名，build 的点表示当前项目构建目录。端口这一行分成 **宿主绑定地址 : 宿主端口 : 容器端口**：本机 127.0.0.1 的 8029 转到容器 8028。`${HOST_PORT:-8029}` 表示读取插值变量 HOST_PORT，没有或为空时用 8029。

容器里的服务设置 HOST=0.0.0.0，是为了接收从容器网络接口送来的请求；如果容器内只监听自己的 127.0.0.1，宿主发布端口通常无法接到它。宿主却仍绑定 127.0.0.1，限制为本机访问。两处地址属于不同网络环境。

volumes 这一项其实是 **bind mount（绑定挂载）**：把宿主项目的 ./data 映射到容器 /app/data，`ro` 表示容器只读。挂载后，容器看到的是宿主数据，镜像 COPY 进去的同路径数据暂时被遮住。更改宿主文件会影响后续查询，不能以“重新构建镜像”解释这种变化。

Docker 也有由引擎管理、按名称使用的 **volume（数据卷）**，常用于独立保存持久数据；本例没有创建命名卷，避免把源数据与另一个存储位置混淆。

## 5. .env 插值不等于自动传入容器

在这个 Compose 项目旁写 `.env`，例如内容 `HOST_PORT=8039`，Compose 可读取它来替换 YAML 中的 `${HOST_PORT:-8029}`。但文件中的任意变量不会因此自动全部出现在容器进程中。

传给容器的是 `environment` 显式列出的变量，或另外配置的 `env_file`。本例 environment 固定传入 CNY、0.0.0.0、8028；如果你在本机 `.env` 写 `HOST=127.0.0.1`，它不会覆盖这里的字面值。

先不创建文件，也能观察插值。**Mac 终端，service-lab：**

```sh
docker compose -p receivable-demo config
HOST_PORT=8039 docker compose -p receivable-demo config
```

第二份输出应把 published 端口改为 8039，而容器 PORT 仍是 8028。这是配置解析，通常无需运行中的引擎。Shell 同名变量可能优先于 `.env`，所以排错时先查看最终 config，而非只盯某一个配置文件。

## 6. 具备引擎后，启动与验证

**前提：docker info 成功、宿主 8029 空闲。Mac 终端 A，service-lab：**

```sh
docker compose -p receivable-demo build
docker compose -p receivable-demo up -d
docker compose -p receivable-demo ps
docker compose -p receivable-demo logs --tail 30 query
```

第一次 build 可能下载基础镜像，需要网络。`-p receivable-demo` 固定本练习的 Compose 项目名，后续所有命令保持一致。up 创建并启动容器，`-d` 在后台运行；ps 看状态，logs 看进程输出。容器显示 Up 还不足以证明查询正确，继续请求。

**Mac 终端 B，HTTP 客户端，任意目录（未覆盖 HOST_PORT 时）：**

```sh
curl -i --max-time 3 http://127.0.0.1:8029/health
curl -i --max-time 3 http://127.0.0.1:8029/receivables/C001
```

预期 200/ok 与 200/12800元。若本机同时有 02-06 的 8028 服务，8029 请求才是本章的映射入口，不要把两者响应混记。

**Mac 终端 A，service-lab：**

```sh
docker compose -p receivable-demo exec query python -c 'import os; print(os.environ["HOST"], os.environ["PORT"])'
docker compose -p receivable-demo exec query python -c 'from urllib.request import urlopen; print(urlopen("http://127.0.0.1:8028/health").read().decode())'
```

exec 在已运行容器内执行命令。第二条的 127.0.0.1 属于容器自身，因此访问 8028；它不是宿主 8029。容器默认没有必须预装的 curl，我们复用 Python 标准库验证。

## 7. 排错和结束

| 现象 | 对应检查 |
| --- | --- |
| Cannot connect to Docker daemon | 客户端未连上引擎；应用尚未启动 |
| 宿主端口已分配 | 查看占用者，必要时改 HOST_PORT 并同步客户端地址 |
| 容器立即退出 | compose logs 查看环境、文件、启动错误 |
| 容器 Up，宿主请求失败 | 核对 config 的端口映射与容器内部监听地址 |
| health 成功，查询 500 | 检查挂载后的 data 文件及日志；镜像里的副本可能被挂载遮住 |

**Mac 终端 A，service-lab，结束本项目：**

```sh
docker compose -p receivable-demo down
```

down 停止并移除本项目容器和默认网络；不删除宿主 ./data，也不默认删除镜像。此时 8029 应不再服务本例。不要使用全局清理命令来代替停止一个明确的教学项目。

## 8. 可选练习

A. 宿主映射为 8039:8028，容器里检查自己要访问哪个端口？B. 为什么修改宿主 data 后不构建也可能改变查询结果？C. 只有 EXPOSE 8028 就能让宿主访问吗？

??? note "参考答案与推理"
    A：容器内部服务仍是 8028；宿主客户端用 8039。B：本例绑定挂载了宿主目录，进程每次从挂载位置读取。C：不能，EXPOSE 是端口说明，需要发布映射并让进程监听容器可达接口。

## 本章回顾与检查清单

- [ ] 能说清 Dockerfile 构建镜像、Compose 配置容器启动的分工。
- [ ] 能画出宿主 8029 → 容器 8028 的请求路线。
- [ ] 能区分 .env 插值与进程环境、bind mount 与镜像内文件。
- [ ] 能用配置、状态、日志和请求逐步验证，并只结束本项目。

## 阅读中产生的答疑

暂无。没有引擎时可以先读配置与推演；本章未要求启动系统服务。

## 来源与后续

2026-10-31 核对 [Docker 端口发布](https://docs.docker.com/engine/network/port-publishing/)、[Compose 变量插值](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)、[服务配置参考](https://docs.docker.com/reference/compose-file/services/)。作者验证范围见 VERIFICATION.md：配置解析与容器运行分开记录。至此可回到 [模块目录](index.md)，按实际学习情况选择答疑或综合练习。
