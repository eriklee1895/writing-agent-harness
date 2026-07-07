# Project Todo List

记录 Erik 对 `writing-agent-harness` 的当前建设想法和待办。本文是活文档：先保存方向，再逐步拆成 specs、plans、skills 和可运行脚本。

更新日期：2026-07-07

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
- repo 内长期 canonical article：`content/origin/` 中的 Markdown / MDX。
- 博客（primary home base）已上线：`/Users/eriklee/code/my_project/eriklee-blog`，Cloudflare Pages 部署 `https://eriklee-blog.pages.dev/`。
- 飞书文档 `<->` Markdown：当前已通过 `lark-cli` 跑得比较顺手，优先继续固化。
- Notion `<->` Markdown：**写入方向（Markdown / 网页 → Notion）已落地**——`article-to-notion` 支持把任意网页（微信/博客/arXiv）抓取清洗后写入 Notion page 或 database row，底层由 `notion-cli` skill 封装官方 `ntn` CLI（OAuth 登录，坑点集中规避）；见 [retrospectives/2026-06-28-article-to-notion-ntn-cli-refactor.md](../retrospectives/2026-06-28-article-to-notion-ntn-cli-refactor.md)。**读取方向（Notion → Markdown / MDX）尚未打通**，这是 North Star 里"飞书/Notion 作为写作入口"的另一半，仍待调研。

## Source Sync Todos

- [ ] 沉淀飞书文档到 Markdown / MDX 的标准 runbook：
  - [ ] 记录 `lark-cli` 常用命令、认证方式、导出路径和失败排查。
  - [ ] 明确飞书文档 metadata 如何映射到 frontmatter。
  - [ ] 验证图片、表格、代码块、标题层级、引用块和链接的转换质量。
  - [ ] 判断是否值得项目级 skill 化为 `feishu-to-markdown` 或合并进 writing workflow。
- [x] **Notion 写入方向已完成**（2026-06-28）：文章剪藏/网页收藏 → Notion 已通过 `article-to-notion` + `notion-cli` 两个 skills 落地，支持 OAuth、图片本地上传、database property 自动填充、normalize 防御层。
- [ ] 调研 Notion → Markdown / MDX 的读取路线：
  - [ ] Notion MCP：确认是否适合 agent 直接读取 page / database / block（现有 MCP 主要用于交互式探索，headless 批处理还需评估）。
  - [ ] `ntn pages get`（输出 markdown + YAML frontmatter）：小样本测试其保真度，覆盖 callout / toggle / database relation / 同步块 / 嵌套页面。
  - [ ] `notion-to-md`（社区 JS 库）：做对照实验，检查 frontmatter、嵌套 block、callout、toggle、database relation、media 的保真度。
  - [ ] 决定 Notion 读取的首个最小可用范围：单 page 导出、database 批量导出，还是指定 collection 增量同步。
- [ ] 定义统一 origin package：
  - [x] 使用 `content/origin/YYYY-MM-DD-topic/` 作为可追踪 canonical Markdown / MDX 目录。
  - [x] 回填第一批现有文章到 `content/origin/`，形成 origin package 样例。
  - [x] 统一现有 `content/wechat/` 目录 slug，并在渠道稿 frontmatter 增加 `source:` 反向指针。
  - [ ] 每篇文章一个目录，包含 `article.md` / `article.mdx`、`notes.md` 和 `assets/`。
  - [ ] frontmatter 统一字段：title、subtitle、slug、date、updated、source、source_url、channels、tags、status。
  - [ ] 保留 upstream source link，方便回溯飞书或 Notion 原文。

## Blog Primary Home Todos

博客已上线（2026-06 完成初始搭建），基于 AstroPaper 主题做了原生定制改造。当前迭代重点：

### 已完成
- [x] 建立 Astro 博客工程（eriklee-blog repo，Astro 6.4.2 + Tailwind v4 + MDX）。
- [x] Cloudflare Pages 部署（main 分支自动部署）。
- [x] GitHub Actions CI（lint + format:check + build on PR）。
- [x] Astro content collections schema 定义（posts + pages，Zod schema）。
- [x] 文章批量导入（26 篇 origin 文章同步为 MDX，含图片 assets）。
- [x] `scripts/sync_origin_to_blog.py` 同步脚本。
- [x] `erik-blog-publish-workflow` project skill。
- [x] 中文本地化（i18n、about 页面、taxonomy label 翻译）。
- [x] 自定义主题色（暖纸张 light / 深炭 dark，Charter 衬线正文，Google Sans Code 等宽）。
- [x] 原生 taxonomy sidebar（分类 + 系列 + 形态）。
- [x] PostExplorer 统一列表布局（首页 / 分类页 / 系列页 / 形态页）。
- [x] 首页改版（PostExplorer + hero copy）。
- [x] Shiki 双主题代码高亮（min-light / night-owl）+ transformers（filename / diff / highlight / word-highlight）。
- [x] Pagefind 中文搜索。
- [x] View Transitions（ClientRouter）。
- [x] 图片 lightbox（click-to-zoom，支持移动端双指缩放/pan）。
- [x] Back 按钮 + sessionStorage 导航记忆。
- [x] RSS feed + 动态 OG 图。
- [x] 文章详情页 JSON-LD 结构化数据。
- [x] 微信域名验证文件部署。

### 当前迭代（UI 一致性 + 阅读体验）
- [ ] **布局一致性收尾**：tags / archives / search 页面仍使用旧 `Main` 组件，未迁移到 PostExplorer 统一布局。
- [ ] **清理无效 taxonomy**：`type` 字段默认"技术笔记"导致所有文章 type 相同，侧边栏形态区块无意义；要么去掉默认值并给文章分 real type（长文笔记 / 研究报告 / 随笔 cheatsheet 等），要么移除 type 维度。
- [ ] **清理 AstroPaper 残留**：删除 `src/content/astropaper-examples/` 示例文档；`astro-paper.config.ts` / `ResolvedAstroPaperConfig` 命名去 AstroPaper 化；config 中残余 `editPost` GitHub 链接配置（公开 edit 链接已移除但配置未清理）。
- [ ] **文章详情页体验**：
  - [ ] 阅读时间估算（reading time）。
  - [ ] 文章目录 TOC（remark-toc 已配置但需要检查是否在正文正确渲染，考虑右侧 sticky TOC for long posts）。
  - [ ] 系列文章内导航（同一 series 内 prev/next 优先走系列顺序而非全局时间序）。
  - [ ] 文章末尾标签区样式优化（当前 tag 列表较简陋）。
- [ ] **首页打磨**：
  - [ ] 精选文章（featured）区块。
  - [ ] 个人简介/avatar 区域（目前首页只有 hero copy + 文章列表）。
- [ ] **代码块样式**：确保代码块在移动端水平滚动正常；代码块文件名 transformer 视觉对齐。
- [ ] **Lightbox 脚本**：详情页内联 lightbox 脚本约 300 行，考虑抽离为独立 TS 模块。

### 中期迭代（内容质量 + SEO + 生态）
- [ ] Astro 7 升级（等 UI 布局稳定后再做，避免同时处理 breaking changes 和布局改造；详见 `eriklee-blog/TODO.md`）。
- [ ] 自定义域名配置。
- [ ] OG 图质量优化（当前动态 OG 图较简陋，可参考文章标题 + 分类生成更精美的社交卡片）。
- [ ] frontmatter 质量审计：确保所有文章 tags / category / series / description 完整；部分 category 英文 label（"AI Engineering"）依赖 taxonomy.ts 翻译表，考虑统一使用中文 frontmatter。
- [ ] 同步脚本加固：增量同步检查、frontmatter 字段校验、assets 引用完整性检查、dry-run 模式。
- [ ] Production deploy workflow 与 preview 分离（目前 main 直接部署，可考虑 PR preview 环境）。
- [ ] 考虑 Giscus / 其他评论方案（先不急）。

### 远期
- [ ] 博客自动发布 preview-first 自动化：push 到 feature branch 自动 preview，merge main 经人工确认后发布。
- [ ] 文章系列索引页（每个 series 有独立 landing page，带目录和简介）。
- [ ] 订阅（RSS is done; possibly email newsletter later）。

## Distribution Todos

- [ ] 微信公众号：
  - [ ] 继续完善 `wechat-article-renderer` 和 `wechat-publish-workflow`。
  - [ ] 默认 style preset 已切换为 `warm-editorial`。
  - [ ] 发布前必须有 HTML preview、草稿箱检查和 user final review。
- [ ] 掘金（pending，博客建设好后再启动）：
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

1. 完成博客 UI 一致性收尾（tags/archives/search → PostExplorer，清理无效 type taxonomy，清理 AstroPaper 残留）。
2. 博客文章详情页体验优化（阅读时间、TOC、系列导航、标签区）。
3. 博客首页打磨（精选、个人简介区）。
4. Astro 7 升级（布局稳定后独立分支做）。
5. 把飞书文档 `<->` Markdown 的现有成功经验写成 runbook。
6. 用一个真实 Notion page 做 `Notion -> Markdown / MDX` 读取方向小实验。
7. 定义统一 frontmatter 和 article folder contract。
8. 同步脚本加固（增量同步 + 校验）。
9. 继续验证视频素材链路：用真实文章测试 `video-highlight-select`，再决定 ASR/TTS 是否进入实现。

## Open Questions

- Notion 写入方向（网页/Markdown → Notion 剪藏）已落地（`article-to-notion` + `notion-cli`）；读取方向（Notion → Markdown / MDX 回 repo）尚未实现。
- Notion database 的哪些字段应该成为博客 / 微信共同 metadata？
- Blog production publish 是否需要人工确认，还是只要 GitHub PR review 即可？（当前：`git push main` = 公开发布，需要明确确认）
- 掘金等其他渠道是否需要登录态浏览器自动化，还是先手动复制粘贴更稳？（当前结论：手动先）
- 是否需要给 `source:` 反向指针补一个小脚本，批量检查渠道稿是否能找到 canonical article？
- ASR/TTS 供应商第一版选 MiniMax、火山引擎，还是做一个 provider interface 后再接多个实现？
- 博客是否需要评论系统（Giscus），还是保持纯静态发布更干净？
- 博客自定义域名用什么？（eriklee.blog? erik.engineering?）
