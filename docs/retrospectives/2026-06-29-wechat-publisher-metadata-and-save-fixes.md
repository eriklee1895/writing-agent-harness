# 2026-06-29 WeChat Publisher: Pre-allocated appmsgid, Vue Reactive Flush, and Empty Wrappers

## Summary

本次 closeout 中对 `wechat-article-publisher`（Playwright 版）修复了 3 个累积 bug，使 end-to-end 自动化从「封面/摘要可以，标题/作者经常丢失」升级到「标题/作者/摘要/封面/原创声明/正文开头全对」。最终产出干净草稿 appmsgid=100000498（作者=李玉恒，无开头空行），保存耗时 5.16s（之前错误路径 122s 超时）。

## Bugs Fixed

### 1. Pre-allocated appmsgid false-positive (CRITICAL)

**症状**：`save_draft_and_confirm()` 把 URL 中任何 `appmsgid=...` 当成保存成功信号，立即返回。但微信公众号在**新开编辑器 tab 时就预分配**一个 appmsgid 槽位（在 URL 里）。所以函数实际从未真正点击「保存为草稿」按钮，元数据也从未 commit。这是为什么前 11 次草稿（100000410→100000490）要么标题/作者为空、要么被自动保存覆盖但 metadata 不完整。

**修复**：
- 编辑器打开后立即捕获 `initial_appmsgid`；
- 保存成功信号改为三重验证：(a) 出现「保存成功」toast；(b) appmsgid 变为新值；(c) `#title` 文本匹配预期标题且按钮 loading 态消失 ≥2s；
- 保存前先按 `Tab` 触发 blur 让 Vue 把 ProseMirror 输入 flush 到隐藏 `#title` / `#author` textarea；
- 增加保存后回填失败时的 remediation 循环（重新填标题 + 再保存一次）。

**教训**：不要把 SPA 在 URL 中预分配的资源 ID 当成"操作完成"信号。必须找业务层确认（toast、DOM 状态、字段回读）。

### 2. H1 剔除后残留空 section 导致正文开头空行

**症状**：warm-editorial / impact-rational renderer 把 H1 hero 包在一个带 `padding:0 2px 18px; margin-bottom:28px` 的 `<section>` 里。`extract_body_from_html()` 只 `decompose()` 了 `<h1>`，留下空 section，注入微信编辑器后表现为 1-2 行开头空白。

**修复**：剔除 H1 后向上遍历 ancestor 链，把随之变空的 wrapper（`section`/`div`/`p`）逐个 decompose，然后在循环中继续剔除 leading empty blocks（`p/section/div/br`），直到遇到第一个带文本或媒体的元素。

**教训**：HTML 注入编辑器时，不要只删目标元素；要检查 ancestor wrapper 是否因此变空，特别是 inline-style 带 padding/margin 的 wrapper。

### 3. publish-status.md frontmatter 关闭分隔符丢失后 upsert 静默失效

**症状**：closeout 时发现 `publish-status.md` 顶部 frontmatter 的 `appmsgid`/`author`/`saved_at` 停留在 11:02 的旧值，而 Draft History 已更新到 14:24 的最新 appmsgid=100000498。原因：一次早期写入可能丢失了 closing `---` 分隔符，后续 `_upsert_status_frontmatter()` 因为找不到 `\n---` 而 `return existing` 静默跳过更新，导致 frontmatter 永远停在第一次写入时的状态。

**修复**：
- `end == -1` 时不再 bail out，而是从 `\n## Draft History\n` 或 `\n# 发布状态` 分界处重建最小 frontmatter（date/slug/dir/channel + 当前 updates）；
- 在「key 是否存在」检查里改用 `\n{k}:` 匹配（避免 `image_count` 误命中 `saved_at` 之类的 substring）。

**教训**：frontmatter 读写必须有 fallback，不能假设结构永远正确；任何"找不到就返回原值"的分支都可能成为静默失败点。

## Side Changes

- **配置位置迁移**：publisher 配置从 `.agents/skills/wechat-article-publisher/config.toml`（随 skill 目录）迁移到 repo 根的 `.config/wechat.toml`（已 .gitignore）。新脚本启动时自动迁移旧文件。
- **默认作者**：`.config/wechat.toml` 的 `default_author = "李玉恒"`；本文 frontmatter 同步从 `Erik` 改为 `李玉恒`。
- **封面自动上传**：`--try-cover` 走 WebUploader 隐藏 `<input type=file>` 的 `set_input_files`，不用点击透明 label 覆盖层（之前会被 overlay 拦截）。
- **原创声明**：`--declare-original` 自动勾选原创，作用域限定在原创弹窗内的「确定」按钮。
- **`_click_visible` JS helper**：在 3+ 重复隐藏副本的按钮中只点击 `getBoundingClientRect()` 非零的可见元素。

## Performance

最终运行 timings（s）：

```
browser_launch     2.00
login_wait         0.00  （profile 复用登录态）
open_editor        3.64
fill              23.79  （4 张图串行上传，每张 ~5s）
save_draft         5.16
total             58.50
```

## Contrastive

- **vs 上次成功发布（2026-06-11 Playwright 迁移）**：当时只验证了「正文+图片能保存」的 happy path，没有覆盖 metadata（标题/作者/封面/原创）完整链路。本次暴露了 SPA 预分配 ID、Vue reactive flush、HTML wrapper 清理三类"正文能过、元数据/样式细节不过"的坑。**重复模式**：浏览器自动化要分两层验证——(a) 操作触发成功（按钮可点、无报错 toast）；(b) 状态持久化（URL/DOM 回读、字段值匹配），两层都过才算成功。
- **上次 closeout 标记的改进方向**：6/11 复盘提了"cover upload 还没跑通，best-effort"；本次补全了 cover + 原创声明两条链路，并且把它们都纳入了 publisher 主路径和 post-save verification。
- **headed 模式决策**：2026-06-29 上午的 retrospective 解释了为什么默认 headed，本次再次验证——图片上传/弹窗/保存 toast 在 headless 下更易隐式失败，headed + 持久 profile 复用登录态反而是最快最稳的组合。

## Staleness Check

- `wechat-publish-workflow` SKILL.md 之前描述"封面 best-effort，通常需在草稿箱 final review 时手动设置"已过时——本次 `--try-cover` 已稳定工作。需要更新 SKILL.md（本次 closeout 会同步更新）。
- `docs/workflows/wechat-writing-publishing.md` 第 149 行"封面图当前需在草稿箱 final review 时手动设置"也过时，本次已顺带更新。
- 没有发现 skill 指令被 agent 忽略、或 API/路径变更导致的腐化；三个 bug 都是脚本实现层，不是文档层。

## Remaining Follow-ups

- 未来可考虑：publisher 启动时主动清理（或提示清理）草稿箱里的重复 buggy 草稿；
- 未来可考虑：加 `--headless` opt-in flag（需要先在 5+ 次真实发布上收集稳定性数据）；
- 未来可考虑：视频素材上传链路（本次无视频，未触及）。
