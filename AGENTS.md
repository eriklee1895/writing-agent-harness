# AGENTS.md

这个 repo 是 Erik 的个人 AI 自动化写作 harness。它用项目级 skills、docs runbooks 和可追踪 Markdown / MDX source，帮助 Codex / Claude Code / Hermes / OpenClaw / Pi 等 agents 完成选题、研究、写作、润色、配图、排版、分发与复盘。

本文件只保留高频规则和文档路由。低频细节使用 progressive disclosure：先读 `AGENTS.md`，再按任务读取 `docs/` 中的对应文档。

## Always

- 保留用户 edits；不要 revert 用户改动，除非用户明确要求。
- 不要打印、提交或泄漏 secrets、本地运行态、账号态数据和依赖目录。
- Current events、company/product facts、pricing、laws、fast-moving tech topics 必须查证，并写清具体日期。
- repo 内长期 canonical source 是 Markdown / MDX。飞书文档、Notion 等可以作为上游写作入口；进入 repo 后要同步或转换成可追踪文本。
- 图片生成优先使用系统 `$imagegen` skill，不要重建项目重复的 `gpt-image-gen`。
- 任何最终发布动作都需要 user final review，除非用户明确授权自动发布。
- 先做 small, practical automation；不要把未跑通的能力写成已可用能力。
- 遇到可复用的新坑点、新技巧、workflow 改进或 skill 缺陷，随手沉淀到 docs / skills。
- 当某项能力已经值得 project-level skill 化时，主动建议并沉淀为 `.agents/skills/*`。

## Docs Router

根据任务读取最小必要文档：

| 任务 | 先读 |
| --- | --- |
| 了解项目愿景、写作场景 | [docs/project/vision.md](docs/project/vision.md) |
| 了解完整 AI 写作工作流、skill 分工、目录约定 | [docs/workflows/ai-writing-workflow.md](docs/workflows/ai-writing-workflow.md) |
| 理解 writing-agent-harness 身份和边界 | [docs/reference/writing-agent-harness-profile.md](docs/reference/writing-agent-harness-profile.md) |
| 查看当前建设 todo | [docs/project/todolist.md](docs/project/todolist.md) |
| 新建或整理文章目录 | [docs/project/directory-layout.md](docs/project/directory-layout.md) |
| 规划自动化能力 | [docs/project/automation-roadmap.md](docs/project/automation-roadmap.md) |
| 常规写作、研究、润色 | [docs/workflows/writing-overview.md](docs/workflows/writing-overview.md) |
| 早期灵感脑暴、确定 writing brief / outline | [docs/workflows/writing-overview.md](docs/workflows/writing-overview.md#ideation-first) |
| 微信公众号排版、草稿箱、发布 | [docs/workflows/wechat-writing-publishing.md](docs/workflows/wechat-writing-publishing.md) |
| Markdown / MDX 到微信公众号同步方案 | [docs/workflows/markdown-to-wechat.md](docs/workflows/markdown-to-wechat.md) |
| 查看项目 skills 边界 | [docs/reference/skills.md](docs/reference/skills.md) |
| 沉淀 memory、复盘、skill 自我进化 | [docs/reference/self-evolution.md](docs/reference/self-evolution.md) |
| 图片、封面、正文插图 | [docs/reference/visuals.md](docs/reference/visuals.md) |
| 微信发布复盘与坑点 | [docs/retrospectives/2026-06-05-wechat-publish.md](docs/retrospectives/2026-06-05-wechat-publish.md) |
| Superpowers specs / plans 约定 | [docs/README.md](docs/README.md#superpowers) |

总索引见 [docs/README.md](docs/README.md)。

## Current Defaults

- 微信公众号 renderer 支持三种 style：`impact-rational`（技术评论/观点文，默认）、`literary-essay`（个人散文/随笔，推荐用于文学类）、`tech-blog`（通用技术博客）。
- 文章插图生成默认使用 `watercolor-illustration` 风格、`zh` 语言；Python 脚本一律用 `uv run`。
- 早期灵感脑暴使用 project skill：`article-ideation`。
- 文章打磨使用 project skill：`polish-article`。
- 微信公众号 HTML preview 使用 project skill：`wechat-article-renderer`；生成后可用 `node scripts/preview-server.mjs <dir>` 本地预览。
- 微信公众号发布流程使用 project skill：`wechat-publish-workflow`；底层上传器当前可复用 `baoyu-post-to-wechat`。
- 不使用 paid `md2wechat` API。
- `docs/superpowers/specs/` 和 `docs/superpowers/plans/` 是 Superpowers 长期文档目录；`.superpowers/` 是 generated scratch，通常忽略。

## Quick Commands

生成 WeChat preview：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs /absolute/path/to/article.md --style literary-essay
```

列出 WeChat renderer styles：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs --list-styles
```

本地预览（渲染后可手动启动 server）：

```bash
node .agents/skills/wechat-article-renderer/scripts/preview-server.mjs /absolute/path/to/article-dir
# 然后打开 http://localhost:49255/
```

或一步完成渲染+预览：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs /absolute/path/to/article.md --style literary-essay --serve
```

生成插图（Python 脚本一律使用 `uv run`）：

```bash
uv run .agents/skills/article-illustration/scripts/generate_doc_illustration.py \
  --title "插画标题" --brief "描述" \
  --style-profile watercolor-illustration --size wechat-cover-hd
```

## Publish Boundary

Agent 可以创建草稿、检查图片、检查封面、检查链接、报告 `appmsgid`。不要未经用户明确确认点击最终发布 / 群发。
