# Docs

这里是 `writing-agent-harness` 的文档路由层。原则：高频规则放在 `AGENTS.md`；低频细节放到分层 docs，需要时再读取。

## Project

- [project/vision.md](project/vision.md)
  - 项目愿景、两种 AI 自动化写作场景、分发目标。

- [project/directory-layout.md](project/directory-layout.md)
  - 推荐目录结构、文章自包含目录、历史目录迁移原则。

- [project/prepare-environment.md](project/prepare-environment.md)
  - 新机器 / 新 agent 环境的 runtime、外部 skills 和本机账号态准备。

- [project/automation-roadmap.md](project/automation-roadmap.md)
  - 从 human-in-the-loop 到 scheduled agents 的路线图和安全边界。

- [project/todolist.md](project/todolist.md)
  - 当前项目建设 todo：Feishu / Notion 到 Markdown / MDX、Astro 博客主阵地、多渠道分发。

## Workflows

- [workflows/ai-writing-workflow.md](workflows/ai-writing-workflow.md)
  - AI 写作自动化 harness 全景、目录约定、skill 分工和关键约束。

- [workflows/writing-overview.md](workflows/writing-overview.md)
  - 从 idea / Feishu / notes 到 Markdown / MDX 的通用写作流程。

- [workflows/wechat-writing-publishing.md](workflows/wechat-writing-publishing.md)
  - 微信公众号写作、排版、HTML preview、草稿箱同步和发布前验证。

## Skills

- [skills/skills-guide.md](skills/skills-guide.md)
  - Skill 开发指南：Python 脚本规范、路径引用约定、脚本接口设计。

- [skills/skills-list.md](skills/skills-list.md)
  - 当前项目 skills 列表、用途边界、命名和保留原因。

## Reference

- [reference/writing-agent-harness-profile.md](reference/writing-agent-harness-profile.md)
  - `writing-agent-harness` 的身份、职责、运行模式、边界和协作方式。

- [reference/self-evolution.md](reference/self-evolution.md)
  - 遇到新坑点、新技巧、workflow 改进和 skill 缺陷时，如何沉淀到项目 docs、`AGENTS.md` 或 `.agents/skills/`。

- [reference/local-memory.md](reference/local-memory.md)
  - `.local-memory/` 本机 scratch memory 的使用边界和迁移规则。

- [reference/visuals.md](reference/visuals.md)
  - 图片生成、视频素材、文章视频剪辑、微信公众号封面、正文插图和 asset 规则。

- [reference/article-illustration/README.md](reference/article-illustration/README.md)
  - `article-illustration` 的 guide、风格选择、prompt pattern 和历史优质生图案例。

- [benchmark/html-parser-stack-bench.md](benchmark/html-parser-stack-bench.md)
  - HTML 解析与内容抽取栈选型：BeautifulSoup4 / Selectolax / Trafilatura / markdownify 的定位、benchmark、维护状态、按场景的选型矩阵和当前 `wechat-article-fetcher` 决策。

- [benchmark/dynasty-poster-series-case-study.md](benchmark/dynasty-poster-series-case-study.md)
  - 7 张中国朝代兴衰史海报的生图技术案例：情绪弧配色法、Workflow 多 agent 并行编排、gpt-image-2 密集中文排版 prompt 结构、scaffolding preset 实战验证。

## Retrospectives

- [retrospectives/2026-06-05-wechat-publish.md](retrospectives/2026-06-05-wechat-publish.md)
  - Cloudflare/Vite 微信公众号文章发布复盘、限制坑点和可验证信号。

- [retrospectives/2026-06-06-wechat-cdp-only-decision.md](retrospectives/2026-06-06-wechat-cdp-only-decision.md)
  - 微信公众号发布只维护 CDP/browser 主路径的决策、API 放弃原因和扫码登录边界。

- [retrospectives/2026-06-07-banshengxue.md](retrospectives/2026-06-07-banshengxue.md)
  - 《半生雪》个人散文从 ideation、插图、renderer 到微信公众号草稿箱的全流程复盘。

- [retrospectives/2026-06-08-video-material-clip.md](retrospectives/2026-06-08-video-material-clip.md)
  - 视频素材摄取、裸 mp4 包装、HyperFrames 模板 contract 和文章视频剪辑复盘。

- [retrospectives/2026-06-11-playwright-wechat-migration-analysis.md](retrospectives/2026-06-11-playwright-wechat-migration-analysis.md)
  - 微信公众号发布从 baoyu 浏览器/CDP 到 Playwright 持久 profile 的迁移分析与决策。

- [retrospectives/2026-06-15-skill-creator-wechat-table-flex.md](retrospectives/2026-06-15-skill-creator-wechat-table-flex.md)
  - 微信公众号表格从 `<table>` 标签切换到 flex `<div>` 渲染的复盘（避免微信编辑器套虚线编辑框）。

- [retrospectives/2026-06-18-seedance-concurrency-benchmark.md](retrospectives/2026-06-18-seedance-concurrency-benchmark.md)
  - Seedance 视频生成并发能力 benchmark（串行 vs 4 并发）与提交/轮询策略选型。

- [retrospectives/2026-06-21-volcengine-bigmusic-end-to-end.md](retrospectives/2026-06-21-volcengine-bigmusic-end-to-end.md)
  - 火山引擎 BigMusic BGM 生成端到端集成与坑点记录。

- [retrospectives/2026-06-28-article-to-notion-ntn-cli-refactor.md](retrospectives/2026-06-28-article-to-notion-ntn-cli-refactor.md)
  - article-to-notion 从手写 REST + md-to-blocks 重构到官方 ntn CLI 的全流程、`notion-cli` 基础 skill 沉淀、ntn CLI 14 个坑点汇总、sentinel-marker 图片交错与 normalize 防御层设计。

## Superpowers

- [superpowers/specs/](superpowers/specs/)
  - `brainstorming` skill 的默认设计文档目录。

- [superpowers/plans/](superpowers/plans/)
  - Superpowers 生成的实施计划目录。

`.superpowers/` 是运行时 scratch / visual companion 预览产物目录，通常不需要读取，也不应提交。

## Writing Rules

- 文档以中文为主，技术关键词和命令保持 English。
- Runbook 要写成 agent 可以执行的 checklist，而不是只写理念。
- 复盘要记录真实坑点、错误信息、可验证信号和下次避免方式。
- 先记录已经跑通的流程，再设计重型自动化。
