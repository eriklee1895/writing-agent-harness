---
name: article-to-notion
description: |
  将任意网页文章（微信公众号、技术博客、论文页面等）抓取、清洗并转写到用户指定的 Notion page 或 database row。
  当用户给出一个或多个文章 URL 和一个 Notion 目标链接，并说"读到 Notion / 收藏到 Notion / 剪藏到 Notion / 整理进笔记 / 整理进 Notion"时，必须使用本 skill。
  支持微信公众号 Playwright 抓取（含 data-src 懒加载图片）、通用站点 firecrawl/tavily 抓取、图片本地上传到 Notion（解决微信防盗链）、表格/代码块适配 Notion 排版、database property 启发式填充、cover 图片自动设置。
  依赖 notion-cli skill 的 ntn CLI 封装；认证走 ntn login OAuth，无需手动创建 integration 或 share connection。
---

# article-to-notion

将网页文章高质量剪藏到 Notion。支持微信公众号、技术博客、论文页面等来源。

## 何时使用

- 用户给出文章 URL + Notion 目标 URL，要求"读到 Notion / 收藏到 Notion / 剪藏到 Notion / 整理进笔记"
- 用户提到要把某篇文章整理收藏，并指定了 Notion 的具体位置（page 或 database）
- 需要把微信公众号文章完整抓取（含正文图片）并写入 Notion

## 不适用

- 批量迁移整个网站（用 firecrawl-crawl）
- 视频、音频、播客页面（本 skill 只处理文字 + 静态图）
- 登录墙后的非微信页面（不处理通用登录墙）
- 用户没有给目标 Notion URL（skill 不猜目标位置）

## 前置条件

1. 已安装并登录 `ntn` CLI（由 [notion-cli](../notion-cli/SKILL.md) skill 管理）：
    ```bash
    ntn doctor
    ```
    "Public API access" 显示 ✔ 即可。如果未登录，运行 `ntn login` 通过 OAuth 授权一次。
    **不需要**手动创建 Notion API integration，也**不需要**对目标 page/database 做 "share connection"。

2. 微信公众号抓取需要 `wechat-article-fetcher` skill 的 Playwright 环境。
3. 通用站点抓取建议安装 `firecrawl` CLI 或 `tvly` (Tavily) CLI。

## 整体流程

skill 由 agent 编排，分四步：

1. **抓取**：`fetch_article.py` 把文章拿到本地（含图片）
2. **清洗与重组**（agent 智能完成）：你阅读抓回来的 markdown，按下文规则清洗、提炼摘要、按原文层级保留结构
3. **确定写入模式**：根据目标 URL/ID 判断是创建新页面/新行，还是覆写已存在的行
4. **写入**：`compose.py` 调用 notion-cli helper（上传图片 + 创建/覆写页面 + 填 properties + 设置 cover/icon）

## Step 1：抓取文章

```bash
uv run scripts/fetch_article.py <article-url>
```

行为：
- `mp.weixin.qq.com` → 调用项目 [wechat-article-fetcher](../wechat-article-fetcher/SKILL.md)（Playwright + 持久 Chrome profile）
- 其他域名 → firecrawl scrape，失败 fallback 到 tavily extract
- 输出到 `~/.cache/article-to-notion/fetches/<date>-<slug>/`，含：
  - `article.md`：原始 markdown（带 YAML frontmatter）
  - `manifest.json`：标题、作者、发布时间、图片清单（字段：title/account/publish_time/source_url/images[]）
  - `assets/`：本地图片副本

加 `--output-dir <dir>` 可指定输出位置。

## Step 2：清洗与重组（agent 智能完成）

读取 `article.md`，重写成 Notion 友好的内容。规则：

### 删除
- YAML frontmatter（compose.py 会自动剥离，你也可以手动删）
- 公众号 UI 垃圾：二维码、点赞在看、推荐阅读专辑链接、公众号名片、"推荐阅读" 栏
- 引流段落：含"关注公众号"、"扫码加入"、"星球"、"加群"等关键词
- 作者抒情、自我介绍、号召分享（不影响核心信息理解时）

### 保留
- 正文、章节小标题、代码块、表格、有信息量的图片
- GitHub / arXiv / 论文 / 官方文档等 reference 链接（移到末尾 Reference 节）

### 重写规则
- 按原文层级保留小标题（Notion `##` 二级）
- 重新组织句子，去除啰嗦，但**不要过度概括**——保持信息密度，保留具体数据、名词、链接
- 提炼 3-5 句摘要（用于 database `介绍/Summary` property，**不重复写入正文**）
- 不在正文加额外的 `# 摘要` 或 `# 个人备注` 标题
- 不要改写图片引用路径 `![alt](assets/img-xxx.png)`——compose.py 会自动替换为上传占位符

### 最终正文结构

```markdown
[清洗后的正文，按原文层级保留结构]

# Reference
- 原文：[标题](URL)
- 相关链接：...
```

compose.py 会自动在正文前加**单个 quote block** 形式的文章名片（所有字段用 `<br>` 连接在一个 `>` 段落里，避免 ntn markdown 把多行 `>` 拆成多个独立 quote block）：

```
> **标题**：《...》<br>**来源**：...<br>**发布时间**：YYYY-MM-DD<br>**原文**：[链接](URL)
```

### 构造 metadata JSON

准备一份 metadata JSON 给 compose.py（用于 database properties + 文章卡片）。字段名用**规范名**：

```json
{
  "title": "文章标题",
  "author": "公众号/作者名",
  "date": "2026-06-24",
  "url": "https://...",
  "summary": "3-5 句摘要，用于 database 介绍/description 字段",
  "tags": ["OCR", "多模态"],
  "type": ["OCR"],
  "stars": "⭐⭐⭐⭐"
}
```

如果你直接传 fetch_article 输出的 manifest.json 路径给 `--fetch-dir`，compose.py 会自动做字段映射（account→author, publish_time→date, source_url→url），但 summary/tags/type/stars 这些需要你另外提供（可以通过 `--metadata` 覆盖）。

## Step 3：确定写入模式

`--notion-target` 接受 Notion 页面 URL、database URL、data-source URL、或 `<kind>:<id>` 形式的 ref。`--mode` 决定写入方式：

| 目标类型 | mode=auto（默认） | mode=create | mode=overwrite |
|---|---|---|---|
| plain page URL | 在该 page 下创建**子页面** | 同 auto | 清空该 page 并重写 |
| database / data-source URL | 在库里创建**新行** | 新行 | （不支持） |
| database row URL（已存在行） | （不适用） | （不适用） | 清空该行内容并重写，更新 properties |

**常见用法**：
- 剪藏到一个 inbox 页面下：传 page URL，mode=auto（默认），会在该 page 下建子页面
- 剪藏到 database：传 database/data-source URL，mode=auto（默认），会新建一行
- 更新已有 database row：传 row 的 page URL，加 `--mode overwrite`

## Step 4：写入 Notion

```bash
uv run scripts/compose.py \
  --notion-target <notion-url-or-ref> \
  --content-file <path-to-cleaned-markdown> \
  --fetch-dir <fetch-dir>                  \
  --metadata <path-to-metadata-json>      \
  --cover <local-image-path>              \
  --icon-emoji "📰"                       \
  --mode auto
```

参数：
- `--notion-target`（必填）：Notion URL 或 `page:<id>` / `data-source:<id>` 形式
- `--content-file`（必填）：清洗后的 markdown 文件
- `--fetch-dir`：fetch_article.py 的输出目录（用于解析 `assets/` 相对路径图片和 manifest.json 元数据）
- `--metadata`：额外 metadata JSON（覆盖 fetch-dir 的 manifest.json）
- `--cover`：本地封面图路径；不传则不设 cover；传 `"none"` 显式禁用
- `--icon-emoji`：页面 emoji icon
- `--mode`：`auto`/`create`/`overwrite`（默认 auto）
- `--dry-run`：只打印将要做什么，不调用 Notion API

stdout 输出 JSON：
```json
{
  "ok": true,
  "page_id": "...",
  "url": "https://app.notion.com/p/...",
  "images_uploaded": 4,
  "cover_set": false,
  "icon_set": true,
  "properties_set": ["Name", "Tags", "介绍"]
}
```

`compose.py` 内部步骤（对 agent 透明）：
1. 调 `ntn_cli.py probe <target>` 判断目标类型（page / data_source / database）
2. 读取 markdown，剥离 YAML frontmatter
3. 把 `![alt](assets/xxx.png)` 本地引用替换为 `NTN_IMG_MARKER_<idx>` 占位符，收集图片路径
4. 在 plain page/database row 正文前自动加文章卡片 quote block（标题/来源/时间/原文链接）
5. 调 `ntn_cli.py create-page-with-images`（create 模式）或 `overwrite-page-with-images`（overwrite 模式）：
   - 上传所有本地图片到 Notion（single_part，长期有效 S3 托管）
   - 创建页面/清空目标页面
   - 按 markdown 中的顺序，段间插入 image block + 正文
6. 上传并设置 cover（如有）、设置 emoji icon
7. 如果页面是 database row（新建的或 overwrite 的），用 `property_mapper.py` 把 metadata 按 schema 映射成 Notion properties 并 PATCH
8. 输出最终 JSON

## Cover 图选择

从清洗后的图片里挑第一张"内容图"作为 cover：
- 排除：二维码、作者头像（通常是小尺寸圆形）、纯文字 banner、广告条
- 优先：架构图、对比图、截图、第一张正文插图

不强求。没有合适的图就不传 `--cover`（compose.py 自动跳过）。

## 错误诊断

| 现象 | 原因 | 处理 |
|---|---|---|
| `Error: ntn CLI not found in PATH` | 没装 ntn | `curl -fsSL https://ntn.dev \| bash` 然后 `ntn login` |
| `ntn doctor` 里 "Public API access" 不是 ✔ | 未登录 | `ntn login` 浏览器 OAuth 授权一次 |
| `Error: notion-cli helper not found at ...ntn_cli.py` | notion-cli skill 未安装/不在同级目录 | 安装 notion-cli skill 到 `.agents/skills/notion-cli/` |
| `image not found locally: assets/xxx.png` | markdown 图片路径不对 | 传 `--fetch-dir` 指向 fetch 输出目录，或用绝对路径 |
| properties skip: "no matching property" | 目标 database 没这个字段 | 正常；property_mapper 会跳过 schema 里没有的字段 |
| PATCH 400 "Invalid property identifier X" | 试图给非 database row 的普通页面设 properties | 检查 `--notion-target` 类型；这是 compose.py 的 bug 请上报 |

## Gotchas

- **图片必须上传，不要用外链**。Notion 不会自动转存外链；微信 CDN（mmbiz.qpic.cn）有 Referer 防盗链，外链会失效（已实测）。
- **微信公众号必须走 Playwright 抓取**：firecrawl / tavily 都拿不到 `data-src` 懒加载的正文图（[[tavily-can-fetch-wechat-text-not-images]]）。
- **YAML frontmatter 不解析成 properties**：`ntn pages create` 把 `---` 当 divider、字段当列表。compose.py 会自动剥离 frontmatter；metadata 通过 property_mapper 单独设置。
- **正文和 properties 不重复**：摘要只填 property，不在正文加 `# 摘要` 标题。
- **Plain page 元数据用 quote block**：compose.py 自动在正文前加单个 quote block 的文章卡片。多行 `>` 在 ntn markdown 里会被拆成多个独立 quote block，所以用 `<br>` 连接在一个 `>` 里，不要写成多行 `>`。
- **single_part 上传限制**：免费 workspace 单文件 ≤5 MiB；超过会失败（脚本不会自动压缩）。
- **file_upload ID 有效期约 1 小时**：compose.py 一次性完成上传+绑定，不会有过期问题；如果你手工分步调用 ntn_cli.py，注意时效。
- **覆写已有页面会清空全部 children**：`--mode overwrite` 会删除目标页下所有 block 再重写，不能部分更新。
- **Block type 不可 PATCH 改变**：所以 overwrite 是先 delete 再 append，不是 in-place 替换。
- **不要在 markdown 里写 HTML 注释**：ntn 的 markdown 解析器会吃注释，里面的 `__xxx__` 会变粗体。图片占位符用纯文本 `NTN_IMG_MARKER_N`（compose.py 自动生成，你不用手写）。
- **compose.py 有 normalize 防御层兜底**：上传前会自动（1）把连续 `>` 行合并成单 quote + `<br>`（避免多行 quote 被拆成独立块）、（2）删掉正文开头第一个 `# 标题`（和文章卡片重复）、（3）从尾部自动剥掉公众号引流段落（"本公众号主要关注..."、"推荐阅读"+专辑链接、"扫码关注"、"未经授权禁止转载"等）。你仍然应该在 Step 2 清洗时主动删明显垃圾，但少量漏掉的会被兜底。尾图（二维码、公众号头像）保留，留给 agent 人工判断是否需要删。

更多 ntn CLI 本身的坑点见 [notion-cli/SKILL.md Gotchas 段](../notion-cli/SKILL.md)。

## 脚本清单

- `scripts/fetch_article.py`：抓取文章到本地（Playwright / firecrawl / tavily）
- `scripts/compose.py`：主编排脚本（probe → 图片占位替换 → create/overwrite page → set cover/icon/properties）
- `scripts/property_mapper.py`：metadata → Notion properties 的启发式映射（按 schema 自动包装类型）

`notion_io.py` 和 `md_to_blocks.py` 已删除（v2 重构后所有 Notion IO 通过 ntn CLI 完成）。

## 依赖

- `uv`、`ntn` CLI（`curl -fsSL https://ntn.dev | bash` 后 `ntn login`）
- `playwright` + Chrome（微信公众号抓取）
- 可选：`firecrawl` CLI、`tvly` CLI（通用站点抓取）
- 项目 skills：[notion-cli](../notion-cli/SKILL.md)、[wechat-article-fetcher](../wechat-article-fetcher/SKILL.md)

## 参考

- [Property 别名表](references/property-aliases.md)
- [notion-cli skill](../notion-cli/SKILL.md)
- [wechat-article-fetcher skill](../wechat-article-fetcher/SKILL.md)
