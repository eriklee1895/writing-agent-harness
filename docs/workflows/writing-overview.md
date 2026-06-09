# 写作总流程

本文记录通用写作 workflow。渠道细节请跳转到对应 runbook。

## Canonical Source

尽量把 Markdown / MDX 作为 repo 内 canonical source。

飞书文档可以作为原始写作入口，但进入 repo 后应同步/转换为 Markdown / MDX，方便 diff、review、render 和 publish automation。

## Workflow

1. 捕捉 idea / inspiration。用户可以先给灵感、素材、判断、链接或几段粗糙想法。
2. 进入 `article-ideation`，通过脑暴校准 central question、target reader、thesis、angle、tone、anti-goals 和 distribution channel。
3. 产出 `writing brief`、`research questions` 和初版 outline。不要在没理解清楚前急着写正文。
4. 做 research。遇到 current events、company/product facts、pricing、laws、fast-moving tech topics 时，必须查证并写清具体日期。
5. 根据 writing brief 和 research 形成 full draft。
6. 使用 `polish-article` 打磨逻辑、文风、专业深度和题材气质。
7. 只有当图片或视频能帮助理解、传播或渠道呈现时，才生成或优化 visuals。
   - 图片/封面/信息图走 `article-illustration`。
   - 已知视频 URL 先走 `video-material-ingest` 留痕。
   - 文章内视频先走 `video-highlight-select` 做人工辅助选片，再走 `article-video-clip` 做轻包装。
8. 使用 `article-readiness-check` 做发布前检查：正文 readiness、事实边界、Markdown/MDX hygiene、frontmatter、图片/视频引用、渠道 handoff 和 publish blockers。
9. 按不同渠道做 packaging。
10. 在声称 ready 之前先 verify rendered output。
11. 用户确认 preview/draft 后，才进入 publish。
12. 发布、创建草稿或最终交付之后，使用 `writing-task-closeout` 做任务收尾：回填发布状态、归档媒体到 `.local-archive/YYYY-MM-DD-slug/`、复盘、memory / skill 决策和 git / task handoff。

## Ideation First

高质量写作不要从“直接写稿”开始，而要先把灵感校准成可执行的写作设计。

`article-ideation` 阶段应该帮助 Erik 和 agent 对齐：

- 这篇文章真正要回答的问题是什么；
- 为什么现在值得写；
- 写给谁；
- 核心判断和锋芒是什么；
- 哪些角度值得展开；
- 不要写成什么样；
- 需要查证哪些事实；
- 初版 outline 应该如何组织。

这个阶段的产物是 `writing brief`，不是完整正文。确认 brief 后，再进入 research / draft，文章质量会更稳定。

## Two Modes

### AI 自主选题

Agent 主动 web search、发现热点、判断选题价值、构思文章框架并完成写作。该模式还在规划中，默认不要自动发布。

### 个人写作助手

Erik 提供主题、灵感、素材、判断和雏形；agent 先用 `article-ideation` 做思路校准，再做研究、组织、表达增强和渠道派生。这是当前主要模式。

## Channel Router

- 微信公众号：读 [wechat-writing-publishing.md](wechat-writing-publishing.md)。
- 个人博客：尚未创建。未来补 [../project/automation-roadmap.md](../project/automation-roadmap.md) 中的 blog publishing skill。
- 其他平台：视为 downstream repackaging targets。保持一个 canonical Markdown / MDX source，再派生不同平台版本。
