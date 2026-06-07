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
