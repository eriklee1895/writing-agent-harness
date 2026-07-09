---
name: notion-cli
description: |
  通过官方 `ntn` CLI 操作 Notion（创建/读取页面、上传文件/图片、设 cover/properties/icon、列出 blocks、追加内容）。
  封装了已踩过的坑（空括号 hang、emoji 内联失败、YAML frontmatter 输入方向不解析、block type 不能 PATCH 改、paragraph.icon:null 拒绝等），
  提供 `uv run scripts/ntn_cli.py <cmd>` 统一入口，默认用 `ntn login` OAuth（无需 integration token 和 share connection）。
  当其他 skill 需要写/读 Notion 页面，或 agent 自己要操作 Notion 时，优先用本 skill 而不是手写 `ntn api` 或直接调 REST API。
---

# notion-cli

通过官方 `ntn` CLI 操作 Notion 的基础 skill。封装了真实使用中踩过的坑点，提供统一的 Python helper 脚本。

## 何时使用

- 需要创建/更新/读取 Notion 页面（文字 + 图片混合排版）
- 需要上传图片/文件到 Notion 并获得 file_upload ID
- 需要给 database row 设置 properties（包括 title/select/multi_select/rich_text/date/url/number 等）
- 需要批量追加 markdown 内容到已有页面

其他 skill（如 `article-to-notion`）通过调用本 skill 的 `scripts/ntn_cli.py` 完成 Notion 写入。

## 不适用

- **跨连接器搜索**（Slack/Drive/GitHub + Notion 联合搜索）→ 用 MCP `notion-search`
- **管理 Notion Workers** → 直接用 `ntn workers *`（本 skill 不包装）
- **创建/修改 view** → 直接用 `ntn api` 或 MCP
- **创建/修改 database schema**（DDL 操作）→ 用 MCP `notion-update-data-source`（它用 SQL DDL 比 JSON 方便）

## 前置条件

1. 安装 ntn CLI：

    ```bash
    curl -fsSL https://ntn.dev | bash
    # 或
    npm install --global ntn
    ```

2. 登录（只做一次）：

    ```bash
    ntn login
    ```

    OAuth 浏览器授权后，凭证存在系统 keychain。**无需**去 https://www.notion.so/developers/connections 创建 integration token，**无需**对 page 做 "share connection"。

3. 验证：

    ```bash
    ntn doctor
    ```

    "Public API access" 显示 ✔ 即可。

可选：也支持 `NOTION_API_TOKEN` 环境变量（integration token），适合 CI 场景；存在时优先于 keychain。

## 核心命令

所有命令通过 helper 脚本调用：

```bash
uv run scripts/ntn_cli.py <cmd> [args...]
```

### probe — 探查目标

```bash
uv run scripts/ntn_cli.py probe <notion-url-or-id>
```

返回 JSON：`{"kind": "page|database|data_source", "id": "...", ...}`，database 还会列出 data sources，data source 还会返回 schema（字段名/类型/选项）。

### upload-file — 上传本地文件

```bash
FILE_ID=$(uv run scripts/ntn_cli.py upload-file ./photo.png --filename photo.png --content-type image/png)
# → 38d4a37a-.... (file_upload ID)
```

- 不传 `--filename`/`--content-type` 时从路径推断
- 支持 stdin：`cat photo.png | uv run scripts/ntn_cli.py upload-file - --filename photo.png --content-type image/png`
- 底层是 single_part 上传，文件持久托管到 Notion S3，URL 不会过期（返回给 block 的 URL 是带签名的，但 file_upload ID 长期有效）
- 免费 workspace 单文件 ≤5 MiB

### create-page-with-images — 创建图文混排页面（最常用）⭐

```bash
uv run scripts/ntn_cli.py create-page-with-images \
  --parent "<notion-url-or-parent-ref>" \
  --content-file ./article.md \
  --image "0=./assets/fig1.png" \
  --image "1=./assets/fig2.png" \
  --verbose
# → {"ok": true, "page_id": "...", "file_upload_ids": {"0": "...", "1": "..."}}
```

`article.md` 里用纯文本占位符标注图片位置（**必须独占一行，前后空行**）：

```markdown
# 标题

正文第一段。

NTN_IMG_MARKER_0

正文第二段，在图 0 之后。

NTN_IMG_MARKER_1

收尾段落。
```

- `--image key=path` 可以重复多次
- 也支持 `--images-file mapping.json`（JSON `{key: path}`）
- `--parent` 支持 Notion URL、`page:<id>`、`data-source:<id>`、`database:<id>`、纯 ID
- 创建 database row 时，用 `--parent data-source:<ds-id>`，然后用 `set-properties` 填字段
- 占位符名是 `NTN_IMG_MARKER_<key>`，key 是 `--image key=path` 里的 key（用数字最简洁）

**实现机制**：上传图片 → 创建 page（含第一段）→ 循环追加 image block 和后续 markdown 段（通过 throwaway 子页 + block harvest 技巧）。图片位置完全按 markdown 中的顺序插入。

### create-page — 创建纯文本页面（无图）

```bash
PAGE_ID=$(uv run scripts/ntn_cli.py create-page --parent <ref> --content-file ./doc.md)
```

### get-page — 读取页面

```bash
uv run scripts/ntn_cli.py get-page <page-id>                 # Markdown + YAML frontmatter(properties)
uv run scripts/ntn_cli.py get-page <page-id> --json          # JSON: page object + markdown string
```

### set-cover / set-icon

```bash
uv run scripts/ntn_cli.py set-cover <page-id> --file-id <file_upload_id>
uv run scripts/ntn_cli.py set-icon <page-id> --emoji "🧪"
uv run scripts/ntn_cli.py set-icon <page-id> --file-id <file_upload_id>
uv run scripts/ntn_cli.py set-icon <page-id> --external-url https://...
```

### set-properties — 设置 database row 属性

**Flat form（推荐）**：自动根据 data source schema 包装成 Notion 需要的结构：

```bash
uv run scripts/ntn_cli.py set-properties <row-id> --data-source-id <ds-id> --properties-json '{
  "Name": "文章标题",
  "Stars": "⭐⭐⭐⭐",
  "Tags": ["OCR", "多模态"],
  "介绍": "一句话摘要",
  "类型": ["OCR"],
  "Published": "2026-06-28",
  "URL": "https://example.com",
  "Score": 4.5
}'
```

支持的类型自动映射：`str → select`、`list[str] → multi_select`、`str → title/rich_text/date/url/email/phone_number`、`int/float → number`、`bool → checkbox`。

如果 page 已经是某个 data_source 的 row（parent.data_source_id 存在），可以省略 `--data-source-id`。

**Raw form**：传完整 Notion-shaped properties（`{"Name": {"title": [{"text": {"content": "..."}}]}, ...}`），原样 PATCH，不经 flat-form 转换。

### list-blocks — 列出页面 blocks

```bash
uv run scripts/ntn_cli.py list-blocks <page-or-block-id>
uv run scripts/ntn_cli.py list-blocks <page-id> --json
```

### append-markdown — 在页面末尾追加 Markdown

```bash
uv run scripts/ntn_cli.py append-markdown <page-id> --content-file ./more.md
```

底层用 throwaway 子页技巧，先写临时页、拷贝 blocks、再删临时页。支持所有 Markdown 元素。

### append-blocks / clear-children / trash-page

```bash
uv run scripts/ntn_cli.py append-blocks <page-id> --blocks-file ./blocks.json
uv run scripts/ntn_cli.py clear-children <page-id>         # 清空全部子 blocks（危险）
uv run scripts/ntn_cli.py trash-page <page-id>
```

## Gotchas（真踩过的坑）

- **❌ 不要用 `ntn api` 的空括号 `children[]` / `rich_text[]` 内联语法**：ntn 0.17.x 会挂起无响应。必须用显式索引 `children[0]`、`children[1]`。本脚本全程用 `--data '<json>'` 传 body，彻底规避。
- **❌ 不要用 `key=value` 内联语法传 emoji/非 ASCII**：`icon[emoji]=🧪` 会 hang，用 `--data '{"icon":{"type":"emoji","emoji":"🧪"}}'`。本脚本已封装。
- **❌ YAML frontmatter 是输出方向的**：`ntn pages get` 会把 properties 序列化为 YAML frontmatter，但 `ntn pages create` 输入 Markdown 时**不会**解析 frontmatter——会被当成正文展示（三横线变 divider、字段变列表）。properties 必须通过 `set-properties` 单独 PATCH。
- **❌ Block 的 `type` 字段不能通过 PATCH 修改**：一个空的 external image block 不能直接改成 file_upload image。必须删了重建。本 skill 的 create-page-with-images 不用 placeholder block，直接按 segment 追加。
- **❌ PATCH block children 时要清理 null 字段**：Notion API 会拒绝 `paragraph.icon: null`、空 `children: []`，要求必须是 undefined。`_strip_block_ids` helper 已处理。
- **❌ Markdown 多行 `>` quote 会拆成独立 quote block**：每行一个 `>` 会被解析成多个独立 quote block（每个带单独左侧竖线），不会合并。要在**单个 quote block 内换行**，用 `<br>` 把所有内容放在同一行 `>` 段落里：`> line1<br>line2<br>line3`。
- **❌ Markdown 里的 HTML 注释会被 parse**：`<!-- __IMG_0__ -->` 里的 `__xxx__` 会被当成粗体，`<!--` 会被吃。所以图片占位符必须是纯文本独占一段 `NTN_IMG_MARKER_<key>`。
- **❌ `ntn api` 在 stdin 未关闭时可能阻塞等 body**：subprocess 调用时必须显式设 `stdin=DEVNULL`（本脚本已处理）。
- **⚠️ `ntn pages create` 不支持 callout / highlight 语法**：`> 💡 xxx` 是普通 quote，`==xxx==` 原样输出。要做 callout 必须手 PATCH 把 quote block 改成 callout type（本 skill 暂不封装，需要时通过 append-blocks 手写）。
- **⚠️ file_upload ID 有效期约 1 小时**：上传后要在 1 小时内绑到 page/block/cover/icon 上，过期要重新传。
- **⚠️ cover 请求体是 `{type:"file_upload", file_upload:{id}}`**（不是 `type:"file"`）。响应里会变成 `type:"file"` 带 S3 URL。`set-cover` 已处理。
- **⚠️ 直接调 ntn 时，parent 参数对 database row 要用 `data-source:<id>`，不是 `database:<id>`**：一个 database 可能有多个 data source。probe 命令会自动解出默认 data source。
- **⚠️ `has_children: true` 不等于 children 内联**：`GET /v1/blocks/{id}/children` 对容器 block（table、toggle、synced_block、嵌套 list item）只返回 flag，不内联子 blocks。收割 block 再 PATCH 的路径必须对每个 `has_children: true` 的 block 额外 GET 一次 `/v1/blocks/{block_id}/children` 拿子块，否则 PATCH 会报 `X.children should be defined`。`ntn_cli.py` 的 `_strip_block_for_new` 已处理。
- **⚠️ `numbered_list_item.list_format` 是只读字段**：GET 返回里带 `list_format: "numbers"`（bulleted 有时也带），但 CREATE/PATCH 不接受，会报 `X.list_format should be not present`。写新 block 前要剥掉这类服务端派生字段。`_strip_block_ids` 通过 per-type `_READ_ONLY_TYPE_FIELDS` 集合在递归时过滤；后续碰到同类字段直接往里加。

## 为什么默认用 `ntn login` OAuth 而不是 integration token

| 维度 | `ntn login` (OAuth) | `NOTION_API_TOKEN` (integration) |
|---|---|---|
| 配置步骤 | `ntn login` 浏览器授权一次 | 去 developers/connections 创建 integration + 复制 token + 写入 .env |
| Page 授权 | 用户身份，能访问你能看到的所有 page | 必须对每个根 page/database 做 "share connection" |
| 适合场景 | 个人剪藏、日常操作（默认） | CI/CD、团队共享脚本、跨 workspace |

两种方式都能用；脚本自动识别（env var 优先，其次 keychain）。

## 脚本实现

- `scripts/ntn_cli.py`：单文件 PEP 723 Python 脚本，无第三方依赖（只用标准库 subprocess/json/argparse）。`uv run` 自动管理环境。
- 所有 `ntn api` 调用都走 `--data <json>` 模式，绕过内联语法坑。
- `--help` 自描述完整命令清单。

## 直接用 ntn 命令的场景

以下场景本 skill 不封装（很少用、或官方 CLI 已足够友好）：

- `ntn search` 不存在，要用 `ntn api v1/search query=foo` — 但对 agent 来说 MCP `notion-search` 更强（跨 connector）
- `ntn datasources query <id>` 简单查询
- `ntn api v1/comments` 评论操作（需要时直接调）
- `ntn workers *` Workers 生命周期管理

## 参考

- 官方文档：https://developers.notion.com/cli/get-started/overview
- File uploads 指南：https://developers.notion.com/cli/guides/file-uploads
- API requests inline 语法（不推荐，用 `--data` 更稳）：https://developers.notion.com/cli/guides/api-requests
- 项目内使用方：[article-to-notion](../article-to-notion/SKILL.md)
