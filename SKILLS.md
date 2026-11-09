# AI Skills 迁移包

更新：2026-11-09。已保存 75 个非论文/科研工作流 Skills，共 298 个文件；目标电脑尚未安装。

用户要求：迁移相关 AI Skills，不迁移论文和科研相关 Skills。保留 LLM 应用、RAG、微调、推理部署、评估观测、多模态应用和代码理解等工程能力；论文写作、文献检索、科研选题与实验编排、学术审稿、统计研究、学术图表、专利及机理研究工作流不纳入。技术 Skill 的参考文献或框架研究背景不影响其工程用途归类。

本轮没有打包独立的视频制作、设计和云算力管理 Skills。插件自带的文档、表格等功能按新电脑实际插件安装方式恢复，不复制旧插件缓存。

## 内容清单

| 分类 | Skills |
| --- | --- |
| LLM应用与结构化输出 | `langchain`, `llamaindex`, `dspy`, `crewai`, `autogpt`, `instructor`, `guidance`, `outlines` |
| RAG与数据接入 | `chroma`, `faiss`, `qdrant`, `pinecone`, `sentence-transformers`, `markitdown`, `huggingface-tokenizers`, `sentencepiece` |
| 微调与训练工程 | `llama-factory`, `peft`, `unsloth`, `axolotl`, `trl-fine-tuning`, `accelerate`, `pytorch-lightning`, `deepspeed`, `pytorch-fsdp2` |
| 量化部署与优化 | `bitsandbytes`, `awq`, `gptq`, `gguf`, `hqq`, `llama-cpp`, `vllm`, `sglang`, `tensorrt-llm`, `flash-attention`, `speculative-decoding`, `knowledge-distillation`, `model-merging`, `model-pruning` |
| 评估观测与数据处理 | `langsmith`, `phoenix`, `mlflow`, `tensorboard`, `weights-and-biases`, `swanlab`, `ray-data`, `ray-train`, `nemo-curator`, `nemo-evaluator`, `lm-evaluation-harness`, `bigcode-evaluation-harness` |
| 运行防护与开发辅助 | `nemo-guardrails`, `llamaguard`, `prompt-guard`, `system-profile`, `web-debug-search`, `exa-search`, `humanizer-zh`, `mermaid-diagram` |
| 语音视觉与生成应用 | `whisper`, `clip`, `blip-2`, `llava`, `segment-anything`, `stable-diffusion`, `audiocraft` |
| 代码理解与技能发现 | `find-skills`, `understand`, `understand-chat`, `understand-dashboard`, `understand-diff`, `understand-domain`, `understand-explain`, `understand-knowledge`, `understand-onboard` |

## 新电脑恢复步骤

1. 读取 `skills-manifest.json`，核对各目录的 `SKILL.md` 及随附脚本、资料；其中 SHA-256 用于核对文件完整性。
2. 检查目标 Codex 版本实际支持的用户 Skill 目录、已有插件和同名 Skills；已安装的同版本无需重复复制。普通 Skill 保留整个目录结构，发生同名差异时先备份再合并。清单中的 `source` 是旧电脑来源记录，不是目标电脑的绝对路径。
3. 对 `restore_method = copy_skill_directory` 的项目，将整个 Skill 目录恢复到已确认的目标用户 Skill 目录。按目标环境识别结果刷新/重新打开会话，核对其名称和描述可见。
4. `understand*` 共 8 个 Skills 依赖完整 Understand-Anything 插件。旧来源为 https://github.com/Lum1104/Understand-Anything.git ，记录提交为 `b42e40d65850559f26918c45c1c8378c03cb588f`。请按该仓库适合目标系统的安装说明恢复插件及依赖，再比较本包内的 Skill 快照并合并必要的本地改动；单独复制 SKILL.md 无法恢复看板等功能。
5. 不批量运行 Skill 内的示例，不因迁移自动下载模型、租用 GPU、训练模型或发送消息。用到某项能力时，再按它的实际依赖安装与验证。Skill 保存成功不代表相应软件已经安装。
6. 在 `MIGRATION-STATUS.md` 分别记录文件恢复、Skill 发现、插件/运行依赖和实际功能验证状态；缺少账号的能力可以记录待接入。

## 全局规则与排除项

`anti-defensive-writing` 专用于论文写作，已排除。用户询问的减少防御性思考规则来自旧电脑 `~/.codex/AGENTS.md`，本轮向用户展示原文，没有改写该文件，也没有把它安装或覆盖到新电脑。

此包未包含 `.env`、登录文件、私钥、MCP 账号配置或工具插件缓存。目录复制时排除了 Git 元数据、虚拟环境、node_modules 和 Python 缓存；对常见凭据格式和敏感文件名进行了检查，匹配到的 API Key 示例已核对为占位内容。

Skills 是旧机器的内容快照；框架版本、操作系统命令及目标工具支持情况在实际使用时核对。
