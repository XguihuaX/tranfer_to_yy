# 用友学习项目快照

打包日期：2026-11-09（Asia/Shanghai）。

项目文件位于 [projects/yonyou/](projects/yonyou/)，包含 199 个源文件，共约 2.3 MB。精确清单、大小和 SHA-256 见 [project-manifest.json](project-manifest.json)。

## 已包含内容

- [教材正文](projects/yonyou/docs/index.md)、导航和素材。
- [练习代码与学习进度](projects/yonyou/learning/)，包括 00、01、02、03、08 模块的 `PROGRESS.md`。
- 3 份 XMind 文件、SQLite 教学数据库及初始化 SQL。
- Python 依赖清单、MkDocs 配置和启动脚本。
- 项目 `AGENTS.md`、学习总览、教学规则、章节模板及核对/工具调研记录。

这是截至本次打包的快照；尚未编写的后续课程保留原有状态。迁移后优先读取各模块实际进度，教材准备完成不表示用户已经学习完成。

## 新电脑从哪里开始

1. 下载或克隆整个迁移仓库。
2. 将 `projects/yonyou/` 作为学习项目目录，可以直接在这里使用，也可以复制到自己的工作目录。若已存在同名项目，先比较并保留已有修改。
3. 阅读该目录的 `AGENTS.md`、`LEARNING-HUB.md`、`TEACHING-GUIDE.md` 及相关 `learning/*/PROGRESS.md`。
4. 进入该项目目录，再按 [Windows 配置指南](setup/WINDOWS.md) 重建基础环境和启动教材。
5. 在 PyCharm 中选择新建解释器与实际工作目录；已有 README 中的旧 Mac 绝对路径仅作历史参考。

例如，从迁移仓库根进入项目：

```sh
cd projects/yonyou
```

教材启动后访问 `http://127.0.0.1:8765/`。也可以直接在 GitHub 或编辑器中阅读 Markdown 正文。

## 本次核对结果

- 199 个文件与旧项目来源文件逐一核对 SHA-256。
- 使用旧电脑已有文档环境，对迁移副本执行 `mkdocs build --strict`，通过。
- 3 份 XMind 压缩容器完整性检查通过。
- SQLite 示例数据库以只读方式执行 `PRAGMA integrity_check`，结果为 `ok`。
- 全局规则片段与源文件对应的两节原文一致。

未复制旧虚拟环境、IDE 工作区、Python 缓存、临时预览日志及历史验证运行日志目录；教学用的示例日志保留。没有执行真实模型请求，也没有在新电脑重建环境。

仓库根的 `.gitignore` 为后续使用排除了虚拟环境、真实 `.env`、缓存和 IDE 目录。原项目文件内容保持不变，发布前仍需检查实际新增文件。
