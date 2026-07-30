# 2026-07-16 《胡适种下一盆花，我们唱了一百年》写作与发布复盘

## Timeline

- 早上地铁听到《兰花草》，触发选题。
- article-ideation → 确定 thesis（小歌见大历史，散文+轻考古），brief 落盘 `content/drafts/2026-07-16-lanhua/`。
- Workflow 广泛搜集素材（8 路 web search + 12 路 fetch verify，~61 万 token）。
- 初稿 → polish → 加章节短标题 → 补胡适西山赠花细节 → 精简结尾到金句。
- Seedream 5.0 Pro 生成插图：首次竖版图构图失衡，改为 16:9 横版 + 新中式编辑插画，5 张图定稿（封面/赠花/校园/歌词漂流/结尾）。
- 归档到 `content/origin/2026-07-16-lanhua/`。
- `wechat-article-renderer --style warm-editorial` 渲染 HTML，preview server 用 python http.server 修复图片路径问题。
- `wechat-article-publisher` 创建草稿：appmsgid=100001000，5 张图全部上传到微信 CDN，14 秒登录扫码。
- 复盘时发现 frontmatter 缺 `summary`，触发 skill 优化。

## 最终状态

- **Status**：draft-created
- **appmsgid**：100001000
- **作者**：李玉恒（`.config/wechat.toml` default_author）
- **正文**：19401 chars，5 张插图
- **本地归档**：`.local-archive/2026-07-16-lanhua/`
- **剩余人工动作**：草稿箱设置封面 → 最终 review → 群发

## 好的部分

1. **Workflow 并行素材搜集非常高效**：8 路搜索 + 12 路 fetch 并行，~13 分钟拿到 20 个 agent 的整理结果，覆盖了原诗出处、民歌运动、翻唱版本、歌词差异、植物考据等所有关键事实点。《光明日报》《三联生活周刊》《澎湃》等权威源交叉验证。
2. **散文 register 拿捏到位**：SOUL.md 的 Literary Essay 指引让文章保持了克制、现场感、不鸡汤，金句"它是一朵没开的花，所以每个人都可以替它开一次"有收束感。
3. **插图用横版 16:9 新中式编辑插画比竖版水墨效果好很多**，微信公众号 mobile 阅读时图片不挤压正文节奏。
4. **wechat-publisher 流程稳定**：5 张正文图串行上传 CDN 全部成功，标题/作者/摘要写入并回读校验通过，保存草稿三重验证成功。

## 问题与改进

### 1. frontmatter `summary` 缺失（本次主要发现）

**现象**：draft 阶段 frontmatter 没有 `summary`，publisher 自动从首句截取"我从山中来，带着兰花草。…"作为摘要，虽然可用但不是作者确认的判断。
**根因**：三个 skill 之间存在契约断层：
- `article-ideation` 产出 writing brief 的 one-line idea，但没有要求同步到 frontmatter。
- `polish-article` 的结束前检查没有校验 frontmatter 完整性。
- `wechat-publish-workflow` 调用 publisher 前没有 pre-flight 检查，直接让 publisher fallback。

**改进**：
- ✅ 已改三个 skill（`polish-article` 加第 7 步 frontmatter 校验；`article-ideation` 加第 7 步 one-line idea → frontmatter；`wechat-publish-workflow` 加第 5 步 pre-flight）。
- ✅ 已沉淀 memory `frontmatter-fields-contract.md`。
- ✅ 当前文章的 frontmatter 已补 summary。

### 2. 竖版 vs 横版插图踩坑

**现象**：第一次按 3:4 竖版（默认 2K preset）生成，结果：
- 封面图左侧大面积空白失衡；
- 公众号正文里竖版图会把文字段落拉得很长，节奏断。

**教训**：微信公众号正文插图默认应该走 `--wide` 16:9，尤其是叙事型散文。竖版只适合封面或需要纵向构图的特定场景。下次 seedream 为微信生成插图，**默认横版**。

### 3. 预览服务器图片路径问题

**现象**：`wechat-article-renderer/scripts/preview-server.mjs` 只 serve 了单个 HTML 文件，没有 serve 同目录 assets，导致图片 404。
**临时解决**：改用 `python3 -m http.server` 在文章目录启动。
**未来改进**：可以给 preview-server.mjs 加一个 flag 或默认 serve 整个目录（不过这是 renderer 的小 bug，不阻塞本次流程）。

### 4. 封面必须手动设置

publisher 目前不会自动设置封面。frontmatter `cover:` 字段可触发 `--try-cover`，但本次没有提前指定。如果希望封面自动化，下次 draft 阶段在 frontmatter 里写 `cover: assets/hero-cover.png` 即可。

## Contrastive（对比上次同类任务）

1. **与上次微信公众号发布（Cloudflare/Vite 文）对比**：
   - 上次踩过"外链导致保存失败"的坑，本次 HTML 无外部 href（renderer 已处理），一次保存成功。
   - 上次流程没有系统搜素材，本次引入 Workflow 并行搜 + fetch，素材质量大幅提升。
   - 上次同样是 publisher 自动截摘要（没显式写 summary），这是**重复模式**，所以本次确认是 skill 契约问题而非偶发——已通过 frontmatter contract 修复。

2. **上次 closeout 标记的改进方向**：
   - "图片不双写，closeout 时统一归档"——本次遵守，assets 先在 `content/origin/` 工作副本，closeout 时统一移到 `.local-archive/`，没有双写。
   - "封面自动上传不稳定"——本次确认 `--try-cover` 在 frontmatter 有 cover 路径时可用，下次直接走这个路径即可。

3. **本次发现的新问题（本次独有）**：
   - Workflow 批量生成图片时 agent 直接下载 PNG，但没有保存每个图片的 `.json` metadata 到 origin assets。下次批量插图时应在 workflow 脚本里把 metadata 一并落盘，方便 prompt 追溯。
   - preview-server.mjs 静态目录 serve bug，属于 renderer 小缺陷。

## Skill Staleness Check

| 信号 | Skill | 处理 |
|---|---|---|
| frontmatter 契约在三个 skill 间断层 | polish-article / article-ideation / wechat-publish-workflow | ✅ 已修复 |
| preview-server.mjs 不 serve assets 目录 | wechat-article-renderer | ⚠️ 登记为待修；有 python http.server workaround，不阻塞 |

## 沉淀到项目的东西

- Skill 改动：`polish-article` / `article-ideation` / `wechat-publish-workflow` 三个 SKILL.md 已更新 frontmatter 契约。
- Memory：`frontmatter-fields-contract.md` 已写入 `~/.claude/projects/.../memory/`。
- 待修：wechat-article-renderer 的 preview-server.mjs 静态目录 serve 问题，已在复盘里登记。

## Git / Task

- canonical source 已在 `content/origin/2026-07-16-lanhua/`（含 Markdown + writing-brief.md）。
- 渠道产物在 `content/wechat/2026-07-16-lanhua/`（HTML + publish-status.md）。
- 本地归档在 `.local-archive/2026-07-16-lanhua/`（图片 + Markdown 快照 + manifest）。
- 图片 PNG 是 .gitignore 覆盖的二进制，不入 Git；Markdown / manifest / publish-status.md 是文本，tracked。
- 待用户 final review 后群发，群发后更新 `publish-status.md` 状态为 `published` 并补 URL。
