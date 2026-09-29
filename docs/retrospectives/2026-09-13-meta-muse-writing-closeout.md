# Meta Muse 写作与发布收尾复盘

## Context

本次任务围绕 Meta 于 2026-09-08 发布的 Muse 展开，产出一篇 canonical 文章、Blog 版本和微信公众号版本，并经过多轮封面反馈迭代。最终封面使用 Meta 与 Muse 官方标记作为生图参考图，形成动态的云端 Agent 主题视觉；没有把 logo 后期硬贴到原图上。

最终发布边界是：Blog 已公开上线；微信公众号已保存草稿，但没有代替作者完成最终发布或群发。

## What worked

- `content/origin/` 作为唯一 canonical 源稿，Blog 与 WeChat 都从同一源稿派生，文章内容和图片引用可追踪。
- Blog 同步、构建、Pages 部署和线上验证形成闭环：文章发布提交 `a20c90e` 及后续封面归档修复已推送到 `main`，当前 HEAD 为 `8902f88`；线上文章路由返回 200，桌面端与 390px 移动端均无横向溢出和控制台错误。
- 微信流程使用同级 `index.wechat-preview.html` 作为渠道交接产物；正文 3 张图片均上传 CDN 并成功插入，标题回读、作者、封面和保存结果均有证据。
- 面对封面反馈，最终采用“官方 logo 作为 reference image + 生图体现 Muse 主题”的方式，满足品牌识别和主题表达两个要求。
- closeout 将最终稿、实际使用媒体、提示词、manifest、研究笔记和微信发布记录集中归档，同时保留 origin assets 工作副本，避免破坏 canonical 的相对路径。

## Pitfalls / failure / workaround / verification

- 初始封面方向没有准确表达“用 logo 做生图参考”，经过多轮反馈后改为 reference-image 方案；通过检查最终图片尺寸、manifest 和文章引用确认 Blog/WeChat 使用的是 v4 资产。
- 渠道源稿最初只有 `article.wechat-preview.html`，closeout 前补齐了 workflow 约定的同级 `index.wechat-preview.html`，并验证 HTML 无脚本、外链 href、data URI 和占位符。
- 当前文件预览页不一定能被浏览器控制面直接接管，因此没有把 UI 状态当作唯一证据；改用 publisher 的标题/封面回读、CDN 计数、`appmsgid` 和本地发布记录完成验证。
- 发布器能可靠创建草稿，但不负责最终群发；因此状态明确记录为 `draft-created`，不把“保存成功”误报成“已发布”。

## Contrastive

### 与之前同类任务相比

本次继续沿用了前几次收尾中已证明有价值的三类证据：补齐渠道级 `index.wechat-preview.html`、记录 publisher 的 CDN 上传/插入计数、把草稿保存与最终群发严格分开。Blog 侧则补充了线上移动端和 Pagefind 搜索验证，发布证据比仅有 commit 更完整。

### 之前改进方向是否被验证

已验证：渠道 preview 标准产物已补齐；微信侧拿到了 3/3 CDN 与标题/封面回读；canonical 相对路径所需的 origin asset working copy 被保留；本轮没有出现新的占位符误判。封面生图从“后期合成 logo”切换到“logo 参考图”也被最终视觉验收验证。

### 是否是历史重复问题

是。`wechat-article-publisher` 仍然只覆盖“登录、注入、上传、保存草稿”，不覆盖最终群发；`closeout-preserve-working-copy-for-canonical-relative-assets` 也再次出现，说明它应继续作为固定收尾检查项。另一方面，canonical author 与微信配置 author 的文档契约不一致是本轮新发现的问题，已同步修正文档并留下 staleness note。

## Skill Staleness

发现 `docs/workflows/wechat-writing-publishing.md` 的 frontmatter 示例仍包含 `author: "Erik"`，但当前 `wechat-publish-workflow` 的约定要求 canonical 不写 author，发布器从 `.config/wechat.toml` 的 `default_author` 读取。已删除示例中的 author 行，补充配置来源说明；详细记录见 `.local-memory/skill-staleness-wechat-publish-workflow.md`。

## Follow-up

WeChat 还没有公开文章 URL。作者需要在微信后台草稿箱完成 final human review，确认无误后自行决定是否群发。
