# Research and editorial notes

核对日期：2026-10-15，Asia/Shanghai。此文件为编辑证据，不随正文一起发布。

## 文章输入

- 用户本次消息：目标读者为 agent 工程师；手机指挥开发的价值；公司内网接入障碍；对话式 Python/Rust/Go/Node 工具准备；凭证类型与 egress 预填；重点解释凭证注入；2026 年下半年 cloud agent 的个人判断。
- 学习对话：https://chatgpt.com/share/6ad0394e-bd4c-83ee-bafb-254a82b7b00c 。标题“云端环境配置使用”，浏览器显示对话开始于“昨天 22:13”，相对当前日期对应 2026-10-14。
- 分享页通过 web 文本抓取返回空正文；改用 Codex in-app browser 读取，已读取环境/任务、Vault、Network Secret、OpenAI/Firecrawl 示例、VM/sandbox 及体验反馈等讨论。按页面消息导航懒加载，未下载上传图片，未将任何凭证值或账号状态写入稿件。
- 用户体验是一手输入；分享对话中 ChatGPT 的回答只用来发现问题，不作为产品事实的独立证据。

## 已实际抓取的官方资料

1. [Codex Cloud](https://learn.chatgpt.com/docs/cloud)；取得同路径 `.md` 完整正文。
2. [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments)；取得同路径 `.md` 完整正文。
3. [Codex Cloud (Legacy)](https://learn.chatgpt.com/docs/environments/cloud-environment)；取得同路径 `.md` 完整正文。注意当前与 Legacy URL 差一个复数 s。
4. 旧 developers.openai.com 的 `/codex/cloud/environments` 已重定向至 Legacy 页面；不能沿旧入口假定读到当前文档。

## 关键结论与证据范围

| 结论 | 依据 | 采用方式 |
| --- | --- | --- |
| 云端任务可跨网页/手机/桌面继续，电脑休眠可继续工作 | 当前 overview；当前环境指南 | 产品事实 |
| 一环境可选多仓库；新任务独立；已发布文件系统复用 | 当前环境指南 create/reuse 章节 | 产品事实；图不暗示底层快照实现 |
| 对话式识别依赖与缺失配置；Install script / Start skill | 当前环境指南 customize/configure | 产品事实；更细的自动预填体验来自用户 |
| 直接变量交付真实值，Network Secret 交付 placeholder | 当前 configure 章节 | 核心机制 |
| HTTPS:443；setup 和 task 期间都替换；不将 raw 值放入任务进程/文件 | 同上 | 必须明确限定 |
| environment-owned network secret 保存后加入网络目标；个人值/直接变量不自动加 | 同上 | 防止“填了 Key 就能联网”的错误 |
| Vault 请求匹配、适用范围、特定环境值优先 | supply-personal-values | 不额外推定其他来源的优先级 |
| Tailscale、IPv4 subnet routes、split DNS、MagicDNS | private-networking | 纠正“任何内网都不能访问”的泛化 |
| 每任务 VM；资源和七日默认恢复窗口 | vm-specifications | 2026-10-15 时间限定 |
| GitLab/GHES/browser/computer use 当前限制；local personal skills 不同步 | current-limitations | 只用于本文当前云端产品，不泛化整个 Codex |
| Legacy secrets 只在 setup 提供、agent 阶段移除 | Legacy environment-variables-and-secrets | 编辑区分，不套用到当前 Network Secret |

## 工程推论，不写成官方实现

- 职责层分为环境配置/生命周期、任务执行、受控服务访问；属于解释模型，不是内部服务名。
- 不能从文档推断 Firecracker/Kata/KVM 的具体使用、VM 与容器层次、存储与密钥库产品、TLS 终止拓扑。
- Network Secret 仍授予服务使用能力和可能的消费/副作用；目标回显可造成泄露是一般威胁分析，不是本轮漏洞复现。
- HMAC/签名等本地计算不能直接把占位符当作原始密钥；SDK 代理兼容性需分别验证。

## 没有沿用的对话结论

- 分享对话讨论了 Responses API Network Secret 兼容性 issue（#51081）。本轮没有核对该 issue 当前状态、没有实际复现，不在文章中写成“当前已知 bug”，也不因此建议默认改成真实值直注。
- 不写环境数量的确定上限或“无限”；不扩写套餐价格、单独收费、API 计费等未经本轮完整查证的信息。
- 没有将示例代码包装为已运行成功的测试；例子使用明确的占位主机。

## 补充静态参考（未作为云端生产证明）

- 阅读了本机 cloud-environment 插件 0.1.2 的 runtime/networking 指引，其中描述 sidecar、受管代理、CA trust 和 placeholder 行为；当前会话运行在本机，并未执行云端 environment_status，也未观察云端运行状态。
- 查看了本机 openai/codex checkout，HEAD `279ba894152b2c01c5294cc0723b463b209bdca4` 的 network-proxy/credential_broker 源码。只确认本地代码里有 broker、dummy 和 host-binding 相关结构；没有验证远端该提交、工作树差异或云端实际部署。正文不据此声称生产链路已源码验证。

## 交付边界

- 交付 canonical Markdown 初稿；包含个人体验、官方行为和明确标记的工程推论。
- 本轮不接入用户账号、不配置真实环境、不执行付费 API 调用、不做渠道同步或最终发布。
- 后续如补图，可由用户提供经脱敏的配置截图；文章无需依赖截图即可阅读。

## 2026-10-15 第二轮编辑

- 用户指定标题改为《Codex 云端环境学习体验：把开发带离办公桌》。
- 引子改为简短的 Cloud Agent 技术方向观察：持续执行、可复用 Environment、可恢复 Task state、受控服务访问；不声称这些能力在某个月首次发布，也不将个人趋势判断当作行业采用率事实。
- 重读官方 overview 和 Environment guide 核对引子中的能力描述；没有新增未经查证的竞品对比或发布时间。
- 重看分享页的 Environment/Task 卡片，以及 Task → Network Proxy → allowed HTTPS service 图。借鉴其分层、留白、并列卡片和路径表达，重新编写英文 SVG；没有直接复制原网页图片。
- 正文改为英文技术术语优先，保留中文叙述。Environment、Repository、Task、Credential、Network Secret、placeholder、Network Proxy、Sandbox、VM 等概念不再反复翻译。
- 用两张 article-local SVG 替换初版两张 Mermaid，补充一张 Sandbox / Container / VM / MicroVM 概念分类 Mermaid。图示均标明概念关系，不声称展示生产部署拓扑。
- 初版正文在本机 `.local-memory/2026-10-15-codex-cloud-environments/before-2026-10-15-revision.md` 留有快照；canonical source 继续使用同一个 index.md。

## 2026-10-15 第三轮：dot delegation 与 handoff

- 用户补充：ChatGPT dot 可以将任务放进 Codex Cloud Environment；本地 ChatGPT 与云端任务间的 handoff 很有价值。
- 新增独立章节，包含 dot → Cloud / Local Task 的 orchestration 图、用户直接进入 Cloud Task steering 的路径，以及 instructions/context/results 的交接要求。引子与结尾同步纳入这条使用路径。
- 实际抓取官方 Markdown：
  - [Tasks and memory](https://learn.chatgpt.com/docs/dots/tasks-and-memory)：dot 可创建已配置 Environment 中的 Cloud Coding Task；可 follow up 已创建 Task；context 不是全部对话的自动复制。
  - [Computers and apps](https://learn.chatgpt.com/docs/dots/computers-and-apps)：dot 的 cloud computer、Cloud threads、connected computer 不同；本地执行要求电脑在线且 app 打开。
  - [Remote connections](https://learn.chatgpt.com/docs/remote-connections)：正式 Hand off 转移 chat 与 Git state；当前文档明确不支持 handoff 到 Codex Cloud Environment。Local computer access with Work Cloud 是独立路径，不等价于 Codex Cloud VM 迁移。
  - [Codex environments](https://learn.chatgpt.com/docs/environments/modes)：Local / Worktree / Cloud 的执行位置，Cloud 不自动继承本机文件、process、browser session 或 VPN。
- 用户已通过异步回复明确 handoff 的实际含义：“dot 将目标和上下文交给另一个 Cloud Task，再协调结果”。正文按一手体验写为 workflow handoff，明确目标/context/results 的交接；删除不相关的正式 Hand off / Git state 迁移展开说明。原官方边界仅留在此编辑证据中。

## 2026-10-15 第四轮：Environment / Task VM 架构与 VM trade-offs

- 用户提供原对话架构图截图，要求借鉴 Environment → prepared filesystem → Task VM 的关系，并补充为什么使用 VM。
- 用新英文 SVG `assets/environment-vm-architecture.svg` 替换第 7 节的 Sandbox 分类 Mermaid。保留第 1 节的简图作为产品概念入口，第 7 节展示准备、执行和 access configuration 三种职责。
- 图中不把 raw Network Secrets 画入 filesystem，不声称 Publish 捕获 RAM / process 的完整 VM snapshot，不将 model inference 或完整 Harness 的部署位置推断为 Task VM 内。
- 重新抓取当前 Cloud environments 官方正文，确认每 Task VM、Publish captures prepared filesystem、独立 working state 的公开行为。
- 新增参考：[Agents API Sandbox security](https://developers.openai.com/api/docs/guides/agents-api/environments/security)，实际抓取 `.md` 正文。其 Isolate workloads 建议使用 VM 等 isolated compute；只支持一般隔离原则，不作为 Codex Cloud 内部选型决策或相同实现的证明。
- VM 的 isolation boundary、Task lifecycle/resource unit、prepared filesystem reuse 为明确标记的工程分析；Container 也能执行相同开发命令、控制资源和复用 filesystem。没有填写未测量的启动耗时、性能提升或 VM / Container 的绝对优劣结论。

## 2026-10-15 第五轮：分享对话素材汇总

- 用户要求继续总结原 ChatGPT 对话中的有价值内容。本轮增加 `conversation-takeaways.md`，整理 13 个原问题、12 个可复用要点、正文覆盖位置与不应直接沿用的结论。
- 通过消息导航重新读取此前未完整展示的第 6 轮 placeholder 确认，以及第 8 轮两种 delivery 总结；也重读 Network Secret 安全建议、Firecrawl 示例和 Environment 数量回答。
- 新增发现：原第 8 轮回答已经区分值的 delivery 与 GitHub OAuth / SSH 等 account authentication；原第 6 轮 sequence diagram 的 Proxy → Vault 每请求取值属于未被产品文档证明的内部画法，汇总中予以限定。
- 重读 Environment guide 中 connection、personal values、environment-owned destination、OIDC 段落；实际抓取 [Pricing](https://learn.chatgpt.com/docs/pricing) 与 `.md`，核对 Local / Cloud usage 共享及 API token pricing 与 subscription usage 分离。
- 不沿用具体 Environment quota、未经核实的 Responses API bug、所有 SDK 兼容等结论。没有把 billing 说明扩写为具体套餐价格或消费建议。
- 本轮主稿未改，先交付素材汇总及少量编辑建议，避免内容持续膨胀。

## 2026-10-15 第六轮：正文整合与叙事结构优化

- 用户明确授权 proceed，并要求顺带优化 outline。已将确认的素材融入主稿，保留现有标题、作者立场和技术术语偏好。
- 叙事顺序：使用价值与 dot handoff → Environment / Task 模型 → provisioning → Credential delivery → access verification → VM architecture → practical limits → engineering takeaways。
- 从 9 个顶级 section 收束为 8 个；Ownership × Delivery 表、account / identity 接入区别、quota / resources / usage 区分、Harness / Sandbox 职责分离已加入。
- 合并重复的状态复用、Republish、最小 request / SDK 验证及安全边界说明；整合前后中文字符数从 6228 到 6231，新增信息主要通过重组和替换纳入，未继续堆叠章节。
- 继续保留关键限定：workflow handoff 不是 Task VM 迁移；Network Secret 不覆盖全部 authorization；Proxy / Vault 内部 RPC、完整 memory snapshot、具体 hypervisor 未确认；无真实 SDK 兼容性实测。
- writing brief 与 conversation-takeaways 的章节定位已同步；整合前正文快照保存在本机 `.local-memory/2026-10-15-codex-cloud-environments/before-outline-revision.md`。
- 本轮沿用同日已抓取并记录的官方来源，不引入新的发布时间、具体价格、配额或兼容性结论。

## 2026-10-15 第七轮：官方 UI 插图

- 用户明确要求将 Cloud environments 官方页面中的插图用于文章。重新打开原页，核对其实际渲染内容。
- 页面并无对应的独立截图文件：五张 UI 插图以带 aria-label 的 HTML/CSS figure 直接绘制。采用官方原页浏览器画面，按 figure 的实际边界截取为 JPEG；没有用生成模型重绘，也未登录或读取个人账号。
- 选入四张：Environment picker、Environments 管理 / Edit、Manage secrets、Personal Vault。较长的 setup 总览未选，避免缩小后小字难读。
- 图片放在 article-local assets，正文分别在 Environment 更新、创建入口、Network Secret 配置、Personal Vault 操作段落中引用，并附可见的“官方文档 UI 示意”caption 与来源 anchor。
- `assets/manifest.json` 记录官方 source page、figure label、capture date、dimensions、SHA-256、使用位置。图片中的项目与 credential 字段均来自公开文档示例，不是作者的账号状态。
- 三张原有 SVG 与 dot Mermaid 保留：官方 UI 插图解释操作位置，概念图解释 execution / credential / VM 关系。
- 原稿快照保存在本机 `.local-memory/2026-10-15-codex-cloud-environments/before-official-illustrations.md`。本轮只完善本地文章与 assets，没有执行渠道发布。

## 2026-10-15 第八轮：polish-article 全文精修

- 用户明确调用 polish-article。按 SOUL 的 Agent / AI Technical Essay 主 register、personal technical blog 辅 register 精修，未改变已确认的八节结构和 thesis。
- 收紧引子与结尾的重复论述，删减图前图后的重复边界说明，将动作表达改为更自然的中文，保留英文技术名词。
- 统一 raw credential / placeholder / Proxy substitution 的表述，消除“替换 raw credential”可能引起的替换方向歧义；Ownership 与 delivery 的含义保持分离。
- 保留 dot workflow handoff 的用户一手体验、Credential 的适用条件、SDK 验证与 authorization boundary、VM 的三项工程取舍和成本、未公开实现的限定，以及公司接入和 usage 说明。
- 标题、frontmatter、源链接集合、四组代码示例与七张图片引用保持完整；没有补写新的价格、quota、bug 或 SDK 实测结论。官方图片 attribution 与 provenance manifest 保留。
- 精修前主稿快照保存在本机 `.local-memory/2026-10-15-codex-cloud-environments/before-polish.md`，便于逐句比较。
