# AGENTS.md

这个 repo 是 Erik 的个人 AI 自动化写作 harness。它用项目级 skills、docs runbooks 和可追踪 Markdown / MDX source，帮助 Codex / Claude Code / Hermes / OpenClaw / Pi 等 agents 完成选题、研究、写作、润色、配图、排版、分发与复盘。

本文件只保留高频规则和文档路由。低频细节使用 progressive disclosure：先读 `AGENTS.md`，再按任务读取 `docs/` 中的对应文档。

## Always

- 保留用户 edits；不要 revert 用户改动，除非用户明确要求。
- 不要打印、提交或泄漏 secrets、本地运行态、账号态数据和依赖目录。
- Current events、company/product facts、pricing、laws、fast-moving tech topics 必须查证，并写清具体日期。
- repo 内长期 canonical source 放在 `content/origin/`，格式是 Markdown / MDX。飞书文档、Notion 等可以作为上游写作入口；进入 repo 后要同步或转换成可追踪文本。
- 内容写作、选题构思、文章润色、改稿、标题和风格判断时读取 [SOUL.md](SOUL.md)，对齐 Erik 的作者写作气质、register、anti-style 和审美边界；非写作任务不要默认加载。
- 图片生成优先使用系统 `$imagegen` skill，不要重建项目重复的 `gpt-image-gen`。
- 任何最终发布动作都需要 user final review，除非用户明确授权自动发布。
- 先做 small, practical automation；不要把未跑通的能力写成已可用能力。
- 遇到可复用的新坑点、新技巧、workflow 改进或 skill 缺陷，随手沉淀到项目 docs，或新增、修改 project-level skills。
- 临时想法、未确认价值的 todo、本机上下文先放 `.local-memory/`；验证为可复用后再迁移到项目 docs、`AGENTS.md` 或 `.agents/skills/`。
- 当某项能力已经值得 project-level skill 化时，主动建议并沉淀为 `.agents/skills/*`。
- Python 工具链统一使用 uv（`uv add` / `uv sync` / `uv run` / `uv lock`），禁止 pip / pipx / poetry / 裸 python 直接操作依赖。

## Operating Principle

这些规则是为了保护安全、可追踪性、发布边界和长期复用，不是为了限制 agent 的创造力。Agent 应在边界内主动提出更好的选题、结构、表达、视觉方案、工具组合和 workflow 改进；新做法先以小实验跑通并验证，再沉淀为项目 docs、scripts 或 skills。

## Decision Autonomy

- 可逆、低风险的写作、研究、整理、preview、本地验证和小型项目 docs 或 skills 改进，agent 应主动推进。
- 涉及最终发布、外部发送、账号态、付费、secrets、删除或移动用户稿件、改写 canonical source 但意图不清时，先向用户确认。
- 不确定时优先做小实验、保留原始材料、记录假设和验证结果，而不是把探索写成长期规则。

## Memory Layers

- `AGENTS.md`：高频规则、行为边界和 docs router，保持简短。
- `docs/`：长期项目 memory，存放项目技术文档、workflow runbooks、复盘、规范和已验证的可复用经验。
- `.local-memory/`：本机短期临时 memory，不入 Git，不是 canonical source；验证为可复用后再迁移到 `docs/`、`AGENTS.md` 或 `.agents/skills/`。
- `.agents/skills/`：可执行 memory，沉淀可重复执行的项目级能力、脚本、checklist 和 workflow。

## Writing Storage Paths

- `content/inbox/`：原始输入和待整理材料 scratch。
- `content/drafts/`：本地写作草稿 scratch。
- `content/origin/YYYY-MM-DD-topic/`：可追踪 canonical Markdown / MDX 文章源稿（目录名必带日期，不写无日期歧义的 slug）。
- `content/wechat/`、`content/blog/`：从 `content/origin/` 派生的渠道版本。
- `content/origin/YYYY-MM-DD-<slug>/assets/`：article-local assets，跟随 origin article 使用；图片、封面、正文插图等应放此处并由 `index.md` 引用。大体积二进制素材默认不提交（受 `.gitignore` 全局忽略），除非任务明确需要 repo 追踪。
- `content/wechat/YYYY-MM-DD-<slug>/assets/`：微信渠道专用 assets；如果图片已在 origin assets 且体积较大，可用相对路径指回 origin，避免重复提交。
- `content/assets/`：跨文章复用的 prompts、metadata、manifest 和 sources；不要放单篇文章的一次性素材。
- `.local-archive/YYYY-MM-DD-<slug>/`：本机归档快照，`<slug>` 为裸 topic，目录名带日期前缀。写作收尾时由 `writing-task-closeout` 把最终 `index.md`、实际使用的图片、生成 prompts/metadata 统一归档至此，不入 Git。图片生成阶段不要双写，只保留一份在 `assets/` 工作副本中。
- 不要把文章草稿、渠道预览或一次性写作 scratch 放到 `docs/`；不确定时读取 [docs/project/directory-layout.md](docs/project/directory-layout.md)。

## Docs Router

根据任务读取最小必要文档：

| 任务 | 先读 |
| --- | --- |
| 了解项目愿景、写作场景 | [docs/project/vision.md](docs/project/vision.md) |
| 对齐 Erik 作者写作气质、register、anti-style 与审美边界 | [SOUL.md](SOUL.md) |
| 了解完整 AI 写作工作流、skill 分工、目录约定 | [docs/workflows/ai-writing-workflow.md](docs/workflows/ai-writing-workflow.md) |
| 理解 writing-agent-harness 身份和边界 | [docs/reference/writing-agent-harness-profile.md](docs/reference/writing-agent-harness-profile.md) |
| 查看当前建设 todo | [docs/project/todolist.md](docs/project/todolist.md) |
| 新建或整理文章目录（`content/origin/` 必须使用 `YYYY-MM-DD-topic` 格式） | [docs/project/directory-layout.md](docs/project/directory-layout.md) |
| 规划自动化能力 | [docs/project/automation-roadmap.md](docs/project/automation-roadmap.md) |
| 常规写作、研究、润色 | [docs/workflows/writing-overview.md](docs/workflows/writing-overview.md) |
| 早期灵感脑暴、确定 writing brief / outline | [docs/workflows/writing-overview.md](docs/workflows/writing-overview.md#ideation-first) |
| 微信公众号排版、草稿箱、发布 | [docs/workflows/wechat-writing-publishing.md](docs/workflows/wechat-writing-publishing.md) |
| 查看项目 skills 边界 | [docs/reference/skills.md](docs/reference/skills.md) |
| 沉淀 memory、复盘、skill 自我进化 | [docs/reference/self-evolution.md](docs/reference/self-evolution.md) |
| 使用本机 scratch memory | [docs/reference/local-memory.md](docs/reference/local-memory.md) |
| 图片、封面、正文插图、视频素材/剪辑 | [docs/reference/visuals.md](docs/reference/visuals.md) |
| 微信发布复盘与坑点 | [docs/retrospectives/2026-06-05-wechat-publish.md](docs/retrospectives/2026-06-05-wechat-publish.md) |
| 选 HTML 解析 / 内容抽取栈（bs4 / selectolax / trafilatura / markdownify） | [docs/benchmark/html-parser-stack-bench.md](docs/benchmark/html-parser-stack-bench.md) |
| Superpowers specs / plans 约定 | [docs/README.md](docs/README.md#superpowers) |

总索引见 [docs/README.md](docs/README.md)。

## Current Defaults

- 微信公众号 renderer 支持五种 style：`agent-flow`（纯白底、无卡片、扇形流式排版，技术评论/观点文默认）、`impact-rational`（白底带左边框 hero + 目录/摘要面板的技术评论 style，备用）、`literary-essay`（个人散文/随笔）、`cultural-essay`（文化现象/城市/音乐/文旅随笔）、`tech-blog`（通用技术博客）。默认偏向 `agent-flow`：微信夜间模式会自动反色，带浅色卡片+背景的 style 在暗色下会显得很亮，纯白无卡片排版更稳。
- 文章插图生成默认使用 `article-illustration --style-profile auto` 按文章气质选择画风。
- 早期灵感脑暴使用 project skill：`article-ideation`。
- 文章打磨使用 project skill：`polish-article`。
- 发布前文章 readiness 检查使用 project skill：`article-readiness-check`。
- 微信公众号 HTML preview 使用 project skill：`wechat-article-renderer`；生成后可用 `node .agents/skills/wechat-article-renderer/scripts/preview-server.mjs <dir>` 本地预览。
- 微信公众号文章提取使用 project skill：`wechat-article-fetcher`；输入 URL 提取正文、元数据和图片到结构化素材包，支持 `--output-dir content/inbox/articles/` 直接入库。
- 微信公众号发布流程使用 project skill：`wechat-publish-workflow`；底层上传器默认用 `wechat-article-publisher`（Playwright，已验证文章流程 + 标题/作者/摘要 + 串行正文图片上传 + 草稿保存；封面通常在草稿箱 final review 时手动设置）。迁移背景见 [docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md](docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md)。
- 发布或交付后的写作任务收尾使用 project skill：`writing-task-closeout`。
- 不使用 paid `md2wechat` API。
- `docs/superpowers/specs/` 和 `docs/superpowers/plans/` 是 Superpowers 长期文档目录；`.superpowers/` 是 generated scratch，通常忽略。

## Self-Evolution Loop

执行任务过程中，如果遇到新的可复用经验，agent 应主动判断是否沉淀：

- 临时想法、未验证 todo、本机上下文：写入 `.local-memory/`。
- 已验证的 workflow 改进、坑点、检查清单：更新 `docs/`。
- 高频规则或项目级行为边界：更新 `AGENTS.md`，保持简短。
- 可重复执行 3 次以上、边界清晰的能力：沉淀为 `.agents/skills/*`。
- 已经跑通且值得自动化的步骤：补充 scripts 或 workflow runbook。

不要把一次性细节过度制度化；先验证，再沉淀。

## Publish Boundary

Agent 可以创建草稿、检查图片、检查封面、检查链接，并报告草稿创建结果（如微信公众号编辑页 URL 中的 `appmsgid`）。不要未经用户明确确认点击最终发布 / 群发。
