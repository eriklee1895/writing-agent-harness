# Research Notes

本文件保存两轮 deep-research 的原始调研产物，供 `index.md` 复核与追溯。

- **Round 1**：Maria Educação × Temporal 案例深挖（2026-08-18 执行）
- **Round 2**：2026 主流云端 Agent 运行时与持久化架构调研（2026-09-29 执行）

两轮都用同一套 harness：5 个搜索角度并行 → URL 去重抓取 → 提取可证伪 claim → 每条 claim 3 票对抗式验证（2/3 反驳才淘汰）→ 合并语义重复、按置信度排序。

---

## Round 1：Maria Educação × Temporal

### 统计

| 指标 | 值 |
|---|---|
| 搜索角度 | 5（官方一手来源 / 工程技术深潜 / AI Agent 设计模式 / Temporal 编排层对比 / 社区演讲与规模数据） |
| 抓取来源 | 17 |
| 提取 claim | 67 |
| 验证 claim | 25（top by importance） |
| 确认 | 24 |
| 驳回 | 1 |
| 未验证 | 0 |
| 合并后 | 14 |
| agent 调用 | 99 |
| 耗时 | ~20.5 分钟 |

### 已验证的核心事实（按重要性）

**公司定位与规模**（confidence: high, vote 3-0）
巴西 B2G/B2B 教育科技公司，自我定位「把教材转化为个性化学习体验的 AI 基础设施」，而非传统出版商或 LMS。四条产品线：(1) AI 生成教科书/印刷与数字教学材料；(2) 大规模自适应测评，含自动批改与能力（proficiência）报告；(3) 数据智能——视频、音频、题目自动组织；(4) Lisa，AI 家教与教师 copilot。

LinkedIn tagline 原文：「A infraestrutura de IA que transforma materiais didáticos em experiências personalizadas — produção editorial, avaliações, tutoria adaptativa e dados educacionais em uma única plataforma」

产品理念：「IA com propósito. Professores no controle. Alunos no centro.」

规模数字在两个一手源（官网 + Temporal 案例）之间完全一致：80+ municípios、10M+ students、1M+ pages、1M+ assessments、3M+ questions、3B+ data points、10B+ AI tokens。客户含 FTD Educação、SOMOS Educação、Prefeitura de Palmas、Instituto Alfa e Beto。

**注意**：「alunos impactados（受影响学生）」是 B2G 覆盖口径，不等于月活或付费用户。

来源：`https://www.linkedin.com/company/maria-educa%C3%A7%C3%A3o` · `https://mariaeducacao.com` · `https://temporal.io/resources/case-studies/maria-educacao`

---

**技术栈**（confidence: high, vote 3-0）

案例逐项列出的栈，每项都有原文对应：
- Backend: Python (Django)
- Temporal Python SDK: temporalio
- Agent/LLM logic: LangGraph/LangChain inside activities (keeps the Workflow code deterministic)
- Workers: Google Kubernetes Engine (GKE)，重负载任务用 isolated node pools
- 两个 Temporal Cloud 集群（主平台 + 独立隔离服务），全 mTLS 客户端证书认证
- 选 Cloud 理由：「a fully-managed service (no cluster for us to run)」
- 团队 ~38 人

来源：`https://temporal.io/resources/case-studies/maria-educacao`

---

**Temporal 部署规模**（confidence: high, vote 3-0）

原文：「orchestrates virtually every long-running/AI pipeline on the platform — roughly 100 workflows and 240+ activities across 16 task queues, plus 13 scheduled routines」

结构原则：
- 「Each business pipeline is one Workflow; each atomic unit of work ... is an Activity ... its own timeout and retry policy」
- 「Fan-out is done with child workflows (e.g. one child per document window/chunk)」

来源：同上

---

**迁移路径**（confidence: high, vote 3-0）

原文逐字引用：
- 「Original approach: raw Python threads — lost state on every deploy」
- 「Briefly used Celery + Redis — handled task execution but no durable, resumable, observable multi-step workflows」
- 「Most critical factor: durable execution delivered as a managed service」

决策标准还包括 per-step retry policies、heartbeat/timeout（对慢 LLM 调用关键）、受控 fan-out、可观测性、成熟 Python SDK、全托管免运维。评估由 CTO Rubens Aguiar 主导。

来源：同上

---

**LISA 内容摄入工作流**（confidence: high, vote 3-0）

原文：「LISA content ingestion (largest): raw PDF → complete interactive course ... chapters, lessons, concepts, questions, images, and simulations」「11-stage flow」「Each LLM call is its own activity for independent retries and observability」

双模式：「one long workflow that resumes from wherever it stopped」vs「where a curator reviews before each step advances」

扇出：「heavy per-lesson fan-out」「child workflows plus concurrency caps」

**未公开**：11 个阶段的精确顺序与名称。已知阶段类别：document extraction、conversion、AI structuring、resource generation fan-out、curator gate（可选）。

来源：同上

---

**三条测评工作流**（confidence: high, vote 3-0）

原文：「Assessments (three correction flows): answer-card (OMR) reading via computer vision; AI-based open/essay correction against rubric; IRT/TRI psychometric grading — polls with heartbeats for up to an hour」

三种 Activity 形态：
1. CPU/GPU 密集型批处理（OMR CV）→ 独立 task queue + 隔离 node pool
2. LLM 调用密集、rubric 驱动（开放题批改）→ 细粒度 Activity + retry/validation loop
3. 长时轮询型（IRT 统计，可达 1 小时）→ heartbeat 是关键

来源：同上

---

**Temporal 与 LangGraph 是两层协作**（confidence: high, vote 3-0）

原文：「Temporal and LangGraph work at two different layers rather than one replacing the other」「When an agent or LLM needs its own multi-step reasoning, that logic runs as a LangGraph graph inside a single activity」「Temporal is the durable orchestrator, LangGraph is the in-activity 'agent brain'」「because Workflow code has to stay deterministic (for replay), any non-deterministic LLM/agent work lives in an activity」

官方集成（`temporalio[langgraph]` 1.27.0+）把模式产品化：每个 LangGraph 节点必须声明 `metadata={'execute_in': 'activity'}` 或 `'workflow'`——网络调用、LLM、随机数、时钟、文件 IO、`interrupt()` 必须 activity 模式；纯状态变换、路由、subgraph dispatch 可 workflow 模式。不声明插件直接报错（无默认值）。

来源：`https://temporal.io/resources/case-studies/maria-educacao` · `https://docs.temporal.io/develop/python/integrations/langgraph`

---

**Durability 与 Memory 架构约束**（confidence: high, vote 3-0）

官方文档原文：
- 「If your LangGraph code requires a checkpointer ... use InMemorySaver. Temporal handles durability, so third-party checkpointers (like PostgreSQL or Redis) are not needed」
- 「LangGraph's Store ... isn't accessible inside Activity-wrapped nodes」（原因：Activities 可能跑在与 Workflow 不同的 worker 上，Store 的活状态无法跨越边界；提供 store 时插件打 warning，`runtime.store` 为 None）
- 「Use Workflow state for per-run memory, or an external database ... for shared cross-run memory」
- 「Long-running graphs can hit Temporal's per-Event history size limit」→ 文档提供 `cache()` helper 配 `continue-as-new`
- Streaming Activities 是 at-least-once per attempt，已 publish 的 chunk 不回滚，订阅端必须幂等

来源：`https://docs.temporal.io/develop/python/integrations/langgraph`

---

**Human-in-the-loop 标准模式**（confidence: medium, vote 2-1）

官方文档「Human-in-the-loop」段四步：
1. 「A graph node calls interrupt(draft), pausing execution」
2. 「The Workflow exposes the pending draft via a Temporal query」
3. 「An external process (UI, CLI) queries the draft and sends approval via a Temporal signal」
4. 「The graph resumes — interrupt() returns the signal value and the node completes」

`interrupt()` 必须在 Activity 节点内调用（插件序列化并传播到 Workflow）；`Command(resume=...)` 用于 Workflow 恢复。可运行样例：`github.com/temporalio/samples-python/langgraph_plugin/graph_api/human_in_the_loop`

confidence 给 medium 而非 high：该 claim 以 2-1 通过，且文档标注 Public Preview、要求 `temporalio[langgraph]` 1.27.0+ / Python 3.11+，API 表面未来可能调整。

来源：`https://docs.temporal.io/develop/python/integrations/langgraph`

---

**Temporal 官方 AI 定位**（confidence: high, vote 3-0）

temporal.io/ai 原文：「The orchestrator for AI applications」「Get automatic retries out-of-the-box, and maintain the ability to retry until a probabilistic LLM returns valid data」「Workflows automatically hold state over long periods of time (even years), so you don't need state machines」「Orchestrate reliable, long-running, and human-in-the-loop agents. Protect against hallucinations and rate limiting. Scale to millions of agents」

**冷静看待**：「protect against hallucinations」是营销措辞——Temporal 作为编排层可以承载 verify/retry/guardrail loop，但无法从根本上阻止 LLM 产生幻觉。「millions of agents」「99.9999% uptime」是未独立验证的营销数字。

来源：`https://temporal.io/ai`

---

**LangGraph 的自我定位与重叠**（confidence: high, vote 3-0）

LangGraph README 原文：「LangGraph is a low-level orchestration framework for building, managing, and deploying long-running, stateful agents」「Build agents that persist through failures and can run for extended periods, resuming from where they left off」

checkpointer 抽象（InMemory/Postgres/Redis/Sqlite）提供真实的状态检查点、time-travel/replay、HITL interrupt。

重叠真实存在但深度不同：Temporal 提供 event sourcing、语言无关、activity heartbeat + 无限重试、成熟 signals/queries/timers、多语言 SDK；LangGraph 的持久化是 Python/JS 单语言、checkpointer 级别的 resume。

来源：`https://github.com/langchain-ai/langgraph` · `https://docs.temporal.io/develop/python/integrations/langgraph`

---

**跨案例：HeyGen**（confidence: high, vote 3-0）

Temporal 博客（HeyGen 工程师 Jiajun Zhao 署名，2026-08-14 更新）：
- legacy stack：「combined a MySQL job table, a polling scheduler, RabbitMQ, Celery workers, and a separate service for tracking job completion」
- 失败模式：「A worker might complete a job but fail to deliver its callback」「A tracker restart could drop requests」
- 事故：「During one managed RabbitMQ upgrade, work stalled across the platform. We brought up replacement capacity and repaired affected jobs manually」
- 架构：「The production Workflow coordinates close to 90 distinct activity types」
- 扇出：「We implement these scene pipelines as concurrent coroutines inside the main workflow rather than creating a child workflow for every scene」，child workflow 用于「operations that need an independent timeout, retry boundary, or failure domain」
- 代码里可见：`Act.check_video_limits`、`Act.deduct_quota`、TTS、`asyncio.gather` 并发渲染、`Act.render_and_composite`（RENDER_GPU queue）、失败补偿 `await self._refund_if_charged(input)`、per-stage semaphore

来源：`https://temporal.io/blog/how-temporal-powers-workflows-at-heygen`

---

**Maria 是案例库中唯一教育主题案例**（confidence: medium, vote 2-1）

对 temporal.io/resources/case-studies 索引全部 3 页（42 个案例）逐条核对：唯一标题/tag 明确围绕 education/edtech/schools/students/teaching/learning/LMS 的就是 Maria Educação。Duolingo 案例题为「Duolingo simplifies self-service infrastructure with Temporal Nexus」，tag 为 High Tech，内容是内部开发者基础设施。索引页没有 Education 行业 facet。

confidence 给 medium：这是穷尽性否定结论，且案例库会随时间增减（截至 2026-08-18 成立）。

来源：`https://temporal.io/resources/case-studies`

---

### 被驳回的 claim

| Claim | 票数 | 来源 |
|---|---|---|
| 「AI 工作流是一条五阶段 pipeline，且在 AI 生成与人审之间有明确的 human-in-the-loop 边界：教师上传现有材料 → AI pipeline 抽取、结构化并生成题目/视觉资源/模拟 → 教师审核决定发布 → 学生按节奏自适应学习 → 实时仪表盘反哺教学管理」 | **1-2 ✗** | `https://mariaeducacao.com` |

驳回理由：官方案例确实说 LISA 可全自动或 curator-gated，但**并未给出那五个具体阶段顺序**——该 claim 编造了阶段顺序。

### Round 1 caveats

1. Maria 的核心技术事实几乎全部来自 Temporal 官方 2026-08-12 发布的联合客户案例研究，属于厂商联合发布的营销性一手材料。它是架构自陈事实的合适权威来源（代码库规模、组件选型、迁移路径均为客户自述），但「Temporal 优于 Celery」「99.9999% uptime」「百万级 agents」属于厂商或客户立场陈述，并非独立第三方 benchmark
2. 业务规模数字由 mariaeducacao.com 与 Temporal 案例两个一手源交叉确认，一致性高；但「alunos impactados」是 B2G 覆盖口径
3. **未找到** Maria Educação 工程博客、Rubens Aguiar 独立技术演讲、GitHub 开源仓库、StackShare 或葡萄牙语深度技术采访——所有 Temporal 用法细节只能回溯到那一篇官方案例。Temporal 社区演讲/YouTube/播客搜索未返回该客户的独立 talk
4. Temporal+LangGraph 集成文档标注 Public Preview，要求 `temporalio[langgraph]` 1.27.0+ / Python 3.11+，API 未来可能变更。原 claim 中引用的 `/ja/python/temporal-langchain` 与 `/python/temporal-langchain` URL 已 404 或重定向，canonical 路径以 `/develop/python/integrations/langgraph` 为准
5. HeyGen 是另一家 Temporal 客户，不是 Maria 本身；其设计只能作为跨案例参考，不能当作 Maria 的事实
6. 五阶段 pipeline claim 被驳回（见上）

### Round 1 未解答问题

1. LISA 11 阶段的具体顺序与名称、每阶段用的哪些 LLM 模型（GPT-4/Claude/Gemini/巴西本土模型？）、prompt 结构、rubric 设计与质量评估指标
2. Lisa AI 家教的实时辅导会话如何建模——每学生会话一个 Temporal workflow，还是仅把离线内容/题目生成放 Temporal、实时对话走另一条栈？多轮记忆、工具调用、自适应选题算法与 workflow 生命周期的映射完全没展开
3. 生产规模硬指标：峰值并发 workflow 数、P50/P95 延迟、token 月烧（10B+ 是累计还是月度？）、Temporal Cloud 成本、retry 率、event history 平均大小、continue-as-new 频率、worker 数与机器规格、故障/RTO 历史
4. Maria 是否已采用官方 `temporalio[langgraph]` plugin，还是自研「LangGraph 跑在 Activity 内」的封装

### Round 1 来源清单

| URL | 质量 | 角度 | claim 数 |
|---|---|---|---|
| `https://temporal.io/resources/case-studies/maria-educacao` | primary | 官方一手来源 | 5 |
| `https://mariaeducacao.com` | primary | 官方一手来源 | 5 |
| `https://br.linkedin.com/in/rubensmgaguiar` | unreliable | 官方一手来源 | 0 |
| `https://www.linkedin.com/company/maria-educa%C3%A7%C3%A3o` | primary | 官方一手来源 | 5 |
| `https://temporal.io/resources/case-studies` | primary | 官方一手来源 | 4 |
| `https://temporal.io/blog/feed.xml` | blog | 官方一手来源 | 5 |
| `https://langchain-ai.github.io/langgraph/` | primary | 工程技术深潜 | 5 |
| `https://docs.temporal.io/develop/python/core-application` | primary | 工程技术深潜 | 4 |
| `https://temporal.io/cloud` | primary | 工程技术深潜 | 4 |
| `https://docs.temporal.io/ja/python/temporal-langchain` | primary | AI Agent 设计模式 | 5 |
| `https://github.com/temporalio/sdk-python/tree/main/contrib/temporal-langchain` | unreliable | AI Agent 设计模式 | 0 |
| `https://temporal.io/ai` | primary | AI Agent 设计模式 | 5 |
| `https://learn.temporal.io/tutorials/python/llm-workflow/` | unreliable | AI Agent 设计模式 | 0 |
| `https://temporal.io/customers` | primary | AI Agent 设计模式 | 5 |
| `https://temporal.io/blog/how-temporal-powers-workflows-at-heygen` | primary | 编排层对比 | 5 |
| `https://temporal.io/blog/durable-flexible-multi-agent-systems` | blog | 编排层对比 | 5 |
| `https://temporal.io/blog/announcing-openai-agents-sdk-integration` | primary | 编排层对比 | 5 |

「社区演讲与规模数据」角度返回 6 个结果、0 个 novel（全部被过滤）。

---

## Round 2：2026 主流云端 Agent 运行时架构

### 统计

| 指标 | 值 |
|---|---|
| 搜索角度 | 5 |
| 抓取来源 | 25 |
| 提取 claim | 115 |
| 验证 claim | 25 |
| 确认 | 25 |
| 驳回 | 0 |
| 未验证 | 0 |
| 合并后 | 14 |
| agent 调用 | 107 |
| 耗时 | ~20.8 分钟 |

### 已验证的核心事实

**Devin 用专用 microVM**（confidence: high, vote 3-0）

Cognition 工程博客（2026-04-23）原文：每个 session「its own dedicated kernel with fully isolated storage, networking, and compute」；容器共享内核导致横向风险（一个被攻破的会话可触及别的会话的文件系统、凭据、网络）；microVM 实现花了「over a year of hypervisor engineering」。

blockdiff 博客（2025-06-23）补充：「Devin writes and runs code in a VM environment」「Each VM disk is a CoW copy of the base disk image」，选择 VM 是因为「full isolation for security purposes」以及「many dev environments need Docker-in-Docker」（容器内嵌套容器存储放大 17 倍、慢 6 倍）。

来源：`https://cognition.com/blog/what-we-learned-building-cloud-agents` · `https://cognition.com/blog/blockdiff`

---

**Devin 的整机 snapshot + blockdiff**（confidence: high）

原文：「snapshotting full machine state at the hypervisor level — memory, process trees, and filesystem. Compute shuts down while the agent is idle, and the session resumes exactly where it left off when a CI result or review comment arrives.」

blockdiff（`github.com/CognitionAI/blockdiff`）：「blockdiff stores only the blocks in B that are different from blocks in A」；hypervisor XFS 开 reflink，「creating the rest of the file is purely a rewiring of file metadata」；20GB 快照约 200ms vs 裸拷贝 6.5s；`blockdiff apply` 重建后 xxhsum 哈希相等。50MB 会话快照 vs 多 GB 全镜像。

注：「进程不存活」是 2-1 票推断，但博客把「How to roll back the disk while the VM is running?」列为未解决问题，佐证当前 sleep 路径非热迁移。

来源：同上

---

**Cognition 自建编排层**（confidence: high, vote 3-0）

原文：「Our solution for the orchestration layer took over three quarters of dedicated engineering to build」「can manage thousands of concurrent VMs — handling provisioning, demand prediction, crash recovery, and teardown」「predicting demand to keep warm VM pools ready」；每个 session「tied to a specific task and engineer's permissions」。

**全文检索无 Temporal/Cadence/state-machine/event-sourcing 字样**——这里的 orchestration 仅指资源生命周期管理。

来源：`https://cognition.com/blog/what-we-learned-building-cloud-agents`

---

**Devin 的 HITL 框架**（confidence: high, vote 3-0）

原文：「agents execute and humans direct, review, and decide」；异步间隙描述为「An agent opens a PR, waits on CI, responds to code review, reruns tests, and pushes a follow-up commit」→「gaps — minutes, hours, sometimes days」，解决方案即整机 snapshot。

文中**无**审批工作流引擎、无挂起/信号原语描述。

来源：同上

---

**Devin 多 agent 架构**（confidence: high）

Multi-agents 博客（2026-04-22, Walden Yan）：「A manager Devin can break a larger task into pieces, spawn child Devins to work on them, and coordinate their progress through an internal MCP」；reviewer 与 coder「do not share any context beforehand」，reviewer「forced to reason backward from the implementation」，coder 用「broader context of user instructions, decisions, etc. to filter the bugs... key to preventing looping, disobeying the user, doing work that is out of scope」。

官方列为开放失败模式：「Agents assume they share state with their children when they don't」；跨 agent 通信「doesn't happen by default, because models haven't been trained in environments where it needed to」。

来源：`https://cognition.com/blog/multi-agents-working`

---

**Manus 的 per-task VM 与生命周期**（confidence: high, vote 3-0）

Manus 官方博客：「Manus Sandbox is a fully isolated cloud virtual machine that Manus allocates for each task」「Each Sandbox runs in its own environment, does not affect other tasks, and can execute in parallel」「A Sandbox is created on demand in a new session」；睡眠/唤醒周期中「the files and data in the Sandbox remain unchanged」；「continuously sleeping Sandbox may be recycled (Free users: 7 days; Manus Pro: 21 days)」。

「per-task not per-turn」是基于 session 级生命周期与 hibernation 描述的合理推断。第三方报道指基础设施由 E2B/Daytona 提供（底层 Firecracker microVM），非 Manus 官方确认。

来源：`https://manus.im/blog/manus-sandbox`

---

**Manus 的文件系统哲学**（confidence: high）

Context Engineering 博客（2025-07-18）：「we treat the file system as the ultimate context in Manus: unlimited in size, persistent by nature, and directly operable by the agent itself」「a document's contents can be omitted if its path remains available in the sandbox」；模型「write to and read from files on demand」；用 `todo.md` 勾选进度。

Sandbox 博客：recycle 后「Manus artifacts, uploaded attachments, and important files such as Slides/WebDev will be restored automatically」，而「intermediate code and temporary files created during execution will not be restored」。

「不依赖独立 DB/checkpoint」为 2-1 票推断。

来源：`https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus` · `https://manus.im/blog/manus-sandbox`

---

**Cursor Cloud Agents 的 Build**（confidence: high, vote 3-0）

Cursor 官方文档（2026-08-19 抓取）：agents「run in isolated VMs in the cloud with full development environments」「Cursor manages VM provisioning, isolation, snapshots, startup, artifacts, and capacity for every Cloud Agent」；Build 是「a bootable snapshot of a prepared Cloud Agent environment」；**「Builds preserve disk state only」**「Running processes, shell exports, and in-memory caches stop when Cursor snapshots the machine」；「Cursor keeps pre-warmed copies of active Builds ready」「removes repository cloning and dependency installation from the agent startup path」。

交接：agent「clone your repo... and work on a separate branch, then push changes to your repo for handoff」；多 repo 时「open pull requests in the repos it changes」。

来源：`https://docs.cursor.com/background/agents` · `https://cursor.com/docs/cloud-agent` · `https://cursor.com/docs/cloud-agent/builds`

---

**Cursor 的并行与触发入口**（confidence: high, vote 3-0）

「You can run as many agents as you want in parallel, and they do not require your local machine to be connected to the internet」；触发入口：Cursor for iOS、cursor.com/agents、Desktop、Slack @cursor、GitHub/Bitbucket 评论、Linear @cursor、API。

「Long-running is not available for multi-repo environments yet」（在 `/docs/cloud-agent` 与 settings 页两处出现）。

「unlimited」是对「as many as you want」的转述，实际可能有配额但文档未列数字上限。

来源：`https://cursor.com/docs/cloud-agent`

---

**Cursor 的 HITL 是实时协作而非 durable gate**（confidence: high, vote 3-0）

文档原文：「Viewing is read-only.」；「Take control of the agent's desktop to test the software yourself in a full development environment without checking out the branch locally. Release control back to the agent for it to keep working.」；「a team admin can enable team follow-ups」；「Cursor also verifies each viewer's repository access... Team membership alone doesn't grant access.」

文档中**无**「pause at checkpoint for approval」、durable wait、turn-by-turn approval 描述。一个 AI 搜索摘要声称有 review checkpoints，但直接读官方文档未找到对应功能。PR Routing & Approval 是完成后的 PR merge 门。

来源：`https://cursor.com/docs/cloud-agent`

---

**E2B 的 pause/snapshot 语义**（confidence: high, vote 3-0）

E2B 官方文档（2026-08-19 抓取）persistence 页：「includes not only state of the sandbox's filesystem but also the sandbox's memory」；恢复后「all running processes, loaded variables, data, etc. will be restored」；resume「approximately 1 second」；pause「approximately 4 seconds per 1 GiB of RAM」；「paused sandboxes are kept indefinitely; there is no automatic deletion or time-to-live limit」「to remove a paused sandbox, you must kill it explicitly」「You can save the sandbox ID in your database to resume the sandbox later」。

snapshots 页：「persistent point-in-time capture of a running sandbox, including both its filesystem and memory state」「One-to-many — snapshot can spawn many new sandboxes」「spawn multiple sandboxes from the same snapshot to explore different approaches in parallel」。

来源：`https://docs.e2b.dev/sandbox/persistence` · `https://docs.e2b.dev/sandbox/snapshots`

---

**E2B 刻意不内置 workflow 层**（confidence: high, vote 3-0）

persistence 页逐字列出 Running/Paused/Snapshotting/Killed 四态及语义；「Sandbox.connect() only ever extends the sandbox's lifetime - the new expiry is the later of the current expiry and now plus the timeout you pass (default 5 minutes)」。

整页**无** Temporal/Cadence/Inngest/Restate、step retry、event sourcing、human-task signal 等概念——E2B 把自己定位为原语，工作流语义由上层产品自建。

来源：`https://docs.e2b.dev/sandbox/persistence`

---

**跨产品综合结论**（confidence: **medium**）

已验证的四家（Devin、Cursor、Manus、E2B）**没有一家在公开材料中使用 Temporal/Cadence/Inngest/Restate/Airflow 作为 agent 步骤的 durable workflow 层**。

主流 archetype：**stateful per-session/per-task VM + hypervisor 或磁盘 snapshot 休眠 + 自建/产品级编排 + git/文件产物交接**。

HITL 建模为活 VM 观察/接管或事后 PR 审批，而非可挂起数周的 durable 审批 gate。扇出靠多 agent spawn（Devin manager/child + 内部 MCP）或 snapshot one-to-many fork（E2B）。

**confidence 降为 medium 的理由**：这是基于公开博客/文档的**缺席论证**——vendors 不公开完整后端栈，Cognition 的编排引擎亦未具名。产品样本只覆盖编码/通用 agent 与一个 sandbox 原语，**未覆盖 OpenAI/Anthropic 第一方 agent 及文档/PPT 类产品**。

来源：四家 primary 来源综合

---

### 教育/B2G 架构建议（分析性推断，非 vendor evidence）

对教育/出版类多步审批 + 多轮编辑 + 教师 gate + B2G 审计合规场景：

编码 agent 模式优化的是「**可丢弃 workspace + 单一 owner 事后 merge**」（git revert 可逆、信任二元），与教育场景的**多角色顺序审批**（教师→编辑→合规→管理员）、跨学期按月计的休眠周期、审计级决策留痕存在结构性错配。

VM snapshot 保存机器状态，不保存可查询、可签名、符合留存策略的**审批台账**；paused-VM 要么无限期留存（E2B，无 TTL）要么定时炸弹式回收（Manus 7/21 天），均不符合政策定义的 records-retention 日程，恢复 snapshot 也无法重放一条可审计的决策链。

Temporal/durable workflow 层在以下条件同时出现多条时才值得引入：
- 等待可能超过 snapshot 留存窗口或须跨基础设施迁移存活
- 多个不同 human role 需顺序批准且决策须独立于 agent 记忆记录
- 监管要求 tamper-evident 的步骤级历史、幂等重试与补偿
- 需要对大量 artifact（多学生文档、多章节）做确定性扇出/扇入

对单一教师 gate + 草稿编辑的轻量场景，数据库里一个状态字段 + sandbox pause/resume 已足够，Temporal 属过度工程。

**confidence: medium** — 这是基于架构事实的分析性推断，被研究产品均不以 K-12/B2G 审批为目标市场，因此不应作为有行业案例背书的 best practice，而应作为设计假设，需在真实教育场景中另行验证。

### Round 2 caveats

1. **产品覆盖严重倾斜**：25 条被验证 claim 只覆盖 Devin（Cognition）、Manus、Cursor Cloud Agents 和 E2B 一个 sandbox 原语。原始问题点名的 OpenAI/ChatGPT Tasks、Operator、Codex cloud agent、Async tasks、GPT-4o computer use，Anthropic Cowork/collaborative agents、Claude.ai Projects/Artifacts、Claude Code background/remote agents、Computer Use，WorkBuddy，以及 Replit Agent、Lovable、Bolt.new、v0、Gamma、Notion AI、Genspark、MultiOn、Browser Use、Daytona、Modal、Cloudflare Sandboxes、Kubernetes pod-per-session 等**均无 claim 存活验证**。因此 archetype 综合描述的是**编码/headless 研究 agent 这一角落**，不能代表全部云端 agent 市场，尤其不能代表文档/PPT canvas 类产品的状态模型
2. **「没有使用 Temporal/durable workflow」是缺席论证**：厂商不公开完整后端栈，Cognition 的编排引擎本身就未具名；Devin/Manus 内部可能使用 Temporal 类系统而未写入博客。该结论应理解为「公开工程叙事中 durable workflow 引擎不是卖点/被讨论对象」，而非「经逆向确认无人使用」
3. **来源多为 vendor 一手工程博客/文档**（权威性高但自带立场）：Cognition 两篇都在论证 microVM 优于容器，其容器安全断言略夸大（gVisor/Kata 等可缓解）；Manus sandbox 页是产品/marketing 页而非工程深潜；E2B 的 1 秒恢复、4 秒/GiB pause 是文档标称值，未在真实负载下独立复测
4. **时效与改名**：blockdiff 博客为 2025-06，Cognition multi-agents 为 2026-04，Cursor/E2B 文档于 2026-08-19 实时抓取；期间 Cursor「Background Agents」已改名为「Cloud Agents」，旧 URL 308 跳转，特性仍在演进
5. **三条 2-1 票 claim 各有小措辞瑕疵**（不影响实质结论）：Devin「进程不存活」是强推断（博客未明说关机，但把运行中回滚列为未解问题）；Manus「FS 是唯一记忆、无独立 DB」是基于文章定位的推断（文章不涉及用户/元数据存储）；Cognition 跨 agent 状态条目中「child 假定与 siblings 共享」方向原文为 manager 假定与 children 共享，但 sibling 协调由 messaging 句独立支撑
6. **教育/B2G 建议段落全部是架构分析推理**，被研究产品无一以 K-12/B2G 多角色审批为目标场景

### Round 2 未解答问题

1. OpenAI（Codex cloud agent、ChatGPT Tasks、Operator/Computer Use）和 Anthropic（Claude Code background/remote agents、Cowork、Computer Use）的第一方 agent 产品到底用什么运行时、snapshot 粒度和 HITL 原语？本轮验证没有任何相关 claim 存活——是公开材料确实稀缺，还是检索/验证阶段漏掉了？
2. 到底有没有主流 agent 产品在生产中使用 Temporal/Cadence/Inngest/Restate（或 Postgres outbox + 状态机）作为 agent 步骤的 durable 层？已验证的四家公开材料里一家都没点名——是行业普遍不用，还是用了但不写进工程博客？若是后者，是什么具体问题（HITL 等待、长时 fan-out、合规重试）把他们推过去的？
3. 针对多角色、长周期审批（教育出版、B2G、金融/医疗合规），业界可参考的 agent + durable 执行参考架构是什么？Temporal 的 Update-with-Start + human-task signal pattern 是否被 agent 团队采用，还是多数团队在 Postgres 上自建状态机？两种路线在 agent 场景下的失败模式对比如何？
4. **PPT/研究报告/canvas 类 agent（Gamma、Genspark、v0、Lovable、Notion AI、Artifacts 式编辑器）在会话间如何持久化「可继续编辑的中间状态」**——是版本化文档模型存数据库，还是像编码 agent 那样靠 workspace 文件 + snapshot？本轮证据几乎全部来自文件系统/git 范式的编码产品，文档-canvas 产品的状态架构是否本质不同（更接近 OT/CRDT + 文档数据库）？**直接外推可能误导教育文档场景的选型。** 这是对 `index.md` 结论威胁最大的未解问题

### Round 2 来源清单

| URL | 质量 | 角度 | claim 数 |
|---|---|---|---|
| `https://cognition.com/blog/what-we-learned-building-cloud-agents` | primary | flagship agent runtime teardowns | 5 |
| `https://cognition.com/blog/blockdiff` | primary | flagship agent runtime teardowns | 5 |
| `https://manus.im/blog/manus-sandbox` | primary | flagship agent runtime teardowns | 5 |
| `https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus` | primary | flagship agent runtime teardowns | 5 |
| `https://docs.cursor.com/background/agents` | primary | flagship agent runtime teardowns | 5 |
| `https://cognition.com/blog/multi-agents-working` | primary | flagship agent runtime teardowns | 5 |
| `https://docs.e2b.dev/sandbox/persistence` | primary | sandbox tech deep dive | 5 |
| `https://docs.e2b.dev/sandbox/snapshots` | primary | sandbox tech deep dive | 5 |
| `https://blog.cloudflare.com/sandboxes/` | unreliable | sandbox tech deep dive | 0 |
| `https://www.daytona.io/docs/sandboxes/snapshots` | primary | sandbox tech deep dive | 5 |
| `https://modal.com/docs/guide/sandbox` | primary | sandbox tech deep dive | 5 |
| `https://github.com/firecracker-microvm/firecracker/blob/main/docs/snapshotting/snapshotting.md` | primary | sandbox tech deep dive | 5 |
| `https://temporal.io/blog/durable-flexible-multi-agent-systems` | primary | durable orchestration | 5 |
| `https://temporal.io/blog/how-temporal-powers-workflows-at-heygen` | blog | durable orchestration | 5 |
| `https://github.com/inngest/agent-kit` | primary | durable orchestration | 5 |
| `https://docs.restate.dev/` | primary | durable orchestration | 5 |
| `https://code.claude.com/docs/en/agent-view` | primary | OpenAI/Anthropic async agents | 5 |
| `https://code.claude.com/docs/en/workflows` | primary | OpenAI/Anthropic async agents | 5 |
| `https://code.claude.com/docs/en/routines` | primary | OpenAI/Anthropic async agents | 5 |
| `https://code.claude.com/docs/en/cloud-environments` | primary | OpenAI/Anthropic async agents | 5 |
| `https://developers.openai.com/api/docs/guides/tools-computer-use.md` | primary | OpenAI/Anthropic async agents | 5 |
| `https://learn.chatgpt.com/docs/cloud` | primary | OpenAI/Anthropic async agents | 5 |
| `https://temporal.io/ai` | primary | contrarian/compliance | 5 |
| `https://news.ycombinator.com/item?id=42753531` | unreliable | contrarian/compliance | 0 |
| `https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/` | primary | contrarian/compliance | 5 |

**注意**：抓取到了 OpenAI/Anthropic 第一方文档页（code.claude.com、developers.openai.com、learn.chatgpt.com），但这些来源的 claim **一条都没能通过验证**——所以虽然页面上有内容，关于它们架构的具体结论仍属空白。这是下一轮调研最该补的口子。

---

## 方法论说明

两轮都用同一套对抗式验证 harness：

1. **Scope**：把问题拆成 5 个互补搜索角度
2. **Search**：5 个并行搜索 agent，每个负责一个角度，返回 novel 结果（去重）
3. **Fetch**：URL 去重后抓取来源，逐条提取**可证伪的 claim**，附带原文引用
4. **Verify**：每条 claim 3 票对抗式验证——2/3 反驳才淘汰。票数记在 claim 上
5. **Synthesize**：合并语义重复，按 confidence 排序，保留来源和票数

**这套 harness 的已知局限**：

- **缺席论证识别不了**：厂商不公开的东西查不到，但查不到 ≠ 不存在。Round 2 的「没人用 Temporal」结论就属于这类
- **覆盖度取决于搜索结果质量**：Round 2 抓到了第一方文档页但 claim 全部未通过验证，说明覆盖度和结论强度是两件事
- **票数 ≠ 真值**：3-0 通过的 claim 仍可能是厂商营销措辞（如「protect against hallucinations」）。票数衡量的是「原文是否支持这个说法」，不是「这个说法是否客观为真」
- **对抗验证会杀掉过度推断，但杀不掉过度保守**：一个正确但原文没直说的 claim 会被驳回（如 Maria 的五阶段 pipeline）；反过来，一个原文直说但本身是营销的 claim 会高票通过
