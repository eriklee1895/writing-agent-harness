# Cloud Agent Runtime 写作与分发复盘

日期：2026-09-29。文章：[从 Muse 到 Manus，为什么 Agent 开始需要一台自己的电脑？](../../content/origin/2026-09-29-cloud-agent-runtime/index.md)。

## 交付状态

- Blog 已发布：[线上文章](https://eriklee-blog.pages.dev/posts/2026-09-29-cloud-agent-runtime/)，提交 `02c6fce0fee255dcee39928d9a5f4c62d7138a57`。Cloudflare Pages 部署成功；线上正文、5 图、表格、RSS 与搜索已经验证。
- 微信草稿 `100001416` 已由用户检查，状态保持 `draft-created`，未执行发表或群发。原始提交文件保留在 `content/wechat/2026-09-29-cloud-agent-runtime/index.wechat-preview.html`。
- [飞书文档](https://bytedance.my.larkoffice.com/docx/YNHsddyDYoCBKUxQwOMmsCZrykh) 已转写，回读 revision 16：102 个 block、7 节正文、5 图、2 张原生表格、17 链接，58 个非表格文本 block 核对完整。
- 最终稿和 6 张使用中的图片（5 张正文图及封面）归档至 `.local-archive/2026-09-29-cloud-agent-runtime/`。原 assets 路径改为相对软链接，文章图片引用不变。博客仓库部署资产保留。
- canonical frontmatter 的 `status: draft` 沿用原稿状态；实际交付状态以三份渠道 `publish-status.md` 为准，不能据此推断微信已发表。

## 写作与证据

本篇从用户对云电脑与 Sandbox 的直觉比较，收敛为三个相互独立的维度：产品提供的工作环境、隔离机制、运行寿命。保留用户对登录态与连续工作的关切，同时补充文件、授权、执行现场和任务进度的区别。microVM 的启动指标不直接等于浏览器、依赖与业务准备完成的端到端延迟。

用户要求多搜索入口后，Firecrawl、Tavily 与内置 Web 互补召回，再回到一手材料核对。Cloudflare Computer 成为“共享工作区、不同执行后端”的具体案例。多个搜索引擎命中同一页面不算多份独立证据。代表性产品用于说明架构选择，不扩展成产品清单。

## 视觉与渠道适配

用户先后指出插图不足、表格列宽不合适、品牌元素缺失。最终形成开篇、状态连续性、隔离分层、Cloudflare 实现、结尾五个插图位置，另有横幅封面。品牌场景以官方 Manus/Muse 资产为参考；通用技术图保留清晰的层次和文字。Cloudflare 图基于官方图意重绘并注明来源。

首版技术图背景和文字对比度不足，修订为不透明 RGB；生成图中文字逐项核对。用户要求删除的“（概念插图）”图注后缀保持删除。精修保留 16 个来源链接、5 图和两张表格，主要压缩重复解释。

微信两张表分别采用 20/40/40 与 20/32/48 列宽，由文章专属 `render-preview.mjs` 固化；不把该能力误报为通用 renderer 已支持配置。博客转换成现有 Astro `ArticleTable`，用本篇局部样式防止 `microVM` 首列标签折行。飞书转为原生可编辑表格，宽度为 164/328/328 与 164/262/394。

微信 publisher 返回 5/5 图片上传后，仍重新打开已保存草稿检查实际显示尺寸、CDN 加载、表格和结尾。日志中的“窗口保留打开”不保证退出后仍有可操控的编辑窗口；本次通过已有专用会话重新进入草稿完成复核。未将临时预览凭据或飞书登录重定向链接写入归档。

## Contrastive

1. **与上次同类任务有什么不同？** 对照 [Starship Flight 14](2026-09-29-starship-flight14-closeout.md)，本篇是技术概念比较，没有双栏图片上传故障，但同样需要文章专属表格比例和真实渠道回读。对照 [Meta Muse](2026-09-13-meta-muse-writing-closeout.md)，品牌参考应在首轮配图准备阶段纳入，避免用户再次指出缺少 logo。
2. **上次标记的改进是否验证？** 本次沿用相对软链接维持 canonical 图片路径，并归档原始微信提交 HTML，避免移动图片后文章失效。博客同步文档已有能力边界说明，但脚本仍需显式传入 summary 对应的 description、筛选使用资产、人工适配渠道表格；尚未验证自动适配已实现。
3. **哪些问题重复出现？** 品牌参考晚介入、表格缺少按篇列宽配置、博客渠道语法适配、保存草稿与可继续操作窗口之间的断层，均需在已有 skill 范围内处理。任务索引已有多次“归档后保持原图片路径”和“技术图需要文字标签”，不应再建同功能 skill；继续加强现有 skill 的检查与参数接口。

## Skill Staleness

⚠️ 技能腐化风险：已追加本机 staleness 记录，未把临时 workaround 写成已落地的通用能力。

- `wechat-article-renderer`：本篇列宽依赖局部 wrapper；建议通用接口支持按表配置列宽，并验证短标签换行。
- `erik-blog-publish-workflow`：summary、资产筛选和渠道专用表格仍需人工桥接，Starship 中相同缺口再次出现。
- `wechat-article-publisher`：进程完成日志与后续浏览器控制状态需要分别验证；交付 appmsgid 和可重复打开草稿的路径。
- `markdown-article-to-feishu-doc`：当前 CLI 1.0.88 命令帮助与旧例子的 `--api-version v2`、文件路径约定有差异。本次按实际帮助使用相对路径，写入成功且回读验证；应单独修订并验证 skill 示例，不能直接推断所有版本相同。

本次只新增本篇复盘、任务索引与局部风险记录；共享 skill 和工程配置已有其他任务改动，保持原样。没有新的长期作者风格规则需要写入 SOUL，也不需要新建 skill。

## Git 与后续

写作仓库未暂存或提交本次收尾文件，其他任务改动保留。博客发布提交独立存在，不随本机归档修改。用户若决定在公众号正式发表，需要执行单独的发表动作并回填永久链接；该动作不影响本次归档完成。
