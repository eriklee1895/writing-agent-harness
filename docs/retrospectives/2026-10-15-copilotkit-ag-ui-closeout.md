# CopilotKit / AG-UI 写作与三渠道交付复盘

日期：2026-10-15。源稿：[CopilotKit: 会成为下一个LangChain吗？](../../content/origin/2026-10-14-copilotkit-ag-ui/index.md)。

## 交付与归档

- [博客完整版](https://eriklee-blog.pages.dev/posts/2026-10-14-copilotkit-ag-ui/)已上线，生产提交 `e43358c`，Cloudflare 构建成功。公开文章、图片、JSON / CSV 与线上搜索核对通过。
- 微信保留[实际交付 HTML](../../content/wechat/2026-10-14-copilotkit-ag-ui/index.wechat-preview.html)。用户到草稿箱检查后明确反馈“格式 perfect”。平台运营信息仅见 `.local-archive/2026-10-14-copilotkit-ag-ui/publish-status.md`，不得从博客上线或格式验收推断微信后续发表状态。
- [飞书完整版](https://bytedance.my.larkoffice.com/docx/JjFCdWebSo3ygHxKdqAmH3wyy6e)回读核对 8 节、7 图、2 张原生表格及 42 个原始来源链接，无残留占位符、无写入降级警告。
- 本机归档 `.local-archive/2026-10-14-copilotkit-ag-ui/` 保存最终文章快照、实际使用图片、提示词与元数据、研究 scratch 以及渠道验证。7 个 PNG 移动后保留相对软链接；增长 SVG 继续入 Git并复制到归档。未使用或被否定的生成版本保留，不强制删除。
- canonical `status: draft` 保留原稿元数据；真实渠道状态分开记录，不用一个 frontmatter 字段代替三种交付状态。

## 写作与证据

开头最终落在作者真实项目经历：ChatGPT 推荐方案，使用 CopilotKit / AG-UI 后开始研究公司和生态。保留第一人称随笔感，主体采用行业分析。用户明确删掉“法律主体名字出现在服务条款”这类无助于论点的信息；LangChain 类比则落到“从 SDK 获得开发者入口，再承接生产需求”的成长路径。

生态增长使用固定 README 提交的离散快照，统一计数口径，不把目录支持数量等同为原生支持、生产采用或市场份额。用户指出 ACP 与 AG-UI 相近后，协议图补入 Agent Client Protocol，并承认能力重叠，避免画成互斥分层。CLiF 图保留 early access 与延伸方向边界；收尾商业图明确使用协议不必然产生付费。

## 配图与公众号

首轮氛围图被用户否定，后续采用带中文标签、节点关系和事实边界的信息图。最终成套图沿用用户指定内置 imagegen，增长数据图使用确定性绘图。公开文档的图内文字不等于产品实测证据；正文图注继续说明推论与限制。

renderer 首次忽略 frontmatter 标题，产生“未命名文章”；自动 alt 图注与源稿显式图注重复。修正派生 HTML 的 title、hero、摘要，合并图注，增长 SVG 切换现有 PNG。没有为适配而修改 canonical 正文结构。

用户明确要求公众号纯白底，以适应手机昼夜阅读。最终使用白底、透明外层/章节容器及透明表头，保留橙色强调和留白。390px / 430px 浏览器检查通过，但不将 media query 模拟等同为微信夜间模式的真机验证。用户随后在真实草稿箱确认排版满意。

publisher 逐张确认 6/6 CDN 后保存，标题、署名、52 字摘要及封面校验通过。保存后从内容管理进入草稿箱，再点卡片的编辑入口回读：6 张图全部加载、显示尺寸非零，6 份图注与收尾图均在。不要仅凭保存成功或“窗口保留打开”日志代替回读。

## 博客与飞书适配

博客同步保留完整原文、42 个来源链接和 7 个视觉，构建、Pagefind 和图片优化检查通过。关键词推断误将本篇归入 LangChain 系列，手动按文章主体改为 AI Frontier / CopilotKit Notes / 行业观察。README 数据说明并不属于图片复制集合，因此单独公开精简的数据说明页、JSON 和 CSV，修正博客链接；不为修一条数据链接公开研究缓存或被拒图。

部署检查先遇到未完成部署的 404，再遇到连接超时。保留负面证据，等待 Cloudflare 成功并重试公开路由、图片与搜索。最终线上搜索结果已出现新文章；不将单次网络超时升级为站点故障。

飞书沿用 user-level 转换 skill，按实际 `--help` 省去旧 `--api-version v2`，CLI 文件输入使用当前目录内的相对路径。封面作为开篇图片，SVG 切 PNG，主章节映射为原生一级标题；图片保留原始尺寸并避免重复 caption。用户要求新文档，未覆盖已有用户稿件。完整回读比只数上传成功更能确认交付。

## Contrastive

1. **与上次同类任务的不同**：对照 [Cloud Agent Runtime](2026-09-29-cloud-agent-runtime-closeout.md)，本次同为博客、微信、飞书三渠道，仍需真实草稿重开与飞书全文回读。新增问题是 frontmatter 标题不被 renderer 读取、双份图注、白底要求与 preset 冲突。对照[塞罕坝](2026-10-06-saihanba-forest-road-closeout.md)，本次有两张表格和可复现数据链接，不能用纯散文成功推断所有渠道适配已覆盖。
2. **上次改进是否验证**：归档加相对软链接继续验证 hash、忽略规则和预览加载；公众号作者从本机配置读取，原稿不带 author。本次博客 adapter 已正确使用 summary 并筛选引用图片，之前这两项缺口不再复现；仍需按篇核对 taxonomy、本地说明链接。长标题超过 40 字符的 publisher 修复仍未由本篇 29 字标题验证。
3. **重复问题如何处理**：媒体选型与 article-illustration 历史脚本默认冲突再次出现，本次在项目 skill 中明确规划与执行分工、优先沿用任务中用户已选的生成器。飞书旧 CLI 参数和文件路径问题与 Cloud Agent Runtime 相同，登记重复 staleness，未擅自修改外部共享 skill。保存成功与浏览器继续可操作之间的差异继续靠重开草稿复核。

## ⚠️ 技能腐化风险与处置

- `wechat-article-renderer`：暖底默认、frontmatter 标题、重复图注尚未在通用脚本内修复。已补项目规则与 Gotchas，保留已验收 HTML；没有把文档补丁宣称为自动化能力上线。
- `article-illustration`：补用户指定生成器优先级，避免再次退回历史 API/模型入口。本次只改指导，不改生成脚本。
- `erik-blog-publish-workflow`：补 taxonomy 主体核对与非图片本地链接检查。适配器自动分类/辅助资料复制仍是待完善项。
- `markdown-article-to-feishu-doc`：外部 skill 示例与 CLI 1.0.88 帮助存在差异，写入 `.local-memory/skill-staleness-markdown-article-to-feishu-doc.md` 等后续修订。
- `AGENTS.md`：把公众号白底要求作为已确认偏好，修正 Mermaid 默认是代码块、非自动画板的旧说明。

没有新增 skill，没有改 SOUL，也没有写入用户级全局 memory。任务索引和待修线索保存在本机 `.local-memory/`。

## Git 与后续

博客生产提交已独立发布。写作仓库用 `codex/copilotkit-ag-ui-closeout` 分支锚定原有两次本地文章提交；初次 closeout 时仅准备改动。用户随后明确要求提交 GitHub、清理本地资源并回到最新 main，因此进入提交与主分支同步流程；具体提交以 Git 历史为准。本机归档迁至主检出 `.local-archive/2026-10-14-copilotkit-ag-ui/` 后再清理任务临时目录，其他 worktree 和无关改动保留。公众号若后续正式发表，再在本机发布态回填永久链接；该动作不影响本次三渠道交付与本机归档的完成。
