# 已替换的PowerShell参考段

用户已明确选择cmd与Mac，以下仅保留历史材料，不属于当前教学路线。

## Windows 本机操作：从文件修改到提交 { #windows-practice }

当前先以 Windows PowerShell 5.1/7 为默认示例，具体常用终端待你确认；不要把这组命令粘到 cmd 或 Git Bash。Windows Terminal 是容纳不同 Shell 的终端应用，打开它后还要看当前标签运行的是 PowerShell、cmd，还是 WSL。

### A. 先准备一个独立目录

**Windows 本机，PowerShell，一个终端持续使用。** 先执行 `git --version`，确认能找到Git且版本为2.28+；未找到时先处理Git安装或命令路径，不继续初始化。

```powershell
$labName = "git-practice-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$gitLab = Join-Path $env:USERPROFILE $labName
New-Item -ItemType Directory -Path $gitLab -ErrorAction Stop
```

`$env:USERPROFILE` 是Windows用户主目录，例如 `C:\Users\你的用户名`；变量名以`$`开头。这里用时间组成新目录名，`Join-Path`拼接位置，`New-Item`创建目录。若创建报错，先处理错误再继续；原有目录不会被强行重建。这段只用于准备练习位置，不需要背诵。

**目录创建成功后，仍在同一个PowerShell终端：**

```powershell
Set-Location $gitLab
git init -b main
git config --local user.name "Learning User"
git config --local user.email "learner@example.invalid"
git config --local commit.gpgsign false
git rev-parse --show-toplevel
```

`Set-Location`切换目录，常用简写是`cd`。最后确认输出的是新练习目录。后面的`git ...`与Mac例子相同，`--local`只配置本仓库。

### B. 新建文件，再提交

**同一练习目录：**

```powershell
Set-Content -Path query.txt -Value "customer=C001" -Encoding ascii
Set-Content -Path README.txt -Value "Query practice" -Encoding ascii
git status --short
git add query.txt README.txt
git diff --staged
git commit -m "Add initial query example"
git log --oneline
```

`Set-Content`创建或覆盖文本文件；这里明确用ASCII，因为这两份示例文本只有英文和数字，避免不同PowerShell版本的默认编码差异。实际中文文件不能照搬ASCII编码。status应先出现两个未跟踪文件；暂存、查看、提交的含义与下面正文完全一致。

### C. 看懂两份 diff

**第一次提交后，继续在同一目录：**

```powershell
Add-Content -Path query.txt -Value "currency=CNY" -Encoding ascii
git add query.txt
Add-Content -Path query.txt -Value "timeout=3" -Encoding ascii
git status --short
git diff
git diff --staged
```

`Add-Content`追加一行，不覆盖原文件。第一次追加后add，第二次追加后还没add，所以普通diff显示timeout，staged diff显示currency；status是`MM`。这里是本章关键，与Windows或Mac无关。

把两项一起保存：

```powershell
git add query.txt
git commit -m "Specify currency and timeout"
git show HEAD:query.txt
```

最后应看到customer、currency、timeout三行。

### D. 排除运行文件

**同一练习目录：**

```powershell
Set-Content -Path .gitignore -Value ".venv/", "logs/", ".env" -Encoding ascii
New-Item -ItemType Directory -Path logs
Set-Content -Path logs/query.log -Value "demo log" -Encoding ascii
Set-Content -Path .env -Value "QUERY_CURRENCY=CNY" -Encoding ascii
git status --short
git add .gitignore
git commit -m "Ignore local runtime files"
git status --short
```

status应只提示新增的.gitignore，最后提交后干净。忽略规则对已跟踪文件的限制，见下面完整正文§5；原练习也仍可使用。

**Mac对照只需看这几处差别：** 进入目录用`cd`；正文原例用`printf ... > 文件`创建或覆盖、`printf ... >> 文件`追加。`git status/add/commit/diff/log/show`沿用同一套，不重复学两遍。

