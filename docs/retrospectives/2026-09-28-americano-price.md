# 2026-09-27 《一杯美式引发的思考》写作与发布复盘

## Timeline

- 用户路过库迪，喝了杯 9.9 的美式，回来给了几段灵感碎片。
- `article-ideation`：定 thesis（星巴克卖的是"一个不需要解释的选择"，价格战消灭的是这笔确定性；9.9 也不是真实价格，是加盟商在替消费者付账），brief 落盘 `content/drafts/2026-09-27-americano-price/writing-brief.md`。
- 用户逐条打磨：标题、两个小标题（"成本"、"苦咖啡"）、Phil Burk 的身份写法、开头场景（改成"去家门口超市买菜，下午五点路过"）。
- 发现并修掉一处自造矛盾：开头写"不是为了喝咖啡"、结尾写"是因为我下午会困"——两句都是我编的，用户澄清是纯粹好奇，遂把结尾改成"好奇它到底有多苦"。
- `polish-article`：register 定为 literary-essay 主 + industry-analysis 次。删一处真冗余（第 6 节答案说了两遍）、修 3 处准确度、4 处 AI 味/网感、统一称呼（老先生/老爷子混用 6 处）、破折号 13→10。
- 配图：6 张静物/空间图基本 1–2 轮过；唯一的多人场景 `three-at-starbucks` **迭代 5 轮后被用户否掉**，撤出正文。
- `wechat-article-renderer --style warm-editorial` → 移动端 390px 校验通过 → `wechat-article-publisher` 建草稿，appmsgid=<见 .local-archive 发布态>，6 张图全部上传微信 CDN，`--try-cover` 成功。
- 用户群发。
- `erik-blog-publish-workflow` → 同步到 `eriklee-blog` → 构建 → 推 `main` → Cloudflare Pages 上线。
- 用户追问"最新几篇 blog 没有缩略图"，牵出同步脚本的 4 个缺陷，连带修了 10 篇旧文的重复封面、给 10 篇更早的文章补了封面、恢复了 3 篇丢失的源稿、修了一个从未跑过的 CI。

## 最终状态

- **Status**：published（微信 + 博客双渠道）
- **微信**：已群发。`appmsgid` 按 Publish Boundary 不写入 git，见 `.local-archive/2026-09-27-americano-price/publish-status.md`
- **博客 URL**：https://eriklee-blog.pages.dev/posts/2026-09-27-americano-price/
- **作者**：李玉恒（`.config/wechat.toml` default_author）
- **正文**：3037 中文字，6 张插图
- **本地归档**：`.local-archive/2026-09-27-americano-price/`
- **剩余人工动作**：无

## 好的部分

1. **个人经验与宏观结构同构**，这是这篇的骨架。用户 2018 年"学人精"点美式（为符号付钱）→ 2026 年为好奇买 9.9（为功能/兴趣付钱），正好是中国咖啡从身份消费到日常刚需的迁移。商业分析长在这个骨架上就不是行业报告。
2. **"为什么星巴克不能降价"是全文最硬的一击**。库迪只能打价格战是因为产品可复制；星巴克不能降价是因为"一降价它卖的那个东西就没了"。用户原文里"星巴克在中国更上档次"的直觉，落成了"三十块的星巴克是一个不需要解释的选择"。
3. **店员那句"一个更苦一点，价钱一样"做成了全文钥匙**，结尾回收成"美式从诞生第一天起就是一次稀释"。
4. **`--try-cover` 这次成功**（lanhua 那次没提前在 frontmatter 写 `cover:`）。封面自动化路径确认可用。
5. **信息图文字 13 处逐字核对全对**，gpt-image-2.5-sunburst 在中文数据标注上可靠。

## 问题与改进

### 1. 配图：写实多人场景迭代 5 轮仍被否（本次最大教训）

`three-at-starbucks.png` 要同时满足族裔、性别、年龄、姿态、气氛、道具六项约束。每轮只修好一两项，其余漂移：叙述者画成女性 → 改男性后 Phil 成亚洲面孔 → 修族裔+改中远景后姿态拘谨、纸杯错成热饮杯 → 改冰杯后人物背对镜头做不出"相谈甚欢" → 放开面部后构图仍不成立。用户最终撤下。

对比：同一批 6 张静物/空间图只有两三项约束，一两轮就过。

**改进**：已沉淀 memory `article-illustration-avoid-multi-person-scenes.md`。拟配图清单时先问"这张有没有具体人物"，超过三项约束就改构图或提前告知用户要多轮。

### 2. blog 同步脚本的 4 个缺陷（用户追问缩略图牵出）

| 缺陷 | 影响 |
| --- | --- |
| 只写 `ogImage`，从不写 `heroImage` | 博客列表缩略图和文章页 hero 读的是 `heroImage`，所以所有同步过去的文章列表上都是文字占位块 |
| `copytree` 前先 `rmtree` 目标目录 | 图片二进制被 gitignore，从 git 恢复的 origin assets 必然不全，一同步就把博客侧还在用的图删掉且无法恢复。**本次实测触发过一次**（hermes-bot 的 9 张图被删），已回滚 |
| `description` 取值链里没有 `summary` | 重新同步会把手工写好的摘要换成正文首段 |
| `<callout emoji>` 原生 HTML 不转换 | 博客没有该组件，MDX 当未知小写标签渲染成无样式元素 |

全部已修，详见 `scripts/sync_origin_to_blog.py` 的注释与 commit `aac5ea0`。

### 3. 三篇源稿只存在于未合并分支

`hermes-bot-architecture`、`jev`、`jev-system-one` 的 `index.md` 在 `claude/silly-wozniak-023f92` 和 `claude/eager-chebyshev-9c0c4c` 上，main 和当时分支的 `content/origin/` 下只剩 `assets/`，博客 mdx 的 `source:` 字段是死链。已恢复并验证重新同步零 diff。

**根因**：这些分支从没合并，但文章已经发布了。发布流程没有校验"源稿是否在当前分支上"。

### 4. CI 从来没跑过

`eriklee-blog` 的 `ci.yml` 只在 `pull_request` 时触发，而本次是它写出来之后的第一个 PR。一跑就死在 `actions/setup-node`：`pnpm-workspace.yaml` 缺 `packages` 字段（`pnpm store path` 会校验）+ workflow 钉的 pnpm 9 与仓库的 pnpm 12 工具链不匹配。已修，见 PR #1。

### 5. 微信发布态写进了 git（用户裁决）

记忆 `wechat-appmsgid-not-in-git` 记的是"appmsgid 不进 git"，但发布器把 `publish-status.md` 写进了 git 跟踪的 `content/wechat/`，重发快照的文件名里也带 appmsgid。用户裁决：**记忆对，skill 不合理**。已把发布态读写都挪到 `.local-archive/`，`.gitignore` 补两条防御网，AGENTS.md 的 Publish Boundary 记下这条边界。

## Contrastive（对比上次同类任务）

对比对象：`2026-07-16-lanhua-essay.md`（上一次散文类写作发布，同一套 skill 链）。

1. **上次标记的改进方向，这次验证情况**：
   - "图片不双写，closeout 时统一归档到 `.local-archive/`"——**本次遵守**，生成期只在 `content/origin/.../assets/` 留一份，closeout 时才归档。
   - "封面自动上传不稳定，下次 draft 阶段在 frontmatter 写 `cover:` 走 `--try-cover`"——**本次验证成立**，`--try-cover` 一次成功（cover-set）。
   - "批量生图时要保存每张图的 `.json` metadata"——**本次已由 gpt-image-api CLI 自动完成**，每张图都有同名 `.json`，无需手工。
   - "`preview-server.mjs` 不 serve assets 目录，登记为待修"——**本次已不是问题**，该脚本现在接受 ROOT 参数并 serve 整个目录。

2. **重复模式识别**：
   - **"skill 契约与实际行为不一致"是重复模式**。lanhua 那次是 frontmatter `summary` 在三个 skill 间断层；这次是 `wechat-appmsgid-not-in-git` 边界在记忆和 skill 之间冲突，加上 closeout/publish skill 都写"publish-status.md 在 content/wechat/"。**两次都是"某个约定只存在于一方"**。→ 已写入本节，建议后续 closeout 都做一次"记忆 vs skill"一致性扫描。
   - **"发布流程不校验前置状态"也是重复模式**。lanhua 那次是 publisher 不检查 summary 就 fallback 截首句；这次是发布不校验源稿是否在当前分支。→ 已在 `wechat-publish-workflow` 有 pre-flight，但 **blog 流程没有对应的源稿存在性校验**，登记为待改进。

3. **本次独有**：
   - 多人场景配图的脆弱性（前几次散文都是静物/风景图，没暴露）。
   - 一个只在 `pull_request` 触发的 CI，因此长期处于"写了但没跑过"的状态。

## Skill Staleness Check

| 信号 | Skill | 处理 |
| --- | --- | --- |
| 步骤 3 要求校验 `content/wechat/.../publish-status.md`，但该文件按新边界已移到 `.local-archive/` | `writing-task-closeout` | ⚠️ 本次已修 SKILL.md |
| 步骤 3 同上 | `wechat-publish-workflow` | ✅ 本次会话已修（发布态边界那次） |
| 归档章节说"移动图片"，步骤 5 说"移动**或确认**" | `writing-task-closeout` | ⚠️ 措辞歧义，本次按"移动"执行（与 lanhua 一致）；登记 |
| blog 流程无"源稿是否在当前分支"校验 | `erik-blog-publish-workflow` | ⚠️ 登记为待改进，未修 |

## 沉淀到项目的东西

- **Code**：`scripts/sync_origin_to_blog.py` 四个缺陷修复 + 破坏性 rmtree 防护。
- **Code**：`publish.py` 发布态移出 git（`status_dir_for()`）。
- **Docs**：`AGENTS.md` Publish Boundary 增加"发布态信息不进 git"。
- **Skill**：`wechat-publish-workflow` 4 处文档改口径；`writing-task-closeout` 修正 publish-status.md 位置。
- **Memory**：`article-illustration-avoid-multi-person-scenes.md`（新）、`blog-sync-old-articles-are-not-resyncable.md`（新）、`title-prefer-plain-descriptive.md`（补 register 边界）。
- **Blog**：10 篇旧文补封面、10 篇去重复封面、3 篇补 heroImage、CI 修复。

## Git / Task

- **canonical source**：`content/origin/2026-09-27-americano-price/`（index.md + writing-brief.md + assets manifest）。
- **渠道产物**：`content/wechat/2026-09-27-americano-price/index.wechat-preview.html`。
- **发布态**：`.local-archive/2026-09-27-americano-price/publish-status.md`（gitignored）。
- **本机归档**：`.local-archive/2026-09-27-americano-price/`（index.md 快照 + images/ + prompts/ + archive-manifest.md）。
- **harness 仓库**：4 个提交在 `claude/musing-agnesi-528f40`，**未推送**。
- **eriklee-blog**：已推 `main` 并部署，工作区干净，PR #1 已合并、分支已删。
