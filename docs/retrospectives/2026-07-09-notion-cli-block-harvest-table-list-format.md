# notion-cli block-harvest fix: tables + list_format

**日期**：2026-07-09
**触发文章**：`content/origin/2026-07-08-claude-tool-search-deep-dive/` 写入 Notion 页面 `3974a37a-2324-8015-9b06-f04dfaaa221b`
**主题**：`ntn_cli.py` 的 throwaway-subpage block-harvest 路径在长文（含 table 和 numbered_list_item）下连续踩两个 PATCH 400，已修复。

## 背景

`notion-cli/scripts/ntn_cli.py` 里的 `create-page-with-images` / `overwrite-page-with-images` / `append-markdown` 都走"临时子页 + block 收割 + strip 字段 + PATCH 回目标页"的 trick：
1. 用 `ntn pages create` 在目标页下建一个临时子页，把 markdown 交给 Notion 自己渲染成 blocks；
2. `_fetch_all_children(scratch_id)` 拿所有 block JSON；
3. `_strip_block_for_new(b)` 递归剥掉 id/parent/timestamps/None 值/失效 S3 URL/空 children；
4. `run_ntn(["pages", "trash", scratch_id, "--yes"])` 清掉临时页；
5. 把 clean blocks 按 50 个一批 PATCH 到目标页 `/children`。

这个方案之前在短文（无表格、只有 bullet list）上跑得通，但写 Tool Search 这篇长文时连挂两次。

## 问题 1：table block 的 children 不内联返回

### 报错

```
Error: ntn failed (PATCH v1/blocks/.../children):
  stderr: error: Public API request failed (400 Bad Request validation_error):
    body failed validation: body.children[24].table.children should be defined, instead was `undefined`.
```

### 根因

`_strip_block_for_new()` 原先只在 block JSON 内联携带 `children` 字段时递归复制：

```python
if b.get("has_children") and "children" in b.get(t, {}):
    out[t]["children"] = [_strip_block_for_new(c) for c in b[t]["children"]]
```

但 Notion API 的 `GET /v1/blocks/{id}/children` 对容器 block 的行为是：
- `has_children: true` 只是个 flag；
- 容器的**子 blocks 不在父 block JSON 里内联**，必须再发一次 `GET /v1/blocks/{parent_block_id}/children` 才能拿到；
- 这对 `table`、`toggle`、`synced_block`、含嵌套 list 的 `bulleted_list_item` / `numbered_list_item` 等都成立。

短文里只有 flat 结构（paragraph/bulleted_list/code/quote/image/divider），没有带 children 的容器，所以 bug 一直没爆。Tool Search 文第一张表（核心概念地图 7 行）触发了 `table.children undefined`。

### 修复

对所有 `has_children=True` 的 block 显式 fetch 一次子块：

```python
if b.get("has_children"):
    child_blocks = _fetch_all_children(b["id"])
    nested = [_strip_block_for_new(c) for c in child_blocks]
    if nested:
        out[t]["children"] = nested
```

副作用：每次 strip 会多一次 GET/容器。目前只有真正有 children 的 block 才触发（table / toggle / 嵌套 list），短文中不会增加 API 调用；长文里 tables 本来就不多，可接受。

## 问题 2：`numbered_list_item.list_format` 是只读字段

### 报错

修完问题 1 后重跑，换了新错误：

```
Error: ntn failed (PATCH v1/blocks/.../children):
  stderr: error: Public API request failed (400 Bad Request validation_error):
    body.children[12].numbered_list_item.list_format should be not present, instead was `"numbers"`.
```

### 根因

Notion 在 GET 返回的 `numbered_list_item` / `bulleted_list_item` JSON 里会加一个 `list_format: "numbers"` / `"bulleted"` 字段（标记列表渲染风格），但 **CREATE/PATCH children 不接受这个字段**，会被判为"不应出现"而 400。

之前短文中所有列表都是 bullet（`bulleted_list_item`），而 ntn 给 `bulleted_list_item` 返回的 JSON 里恰好没加 `list_format`（或者老版本没加），所以没暴露。Tool Search 文有多处 `1. / 2. / 3.` 编号列表，第一次触发。

### 修复

加了 per-type 只读字段集合，在 `_strip_block_ids()` 递归剥离时按 type_name 过滤：

```python
_READ_ONLY_TYPE_FIELDS: dict[str, set[str]] = {
    "numbered_list_item": {"list_format"},
    "bulleted_list_item": {"list_format"},
}
```

同时把 `_strip_block_ids()` 签名改为接一个 `type_name` 参数：`_strip_block_for_new()` 调它时传当前 block type，递归进嵌套 dict（rich_text span、annotations、file_upload 对象等）时传 `None`，避免误把同名非类型字段剥掉。

> 这是个 whack-a-mole 集合。后面如果碰到其他"GET 返回 / PATCH 拒收"字段（例如某些 block 的 `color` 派生字段、toggle 的状态字段），直接往 `_READ_ONLY_TYPE_FIELDS` 加即可。

## 验证

用 Tool Search 整篇（~24KB markdown，含 5 张表、~15 段代码块、2 张上传图、编号列表、引用、Mermaid 代码块）重跑 `overwrite-page-with-images`：
- clear → upload 2 图 → 5 段 segment append 全部成功；
- `list-blocks` 显示 286 个 block，tail 走到"Last updated: 2026-07-08"；
- table、numbered list、mermaid code block 都能正确打开（在 Notion 浏览器里目视检查）。

## 建议沉淀

这两个坑的通用规律：

1. **Notion block 的 `has_children: true` ≠ children 内联**。任何收割 block 再 PATCH 的路径，都必须对每个 has_children block 额外 GET 一次 children，不能指望初始 list 返回里带。
2. **Notion block 上很多"看起来是属性"的字段其实是服务端派生的只读字段**（`list_format` 是典型）。碰到"X should be not present"这种 400，第一反应是往只读字段集合里加，不要猜是值不对。

这两条经验更新到 `notion-cli/SKILL.md` 的 Gotchas 段即可；不需要改 `article-to-notion`（底层逻辑都在 ntn_cli.py）。

## 后续

- [x] 修复 `ntn_cli.py`
- [x] 在 Tool Search Notion 页面上端到端验证（286 blocks, 2 images, 5 tables）
- [ ] 把两条规律补进 `.agents/skills/notion-cli/SKILL.md` Gotchas
- [ ] 提交 PR 到 main
