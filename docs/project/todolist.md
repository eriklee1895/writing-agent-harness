# Project Todo List

记录 Erik 对 `writing-agent-harness` 的当前建设想法和待办。本文是活文档：先保存方向，再逐步拆成 specs、plans、skills 和可运行脚本。

更新日期：2026-06-06

## North Star

终极愿景：

```text
Feishu / Notion / etc.
-> Markdown / MDX
-> Blog as primary home base
   Astro + Cloudflare + GitHub Actions
-> downstream distribution
   WeChat Official Account / 掘金 / others
```

这个项目不强迫原文写作发生在 Markdown 里。飞书文档和 Notion 可以继续作为主力写作、笔记和早期沉淀入口；进入 repo 后，再转换成 Markdown / MDX，获得 diff、review、自动化渲染、博客发布和多渠道派生能力。

## Current Preference

- 原文写作主力：飞书文档 / Notion。
- 不把直接 Markdown 写作作为默认要求；Typora 也不是当前最顺手的主入口。
- 笔记沉淀主力：Notion。
- repo 内长期 canonical source：Markdown / MDX。
- 飞书文档 `<->` Markdown：当前已通过 `lark-cli` 跑得比较顺手，优先继续固化。
- Notion `<->` Markdown：尚未完全打通，待调研 Notion MCP、Notion API 和 `notion-to-md` 方案。

## Source Sync Todos

- [ ] 沉淀飞书文档到 Markdown / MDX 的标准 runbook：
  - [ ] 记录 `lark-cli` 常用命令、认证方式、导出路径和失败排查。
  - [ ] 明确飞书文档 metadata 如何映射到 frontmatter。
  - [ ] 验证图片、表格、代码块、标题层级、引用块和链接的转换质量。
  - [ ] 判断是否值得项目级 skill 化为 `feishu-to-markdown` 或合并进 writing workflow。
- [ ] 调研 Notion 到 Markdown / MDX 的路线：
  - [ ] Notion MCP：确认是否适合 agent 直接读取 page / database / block。
  - [ ] Notion API：确认认证、database 查询、page 拉取、block 遍历、rate limit 和图片下载策略。
  - [ ] `notion-to-md`：做一个小样本 page 转换实验，检查 frontmatter、嵌套 block、callout、toggle、database relation、media 的保真度。
  - [ ] 决定 Notion sync 的首个最小可用范围：单 page 导出、database 批量导出，还是指定 collection 增量同步。
- [ ] 定义统一 source package：
  - [ ] 每篇文章一个目录，包含 `article.md` / `article.mdx`、`notes.md`、`assets/` 和渠道派生稿。
  - [ ] frontmatter 统一字段：title、subtitle、slug、date、updated、source、source_url、channels、tags、status。
  - [ ] 保留 upstream source link，方便回溯飞书或 Notion 原文。

## Blog Primary Home Todos

- [ ] 建立 Astro 博客实验工程。
- [ ] 设计 Astro content collections schema，兼容当前 Markdown / MDX frontmatter。
- [ ] 设计文章详情页、列表页、标签页和 RSS。
- [ ] 接入 Cloudflare Pages。
- [ ] 接入 GitHub Actions：
  - [ ] lint / typecheck / build。
  - [ ] preview deploy。
  - [ ] production deploy。
- [ ] 形成 `Markdown / MDX -> Blog` 发布 skill 或 runbook。
- [ ] 明确博客自动发布边界：博客可以先尝试 preview-first automation，正式 production publish 仍保留人工确认，直到流程稳定。

## Distribution Todos

- [ ] 微信公众号：
  - [ ] 继续完善 `wechat-article-renderer` 和 `wechat-publish-workflow`。
  - [ ] 保持 `impact-rational` 为当前默认 style preset。
  - [ ] 发布前必须有 HTML preview、草稿箱检查和 user final review。
- [ ] 掘金：
  - [ ] 调研 Markdown 兼容性、图片上传、frontmatter/摘要/标签映射。
  - [ ] 先做手动 runbook，再考虑自动发布。
- [ ] 其他渠道：
  - [ ] 暂时作为 downstream repackaging targets，不抢先做重自动化。
  - [ ] 每个渠道独立记录 format constraints、asset rules、publish boundary 和 rollback path。

## Near-Term Build Order

1. 把飞书文档 `<->` Markdown 的现有成功经验写成 runbook。
2. 用一个真实 Notion page 做 `Notion -> Markdown / MDX` 小实验。
3. 定义统一 frontmatter 和 article folder contract。
4. 让一篇文章从 `content/drafts/` 派生到微信公众号 preview。
5. 建立 Astro 博客最小工程，让同一篇文章能被博客消费。
6. 再抽象 project-level skills，避免把没跑通的能力包装成“已完成”。

## Open Questions

- Notion 是只作为输入源，还是也需要 Markdown 回写到 Notion？
- Notion database 的哪些字段应该成为博客 / 微信共同 metadata？
- Blog production publish 是否需要人工确认，还是只要 GitHub PR review 即可？
- 掘金等其他渠道是否需要登录态浏览器自动化，还是先手动复制粘贴更稳？
- 文章目录是否从现在开始全部进入 `content/drafts/`，历史 `微信公众号/` 是否以后再迁移？
