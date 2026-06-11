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

当前推荐目录：

```text
content/wechat/YYYY-MM-DD-topic/
├── article.md
├── article.wechat-preview.html
└── assets/
```

`content/drafts/` 可以作为本地写作工作区，但默认 gitignored。文章进入草稿箱同步、发布交付或 repo review 前，应把 canonical Markdown / MDX、notes 和 metadata promote 到 `content/source/`，再把微信公众号派生稿和 preview 放到 `content/wechat/`。微信目录可以有自己的 `assets/`；如果图片已在 `content/source/<slug>/assets/` 且体积较大，可以用相对路径指回 source，避免重复二进制文件。

## Step 1: 准备 Markdown source

`content/source/` 里的 Markdown / MDX 是 repo 内 canonical source。飞书文档可以作为原始写作入口，但进入发布流程前应转换为 Markdown / MDX。

建议 frontmatter 至少包含：

```yaml
---
title: "文章标题"
description: "文章摘要"
author: "Erik"
cover: "./assets/cover.png"
---
```

正文图片放在文章目录的 `assets/`，并使用有意义的 alt text，因为 renderer 会把 alt text 转成 caption。

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
- no base64 image payload；
- local images 带 `data-local-path`，可指向文章 `assets/` 或 `.local-archive/YYYY-MM-DD-slug/images/`；
- mobile width `390-430px` 不横向溢出。

## Step 4: 本地预览与检查

本地 visual preview 常见地址：

```text
http://localhost:49255/
```

说 preview ready 前检查：

- title 和 image count 正常；
- generated HTML 没有 `<script>`、`TODO`、`TBD`；
- generated HTML 没有 base64 图片；
- HTML 没有 `<a>`、`href`、外部 URL；
- 表格、图片、caption、section cards 没有移动端溢出；
- 图片路径可解析；
- 参考资料以 plain text reference 呈现。

## Step 5: 同步到微信公众号草稿箱

使用：

```text
wechat-publish-workflow
```

当前底层默认上传器：

```text
wechat-article-publisher    # Playwright，默认
baoyu-post-to-wechat        # CDP，fallback
```

发布器默认走 `wechat-article-publisher`（Playwright），通过持久化 profile 复用登录态，填 title/author/summary、注入正文 HTML、串行上传正文图片到微信 CDN、保存草稿。元数据取自 source `.md` frontmatter（作者缺省取 `config.toml`，已预填 李玉恒）；标题写入可见标题 ProseMirror（同步隐藏 `#title`），正文剔除 hero 大标题避免重复。代码约为 baoyu 文章流程的 1/4，auto-wait 更稳，无 `baoyu-chrome-cdp` 依赖。已验证文章流程、标题/作者/摘要、串行正文图片上传、草稿保存。迁移背景与对比数据见 [../future_plans/playwright-wechat-migration-analysis.md](../future_plans/playwright-wechat-migration-analysis.md)。

`baoyu-post-to-wechat` 的 CDP 模式保留为 fallback，不再扩展新功能。官方 API / remote-api 仍只作为历史/实验能力（需要 AppID/AppSecret、access_token、IP 白名单，富文本兼容成本高，不维护主线）。

成功后的可靠信号是保存后编辑页 URL 出现 `appmsgid=...`（或保存成功 toast）。进入草稿箱不代表已经发布。

用法：

```bash
uv run python .agents/skills/wechat-article-publisher/scripts/publish.py \
  --article /absolute/path/to/source/article.md \
  --html    /absolute/path/to/article.wechat-preview.html --save-draft
```

唯一不可避免的人工参与点是微信登录确认（首次扫码）。这是微信账号安全模型带来的边界，不是自动化缺口；登录态存独立 profile 可复用后，后续 `login_wait≈0`，从 preview 到草稿箱同步接近 100% AI 自动化。

封面图当前需在草稿箱 final review 时手动设置（封面上传链路未自动化）。

如果登录页显示「微信快捷登录」按钮而不是二维码，应直接点击该按钮继续登录流程，不要等待扫码超时；如果显示二维码，再由用户扫码确认。

### 图片上传策略

不要把正文图片以 base64 内联进 WeChat preview HTML。Markdown / HTML preview 只保留轻量引用和 `data-local-path` / archive hint。

CDP 同步草稿箱时实时处理图片：

1. 读取 HTML 中的 `data-local-path` 或 `.local-archive` 相对路径；
2. 找到本地图片；
3. 上传到微信公众号编辑器/素材；
4. 将 `<img src>` 替换为微信 CDN URL；
5. 保存草稿后检查正文图片是否变成 `https://mmbiz.qpic.cn/...`。

`.local-archive/` 是本机素材库，不提交 Git。换机器时需要手动同步 archive、从外部资产库取回，或从已发布平台 CDN 回填。

### 视频素材

文章内视频素材准备分三层：

- `video-material-ingest`：抓取已知视频 URL，保存本地素材包和来源留痕。
- `video-highlight-select`：生成 contact sheet 和候选片段表，帮助人确认适合文章的高光片段。
- `article-video-clip`：从本地素材包裁片段、转码并用 HyperFrames 做轻包装。
- `wechat-publish-workflow`：决定视频是否插入草稿，以及后续是否调用 CDP 上传到微信公众号素材/草稿箱。

不要把 `article-video-clip` 产物等同于“已上传微信公众号”。WeChat video upload via CDP 仍属于发布 workflow 的后续能力。

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

2026-06-08，跑通视频素材再包装测试，确认裸 mp4 需要先包装成标准素材包，并修复 HyperFrames 模板 contract。复盘见 [../retrospectives/2026-06-08-video-material-clip.md](../retrospectives/2026-06-08-video-material-clip.md)。
