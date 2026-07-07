# Project Skills

项目级 skills 放在 `.agents/skills/`。

- Codex原生支持加载`.agents/skills/` 目录下的技能
- Claude Code通过软链接形式复用skills:
```
.agents/skills/ -> ./claude/skills/
```

它们随 repo 提交，是 `writing-agent-harness` 的稳定能力边界。部分任务还会使用本机 user-level skills，例如 `tavily-search`、`imagegen`、`openai-docs`；这些 skills 通常安装在 `~/.agents/skills/` 或 `~/.codex/skills/`，不属于本 repo。新环境准备见 [../project/prepare-environment.md](../project/prepare-environment.md)。

## Current Core Skills

- `article-ideation`
  - 把模糊写作灵感打磨成清晰 writing brief、research questions 和初版 outline。
  - 用于”我想写一篇””帮我理一下思路””脑暴选题””先定 outline”这类早期写作阶段。
  - 它不负责写完整正文；它负责避免 agent 在没理解清楚前直接开写。

- `polish-article`
  - 润色和打磨文章写作。
  - 按题材强化逻辑、register、表达质感、专业深度与作者气质。
  - 已吸收旧 `humanizer` 的目标，不再单独维护 “去 AI 味” skill。

- `article-readiness-check`
  - 发布前文章 readiness 检查。
  - 用于 polish 之后、renderer / blog build / 草稿箱之前，判断文章是否可以进入渠道包装。
  - 检查正文 readiness、事实边界、Markdown/MDX hygiene、frontmatter、图片/视频引用、渠道 handoff 和 publish blockers；不负责发布后归档、复盘、git 或任务关闭。

- `writing-task-closeout`
  - 写作任务发布后 closeout。
  - 用于微信公众号草稿/发布、blog 发布或最终交付之后，关闭一次写作任务。
  - 负责回填发布状态、把图片/视频二进制移动到 `.local-archive/YYYY-MM-DD-<slug>/`、保留 prompt/metadata/manifest/notes、复盘、memory 决策、skill 改进和 git / task handoff；不执行最终发布。

- `wechat-article-renderer`
  - 从 Markdown 生成微信公众号 HTML preview。
  - 当前默认 style preset 是 `impact-rational`。
  - 未来 style 扩展应放在 renderer 内，而不是新建一堆一次性 style skill。

- `wechat-publish-workflow`
  - 端到端微信公众号发布 runbook。
  - 负责编排 preview、草稿箱同步、验证和最终发布交接。

- `eriklee-blog-publish-workflow`
  - 发布正式稿到 Erik Lee 个人 Astro 博客的专用 workflow。
  - 负责编排 `content/origin/` 到 `eriklee-blog` 的同步、assets / taxonomy 检查、`npm run build`、git 提交、Cloudflare Pages 发布交接。
  - 仅适用于 Erik 的本地 repo 布局和个人博客；不是通用博客发布 skill。`git push main` 等价于公开发布，默认需明确确认。

- `video-material-ingest`
  - 用 `yt-dlp` 把已知视频 URL 摄取到本地可追溯素材目录。
  - 第一版只负责下载、metadata、manifest 和 sources 留痕；不负责搜索视频、图片搜索、版权判断或剪辑生产。
  - 默认使用 `--cookies-from-browser chrome` 读取本机 Chrome 登录态，但不导出、打印或提交 cookies。
  - 输出素材包应包含 `media.ext`、`manifest.json` 和 `sources.md`；早期裸 `.mp4` 需要先包装或迁移成该结构，才能进入下游剪辑。

- `video-highlight-select`
  - 从本地视频素材包生成 contact sheet 和候选高光片段记录，帮助人更快选择文章相关片段。
  - 第一版是 human-in-the-loop：可以记录人工候选 `start/end/title/caption/preset`，但不自动判定最佳高光。
  - 输出 `highlight-select/contact-sheet.jpg`、`highlight-candidates.md` 和 `highlight-candidates.json`，下一步交给 `article-video-clip`。

- `article-video-clip`
  - 把 `video-material-ingest` 素材包剪成适合文章插入的轻包装视频。
  - 第一版由用户指定片段、横竖 preset、标题和说明；底层用 `ffmpeg` 裁切/转码，用 HyperFrames 包装标题、caption 和来源提示。
  - 不负责下载视频、自动选片、自动字幕或微信公众号上传。
  - 实测可生成 `final.mp4`、`preview-frame.jpg`、`clip-manifest.json`、`notes.md` 和 HyperFrames source；完成前应检查 `ffprobe` 元信息和预览帧。

- `article-illustration`
  - 生成文章封面、正文插图、章节视觉分隔图和技术图示。
  - 默认支持 `--style-profile auto`，但正式文章出图时应优先明确指定风格。
  - Guide 和历史优质生图案例见 [article-illustration/README.md](article-illustration/README.md)。

- `gpt-image-2`
  - 用 OpenAI 的 gpt-image-2 生成、编辑和批量生成位图。
  - 支持文生图、参考图编辑（背景替换、物体移除、文字替换、风格迁移）、最多 16 张参考图、批量提示词变体。
  - gpt-image-2 是 2026-06 时点的 SOTA，擅长文字精准渲染、照片级真实感和身份敏感编辑。
  - 不用于 SVG/矢量图标、代码原生图示、确定性布局工作或需要干净透明背景的场景（gpt-image-2 的透明背景建议先生成不透明再用下游 rembg 处理）。

- `seedance-video-gen`
  - 用火山引擎 Seedance 2.0 生成视频。
  - 支持文生视频、图生视频（首帧/首尾帧）、多模态参考、批量镜头、提示词优化和首帧图生成。
  - 前置依赖：`uv`、`ARK_API_KEY` 环境变量或 `.env` 文件。
  - 生成的视频素材包包含 `video.mp4`、`manifest.json`、`prompt.md`，可选 `last-frame.jpg`。

- `wechat-article-fetcher`
  - 用 Playwright + 本地持久化 Profile 提取微信公众号文章到结构化 Markdown + assets。
  - 输入 URL 输出 `article.md` + `manifest.json` + `sources.md` + `assets/`，支持图片落地和交互式首次登录引导。
  - CLI 参数：`--output-dir`（默认 `./wechat-articles/`）、`--no-images`（跳过图片下载）。
  - 已验证 4/4 真实 URL 成功提取，无验证码触发。CDP 路线因进程管理复杂未采用。

- `wechat-article-publisher`
  - Playwright 微信公众号发布器。
  - 输入 origin `.md`（`content/origin/&lt;slug&gt;/`，frontmatter 元数据权威源）+ renderer HTML preview，自动登录态复用、注入正文、上传正文图片到微信 CDN、写标题/作者/摘要、保存草稿并报告 `appmsgid`。
  - 仅创建草稿，不点发布/群发。不负责排版风格（由 `wechat-article-renderer` 负责）。

- `markdown-article-to-feishu-doc`
  - 把本地 Markdown 文章转写为飞书云文档（docx）。
  - 解析 frontmatter，保留标题层级、列表、代码块、表格、引用块；本地图片按原始尺寸上传，` ```mermaid ` 代码块自动渲染为飞书画板，`==高亮文本==` 转换为黄色 callout。
  - 会清洗 `<video>` / `<source>` / HTML 注释等飞书 markdown 模式不支持的标签；缺失的本地图片降级为 `[图片缺失]` 提示，不阻塞整篇转换。
  - 默认新建飞书文档；若用户提供已有 docx URL，会先 fetch 探测并确认后再 overwrite。
  - 底层依赖 `lark-cli` 和 `lark-doc` / `lark-whiteboard` / `lark-shared` skills，本 skill 只负责预处理和编排。

- `article-to-notion`
  - 将任意网页文章（微信公众号、技术博客、论文页面等）抓取、清洗并转写到用户指定的 Notion page 或 database row。
  - 微信公众号走 Playwright（复用 `wechat-article-fetcher`，含 data-src 懒加载正文图），通用站点走 firecrawl/tavily fallback；本地图片 single_part 上传到 Notion 解决防盗链问题。
  - 正文前自动加 single-quote 文章卡片（`<br>` 连接多行，规避 ntn CLI 多行 `>` 拆成独立 quote block 的坑）；上传前自动 merge quote、剥开头重复 H1、尾部公众号引流段落（"推荐阅读"/专辑链接/"本公众号..."等）。
  - 依赖底层 `notion-cli` skill；认证走 `ntn login` OAuth，无需 integration token 或 share connection。

- `notion-cli`
  - 封装官方 `ntn` CLI（`curl -fsSL https://ntn.dev | bash`）的项目级基础 skill，所有需要读写 Notion 的 skill 应通过本 skill 的 `scripts/ntn_cli.py` helper 完成，不手写 `ntn api` 或 REST 调用。
  - 提供统一子命令：`probe`、`upload-file`、`create-page`/`get-page`、`create-page-with-images`⭐、`overwrite-page-with-images`、`append-markdown`、`set-cover`/`set-icon`/`set-properties`、`list-blocks`、`append-blocks`/`clear-children`/`trash-page`。
  - 集中规避 ntn 0.17.x 全部已知坑（空括号/带 emoji 内联语法 hang、stdin 必须 DEVNULL、YAML frontmatter 只输出不输入、block type 不可 PATCH、PATCH children 需清 null 字段、PATCH children 无 after 参数、HTML 注释被 parse、cover 必须 `type=file_upload`、database parent 用 `data-source:<id>` 等）。
  - 认证走 `ntn login` OAuth 一次（凭证存系统 keychain）；可选 `NOTION_API_TOKEN` 环境变量用于 CI 场景。

## Language

面向中文产品/中文工作流的 project skills 可以中文为主；流程、技术约束、工具名和 checklist 中更清楚的地方使用 English。

微信 UI 文案和报错必须保留中文原文。
