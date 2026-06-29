---
name: wechat-publish-workflow
description: "微信公众号文章发布 workflow。Use when the user wants to publish/sync/create 草稿箱 draft from a Markdown article: generate WeChat preview, verify HTML/images/封面, remove external href, use wechat-article-publisher, save 草稿箱, and hand off final publish review."
---

# 微信公众号发布 Workflow

## Overview

这个 skill 是本 repo 的微信公众号发布 runbook。默认保持 `content/origin/` 下的 Markdown 作为 canonical article，用 `wechat-article-renderer` 生成 WeChat HTML preview，用 `wechat-article-publisher` 把已确认的 HTML 搬运到微信公众号编辑器/草稿箱。

发布器只用 `wechat-article-publisher`（Playwright，代码更少、auto-wait 更稳，已验证文章流程 + 正文图片上传 + 草稿保存）。`baoyu-post-to-wechat` 的 CDP 模式已删除。迁移背景见 [docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md](../../../docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md)。官方 API / remote-api 仍只作为历史/实验能力。

不要把 generated preview、已填好的编辑器页面、或已保存草稿理解成 published。真正发布必须由用户明确确认。

## Skill 组合

- 文章还在写作/润色阶段：先用 `polish-article`。
- 文章需要公众号排版：用 `wechat-article-renderer`。
- 文章包含本地视频素材：先确认视频来自 `video-material-ingest` 素材包，并在发布前确认使用权、插入位置和最终呈现。
- 用户确认 preview 后要求同步/推送/创建草稿：用 `wechat-article-publisher`。
- 用户要求直接发布：先创建或确认草稿，再请求 explicit final confirmation，之后才能点击发布/群发。

## 标准流程

1. 发布前确认 git working tree 干净（`git status` 无未提交的文章/素材改动）——这是默认的回滚保障，不要生成 `.bak-*` 备份文件污染 canonical 目录。
2. 从 canonical Markdown 生成 WeChat preview，输出放到**源 md 同目录**（renderer 默认行为）：

   ```bash
   node ../wechat-article-renderer/scripts/render-wechat-article.mjs \
     /abs/path/to/content/origin/YYYY-MM-DD-<slug>/index.md
   # → 产出 /abs/path/to/content/origin/YYYY-MM-DD-<slug>/index.wechat-preview.html
   ```

   不要加 `--output` 指向 `content/wechat/`，renderer 没有建目录/复制逻辑，容易写出半拉子产物。
3. Verify generated HTML：
   - renderer 成功退出，title 和 image count 正常；
   - no `<script>`, external stylesheet dependency, `TODO`, `TBD`；
   - no base64 image payload；
   - no external link `href`，引用来源用 plain text reference；
   - local images 带 `data-local-path`，可解析到文章 `assets/`、`.local-archive/YYYY-MM-DD-<slug>/images/` 或其他本地归档路径，方便上传器读取本地图片；
   - 如含本地视频，video placeholder / embed marker 带本地视频路径和素材来源说明；
   - mobile preview `390-430px` 无 horizontal overflow。
4. 如需要，打开或刷新本地 preview，常见地址是 `http://localhost:49255/`。
5. 在触碰微信公众号编辑器前，先让用户确认 preview。
6. **渠道产物约定：`content/wechat/YYYY-MM-DD-<slug>/` 是微信渠道派生 artifact 的 canonical 目录，与 `appmsgid`/发布 URL 一一对应。**
   - **publisher 会自动兜底**：如果 `--html` 指向 `content/origin/.../`，`publish.py` 会自动拷贝（或快照后再覆盖，见下）到 `content/wechat/.../index.wechat-preview.html`，并在保存草稿成功后自动写 `publish-status.md`。所以即使忘了这一步，归档不会丢。
   - **仍然推荐手动 cp 一次**（命令见下），因为这是你在点击发送按钮前最后一次在 repo 里确认"就是这份 HTML 要被送到微信"的机会，也让 `content/wechat/` 目录在调用 publisher 前就是完整可 review 的状态：

     ```bash
     SRC_DIR=content/origin/YYYY-MM-DD-<slug>
     DST_DIR=content/wechat/YYYY-MM-DD-<slug>
     mkdir -p "$DST_DIR"
     cp "$SRC_DIR/index.wechat-preview.html" "$DST_DIR/index.wechat-preview.html"
     # 如果有微信渠道专用 assets（非 origin 复用）才放 $DST_DIR/assets/；
     # 共用图片保持相对路径指回 ../../origin/.../assets/，不要重复复制二进制。
     ```

   - **重发安全网**：如果检测到 `content/wechat/.../publish-status.md` 里已有非空 `appmsgid`（意味着这份 HTML 对应一个已存在的草稿），publisher 会在覆盖前把旧 HTML 快照为 `index.wechat-preview.appmsgid-<id>.html`，避免之前草稿对应的 artifact 丢失。草稿箱里旧草稿还在，traceability 不丢。
7. 用 `wechat-article-publisher` 把归档副本 HTML 填入微信公众号编辑器并创建草稿。默认偏向创建草稿，不直接发布。

   ```bash
   uv run ../wechat-article-publisher/scripts/publish.py \
     --article /abs/path/to/content/origin/YYYY-MM-DD-<slug>/index.md \
     --html    /abs/path/to/content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html \
     --save-draft
   ```

   - 元数据（标题/作者/摘要/封面）取自 `--article` 的 frontmatter；作者缺省取 repo 根下 `.config/wechat.toml`（首次缺失时询问并写回，已 .gitignore）；
   - 标题写入可见标题 ProseMirror（同步隐藏 `#title`），正文剔除 hero 大标题避免重复；
   - 自动读取 `data-local-path` 指向的本地图片（renderer 产出绝对路径，和 HTML 所在目录无关，所以 origin/wechat 两份 HTML 用的是同一组图片，不用双拷贝二进制）；
   - 串行上传正文图片到微信公众号，等其变成 `mmbiz.qpic.cn` CDN URL 再传下一张/保存；
   - 不把图片 base64 内联进 HTML；
   - 传 `--try-cover` 会用 frontmatter 中的 `cover:` 路径自动上传封面（走 WebUploader 隐藏 file input，已稳定）；
   - 传 `--declare-original` 会自动勾选原创声明（需要该账号已开通原创功能）；
   - 保存前按 Tab blur 让 Vue 把 ProseMirror 输入 flush 到隐藏 textarea，避免 metadata 不 commit；保存后三重验证（toast / appmsgid 变更 / title 回读匹配），不再依赖 URL 中预分配的 appmsgid 槽位作为成功信号。
   - **浏览器默认以 headed 模式启动（`headless=False` + `launch_persistent_context`）**。这是刻意的默认：首次必须扫码；已登录时仍保留 headed 是因为微信后台反自动化对头less 敏感、图片上传链路在 headless 下易隐式失败、final human review 本来就需要人眼、debug 时直接可见错误弹框。不要自作主张改成 headless；决策细节见 [docs/retrospectives/2026-06-29-wechat-publisher-headed-mode.md](../../../docs/retrospectives/2026-06-29-wechat-publisher-headed-mode.md)。未来若加 `--headless` flag，必须先在该 retrospective 中登记稳定性数据，且只能 opt-in。
8. 填入后检查：
   - title、author、summary；
   - 封面可见，上传后指向 WeChat CDN；
   - 正文图片已上传到 WeChat CDN；
   - 如含视频，视频卡片/播放器在编辑器中可见，插入位置正确；
   - editor body 中 external links 数量为 `0`；
   - 保存后 URL 出现 `appmsgid=...`（publisher 会自动写入 `publish-status.md` 的 frontmatter 和 Draft History，无需手动回填）。
9. 向用户报告草稿状态和 `appmsgid`。除非用户明确确认 live publish，否则停在 final human review。
10. 用户完成 final review 并群发/发布后，把正式发布 URL 追加到 `publish-status.md`（或把 `status` 改成 `published`），再调用 `writing-task-closeout` 做归档、复盘和素材清理。

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

正文图片可以放在文章目录的 `assets/` 中，也可以按任务归档到 `.local-archive/YYYY-MM-DD-<slug>/images/`。Renderer 通过 `data-local-path` 或本地 archive hint 让上传器找到文件。

不要把图片以 base64 写进 WeChat preview HTML。HTML artifact 保持轻量；发布时由 CDP 上传器实时读取本地图片、上传到微信，并替换为微信 CDN URL。上传后检查正文图片 URL 是否变成 `https://mmbiz.qpic.cn/`。

封面图和正文图是两套状态。封面以编辑器左侧卡片/封面预览可见为准；DOM 里的 `#js_cover_area` 有时仍会显示 placeholder text，不一定代表封面失败。

### 视频素材

微信公众号文章里插入视频属于 channel-specific publishing step，不属于 `video-material-ingest` 的职责。

职责边界：

- `video-material-ingest`：抓取已知视频 URL，保留 `manifest.json` 和 `sources.md`，形成本地可追溯素材包。
- `wechat-article-renderer`：未来可把 Markdown 中的视频引用渲染成 WeChat-ready placeholder，并保留本地视频路径和素材来源说明。
- `wechat-publish-workflow`：编排视频素材发布前确认、上传/插入、草稿保存和最终检查。
- `wechat-article-publisher`：未来负责具体 Playwright/browser 上传视频、插入编辑器和读取插入结果。

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

Cloudflare/Vite 文章已经按这个流程成功发布（当时用的是 baoyu-post-to-wechat CDP，现已迁移到 wechat-article-publisher Playwright）：

```text
Canonical Markdown (content/origin/) → WeChat HTML preview → mobile/visual verification → WeChat editor via Playwright → remove external hrefs → save 草稿箱 → user final publish
```

关键修复：参考资料里的 external links 导致微信保存失败。将 reference links 渲染成 plain text 后，草稿保存和后续发布成功，同时 canonical Markdown 仍保留真实链接，方便博客等其他渠道复用。
