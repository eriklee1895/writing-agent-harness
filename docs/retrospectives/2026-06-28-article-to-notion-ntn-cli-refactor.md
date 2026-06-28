# article-to-notion 用 ntn CLI 重构（v2）

**日期**：2026-06-28
**主题**：把 `article-to-notion` skill 从手搓 REST API + 自写 markdown-to-blocks 解析器重构成用官方 `ntn` CLI，顺手沉淀 `notion-cli` 通用基础 skill。

## 背景

初版 article-to-notion 直接调 Notion REST API（`requests` + `NOTION_TOKEN` integration token + `.env`），自己写了 `notion_io.py`（18KB）+ `md_to_blocks.py`（16KB）。能跑，但痛点明显：

1. **integration token 配置负担**：用户要去 notion.so/developers/connections 创建 internal integration、复制 token、写 .env、然后对每个目标 page/database 做 "share connection"。这是 OAuth 时代完全没必要的 friction。
2. **markdown-to-blocks 转换难维护**：16KB 的递归下降解析器只覆盖了 heading/paragraph/list/code/quote/image/divider 基础块，碰到 table、复杂 nested list、callout 就漏。而 Notion 自己有成熟的 markdown → blocks 转换（`ntn pages create` 内置）。
3. **图片位置问题**：原实现用 placeholder external image block 占位 → PATCH 替换，但是 PATCH 不允许改 block type（external → file_upload），而且 `/blocks/children` PATCH 没有 `after` 参数（文档写了也不能用），没法真正在文档中部插入图片。只能先建 page 再 append，无法精确控制图片位置。

同期发现官方 `ntn` CLI（v0.17.1，通过 `curl -fsSL https://ntn.dev | bash` 安装）支持：
- OAuth 登录（`ntn login`），凭证存 keychain，**不需要 integration token 也不需要 share connection**
- `ntn pages create` 内置 markdown → blocks 转换
- `ntn files create --plain` 单行 single_part 上传
- `ntn api` 泛型 API wrapper

但 CLI 有一堆坑（空括号 `children[]=...` 内联语法会 hang、emoji/non-ASCII 内联 hang、stdin 未关闭时阻塞等），所以决定做个**项目级基础 skill** `notion-cli` 封装这些坑，上层 skill 通过 subprocess 调它的 Python helper。

## 做了什么

### 1. 新建 `notion-cli` 基础 skill（`.agents/skills/notion-cli/`）

- **SKILL.md**：命令清单 + gotchas（踩过的坑全记录）+ OAuth vs token 对比表
- **scripts/ntn_cli.py**（~760 行，PEP 723 单文件，零第三方依赖）：封装 13 个子命令：
  - `probe`：判目标类型（page / data_source / database）并返回 schema
  - `upload-file`：single_part 上传本地文件返回 file_upload ID
  - `create-page` / `get-page` / `trash-page` / `list-blocks`
  - `set-cover` / `set-icon` / `set-properties`（flat form 自动包装 + raw form 透传）
  - `create-page-with-images`⭐：核心——sentinel-marker 分片 + 段间交错插入图片
  - `overwrite-page-with-images`：clear-children 后走同样的 segment 布局
  - `append-markdown`：throwaway 子页 + block harvest + strip 技巧
  - `append-blocks` / `clear-children`

关键技术点：
- 所有 `ntn api` 调用都走 `--data <json>` body，避免内联语法 hang
- subprocess.run 总是显式 `stdin=DEVNULL` 或给 `input=...`，避免 ntn 阻塞等 body
- `_strip_block_ids()` 递归清掉 id/parent/timestamps/None 值/空 children/失效 external/presigned S3 URL，才能把临时页的 blocks 重新 POST 到目标页
- sentinel marker 用纯文本 `NTN_IMG_MARKER_<key>` 独占一行（前后空行），HTML 注释形式会被 markdown 解析器吃

### 2. 重构 `article-to-notion` 为 v2

- **删除** `notion_io.py`（18KB）和 `md_to_blocks.py`（16KB）——合计 34KB 易坏代码
- **重写 `compose.py`**（~280 行 vs 原 500+ 行）：核心职责压缩为
  1. probe 目标
  2. 剥 YAML frontmatter
  3. `![alt](local)` → NTN_IMG_MARKER_N 替换 + 收集图片
  4. 构造文章卡片 quote block
  5. 调 ntn_cli.py create/overwrite-page-with-images
  6. 设 cover/icon
  7. 如果是 database row，调 property_mapper 填 properties
- **保留** `fetch_article.py`（抓取逻辑与 Notion 无关）和 `property_mapper.py`（启发式字段映射）
- **新增 `_normalize_markdown()` 防御层**（v2.1，用户反馈后加的）：在上传前自动修复三类 agent 清洗容易遗漏的问题：
  1. **Merge quote blocks**：把连续的 `>` 行（包括空 `>`）合并成单行 `<br>` 连接的 quote，规避 ntn 把多行 `>` 拆成独立 quote 的坑
  2. **Strip leading H1**：删掉正文第一个 `# 标题`（文章卡片已经显示标题，H1 重复冗余）
  3. **Strip tail boilerplate**：从尾部扫描，自动删除公众号引流段落（"本公众号主要关注..."、"推荐阅读"+专辑链接列表、"扫码关注"、"未经授权禁止转载"等）。检测逻辑只从尾部起作用，避免误伤正文里偶尔提到"知识星球"等词的段落；尾图（二维码等）保留，留给 agent 人工判断
- **字段别名兼容**：manifest.json 里的 `account/publish_time/source_url` 自动映射到 `author/date/url`
- **properties 逻辑收紧**：只在 target 是 data_source/database（新建 row）或 page 是数据库行（overwrite）时设置 properties，不在普通 page 上 PATCH properties（400 Invalid property identifier）
- **SKILL.md 重写**：删除 NOTION_TOKEN 配置段，改成 `ntn login` OAuth 前置；去掉 notion-api-notes.md（被 notion-cli/SKILL.md 取代）

### 3. 端到端验证

用 2026-06-24 抓取的 Unlimited OCR 微信公众号文章（4 张图、~3.5KB 正文）做测试：

- 在测试 parent page 下创建子页面：4 张图都在正确位置（段落间），file_upload 类型（不担心防盗链）
- 在 AI模型收藏 database（`1954a37a-2324-816e-b381-000b37e5fdda`）创建新 row：Name/Tags/介绍 properties 正确填充
- Overwrite 已有 page：clear-children + 重新布局正常工作
- 最终成品：https://app.notion.com/p/Unlimited-OCR-Paddle-OCR-40-38d4a37a232481baa412f7edac5c2be9

## 关键决策与权衡

### 为什么 CLI 比 MCP 更适合 project skill

| 维度 | ntn CLI（选这个） | Notion MCP |
|---|---|---|
| 认证 | OAuth 登录一次，key 存 keychain | 需要手动给 MCP server 配 integration token |
| 环境可移植 | `uv run script.py` 子进程即可，不依赖 Claude/MCP runtime | 只有连 MCP server 的 session 能用 |
| 测试/调试 | 命令行直接跑，可 dry-run | 只能在 agent session 里试 |
| 脚本组合 | 一个 Python helper 脚本封装所有坑，上层脚本 subprocess 调用 | agent 每次都要读工具描述、重新踩坑 |
| 版本/行为可控 | ntn CLI 固定版本，helper 脚本可 patch | MCP server 升级可能偷偷改行为 |

**MCP 的优势**（跨工具搜索、UI 交互、DB schema 可视化等）在 article-to-notion 这种 headless 批处理场景用不上。结论：**project skill 的底层能力优先用 CLI，MCP 保留给探索性/交互式操作**。

### 为什么不直接在 compose.py 里调 ntn 命令而要写 helper

ntn CLI 的几个坑决定了不能直接把 ntn 命令拼 subprocess：
1. 内联 body 语法 `children[0][object]=block` 对空数组/non-ASCII 会 hang
2. set-cover 对 `type=file` 报错，必须 `type=file_upload`
3. PATCH block children 要清 null 字段
4. append markdown 需要 throwaway 子页 + block harvest + strip

这些坑集中在 ntn_cli.py 里处理一次，上层 compose.py 只要传干净参数就行。**以后任何 skill 需要写 Notion，直接调 ntn_cli.py 就能躲开所有已知坑**——这就是沉淀基础 skill 的价值。

### sentinel-marker + segment interleaving 解决图片位置

notion API 不支持在文档中部插入 block（PATCH children 只追加尾部），解决方案：

1. 把 markdown 按 `NTN_IMG_MARKER_<key>` 切成 `[text0, (image,key0), text1, (image,key1), text2, ...]`
2. 用 text0 创建 page
3. 循环：append image block → append text segment（用 throwaway 子页技巧）

这样图片严格保持在 markdown 里的位置，不用任何"占位 + 回填"花招。

## 坑点汇总（新沉淀的记忆）

- ntn 0.17.x 内联语法 `children[]=` 空括号会 hang；`icon[emoji]=🧪` 带 emoji 会 hang——**一律用 `--data '<json>'`**
- subprocess 调 ntn 必须显式 `stdin=DEVNULL`，否则 ntn api 阻塞等 body
- YAML frontmatter 是 `ntn pages get` 的**输出**方向；create 时**不解析** frontmatter，会被渲染成 divider+列表
- Block 的 `type` 字段不可 PATCH 修改（external image block 不能直接变 file_upload）
- PATCH children 时必须清掉所有 null 字段（`paragraph.icon: null` 被拒）和空 `children: []`
- PATCH /v1/blocks/{id}/children **不支持 `after` 参数**（文档写了但实测 400），只能追加尾部
- HTML 注释在 ntn markdown 里会被解析（`<!-- -->` 消失，`__xxx__` 变粗体），占位符必须用纯文本
- file_upload ID 有效期约 1 小时
- cover 在请求体是 `type=file_upload`（不是 `type=file`），响应返回才变成 `type=file`
- 对 database parent 要用 `data-source:<id>` 不是 `database:<id>`；一个 database 可能有多个 data source
- 给普通 page PATCH properties 报 400 "Invalid property identifier"；必须先判断页面是不是 database row（parent.data_source_id 是否存在）
- **多行 `>` quote 会拆成独立 quote block**：每行一个 `>`（包括空 `>`）会被 ntn 解析成多个 quote block，各带独立左侧竖线，不会像 CommonMark 那样合并。要在**一个 quote block 内换行**，必须用 `<br>` 把内容放在**同一行** `>` 段落里：`> line1<br>line2<br>line3`。这也是为什么文章卡片 quote 要从 4 行 `>` 改成单行 `<br>` 拼接
- ntn doctor 显示 "Public API access ✔" 才说明 OAuth 登录有效
- OAuth 登录的身份是用户本人，不需要 share connection；integration token 才需要 share

## 后续可以做的改进

- **property_mapper tags/type 重叠问题**：当前 tags 语义匹配到 Tags multi_select 后，type 语义因为 used set 就找不到字段了（"类型" 也是 multi_select 但被 tags 先占）。可以在 alias 匹配时更聪明：优先精确名字匹配，fallback 再 substring。
- **自动选 cover**：compose.py 已经支持 --cover，但没自动从正文图里挑一张。可以加个 `--auto-cover` 做"排除二维码/头像/小图，选第一张架构/对比图"的启发式。
- **nested list 渲染**：ntn 的 markdown parser 对中文输入法下的全角空格、缩进数量比较敏感，fetch_article 输出的 `* ` 列表已经 OK，但某些博客的 `-   ` 多空格缩进会渲染失败。
- **ntn 升级到 0.18.1**：当前是 0.17.1，新版本可能修了部分 hang 问题——但 helper 脚本的规避应该仍然安全。
- **append 模式**：compose.py 声明了 `--mode append` 但还没实现（当前 create/overwrite 已够用，append 留到真需要时再做）。

## 主要文件改动

- 新增：`.agents/skills/notion-cli/SKILL.md`、`.agents/skills/notion-cli/scripts/ntn_cli.py`
- 重写：`.agents/skills/article-to-notion/SKILL.md`、`.agents/skills/article-to-notion/scripts/compose.py`
- 修改：`.agents/skills/article-to-notion/scripts/property_mapper.py`（docstring 小修）
- 删除：`.agents/skills/article-to-notion/scripts/notion_io.py`、`.agents/skills/article-to-notion/scripts/md_to_blocks.py`、`.agents/skills/article-to-notion/references/notion-api-notes.md`

