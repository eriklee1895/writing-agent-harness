# Project Skills

项目级 skills 放在 `.agents/skills/`。

它们随 repo 提交，是 `writing-agent-harness` 的稳定能力边界。部分任务还会使用本机 user-level skills，例如 `tavily-search`、`imagegen`、`openai-docs`；这些 skills 通常安装在 `~/.agents/skills/` 或 `~/.codex/skills/`，不属于本 repo。新环境准备见 [../project/prepare-environment.md](../project/prepare-environment.md)。

## Current Core

- `article-ideation`
  - 把模糊写作灵感打磨成清晰 writing brief、research questions 和初版 outline。
  - 用于“我想写一篇”“帮我理一下思路”“脑暴选题”“先定 outline”这类早期写作阶段。
  - 它不负责写完整正文；它负责避免 agent 在没理解清楚前直接开写。

- `polish-article`
  - 润色和打磨文章写作。
  - 按题材强化逻辑、文风、专业深度与作者气质。
  - 已吸收旧 `humanizer` 的目标，不再单独维护 “去 AI 味” skill。

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

- `article-video-clip`
  - 把 `video-material-ingest` 素材包剪成适合文章插入的轻包装视频。
  - 第一版由用户指定片段、横竖 preset、标题和说明；底层用 `ffmpeg` 裁切/转码，用 HyperFrames 包装标题、caption 和来源提示。
  - 不负责下载视频、自动选片、自动字幕或微信公众号上传。

- `baoyu-post-to-wechat`
  - 当前作为底层微信公众号上传器使用，只维护 browser/CDP 主路径。
  - API / remote-api 仅作为历史/实验能力保留，不作为本 repo 的常规自动化路线。
  - 不负责本文 repo 的排版风格。
  - 后续可以把常用子集蒸馏成 project-specific uploader。

## Removed / Avoid

- 不使用 paid `md2wechat` API。
- 不恢复旧 `md2wechat` skill，除非用户明确要求。
- 不重建项目重复的 `gpt-image-gen`。图片生成优先使用系统 `$imagegen`。

## Language

面向中文产品/中文工作流的 project skills 可以中文为主；流程、技术约束、工具名和 checklist 中更清楚的地方使用 English。

微信 UI 文案和报错必须保留中文原文。
