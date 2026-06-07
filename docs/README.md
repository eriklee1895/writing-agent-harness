# Docs

这里是 `writing-agent-harness` 的文档路由层。原则：高频规则放在 `AGENTS.md`；低频细节放到分层 docs，需要时再读取。

## Project

- [project/vision.md](project/vision.md)
  - 项目愿景、两种 AI 自动化写作场景、分发目标。

- [project/directory-layout.md](project/directory-layout.md)
  - 推荐目录结构、文章自包含目录、历史目录迁移原则。

- [project/automation-roadmap.md](project/automation-roadmap.md)
  - 从 human-in-the-loop 到 scheduled agents 的路线图和安全边界。

- [project/todolist.md](project/todolist.md)
  - 当前项目建设 todo：Feishu / Notion 到 Markdown / MDX、Astro 博客主阵地、多渠道分发。

## Workflows

- [workflows/writing-overview.md](workflows/writing-overview.md)
  - 从 idea / Feishu / notes 到 Markdown / MDX 的通用写作流程。

- [workflows/wechat-writing-publishing.md](workflows/wechat-writing-publishing.md)
  - 微信公众号写作、排版、HTML preview、草稿箱同步和发布前验证。

- [workflows/markdown-to-wechat.md](workflows/markdown-to-wechat.md)
  - 旧入口，后续可展开为更底层的 Markdown/MDX -> 微信公众号同步技术方案。

## Reference

- [reference/writing-agent-harness-profile.md](reference/writing-agent-harness-profile.md)
  - `writing-agent-harness` 的身份、职责、运行模式、边界和协作方式。

- [reference/skills.md](reference/skills.md)
  - 当前项目 skills、用途边界、命名和保留原因。

- [reference/self-evolution.md](reference/self-evolution.md)
  - 遇到新坑点、新技巧、workflow 改进和 skill 缺陷时，如何沉淀到 docs / skills。

- [reference/visuals.md](reference/visuals.md)
  - 图片生成、微信公众号封面、正文插图和 asset 规则。

## Retrospectives

- [retrospectives/2026-06-05-wechat-publish.md](retrospectives/2026-06-05-wechat-publish.md)
  - Cloudflare/Vite 微信公众号文章发布复盘、限制坑点和可验证信号。

- [retrospectives/2026-06-06-wechat-cdp-only-decision.md](retrospectives/2026-06-06-wechat-cdp-only-decision.md)
  - 微信公众号发布只维护 CDP/browser 主路径的决策、API 放弃原因和扫码登录边界。

## Superpowers

- [superpowers/specs/](superpowers/specs/)
  - `brainstorming` skill 的默认设计文档目录。

- [superpowers/plans/](superpowers/plans/)
  - `writing-plans` skill 的默认实施计划目录。

`.superpowers/` 是运行时 scratch / visual companion 预览产物目录，通常不需要读取，也不应提交。

## Writing Rules

- 文档以中文为主，技术关键词和命令保持 English。
- Runbook 要写成 agent 可以执行的 checklist，而不是只写理念。
- 复盘要记录真实坑点、错误信息、可验证信号和下次避免方式。
- 先记录已经跑通的流程，再设计重型自动化。
