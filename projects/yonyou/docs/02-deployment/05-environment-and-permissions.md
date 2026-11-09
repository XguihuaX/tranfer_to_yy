# 02-05 配置、Python 环境与文件权限

> 教材已准备，2026-10-31。命令默认在 Mac 本机执行。按2026-11-05确认的偏好，以Mac为主；Windows差异单独标注cmd写法，不重复两套流程。

## 本章怎么读 { #reading-guide }

**主线 1／3。** 重点读 §1–5：配置怎样传入进程、选中了哪个 Python、文件为什么不可读。已有例子可以边读边推演；权限故障练习按需运行。

下一步：[02-06 进程与端口](06-processes-and-ports.md#reading-guide)。

## 本章问题、目标与前置

同一段代码，在一个终端能运行，另一个却说缺配置；文件明明存在，却读不进去。本章把“运行环境”拆成可检查的几个条件：环境变量、解释器与依赖、文件权限。前置为 [路径](01-terminal-paths.md)、[输出和退出码](02-files-and-logs.md)。约 30–40 分钟。

本章会实际复现缺配置与权限不足，使用新的练习副本。虚拟环境只创建在副本里，无第三方依赖安装。

## 1. 配置怎样进入程序？

查询程序需要知道金额币种。把机器或部署有关的配置放在**环境变量**里，程序可以在启动时读取，不必为每个环境修改源码。

但 Shell 中的普通变量不一定会传给程序。**父进程**是启动另一个进程的进程，启动出的叫**子进程**。Shell 启动 Python 时，导出的环境变量会被复制给子进程；子进程不会反向修改父 Shell 的环境，已运行的程序也不会随之后的 export 自动更新。

**以下是Mac本机的zsh/Bash写法，同一个终端，起始目录不限；不能原样粘贴到Windows cmd：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/env-lab"
env_work=$(mktemp -d "$PWD/practice.XXXXXX")
cp check.py balance.txt "$env_work/"
cd "$env_work"
unset QUERY_CURRENCY
QUERY_CURRENCY=CNY
python3 check.py
```

这七行分成“准备目录”和“演示变量”两段：

| 行 | 含义 |
| --- | --- |
| `cd "/Users/.../env-lab"` | 进入已有样例目录，后面从这里复制check.py和balance.txt。引号把整条路径当作一个参数。 |
| `env_work=$(mktemp -d "$PWD/practice.XXXXXX")` | mktemp -d新建名字不重复的目录；$PWD是当前目录，XXXXXX被替换为随机字符。$(...)取得命令输出的新目录路径，赋给普通变量env_work。 |
| `cp check.py balance.txt "$env_work/"` | 把两份样例复制进新目录，原件仍保留。$env_work取出刚保存的路径。 |
| `cd "$env_work"` | 进入新建的练习目录。 |
| `unset QUERY_CURRENCY` | 清除当前Shell中这个变量及其导出状态，排除之前设置的影响；不删除文件。 |
| `QUERY_CURRENCY=CNY` | 给当前Shell设置一个普通变量，值为CNY；此处还没有export，Python不会继承它。 |
| `python3 check.py` | 启动Python运行脚本；脚本从进程环境读取QUERY_CURRENCY，因此此时报告缺少配置。 |

**env_work只是保存目录路径的变量；新建的是练习文件夹，不是Python虚拟环境，也没有启动新的Shell。** 比如变量值可能是 `/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/env-lab/practice.a1B2c3`。目录不会因为关闭终端就自动删除。Python虚拟环境在§3用 `python -m venv` 创建。

**Windows cmd差异：** `set "QUERY_CURRENCY=CNY"` 设置后，随后启动的Python即可继承，不需要export。查看值用 `echo %QUERY_CURRENCY%`；删除变量用 `set "QUERY_CURRENCY="`。Mac对应为 `export QUERY_CURRENCY=CNY`、`echo "$QUERY_CURRENCY"`、`unset QUERY_CURRENCY`。这些设置作用于当前终端及之后启动的子进程，不会修改其他已打开的终端。

最后应打印“配置错误：请设置 QUERY_CURRENCY=CNY”并退出。先 unset 清掉可能继承的值及导出状态，再只赋普通 Shell 变量；Python 看不到它。

```sh
export QUERY_CURRENCY
python3 check.py
```

现在输出 `读取结果：12800 CNY`。export 将该变量标记为可继承。也可只为一次命令提供环境：

```sh
unset QUERY_CURRENCY
QUERY_CURRENCY=CNY python3 check.py
python3 check.py
```

前一条成功，后一条再次缺配置。命令前的赋值只为那次 Python 提供变量，没有在当前 Shell 中持久 export。

## 2. 引号怎样影响变量内容？

**Mac zsh/Bash，同一个副本目录和终端；下面的变量与echo实验不依赖当前目录：**

```sh
label=C001
printf '%s\n' '$label'
printf '%s\n' "$label"
```

单引号保留字面内容，第一行打印 `$label`；双引号允许变量展开，第二行打印 `C001`。双引号还让含空格的结果保持为一个参数，因此路径变量常写 `"$env_work"`。

这里的“变量展开”就是Shell先把 `$label` 替换为变量值，再交给命令。与§1的export是两回事：Shell读取自己的普通变量不需要export，启动的Python要继承该值才需要export。

**Windows cmd对照：** 设置用 `set "label=C001"`，显示用 `echo %label%`。cmd不把单引号当作上述“禁止展开”的引号；不要照搬Mac的单/双引号规则。

项目中常见的 `.env` 只是一个文件名。Python 标准库不会因为文件存在就自动读取它。本例如果写：

```sh
unset QUERY_CURRENCY
printf 'QUERY_CURRENCY=CNY\n' > .env
python3 check.py
```

先unset排除上一节残留配置后，仍会缺配置：文件里虽然有文字，但check.py只用os.environ读取进程环境，没有读取.env文件的代码。加载.env的工具需要读取文件内容，并把配置提供给程序；加载方式取决于实际框架或启动命令。本教材的默认方式是显式 export，或命令前赋值。Shell 的 `source 文件` 会执行文件中的 Shell 内容，不是通用的“安全读配置”；不同库支持的 `.env` 格式也未必等同 Shell 语法。

## 3. 同名 python3 为什么可能不是同一套环境？

**继续在练习副本：**

```sh
command -v python3
python3 --version
python3 -c 'import sys; print(sys.executable)'
```

这三条都先在Mac终端执行，只查询信息，不修改环境：

| 命令 | 回答的问题 |
| --- | --- |
| `command -v python3` | 当前Shell会找到哪个python3命令？这里的-v不是查看Python版本。 |
| `python3 --version` | 找到的Python版本是多少？ |
| `python3 -c 'import sys; print(sys.executable)'` | 实际启动的Python解释器路径是什么？ |

`-c`让Python执行引号里的短代码；`import sys`导入自带模块，`print(sys.executable)`输出解释器路径，分号把两句代码放在一行。示例路径只是说明，实际以自己的输出为准。

**Windows cmd差异：** 如果本机使用的命令名是python，对应为：

```bat
where python
python --version
python -c "import sys; print(sys.executable)"
```

where可能列出多个匹配项，实际解释器看最后一条。若使用python3命令，则将上述python替换为python3。cmd中的Python代码使用双引号。

Shell 根据 **PATH** 变量中的目录顺序查找命令，`command -v` 显示选中的命令路径。PATH 中有多个 Python 时，排在前面的可能先被使用。`sys.executable` 则从 Python 内部确认实际解释器。

**虚拟环境 venv** 为一个项目提供独立的 Python 包安装位置，便于不同项目使用不同依赖版本。它仍使用同一台操作系统、同一个用户权限；它不是虚拟机或容器。

本机默认 Homebrew Python 3.14.4 在作者核对时出现 `pyexpat` 与系统 `libexpat` 的符号不匹配，导致 venv 的 ensurepip 阶段失败。为使本章可直接复现，下面使用项目已有、已验证的 Python 3.12.14 作为基础解释器，给练习单独创建环境，不改动共享环境。

**先单独执行创建命令，成功后再执行下一组；若创建失败，停在该步保存错误，不继续运行尚不存在的 pip 或 activate。**

```sh
"/Users/liujunhong/Documents/ChatGPT/用友/.venv-docs/bin/python" -m venv .venv
```

创建成功后，仍在同一练习副本中：

```sh
.venv/bin/python --version
.venv/bin/python -m pip --version
.venv/bin/python -m pip check
QUERY_CURRENCY=CNY .venv/bin/python check.py
```

`python -m pip` 指定“由这个 Python 运行它对应的 pip”，避免命令名 `pip` 指向另一套环境。此处 pip check 应报告无依赖冲突；不证明程序所有功能正确。本例只用标准库，没有需要 pip install 的包。

可选地激活这个环境。**以下仍为Mac，在已成功创建.venv的练习目录执行：**

```sh
source .venv/bin/activate
command -v python
python -c 'import sys; print(sys.executable)'
deactivate
```

这四行依次是：激活 → 查询Shell找到的python → 让Python报告实际路径 → 退出激活状态。激活后通常会看到练习目录下的 `.venv/bin/python`。

activate 修改当前 Shell 的 PATH 等设置，让短命令优先使用这个环境；deactivate 恢复激活前的设置。**deactivate不删除.venv、不卸载包，也不关闭终端**；之后仍可重新激活。若想中断正在前台运行的程序，通常按Ctrl+C，那与deactivate是不同操作。

**Windows cmd差异（已安装可用的python，在自己的练习目录）：** 创建用 `python -m venv .venv`，成功后再执行：

```bat
.venv\Scripts\activate.bat
where python
python -c "import sys; print(sys.executable)"
deactivate
```

Mac的虚拟环境可执行文件在 `.venv/bin/`，Windows在 `.venv\Scripts\`；cmd也可以不激活而直接使用 `.venv\Scripts\python.exe`。两套路径不能直接互换。

显式写 `.venv/bin/python` 不依赖激活，尤其适合启动脚本和交接说明。

将来出现 `ModuleNotFoundError`，先检查实际解释器，再查看对应 `python -m pip` 的包信息。不要刚看见缺包就对系统 Python 反复安装。

## 4. 文件权限决定谁能做什么？

**本节与§5使用Mac的权限命令。Windows cmd差异：** 查看Windows权限可用 `icacls balance.txt`；它使用访问控制列表，不能把下面的chmod参数机械换写。这里的权限增删练习继续在Mac做。

**副本目录：**

```sh
ls -l balance.txt
id
```

`ls -l` 的开头可能像 `-rw-r--r--`。第一个字符表示类型：`-` 为普通文件，`d` 为目录；后面分三组，对应所有者、所属组、其他用户。`r` 可读、`w` 可写、`x` 可执行。`id` 显示当前用户和组，用来判断自己属于哪一类。

目录的权限有特殊含义：`r` 允许列出名字，`x` 允许穿过该目录访问已知路径，`w` 配合 `x` 通常允许创建、删除目录项。因此读某个文件，不仅要有该文件的读取权限，还要能穿过上层目录。目录可写也可能允许删除其中的文件，即使文件本身不可写。

macOS 还可能显示 ACL 等额外权限信息；本章先用自己拥有的普通练习文件解释基础权限位。

## 5. 复现“文件存在但无法读取”

**在本章副本目录，使用普通用户；不要在 root 身份下验证这个错误。**

```sh
chmod u-r balance.txt
QUERY_CURRENCY=CNY python3 check.py
```

`chmod u-r` 从文件所有者的权限中移除读取位。程序应出现 `PermissionError`；这是预期演示。文件没有消失，配置也已给出，失败发生在 read_text。

立即恢复所需权限，再验证：

```sh
chmod u+r balance.txt
QUERY_CURRENCY=CNY python3 check.py
ls -l balance.txt
```

输出恢复为 12800 CNY。`u+r` 只增加所有者读取位；不需要给所有人全部权限。类似地，自己写的 Shell 脚本需要直接执行时可用 `chmod u+x script.sh`；但 `python3 check.py` 是让解释器读取脚本，脚本本身不必有 x 位。

如果权限演示未报错，先核对 `id`、文件所有者、实际权限和 ACL；管理员/root 能力可能改变结果，不据此推翻普通权限规则。

## 6. 完整例子如何定位资源？

配套 check.py 只有一条检查链：先从环境取币种，再读脚本旁边的 balance.txt，最后输出结果。它采用：

```python
data = Path(__file__).resolve().parent / "balance.txt"
```

例如脚本位于 `/Users/liujunhong/demo/check.py`，数据文件位于 `/Users/liujunhong/demo/balance.txt`。`Path("balance.txt")` 从终端当前工作目录查找，而上面的写法从脚本所在目录查找；即使在 `/Users/liujunhong` 下用 `python3 demo/check.py` 启动，也能定位到demo里的数据文件。

逐步看：`__file__` 是当前脚本的路径，`Path(...)` 把它转为路径对象，`.resolve()` 得到解析符号链接后的绝对路径，`.parent` 取其所在目录，最后的 `/ "balance.txt"` 是pathlib的路径拼接写法，不是数值除法。整句只构造路径；随后调用 `data.read_text()` 才读取文件。

`__file__` 表示脚本位置，`.parent` 取得目录。与 02-01 的相对路径不同，这次资源跟着脚本位置走，便于后面部署。这里代码变化解决的是“启动目录变化导致找不到附带资源”；它不会解决环境变量缺失或文件不可读。

| 错误 | 首先核对 |
| --- | --- |
| 配置错误 | 是否在启动这个进程的终端 export，或给本次命令赋值 |
| ModuleNotFoundError | 解释器路径与对应环境的依赖 |
| FileNotFoundError | 实际资源路径及文件存在性 |
| PermissionError | 当前用户、路径各级目录与文件权限 |

## 7. 可选练习

A. 终端 A export 后，早已打开的终端 B 一定有这个变量吗？B. `.env` 写好了，程序仍缺配置，应该先查什么？C. 为什么不把权限统一改成 777？

??? note "参考答案与推理"
    A：不一定；两者是独立会话，A 不会改 B 的环境。B：查程序或启动流程是否真的加载 .env，本例没有自动加载。C：777 会把读写执行都授予所有人，超出“让所有者读取”这个需求，也掩盖真正的用户或目录权限问题；用具体的 u+r 修复本例即可。

## 本章回顾与检查清单

程序的运行条件来自启动环境、解释器与包、文件系统权限。先判断失败发生在哪一步，再修改对应条件。

- [ ] 能解释普通变量与 export，以及单次命令赋值。
- [ ] 能用解释器路径核对 pip，独立运行虚拟环境中的程序。
- [ ] 能复现并修复本例的两种故障，说明目录 x 的作用。

## 阅读中产生的答疑

暂无；当前主线从 §1 开始，Python 基础语法按需要回查 01。

## 来源与后续

[Python 官方 venv 文档](https://docs.python.org/3/library/venv.html)与[os.environ](https://docs.python.org/3/library/os.html#os.environ)说明环境机制；Shell/权限参考本机 `man zshbuiltins`、`man chmod`。本章配置和权限路径已实际验证，结果见作者记录。下一章：[02-06 进程与端口](06-processes-and-ports.md)；[目录](index.md)。
