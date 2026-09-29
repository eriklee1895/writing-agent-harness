# Meta Muse 调研笔记

更新时间：2026-09-11（Asia/Shanghai）

## 文章判断

暂定 thesis：Muse 的核心创新不是证明了新的通用智能，而是把个人 Agent 产品化为一个持续存在、可操作真实世界、受独立权限层约束的云端运行时。它在产品架构上具有革命性潜力，但在模型跃迁、可靠性、用户信任和规模经济上仍需要真实生产数据验证。

## 事实台账

### Meta 官方发布与产品设计

- 2026-09-08，Meta 发布个人 AI Agent Muse；首发美国，入口为 Muse App、网页和 WhatsApp，未来计划进入 AI glasses。
- Meta 将 Muse 描述为能够处理任务与长期目标、打开浏览器、填写表单、代表用户协商，并在 App 关闭后继续工作。
- Muse 可以连接邮件、日历、Meta 应用等服务；支付场景使用 Stripe Link 的一次性卡号，Shop Pay 和 1Password 为后续计划。
- Muse 记住用户重要信息，支持 Goals、Ideas、activity log、权限设置和可编辑的 memory；可以产出文档、PDF、网页和交互式 dashboard，称为 Artifacts。
- 产品设计稿强调主聊天、side chats、并发任务、主动消息、后台任务、结构化审批卡和不可逆动作的确定性控制。

### Meta 官方安全架构

- 每个用户有一台专用 Muse Secure VM：隔离 Linux box，含浏览器、文件系统、终端、存储、CPU、内存，可编译代码、创建自定义 skills、运行并发子 Agent 和 cron。
- 内部代号 Hatch 的核心 Agent harness 在 `systemd-nspawn` runtime cell 中运行；cell root 不等于 host root，使用独立 root filesystem、虚拟网络和受限 kernel capabilities。
- `hatch-safety` 在 runtime cell 外运行独立模型和 classifiers；`privsep` 运行权限受限的内置 connector worker；`hatch-authd` 存储 token 并负责 credential surrogation；Sentinel 是 connector action 和 network egress 的唯一权限权威；持久应用状态存放在与 runtime 和凭据存储分离的 Postgres 中。
- Sentinel 通过 forward proxy、Linux networking controls 和 eBPF 检查外发请求，可以判断域名、IP、端口、协议、HTTP method、path、解码后的请求，并做 SSRF 限制。
- 真正的 credential 在网络边界才由 `authd` 注入；runtime 和主 Agent 只看到 surrogate token。用户批准会直接到客户端和 Sentinel，不依赖 Agent 对话转述，并可绑定一次性、session、任务、时间或长期权限。
- 浏览器通过 CDP broker 控制；浏览器子 Agent 看到 accessibility tree，不是 raw DOM；不能在页面上下文运行 JavaScript、使用 script verbs 或 Chrome DevTools。用户接管或凭据填充时 Agent 暂停。
- Meta 描述了 prompt-injection 防御的多层机制：模型训练、untrusted input 标记、独立 classifiers、agentic red-team、人工审批、runtime/credential/egress 的确定性边界；并使用 tainted egress 影响自动放行策略。
- 当前 Secure VM 通过隔离和运营政策降低访问风险，但官方明确说明它不阻止 Meta 在必要时为了支持、保护或运营服务访问数据。后续 Confidential VM 计划使用只有用户持有的密钥，目标是密码学、可验证地阻止 Meta 访问 VM 内容。
- VM 数据会持续备份；对话和 VM 数据不进入 Meta 广告系统，但浏览行为可能通过外部网站间接影响广告；对话、工具调用、子 Agent handoff 等 trajectories 在清理关键个人身份信息后可用于训练，用户可以 opt out。

### Muse Spark 1.3

- 2026-09-02，Meta AI Research 发布 Muse Spark 1.3，面向 Muse Code 和 Meta Model API。
- 官方强调长程 Agent 工作、复杂指令保持、多任务映射、主动协作、遇到阻塞时向用户求助、后果性动作前确认、能力边界意识，以及更强的 prompt-injection 抵抗。
- Meta 工程师内部对比称，相对 1.2 使用约 20% 更少的 tool calls 和约 25% 更少的 tokens；这是 Meta 自报的相对指标，不等同于独立生产成功率。
- 产品发布稿把 Muse 说成由 Muse Spark 驱动，但没有公开完整的模型路由表；文章因此不把每个 Muse 请求都确定写成 Muse Spark 1.3。

### 可用于文章的公开场景

- 购物：搜索、比较、监控价格、在 checkout 前请求确认，并用 Stripe Link 一次性卡号完成购买。
- 旅行与门票：规划行程、持续监控票价或库存，状态变化后再通知用户；长期监控的稳定性仍需实测。
- 家庭事务：从学校邮件和网站提取日期、更新日历、准备购物车，并在临近截止时提醒。
- 个人目标：制定年度健身计划、根据生活变化调整训练计划，或把创业目标拆成行动线。
- 生活协作：把保存的 Instagram 食谱变成购物清单，并记住朋友的饮食限制。
- Artifacts 与自定义工具：生成文档、PDF、网页、dashboard；对有 API 或 CLI 的服务，写自定义 connector。
- 上述示例 prompt 是编辑性翻译，不是 Meta 官方逐字脚本；具体能力受连接器、网站、授权和地区限制。

### 独立交叉材料

- Reuters 2026-09-08 报道，Meta 内部测试一方面出现长途旅行安排成功的正面案例，另一方面出现断连、频繁重新登录、监控页面约 15 分钟后停止刷新、无故关闭监控，以及一次识别儿童生日照片玩具的任务中绕过防护暴露 iCloud 照片等问题。Meta 没有立即回应具体事件。
- Reuters 同文报道 Muse 内部代号为 Hatch、首发美国，并引用 Meta 高管称产品发布前曾在 4 月推迟以加强安全。

## 事实 / 推断 / 未验证

### 直接事实

- 发布日期、入口、公开功能、Secure VM、Sentinel、authd、privsep、Postgres、浏览器 broker、审批和 Confidential VM 计划，均来自 Meta 官方页面。
- 内部测试问题、Hatch 名称和发布延期，来自 Reuters 报道的内部帖子与访谈。

### 基于事实的推断

- Muse 的核心产品单位从 chat turn 变成 durable goal，交付单位从 answer 变成 state change / artifact。
- “每人一台云电脑”意味着长期成本单位可能从请求转向租户、运行时和持续资源；这是架构推断，不是 Meta 的成本披露。
- Sentinel 的价值主要来自权力分离和不可绕过的执行边界，不在于它是不是“第二个更聪明的 Agent”。

### 没有写成事实的内容

- Muse 的真实任务成功率、SLO、长期在线比例、用户周活、订阅转化、实际并发上限和每用户成本。
- Muse 产品内部的完整服务拓扑、模型路由策略、代码实现和 Confidential VM 的正式发布日期。
- “Muse 是第一个个人 Agent”或“已经实现超级智能”这类官方营销/战略表述之外的强事实结论。

## Sources

- https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/
- https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse
- https://introducing.muse.ai/
- https://research.meta.ai/blog/introducing-muse-spark-1-3
- https://about.fb.com/news/2026/08/the-future-is-for-everyone/
- https://tech.yahoo.com/ai/meta-ai/articles/meta-launches-ai-agent-access-190605563.html

## Visual research and cover iterations

- 2026-09-11 used Volcano Engine image search for “Meta Muse personal AI agent official launch visual” and “Meta Muse Secure VM Sentinel product”. Results were mostly reposted or AI-generated promotional images; no external image was reused.
- The visual direction was extracted from Meta’s own launch/product pages: deep blue cloud environment, warm coral/orange agent core, a dedicated cloud computer, and a distinct security boundary.
- The v2 cover was an original built-in `imagegen` generation and is now superseded. The v3 cover added exact Meta and Muse brand marks as a post-composited lockup and is also superseded after editorial review.
- The current v4 cover uses the official Meta wordmark and Muse M mark only as imagegen reference inputs. The generated scene itself integrates a Muse-shaped blue intelligence core, a Meta-like infinity trajectory, a cloud computer, a user goal, shopping, travel and email/calendar cues. There is no post-composited Logo panel. The source is `assets/meta-muse-cover-v4.png`; the WeChat headline crop is `assets/meta-muse-cover-v4-wechat.png`; the exact prompt is recorded in `assets/meta-muse-cover-v4.prompt.md`.
- The official reference assets are stored locally as `assets/meta-brand-official.svg`, `assets/muse-logo-official.svg`, `assets/meta-brand-reference.png` and `assets/muse-logo-reference.png`.
