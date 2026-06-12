---
name: wechat-article-publisher
description: 用 Playwright 把微信公众号文章（文章流程）同步到草稿箱。输入 source article.md（frontmatter 元数据权威源）+ wechat-article-renderer 产出的 HTML preview，自动登录态复用、注入正文、上传正文图片到微信 CDN、写标题/作者/摘要、保存草稿并报告 appmsgid。本项目替换 baoyu-post-to-wechat CDP 模式的首选发布器。当用户要"发布公众号草稿""同步到草稿箱""publish wechat draft"时使用。仅创建草稿，不点发布/群发。
---

# WeChat 公众号文章发布器（Playwright）

用 Playwright 驱动微信公众号后台的「文章」编辑器，把渲染好的文章同步到草稿箱。无缝替换 `baoyu-post-to-wechat` CDP 模式：代码约 1/4、依赖更少（无 `baoyu-chrome-cdp`）、auto-wait 更稳。延续 `wechat-article-renderer` / `wechat-article-fetcher` 命名家族。

迁移背景与对比数据见 [docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md](../../../docs/retrospectives/2026-06-11-playwright-wechat-migration-analysis.md)。

## 发布边界（重要）

- 本 skill **只创建草稿**（保存到草稿箱），**绝不点击发布/群发**。
- 成功信号：编辑页 URL 出现 `appmsgid=...`（或保存成功 toast）。进入草稿箱 ≠ 已发布。
- 最终发布必须由用户在微信后台做 human review 后手动决定。

## 前置

- 本机安装 Google Chrome（或设 `CHROME_EXECUTABLE`）。
- Python 依赖已在项目 `pyproject.toml`：`playwright`、`beautifulsoup4`。`uv sync` 即可。
- 首次运行需扫码登录一次；登录态存独立 profile `~/.config/wechat-article-publisher/profile/`，之后免扫码（`login_wait≈0`）。可用 `--profile` 或 `WECHAT_PUBLISH_PROFILE_DIR` 覆盖。

## 元数据权威源

**标题/作者/摘要/封面 取自 source `.md` 的 frontmatter，不是渲染后的 HTML**（renderer 的 `<title>`/`<meta>` 是正文派生值，会与作者意图不一致）。渲染 HTML 只提供排版好的正文。

| 字段 | 解析顺序 |
|------|----------|
| 标题 | `--title` → frontmatter `title` → 正文首个 H1（renderer hero，会从正文剔除避免重复） |
| 作者 | `--author` → frontmatter `author` → `config.toml` `default_author` →（缺失）首次运行询问并写回 |
| 摘要 | `--summary` → frontmatter `description`/`summary` → 正文首段（≤120 字） |
| 封面 | **默认手动**（在草稿箱 final review 设）。`--try-cover` 实验性自动上传：`--cover`（相对 CWD）→ frontmatter `cover`（相对 .md 目录） |

作者等恒定项放 [config.toml](config.toml)（已预填 `default_author = "李玉恒"`）。

## 推荐链路

```text
article.md（frontmatter）→ wechat-article-renderer → *.wechat-preview.html（正文）
  → 本 skill（--article + --html）→ 草稿箱 → user final review（设封面、定夺发布）
```

## 用法

先 dry-run 验证填充（不存草稿），确认无误再加 `--save-draft`：

```bash
# 推荐：frontmatter 来自 source .md，正文用 renderer 产出的 HTML
uv run python .agents/skills/wechat-article-publisher/scripts/publish.py \
  --article content/source/<slug>/article.md \
  --html    content/wechat/<slug>/article.wechat-preview.html \
  --save-draft

# 备用：只给 .md（极简排版，无 renderer 样式）
uv run python .agents/skills/wechat-article-publisher/scripts/publish.py \
  --article content/source/<slug>/article.md --save-draft
```

| 参数 | 说明 |
|------|------|
| `--article` | source `.md`，frontmatter 元数据权威源；无 `--html` 时也作正文（极简渲染） |
| `--html` | renderer 产出的 `*.wechat-preview.html`，提供排版好的正文（优先） |
| `--title` / `--author` / `--summary` / `--cover` | 覆盖对应元数据 |
| `--save-draft` | 实际保存草稿（默认 dry-run 只填不存） |
| `--profile` | Chrome profile 目录（多账号用不同 profile） |

`--article` 和 `--html` 至少给一个。

## 工作原理（已验证）

1. **登录态复用**：`launch_persistent_context` 复用独立 profile；未登录时等待扫码（或点「微信快捷登录」），轮询进入 `/cgi-bin/home`。
2. **进编辑器**：首页点「文章」菜单，`expect_page()` 声明式捕获新标签页，等正文 ProseMirror 就绪。
3. **正文注入**：从 HTML 提取 `article.dark-text`、**剔除 hero 大标题**（避免与标题字段重复），图片先替换成占位符，`execCommand('insertHTML')` 注入正文 ProseMirror。外链兜底转纯文本（微信拒绝非 mp.weixin.qq.com 外链）。
4. **正文图片（串行）**：renderer 把图片包成 `<figure><img><figcaption>`。提取时**拆掉 figure**，转成「占位符段 + 干净的居中 caption 段」（否则图片被抽走后 figure 里残留空 leaf，在图与 caption 之间留一条空行——baoyu 当年没解决的正是这个嵌套空节点）。再定位占位符 → 删除 → `set_input_files` 上传 → 等图片计数 +1 → **等该图 `src` 变成 `mmbiz.qpic.cn`（CDN 完成）再传下一张**（微信串行化上传，不等就会让第 2 张起超时）。上传后清理残留占位符和空段（消除图-caption 空行）。
5. **标题/作者/摘要**：在正文+图片**之后**写（否则会被正文编辑冲掉）。标题不是普通 input——可见标题是独立的 `#js_title_main .ProseMirror`（同步到隐藏 `<textarea id=title>`），用**点击+键入**写入，再回读 `#title.value` 校验；保存前再确认一次。
6. **保存草稿**：按「保存为草稿」按钮文本定位点击，多信号确认（appmsgid / 成功 toast），超时报错并截图。

## 已知限制 / 坑点

- **封面图：默认手动（Playwright 自动化尝试结论）**。微信封面不是标准 file input，它是自定义的「拖拽/选图 + 裁剪 + 确认」多步模态，走**自定义拖拽控件 + 异步图库上传**（非 native file chooser）。Playwright `expect_file_chooser` + `set_input_files` 能触发上传，但 `mmbiz.qpic.cn` 预览图加载后弹窗残留"必须插入一张图片"错误——裁剪/确认步骤的 DOM 信号不可靠。最终技术结论：**封面自动化不可靠，不走这条线**。所以封面**默认不尝试**（避免每次发布白等 ~25s），在草稿箱 final review 时手动设置——你本来就要过一遍草稿箱核对正文图文，设封面是顺带的事。`--try-cover` 保留为实验性 flag（点封面区→本地上传→等加载→完成），**不保证成功，不阻塞草稿保存**。弹窗有用观察：「从正文选择」可选择已上传的正文首图做封面——若封面即正文首图，未来可探更稳路径。
- **标题字段是隐藏 textarea + 独立 ProseMirror**：直接设 `#title.value` 不显示（隐藏镜像），必须键入可见的 `#js_title_main .ProseMirror`。
- **正文图片串行上传**：每张等 CDN 完成再传下一张，多图文章更慢但可靠。大图慢网络下单张可能逼近 60s 超时；脚本如实打印「请求 N / 已插入 M」，M<N 时清理残留占位符并提示人工补图。不自动重传。
- **草稿保存确认是微信侧 flaky 行为**：同样内容可能 2s 或数十秒。脚本用 robust 点击 + 多信号 + 120s 容忍；仍失败时截图存 `scripts/.artifacts/` 并提示去草稿箱人工确认（草稿常已自动保存）。
- **多账号**：用不同 `--profile` 目录隔离登录态，无内置账号管理。
- 失败/校验截图存 `scripts/.artifacts/`（gitignored，可能含后台/登录态，勿提交）。

## 与 baoyu-post-to-wechat 的关系

baoyu CDP 模式已从本 repo 移除（历史代码可在 upstream [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 找到）。新文章走本 skill。两者都只到草稿箱，最终发布由用户确认。
