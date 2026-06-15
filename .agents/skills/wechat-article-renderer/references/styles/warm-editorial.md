# Warm Editorial Style

中文名：暖色纸张，编辑随笔

## Intent

`warm-editorial` 是从文章 origin `index.html` 单页报告移植过来的暖色纸张风格，适合需要"杂志/编辑手记"质感的技术深度长文。比 `agent-flow` 更有设计感、更暖，但仍保持长文阅读的克制。首次用于《Claude Code Skill Creator 评测体系深度解析》（2026-06-15，appmsgid=100000376）。

## Visual System

- **底色**：`#faf9f5` 暖纸张白（不是纯白）。
- **Accent**：`#d97757` 陶土橙（hero、首列文字、强调）。
- **正文文字**：`#141413` 近黑。
- **表头**：黑底 `#141413` + 暖白字 `#faf9f5`（高对比，杂志感）。
- **引用块**：`#f3f1ea` 暖灰底 + 橙色左边框。
- **代码块**：深色 `#1f252c` 底（与暖色正文形成对比），带语言类型标签。
- **无卡片**（`useCards:false`）：纯流式排版，章节之间靠留白和标题分隔，不套白卡片。

## Structure

- **Hero**（`heroStyle:"warm"`）：极简居中，无标签，24px H1，下方一条浅色分隔，不用大色块。
- 不显示 `文章大纲` / `一句话总结` 面板（`showOutline:false` / `showSummary:false`）。
- 章节标题用橙色左边框 + 序号。
- 行高 `1.9`，偏松，适合长文慢读。
- 无 closing CTA 面板（`closingPanel:false`）。

## Tables（关键）

**必须用 flex `<div>` 表格，不能用 `<table>` 标签**——微信编辑器会给 table 套虚线编辑框。详见 `../wechat-editor-pitfalls.md` #1。

列宽约定（`tableHtml()`）：
- 2 列：`22% / 78%`（首列窄，术语/标签列）。
- 3 列：`30% / 35% / 35%`（首列略宽容纳长术语，后两列均分）。
- 4 列及以上：等分。
- 表头黑底白字，行间浅分隔线，整表 `border-top` 收口。

## Dark Mode

微信夜间模式自动反色。warm-editorial 提供了 dark token（`darkBg:#1a1a18` 等），但纯纸张白 + 无卡片本身在暗色下也稳，不会出现浅色卡片"过亮"问题。

## Mobile Safety

- inline only，`box-sizing:border-box`，`max-width:100%`。
- 表格用 flex + 百分比宽度，天然不溢出。
- 代码块横向滚动用 `overflow-x:auto` section + 内层 `white-space:nowrap` inline-block（不用 `white-space:pre`，会被 strip）。
- `overflow-wrap:break-word` 处理长 token。

## When To Use

- 技术深度长文，想要比 agent-flow 更"成品/编辑"质感时。
- 文章本身已有一份 warm 纸张风的 origin HTML 单页报告，想在微信端复刻视觉时。
- 默认技术评论/观点文仍优先 `agent-flow`（最稳）；warm-editorial 是有意做设计感时的升级选项。
