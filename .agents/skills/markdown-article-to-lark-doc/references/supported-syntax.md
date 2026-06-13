# 支持的 Markdown 语法清单与降级策略

本 skill 用 `lark-cli docs +update --doc-format markdown` 写入飞书 docx,主要依赖**飞书服务端的 Markdown renderer**处理 GFM 语法。下面是各 markdown 元素的支持现状。

## ✅ 原生支持(无降级)

| 元素 | 飞书行为 |
|---|---|
| 标题 `# ## ###` | 转飞书 `<heading>` block |
| 段落 / 行内强调 `**bold**` `*italic*` `~~del~~` | 转富文本 |
| 行内代码 `` `code` `` | 转 `<code>` 行内样式 |
| 代码块 ` ```lang ` | 转 `<pre lang="...">` block,语言标记保留 |
| 无序列表 `- *` | 转 `<ul>` + `<li>` |
| 有序列表 `1.` | 转 `<ol>` + `<li>` |
| 嵌套列表 | 嵌套结构保留 |
| 引用块 `>` | 转 `<blockquote>` |
| 表格(GFM) | 转飞书原生 `<table>` |
| 链接 `[text](url)` | 转富文本 link |
| 远程图片 `![alt](https://...)` | 飞书自动下载并转 `<img>` block |
| 水平分隔线 `---` | 转 `<hr>` |
| 行内 LaTeX `$E=mc^2$` | 转 `<latex>` 行内公式 |

## ⚠️ 部分支持(本 skill 主动转换)

| 元素 | 处理 |
|---|---|
| 本地图片 `![](./assets/x.png)` | preprocess.py 把它换成 `<img src="__PLACEHOLDER_N__"/>`;skill 主流程通过 `+media-insert` 上传后用 `file_token` 替换占位 |
| Mermaid `` ```mermaid `` 块 | preprocess.py 换成 `<whiteboard type="mermaid">code</whiteboard>` 内联标签;飞书服务端自动渲染成画板 block |
| Frontmatter `--- ... ---` | preprocess.py 抽离;`title` 字段用作 docx 标题,其它字段不映射(可在写入后手动补到摘要 callout) |

## ❌ 降级 / 不支持(写 warning)

| 元素 | 降级行为 |
|---|---|
| 块级 LaTeX `$$ ... $$` | 飞书 markdown renderer 通常不识别块级,降级为纯文本或行内公式;复杂数学排版会丢 |
| `<details>` / `<summary>` 折叠块 | 飞书 docx 无对应 block,降为纯文本段落 |
| 脚注 `[^1]: ...` | 不支持,降为纯文本 |
| `<kbd>` 标签 | 不支持,降为普通文本 |
| 任务列表 `- [ ] task` | GFM 任务列表转 `<checkbox>` 的支持视 lark-cli 版本而定;若失败,会显示成普通列表 |
| 链接引用 `[text][ref]` + `[ref]: url` | 本 skill v1 未实现 ref 解析,文章里建议用 inline link `[text](url)` |
| HTML 内嵌(任意 `<div>` / `<span>` 等)| 飞书 markdown 模式会识别飞书认可的 inline XML(如 `<img>`、`<callout>`、`<whiteboard>`),其它 HTML 标签可能被忽略或转纯文本 |

preprocess.py 会扫上述模式并把告警写到 manifest.json 的 `warnings` 字段。skill 主流程在最终报告里把 warnings 列出来,提醒用户去飞书人工 review。

## 飞书原生 block,markdown 中不可表达

下列飞书富 block 在纯 markdown 里**没有对应语法**,本 skill v1 不主动生成。如果你想在飞书里看到它们,有两条路:

1. **在源 markdown 里直接写 inline XML**(飞书 markdown renderer 识别),例如:
   ```markdown
   <callout emoji="💡" background-color="light-yellow">
     <p>这是一段高亮提示。</p>
   </callout>
   ```
   preprocess.py 不会动这些标签,会原样传到飞书。
2. **写完后用 `lark-doc` skill 局部精修**,加 callout / grid / button 等。

| 飞书 block | 推荐写法 |
|---|---|
| 高亮框(callout) | inline `<callout>` 标签 |
| 分栏(grid + column) | inline `<grid>` 标签 |
| 待办框(checkbox) | inline `<checkbox done="false">` 或 GFM `- [ ]` |
| 书签 / URL 预览 | inline `<bookmark>` 或 `<a type="url-preview">` |
| 按钮 | inline `<button>` 标签(必须含 action 属性) |

详见 lark-doc skill 的 `references/lark-doc-xml.md`。

## 设计决策

本 skill **故意不写**完整的 MD → XML 转换器。理由:

- GFM 已经覆盖 90% 写作场景;飞书服务端 renderer 处理 90% GFM 语义。剩下 10% 的 edge cases 由 inline XML 补齐就够了。
- 自己写转换器 = 维护一份"小型 markdown parser",bug 数量随语法树深度指数增长。
- 飞书 markdown renderer 由飞书团队维护,会跟着 GFM spec 更新;复刻它没有意义。

如果发现某个常用 markdown 语法在飞书里渲染异常,优先方案是:

1. preprocess.py 加一条降级规则(把它转成飞书认可的等价 inline XML)
2. 在本文档加一行 warning
3. 让用户在飞书里手动调整

不要去重写 GFM parser。
