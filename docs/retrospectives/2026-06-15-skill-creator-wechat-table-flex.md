# Retrospective — Skill Creator 评测体系深度解析（微信排版与发布）

- **日期**: 2026-06-15
- **Slug**: `2026-06-14-skill-creator-eval-framework`
- **状态**: draft-created（微信草稿箱 appmsgid=100000376，未发布）
- **Skills used**: `wechat-article-renderer`, `wechat-article-publisher`, `article-illustration`, `writing-task-closeout`

## Timeline

1. 走 `wechat-article-renderer` 排版 → 创建草稿。
2. 补封面（首次漏了）。
3. 代码块在移动端 wrap + 无语言标签 → 改横向滚动 + 语言标签。
4. 用户不喜欢默认 style → 移植 origin `index.html` 暖色纸张风，新增 `warm-editorial` style preset。
5. 表格虚线框 + 2 列等分问题 → 多轮修。
6. 指定列宽比例（四模式表、术语表首列太宽）→ 调比例。
7. 补 5 张配图；origin 的 3 个 Mermaid 图改用 `article-illustration` 重绘静态信息图。
8. 表格虚线框反复出现 → **最终定位根因：`<table>` 标签本身触发微信编辑框**，改用 flex div 表格，彻底解决。

## 关键失败 → 解决

### 表格虚线框（多轮反复，最终根因）
- **错误假设链**：以为是 (a) 单元格边框样式 → (b) `<colgroup>` → (c) `overflow-x:auto` wrapper div。逐个排除后虚线框仍在。
- **真根因**：微信编辑器识别到**真正的 `<table>` 标签**就自动套"表格编辑模式"UI（虚线框 + 顶部空白工具区）。inline style 改不掉，与外层 wrapper 无关。窄表不明显，宽表暴露。
- **最终解法**：整张表改用 `display:flex` 的 `<div>` 行 + 百分比宽度（`width` + `flex:0 0 <pct>` 双保险）。微信对普通 div 不套编辑框。输出里 `<table>/<th>/<td>` = 0。
- **验证**：本地 mobile 375px 实测 2 列 77/274、3 列 105/123/123、4 列均分，全部满宽无溢出；草稿箱实测虚线框消失，用户确认通过。

### 代码块移动端 wrap + `white-space:pre` 被 strip
- 本地预览 `white-space:pre` 正常，微信 strip 掉 → 代码 wrap。
- 解法：`overflow-x:auto` section + 内层 `white-space:nowrap` inline-block + `&nbsp;` 显式缩进 + `<br>` 换行 + 语言类型标签。

### Mermaid 移动端不可靠
- origin HTML 用 CDN mermaid@11，微信端不渲染。
- 解法：3 个流程图用 `article-illustration --style-profile flat-tech-infographic` 重绘成静态信息图。

## Contrastive（对比，不只是记录）

1. **和上次同类任务（2026-06-12 hermes）有什么不同？**
   - 上次也踩了表格坑（`renderer-table-borders-wechat-incompatible`）和 Mermaid 坑（`mermaid-too-plain-replace-with-rendered-diagram`）。这次表格坑以**更深的形式**（编辑框而非边框样式）重现，Mermaid 坑则按上次经验**一次性正确处理**（直接改静态图，没走弯路）→ 上次的改进落地了。
   - 封面 auto-upload 不可靠（`publisher-cover-auto-upload-unreliable`）连续第 3 次出现 → 仍是 `uploaded-unconfirmed`，需手动在草稿箱设。

2. **上次 closeout 标记的改进方向，这次验证了吗？**
   - "Mermaid → 静态信息图" 已内化为默认动作 ✅。
   - "表格在微信不兼容" 上次只记了现象，没沉淀解法 → 这次才真正定位根因并固化为 flex 表格方案。**教训：上次只记现象不记解法，导致这次重新 debug 了好几轮。**

3. **这次的问题在上次是否出现过？（重复模式）**
   - 表格坑 = 重复模式（2 次）→ 已固化进 `references/wechat-editor-pitfalls.md` + SKILL.md 硬规则。
   - 封面 auto-upload 不可靠 = 重复模式（3 次）→ 已是已知 staleness，publisher 行为短期不会改，接受"草稿箱手动设封面"为标准收尾步骤。

## 沉淀产出

- **新增** `references/wechat-editor-pitfalls.md`：5 条微信 sanitizer anti-pattern（table 编辑框、overflow wrapper 占位框、white-space:pre strip、colgroup strip、外链拒绝）。
- **新增** `references/styles/warm-editorial.md`：暖色纸张 style 文档。
- **改** `tableHtml()`：table 标签 → flex div 表格。
- **改** SKILL.md：注册 warm-editorial + agent-flow，加表格/sanitizer 硬规则与 pitfalls 引用。

## ⚠️ 技能腐化风险

- `publisher-cover-auto-upload-unreliable`：连续 3 次 `uploaded-unconfirmed`。publisher 的 `--try-cover` 实际不能确认封面落地。短期方案是接受手动设封面；若要根治需查 publisher 封面上传选择器（已记 staleness flag）。

## Follow-ups

- 无阻塞项。文章在草稿箱待用户 final review + 手动设封面后决定是否发布。
- 可选：把 `agent-flow` / `warm-editorial` 两个新 style 的选择决策树补进 `docs/workflows/wechat-writing-publishing.md`（低优先）。
