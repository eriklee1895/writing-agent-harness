# Codex Cloud Environment 学习笔记：写作与分发复盘

日期：2026-10-15。正式稿：[Codex 云端环境学习体验：把开发带离办公桌](../../content/origin/2026-10-15-codex-cloud-environments/index.md)。

## 交付与证据

- Blog 已发布：[线上文章](https://eriklee-blog.pages.dev/posts/2026-10-15-codex-cloud-environments/)。博客提交 `a727fbb` 已在 main / origin/main，Cloudflare Pages 成功；文章、技术封面和 Open Graph 元数据已通过真实浏览器检查。
- 公众号为 `handoff-only`：[渠道稿与 HTML](../../content/wechat/2026-10-15-codex-cloud-environments/index.md) 已交付，未创建微信账号草稿、未发表或群发。八节内容、四张表的 33 个 data cells、Shell 示例完整保留；九张正文图、七个官方来源页面，390px / 430px 本地检查通过。
- 图片与最终文章快照归档至 `.local-archive/2026-10-15-codex-cloud-environments/`。渠道状态和核验截图只在本机归档；账号态不进 Git。
- 其他任务写入 research-notes.md 的飞书交付记录保持原样。本次未重新核验飞书远端，也未把该并行改动计入收尾修改。

## 写作中值得保留的判断

用户的使用价值是从手机和 dot 交代工作、让 Cloud Task 继续开发。叙事先说明这个 workflow，再分清 Repository、Environment 与 Task，随后展开 provisioning、credential delivery、request path、VM isolation 和公司网络边界。技术 nouns 尽量沿用英文。

对 dot 的 handoff，按用户确认写成目标与 context 交给另一个 Cloud Task、再协调结果，没有误写成同一 chat 与 Git state 的云端迁移。Secrets 则按 ownership 与 delivery 两个维度解释；VM 的适用性属于工程分析，hypervisor、snapshot 格式与 Harness 部署位置保持未知边界。共享聊天可提供问题线索，产品事实仍回到当日官方文档。

四张官方 UI 图来自文档原始 HTML/CSS figure 的浏览器截图，保留来源、尺寸与哈希；它们是官方示意图，不是用户账号截图。概念 SVG 与生成式封面分别记录 provenance。

## 视觉修订

第一张封面虽然有手机和云，但办公室、晨光与自然景色主导画面，用户指出“没有技术插图的感觉”。用户明确要求 ChatGPT Logo 与 Codex Cloud Environment 后，改用内置 imagegen：手机上的 Logo → Task handoff → 云端 Environment → 三个独立 Task VM。用户明确评价“这个图 perfect”“这才是技术文章应该有的风格”。

一次定向修订移除了被错误置于手机任务入口上的 Credential Proxy，以免技术封面混淆 handoff 与 secret delivery。图片生成能力不能替代关系检查；封面同样需要与正文中的职责边界一致。内置工具未返回 backend model identity，因此没有把用户提及的 GPT Image 2.5 写成已验证调用型号。

公众号正文继续使用获认可的封面，另将背景横向延展为 1920×819 的头条封面（约 2.35:1），避免裁掉 Logo、标题或 VM base。四张技术图改为窄画布、竖向布局和大字标签，保留 SVG source，再转换为可上传的 PNG。没有把生成式模型用于重画有精确关系的正文 diagram。

## 渠道适配与验证边界

公众号用 warm-editorial。四张三列表格变为逐项说明，逐 cell 核对内容；配置请求模板改成自动换行的引用，Shell code 保持逐字一致。外部 source links 改为编号与七条可复制的官方地址，HTML 不保留 href。

本地检查覆盖所有 data-local-path、九图加载、390px / 430px 页面宽度、关键图与代码块；这些结果只证明本地预览。没有执行 publisher，因此无法据此声称微信 editor sanitation、CDN upload 或草稿封面设置已通过。

博客首次核验新资源时出现较慢的图片加载和一次 HTTP/2 connection 错误；后续观察到对应 WebP HTTP 200 且实际显示。以部署成功、HTTP 响应、页面可见三个信号分别判断，避免刚刷新时的空图被直接当成构建错误。

## Contrastive

1. **与上次同类任务的不同。** 对照 [Cloud Agent Runtime](2026-09-29-cloud-agent-runtime-closeout.md)，本篇聚焦一个产品的实际配置与 credential mechanism，采用官方 UI + 精确概念图；微信只交付本地预览，上次的真实草稿回读不能移用到本次。对照 [塞罕坝](2026-10-06-saihanba-forest-road-closeout.md)，本篇包含 Mermaid、代码和长英文表格，散文交付成功不足以证明这些形状自动兼容。
2. **上次改进是否验证。** 继续采用“归档媒体 + 原路径相对软链接 + 哈希/加载检查”，本次十张实际使用的位图执行并验证。博客 adapter 已正确同步 summary、heroImage / ogImage 以及实际引用资产，本次 diff 和构建有证据；没有 `::compare`，不据此宣称该转换缺口已修。公众号未跑 publisher，长标题、登录窗口及真实草稿表格问题均未验证。
3. **重复出现的问题。** 品牌标识晚介入在 Cloud Agent Runtime 复盘中已出现，本次再度由用户纠正，因此把“先确认产品标识、组件、关系”补入现有 article-illustration。旧配图 CLI routing 与用户指定工具冲突在 Starship、塞罕坝、本篇均有信号；按当前 AGENTS.md 明确 Skill 负责 brief/provenance，live generation 服从用户选型，无需新增 Skill。长英文表格的移动端问题再次出现，本次采用逐项说明，并未虚称通用 renderer 获得按表自动重排能力。

## Skill Staleness 与沉淀

⚠️ 技能腐化风险：article-illustration 仍包含旧模型 CLI 默认路径与自动裁切说明；公众号默认风格在 runbook、format reference、style reference 之间不一致。已记录两份本机 staleness 文件，并修正文档 routing、默认风格与 plain-text URL 规则；未修改或宣称验证旧 CLI 的当前 provider 兼容性。

SOUL.md 新增已获作者明确认可的技术配图审美，强调产品辨识、英文标签、组件关系与清爽层次；不把一张图的 palette 固化成所有文章的唯一画风。任务索引记录 Blog published / WeChat handoff-only。未新建 Skill，未修改全局 memory 系统。

后续 GitHub 入库时，同日 main 已新增公众号白底/透明容器要求与用户生图选型规则。整合时保留上游规范，runbook 和 format reference 对齐最新交付要求；本篇已交付 HTML 保留其生成时的 warm-editorial 样式，不在入库阶段重渲染。本文对本次预览样式的记录属于历史证据。

## Git 与后续

文章、封面 provenance 与公众号版本已在文章分支提交，公众号版本提交为 `4922d5e`。用户随后授权将 closeout 复盘、规范修订及 archive hints 一并提交 GitHub，并通过文章分支 PR 审核。博客部署资产不随写作仓库归档移动；博客的 `.claude/` 和本仓库的其他未提交内容保持原样。

后续若继续公众号分发，从现有 HTML 和头条封面同步草稿箱，再在真实 editor 中检查图片、代码与封面；最终发表按用户审核决定。换机需要同步本机归档或按 manifest 恢复二进制素材，Git 中的文本与 SVG 不能自动还原生成式封面。
