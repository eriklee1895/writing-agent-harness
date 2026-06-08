# 自动化路线图

远期目标是打造高度 AI 自动化的写作工作流，但当前优先保持简单、明确、可验证。

当前建设 todo 见 [todolist.md](todolist.md)。

## Short Term

先沉淀可靠 skill 和人工确认 workflow：

```text
Feishu / notes -> Markdown / MDX -> research -> polish -> channel packaging -> preview -> human review -> publish
```

重点：

- 微信公众号流程已跑通，继续完善 `wechat-article-renderer` 和 `wechat-publish-workflow`。
- 微信公众号草稿箱同步只维护 CDP/browser 自动化；扫码登录是唯一不可避免的人工参与点。
- 用 `polish-article` 做高质量文章打磨，而不是只做 “humanizer”。
- 所有发布前都要有 rendered preview 和用户确认。

## Mid Term

补齐：

- 飞书文档到 Markdown / MDX 的同步 skill。
- Markdown / MDX 到 Astro content collections 的博客发布 skill。
- 微信公众号草稿箱同步的项目定制 CDP uploader，逐步减少对通用 skill 的依赖。
- 文章 metadata、assets、reference links 的统一规范。
- `video-material-ingest`：基于 `yt-dlp` 摄取已知视频 URL，沉淀 metadata、manifest 和 sources，为后续转写、抽帧、切片、HyperFrames 和短视频生产做素材入口。

## Long Term

支持 scheduled agents 自主选题、研究、写作、配图和发布到个人博客：

```text
cron / scheduled run
-> web search
-> topic mining
-> topic scoring
-> outline
-> research
-> draft
-> polish
-> visuals
-> blog preview
-> publish
```

## Automation Boundary

正式全自动发布前，需要先沉淀：

- source 可追踪：飞书原文或 Markdown / MDX source 清楚。
- factual check：current events 和 company/product facts 有日期和来源。
- rendered preview：博客/微信预览可打开，无明显排版错误。
- rollback path：发布失败或内容错误时知道如何修复。
- explicit authorization：用户明确授权某个渠道可以自动发布。

默认策略：博客可以更早尝试自动发布；微信公众号保持 human final review。微信公众号自动化不追求官方 API 主路径，避免维护固定公网出口 IP 和富文本 API 兼容层。
