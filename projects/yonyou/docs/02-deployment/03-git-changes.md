# 02-03 用 Git 保存和追溯一组修改

> 教材已准备，2026-10-31。练习仓库与主项目独立。

## 本章怎么读 { #reading-guide }

**快速复习。** 先看下方“快速读”，熟悉就跳过。Mac完整演示从§1开始，实操从§2准备；Windows cmd完整流程保留在后面的折叠补充中。

需要协作与撤销时看 [02-04 快速读](04-git-collaboration.md#quick-read)；主线从 [02-05](05-environment-and-permissions.md#reading-guide) 开始。

## 本章问题、目标与前置

修改服务说明后，如果新版本有问题，你需要知道“改了什么、为什么改、以前是什么”。Git 用提交保存一组文件的版本。本章沿一个查询配置的小例子建立工作区、暂存区、提交和 HEAD 的关系，完成一次修改、核对、提交和追溯。前置为 [02-01](01-terminal-paths.md) 的目录操作，完整演练约 30 分钟；快速复习约 3–5 分钟。

本章以 **Mac终端为主，Windows cmd按差异补充**。Git核心命令共用；Mac概念与完整演示放在正文，Windows cmd流程折叠保留供查阅。本套完整命令要求Git 2.28+，其中`git init -b`从2.28起可用。无需GitHub账号或联网，只在独立练习仓库操作。Mac旧例已用Git 2.39.2验证；新增cmd流程按官方命令语义核对，尚未在Windows执行。

## 快速读：Git 日常操作只复习这几件事 { #quick-read }

已会基本 Git 操作，可以用 3–5 分钟看完这里，下面的完整演示按需展开。

一次修改沿 `status → diff → add 指定文件 → diff --staged → commit` 走。两个 diff 最容易混：普通 `diff` 看工作区比暂存区多了什么，`diff --staged` 看本次准备提交什么。**add 之后再编辑，新增内容要再次 add 才会进入提交。**

`log --oneline` 查历史，`show HEAD:query.txt` 只查看当前提交里的文件。`.gitignore` 主要作用于未跟踪文件，不会让已经提交的文件自动退出版本管理。这几项熟悉的话，本章直接略过即可。

## 1. Git 保存的是什么？

你平时编辑的文件构成**工作区**。Git 不会把每一次键盘输入自动变成版本；先用 `git add` 把选定内容放进**暂存区**，再用 `git commit` 保存为一次**提交**。暂存区可以理解为“这次准备保存的文件内容清单”。

```text
编辑文件 → 工作区发生变化
          ↓ git add
         暂存区记录选定内容
          ↓ git commit
         仓库新增一个提交
```

提交包含文件快照、作者、说明及父提交关系。每个提交有标识，通常用一小段十六进制字符表示。**HEAD** 表示当前检出的位置；通常它指向当前分支，而分支指向最新提交。分支的协作在下一章展开。

本章最关键的一点是：`add` 保存的是执行当时的内容。之后又修改文件，新增修改不会自动进入已经准备好的提交。

## 2. 建立一次独立练习

**本机终端，起始目录不限，按顺序执行并保留该终端：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment"
git_lab=$(mktemp -d "$PWD/git-practice.XXXXXX")
cd "$git_lab"
git init -b main
git config --local user.name "Learning User"
git config --local user.email "learner@example.invalid"
git config --local commit.gpgsign false
git rev-parse --show-toplevel
```

最后输出必须是刚建的 `git-practice.随机字符` 目录。`.git` 是 Git 保存本仓库历史与索引的内部目录；`git init` 只在这里创建一个新仓库。`--local` 把练习身份写入本仓库，不修改全局配置。关闭本仓库提交签名，是为了避免演示依赖额外签名工具。

`main` 是本练习的主分支名。刚初始化时尚无提交，HEAD 已指向这个待建立的分支；完成第一次提交后它才有对应的提交历史。

## 3. 从未跟踪到第一次提交

**当前在练习仓库：**

```sh
printf 'customer=C001\n' > query.txt
printf '查询练习说明\n' > README.txt
git status --short
git diff
```

`?? query.txt` 和 `?? README.txt` 表示**未跟踪文件**：Git 看见它们，但还没有纳入管理。此时 `git diff` 没有显示它们的内容是正常的；普通 diff 主要比较已跟踪文件的工作区和暂存区。

接着明确选择要提交的两个文件：

```sh
git add query.txt README.txt
git diff --staged
git commit -m "Add initial query example"
git status --short
git log --oneline
```

`git diff --staged` 显示暂存内容与当前提交的差异；首次提交前展示准备新增的文件。提交后 `status --short` 应无输出，表示相对于当前提交没有待保存变化，`log` 显示一条历史。

这里的 `-m` 是提交说明。写清“这次改动的目的”，比“update”更方便以后调查。

## 4. 为什么要分别看两个 diff？

**同一练习仓库，第一次提交已完成：**

```sh
printf 'currency=CNY\n' >> query.txt
git diff
git add query.txt
printf 'timeout=3\n' >> query.txt
git status --short
git diff
git diff --staged
```

在 `add` 之前，工作区新增币种；`add` 后，暂存区也有了币种；再追加超时后，工作区比暂存区多了 `timeout=3`。因此 `status --short` 中 query.txt 应是 `MM`：第一列是暂存区相对 HEAD 的变化，第二列是工作区相对暂存区的变化。

此时普通 `git diff` 只显示超时那一行；`git diff --staged` 显示币种那一行。如果此刻提交，只有币种进入新提交，超时仍留在工作区。本例希望两者一起保存，因此执行：

```sh
git add query.txt
git diff --staged
git commit -m "Specify currency and timeout"
git show --stat HEAD
git show HEAD:query.txt
```

最后显示三行：customer、currency、timeout。`git show HEAD:query.txt` 查看某个提交中的文件内容，不改变当前文件；`--stat` 则摘要显示修改了哪些文件、多少行。

## 5. 哪些文件不该跟着版本走？

依赖虚拟环境、运行日志、机器自己的配置通常不需要纳入代码历史。**在本练习仓库创建合成文件：**

```sh
printf '.venv/\nlogs/\n.env\n' > .gitignore
mkdir logs
printf 'demo log\n' > logs/query.log
printf 'QUERY_CURRENCY=CNY\n' > .env
git status --short
git add .gitignore
git commit -m "Ignore local runtime files"
```

`.gitignore` 告诉 Git 哪些未跟踪路径通常不需要提示和添加。此时日志和 `.env` 不应列为待添加文件。这里 `.env` 只有合成配置；实际凭据也不应放进提交。

但是 `.gitignore` **不会让已跟踪文件自动退出版本管理**。例如 query.txt 已提交，即使把它加入忽略规则，它的修改仍会显示。如果误跟踪的是自己确认不该版本化的文件，可以在评估后用 `git rm --cached 文件名` 从索引移除、保留工作区文件，再提交这次移除；这也不会抹掉旧历史中的内容。本例不需要执行这个命令。

## 6. 一次修改的检查顺序

日常可按 `status → diff → add 指定文件 → diff --staged → commit → log` 走。每一步回答一个问题：有哪些变化、具体改了什么、哪些属于本次任务、即将保存什么、为何保存、历史是否出现。

| 现象 | 原因与处理 |
| --- | --- |
| 新文件不出现在 git diff | 先看 status 是否为 `??`；暂存后看 `diff --staged` |
| 提交后文件仍有 M | 可能暂存后又编辑过；看普通 diff 核对剩余修改 |
| 提交提示无内容 | 暂存区可能为空；工作区有修改不等于已暂存 |
| 忽略规则不生效 | 先查文件是否已跟踪，而非不断追加同样规则 |

本章不需要上传远端。一次本地 commit 已形成版本，但其他人的仓库不会自动得到它，下一章再通过 push/fetch 协作。

<details markdown="1">
<summary>Windows cmd补充：完整练习流程（按需展开）</summary>

## Windows cmd 操作：从文件修改到提交 { #windows-practice }

**Windows本机，命令提示符cmd，所有步骤在同一个窗口按顺序执行。** 可以通过开始菜单搜索“cmd”打开。若使用Windows Terminal，选择“命令提示符”标签；这里补充cmd写法，Mac主线见前文。

### A. 先准备一个独立目录

先执行 `git --version`，确认能找到Git且版本为2.28+；未找到时先处理Git安装或命令路径，再继续。

```bat
set "git_lab=%USERPROFILE%\git-practice-%RANDOM%-%RANDOM%"
echo %git_lab%
mkdir "%git_lab%"
```

`%USERPROFILE%`是Windows用户主目录，例如`C:\Users\你的用户名`；`set "名字=内容"`设置变量，`%名字%`取出变量的内容。`%RANDOM%`提供随机数字，这里用于区分练习目录。若mkdir提示已存在或创建失败，先更换目录或处理错误，不进入已有仓库继续本例。

**目录创建成功后，仍在同一个cmd窗口：**

```bat
cd /d "%git_lab%"
git init -b main
git config --local user.name "Learning User"
git config --local user.email "learner@example.invalid"
git config --local commit.gpgsign false
git rev-parse --show-toplevel
```

`cd /d`同时切换盘符与目录；最后确认Git仓库根目录就是新练习目录。后面的`git ...`与Mac相同，`--local`只配置本仓库。

### B. 新建文件，再提交

**同一练习目录：**

```bat
>query.txt echo customer=C001
>README.txt echo Query practice
git status --short
git add query.txt README.txt
git diff --staged
git commit -m "Add initial query example"
git log --oneline
```

`echo`输出文字，`>query.txt`把输出写入该文件；目标不存在时创建，存在时覆盖。本例将重定向写在命令前，避免文本末尾数字紧挨`>`时被cmd当作通道编号。文件内容用英文和数字，不涉及中文编码设置。

status应先出现两个未跟踪文件；暂存、查看、提交的含义与下面正文一致。

### C. 看懂两份 diff

**第一次提交后，继续在同一目录：**

```bat
>>query.txt echo currency=CNY
git add query.txt
>>query.txt echo timeout=3
git status --short
git diff
git diff --staged
```

`>>query.txt`追加内容，不覆盖原文件。第一次追加后add，第二次追加后还没add，所以普通diff显示timeout，staged diff显示currency；status是`MM`。这就是本章的核心，与Windows或Mac无关。

把两项一起保存：

```bat
git add query.txt
git commit -m "Specify currency and timeout"
git show HEAD:query.txt
```

最后应看到customer、currency、timeout三行。

### D. 排除运行文件

**同一练习目录：**

```bat
>.gitignore echo .venv/
>>.gitignore echo logs/
>>.gitignore echo .env
mkdir logs
>logs\query.log echo demo log
>.env echo QUERY_CURRENCY=CNY
git status --short
git add .gitignore
git commit -m "Ignore local runtime files"
git status --short
```

status应只提示新增的.gitignore，最后提交后干净。虽然cmd文件路径通常用反斜杠，`.gitignore`内的Git规则仍使用`/`。忽略规则对已跟踪文件的限制，见下面正文§5；原练习保留。

**与Mac主线的区别：** 进入目录用`cd`，查看位置用`pwd`；原例用`printf ... > 文件`创建或覆盖、`printf ... >> 文件`追加。`git status/add/commit/diff/log/show`沿用同一套，不重复学两遍。


</details>

## 7. 可选练习

A. 把 timeout 从 3 改为 5，执行 add 后又改为 8，立即 commit 会保存哪个值？B. 怎样不改工作文件就查看上一个提交的 query.txt？

??? note "参考答案与推理"
    A：保存 5；暂存区记录 add 时的内容。8 留在工作区。若要保存 8，需要再次 add。B：已有至少两个提交时，用 `git show HEAD~1:query.txt`；`HEAD~1` 表示沿父提交向前一步。它只读取历史，不切换版本。

## 本章回顾与检查清单

Git 的版本形成于明确的暂存和提交。理解两份 diff，能避免把“文件里看见的内容”误认为“已经提交的内容”。

- [ ] 能解释工作区、暂存区与 HEAD 的关系。
- [ ] 能只暂存本次任务的文件，并在提交前核对。
- [ ] 能从 log/show 找到历史，说明忽略规则对已跟踪文件的限制。

## 阅读中产生的答疑

### 已会 add 和 commit，怎样建分支和保存新版本？ { #branch-versions }

branch 是“分支”。**commit 保存一个版本；branch 给一条开发路线起名字，让你能沿它继续提交。** 同一个分支可以保存很多个版本，不必每保存一版就新建分支。

下面是独立的两版小例子，可以先手动推演，无需Windows电脑。假设已按本章准备好练习仓库，当前分支叫 `main`；用编辑器创建 `query.txt`，内容为：

```text
customer=C001
```

保存文件后，在仓库目录执行（以下Git命令在Windows cmd和Mac相同）：

```sh
git add query.txt
git commit -m "Save initial query"
```

把这次提交称为第一版。接下来想试着增加币种，先从当前版本建立并切换到新分支：

```sh
git switch -c add-currency
```

`switch` 表示切换，`-c` 表示创建，`add-currency` 是自己起的分支名。执行后仍在原来的项目文件夹，文件内容也仍是第一版；这一步没有产生新提交。此时 `main` 和 `add-currency` 都指向第一版，你当前位于后者。

用编辑器把同一个 `query.txt` 改成以下内容并保存：

```text
customer=C001
currency=CNY
```

然后提交第二版：

```sh
git add query.txt
git commit -m "Add currency"
```

这次提交发生在当前分支 `add-currency` 上：

```text
第一版 ── 第二版
  ↑         ↑
 main   add-currency（当前）
```

`main` 仍停在第一版。现在修改已提交，执行 `git switch main`，工作目录中的 `query.txt` 就恢复为一行；执行 `git switch add-currency`，又显示两行。两次提交都保存在仓库里，切换分支会把已跟踪文件更新到该分支对应的版本。若还有未提交修改，切换可能带着这些修改一起过去，也可能被Git阻止；练习时先提交再切换，方便观察。

如果还要增加 `timeout=3`，可以继续留在 `add-currency`，编辑、保存、add、commit，就得到这条分支的第三版。`git log --oneline` 能查看当前分支的提交历史，每次提交有自己的编号；这里的“第一版、第二版”只是讲解用称呼。编辑器保存让文件落盘，commit 才让此次内容进入Git版本历史。

本轮先读懂这个例子；分支合并接着看 [02-04](04-git-collaboration.md)，不需要现在同时学习远程推送。

### 修改怎么回滚，大文件怎么放？ { #undo-and-large-files }

以下Git命令适用于Windows cmd和Mac，先手动推演即可。回滚前用 `git status` 确认修改处于哪一层。

**还没commit：** 假设query.txt的已提交内容是 `currency=CNY`，现在改成USD。如果还没add，`git restore query.txt` 会丢弃这份未暂存修改，恢复为暂存区内容，此例就是CNY。如果已经add，先 `git restore --staged query.txt` 取消暂存（文件中的USD仍保留），确定连编辑也不要时，再 `git restore query.txt`。这适用于已跟踪文件；刚创建、从未提交的文件不套用本例。

**已经commit：** 假设第一版为CNY，第二版把它改为USD，当前位于第二版且没有未提交修改，执行：

```sh
git revert --no-edit HEAD
```

HEAD是当前提交，--no-edit表示采用默认提交说明。Git新增第三个提交，撤销第二个提交的修改，文件回到CNY，原来两次提交仍保留。一般形式是 `git revert 提交编号`，编号从 `git log --oneline` 查看；撤销更早提交时，含义是抵消那次修改，未必把整个项目恢复成当时状态，也可能发生冲突。此例使用普通提交；合并提交的撤销在需要时单独讲。详细操作见 [02-04 §6](04-git-collaboration.md)。

**大文件先看用途。** 日志、下载的数据、模型权重、安装包等若不需要随代码管理，可放到外部存储，在README记录下载位置、版本和校验值，本地目录写入 `.gitignore`。例如在项目根目录的 `.gitignore` 写：

```gitignore
/models/
/datasets/
/logs/
```

这些规则让Git忽略上述目录内尚未跟踪的文件，不删除本地文件。如果文件已经跟踪，例如 `models/model.bin`，可执行 `git rm --cached models/model.bin`，再提交这项变更和.gitignore；本地文件保留，历史提交里的大文件仍存在，仓库不会因此立即缩小。

确实要随项目保存版本的大型素材，可用 **Git LFS（大文件存储扩展）**：Git保存小型指针，大文件内容由LFS存储。先安装Git LFS，并确认远端支持LFS。在尚未提交该大文件的例子中：

```sh
git lfs install
git lfs track "*.psd"
git add .gitattributes design.psd
git commit -m "Track design with LFS"
```

假设design.psd是已存在的新文件。track设置PSD规则，生成的.gitattributes也要提交，之后照常push。现有历史不会因track自动转换为LFS；已有大文件的历史迁移另行处理。服务端容量和流量限制按实际平台核对，不把某个平台的限制当成Git统一上限。

本轮依据：[git restore](https://git-scm.com/docs/git-restore)、[git revert](https://git-scm.com/docs/git-revert)、[Git LFS官方入门](https://git-lfs.com/)。Git LFS流程按官方文档核对，未安装或进行远端上传。继续位置仍为02-03本答疑；合并与协作接02-04。

## 来源与后续

[Git 官方书：记录每次更新](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository)，对应暂存和文件状态；本机作者验证覆盖本章操作。下一章：[02-04 分支、协作与撤销](04-git-collaboration.md)；[模块目录](index.md)。

Windows内容参考：[Git官方安装入口](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)、[cmd set](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1)、[echo](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/echo)、[cd](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cd)，2026-11-04核对。
