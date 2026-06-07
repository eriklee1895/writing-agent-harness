# 2026-06-05 微信公众号发布复盘

Cloudflare/Vite 文章已经跑通并沉淀了微信公众号 `impact-rational` 默认风格。

推荐流程：

```text
Markdown source -> polish-article -> WeChat HTML preview -> mobile/visual verification -> WeChat draft -> user final review -> publish
```

## What Worked

- 免费路径可行，不依赖 paid md2wechat API。
- `wechat-article-renderer` 负责排版，可以在本地持续迭代。
- `wechat-publish-workflow` 负责编排发布。
- `baoyu-post-to-wechat` 的 CDP 模式可作为当前主上传器。
- `impact-rational` 适合作为当前默认 style preset，未来 style 扩容优先放在 renderer 中。

## Pitfalls

- 发布前先备份 Markdown 和 generated HTML，避免调试期间破坏用户稿件。
- 微信公众号保存草稿会拦截非 `mp.weixin.qq.com` 域名外链。Markdown 源稿继续保留真实链接；公众号 HTML 将链接渲染为 plain text reference。
- 不要依赖目录锚点跳转。公众号版本的大纲用于阅读提示，不应依赖 `href="#section-x"`。
- 正文图片需要上传成微信 CDN 图；保存后检查正文图片数量和 `mmbiz.qpic.cn` URL。
- 封面图和正文图是两套状态。封面以编辑器左侧/封面预览可见为准，DOM 里 `#js_cover_area` 仍可能显示 placeholder text。
- `自动保存失败` 不等于最终保存失败。可靠信号是保存后 URL 出现 `appmsgid=...`。
- 官方 API 需要白名单出口 IP；如果不想维护固定公网服务器，个人写作 workflow 默认只维护 CDP 主路径，API 只作为历史/实验能力。
- CDP 模式唯一不可避免的人工参与点是扫码登录。登录态可复用后，从 preview 到草稿箱同步已经接近 100% AI 自动化。

## Publish Boundary

Agent 可以创建草稿和辅助检查，不要未经用户明确确认直接发布/群发。
