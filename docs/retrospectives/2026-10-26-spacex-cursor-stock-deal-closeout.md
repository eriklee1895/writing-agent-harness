# SpaceX 豪购 Cursor：研究、视觉与博客发布复盘

日期：2026-10-26。源稿：[SpaceX–Cursor](../../content/origin/2026-10-26-spacex-cursor-stock-deal/index.md)。

## 最终状态

- [博客文章](https://eriklee-blog.pages.dev/posts/2026-10-26-spacex-cursor-stock-deal/)已发布；初始生产提交 `8e39d10`，首页 regenerate 最终提交 `e769de9`。[商业洞察](https://eriklee-blog.pages.dev/categories/business-insights/)分类同时上线，用户确认首页效果满意。
- 微信公众号的最新原生短卡片版本已于 2026-10-27 由用户在后台手工发布。未提供公众号公开 URL，不虚构；早期长图草稿保留，未删除或重复发布。
- 文章同时属于 `AI Frontier / AI 前沿` 与 `Business Insights / 商业洞察`；麒麟大口茶移入商业洞察。全部文章列表不重复计数。
- 线上标题、历史案例、封面、结尾图与交互 HTML 已核验。部署初期 404 与临时 TLS 错误没有直接判定为发布失败，等待部署并按重定向复核后通过。
- 本机归档：`.local-archive/2026-10-26-spacex-cursor-stock-deal/`。最终 Cover family 以相对软链接恢复；`wechat/` 保存正式渠道 HTML、渠道源稿和原生图解生成脚本，长截图仅保留为 QA 证据。

## 写作与事实边界

最终主线是“估值、流动性与风险重新分配”，不是“马斯克零成本收购”或“二级市场单独买单”。SEC 文件纠正了 6 月高点锁定换股、全部股东共用锁定期、基础 IPO 发行规模和 100GW 发射量估算等过强或错误口径。

第三章采用 Shleifer / Vishny 与 Eckbo / Makaew / Thorburn 两种解释，并加入 Google–YouTube 与 AOL–Time Warner 两个短案例。前者说明股票支付与临近交割的平均价格窗口，后者提示估值和整合风险；没有采用聊天材料中未核实的估值倍数和溢价数字。

标题最终来自用户正面样例：`回望SpaceX豪购Cursor：600 亿美元的资本大戏`。600 亿是硬约束，“豪购”替代“壕购”是最终文字选择。封面改为金额前置的同一组信息，但 Blog 保留事件前置，避免同序复读。8 个 H2 的数字序号全部移除。

## 视觉与交互

- 封面及 7 张章节信息图使用用户指定的 `gpt-image-2.5-sunburst`；ch02 / ch08 的 xAI Logo 通过局部编辑修正，封面 v2 只替换顶部标题与副标题。
- 结尾新增 1728×736 无字宽幅 Starship 想象图，和前文的金融信息图形成节奏差异。alt 明示“艺术性想象图”，不把轨道算力写成已建成能力。
- 时间线、股东流动性和全链条 HTML 均为自包含资源，支持键盘、亮暗主题和移动端。实际 Blog iframe 验证自动撑高、模式切换和表格内部横滑。
- 第 8 章 alt 曾虚列图里没有的 Starlink，已改为实际节点。图片本身没有因此返工；1.7GW 的“装机功率”口径仍主要由正文和 HTML 解释。

## 多分类实现

现有 `category` 与 `series` 都是单值。没有用 `series` 伪装专栏，也没有把专栏降级为 tag：Blog 新增可选 `categories` 作为额外分类，主分类始终保留并去重。分类页、sidebar、文章 kicker 和同步器均读取该契约。

同步器最初把 `yaml_list()` 的返回值作为一个列表项嵌入 frontmatter，触发 `TypeError`。改为条件展开 YAML 行后恢复；回归测试覆盖有／无额外分类两种情况。博客新增 `check:categories`，验证 SpaceX 双分类、麒麟迁移和全部文章卡片不重复。

## Contrastive

1. **与上次同类任务的不同**：对照 [CopilotKit](2026-10-15-copilotkit-ag-ui-closeout.md)，本次不是修正单篇 taxonomy 误判，而是出现真实的多分类需求，因此把能力下沉到 schema、聚合、导航和同步器，并加入自动检查。对照[星舰第14次试飞](2026-09-29-starship-flight14-closeout.md)，用户再次通过正面标题样例纠正代理的过度朴素／过度工程化倾向；“星辰大海”类壮阔视觉也不能被信息图规则完全取代。
2. **上次改进是否验证**：`summary`、引用图片筛选和明确 taxonomy 继续有效；归档相对软链接、哈希与公开博客独立副本再次验证。Cloudflare 部署后复查沿用 CopilotKit 的经验，没有把首轮 404 或一次网络错误写成站点故障。图片 metadata、prompt 和 manifest 已分离保存。
3. **重复问题如何处理**：标题偏好再次出现“先给多轮代理候选，最后由用户正面样例定调”的模式。本次不修改 SOUL，但补充已有标题 memory 的 register 边界。Blog skill 的单分类说明与实际需求不匹配，登记 staleness；同步器和 Blog 代码则已完成真实修复，而非只记待办。
4. **跨渠道验收的不同**：初次 derive-first 曾把 pad 通过当作成本与一致性收益，用户后续用同尺寸对比证明 regenerate 更好；长截图也在真实手机阅读中被否定，最终改成原生短卡片。可复用结论是：文件完整、生成成功和成本更低都不等于阅读效果更好。Cover 要追求最佳视觉，交互 HTML 要按渠道重组内容，而不是把同一份资产机械复用。

## ⚠️ 技能腐化风险与处置

- `erik-blog-publish-workflow`：多分类与 `homeCover` 文档缺口已修复，`skill-staleness-erik-blog-publish-workflow.md` 标记 resolved。分类、首页检查及同步器均有真实代码与测试，不是只记待办。
- `wechat-article-renderer`：frontmatter-only 文章会输出“未命名文章”，iframe 会退化为转义源码；preview 的 origin 相对路径也需要正确的 content root。记录在 `skill-staleness-wechat-article-renderer.md`，本次用渠道 H1、静态/原生替换和 content-root 预览解决。
- `wechat-article-publisher`：非交互缺作者会保存空署名，Draft History 中的既有 ID 也没有形成可靠复用。记录在 `skill-staleness-wechat-article-publisher.md`。本次显式补 `Erik Lee`，保留两个历史草稿，没有自动删除或宣称覆盖成功。
- 没有新建通用 skill，没有修改 SOUL。原生移动卡片目前只验证于本篇文章；若同类交互图跨渠道需求重复出现，再抽成共享 builder，而不是过早制度化。

## Git / Handoff

- Blog 初始发布提交 `8e39d10`，首页 regenerate 最终提交 `e769de9`，均已推送 `main` 并完成线上核验；原有 `.claude/` 与旧 `hero-cover.png` 未进入提交。
- 写作仓库 canonical、prompt、manifest、同步器、测试和流程文档已提交到 `8a42087`；本机 `.local-archive/`、`.local-memory/`、图片二进制与发布状态不提交。
- 最终微信 `article.md` / `index.wechat-preview.html`、视觉方案和本复盘的新增收尾修改保留在工作区，未按用户要求执行新的 commit。若后续需要提交，应只选择这些已验收文件，排除未生成的 `home-cover-wide-v2.txt` 和本机文件。
- Blog 与微信公众号发布均已完成，无剩余发布动作。后续仅保留 renderer / publisher 的独立维护项。

## 首页推荐修复

用户发现首页左侧仍是 Claude Duet。根因不是部署缓存，而是两篇 `pubDatetime` 均为 `2026-10-26T00:00:00Z`，且均无 `featured`，首页回退到排序后的第一篇。采用显式编辑推荐而非伪造时间：SpaceX 设置 `featured: true`，同步器增加字段透传与默认省略测试，12 项测试通过。

博客修复提交 `5c7aeb1` 已推送 `main`。本地构建与页面确认 SpaceX 左侧推荐、Claude Duet 右侧最新文章；Cloudflare 多次 200 响应确认新 lead，用户线上截图再次验证。推送前的 GitHub 连接超时通过保留本地提交、网络恢复后重试解决，没有改 remote 或凭据。

## Cover 必备与派生流程落地

用户随后明确：Cover 是每篇文章的必备交付物，Blog 与微信公众号应共享母版和派生流程，但不要求每篇独立 AI 生图。最终规则是“一个视觉母版 + 按渠道确定性派生；crop/pad 先验收，不合适再用原 Prompt、目标比例与失败原因重新生成”。通用模板与系列 Cover 同样是正式路径，不建立 CMS 或批量返工旧文。

新增 `article-illustration/scripts/prepare_cover.py`：支持 focal crop、contain/pad、目标尺寸、背景、输出保护、manifest lineage 和 JSON。输出只能是 candidate / visual_review pending；重新派生会重置旧验收状态。输出软链接一律拒绝，避免覆盖 closeout 归档。27 项 prepare/sync 回归测试通过。

`article-readiness-check`、Blog / 微信 workflow 和 closeout 已接入 Cover 必备、显式绝对 `--cover`、保存重开后的视觉验收、Cover family 去重归档等规则。微信专用派生图不会进入 Blog 引用资产集合。首页检查改为读取文章实际 `homeCover` / `heroImage`，并按无扩展名的资产标识兼容 Astro WebP，不再写死未生成的 v2 文件名；完整 Blog build、图片、分类和首页检查通过。

SpaceX 微信试点先用 center crop 建立基线，在 1080×460、900×383、360×153 下均切掉主标题/底部标签，直接拒绝；pad 保留完整构图，先通过基线验收。随后应用户要求，以原 Prompt、标题修正和具体失败原因生成原生 2.35:1 版本，并与 pad 同尺寸对照。原生版的主标题、股票关系和三项标签在小卡上更有视觉重心，用户最终选择 regenerate，pad 降为备选。规范因此从“低成本派生优先”修正为“实际效果优先”：crop/pad 只作快速基线，原生再生是常规优化路径，不为少一次模型调用接受较弱结果。QA、Prompt、metadata 和最终图片均已归档；未创建新微信草稿。随后 regenerate 同时接入首页 `homeCover`，首次桌面低裁会切掉顶部标题，因此首页统一改为原生 2.35:1 完整显示，不再对信息型 Cover 做桌面低裁；桌面、390px、亮暗主题及完整 Blog build 均通过，文章 hero 未变。首页 regenerate 随提交 `e769de9` 发布，用户确认满意。

## 微信公众号原生排版改造

首次微信派生曾把三个交互 HTML 做成 5 张移动端长截图，虽然信息完整，但用户指出长图在手机阅读体验不好。最终没有以“信息不丢失”为理由保留截图，而是把内容重新设计成微信原生短卡片：六节点时间线、价格与身份卡、当前/规划/验收三个全链条分区。`content/wechat/.../index.wechat-preview.html` 使用白底 agent-flow，390px 无横向溢出，正文回到 8 张原图。

最新原生排版版本已由用户在微信公众号后台手工发布：作者 Erik Lee、regenerate 封面、8/8 正文 CDN 图片，保存回读通过。早前长图草稿仍保留，未擅自删除；公开 URL 未提供，不重复执行发布。
