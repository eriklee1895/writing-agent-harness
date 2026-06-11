---
name: wechat-publish-workflow
description: "微信公众号文章发布 workflow。Use when the user wants to publish/sync/create 草稿箱 draft from a Markdown article: generate WeChat preview, verify HTML/images/封面, remove external href, use wechat-article-publisher (默认；baoyu-post-to-wechat 为 fallback), save 草稿箱, and hand off final publish review."
---

# 微信公众号发布 Workflow

## Overview

这个 skill 是本 repo 的微信公众号发布 runbook。默认保持 `Markdown source` 作为 canonical source，用 `wechat-article-renderer` 生成 WeChat HTML preview，用 `wechat-article-publisher` 把已确认的 HTML 搬运到微信公众号编辑器/草稿箱。

发布器默认走 `wechat-article-publisher`（Playwright，代码更少、auto-wait 更稳，已验证文章流程 + 正文图片上传 + 草稿保存）。`baoyu-post-to-wechat` 的 CDP 模式保留为 fallback，不再扩展新功能。迁移背景见 [docs/future_plans/playwright-wechat-migration-analysis.md](../../../docs/future_plans/playwright-wechat-migration-analysis.md)。官方 API / remote-api 仍只作为历史/实验能力。

不要把 generated preview、已填好的编辑器页面、或已保存草稿理解成 published。真正发布必须由用户明确确认。

## Skill 组合

- 文章还在写作/润色阶段：先用 `polish-article`。
- 文章需要公众号排版：用 `wechat-article-renderer`。
- 文章包含本地视频素材：先确认视频来自 `video-material-ingest` 素材包，并在发布前确认使用权、插入位置和最终呈现。
- 用户确认 preview 后要求同步/推送/创建草稿：用 `wechat-article-publisher`（默认）；如其失效再回退 `baoyu-post-to-wechat` 的 browser/CDP 路径。
- 用户要求直接发布：先创建或确认草稿，再请求 explicit final confirmation，之后才能点击发布/群发。

## 标准流程

1. 发布尝试前，先 backup Markdown 和当前 generated HTML。
2. 从 canonical Markdown 生成 WeChat preview：

   ```bash
   node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs /absolute/path/to/article.md
   ```

3. Verify generated HTML：
   - renderer 成功退出，title 和 image count 正常；
   - no `<script>`, external stylesheet dependency, `TODO`, `TBD`；
   - no base64 image payload；
   - no external link `href`，引用来源用 plain text reference；
   - local images 带 `data-local-path`，可解析到文章 `assets/`、`.local-archive/YYYY-MM-DD-slug/images/` 或其他本地归档路径，方便上传器读取本地图片；
   - 如含本地视频，video placeholder / embed marker 带本地视频路径和素材来源说明；
   - mobile preview `390-430px` 无 horizontal overflow。
4. 如需要，打开或刷新本地 preview，常见地址是 `http://localhost:49255/`。
5. 在触碰微信公众号编辑器前，先让用户确认 preview。
6. 用 `wechat-article-publisher` 把 preview HTML 填入微信公众号编辑器并创建草稿（默认；失效时回退 `baoyu-post-to-wechat`）。默认偏向创建草稿，不直接发布。

   ```bash
   uv run python .agents/skills/wechat-article-publisher/scripts/publish.py \
     --article /absolute/path/to/source/article.md \
     --html    /absolute/path/to/article.wechat-preview.html --save-draft
   ```

   - 元数据（标题/作者/摘要/封面）取自 `--article` 的 frontmatter；作者缺省取 `config.toml`（已预填 李玉恒）；
   - 标题写入可见标题 ProseMirror（同步隐藏 `#title`），正文剔除 hero 大标题避免重复；
   - 自动读取 `data-local-path` 指向的本地图片；
   - 串行上传正文图片到微信公众号，等其变成 `mmbiz.qpic.cn` CDN URL 再传下一张/保存；
   - 不把图片 base64 内联进 HTML；
   - 封面 best-effort，通常需在草稿箱 final review 时手动设置。
7. 填入后检查：
   - title、author、summary；
   - 封面可见，上传后指向 WeChat CDN；
   - 正文图片已上传到 WeChat CDN；
   - 如含视频，视频卡片/播放器在编辑器中可见，插入位置正确；
   - editor body 中 external links 数量为 `0`；
   - 保存后 URL 出现 `appmsgid=...`。
8. 向用户报告草稿状态和 `appmsgid`。除非用户明确确认 live publish，否则停在 final human review。

## 微信公众号限制坑点

### 外链限制

微信公众号保存草稿时可能报错：

```text
请勿插入非mp.weixin.qq.com域名的链接，请删除后重试
```

公众号 HTML 不要输出 external `href`。Markdown 源稿可以继续保留真实 URL，供 blog/future channels 使用；公众号版本只渲染为文本：

```text
01 · Cloudflare 官方博客
VoidZero is joining Cloudflare
```

不要默认在正文展示完整 raw URL。移动端很难看，也可能触发微信的 link handling。

### 目录锚点

不要依赖公众号里的 table-of-contents jump links。本地 preview 可以看起来像可跳转目录，但 WeChat-ready HTML 不应依赖 `href="#section-x"`。

### 图片与封面

正文图片可以放在文章目录的 `assets/` 中，也可以按任务归档到 `.local-archive/YYYY-MM-DD-slug/images/`。Renderer 通过 `data-local-path` 或本地 archive hint 让上传器找到文件。

不要把图片以 base64 写进 WeChat preview HTML。HTML artifact 保持轻量；发布时由 CDP 上传器实时读取本地图片、上传到微信，并替换为微信 CDN URL。上传后检查正文图片 URL 是否变成 `https://mmbiz.qpic.cn/`。

封面图和正文图是两套状态。封面以编辑器左侧卡片/封面预览可见为准；DOM 里的 `#js_cover_area` 有时仍会显示 placeholder text，不一定代表封面失败。

### 视频素材

微信公众号文章里插入视频属于 channel-specific publishing step，不属于 `video-material-ingest` 的职责。

职责边界：

- `video-material-ingest`：抓取已知视频 URL，保留 `manifest.json` 和 `sources.md`，形成本地可追溯素材包。
- `wechat-article-renderer`：未来可把 Markdown 中的视频引用渲染成 WeChat-ready placeholder，并保留本地视频路径和素材来源说明。
- `wechat-publish-workflow`：编排视频素材发布前确认、上传/插入、草稿保存和最终检查。
- `baoyu-post-to-wechat`：未来负责具体 CDP/browser 上传视频、插入编辑器和读取插入结果。

发布前必须确认：

- 视频素材包来自 `video-material-ingest`，并有 `manifest.json` / `sources.md`。
- 用户确认可以在微信公众号文章中使用该视频或相关片段。
- 用户确认视频插入位置、标题/说明和是否需要替代封面图。

如果底层上传器尚未实现视频上传/插入能力，不要声称已自动完成。应停在草稿编辑器可人工处理的状态，提示用户手动上传/插入视频；之后再检查视频卡片/播放器可见、位置正确，并继续保存草稿。

### 保存状态

`自动保存失败` 在编辑器自动化过程中很常见，不等于最终保存失败。可靠信号是点击 `保存为草稿` 后，编辑页 URL 出现 `appmsgid=...`。

### 发布边界

创建草稿和正式发布是两件事。Agent 可以辅助创建草稿、检查图片、检查链接、检查封面；不要未经用户明确确认点击最终发布/群发。

### API 取舍

不要把官方 API 作为本 repo 的默认发布路径。API 需要 AppID/AppSecret、access_token、调用 IP 白名单；如果没有固定白名单出口 IP，就需要维护公网服务器或 remote-api 隧道。对个人写作 harness 来说，这会把发布自动化变成基础设施维护。

API 对富文本的长期兼容也需要额外维护：正文图片要预上传成微信 URL，封面要上传成永久素材 `thumb_media_id`，草稿字段和编辑器最终呈现还需要单独验证。相比之下，CDP 直接操作微信公众号编辑器，看到什么就是什么，更贴近最终人工 review。

CDP 模式唯一不可避免的人工参与点是扫码登录。这来自微信账号安全和登录态限制，可以接受；扫码之外，目标是保持接近 100% AI 自动化。

## Successful Run Memory

Cloudflare/Vite 文章已经按这个流程成功发布：

```text
Markdown source -> WeChat HTML preview -> mobile/visual verification -> WeChat editor via baoyu-post-to-wechat -> remove external hrefs -> save 草稿箱 -> user final publish
```

关键修复：参考资料里的 external links 导致微信保存失败。将 reference links 渲染成 plain text 后，草稿保存和后续发布成功，同时 Markdown source 仍保留真实链接，方便博客等其他渠道复用。
