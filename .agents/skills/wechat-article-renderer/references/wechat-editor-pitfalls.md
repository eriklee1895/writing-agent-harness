# WeChat Editor Sanitizer Pitfalls

微信公众号编辑器在保存草稿时会跑一套 HTML sanitizer + 自动包装逻辑。**本地预览永远是对的；只有真正的草稿箱才暴露这些坑。** 每次改完 renderer 都要在草稿箱里实测，不能只看 localhost 预览。

这是一份按真实踩坑顺序累积的 anti-pattern 清单。

## 1. `<table>` 标签 → 虚线"表格编辑框"（2026-06-15 重复确认）

**现象**：用真正的 `<table>/<thead>/<th>/<td>` 标签时，微信编辑器会自动给整张表套一个**虚线边框 + 顶部一条空白工具区**。窄表格（2 列）不明显，3/4 列宽表格一拉宽就暴露。inline style 改不掉这个框——它是编辑器对 table 标签的内建行为。

**根因**：微信识别到 table 标签 → 进入"表格编辑模式" → 套编辑 UI。和外层是否有 wrapper 无关。

**解法**：**不要用 table 标签。** 用 `display:flex` 的 `<div>` 行来画表格：
- 外层 `<section>`：`border-top` 画顶边。
- 表头行：一个 `display:flex` 的 div，背景色 + `border-radius:6px 6px 0 0`。
- 每个单元格：`<div style="box-sizing:border-box; width:30%; flex:0 0 30%; ...">`，宽度用 `width` + `flex:0 0 <pct>` 双保险。
- 数据行：`display:flex` div，行底 `border-bottom`。

微信对普通 div 不套编辑框，列宽完全可控。见 `render-wechat-article.mjs` 的 `tableHtml()`。

**历史**：`renderer-table-borders-wechat-incompatible` 在 2026-06-12 就出现过一次（当时是 table 边框样式问题），2026-06-15 再次以"表格编辑框"形式出现 → 确认为重复模式 → 固化为 flex 表格方案。

## 2. `overflow-x:auto` 的 wrapper `<div>` → 虚线"区块占位框"

**现象**：为了横向滚动给表格/代码块套一个 `<div style="overflow-x:auto">`，微信编辑器把它渲染成一个虚线"section placeholder"框。

**解法**：表格已用 `flex` + 百分比宽度 = 不会横向溢出，不需要 overflow wrapper，直接去掉。代码块的横向滚动改用别的方式（见下）。

## 3. `white-space:pre` 被 strip → 代码块缩进/换行丢失

**现象**：代码块用 `white-space:pre` 保留缩进和不换行，在本地预览正常，但微信 sanitizer **strip 掉 `white-space:pre`**，导致代码挤成一坨或在移动端 wrap 折行。

**解法**：
- 缩进：用 `&nbsp;` 显式占位（tab → 4 个空格 → `&nbsp;`）。
- 不换行 + 横向滚动：外层 `<section style="overflow-x:auto">` + 内层 `<div style="display:inline-block; min-width:100%; white-space:nowrap">`。`white-space:nowrap`（不是 `pre`）目前不被 strip。
- 换行用 `<br>`。
- 见 `codeHtml()`。

## 4. `<colgroup>` 宽度被 strip + 单元格 inline `width` 被部分忽略

**现象**（已被 #1 的 flex 方案绕过）：table 方案下，`<colgroup>` 的列宽被 sanitizer 删掉，单元格 inline `width` 也常被忽略，列塌成 ~50/50。当时的缓解是同时写 HTML `width=` 属性 + inline `width`。改用 flex div 后此坑不再相关。

## 5. 外部 `href` 链接被拒

非 `mp.weixin.qq.com` 的链接在保存草稿时被微信拒绝。renderer 一律把链接/参考资料渲染成纯文本（title + source），不输出 `href`。publisher 还有一层 safety net 兜底 unwrap。

## 通用纪律

- **改完 renderer 必须在真实草稿箱验证**，localhost 预览不算数。
- 优先用 `<section>/<div>` + inline flex/百分比，避开任何会触发微信"编辑 UI"的语义标签（table 是最大的坑）。
- 不用 `<script>`、外部 CSS、base64 内联大图。
