# 麒麟大口茶：一篇商业模式文章的多渠道交付复盘

- **Date:** 2026-10-26
- **Article:** 只卖一种茶的茶饮店，凭什么活了九年
- **Channels:** blog (Astro / Cloudflare Pages), WeChat Official Account
- **Blog:** https://eriklee-blog.pages.dev/posts/2026-10-25-qilin-dakoucha/
- **WeChat:** published; appmsgid 与公开链接见 `.local-archive/2026-10-25-qilin-dakoucha/publish-status.md`

## What Shipped

- 5,200 字左右的商业模式分析，从“只卖一种茶”进入，讨论低盈亏平衡点、复制与长期条件。
- 8 张同一套 risograph 编辑插画：封面、菜单折叠、深夜小店、彩票罐、前后台、印章复制、冬季/仿店走绳、18 元价签。
- 2 个 HTML 图：2017–2026 时间线、一个味道三层价格。
- Blog 用交互 iframe；WeChat 用 390px 移动宽度渲染的静态图。
- Blog PR #4 squash merge；WeChat 草稿保存后由用户发布。

## What Worked

- **先 ideation、再 research、再写**：把“拆账本/查风险”从主题降级为证据，文章才有“这家店凭什么活”的叙事。
- **对抗式审稿**：四路 review 抓出了两个硬错误（店型写小、昆明“喜茶对面”是把创业假想写成真实选址）和多处口径误读。事实台账回写后，二次引用没有再漂。
- **统一插画风格**：一张 style block 贯穿 8 张图；封面先出样张，确认后再 batch，避免整套返工。
- **HTML 图分工**：时间线和价格卡在 blog 保留交互；WeChat 渲染成静态图，避免 iframe 和微信编辑器不兼容。
- **publisher 流程稳定**：10 张正文图串行上传到 `mmbiz.qpic.cn`，封面 `cover-set`，标题回读校验通过，草稿保存成功。

## What Broke / Lessons

1. **HTML 图不能直接按桌面宽度转成微信图片。** 1600px 宽的时间线/SKU 卡在 366px 手机上字会小到不可读。正确做法是按 **390px CSS 宽度 + DPR 2** 渲染，输出 780px 宽的图；这样手机端有效字号约 12px。这个规则值得进 renderer 或发布 checklist。
2. **Blog sync adapter 会丢掉 `<!-- EMBED -->` 注释。** `sync_origin_to_blog.py` 的 `escape_mdx_text` 对 HTML 注释执行 `continue`，注释不会进入生成的 MDX；iframe 需要手动补。当前没有自动把 embed 复制到 `public/embeds/` 并替换成 iframe 的步骤。
3. **插画细节要和文章事实对齐。** 文章写“不用吸管”，首版两张杯子图却画了吸管；已重生成。以后有强品牌动作的细节，prompt 里要显式写 no straw。
4. **图片 batch 会偶发连接失败。** 4 张 batch 里有 1 张 `APIConnectionError`，单独重跑即可；不要让 batch 的失败拖住其余 3 张。
5. **微信端的“摘要”打印会被截断显示，但实际写入是完整 48 字。** 以保存后回读和 `publish-status.md` 为准，不以终端截断为准。
6. **公众号作者来自 `.config/wechat.toml`，不是 frontmatter。** 本次作者为李玉恒；从主 checkout 复制配置后 publisher 直接读取。

## Contrastive

- 与之前的 CopilotKit / Codex 文章相比，这篇第一次同时交付 blog + WeChat，并第一次把 HTML 图分成“blog 交互 + 微信静态”两套。
- 上次同类任务的主要风险是事实漂移；这次审稿再次证明“总结环节是研究错误的高发点”，尤其是把创业假想写成门店选址。
- 上次沉淀的“先出样张、再批量”这次继续有效；新增的是“移动宽度重渲染”和“插画事实对齐”两条。

## Skill Staleness

⚠️ **技能腐化风险**

- `erik-blog-publish-workflow`：同步脚本丢弃 `<!-- EMBED -->` 注释，也不复制 HTML 到 `public/embeds/`；本次只能手动插入 iframe。建议在 adapter 中增加 embed 后处理。
- `wechat-article-renderer`：没有原生 HTML block/iframe 处理；本次只能手动截图并替换为图片。建议增加“HTML embed → 390px/DPR2 静态图”的预处理步骤，或至少在 checklist 中写明。

本地 staleness 记录见 `.local-memory/skill-staleness-erik-blog-publish-workflow.md` 和 `.local-memory/skill-staleness-wechat-article-renderer.md`。

## Follow-ups

- 回填公众号公开 URL 到 `.local-archive/2026-10-25-qilin-dakoucha/publish-status.md`。
- 考虑给 blog sync adapter 加 embed 自动处理；给 WeChat renderer 加 HTML block 静态化 helper。
- WeChat 渠道稿与 preview 已准备进 `content/wechat/2026-10-25-qilin-dakoucha/`；图片二进制按仓库规则不入 git。
