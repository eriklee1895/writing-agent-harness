# 微信公众号写作与发布流程

本文记录本 repo 当前跑通的微信公众号写作、排版、草稿箱同步与发布前验证流程。

## 目标

把一篇 canonical Markdown article 转成适合微信公众号移动端阅读的 HTML preview，再同步到微信公众号草稿箱，最后由用户进行 final human review 和发布。

当前默认 style preset：

```text
impact-rational
中文名：冲击开场，理性正文
```

## 推荐链路

```text
Feishu / idea notes
-> Markdown source
-> polish-article
-> wechat-article-renderer
-> mobile visual verification
-> wechat-publish-workflow
-> 草稿箱
-> user final review
-> publish
```

## 文章目录

当前历史目录可以继续使用：

```text
微信公众号/YYYY-or-MMDD-topic/
├── article.md
├── article.wechat-preview.html
└── assets/
```

未来建议迁移到：

```text
content/wechat/YYYY-MM-DD-topic/
├── article.md
├── article.wechat-preview.html
└── assets/
```

## Step 1: 准备 Markdown source

Markdown 是 repo 内的 canonical source。飞书文档可以作为原始写作入口，但进入发布流程前应转换为 Markdown / MDX。

建议 frontmatter 至少包含：

```yaml
---
title: "文章标题"
description: "文章摘要"
author: "Erik"
cover: "./assets/cover.png"
---
```

正文图片放在 `assets/`，并使用有意义的 alt text，因为 renderer 会把 alt text 转成 caption。

## Step 2: 打磨文章

使用：

```text
polish-article
```

打磨重点：

- thesis 是否清晰；
- section order 是否符合信息依赖；
- 是否有重复信息；
- 语言是否太软、太空、太 AI；
- 是否体现题材需要的专业气质；
- current events / company facts 是否需要查证。

## Step 3: 生成微信公众号 HTML preview

使用：

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs /absolute/path/to/article.md --style impact-rational
```

默认输出：

```text
/same/folder/article.wechat-preview.html
```

Renderer 必须保证：

- inline styles only；
- no JavaScript；
- no external stylesheet；
- no external `href`；
- local images 带 `data-local-path`；
- mobile width `390-430px` 不横向溢出。

## Step 4: 本地预览与检查

本地 visual preview 常见地址：

```text
http://localhost:49255/
```

说 preview ready 前检查：

- title 和 image count 正常；
- generated HTML 没有 `<script>`、`TODO`、`TBD`；
- HTML 没有 `<a>`、`href`、外部 URL；
- 表格、图片、caption、section cards 没有移动端溢出；
- 图片路径可解析；
- 参考资料以 plain text reference 呈现。

## Step 5: 同步到微信公众号草稿箱

使用：

```text
wechat-publish-workflow
```

当前底层可以继续复用：

```text
baoyu-post-to-wechat
```

自动化工作流只维护 CDP 浏览器模式创建草稿；官方 API 不作为主线维护：

- `browser`：当前唯一维护主路径。它通过 Chrome CDP 复用登录态，填 title/author/summary、插入 HTML、上传正文图片、保存草稿。不需要 AppID/AppSecret、access_token 或固定公网出口 IP，最符合个人写作 harness 的维护成本。
- `api` / `remote-api`：保留为历史/实验能力，不围绕它设计自动化。它需要 AppID / AppSecret、可用 access_token、调用 IP 在公众号白名单中；正文图片先上传为微信图片 URL，封面上传为永久素材 `thumb_media_id`，再调用 `draft/add`。如果没有稳定白名单出口 IP，不值得维护。

CDP 成功后的可靠信号是保存后编辑页 URL 出现 `appmsgid=...`；API 成功后的可靠信号是返回草稿 `media_id`。两种方式都只代表进入草稿箱，不代表已经发布。

CDP 模式唯一不可避免的人工参与点是扫码登录。这是微信账号安全模型带来的物理/账号边界，不是自动化缺口；登录态可复用后，后续从 preview 到草稿箱同步已经接近 100% AI 自动化。

## 微信公众号限制坑点

### 外链限制

微信公众号保存草稿时可能报错：

```text
请勿插入非mp.weixin.qq.com域名的链接，请删除后重试
```

处理规则：

- Markdown source 继续保留真实 URL。
- 微信公众号 HTML 不输出 external `href`。
- 参考资料渲染成 plain text reference。
- 不默认展示完整 raw URL。

示例：

```text
01 · Cloudflare 官方博客
VoidZero is joining Cloudflare
```

### 目录锚点

不要依赖 `href="#section-x"`。公众号版本的大纲用于阅读提示，不作为可靠跳转目录。

### 图片与封面

正文图片和封面图是两套状态。

正文图片保存后应变成：

```text
https://mmbiz.qpic.cn/...
```

封面以编辑器左侧卡片/封面预览可见为准。DOM 里的 `#js_cover_area` 有时仍会显示 placeholder text，不一定代表封面失败。

### 保存状态

`自动保存失败` 不等于最终保存失败。可靠信号是点击 `保存为草稿` 后，编辑页 URL 出现：

```text
appmsgid=...
```

## 发布边界

创建草稿和正式发布是两件事。

Agent 可以：

- 创建草稿；
- 检查图片；
- 检查封面；
- 检查链接；
- 报告 `appmsgid`。

Agent 不应未经用户明确确认点击最终发布/群发。扫码登录可以由用户协助完成；扫码之外不应把常规草稿同步流程重新设计成人工步骤。

## Retrospective

2026-06-05，Cloudflare/Vite 文章已按 CDP 流程成功发布。详细复盘见 [../retrospectives/2026-06-05-wechat-publish.md](../retrospectives/2026-06-05-wechat-publish.md)。

2026-06-06，确认不维护 API 主路径，只维护 CDP 自动化。决策记录见 [../retrospectives/2026-06-06-wechat-cdp-only-decision.md](../retrospectives/2026-06-06-wechat-cdp-only-decision.md)。
