# 项目愿景
**GitHub:** [eriklee1895/writing-agent-harness](https://github.com/eriklee1895/writing-agent-harness)


`writing-agent-harness` 是 Erik 的个人 AI 自动化写作 harness。

它的目标是成为 AI 写作领域的 Superpowers：不是做一个单一写作脚本，也不是 writer bot，而是沉淀一套面向写作 agents 的 skills methodology。

它受到 [obra/superpowers](https://github.com/obra/superpowers) 启发，但服务于写作、研究、配图、分发和复盘：沉淀可组合 writing skills、publishing workflows、docs runbooks 和可追踪 source，把 Claude Code / Codex / Hermes / OpenClaw / Pi 等 agents 接入 Erik 的写作流程。

它也是一个会自我进化的 writing harness：通过 memory、retrospectives、local scratch、docs runbooks 和 project skills，把真实写作、发布、调试中的踩坑经验沉淀下来，持续修复 workflow、优化 skills，让系统越用越贴合 Erik 的写作方式。

它是一套面向写作活动的 agent harness：

```text
research -> outline -> draft -> polish -> visuals -> packaging -> publish -> review
```

更完整的 agent profile 见 [../reference/writing-agent-harness-profile.md](../reference/writing-agent-harness-profile.md)。

## 当前定位

这个 repo 主要承担三件事：

- 作为个人写作工作流的 memory 和规范中心。
- 管理项目级 AI writing skills。
- 存放文章源稿、渠道派生稿、视觉资产和发布流程文档。

写作的 canonical article 以 `content/origin/` 中的 Markdown / MDX 为主。原始思考和初稿可能来自飞书文档或 Notion，进入 repo 后同步或转换为 Markdown / MDX，再分发到个人博客（primary home base）、微信公众号和其他平台。

## 写作场景

### 场景 1：AI 自主选题与发布

远期目标是让 agents 通过 cron / scheduled runs 定时触发：

```text
自主 web search -> 挖掘热点和价值主题 -> 判断选题价值 -> 构思文章框架 -> research -> 写作 -> polish -> 配图 -> 发布到博客
```

这个场景强调 agent autonomy：agent 不只是执行一个给定题目，而是主动发现值得写的主题。

### 场景 2：个人写作助手

Erik 提供主题、灵感、素材、判断和文章雏形；agent 负责：

- 深度收集相关信息。
- 汇总事实和观点。
- 建立文章结构。
- 撰写初稿。
- 用 `polish-article` 打磨逻辑、register、表达质感和专业深度。
- 根据渠道生成博客 / 微信公众号版本。

这个场景强调 human-in-the-loop：人的判断是核心，agent 做研究、组织和表达增强。

## 分发目标

### 个人博客（primary home base）

已上线：

```text
Astro 6 + Tailwind v4 + MDX → Cloudflare Pages（main 分支自动部署）
URL: https://eriklee-blog.pages.dev/
本地 repo: /Users/eriklee/code/my_project/eriklee-blog
```

同步路径：

```text
writing-agent-harness/content/origin/YYYY-MM-DD-<slug>/
  → scripts/sync_origin_to_blog.py
  → eriklee-blog/src/content/posts/
  → GitHub push main
  → Cloudflare Pages auto-deploy
```

当前状态：基于 AstroPaper 主题深度定制，已完成原生 taxonomy sidebar、PostExplorer 列表布局、首页改版、中文本地化、暗色模式、Pagefind 搜索、图片 lightbox、Shiki 双主题代码高亮、View Transitions、RSS、动态 OG 图。仍在持续优化 UI 一致性和阅读体验，详见 [todolist.md](todolist.md)。

发布 skill：[`erik-blog-publish-workflow`](../../.agents/skills/erik-blog-publish-workflow/SKILL.md)。
发布边界：`git push origin main` 触发公开发布，需要用户明确确认。

### 微信公众号

已跑通完整流程：

```text
Canonical Markdown → WeChat HTML preview (warm-editorial style) → Playwright 草稿箱 → final human review → publish
```

默认 style preset：`warm-editorial`（暖纸张底编辑随笔风，技术深度长文默认）。
详细流程见 [../workflows/wechat-writing-publishing.md](../workflows/wechat-writing-publishing.md)。

### 其他渠道

掘金等其他下游渠道暂未启动；当前集中精力把博客建设好，再扩展分发。
