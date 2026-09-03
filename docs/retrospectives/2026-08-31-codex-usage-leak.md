# 2026-08-31 Codex Usage Leak 写作任务收尾

## Final State

- Status: `draft-created`，微信公众号尚未正式发布。
- Canonical: `content/origin/2026-08-30-codex-usage-leak/index.md`。
- Blog channel: `content/blog/ai-agents/2026-08-30-codex-usage-leak/article.md`，未同步到个人 Blog repo，未发布。
- WeChat draft: `appmsgid=100001211`；标题、作者、摘要、封面和 11 张正文图已写入草稿。
- Feishu docx: [Tibo 再次“赛博回血”](https://bytedance.my.larkoffice.com/docx/YkwYdF4ecoI50zxYPPkmyaqWyCc)，revision 18。
- Local archive: `.local-archive/2026-08-30-codex-usage-leak/`。

## What Worked

1. 文章没有停留在“额度重置新闻”，而是把 Tibo 的八项说明映射为 Compaction、Memory、Goals、Automations、Subagents、Computer History、Rolling summaries 和 MCP 八类 Agent runtime 问题，并明确区分源码确认、相邻实现、工程推断与未开源边界。
2. Codex 源码分析与 focused tests 形成了可复核证据链。使用仓库标准 `RUST_MIN_STACK` 后，7 个目标用例全部通过；初次 stack overflow 被正确归类为测试线程配置问题，而不是 assertion failure。
3. 用户对视觉提出“必须有 Codex/OpenAI 品牌语义，且图内文字要帮助理解流程”的修正后，最终保留 4 张带标签的品牌化信息图和 6 张 Mermaid 流程图；装饰性无文字版本没有进入正文。
4. 微信渠道针对长度和传播语境使用更短标题，同时保留 Blog 的完整技术标题。Publisher 完成 11/11 图片 CDN 回填、封面设置与草稿保存。
5. 飞书转写复用了 image-token → Markdown overwrite 链路，回读确认完整目录、5 张图片、6 个画板和 0 warnings。

## Problems And Fixes

### Technical illustrations started too decorative

初版图片有氛围但缺少 Codex/OpenAI 标识和解释性文字，无法承担“辅助理解 Agent 流程”的任务。后续把封面与正文图重做为带品牌锚点、流程节点、计量表和责任标签的信息图。

可复用规则已经存在于 `docs/reference/visuals.md`：技术流程、架构、状态与对比图必须在图内保留可读节点和关系；无文字装饰图不能代替解释性配图。本次再次验证该规则，不再新增重复规范。

### Publisher placeholder signal remains contradictory

Publisher 同时报告 11 张图片全部插入并到达 CDN，以及清理了 1 个残留 placeholder。上传前后 CDN 图片数均为 11，没有明确证据说明哪张图缺失，因此状态保持 `draft-created`，并要求最终群发前人工核对图片顺序与 caption。

### Mermaid code mode changed at the service boundary

本地预处理器在 `mermaid-mode=code` 下确实保留了 6 个 Mermaid fence，但飞书 `docs +update --doc-format markdown` 返回了 6 个 `whiteboard` block。当前 skill 把 code mode 描述为“飞书显示可复制代码块”，已与服务端实际行为不一致。

此次不回写服务端生成结果，也不假设所有租户一致；先登记 skill staleness，后续用独立最小样例确认是 lark-cli 版本、飞书 Markdown renderer 还是租户能力变化。

## Contrastive

1. 与《Codex 长程任务实践》相比，本次再次出现两种相同模式：Codex 主题视觉需要官方品牌锚点，以及 canonical title 与 WeChat title 需要渠道化分离。前者已通过图内品牌元素解决，后者由渠道 Markdown 与 publisher 参数明确承载，不再视为漂移。
2. 上次同类任务记录的 publisher placeholder/CDN 矛盾再次出现。本次仍是 CDN 全量成功但残留 placeholder 被清理，证明它不是偶发信号，应继续保留在 publisher staleness 中。
3. 与同日 Software Factory、Anthropic AI-Native closeout 相比，图片 token 导入飞书和保留 canonical working copy 两项改进都直接生效；无需移动或重写文章中的相对图片路径。
4. `technical-illustration-needs-text-labels` 已在多次任务中重复，并已提升到 `docs/reference/visuals.md`。本次属于规则验证，不需要再创建新 skill。

## Skill Staleness Check

- ⚠️ `wechat-article-publisher`：11/11 CDN 成功与 residual placeholder cleanup 同时出现，无法可靠判断真实缺图。
- ⚠️ `markdown-article-to-feishu-doc`：`mermaid-mode=code` 的本地输出与飞书服务端实际 whiteboard 转换不一致。

## Memory / Skill Decision

- 更新 `.local-memory/skill-staleness-wechat-article-publisher.md`，追加本次重复证据。
- 新建 `.local-memory/skill-staleness-markdown-article-to-feishu-doc.md`，记录 Mermaid code mode 的服务端行为偏差。
- 不修改 `SOUL.md` 或 `AGENTS.md`；视觉规则已经在更精确的 `docs/reference/visuals.md`，发布和飞书问题先保留为 staleness 信号。

## Remaining Human Action

- 在微信公众号草稿箱核对封面裁切、11 张正文图、图注和夜间模式，再决定是否群发。
- 正式发布后回填公开 URL，把 `publish-status.md` 和 task index 更新为 `published`。
- Blog 如需发布，另行启动 `erik-blog-publish-workflow`；当前尚未同步或推送。

## Git / Task

- 11 张实际使用的媒体二进制已复制到 `.local-archive/`；working copy 因 canonical 相对引用而保留，且受 `.gitignore` 忽略。
- Markdown、Mermaid/SVG 源、manifest、渠道 HTML、草稿状态和本复盘属于可追踪交付物。
- 工作树存在用户原有修改、删除和其他文章目录；本次没有暂存、提交或触碰无关内容。
