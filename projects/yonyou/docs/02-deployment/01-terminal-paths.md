# 02-01 在终端找到并运行一个项目

> 教材已准备。更新：2026-10-31。阅读与练习状态单独记录于本模块 PROGRESS.md。

## 本章怎么读 { #reading-guide }

**当前从本章顺序阅读。** 2026-11-04 已讨论到 §4 的路径写法；熟悉的操作可快速略过。要跑本章例子，从 §3 的目录准备开始。

后续按你的阅读节奏继续；[模块目录](index.md)中仍保留快速路线供查阅。

## 本章问题、目标与前置

你已经读过 [01 Python 与 API 工程基础](../01-python-api/index.md)。这一章解决一个实际问题：拿到项目文件之后，怎样在终端找到它、查看说明、运行程序，并解释“明明有文件，为什么报找不到”。

读完后，你应能说清终端、Shell 和 Python 的关系，用 `pwd`、`ls`、`cd` 定位目录，区分绝对路径和相对路径，并从正确位置运行短程序。完整正文约 20–30 分钟（按需查阅，不计入当前必读安排），可以分次阅读；练习也可以先手动推演，不重讲 Python 基本语法。

**本章所有命令都在你的 Mac 本机执行。** 没有远程服务器，也没有 HTTP 通信。macOS 和 Linux 是不同的操作系统，本章选择两者通用的终端操作，具体路径使用你当前的 Mac 项目。Linux 权限、SSH、Git 和 Docker 留到后续章节。

**Windows cmd差异：** 当前目录用不带参数的 `cd` 查看，列出文件用 `dir`，跨盘进入目录用 `cd /d "实际路径"`；用户主目录写 `%USERPROFILE%`，不使用Mac的 `~`。后面的Mac绝对路径须替换为Windows实际位置。


## 1. 为什么在 IDE 能运行，换到终端就可能失败？

在 PyCharm 中点“运行”，IDE 会按运行配置选择 Python、指定程序文件和工作目录，然后启动程序。终端里，这些选择要通过你输入的命令和所在目录表达。

例如应收查询助手的一个小目录里有 `main.py` 和数据文件。输入 `python3 main.py` 时，电脑需要先找到 Python，再找到 `main.py`；程序启动后，还需要找到数据。任何一步的位置不对，都可能失败。

这一章沿同一个例子走完下面的过程：

```text
打开终端 → 确认当前目录 → 进入项目目录 → 查看文件与说明
         → 启动 Python → 程序读取数据并打印结果
```

## 2. 终端、Shell 和命令各做什么？

在 Mac 上用 Spotlight 搜索“终端”并打开。**终端应用**提供你看到的窗口，接收键盘输入、显示文字输出。

窗口中通常运行着一个 **Shell**，即解释并执行命令的程序。macOS 常见的是 zsh，Linux 上常见的是 Bash。输入一行命令并按回车，Shell 就处理这一行，再等待下一条命令。

先在本机终端输入：

```sh
pwd
```

`pwd` 显示当前工作目录。你可能看到 `/Users/liujunhong`，也可能看到其他路径，以实际输出为准。这里的**目录**就是文件夹；**当前工作目录**是这个 Shell 会话定位文件时使用的起点。

再看一条命令的形式，先不用执行：

```sh
python3 main.py
```

Shell 识别出要运行 `python3`，把 `main.py` 作为参数交给它。Python 打开这个文件并执行其中的代码。Shell 和 Python 在这里各做一步：前者启动程序，后者解释 Python 代码。

一般命令可读作“命令名 + 选项 + 参数”。例如 `ls -a data` 中，`ls` 用来列出目录内容，`-a` 这个选项表示也显示隐藏项，`data` 是要查看的目录。不是每条命令都需要选项和参数。

输入行前可能有用户名、目录名以及 `%` 或 `$`，这些是**提示符**，属于界面提示。本章代码块省略提示符，复制命令本身即可。如果看到 `>>>`，说明进入了 Python 交互环境；先输入 `exit()` 返回 Shell，再执行 `cd` 等命令。

## 3. 当前目录为什么重要？

本章已准备下面的小目录。树形图只用于展示，不需要安装或执行 `tree`。

```text
learning/02-deployment/terminal-lab/
├── README.txt
├── main.py
└── data/
    └── balance.txt
```

**执行位置：本机终端，起始目录不限。** 逐行执行：

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/terminal-lab"
pwd
ls
```

`cd` 改变当前 Shell 的工作目录。第一行成功时通常没有文字输出；随后 `pwd` 应显示以上完整目录，`ls` 应列出 `README.txt`、`data`、`main.py`，显示顺序可能不同。

这里发生的是“改变定位文件的起点”，文件本身没有被移动。`pwd` 只显示位置，`ls` 只列出内容。接着在 `terminal-lab` 中执行：

```sh
ls data
pwd
```

前一行应显示 `balance.txt`，后一行仍然显示 `terminal-lab` 的完整路径。**查看一个目录不会自动进入它。** 想进入子目录再回来，可以继续执行：

```sh
cd data
pwd
cd ..
pwd
```

`..` 表示上一级目录，因此两次 `pwd` 的结果分别以 `/terminal-lab/data` 和 `/terminal-lab` 结尾。完成这组操作后，我们回到了 `terminal-lab`。

每个终端会话都有自己的当前目录。在窗口 A 中 `cd data`，不会让已打开的窗口 B 同时进入 `data`。不知道自己在哪时，重新执行 `pwd` 即可。

## 4. 绝对路径和相对路径怎么选？

**路径**描述文件或目录的位置。macOS 和 Linux 用 `/` 分隔各级目录。

先用同一个目标比较两种写法。**假设你在 Mac 本机的 `/Users/liujunhong`，要进入它下面的 Documents 文件夹**：

```sh
cd /Users/liujunhong/Documents
```

这是绝对路径：开头的 `/` 表示从文件系统最顶层的根目录出发，再依次找到 Users、liujunhong、Documents。无论当前目录在哪，这个完整地址都指向同一个目标。

如果当前仍是 `/Users/liujunhong`，也可以写：

```sh
cd Documents
```

这是相对路径：从当前目录出发，找它里面的 Documents。两条命令是从同一起点出发的两种替代写法，不是要求连续执行。若已经进入 Documents，再执行 `cd Documents`，就会尝试进入 `/Users/liujunhong/Documents/Documents`。

因此先看“从哪里出发”：绝对路径从 `/` 出发，相对路径从当前工作目录出发。路径中间有 `/` 不代表绝对路径，例如 `data/balance.txt` 仍是相对路径。

| 写法 | 含义 | 起点 |
| --- | --- | --- |
| `/Users/liujunhong/Documents/ChatGPT/用友` | 绝对路径，以 `/` 开头 | 文件系统根目录 |
| `data/balance.txt` | 相对路径 | 当前工作目录 |
| `./main.py` | 当前目录中的 main.py；`.` 表示当前目录 | 当前工作目录 |
| `../main.py` | 上一级目录中的 main.py | 当前工作目录的上一级 |
| `~/Documents` | Shell 把开头的 `~` 展开为当前用户主目录 | 当前用户主目录 |

`.`、`..`、`~` 可以先记成三个位置：这里、上一级、我的主目录。以当前目录 `/Users/liujunhong/Documents` 为例，`ls .` 查看 Documents 的内容，`ls ..` 查看上一级 liujunhong 的内容，两个命令都不会切换目录；`cd ..` 才会回到上一级。`cd ~` 则回到当前用户的主目录，本例为 `/Users/liujunhong`。

路径负责指出目标，命令决定对目标做什么：`ls data` 查看 data 目录，`cd data` 进入 data 目录。路径也能指向文件，例如 `data/balance.txt`；但 `cd` 的目标必须是目录，不能进入一个普通文本文件。

例如在 `terminal-lab` 中，`data/balance.txt` 指向数据；在 `terminal-lab/data` 中，文件就在当前目录，应写 `balance.txt`。相同的相对路径，在不同目录执行可能指向不同位置。

路径中有空格时，用引号把整个路径括起来，例如 `cd "/某个目录/my project"`，Shell 才会把它当作一个参数。这一行只是格式说明，不要执行这个不存在的示意路径。练习中的中文目录名可以正常使用。

`~` 有个小细节：可以写 `cd ~/Documents`；不要写成 `cd "~/Documents"`，因为引号内的 `~` 不会按这里的规则展开。需要给完整路径加引号时，使用实际的 `/Users/...` 路径即可。

刚开始可以用绝对路径进入项目，确认位置后，再用短的相对路径操作项目内部文件。输入路径的一部分后按 Tab，Shell 通常能帮助补全，减少拼写错误。

## 5. 先看文件，再运行程序

**执行位置：本机的 `terminal-lab` 目录。** 如果之前尝试了其他 `cd` 命令，先重新执行 §3 第一行回到这里。

```sh
cat README.txt
cat data/balance.txt
cat main.py
```

`cat` 把文本内容显示到终端，不会执行文件。这里文件很短，适合直接看；长日志的分段查看留到下一章。

数据内容为：

```text
C001,12800
```

这是合成案例：截至 2026-10-31，客户 C001 有效应收 20000 元，已核销收款 7200 元，无其他调整，未收余额 12800 元，币种人民币。程序读取已经给出的余额，不连接 ERP 或数据库，也不重新进行账务计算。

`main.py` 的完整代码如下：

```python
from pathlib import Path

# 相对数据路径从当前工作目录出发，便于观察启动位置的影响。
print(f"当前工作目录：{Path.cwd()}", flush=True)
text = Path("data/balance.txt").read_text(encoding="utf-8")
customer_id, amount = text.strip().split(",")
print(f"客户 {customer_id} 的未收余额：{amount} 元")
```

`Path` 来自 Python 标准库，用来表示文件路径，不需要安装额外的包。`Path.cwd()` 得到当前工作目录，`read_text` 按指定编码读取文本。后两行拆开客户编号和金额并打印。`flush=True` 让第一行立即显示，便于出错时先看到启动位置。

先检查 Python，再运行：

```sh
python3 --version
python3 main.py
```

第一行应显示 `Python 3.x.x`。本例按 Python 3.9 及以上准备，无第三方依赖；若命令找不到，先按 §7 定位。第二行预期输出：

```text
当前工作目录：/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/terminal-lab
客户 C001 的未收余额：12800 元
```

一次执行的过程是：Shell 启动 Python；Python 继承启动位置，打开 `main.py`，从该工作目录查找 `data/balance.txt`；读取数据并输出；Python 结束后，Shell 再显示提示符。

这个程序运行一次就结束。以后启动 Web 服务时，程序通常持续运行、等待请求，终端不会马上回到提示符；当时再介绍停止服务和进程管理。

## 6. 程序文件找到了，数据为什么仍可能找不到？

**执行位置：先从本机 `terminal-lab` 进入其 `data` 子目录。**

```sh
cd data
python3 ../main.py
```

这次 Python 能用 `../main.py` 找到上一级的程序，却会在读取数据时报告 `FileNotFoundError`。先打印的当前目录会以 `/terminal-lab/data` 结尾。

原因是程序中的 `Path("data/balance.txt")` 仍按当前工作目录定位，于是尝试查找：

```text
terminal-lab/data/data/balance.txt
```

这个文件不存在。**给 Python 一个程序路径，不会自动把工作目录改成程序所在目录。** 即使用绝对路径启动 `main.py`，其中相对数据路径的行为也一样。

本次修复只需要回到项目目录，重新启动：

```sh
cd ..
python3 main.py
```

现在应再次输出 12800 元。实际项目也可以在代码中把资源路径绑定到程序文件位置，或通过配置接收数据目录。本例保留相对路径，帮助你看清工作目录这个启动条件；当前先学会按项目说明从正确目录运行。

## 7. 遇到错误，先确定是哪一步失败

下面的排查都在本机 Shell 中进行，保留报错时的目录，先用 `pwd` 查看位置。

| 现象 | 失败位置与原因 | 下一步 |
| --- | --- | --- |
| `cd: no such file or directory` | Shell 找不到目标目录，目录未切换成功 | 用 `pwd` 确认当前位置，核对路径拼写 |
| `zsh: command not found: python3` | Shell 没找到名为 python3 的命令 | 用 `command -v python3` 查看；本机可核对 `/usr/bin/python3 --version` |
| `python3: can't open file ... main.py` | Python 已启动，但没找到程序文件 | 用 `pwd` 和 `ls` 确认 main.py 所在位置 |
| `FileNotFoundError ... data/balance.txt` | 程序已执行，读取数据时找不到文件 | 查看程序打印的工作目录，以及 `ls data` 的结果 |
| 在 `>>>` 后输入 cd 出现语法错误 | 当前输入被 Python 当作代码 | 输入 `exit()` 回到 Shell 后再执行 cd |

`command -v python3` 用于查看 Shell 将使用哪个 Python 命令。电脑上可能有多个 Python，例如 `/opt/homebrew/bin/python3` 和 `/usr/bin/python3`，版本也可能不同。这个短例没有第三方包，可以使用符合版本要求的解释器；后续涉及项目依赖时会明确指定环境。

看到“找不到”时，先看错误指向什么。程序文件或数据文件找不到时，Python 已经成功启动，需要核对的是文件位置。

## 8. 可选练习

可以口头推演，也可以在本机验证，做完题不是继续阅读的前提。

### 练习 A：查看和切换

从 `terminal-lab` 执行 `ls data`，再执行 `pwd`，当前目录会变成 `data` 吗？希望进入 `data` 时，应该输入什么？

??? note "参考答案与原因"
    不会。`ls data` 只列出目标目录内容。执行 `cd data` 才改变当前 Shell 的工作目录。随后 `pwd` 的输出应以 `/terminal-lab/data` 结尾。

### 练习 B：推演相对路径

当前在 `terminal-lab/data`。哪条命令能显示数据内容：`cat balance.txt`、`cat data/balance.txt`，还是两者都可以？

??? note "参考答案与原因"
    在本章目录结构中，`cat balance.txt` 可以。另一条会寻找 `terminal-lab/data/data/balance.txt`，该文件不存在。相对路径从当前工作目录出发。

### 练习 C：定位运行错误

同事说：“执行 `python3 ../main.py`，已经打印了当前工作目录，随后报找不到 data/balance.txt。”你先检查什么，怎样修复本例？

??? note "参考答案与原因"
    先看输出的当前工作目录，再用 `pwd`、`ls` 核对。如果在 `terminal-lab/data`，执行 `cd ..` 回到 `terminal-lab`，再运行 `python3 main.py`。程序已经开始执行，说明 Python 和程序文件已被找到，问题出在读取数据的相对路径。

## 本章回顾与检查清单

终端承接输入和输出，Shell 解释命令并启动程序；当前工作目录决定相对路径从哪里开始查找。操作项目时，先确认位置，再查看说明，最后启动程序，就能把目录错误、命令错误和程序内的数据读取错误分开处理。

- [ ] 能解释 `python3 main.py` 由谁启动、由谁执行。
- [ ] 能用 `pwd`、`ls`、`cd` 找到并进入练习目录。
- [ ] 能说明为什么 `ls data` 不会改变当前目录。
- [ ] 能解释 §6 中程序找到了而数据找不到的原因。

## 阅读中产生的答疑

暂无。提问可直接说“02-01 §3”，也可以描述卡住的命令；解释补回对应位置。

## 资料与后续

- [Python 官方教程：启动解释器和执行脚本](https://docs.python.org/3/tutorial/interpreter.html)，2026-10-31 核对；对应 §2、§5 的启动方式和交互提示符。
- 本机验证范围记录在模块进度中；当前未连接 Linux 服务器。

下一章：[02-02 文件查找与日志阅读](02-files-and-logs.md)。返回 [02 模块目录](index.md)。
