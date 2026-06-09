# Project Todo List

记录 Erik 对 `writing-agent-harness` 的当前建设想法和待办。本文是活文档：先保存方向，再逐步拆成 specs、plans、skills 和可运行脚本。

更新日期：2026-06-08

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
- repo 内长期 canonical source：`content/source/` 中的 Markdown / MDX。
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
  - [x] 使用 `content/source/YYYY-MM-DD-topic/` 作为可追踪 canonical Markdown / MDX 目录。
  - [x] 回填第一批现有文章到 `content/source/`，形成 source package 样例。
  - [x] 统一现有 `content/wechat/` 目录 slug，并在渠道稿 frontmatter 增加 `source:` 反向指针。
  - [ ] 每篇文章一个目录，包含 `article.md` / `article.mdx`、`notes.md` 和 `assets/`。
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

## Media Intelligence Todos

- [x] 设计并落地第一版视频高光选择 workflow：
  - [x] 明确 `video-highlight-select` 的输入输出：本地素材包、文章主题/段落意图、候选高光片段清单。
  - [x] 第一版保持 human-in-the-loop，只推荐候选片段，不自动决定最终剪辑。
  - [x] 与 `article-video-clip` 分层：前者负责找候选片段，后者负责已确认片段的裁切和轻包装。
- [ ] 规划 ASR/TTS provider abstraction：
  - [ ] 不默认依赖 HyperFrames 自带 Whisper；优先评估 Erik 已用过且体验好的 MiniMax、火山引擎等供应商。
  - [ ] ASR 第一优先服务于 transcript、视频高光选择、文章引用和字幕草稿。
  - [ ] TTS 第一优先服务于未来 HyperFrames 视频生成、动态摘要和短视频配音。
  - [ ] 先沉淀 provider-neutral 输入输出协议，再决定是否做 project-level skill，例如 `video-transcript-extract` / `speech-transcript-extract` / `article-video-narration`。
- [ ] 判断何时实现：
  - [ ] 当 `video-highlight-select` 进入实施，且至少 2 次真实视频任务需要 transcript 时，再实现 ASR skill。
  - [ ] 当 HyperFrames 视频生成进入真实文章/短视频生产，而不是 demo 阶段时，再实现 TTS skill。

## Near-Term Build Order

1. 把飞书文档 `<->` Markdown 的现有成功经验写成 runbook。
2. 用一个真实 Notion page 做 `Notion -> Markdown / MDX` 小实验。
3. 定义统一 frontmatter 和 article folder contract。
4. 让一篇文章从 `content/drafts/` promote 到 `content/source/`，再派生到微信公众号 preview。
5. 建立 Astro 博客最小工程，让同一篇文章能被博客消费。
6. 继续验证视频素材链路：用真实文章测试 `video-highlight-select`，再决定 ASR/TTS 是否进入实现。
7. 再抽象 project-level skills，避免把没跑通的能力包装成“已完成”。

## Open Questions

- Notion 是只作为输入源，还是也需要 Markdown 回写到 Notion？
- Notion database 的哪些字段应该成为博客 / 微信共同 metadata？
- Blog production publish 是否需要人工确认，还是只要 GitHub PR review 即可？
- 掘金等其他渠道是否需要登录态浏览器自动化，还是先手动复制粘贴更稳？
- 是否需要给 `source:` 反向指针补一个小脚本，批量检查渠道稿是否能找到 canonical article？
- ASR/TTS 供应商第一版选 MiniMax、火山引擎，还是做一个 provider interface 后再接多个实现？
