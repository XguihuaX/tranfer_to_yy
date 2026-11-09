# 02-02 从文件和日志找到证据

> 教材已准备，2026-10-31。用户阅读与练习状态见模块进度。

## 本章怎么读 { #reading-guide }

**当前顺序阅读。** 先沿“找到日志 → 查看内容 → 筛出相关行 → 保存结果”理解本章；§4–6再解释管道、输出通道与退出码。运行独立例子时先做§1的副本准备。

在运行服务时遇到日志问题，可从 [02-06](06-processes-and-ports.md#reading-guide) 回到这里。

## 本章问题、目标与前置

上一章解决了“在哪运行”。本章解决“程序说失败了，怎样找到相关文件和记录”。前置是 [02-01 的路径与当前目录](01-terminal-paths.md)。读完应能复制练习文件、查找错误行、把输出保存到文件，并判断一个命令是否成功。完整阅读与独立演练约 25–35 分钟；当前只需按问题查阅。

本章全部在 **Mac 本机，一个 Shell 终端**完成；所用基本命令也适用于常见 Linux 环境。这里用固定的合成日志练习，真实服务日志在 02-06 接上。

**Windows 也有这些概念，但命令不能只按操作系统名称判断。** 本章示例使用 Bash/zsh 风格；Windows 的 WSL（在 Windows 上使用 Linux 环境）或 Git Bash 中可使用许多类似命令，但要换成本机实际路径。本课Windows统一使用cmd，复制与移动命令分别为`copy`、`move`；Mac对应`cp`、`mv`。不同 Shell 的参数、变量和管道规则可能不同，本章整段脚本不直接当作 cmd 脚本执行。

**Windows cmd差异速查：** 查看文本用 `type query.log`，复制用 `copy`，移动或改名用 `move`；简单筛选可用 `findstr /L /C:"ERROR" query.log`。findstr并不支持所有grep参数，cmd也没有直接对应 `tail -f` 的内置命令。日志分析主线继续使用Mac示例。


## 1. 先建立自己的操作副本

假设同事说 C001 查询曾经失败，你需要找出哪次请求、发生什么。日志是程序按时间写下的事件记录；它让你看见已经结束的执行过程。先把固定日志复制到自己的目录，后续追加内容不会改变教材原样本。

**本机终端，起始目录不限，以下变量在同一个终端持续使用：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment/log-lab"
log_work=$(mktemp -d "$PWD/practice.XXXXXX")
cp query.log "$log_work/query.log"
cd "$log_work"
pwd
ls
```

`mktemp -d` 创建一个名字不重复的新目录；`XXXXXX` 会被替换为随机字符。`$(...)` 取命令输出，赋给变量 `log_work`；`$PWD` 是当前目录。因此输出的目录仍在本模块里，且每次练习互不覆盖。`cp` 复制文件，原件保留。

接着只操作这个副本目录：

```sh
mkdir notes
printf '调查 C001 的一次失败\n' > notes/todo.txt
cp notes/todo.txt notes/todo-copy.txt
mv notes/todo-copy.txt notes/investigation.txt
ls notes
```

`mkdir` 建目录；`printf` 输出文字，其中 `\n` 表示换行；`>` 将文字写入文件，文件不存在时创建。`mv` 在此重命名文件。最后应有 `todo.txt` 和 `investigation.txt`。一般的 `cp`、`mv` 遇到同名目标可能覆盖，因此练习使用新目录和明确目标。

`cp` 来自 copy（复制），基本形式是 `cp 源文件 目标路径`：上例复制后，todo.txt 仍在，多出一份 todo-copy.txt。`mv` 来自 move（移动），形式也是 `mv 源文件 目标路径`：源位置不再保留原文件，文件出现在目标位置。同一个目录内只改目标名字，就表现为改名；上例把 todo-copy.txt 改名为 investigation.txt。可以对应文件管理器中的“复制/粘贴”和“剪切/粘贴或重命名”。

## 2. 先找文件，再找内容

**继续在刚才的副本目录。**

```sh
find . -name '*.log'
grep 'customer=C001' query.log
grep -n 'ERROR' query.log
```

`find` 从指定起点向下查找文件。`.` 是当前目录；`-name '*.log'` 按文件名匹配，单引号让这个模式交给 `find`，不被 Shell 提前展开。第一行应输出 `./query.log`。

`find` 回答“文件在哪里”，`grep` 回答“文件里哪些行包含我要的内容”。例如 `grep 'customer=C001' query.log` 中，`query.log` 是输入文件，`customer=C001` 是筛选条件；匹配后输出整行，不只输出这个字段。这里筛选只产生输出，不修改原日志。

`grep` 检索文本行。第二行返回 C001 的三条记录 r001、r004、r005；第三行的 `-n` 显示行号，应得到：

```text
4:2026-10-31T09:03:00 ERROR request_id=r004 customer=C001 status=500 error=data_unavailable
```

`request_id` 是每次请求的标识，`status` 是该次处理的状态；这里的 500 表示服务内部错误。r001、r004、r005 是三次查询，不能因客户相同就当成同一次。继续查 `grep 'request_id=r004' query.log`，可以聚焦这次请求。固定样本只有一条 r004，真实日志可能有多条同标识记录。

如果本机安装了 `rg`，也可用 `rg -n 'ERROR' query.log` 做类似检索；当前不需要安装它，理解“文件名检索”和“文件内容检索”即可。

## 3. 长文件怎样看？

**同一副本目录：**

```sh
head -n 2 query.log
tail -n 2 query.log
less query.log
```

`head` 看开头，`tail` 看结尾。前两条分别显示 r001/r002 与 r004/r005。`less` 是分页查看器：上下键滚动，输入 `/ERROR` 回车搜索，按 `n` 找下一个，按 `q` 退出。退出查看器不删除文件，也不停止写日志的程序。

对持续写入的服务日志，可以执行 `tail -f query.log`。`-f` 会在显示末尾后继续等待新增内容；**按 Ctrl-C 结束跟随**，回到 Shell。它只结束当前的 `tail`，不意味着服务也停止了。固定样本无人追加时一直等待是正常行为。

## 4. 管道为什么能把两个命令接起来？

每个命令可以有三个文字通道：**标准输入 stdin** 接收内容，**标准输出 stdout** 输出正常结果，**标准错误 stderr** 输出诊断。默认情况下，输入常来自键盘，两个输出都显示在终端，但它们是两个通道。

stdout 是 standard output，stderr 是 standard error；它们是程序输出信息的通道名称，不是两个必须创建的文件，也不是要输入的命令。比如 `cat query.log` 成功读取的文字走 stdout，而 `cat absent.txt` 因文件不存在产生的报错走 stderr。分开通道后，就能只把查询结果交给下一个程序，同时单独查看或保存诊断信息。

通道由程序选择，不是系统看文字里有没有“ERROR”来判断：`grep 'ERROR' query.log` 找到的日志行仍是 grep 的正常结果，走 stdout。有些日志程序也会将普通运行日志写入 stderr，所以看到 stderr 有内容，不必然表示进程已经失败。Windows外部程序同样有stdout/stderr，cmd中的`>`与`2>`也分别处理这两路输出。

**副本目录内：**

```sh
grep 'customer=C001' query.log | grep 'status=500'
```

`|` 叫管道，把左侧命令的标准输出接给右侧的标准输入。第一步筛出三行，第二步只保留其中状态为 500 的 r004。右边的 `grep` 没有文件参数，就从管道接收内容。

管道默认不接走标准错误。以下是一次可控演示，故意使用不存在的文件：

```sh
cat absent.txt > normal.txt 2> errors.txt
cat normal.txt
cat errors.txt
```

`normal.txt` 为空，`errors.txt` 包含找不到文件的诊断。数字 `2` 指标准错误；标准输出的编号是 `1`，`>` 可视为 `1>`。错误行的具体前缀随系统不同，核心是 `No such file or directory`。

## 5. 保存输出时，覆盖和追加差在哪里？

**继续在副本目录：**

```sh
grep 'ERROR' query.log > errors-only.txt
grep 'WARN' query.log >> errors-only.txt
cat errors-only.txt
```

`>` 每次先截断目标文件，再写入；`>>` 保留原内容，在末尾追加。因此结果是 ERROR 的 r004 加 WARN 的 r003，顺序是写入顺序，不再是原始时间顺序。需要时间顺序时，可一次筛出两种级别：

```sh
grep -E 'WARN|ERROR' query.log > issues-time-order.txt
```

这里 `-E` 启用扩展匹配，模式内部的 `|` 表示“或”；它被引号包住，属于 `grep` 的模式，不是 Shell 管道。结果为 r003、r004。

服务的两种输出常合到一个日志：`程序命令 > service.log 2>&1`。Shell 按从左到右处理重定向，先让 stdout 指向文件，再让 stderr 指向 stdout 当前去处。反过来写 `2>&1 > service.log` 时，stderr 仍可能留在终端，不能视为等价。

不要把输入文件同时作为 `>` 的目标，例如 `grep ERROR query.log > query.log`；Shell 会先截断它，随后命令读到的可能已是空文件。用不同的结果文件名。

## 6. 没有输出，是否就代表失败？

命令结束时会给 Shell 一个**退出码**：通常 0 表示成功，非 0 表示其他结果或错误。紧接着用 `echo $?` 查看上一条命令的退出码；再执行别的命令，这个值就会更新。

**同一副本目录，逐行执行：**

```sh
grep 'ERROR' query.log
echo $?
grep 'customer=C888' query.log
echo $?
grep 'ERROR' absent.txt
echo $?
```

前两组分别是有匹配（0）和没匹配（1）；第三组是读取失败，退出码大于 1。这说明 `grep` 的非零结果还要区分“没找到内容”和“根本没读成”。同样，`cd` 成功时通常无输出。

一个管道的退出码默认常取最后一条命令的结果，因此调查问题时可以像 §4 一样拆开运行各步骤。本章不依靠复杂 Shell 脚本自动决定故障原因。

## 7. 可选练习与排错

A. 找出 C001 的所有成功查询，预期有几行？B. 希望保留旧调查记录，应选 `>` 还是 `>>`？C. `tail -f` 没有返回提示符，说明服务卡住了吗？

??? note "参考答案与推理"
    A：`grep 'customer=C001' query.log | grep 'status=200'`，两行 r001、r005。B：用 `>>` 追加；需要全新报告时才覆盖。C：不能这样判断，`tail -f` 本来就等待追加内容，用 Ctrl-C 退出查看。服务状态要另查进程、端口或请求结果。

若找不到文件，先 `pwd` 与 `ls`；若没有匹配，核对大小写和字段，再查看退出码；若日志内容和本章不同，确认读的是固定样本的副本，而非后面章节的实时日志。

## 本章回顾与检查清单

调查顺序是：确定目录和文件 → 找相关记录 → 对照请求和时间 → 保存证据。管道连接命令之间的数据，重定向选择输出去处，退出码补充执行结果。

- [ ] 能说明 `find` 与 `grep` 的对象不同。
- [ ] 能找到 r004 并说出失败原因字段。
- [ ] 能区分 `>`、`>>`、`2>`，知道如何退出 `less` 和 `tail -f`。

## 阅读中产生的答疑

- 2026-11-04：Windows与Mac是否通用、cp/mv含义、stdout/stderr是什么，已分别补入本章前置说明、§1和§4。当前继续从§4理解输出通道，再看管道。

## 来源与后续

命令语义依据本机 `man find`、`man grep`、`man less`、`man zshmisc`，固定样本输出已实际核对；更详细的 Bash 通道机制可查 [官方重定向说明](https://www.gnu.org/software/bash/manual/html_node/Redirections.html)。下一章：[02-03 Git 的一次修改与提交](03-git-changes.md)；[返回模块目录](index.md)。

Windows教学口径于2026-11-04按用户要求统一为cmd；本轮没有在Windows机器运行示例。
