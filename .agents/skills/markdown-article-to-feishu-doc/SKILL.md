---
name: markdown-article-to-feishu-doc
description: |
  把一篇本地 markdown 文档转写成飞书云文档(docx),排版精美、block 结构完整。
  Mermaid 默认保留为 ```mermaid 代码块(源码可复制);--mermaid-mode whiteboard 时渲染成飞书画板。
  触发:用户说"把 markdown 发到飞书"/"转写到飞书"/"这篇要发飞书";或给了本地 .md 路径,可附带 docx URL(不提供则创建新文档)。
  不触发:微信公众号(走 wechat-publish-workflow)、Notion、Drive 原生 .md(走 lark-markdown)、docx 内部编辑(走 lark-doc)。
metadata:
  requires:
    bins: ["lark-cli"]
    skills: ["lark-doc", "lark-whiteboard", "lark-shared"]
---

# markdown-article-to-feishu-doc

把本地 markdown 文章转写成飞书云文档(docx),保留 frontmatter 元信息、本地图片、Mermaid 图(默认保留为代码块,可选渲染为画板)。

## 适用 / 不适用

| 适用 | 不适用 |
|---|---|
| 用户给本地 `.md` 路径,要发到飞书 | 微信公众号 → `wechat-publish-workflow` |
| 大部分场景:**全新创建**飞书文档 | 飞书云盘的 `.md` 文件 → `lark-markdown` |
| 少数场景:用户给空白/旧 docx URL,确认 overwrite 后整篇覆盖 | 已发布飞书 docx 内的局部精修 → `lark-doc` |
| markdown 含 frontmatter / 本地图片 / Mermaid | 增量同步、diff/patch(本 skill 不做) |

## 必读前置

第一次跑前,**必须**确认调用方 agent 已安装 `lark-doc` / `lark-whiteboard` / `lark-shared` 三个 skill。
本 skill 只做两件事:**预处理 markdown** + **编排 lark-cli 调用**;XML 规范、画板编辑、认证细节全部委派给上述 skill。

## 流程(Code-Act Loop)

```
                preprocess.py
markdown ─────────────────────────► 处理后 markdown + image manifest + title
   │
   │ (本地图片 → <img src="__PLACEHOLDER_N__"/>;
   │  mermaid 块默认保留为 ```mermaid 代码块,--mermaid-mode whiteboard 时转 <whiteboard type="mermaid">..</whiteboard>)
   │
   ▼
lark-cli docs +create  (空骨架,只写 <title> + 一个占位段落) ─────► doc_id, doc_url
   │
   ▼
对 manifest 里每张本地图:
  lark-cli docs +media-insert --doc <doc_id> --file <local_path> ─► file_token
   │
   ▼
把处理后 markdown 里 __PLACEHOLDER_N__ 替换成对应 file_token
   │
   ▼
lark-cli docs +update --command overwrite --doc-format markdown --content @processed.md
   │
   ▼
报告:doc_url + block 计数 + 上传图片数 + mermaid 数 + warnings
```

### 1. precheck

```bash
bash scripts/precheck.sh
# 失败时打印 GitHub 链接和安装命令;不替用户安装。
```

### 2. 参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `--file <path>` | 是 | 本地 markdown 路径 |
| `--doc <url-or-token>` | 否 | 已存在的 docx URL/token;**提供则走 overwrite 旁路**,缺失则新建 |
| `--parent-position my_library` | 否 | 新建时的父位置;默认个人知识库 |
| `--mermaid-mode <code\|whiteboard>` | 否 | Mermaid 处理方式。默认 `code`(保留为 ```mermaid 代码块,源可复制);`whiteboard` 转成飞书画板(复杂 Mermaid 可能解析失败) |

### 3. 预处理

```bash
mkdir -p .skill-work/
uv run scripts/preprocess.py \
  --input <article.md> \
  --workdir .skill-work/ \
  [--mermaid-mode whiteboard]   # 可选:把 mermaid 渲染成飞书画板;默认保留为代码块
# 产物:
#   .skill-work/processed.md    主体 markdown(图占位;mermaid 按 mode 处理)
#   .skill-work/manifest.json   {"title": "...", "mermaid_mode": "code"|"whiteboard", "images": [...]}
```

### 4. 创建空 docx 或确认覆盖

```bash
# 新建场景(无 --doc):
TITLE=$(jq -r .title .skill-work/manifest.json)
lark-cli docs +create --api-version v2 --parent-position my_library \
  --content "<title>${TITLE}</title><p>__draft_init__</p>"
# → 拿到 doc_id 和 doc_url

# 覆盖场景(有 --doc):
lark-cli docs +fetch --api-version v2 --doc <url> --scope outline
# 给用户报告现有内容摘要,等用户确认 "可以覆盖" 后才继续。
```

### 5. 上传本地图片

```bash
# 对 manifest.images 每一项:
lark-cli docs +media-insert --doc <doc_id> --file <local_path>
# 拿返回值里的 file_token,记录到 .skill-work/manifest.json 的 file_token 字段
```

> **注意:** `+media-insert` 会在文档末尾插入一个图片 block;但下一步 `overwrite` 会清空所有 block,**file_token 仍然有效**(token 是 tenant 级资源)。这是有意为之的"先上传拿 token,再整篇重写"模式。

### 6. 占位替换

`uv run scripts/preprocess.py --finalize --workdir .skill-work/`

把 `processed.md` 里的 `__PLACEHOLDER_N__` 替换成对应 `file_token`,产出 `final.md`。

### 7. 整篇 overwrite

```bash
lark-cli docs +update --api-version v2 --doc <doc_id> --command overwrite \
  --doc-format markdown --content @.skill-work/final.md
```

### 8. 报告

打印:
- doc_url(用户点击直达飞书编辑页)
- 上传图片数、mermaid 数、block 数(从 update 返回值取)
- warnings 列表(降级条目、未支持语法)
- 提示用户去飞书编辑器人工 review 排版

## 关键决策与边界

- **混合写入策略**: 主体 `--doc-format markdown`(借飞书服务端 renderer 处理标题/列表/代码块/表格/引用),只有图片用 inline XML 标签覆盖;Mermaid 默认保留为代码块(`--mermaid-mode whiteboard` 时切到 inline `<whiteboard>` XML)。理由:不重写 GFM(GitHub Flavored Markdown)parser,工作量小,bug 少。
- **不写 MD→XML 全量转换器**:依赖飞书 markdown renderer 处理 90% GFM 语义。
- **Mermaid 默认保留为代码块**:飞书 markdown 模式会把 ```mermaid 渲染成带 `mermaid` 语言标签的代码块,源码可复制/编辑;whiteboard 模式对复杂 Mermaid(subgraph、note、长 label)经常解析失败(返回 warning 2107),且画板内不可直接编辑源码。需要图形化渲染时显式传 `--mermaid-mode whiteboard`。
- **Mermaid whiteboard 直传约束**(仅 whiteboard 模式): `<whiteboard type="mermaid">{code}</whiteboard>` 在 markdown 模式下作为 inline XML 标签被飞书识别,服务端自动渲染成画板;**不调** `lark-whiteboard +update`。注意:不要 XML-escape mermaid 内容(会导致解析失败),不要插入 `<br/>` HTML 换行(用 `\n`)。
- **图片 file_token 是 tenant 级资源**: 上传后写到 XML 的 `<img src="FILE_TOKEN"/>` 里;overwrite 后图片仍可用。
- **不做增量 diff**:每次都是全篇覆盖。
- **overwrite 前必须 fetch 探测**:发现 docx 已有非本 skill 产物的内容时,中断并问用户。
- **LaTeX 块级公式降级**: `$$...$$` 飞书 markdown 模式可能不识别;skill 把它降级成 `<latex>...</latex>` 行内,失精度。
- **GFM `<details>` / KBD / 脚注降级**: 飞书 docx 不原生支持,降级成普通段落,在 warnings 中提示。

## 已知限制

详见 [`references/supported-syntax.md`](references/supported-syntax.md)。

## 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `lark-cli not found` | 未装 lark-cli | 跑 `references/install-lark-stack.md` 指引 |
| `permission denied` / `missing scope` | 未授权或权限不够 | `lark-cli auth login`,见 `lark-shared` |
| 图片在飞书显示空白 | file_token 与上传账号绑定,跨账号失效 | 重新用同一身份上传 |
| Mermaid 渲染失败 / 想保留源码 | `--mermaid-mode whiteboard` 下复杂语法飞书不支持 | 默认就是 code 模式(保留为 ```mermaid 代码块);已传 whiteboard 时重跑用 `--mermaid-mode code`,或手工转 SVG 插入 |
| `+create` 报 `--parent-position` 不可用 | 用户没有个人知识库或未授权 | 改用 `--parent-token <folder_token>` |

## 委派关系

- [`lark-doc`](https://github.com/larksuite/cli):docx 创建 / 更新 / fetch / 媒体插入 / XML 规范
- [`lark-whiteboard`](https://github.com/larksuite/cli):若 mermaid 直传失败,降级路径(本 skill v1 默认不走)
- [`lark-shared`](https://github.com/larksuite/cli):认证、`auth login`、`--as user/bot` 切换

## 相关文件

- `scripts/precheck.sh` — 启动检查
- `scripts/preprocess.py` — frontmatter 解析 + image / mermaid 占位
- `references/install-lark-stack.md` — lark-cli 与相关 skill 的安装指引
- `references/supported-syntax.md` — 支持的 markdown 语法清单与降级策略
