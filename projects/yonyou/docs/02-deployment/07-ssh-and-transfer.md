# 02-07 连接另一台机器：SSH 与文件传输

> 教材已准备，2026-10-31。本章是远程操作说明；当前没有可验证的远程 Linux 主机，未实际登录。

## 本章怎么读 { #reading-guide }

**快速复习／远程操作查阅。** 已会登录，先看下方连接点；完整登录、传输、隧道和会话管理都在折叠区。没有远程机器也可先阅读，实际连接前替换占位值。

主线继续 [02-08 综合交付练习](08-delivery-lab.md#reading-guide)；不必先完成远程练习。

## 本章问题、目标与前置

本机服务已经能运行，客户提供一台 Linux 机器后，怎样把操作迁过去，同时始终知道自己在哪？本章解释 SSH 连接、身份、两端路径与会话生命周期。前置为 [02-06](06-processes-and-ports.md) 的进程、端口与监听地址。完整阅读约 25–35 分钟；快速复习约 5–10 分钟。

本章地址 `linux-lab.example.invalid`、用户 `learner`、端口 `2222` 均为**占位示例，不能直接连接**。真正实操时先取得获准使用的主机、账号、SSH 端口、认证方式与主机指纹，再整体替换示例。没有服务器也可以先推演每条命令在哪执行，不需要租用资源。

## 快速读：会 SSH 登录后，只补这几个连接点 { #quick-read }

登录基础可跳过。本章先用 5–10 分钟确认下面几项，传输与隧道等完整命令按需展开。

- SSH 登录后，命令在远程机器执行；远程 `127.0.0.1` 指远程自己。Mac 上访问同样地址仍访问 Mac，除非已明确建立端口转发。
- `ssh -p` 指 SSH 端口，`scp -P` 用大写 P；scp 的 `用户@主机:路径` 属于远程，没有该前缀的一侧通常属于执行命令的本机。
- 普通后台 `&` 不保证 SSH 断开后持续运行；临时会话可用 nohup/tmux，长期托管按目标环境的服务管理方式处理。
- 首次连接核对主机指纹；公钥用于配置登录，私钥留在本机。上传项目时复制源码和数据，在 Linux 上重建虚拟环境。

已有实际服务器需求时再展开操作步骤；当前不用为了这一章准备一台服务器。

<details markdown="1">
<summary>完整查阅：登录、文件传输、隧道与会话管理</summary>

**Windows cmd差异：** 安装并启用OpenSSH客户端后，ssh/scp的主要参数相同；本地路径换成实际Windows路径，变量写法用 `%变量名%`。登录远程Linux后使用的是远程Shell，仍按正文的Linux命令操作。


## 1. SSH 改变了哪一层？

SSH 是用于加密远程登录和执行命令的协议；本机 `ssh` 是客户端，远程机器需要运行 SSH 服务端。连接成功后，终端窗口仍在你的 Mac 上，但其中的新 Shell 在远程 Linux 上运行。

```text
Mac 终端窗口 → 本机 ssh 客户端 → 远程 SSH 服务端 → 远程 Shell
```

于是输入 `pwd` 看的是远程目录，`python3` 启动的是远程 Python。Mac 上安装过的包不会因此自动出现在远程机器。

## 2. 建立连接：先确认机器，再证明用户身份

**本机 Mac 终端 A，任意目录；以下仅为替换占位后的命令形式：**

```sh
ssh -p 2222 learner@linux-lab.example.invalid
```

`learner` 是远程用户名，域名是远程机器地址，`-p` 是 SSH 服务端口，与我们查询服务的 8028 没有关系。

连接涉及两种不同身份。**主机身份验证**帮助你确认连接的是预期服务器；首次连接会展示主机密钥指纹，应与管理员通过可信途径提供的指纹核对。接受后通常记录到本机 `~/.ssh/known_hosts`。以后密钥意外变化会警告，需要先查明服务器是否重装或地址是否变化，不应默认关闭检查。

**用户认证**证明你有权以 learner 登录，可能用密码，也可能用密钥。密钥分为私钥和公钥：私钥保留在本机，公钥可交给管理员安装到目标账号。私钥口令用于保护本地私钥，和远程账号密码不是同一个东西。

如目标环境要求新建专用密钥，可先确认目标文件尚不存在，再按以下形式生成；本次教材不会代你执行或覆盖已有密钥：

```sh
ssh-keygen -t ed25519 -f ~/.ssh/yonyou_lab_ed25519 -C "learning-lab"
```

生成 `.pub` 是公钥；登录形式为 `ssh -i ~/.ssh/yonyou_lab_ed25519 -p 2222 learner@linux-lab.example.invalid`。不要把私钥当作需要上传的项目文件。

## 3. 登录后先建立位置感

**前提：终端 A 已成功登录远程 Linux。以下命令都在远程执行：**

```sh
hostname
whoami
pwd
python3 --version
mkdir -p ~/receivable-lab
cd ~/receivable-lab
```

hostname 显示机器名，whoami 显示当前用户，pwd 显示远程目录。远程 `~` 表示远程 learner 的主目录，例如 `/home/learner`；它不是 Mac 的 `/Users/liujunhong`。

本例在远程自己的主目录建立项目目录，不需要假设对 `/opt` 等系统路径有写权限。部署目录由实际环境确定，后续所有命令要与选定路径一致。

## 4. 上传和下载时，两个路径属于谁？

保持终端 A 的远程会话。**另开终端 B，仍是 Mac 本机 Shell**，进入本地例子：

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/service-lab"
scp -P 2222 server.py learner@linux-lab.example.invalid:~/receivable-lab/
scp -P 2222 -r data learner@linux-lab.example.invalid:~/receivable-lab/
```

scp 从源复制到目标。没有 `主机:` 前缀的 `server.py`、`data` 属于执行命令的 Mac；冒号后路径属于远程。`-r` 复制目录。注意 **ssh 用小写 `-p` 指端口，scp 用大写 `-P`**；scp 的小写 `-p` 有保留时间和权限等其他含义。

这里复制源码和数据，不复制 Mac 的 `.venv`；虚拟环境与解释器路径、平台有关，应在远程重建。第一次上传使用新建目录；已有部署要先查看版本和文件，避免把复制命令当作完整的发布策略。

**回到终端 A，远程 Linux 的 `~/receivable-lab`：**

```sh
ls
python3 -m venv .venv
QUERY_CURRENCY=CNY .venv/bin/python server.py
```

前提是远程有 Python 3.9+ 和 venv 支持；缺少时按该环境的软件管理流程准备，不能从 Mac 验证结果推断远程已安装。预期启动日志与上一章一致。

## 5. 远程 localhost 是谁？

默认服务监听远程 `127.0.0.1:8028`。你在 Mac 浏览器打开同样地址，只会访问 Mac 本机，不会自动穿过 SSH。

最直接的验证是 **再建立一个远程 Shell**，在远程执行：

```sh
curl -i --max-time 3 http://127.0.0.1:8028/receivables/C001
```

此时 curl 客户端和 Python 服务端都在远程机器。如果需要在 Mac 访问而保持服务只监听远程回环，可在 **Mac 终端 B** 建立端口转发（8029 本机空闲）：

```sh
ssh -N -L 127.0.0.1:8029:127.0.0.1:8028 -p 2222 learner@linux-lab.example.invalid
```

`-N` 表示不启动远程命令，只保持转发。第一个 `127.0.0.1:8029` 是 Mac 的监听入口；后一个 `127.0.0.1:8028` 是从远程端连接的目标。**Mac 新终端 C** 执行 `curl -i http://127.0.0.1:8029/health`，请求通过隧道到达远程服务。B 按 Ctrl-C 只关闭隧道，远程服务仍需在 A 停止。

这里新增的是一条有明确两端的转发路径；不需要把无认证练习服务开放到公共网络。

## 6. 断开会话后，进程会怎样？

只在前台启动服务时，终端 A 按 Ctrl-C 停止服务，然后输入 `exit` 退出远程 Shell，回到本机。若网络意外断开或直接关闭窗口，普通终端相关进程可能因挂断信号、Shell 或会话策略退出；不能将 `&` 理解为“保证永久运行”。

临时演示有两种常见方法：

**远程项目目录，前台实例已停止，使用 nohup：**

```sh
mkdir -p logs
nohup env QUERY_CURRENCY=CNY .venv/bin/python server.py > logs/service.log 2>&1 < /dev/null &
remote_service_pid=$!
printf '%s\n' "$remote_service_pid" > service.pid
```

nohup 让程序忽略通常的挂断信号；重定向输入避免等待终端，输出写到日志。但它不提供开机启动、失败重启或统一状态管理，环境的会话清理策略也可能影响它。再次登录后先根据 service.pid 用 `ps -p PID -o pid,command` 和端口确认身份，再对确认的 PID 发 TERM；旧 PID 文件可能过期，不能盲目 kill。

如果目标主机已安装 **tmux**，它提供可分离、再接回的终端会话。在远程执行 `tmux new -s receivable` 后，进入项目启动服务；按 Ctrl-B 再按 D 分离，会话继续存在。以后 `tmux attach -t receivable` 接回，Ctrl-C 停止服务。tmux 本机当前未发现，本章不要求安装；它保留终端会话，但也不替代正式服务的启动和重启策略。

长期托管通常交给上一章介绍的 systemd 或目标环境已有管理方式。

## 7. 下载日志与排错

如果刚才 nohup 方式生成了日志，**Mac 本机终端，选择一个新的本地目录：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment"
download_dir=$(mktemp -d "$PWD/ssh-download.XXXXXX")
scp -P 2222 learner@linux-lab.example.invalid:~/receivable-lab/logs/service.log "$download_dir/service.log"
```

源带远程前缀，目标是 Mac 路径，方向与上传相反。之后可用 02-02 的 grep/less 分析本地副本。

| 现象 | 先检查 |
| --- | --- |
| Connection refused | 目标 SSH 地址/端口是否正确、SSH 服务是否监听 |
| Connection timed out | 网络路由、防火墙、目标可达性；不等于密码错 |
| Permission denied (publickey) | 远程用户名、选用私钥、管理员是否安装对应公钥 |
| 主机密钥变化警告 | 通过可信渠道核对变更原因和新指纹 |
| SSH 成功但查询服务不可达 | 查询服务是否运行、所在机器的 localhost、隧道或监听地址 |

</details>

## 8. 可选练习

A. SSH 登录远程后执行 `ls ~/receivable-lab`，读的是谁的磁盘？B. Mac 能访问 localhost:8028 就能证明远程服务成功吗？C. 下载时本地路径放在 scp 的哪一侧？

??? note "参考答案与推理"
    A：远程主机，~ 也是远程用户主目录。B：不能；除非明确建立了对应端口转发，否则访问的是 Mac。C：下载的本地路径在目标一侧，远程源写成 user@host:path。判断方向看源与目标，不看你脑中正在“操作哪个项目”。

## 本章回顾与检查清单

- [ ] 能区分主机身份验证与用户认证、公钥与私钥。
- [ ] 能标明 SSH/scp 每条命令在哪台机器执行、两个路径属于谁。
- [ ] 能解释会话、隧道、服务进程各自何时结束。

## 阅读中产生的答疑

暂无。当前从“快速读”开始；真实服务器操作待有明确连接条件后按需查阅。

## 来源与后续

2026-10-31 核对 [OpenSSH ssh 手册](https://man.openbsd.org/ssh)、[scp 手册](https://man.openbsd.org/scp)。当前未进行远程登录、传输、隧道或 tmux 实测，文中为具备前提后的操作流程。下一章：[02-08 综合交付练习](08-delivery-lab.md)；[目录](index.md)。
