# SpaceX 豪购 Cursor：研究、视觉与博客发布复盘

日期：2026-10-26。源稿：[SpaceX–Cursor](../../content/origin/2026-10-26-spacex-cursor-stock-deal/index.md)。

## 最终状态

- [博客文章](https://eriklee-blog.pages.dev/posts/2026-10-26-spacex-cursor-stock-deal/)已在用户最终确认后发布，生产提交 `8e39d10`；[商业洞察](https://eriklee-blog.pages.dev/categories/business-insights/)分类同时上线。
- 文章同时属于 `AI Frontier / AI 前沿` 与 `Business Insights / 商业洞察`；麒麟大口茶移入商业洞察。全部文章列表不重复计数。
- 线上标题、历史案例、封面 v2、结尾图与 3 个交互 HTML 已核验。部署初期 404 与临时 TLS 错误没有直接判定为发布失败，等待部署并按重定向复核后通过。
- 本机归档：`.local-archive/2026-10-26-spacex-cursor-stock-deal/`。9 张最终图片移入归档，origin 保留相对软链接；prompt 保留在 provenance，metadata 与发布状态进入本机归档。

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

## ⚠️ 技能腐化风险与处置

- `erik-blog-publish-workflow`：需补 `Business Insights -> 商业洞察`、额外 `categories` 以及“不要用 series 代替多分类”的规则。记录于 `.local-memory/skill-staleness-erik-blog-publish-workflow.md`，未在 worktree 中直接修改外部共享 skill。
- 没有新建 skill，没有修改 SOUL。多分类能力已经由代码和测试落地，不把文档待更新误写成功能缺失。

## Git / Handoff

- 博客提交已推送 `main`；原有 `.claude/` 与旧封面没有进入提交。
- 写作仓库只提交 canonical、HTML、prompt、manifest、同步器、测试与本复盘；本机 `.local-archive/`、`.local-memory/`、图片二进制和发布状态不提交。
- 博客公开内容已完成，无剩余发布动作。后续若在共享 skill 中补多分类说明，属于独立维护工作。
