# 项目愿景

`writing-agent-harness` 是 Erik 的个人 AI 自动化写作 harness。

它的目标是成为 AI 写作领域的 Superpowers：不是做一个单一写作脚本，也不是 writer bot，而是沉淀一套面向写作 agents 的 skills methodology。

它受到 [obra/superpowers](https://github.com/obra/superpowers) 启发，但服务于写作、研究、配图、分发和复盘：沉淀可组合 writing skills、publishing workflows、docs runbooks 和可追踪 source，把 Claude Code / Codex / Hermes / OpenClaw / Pi 等 agents 接入 Erik 的写作流程。

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

写作的 canonical source 未来会以 Markdown / MDX 为主。原始思考和初稿可能来自飞书文档，后续会自动同步或转换为 Markdown / MDX，再分发到个人博客、微信公众号和其他平台。

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
- 用 `polish-article` 打磨逻辑、文风和专业深度。
- 根据渠道生成博客 / 微信公众号版本。

这个场景强调 human-in-the-loop：人的判断是核心，agent 做研究、组织和表达增强。

## 分发目标

### 个人博客

未来计划：

```text
Astro + Cloudflare Pages + GitHub Actions
```

博客还没创建。当前原则是先保持 Markdown / MDX 和 assets 整理清楚，方便未来迁移到 Astro content collections。

### 微信公众号

微信公众号已经跑通过一次完整流程：

```text
Markdown source -> WeChat HTML preview -> 草稿箱 -> final human review -> publish
```

当前默认微信公众号 style preset：

```text
impact-rational
中文名：冲击开场，理性正文
```

详细流程见 [../workflows/wechat-writing-publishing.md](../workflows/wechat-writing-publishing.md)。
