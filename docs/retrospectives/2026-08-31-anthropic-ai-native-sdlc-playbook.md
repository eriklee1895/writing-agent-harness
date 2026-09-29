# 2026-08-31 Anthropic AI-Native SDLC 写作任务收尾

## Final State

- Status: `draft-created`，未正式发布。
- Canonical: `content/origin/2026-08-31-anthropic-ai-native-sdlc-playbook/index.md`。
- WeChat draft: `appmsgid=100001260`；标题、作者、58 字摘要、封面与 7 张正文图均在保存前后校验。
- Feishu docx: https://bytedance.my.larkoffice.com/docx/NzDqdwD3ZoToUCxjUXfmRpTByLg
- Local archive: `.local-archive/2026-08-31-anthropic-ai-native-sdlc-playbook/`。

## What Worked

1. 把两篇 Anthropic 官方文章、安全文章、DORA/Faros/METR 与中文社区解读放进同一篇学习笔记，避免把 Anthropic 内部的“8 倍代码交付量”误写成普遍生产力结论。
2. 用户明确了“图必须承担解释任务”。最终保留两张带文字的自制技术图和五张带来源的官方流程图；无文字概念封面没有进入项目。
3. 微信发布器 dry-run 与实际保存均确认了 7/7 图片 CDN 回填、标题/作者/摘要回读与封面设置；草稿状态写入 `publish-status.md`。
4. 飞书转写采用图片 token → Markdown overwrite 的标准链路，回查确认 12 个二级章节、7 张图片、0 Mermaid、0 warnings。

## Problems And Fixes

### 1. 微信渠道目录的图片路径

派生 Markdown 位于 `content/wechat/` 时，直接相对引用 sibling 的 origin assets 无法被 preview server 服务。通过在渠道目录创建相对 `assets` symlink 指向 origin assets，保持正文图片不双写，同时让本地 preview 与后续 publisher 都能解析资源。

此外，本次最初只存在 `article.wechat-preview.html`，closeout 补建了标准命名的 `index.wechat-preview.html`，使 `appmsgid` 与渠道 artifact 的对应关系完整。

### 2. warm-editorial 暗色模式不可读

问题：dark CSS 只覆盖少数 class，但正文、标题和表格单元使用行内 `color`，导致暗底下仍显示近黑字。

修复：在 renderer 的 dark media query 中按当前 style token 覆盖行内正文/静音文本，并覆盖 `figcaption`。用系统 Chrome 的 390px 浅色与暗色 viewport 回归：无横向溢出、无缺图，暗色标题和正文均为可读浅色。

## Contrastive

1. 与 2026-07-16《兰花草》草稿任务相比，`summary` 和 `cover` 已在 publisher pre-flight 中完整存在，说明上次补上的 frontmatter contract 生效；此次不再发生自动截首句摘要或封面遗漏。
2. 上次记录的 preview-server 图片路径问题没有原样复现：server 能服务当前目录，但“渠道派生稿引用 origin assets”仍需要显式 asset routing。此次用 symlink 解决，并补齐标准渠道 preview artifact。
3. 与此前仅有微信公众号链路的任务相比，本次额外验证了飞书图片 token 转写链路，7 张图和章节结构均经云端回查确认。

## Skill Staleness Check

⚠️ `wechat-article-renderer` 的 `warm-editorial` 暗色 token 原本未覆盖行内正文色，实际预览不可读。本次已修复脚本并写入 `.local-memory/skill-staleness-wechat-article-renderer.md`；后续应保留 390px 暗色 visual regression。

## Remaining Human Action

- 在微信草稿箱检查封面裁切、图片、标题与夜间模式，再决定是否群发。
- 正式发布后，回填公开 URL 并把 `publish-status.md` 状态更新为 `published`，再做一次发布后 closeout。

## Git / Task

- 二进制媒体留在 origin working copy 与 `.local-archive/` snapshot 中，受 `.gitignore` 忽略，不进入 Git。
- Markdown、provenance manifest、渠道 HTML、草稿状态和复盘可进入 Git。
- 工作树中存在与本任务无关的删除与其他未跟踪目录；closeout 未触碰它们。
