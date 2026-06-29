---
name: wechat-article-publisher
description: 用 Playwright 把微信公众号文章（文章流程）同步到草稿箱。输入 origin index.md（content/origin/YYYY-MM-DD-&lt;slug&gt;/，frontmatter 元数据权威源）+ wechat-article-renderer 产出的 HTML preview，自动登录态复用、注入正文、上传正文图片到微信 CDN、写标题/作者/摘要、保存草稿并报告 appmsgid。当用户要"发布公众号草稿""同步到草稿箱""publish wechat draft"时使用。仅创建草稿，不点发布/群发。
---

# WeChat 公众号文章发布器（Playwright）

用 Playwright 驱动微信公众号后台的「文章」编辑器，把渲染好的文章同步到草稿箱。

## 发布边界（重要）

- 本 skill **只创建草稿**（保存到草稿箱），**绝不点击发布/群发**。
- 成功信号：编辑页 URL 出现 `appmsgid=...`（或保存成功 toast）。进入草稿箱 ≠ 已发布。
- 最终发布必须由用户在微信后台做 human review 后手动决定。

## 前置

- 本机安装 Google Chrome（或设 `CHROME_EXECUTABLE`）。
- Python 依赖由脚本 PEP 723 inline metadata 自声明，`uv run` 自动安装。
- 首次运行需扫码登录一次；登录态存独立 profile `~/.config/wechat-article-publisher/profile/`，之后免扫码（`login_wait≈0`）。可用 `--profile` 或 `WECHAT_PUBLISH_PROFILE_DIR` 覆盖。

## 元数据权威源

**标题/作者/摘要/封面 取自 origin `.md` 的 frontmatter，不是渲染后的 HTML**（renderer 的 `<title>`/`<meta>` 是正文派生值，会与作者意图不一致）。渲染 HTML 只提供排版好的正文。

| 字段 | 解析顺序 |
|------|----------|
| 标题 | `--title` → frontmatter `title` → 正文首个 H1（renderer hero，会从正文剔除避免重复） |
| 作者 | `--author` → frontmatter `author` → repo `.config/wechat.toml` `default_author` →（缺失）首次运行询问并写回 |
| 摘要 | `--summary` → frontmatter `description`/`summary` → 正文首段（≤120 字） |
| 封面 | `--try-cover` 开启自动上传（frontmatter `cover` 相对 .md 目录；推荐预裁剪为 2.35:1 比例，省去编辑器内裁剪步骤）。成功时左侧卡片显示封面，失败不阻塞草稿保存 |
| 原创声明 | `--declare-original` 勾选「声明原创」（需账号已开通原创功能）；作用域限定在原创弹窗内的「确定」按钮 |

作者等恒定本机配置放在 repo 根下 **`.config/wechat.toml`**（已 `.gitignore`），首次缺 `default_author` 时脚本会自动创建。

## 推荐链路

```text
content/origin/YYYY-MM-DD-<slug>/index.md（frontmatter 权威源）
  → wechat-article-renderer → index.wechat-preview.html（在 origin 同目录）
  → 拷贝为 content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html（渠道归档，wechat-publish-workflow 标准流程第 6 步，**不要跳过**）
  → 本 skill（--article 指向 origin index.md + --html 指向 wechat/ 归档副本）→ 草稿箱 → user final review（设封面、定夺发布）
```

`content/wechat/YYYY-MM-DD-<slug>/` 是微信渠道派生 artifact 的 canonical 目录，与 `appmsgid`/发布 URL 一一对应；不要直接从 `content/origin/.../*.wechat-preview.html` 推送给 publisher，否则 `appmsgid` 无法对应到渠道归档。

## 用法

先 dry-run 验证填充（不存草稿），确认无误再加 `--save-draft`：

```bash
# 推荐：frontmatter 来自 source .md，正文用 renderer 产出的 HTML
uv run scripts/publish.py \
  --article content/origin/YYYY-MM-DD-<slug>/index.md \
  --html    content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html \
  --save-draft

# 备用：只给 .md（极简排版，无 renderer 样式）
uv run scripts/publish.py \
  --article content/origin/YYYY-MM-DD-<slug>/index.md --save-draft
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

## 浏览器模式：默认 headed（headless=False）

脚本用 `p.chromium.launch_persistent_context(..., headless=False)` 启动有头 Chrome + 持久 profile，**不要改成 headless**：

1. 首次必须扫码（或点「微信快捷登录」），headless 无法交互。
2. 即使已登录复用 cookie，微信后台反自动化检测对 headless 敏感（UA、`chrome.runtime`、WebGL、事件指纹），容易 403/跳登录/保存失败。
3. 正文图片上传走编辑器内文件选择 + XHR 回填 mmbiz URL，headless 下隐式失败（图片插入但 CDN URL 不回填）难排查。
4. final human review 必须人工看一眼，headed 浏览器停在编辑页就是 review 入口。
5. `自动保存失败`/外链告警等弹框在 headed 下肉眼可见，headless 只能靠截图事后 debug。

未来加 `--headless` 必须作为实验性 opt-in flag（`headless=new`），且需先在 [docs/retrospectives/2026-06-29-wechat-publisher-headed-mode.md](../../docs/retrospectives/2026-06-29-wechat-publisher-headed-mode.md) 登记 ≥20 篇稳定性数据，默认仍保持 headed。

## 已知限制 / 坑点

- **封面图：`--try-cover` 已稳定（2026-06-29 起）**。走 WebUploader 隐藏 `<input type=file>` 的 `set_input_files`（不点透明 label overlay，overlay 会拦截）→ 等 `mmbiz.qpic.cn` URL 出现 → JS 定位「下一步」可见主按钮 → 完成。建议把封面预裁为 2.35:1（公众号封面标准比例），跳过编辑器内裁剪步骤更稳。`--try-cover` 仍为 opt-in（不强制每篇都需要封面），失败时 `cover-set-failed` 不阻塞草稿保存。
- **标题字段是隐藏 textarea + 独立 ProseMirror**：直接设 `#title.value` 不显示（隐藏镜像），必须键入可见的 `#js_title_main .ProseMirror`。
- **正文图片串行上传**：每张等 CDN 完成再传下一张，多图文章更慢但可靠。大图慢网络下单张可能逼近 60s 超时；脚本如实打印「请求 N / 已插入 M」，M<N 时清理残留占位符并提示人工补图。不自动重传。
- **草稿保存三重确认**：编辑器 tab 打开时 URL 已预分配 appmsgid，不能当作保存成功信号。脚本用 (a)「保存成功」toast、(b) appmsgid 变更、(c) `#title` 回读匹配预期标题 + 按钮 loading 态消失 ≥2s 三重验证，默认 30s 超时。保存前先按 `Tab` blur 触发 Vue 把 ProseMirror 输入 flush 到隐藏 textarea。仍失败时截图存 `scripts/.artifacts/` 并提示去草稿箱人工确认（常已自动保存）。
- **多账号**：用不同 `--profile` 目录隔离登录态，无内置账号管理。
- 失败/校验截图存 `scripts/.artifacts/`（gitignored，可能含后台/登录态，勿提交）。
