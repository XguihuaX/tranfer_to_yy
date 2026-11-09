# 02-04 Git 分支、协作与撤销

> 教材已准备，2026-10-31。所有协作发生在本机练习目录内。

## 本章怎么读 { #reading-guide }

**接着02-03学习时，先看下方“从两条分支到合并”例子，再读快速读。** 已熟悉分支合并则直接看四个区别；不熟悉哪项再展开查阅。双人协作演示是一条连续过程，动手时从 §2 准备，不从冲突中间执行。

复习后进入 [02-05 环境与权限](05-environment-and-permissions.md#reading-guide)。

## 本章问题、目标与前置

你与同事各自改了一份查询配置，怎样把改动合在一起？改错了又该撤销哪一层？前置为 [02-03 的工作区、暂存区与提交](03-git-changes.md)。本章先建立分支，再用两个本地副本演示同步、分叉、冲突和修复，最后比较三类撤销。完整演练约 40–50 分钟；快速复习约 5–10 分钟。

**下方入门例子的Git命令共用于Windows cmd和Mac，可先手动推演。折叠区保留的完整双人实操使用Mac本机，所有命令在同一个终端按顺序执行。** Alice、Bob 是两个目录代表的开发者；这里的“远端”也是本机的 bare 仓库，没有联网。每次切换角色都明确 `cd`。

## 从两条分支到合并：接着02-03的例子 { #merge-intro }

这一章接着解决三个问题：自己的功能分支怎样合回主分支；怎样和同事交换提交；双方修改重叠时怎样处理冲突。先只看第一个。

假设你在02-03已经保存了两个提交，所有编辑都已提交，当前练习仓库里有两条分支（若之前删除或reset过分支，此处先按图推演，不直接照抄）：

```text
第一版 ── 第二版
  ↑         ↑
 main   add-currency
```

main里的query.txt只有 `customer=C001`，add-currency的第二版新增 `currency=CNY`。你现在认可币种功能，希望main也包含它。在这个仓库目录执行，Windows cmd和Mac写法相同：

```sh
git switch main
git merge --ff-only add-currency
```

先切到main，是因为 **merge把指定分支合入当前分支**。这里的含义是“把add-currency合入main”。执行后，打开query.txt会看到：

```text
customer=C001
currency=CNY
```

此时两个分支都指向第二版：

```text
第一版 ── 第二版
            ↑
       main（当前）
       add-currency
```

本例中main没有独立的新提交，Git只需把main从第一版推进到已有的第二版，这叫“快进”（fast-forward）。`--ff-only` 表示只允许这种方式；本例合并已经完成，无需再add或commit，也没有额外的合并提交。

add-currency不会自动删除。功能合入后，如果不再需要这条分支，可以在main上执行 `git branch -d add-currency`；main已经包含第二版，所以删除分支名不会丢掉刚合入的内容。

若main也有自己的新提交，两条路线就发生了分叉，`--ff-only` 会停止；分叉不一定有内容冲突。后面的§5再解释怎样合并两边，以及修改同一行时怎样处理。接下来读§1和§4，理解远端与fetch/push；无需现在搭建双人练习环境。

## 快速读：协作与撤销保留四个区别 { #quick-read }

本章先花 5–10 分钟看这里；双人仓库和冲突全过程留作查阅，无需再从头做一遍。

- `fetch` 更新远端信息，当前工作分支不会自动合并；本章用 `pull --ff-only` 获取并尝试快进。双方各有新提交而无法快进时，查看历史，再决定如何合并。
- 合并冲突时，先确认两边修改的意图，再编辑为最终内容，`add` 标记已解决，`commit` 完成。冲突不等于仓库损坏。
- `restore --staged 文件` 取消暂存、保留编辑；`restore 文件` 把工作区恢复为暂存区内容，会丢弃对应的未暂存编辑；`revert 提交` 新增反向提交、保留历史。撤销前先确认自己要改哪一层。
- `stash` 临时收起未提交工作，`-u` 包含未跟踪文件；它不替代正式提交，恢复时也可能冲突。

只对不熟悉的项展开下面的例子，不需要把所有 Git 命令背下来。

<details markdown="1">
<summary>完整演示：两个本地副本的同步、冲突与撤销</summary>

## 1. 分支与远端各解决什么？

分支是指向一串提交末端的名字。创建分支后提交新修改，可以让一条工作路线独立向前；切换分支时，Git 会把对应版本放入工作区。切换前先看 status；未提交修改可能随切换保留，也可能因覆盖风险阻止切换，不应把“换分支”当成保存按钮。

远端是另一份 Git 仓库的地址。开发者各有自己的工作区和提交历史，通过共享仓库交换提交。**bare 仓库**只有 Git 数据，没有供人日常编辑的工作区，适合作为本次共享点。

```text
Alice 工作副本 ←→ shared.git（本机共享仓库）←→ Bob 工作副本
```

`origin` 只是 clone 自动取的远端简称；`origin/main` 是本地记录的“上次获知远端 main 在哪里”，不是实时远程视图。`fetch` 更新这份认识；`push` 把本地提交送过去。

## 2. 准备共享点和两个副本

**本机终端，起始位置不限；保留变量 collab_root：**

```sh
cd "/Users/liujunhong/Documents/ChatGPT/用友/learning/02-deployment"
collab_root=$(mktemp -d "$PWD/git-collab.XXXXXX")
git init --bare --initial-branch=main "$collab_root/shared.git"
git clone "$collab_root/shared.git" "$collab_root/alice"
cd "$collab_root/alice"
git config --local user.name "Alice Learner"
git config --local user.email "alice@example.invalid"
git config --local commit.gpgsign false
printf 'mode=normal\n' > query.conf
git add query.conf
git commit -m "Initialize query mode"
git push -u origin main
```

第一次 clone 提示空仓库正常。`push -u` 除了上传，还把本地 main 的 **upstream（上游跟踪分支）**设为 origin/main；以后 `git pull` 就知道默认从哪里更新。

**仍在同一终端，切换到 Bob：**

```sh
git clone "$collab_root/shared.git" "$collab_root/bob"
cd "$collab_root/bob"
git config --local user.name "Bob Learner"
git config --local user.email "bob@example.invalid"
git config --local commit.gpgsign false
git remote -v
git branch -vv
```

remote 输出应指向本机 shared.git；branch 显示当前 main 跟踪 origin/main。clone 已帮 Bob 设置跟踪关系。两份配置只作用于各自练习仓库。

## 3. 在分支上增加查询币种

**切换到 Alice 副本：**

```sh
cd "$collab_root/alice"
git switch -c add-currency
printf 'currency=CNY\n' >> query.conf
git add query.conf
git commit -m "Add query currency"
git switch main
git merge --ff-only add-currency
git push
```

`switch -c` 创建并进入新分支。切回 main 时，工作文件暂时回到旧内容；merge 后包含新币种。这里 main 没有独立新提交，Git 只需把 main 的指针向前移到 add-currency，叫 **fast-forward（快进）**，不会额外制造合并提交。

`--ff-only` 要求只能快进；不满足时停止，让你先了解历史。此时 add-currency 还在，但两条分支可以指向同一提交。

## 4. Bob 怎样获取改动？

**切换到 Bob 副本：**

```sh
cd "$collab_root/bob"
git fetch origin
git log --oneline main..origin/main
cat query.conf
git merge --ff-only origin/main
cat query.conf
```

fetch 取回提交并更新 origin/main，但没有自动合并当前 main，所以第一次 cat 仍只有 mode。`main..origin/main` 表示“远端跟踪分支已有、当前分支没有的提交”。merge 后第二次 cat 多出 `currency=CNY`。

日常本章采用 `git pull --ff-only`，即先获取，再尝试快进。此刻再执行一次会提示已经是最新：

```sh
git pull --ff-only
```

为什么明确写选项？我们希望每次结果可解释：能快进就更新；双方分叉时先查看，再有意识地合并，不依赖机器上不同的默认 pull 策略。

## 5. 双方改了同一行，发生什么？

现在两份副本都有 mode 和 currency。**Alice 修改 mode 并推送：**

```sh
cd "$collab_root/alice"
printf 'mode=fast\ncurrency=CNY\n' > query.conf
git add query.conf
git commit -m "Choose fast mode"
git push
```

**Bob 在还没更新的副本中，也修改同一行：**

```sh
cd "$collab_root/bob"
printf 'mode=safe\ncurrency=CNY\n' > query.conf
git add query.conf
git commit -m "Choose safe mode"
git pull --ff-only
```

最后一条应失败，提示无法快进。这是预期结果：Alice 和 Bob 各有新提交，任何一条都不包含另一条。先查看再合并：

```sh
git log --oneline --graph --all -6
git merge origin/main
git status --short
cat query.conf
```

merge 应报告冲突，status 中 `UU` 表示双方修改、尚未解决。文件大致包含：

```text
<<<<<<< HEAD
mode=safe
=======
mode=fast
>>>>>>> origin/main
currency=CNY
```

HEAD 一侧是 Bob 当前分支，另一侧是正在合并的 origin/main。Git 能保留双方信息，却无法替业务判断应该快还是稳。本合成练习约定最终采用 balanced；现实中先核对业务意图。

**继续在 Bob，明确替换这份练习配置并完成合并：**

```sh
printf 'mode=balanced\ncurrency=CNY\n' > query.conf
git add query.conf
git diff --cached
git commit -m "Resolve query mode as balanced"
git push
git log --oneline --graph -5
```

此提交有两个父提交，保存了两条路线汇合的结果。如果发现不该进行这次合并，在冲突解决前可用 `git merge --abort` 回到合并前；本例开始合并时工作区干净，恢复关系清楚。完成后 Alice 再 `git pull --ff-only` 就能前进到这次合并提交。

## 6. 撤销前，先指出要改变哪一层

下表中的“恢复”会改变相应内容，应先看 diff。接下来的例子仅操作 Bob 的 query.conf。

| 目的 | 命令 | 影响 |
| --- | --- | --- |
| 撤销暂存，保留编辑 | `git restore --staged query.conf` | 暂存区回到 HEAD，工作区不变 |
| 放弃尚未暂存的编辑 | `git restore query.conf` | 工作区恢复为暂存区版本 |
| 撤销一个已提交修改并留下记录 | `git revert 提交标识` | 新建反向提交，保留原历史 |

**Bob 副本，当前无未提交修改：**

```sh
printf 'timeout=3\n' >> query.conf
git add query.conf
git restore --staged query.conf
git diff
```

timeout 仍在文件里，只是退出暂存。确定这个练习编辑不要了，再执行：

```sh
git restore query.conf
git status --short
```

结果应干净，因为暂存区先前已恢复为 HEAD。注意 `git restore 文件` 默认来源是暂存区；如果暂存区本身已有改动，它不会凭空回到更早提交。

再演示普通提交的撤销：

```sh
printf '临时实验说明\n' > experiment.txt
git add experiment.txt
git commit -m "Add temporary experiment note"
git revert --no-edit HEAD
git log --oneline -2
```

revert 新建一个提交，撤销刚才新增文件的效果，原提交仍可追溯。这里 HEAD 是刚新增的普通提交；合并提交有多个父提交，revert 还需选择主线，不能直接照搬本例。

## 7. 改到一半，想先处理另一件事怎么办？

**Bob 副本，完成 §6 后：**

```sh
printf '临时调查笔记\n' > scratch.txt
git stash push -u -m "Pause local investigation"
git status --short
git stash list
git stash pop
```

stash 把未提交的工作临时收起。`-u` 同时包含未跟踪的 scratch.txt；通常不包含被忽略的文件。pop 尝试把内容放回，并在成功后移除这条 stash。本例恢复后 scratch.txt 应重新出现。

stash 是临时停放，不是协作发布：其他人不会从普通 push 自动获得它。若恢复时与当前内容冲突，需要处理冲突，不能假定 pop 永远成功或一定已删除 stash。

## 8. 常见失败怎样判断？

push 被拒绝可能是远端已经前进，先 fetch 看历史；pull 无法快进意味着分叉，不需要立刻 force push。冲突意味着两份内容需要选择或整合，不代表仓库坏了。想撤销时，先判定编辑是否暂存、是否提交、是否已经共享，再选对应动作。

本例不使用 reset --hard 或强制推送。多数当前问题已经可以用明确的合并、restore 和 revert 解决。

</details>

## 9. 可选练习

A. fetch 后 origin/main 前进，工作文件会必然变化吗？B. 已 add 但不想提交，仍想保留编辑，选什么？C. `pull --ff-only` 报错后直接反复执行会解决分叉吗？

??? note "参考答案与推理"
    A：不会，fetch 主要更新提交和远端跟踪引用，没有合并当前工作分支。B：`git restore --staged 文件`，保留工作区。C：不会，已有的两条提交路线仍存在；查看图形历史，按意图合并，必要时解决冲突。若是已共享的错误提交，通常新增 revert 更便于协作追溯。

## 本章回顾与检查清单

分支表达不同修改路线，远端交换提交；fetch 更新认识，merge 合并路线，push 发布本地提交。撤销也需要指定工作区、暂存区或历史层面。

- [ ] 能解释快进和分叉，并完成本例冲突解决。
- [ ] 能区分 origin、origin/main、main 和 upstream。
- [ ] 能选出保留编辑的取消暂存操作，理解 revert 保留历史。

## 阅读中产生的答疑

### merge是覆盖吗，什么时候用ff-only？

merge参考共同起点，整合两条分支各自的修改；不是直接用另一条分支的所有文件覆盖当前分支。双方修改重叠时可能需要人工解决冲突。普通merge允许整合分叉后的路线；--ff-only只允许沿已有提交路线推进，遇到分叉就停止，不是“防覆盖”的开关。

用户提出的稳定版本场景：stable在A，dev从A发展到已检验的C，可以切到stable执行 `git merge --ff-only dev`，让stable直接指向C。如果stable还有独立补丁D，这条命令会停止；整合D与C后要检验整合结果。ff-only只检查历史关系，不检查测试是否通过；dev若已经继续前进，应指定已检验的提交编号。

### 和同事同步：commit之后还要做什么？ { #remote-intro }

假设你和同事已从同一个共享仓库克隆项目，本地分支为main，远端简称为origin，你有读取权限；推送还需要写入权限且服务端允许直接更新main。下面Git命令共用于cmd和Mac，当前可先读流程。公司的分支保护或评审要求按实际仓库执行。

commit把版本存进自己电脑的仓库，push才把提交送到共享仓库。你在本机仓库内提交后执行 `git push origin main`，就是把本地main推送到origin的main。origin是仓库地址的简称，不是分支名；可以用 `git remote -v` 查看地址。

同事推送新提交后，你的电脑不会自动更新。在本地main上且没有未提交修改时，先执行 `git fetch origin` 获取提交；此时本地main与工作文件不变，`origin/main` 更新为本机刚获取到的远端main位置。执行 `git merge --ff-only origin/main`，才把本地main推进到这个位置。两步可以写成：

```sh
git switch main
git pull --ff-only origin main
```

pull在这里是获取后尝试快进。如果双方各有独立新提交，该命令停止，接§5查看分叉与冲突。origin/main是本机保存的远端状态记录，只有获取后才更新，不是实时联网的远端分支本身。

第一次拿到项目通常用 `git clone 仓库地址`；它创建本地副本，通常把源地址命名为origin。已有副本后日常用fetch/pull获取后续提交，无需反复clone。接下来回到§5，继续看双方修改同一行时的处理。

## 来源与后续

2026-10-31 核对 [git restore](https://git-scm.com/docs/git-restore) 与 [git pull](https://git-scm.com/docs/git-pull) 的操作语义；分支流程见 [Git 官方书](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging)。本地案例作者验证见 VERIFICATION.md。下一章：[02-05 环境与权限](05-environment-and-permissions.md)；[目录](index.md)。
