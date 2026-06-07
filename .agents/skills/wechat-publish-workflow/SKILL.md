---
name: wechat-publish-workflow
description: "微信公众号文章发布 workflow。Use when the user wants to publish/sync/create 草稿箱 draft from a Markdown article: generate WeChat preview, verify HTML/images/封面, remove external href, use baoyu-post-to-wechat, save 草稿箱, and hand off final publish review."
---

# 微信公众号发布 Workflow

## Overview

这个 skill 是本 repo 的微信公众号发布 runbook。默认保持 `Markdown source` 作为 canonical source，用 `wechat-article-renderer` 生成 WeChat HTML preview，用 `baoyu-post-to-wechat` 的 CDP/browser 模式把已确认的 HTML 搬运到微信公众号编辑器/草稿箱。

本 repo 的自动化主线只维护 CDP/browser 模式。官方 API / remote-api 保留为历史/实验能力，不作为常规发布 workflow；原因是 API 需要白名单出口 IP，且富文本、正文图片、封面素材和字段兼容会带来额外维护成本。

不要把 generated preview、已填好的编辑器页面、或已保存草稿理解成 published。真正发布必须由用户明确确认。

## Skill 组合

- 文章还在写作/润色阶段：先用 `polish-article`。
- 文章需要公众号排版：用 `wechat-article-renderer`。
- 用户确认 preview 后要求同步/推送/创建草稿：用 `baoyu-post-to-wechat` 的 browser/CDP 路径。
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
   - no external link `href`，引用来源用 plain text reference；
   - local images 带 `data-local-path`，方便上传器替换成本地图片；
   - mobile preview `390-430px` 无 horizontal overflow。
4. 如需要，打开或刷新本地 preview，常见地址是 `http://localhost:49255/`。
5. 在触碰微信公众号编辑器前，先让用户确认 preview。
6. 用 `baoyu-post-to-wechat` 的 browser/CDP 路径填入微信公众号编辑器并创建草稿。默认偏向创建草稿，不直接发布。
7. 填入后检查：
   - title、author、summary；
   - 封面可见，上传后指向 WeChat CDN；
   - 正文图片已上传到 WeChat CDN；
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

正文图片放在文章目录的 `assets/` 中，并通过 `data-local-path` 让上传器找到本地文件。上传后检查正文图片 URL 是否变成 `https://mmbiz.qpic.cn/`。

封面图和正文图是两套状态。封面以编辑器左侧卡片/封面预览可见为准；DOM 里的 `#js_cover_area` 有时仍会显示 placeholder text，不一定代表封面失败。

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
