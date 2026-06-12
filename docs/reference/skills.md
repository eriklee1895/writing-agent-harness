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
  - 用于“我想写一篇”“帮我理一下思路”“脑暴选题”“先定 outline”这类早期写作阶段。
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
  - 负责回填发布状态、把图片/视频二进制移动到 `.local-archive/YYYY-MM-DD-slug/`、保留 prompt/metadata/manifest/notes、复盘、memory 决策、skill 改进和 git / task handoff；不执行最终发布。

- `wechat-article-renderer`
  - 从 Markdown 生成微信公众号 HTML preview。
  - 当前默认 style preset 是 `impact-rational`。
  - 未来 style 扩展应放在 renderer 内，而不是新建一堆一次性 style skill。

- `wechat-publish-workflow`
  - 端到端微信公众号发布 runbook。
  - 负责编排 preview、草稿箱同步、验证和最终发布交接。

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

- `wechat-article-fetcher`
  - 用 Playwright + 本地持久化 Profile 提取微信公众号文章到结构化 Markdown + assets。
  - 输入 URL 输出 `article.md` + `manifest.json` + `sources.md` + `assets/`，支持图片落地和交互式首次登录引导。
  - CLI 参数：`--output-dir`（默认 `./wechat-articles/`）、`--no-images`（跳过图片下载）。
  - 已验证 4/4 真实 URL 成功提取，无验证码触发。CDP 路线因进程管理复杂未采用。

- `wechat-article-publisher`
  - Playwright 微信公众号发布器。
  - 输入 origin `.md`（`content/origin/&lt;slug&gt;/`，frontmatter 元数据权威源）+ renderer HTML preview，自动登录态复用、注入正文、上传正文图片到微信 CDN、写标题/作者/摘要、保存草稿并报告 `appmsgid`。
  - 仅创建草稿，不点发布/群发。不负责排版风格（由 `wechat-article-renderer` 负责）。
  - 迁移背景与对比数据见 [docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md](../retrospectives/2026-06-11-playwright-wechat-migration-analysis.md)。

## Language

面向中文产品/中文工作流的 project skills 可以中文为主；流程、技术约束、工具名和 checklist 中更清楚的地方使用 English。

微信 UI 文案和报错必须保留中文原文。
