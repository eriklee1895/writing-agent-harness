---
name: article-readiness-check
description: "发布前文章 readiness 检查。Use when the user says ready/发布前检查/最后看一遍/能不能进排版/能不能建草稿, or asks whether a Markdown/MDX article is ready for WeChat/blog rendering, 草稿箱, channel packaging, or final human review; verify editorial readiness, facts, Markdown/MDX hygiene, frontmatter, image/video references, and channel handoff blockers without doing post-publish cleanup."
---

# Article Readiness Check

## Overview

这个 skill 用于 `polish-article` 之后、`wechat-article-renderer` / blog build / 草稿箱之前，判断 canonical Markdown / MDX 是否已经能进入渠道包装。

它只负责 pre-publish readiness，不负责发布后的归档、复盘、memory、git 或任务关闭。那些交给 `writing-task-closeout`。

如果 repo 根目录存在 `SOUL.md`，做作者声音和 register 判断前必须读取它。

## Workflow

1. 找到 canonical source：
   - 优先使用用户给出的 Markdown / MDX 文件路径。
   - 如果只有渲染产物、飞书/Notion 文档或网页内容，先同步/转换成可追踪 Markdown / MDX。
   - 不要把 WeChat HTML preview、草稿箱页面或临时复制内容当成长期 source。
2. 判断检查模式：
   - `audit-only`: 用户只是问“能不能发/最后看看”。输出 findings，不改文件。
   - `fix-and-check`: 用户要求“直接帮我收一下”。做 scoped edits，并报告改动。
   - `channel-handoff`: 用户准备进微信公众号、博客或其他渠道。重点检查 channel blockers。
3. 读取必要上下文：
   - `SOUL.md`：作者声音、register、anti-style。
   - article source：frontmatter、标题、正文、链接、图片、脚注、引用。
   - 如目标是微信公众号，必要时读取 `docs/workflows/wechat-writing-publishing.md`。
4. 逐项检查并修复或标记 blockers。
5. 结束时给出 readiness verdict 和下一步 handoff。

## Checks

### Editorial Readiness

- title、subtitle、opening 是否承接同一个 thesis。
- section headings 是否形成清晰阅读路径，不只是漂亮短句。
- 每节是否承担不同功能：背景、判断、证据、推论、收束不要混成一团。
- 结尾是否真正收束文章，而不是机械 CTA、宏大口号或突然拔高。
- 是否仍有重复铺垫、AI 味转场、营销腔、空泛金句。
- register 是否稳定，并符合 `SOUL.md` 的作者气质。

如果发现结构性问题，不要只做字词润色。先说明 blocker；用户授权编辑时再重排或删改。

### Fact And Source Readiness

- current events、company/product facts、pricing、laws、fast-moving AI / developer tooling facts 必须查证，并写清具体日期。
- 区分 `fact / inference / speculation`。不要把推断写成已发生事实。
- 检查公司名、产品名、人名、时间、数字、引用、链接是否一致。
- 引用必须有来源边界；不要补造原话、来源或链接。
- 对无法当场确认的事实，标记为 publish blocker 或 `needs verification`，不要给 ready。

### Markdown / MDX Hygiene

- 无 `TODO`、`TBD`、占位标题、空链接、调试备注或未处理批注。
- frontmatter 与正文一致：title、description/summary、date、tags、cover、canonical channel、publish status。
- Markdown links 有效且语义清楚；公众号版本不应依赖 external `href`。
- images、video refs、local asset paths 存在，并可追溯到 `content/origin/&lt;slug&gt;/assets/`、素材包或 `.local-archive/` 记录。
- 代码块、表格、脚注、引用块、MDX components 没有破坏语法。
- 文件名、目录、资产命名符合 repo 的目录约定；不确定时读取 `docs/project/directory-layout.md`。

### Visual And Media References

- 只有当 visuals 帮助理解、传播或渠道呈现时才要求补图。
- 封面图、正文图、视频 preview frame 是否与文章气质和渠道一致。
- 生成图必须有 source prompt / metadata；没有 prompt / metadata 的生成图不算可追溯。
- 图片和视频二进制默认不进本 repo；readiness 阶段只确认引用、metadata、alt/caption、发布用途和可找回线索完整。
- 本地视频素材应来自 `video-material-ingest` 素材包，并有 `manifest.json` / `sources.md`。
- 没有确认使用权、来源或插入位置的视频，不要标记 ready。

### Channel Handoff

- 微信公众号：内容 ready 后交给 `wechat-article-renderer`；preview 确认后再交给 `wechat-publish-workflow`。
- Blog / MDX：确认 frontmatter、canonical URL、图片引用、MDX 组件和 build/render 风险。
- 多渠道：保留 canonical Markdown / MDX article，再派生 channel-specific version；不要把渠道版本反向覆盖 origin article。
- 跨渠道复用：判断是否值得同步到 blog、知乎、即刻、小红书等；如需要，记录每个渠道要改的标题、摘要、长度、链接和图片策略。
- 最终发布、群发、上线动作必须由用户 final review 或明确授权。

## Editing Rules

当用户要求直接检查并给出文件路径时：

- 优先做小范围、可解释 edits。
- 可以修错别字、标题一致性、frontmatter、残留 TODO、明显重复、Markdown broken links、图片路径等。
- 可以补全 frontmatter、补齐图片 prompt / metadata 引用、更新 publish status。
- 大幅重排、删整节、改变 thesis 或补写大量事实前，先给 short editorial plan。
- 不要因为 readiness check 而把文章改成更平、更安全、更通用。
- 不要引入未经查证的新事实；需要查证时先 research。
- 不要处理 post-publish cleanup、`.local-archive/` 迁移、git commit 或任务关闭；这些交给 `writing-task-closeout`。

## Output Format

```markdown
## Verdict

Ready / Needs fixes / Blocked

## Must Fix

- ...

## Nice To Have

- ...

## Done

- ...

## Handoff

Next: `wechat-article-renderer` / `wechat-publish-workflow` / blog build / user final review
```

如果没有 blockers，明确说可以进入下一步，但不要声称已经发布。
