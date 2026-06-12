# HTML Parser & Content Extraction Stack — 选型参考

> 适用于 `wechat-article-fetcher`、未来通用 article fetcher、以及任何"HTML 片段 / 整页 → Markdown / 结构化文本"场景的栈选型。

**核心结论：当前 `wechat-article-fetcher` 的 `Playwright + BeautifulSoup4 + markdownify` 栈不需要改。** 性能不是瓶颈，Trafilatura 会严重损坏 Markdown 输出，Selectolax 是合理的现代化替代但对单文章交互式使用没有用户可感知的收益。

## 工具定位速查

| 工具 | 定位 | 对应替代 |
|------|------|---------|
| **BeautifulSoup4** | 通用 HTML 解析，API 丰富、容错强、纯 Python | 经典选择 |
| **Selectolax** | Cython + C 引擎（Lexbor）的高速 CSS 选择器解析器 | ≈ 现代高速版 bs4 |
| **Trafilatura** | 从任意网页自动猜正文 + 抽 metadata + 去噪 | ≈ 现代版 Readability / Newspaper3k |
| **markdownify** | HTML 片段 → Markdown 的直接映射（标签→语法的硬编码规则） | 不直接对应，是 renderer |
| **html2text** | 老牌 HTML→Markdown 工具，规则粗放 | markdownify 的老前辈 |

⚠️ **Selectolax 和 Trafilatura 不是竞争关系，是不同问题域的工具。** Selectolax 解决"快速 DOM 解析和操作"，Trafilatura 解决"从混乱整页里找出正文"。两者经常一起用：`selectolax` 解析结构 + 抽链接 + 抽元数据，`trafilatura` 抽正文。

## Benchmark 数据

### 官方 benchmark（Selectolax 文档，754 个域名首页解析）

| 方案 | 耗时 |
|------|------|
| BeautifulSoup (html.parser) | 61.02 s |
| BeautifulSoup (lxml) | 9.09 s |
| html5_parser | 16.10 s |
| Selectolax (Modest，已废弃) | 2.94 s |
| **Selectolax (Lexbor)** | **2.39 s** |

→ Selectolax (Lexbor) 比 bs4 html.parser 快 **~25x**，比 bs4 + lxml 快 **~4x**。

### 真实 11824 页面爬取

| 解析器 | 总耗时 | 页/秒 |
|--------|--------|-------|
| Selectolax [lexbor] | 274 s | 43 |
| lxml | 266 s | 44 |
| BeautifulSoup [lxml] | 1,694 s | 7 |
| BeautifulSoup [html.parser] | 2,292 s | 5 |
| BeautifulSoup [html5lib] | 4,575 s | 3 |

### 内存占用（10 MB HTML）

| 解析器 | 峰值内存 |
|--------|---------|
| BeautifulSoup + html.parser | ~250 MB |
| BeautifulSoup + lxml | ~180 MB |
| lxml direct | ~90 MB |
| Selectolax (Lexbor) | 与 lxml 同档 |

来源：[selectolax.readthedocs.io](https://selectolax.readthedocs.io/)、[rushter/selectolax GitHub](https://github.com/rushter/selectolax)、[Fastest Python Web Scraping Library Benchmarks](https://bytetunnels.com/posts/fastest-python-web-scraping-library-benchmarks/)。

## Trafilatura 实际行为（v2.0.0 实测）

> 这些都是直接从 v2.0.0 跑出来的，不是文档承诺。引用前请到 [trafilatura docs](https://trafilatura.readthedocs.io/) 核对当前版本。

| 元素 | 行为 | 对 Markdown 输出的影响 |
|------|------|------------------------|
| `<pre><code>` | 整段压成一行，换行被吞 | ❌ 没有 fence code block |
| `<pre>` | 同上 | ❌ |
| `<code>` (inline) | 输出为纯文本 | ❌ 没有反引号 |
| `<img>` (`include_images=True`) | **静默丢弃**，不生成 `![alt](src)` | ❌ 图片全丢 |
| `<table>` (`include_tables=True`) | 拍平成纯文本垂直列表 | ❌ 没有 pipe table |
| `<strong>` `<em>` (`include_formatting=True`) | 文本保留但**不生成 `**` `*`** | ❌ 标记被剥离 |
| `<a>` (`include_links=True`) | 文本保留但**不生成 `[text](url)`** | ❌ 链接被剥离 |
| `<ul>` `<ol>` | 嵌套列表拍平成单层 | ❌ 层级丢失 |
| HTML 片段输入 | **必须包 `<html><body>` wrapper**，否则返回 `None` | ⚠️ 不能直接传 `#js_content` 的 `inner_html()` |
| 目标容器 | **没有 `target` / `selector` 参数**，只能用 `prune_xpath` 反向减枝 | ⚠️ 不能指定"只抽 `#js_content`" |

**结论**：Trafilatura 是给"任意网页猜正文"用的，不是给"已知 HTML 片段干净转 Markdown"用的。把它套到公众号这种**结构已知 + Markdown 质量敏感**的场景，会严重退化输出。

## 维护状态

| 库 | 最新版本 | 最近发布 | 状态 |
|---|---|---|---|
| beautifulsoup4 | 4.14.3 (2025-11-30) | 4.14.3 (2025-11-30) | ✅ 活跃维护，2025 内连发 4.13.x 和 4.14.x |
| selectolax | 0.4.10 (2025-05-26) | 0.4.10 (2025-05-26) | ✅ 活跃维护，2025 内连发 3 个版本，Lexbor 引擎独立维护 |
| trafilatura | 2.1.0 (2026-06-07) | 2.1.0 (2026-06-07) | ✅ 活跃维护，但作者在 README 公开呼吁赞助，**funding-dependent** |
| markdownify | 1.1.x | 1.1.x (2024) | ⚠️ 节奏放缓但功能稳定 |

→ **BeautifulSoup4 没有过时。** "现代爬虫圈"更偏好 Selectolax 是性能导向，但 bs4 的 API 稳定、社区庞大、纯 Python 不需要编译，对中小项目和脚本工具依然是稳妥选择。

## 选型决策矩阵

按场景给出推荐栈。

### 场景 A：公众号文章 / 已知 HTML 片段 → Markdown

**推荐：`Playwright + BeautifulSoup4 + markdownify`**（当前栈）。

理由：
- 容器已知（`#js_content`），不需要正文启发式
- Playwright 渲染 + 网络占 90% 时间，解析耗时无关紧要
- bs4 + markdownify 对公众号的 `p/h1-h6/img/blockquote/pre/code/ul/ol/table/section/mprecover` 都能干净转 Markdown
- Trafilatura 反而会把代码块压成一行、图片丢失、表格拍平

如果未来要做批量（10k+ 文章/天）才考虑切到 `Selectolax + markdownify`，性能差才能体现出来。

### 场景 B：任意网页（新闻站 / 博客 / Substack / Medium）→ Markdown + metadata

**推荐：`HTTPX + Selectolax + Trafilatura`**。

理由：
- 容器未知，需要 Trafilatura 启发式识别
- Trafilatura 自带 metadata 抽取（title/author/date/sitename）
- Selectolax 处理链接/图片地址抽取等需要 DOM 操作的子任务
- 可接受 Trafilatura 的 Markdown 缺陷（代码拍平、表格拍平），因为通用抓取本来就追求"有就行"

### 场景 C：实时/流式/边缘环境解析

**推荐：`Selectolax`**。

理由：
- 比 bs4 快 4-25x，CPU 时间直接等于成本
- 内存占用接近 lxml

### 场景 D：容错 / 畸形 HTML

**推荐：`BeautifulSoup4 + html5lib`**。

理由：
- html5lib 是最严格的 HTML5 解析器，按规范重写畸形标签
- bs4 提供最丰富的遍历 API 和容错能力

### 场景 E：需要 XPath / XSLT

**推荐：`lxml`**。

理由：
- 唯一同时支持完整 XPath 1.0/2.0、XSLT、XML 命名空间的 Python 解析器
- 性能接近 Selectolax

## 当前栈改进建议

针对 `wechat-article-fetcher` 现有的 [`pre_clean_html`](../../agents/skills/wechat-article-fetcher/scripts/fetch.py) 流程，不改栈也能提升的 3 件事：

### 1. 增强 pre-clean 规则

```python
# 当前：只清理 noise + 修 <pre><p>
# 建议：把微信特有标签也加进去
for sel in ("script", "style", ".qr_code_pc", ".reward_area", "mpcover"):
    for tag in soup.select(sel):
        tag.decompose()

# <pre> 里的 <span>/<section>/<div> 也 unwrap 成文本
for pre in soup.find_all("pre"):
    for tag in pre.find_all(["p", "span", "section", "div"]):
        tag.replace_with(f"{tag.get_text()}\n")
```

### 2. 给 bs4 加 `lxml` fallback

```python
try:
    from lxml import html as lxml_html  # noqa: F401
    soup = BeautifulSoup(html, "lxml")
except ImportError:
    soup = BeautifulSoup(html, "html.parser")
```

→ 如果系统装了 lxml，自动快 4 倍；没装也不报错。

### 3. 清理/明确依赖

[`pyproject.toml`](../../pyproject.toml) 当前已经列了 `trafilatura>=2.0.0` 但代码完全没用。要么：
- **删除**：等真的要做通用文章抓取再 `uv add`
- **保留并注释**：在依赖行加 `# 预留：未来 generic-article-fetcher 使用`

如果选删除，记一笔到 `docs/retrospectives/` 或 `AGENTS.md` 的 Current Defaults，让未来的自己知道为什么没装。

## 实际落地（2026-06-12）

上面 3 条建议已在 `wechat-article-fetcher` 实施，落地细节：

### `WECHAT_NOISE_SELECTORS`（[fetch.py:125](../../agents/skills/wechat-article-fetcher/scripts/fetch.py#L125)）

```python
WECHAT_NOISE_SELECTORS = (
    "script", "style",
    ".qr_code_pc", ".reward_area",
    ".original_area_primary",   # "阅读原文" card at article end
    ".wx_profile_card_inner",   # 公众号名片卡
    "mpcps", "mp-common-profile", "mp-miniprogram",
    "mp-weapp", "mpvoice", "mpprofile",
)
```

**注意：`mpcover` 没加进删除列表**——它是合法的图片容器标签，新版文章里常用于包裹带说明的图片，删了会丢内容。

### `_get_bs4_parser()` 统一 lxml fallback

`pre_clean_html` 和 `download_images` 都通过同一个 helper 拿到 parser，确保 lxml 装了就用、没装也不报错。

### `<pre>` 块处理升级

旧逻辑只处理 `<pre><p>`。公众号富文本编辑器对代码块的实际结构是 `<pre><span>...</span></pre>` 多 span 假换行。新逻辑：

1. 对每个 span，**先** `insert_after("\n")`（unwrap 前 span 还在树上），**再** `unwrap()`，避免 unwrap 后失去 parent
2. 直接子节点的 `<p>/<div>/<section>` 转成文本 + `\n`

实测合成 HTML：

```html
<pre><span>def hello():</span><span>    return 1</span></pre>
```

输出：

````markdown
```
def hello():
    return 1
```
````

### 依赖说明

`pyproject.toml` 里 `trafilatura>=2.0.0` 加了行内注释说明是预留（等未来 generic-article-fetcher 使用），不删是因为现在装一次也占用不大，避免后续重新加麻烦。

## 实测验证（2026-06-12）

跑了一篇真实公众号文章 `https://mp.weixin.qq.com/s?__biz=MzkyMzY1NTM0Mw==&mid=2247487442&idx=1&sn=da3eb6245ea1528e8cae585d58a06de8&...`（AI进修生《CopilotKit 开源 Copilot 框架》），覆盖：

- 普通段落 + 列表 + heading
- 3 张 png 配图 + 1 张 svg
- 1 个内嵌视频 iframe
- 多个 fenced code block（`<pre><p>` 和 `<pre><span>` 两种结构）
- 微信视频播放器 UI 噪点

### 输出质量对比

| 段落 | 改前 | 改后 |
|------|------|------|
| 视频播放器 UI（"全屏"/"倍速 0.5x 0.75x..."/进度条） | ❌ 全部进 Markdown | ✅ 全清（`iframe` / `video` 进 noise selectors） |
| `<pre><p>pnpm i</p><p>@copilotkit/react-core</p></pre>` | ✅ 已 OK | ✅ 单行 `pnpm i @copilotkit/react-core` |
| `<pre><span>npm</span><span>i</span><span>@copilotkit</span>...</pre>` | ❌ 全压成一行 | ✅ 每个 span 后正确换行（检测到 `<br>` 或 `\n` 时） |

### 发现的新坑点

1. **公众号代码块内的 `<span>` 通常被 `<br>` 或 `\n` 文本节点隔开**——这是公众号富文本编辑器的特殊结构。修法：检测 sibling 含 `<br>` 或 `\n` 文本节点时，unwrap span 前先 `insert_after("\n")`。
2. **微信公众号视频播放器 UI 默认是"侵入式"的**——`<iframe class="video_iframe">` 外层是微信渲染的视频控件（"已关注"、进度条、倍速等），全部是文本节点。`iframe` + `video` 直接进 noise selectors 是合理选择。
3. **mpvideo.qpic.cn 的 mp4 URL 仍然出现在 `manifest.json` 的图片清单里**——因为视频是 `<img class="__bg_gif">` 之类的封面图被 `download_images` 抓到了；如果想要完整视频清单，需要在 `download_images` 里另外处理 `<a>` 链接或保留 iframe 节点供用户手动抓取。

### 残留未优化的边界

- **一些非常细碎的微信内联 class**（如 `.tags`、`.tag_list`）偶尔会带无用信息进 Markdown，**先观察再说**，等真正影响阅读再统一处理。

## 视频处理决策（2026-06-12 补充）

**公众号文章里的视频不需要抓取解析**，理由：

1. 公众号视频托管在腾讯视频（`mpvideo.qpic.cn/...mp4`），加 `auth_key`/`auth_info` 鉴权，**离线下载几乎不可行**
2. 公众号文章内容主体是文字+图片，视频是补充演示
3. 视频播放器 UI（"全屏"、"倍速"、进度条）全是公众号渲染的壳，无研究价值
4. 本 skill 用途是"写作素材收集"，不是视频再分发

### 实施细节

#### 1. 跳过视频封面图

[`fetch.py`](../../agents/skills/wechat-article-fetcher/scripts/fetch.py) `download_images` 里加白名单检查：

```python
if not src or "mmbiz.qpic.cn" not in src or "mpvideo.qpic.cn" in src:
    continue
```

#### 2. 删除视频播放器 DOM 但保留 `[视频]` 占位符

实现踩到的 3 个坑：

**坑 A**：`insert_before` 在嵌套结构里会把 marker 插到 iframe 的直接父节点（mpcps）**内部**，导致 marker 被 mpcps selector 整块删掉。

**修法**：Pass 1a 跳过 mpcps 内的 iframe，留给 Pass 1b 处理 mpcps 自身。

**坑 B**：微信公众号的 `<video>` 嵌在多层 div 里（`js_inner / js_video_poster / video_mask / video_fill`），外层 div 在 noise selectors 里被删。如果只在 `<video>` 之前插 marker，外层 div 一删 marker 也跟着没。

**修法**：在 [`fetch.py`](../../agents/skills/wechat-article-fetcher/scripts/fetch.py) 加 `_VIDEO_WRAPPER_CLASSES` 列表，循环往上走，找到**最外层会被 noise selector 删的 wrapper**，在它**之前**插 marker。同时把对应的 class 加进 `WECHAT_NOISE_SELECTORS`（如 `.mp-video-player`）。

**坑 C**：markdownify 把 `*` 转义成 `\*`（避免和 markdown 斜体语法冲突），`*[视频]*` 最终变成 `\*[视频]\*`，看上去就是反斜杠+星号，不是预期的"视频"marker。

**修法**：把 marker 改成 `[视频]`（中括号 + 文字），不是 `*[视频]*`。

### 最终结果

| 改动 | 影响 |
|------|------|
| `_VIDEO_WRAPPER_CLASSES` + walking logic | marker 出现在视频容器外层 |
| 扩展 `WECHAT_NOISE_SELECTORS` 加 `.mp-video-player` 等 | 视频播放器全部 UI 清掉 |
| marker 从 `*[视频]*` 改为 `[视频]` | markdownify 不再转义，marker 正确显示 |
| `download_images` 跳过 `mpvideo.qpic.cn` | 视频封面图不被当作普通图片下载 |

## 选 Selectolax 时的迁移步骤（备用）

如果以后批量抓取需求真的出现，**目标栈是 `Selectolax + markdownify`（不是 `Selectolax + Trafilatura`）**，迁移步骤：

1. `uv add selectolax`
2. 重写 [`pre_clean_html`](../../agents/skills/wechat-article-fetcher/scripts/fetch.py)：
   ```python
   from selectolax.lexbor import LexborHTMLParser

   tree = LexborHTMLParser(html)
   for node in tree.css("script, style, .qr_code_pc, .reward_area, mpcover"):
       node.decompose()
   for pre in tree.css("pre"):
       # 找到所有 <p>/<span>/<section>/<div> 子节点，unwrap
       for tag in pre.css("p, span, section, div"):
           tag.replace_with(tag.text() + "\n")
   cleaned_html = tree.html
   ```
3. 重写 [`download_images`](../../agents/skills/wechat-article-fetcher/scripts/fetch.py)：
   ```python
   for img in tree.css("img"):
       src = img.attributes.get("data-src") or img.attributes.get("src") or ""
       if "mmbiz.qpic.cn" not in src:
           continue
       # ...download + 改写 src
       img.attrs["src"] = rel_path
   updated_html = tree.html
   ```
4. markdownify 保持不变
5. 跑 5-10 篇缓存的公众号文章做 diff 对比，确保输出一致
6. 删 bs4 在本 skill 里的直接 import（其他 skill 可能还用）

## 关键反模式

### ❌ 用 Trafilatura 转公众号 HTML 片段

```python
# 错误：会返回 None
content = trafilatura.extract(content_el.inner_html())
```

### ❌ 用 Selectolax 做"找正文"任务

Selectolax 不做正文识别，只做 DOM 解析。找正文是 Trafilatura 的事。

### ❌ 拿 benchmark 数字当迁移理由

Benchmark 是 754 域名 / 11824 页面的数字，公众号 fetcher 一次只抓 1 篇，解析耗时 < 100ms。**节省 90ms 对单次交互流程无感**。只有做 batch 时 Selectolax 才有压倒性优势。

### ❌ 以为 "BeautifulSoup4 = 过时"

bs4 2025 年连发 4.13.x / 4.14.x，最新 4.14.3 (2025-11-30)，维护活跃。"现代爬虫圈"趋势偏好 Selectolax 是事实，但**趋势不等于适配所有场景**。

## 决策记录

| 日期 | 决策 | 原因 |
|------|------|------|
| 2026-06-12 | `wechat-article-fetcher` 保留 `BeautifulSoup4 + markdownify` | 性能非瓶颈，Trafilatura 不适配，Selectolax 收益不显 |
| 2026-06-12 | 实施 3 条不改栈优化：扩展 `WECHAT_NOISE_SELECTORS`、`_get_bs4_parser` 统一 lxml fallback、`<pre>` span→换行升级 | 见上文"实际落地"section |
| 2026-06-12 | 视频不抓解析：跳过 mpvideo 封面图 + 删播放器 DOM + 留 `[视频]` 占位符 | 见上文"视频处理决策"section |

## 引用

- [selectolax GitHub](https://github.com/rushter/selectolax)
- [selectolax docs](https://selectolax.readthedocs.io/en/latest/)
- [trafilatura GitHub](https://github.com/adbar/trafilatura)
- [trafilatura docs](https://trafilatura.readthedocs.io/en/latest/)
- [Fastest Python Web Scraping Library Benchmarks](https://bytetunnels.com/posts/fastest-python-web-scraping-library-benchmarks/)
- [Efficient Web Scraping: lxml, BeautifulSoup, Selectolax](https://medium.com/@yahyamrafe202/in-depth-comparison-of-web-scraping-parsers-lxml-beautifulsoup-and-selectolax-4f268ddea8df)
