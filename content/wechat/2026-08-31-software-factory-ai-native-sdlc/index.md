---
title: "Software Factory：AI Native 软件开发流程的新范式"
date: 2026-08-31
topic: software-factory-ai-native-sdlc
source: "../../origin/2026-08-31-software-factory-ai-native-sdlc/index.md"
tags: ["Software Factory", "AI Native", "Coding Agent", "软件开发"]
register: "wechat-longform"
summary: "从四家一线实践，看 Coding Agent 如何进入完整软件开发流程。"
cover: "assets/00-cover-software-factory.png"
wechatStyle: warm-editorial
---

# Software Factory：AI Native 软件开发流程的新范式

![Software Factory 从 Work Item、Task Control Plane、隔离运行、验证、人工 Gate 到交付与反馈的完整流程](assets/00-cover-software-factory.png)

两条 X 帖子用了同一个词。

8 月 12 日，Vercel 说他们为 AI SDK 建了一套 **Software Factory**：每一步由一个 Agent 负责，人类最终合并。运行四周后，Factory 参与编写了最高 35% 的合并 PR，处理了 7 月大部分关闭 issue。

六天后，Warp 发布 **Warp Factories**：可以用代码配置整套 Factory，为不同阶段选择 Claude Code、Codex 或其他 harness，再统一管理权限、运行环境、成本和评测。

同一个 Software Factory，指向的却是两种系统。

Vercel 展示的是一条已经跑在公开仓库上的开发流程；Warp 想提供的是建立和运营这类流程的控制面。再放入 Anthropic 的 AI-Native SDLC Playbook、OpenAI 的 Harness Engineering 和 Symphony，Software Factory 的工程轮廓就清楚了。

这篇文章不讨论“AI 会不会取代程序员”。我们只看一个更具体的问题：

> 当 Coding Agent 已经会读仓库、改代码、跑测试和开 PR，怎样把它接进一条可以长期运行的软件开发流程？

以下分析以 **2026 年 8 月 31 日** 可查到的官方材料、公开仓库与运行记录为准；文中的效率数字仍按公司第一方数据理解。

## 同时运行更多 Agent，还不是 Factory

先区分四个容易混淆的东西。

![从交互式 Coding Agent、Background Agent、Orchestrator 到 Software Factory，系统逐步补齐异步运行、调度和完整生命周期](assets/10-four-levels.png)

**Coding Agent** 以一次 Session 为中心。你给 Claude Code 或 Codex 一个任务，它在当前仓库里查找、修改、测试。

**Background Agent** 可以离开你的电脑持续运行。你关掉终端，任务仍在云端继续。

**Orchestrator** 管理多个 Run：哪个任务先执行、最多并行几个、失败何时重试、卡住多久算超时。

**Software Factory** 再往外一层。它把“让 Agent 开始工作”扩展成完整生命周期：任务进入系统，经过规格、实现、验证和审核，最后交付并回收反馈。

最简单的判断方法是：Agent 进程退出以后，任务还在不在？

如果任务状态、失败原因和下一步只存在于聊天窗口或某个工程师脑子里，那么它还是 Agent 工具，不是 Factory。

## 一条任务在 Factory 里怎样流动

四家公司的流程名称不同，主干却很接近：

![Software Factory 从 Work Item 开始，经过分诊、规格、风险 Gate、隔离执行、验证、人工审批和反馈闭环](assets/11-unified-lifecycle.png)

### 先判断问题是不是真的

入口可能是一条 GitHub issue、一份产品想法、Linear ticket，也可能是线上告警。

Agent 不能看到一条 issue 就直接改代码。它首先要判断：信息是否完整？问题能不能复现？请求是否符合项目方向？风险有多高？

如果信息不足，正确结果是提问并暂停；如果 issue 的前提不成立，正确结果是保存反证并停止，而不是为了交差硬改几行代码。

### Spec 要先于实现

进入执行前，系统要生成 Spec、Plan 和验收标准。这些 artifact 为后面的 Reviewer 提供验证参照，并不负责规定每一行代码怎么写。

没有验收标准，Review 只能判断“代码看起来像不像那么回事”；有了验收标准，才能判断它是否完成了原始任务。

### Run 要在隔离环境里执行

每次实现发生在独立 Workspace 或 Sandbox：自己的代码 checkout、依赖、进程、测试数据库、浏览器和有限凭据。

这能防止两个 Agent 相互覆盖文件，也避免无人值守 Agent 继承开发者电脑上所有已登录系统的权限。

### 验证要看实际结果

“我已经修改完成，所有测试通过”只是 Agent 的自述。

Verifier 应该读取真实 diff、checkout 实际分支、运行仓库自己的测试，必要时启动应用，查看 UI、日志和指标。Reviewer 最好不要继承 Implementer 的完整 reasoning，避免两者沿着同一个错误前提继续自洽。

### 最后由 Gate 决定是否继续

文档修正可以自动准备 draft PR；公共 API 变更必须等待 Maintainer；生产部署可能需要命名授权；无人值守任务不应该拥有 merge 工具。

这些限制必须由 tool surface 和运行时 policy 强制，不能停在 prompt 里的一句“请谨慎操作”。

## 四家公司分别补上哪一层

![Anthropic、Vercel、Warp 与 OpenAI 分别从流程方法、公开案例、Factory 控制面和调度状态切入](assets/20-four-practices-map.png)

### Anthropic：用 Artifact 串起完整 SDLC

Anthropic 的 AI-Native SDLC Playbook 把传统的 Plan、Design、Build、Test、Deploy、Maintain 从线性阶段改成循环。

![Anthropic 对比传统线性 SDLC 与 AI Native 循环式 SDLC](assets/12-anthropic-ai-native-sdlc.png)

Playbook 没有在每个阶段里各塞一个 Claude。它要求每一步都生成下游可以直接消费的文件：

- 想法整理成 `intent.md`；
- 需求和设计写成 `spec.md`；
- 实现方案写成 `plan.md`；
- 测试和 eval 贯穿实现；
- PR、审批和发布形成审计记录；
- 生产指标异常时，再生成新的 intent。

`CLAUDE.md` 保存仓库工作知识，Skills 保存可复用流程，Hooks 负责确定性的权限和审批。修改这些 Agent 配置时，也要像修改代码一样跑回归 eval。

### Vercel：公开 issue 真的穿过了 Factory

Vercel AI SDK Factory 的优势在于可以通过公开仓库抽样验证。

![Vercel AI SDK Factory 将 Issue 按 Bug、Feature 和 Documentation 分流，并由独立 Agent 复现、实现、审核和回移植](assets/13-vercel-ai-sdk-factory.png)

例如 AI SDK 的 issue #17898 请求增加 blocked-domain 支持。Factory 先运行 probe，证明主分支确实缺少这个功能；再生成 Spec、实现代码、运行真实 web search 验证、创建 PR；人类合并后，Factory 又把修改 backport 到 v6 和 v5。

这条链路里，不同 Agent 分别负责分类、分析、实现和审核。长 Spec 通过 artifact 交接，不必让每个 Agent 共享同一段越来越长的聊天历史。无人值守流程最多创建 draft PR，merge 根本不在工具列表里。

### Warp：把 Factory 做成可配置基础设施

Warp 的方向是 Factory-as-code。

仓库、Agent 角色、模型、harness、Skills、MCP、权限和触发器都进入版本控制。修改 Reviewer 模型或收紧权限，可以像基础设施变更一样 review、canary 和 rollback。

Warp 还把 Factory Agent、Scorer 和 Improver 分开：执行 Agent 做任务，Scorer 按成本和质量评分，Improver 再提出对模型路由、prompt 或 Skill 的修改。

这里的“自改进”仍然是一条受控变更流程：反馈进入评分，Improver 产生 diff，回归任务集验证，最后由人审核合并；Agent 不会私下重写自己。

### OpenAI：让人管理 Task，而不是盯着 Session

OpenAI Symphony 的起点是一个很现实的问题：多数工程师同时管理三到五个 Agent Session 后，context switching 就开始抵消效率提升。

Symphony 让 Linear issue 成为控制面。工程师管理任务，Orchestrator 负责启动 Session、创建 Workspace、限制并发、检测 stall、停止不再 eligible 的 Run，并在失败后重试。

![Task 持有目标与状态，一项 Task 可以经历多个 Run Attempt、Agent Session 和 Workspace，最终由 Artifact 支撑 Gate 与 Handoff](assets/14-task-run-state.png)

这里最重要的区分是：

- **Task** 保存目标、状态、风险和验收标准；
- **Run Attempt** 是一次执行尝试；
- **Session** 是某个 Agent 的具体上下文；
- **Workspace** 保存执行环境和副作用；
- **Artifact** 保存 Spec、Plan、diff、测试与回执。

Agent 进程正常退出，不代表 Task 已经完成。它可能只是把任务推进到 `Human Review`，也可能只完成调查，没有生成任何代码。

## 一套 Factory 至少有哪些组件

![Software Factory 由入口、任务控制面、流程策略、路由、Agent Runtime、Workspace、Artifact、验证 Gate 与评测改进九部分组成](assets/21-nine-components.png)

这张图也解释了为什么“换一个更强模型”不能自动得到 Software Factory。

模型主要工作在 Agent Runtime 这一格。它周围还需要任务状态、权限策略、隔离环境、Artifact、验证、恢复和评测。缺少任何一层，Demo 即使成功，系统仍可能在长期运行中失控。

## 目前仍然没解决的问题

Software Factory 已经能承担真实任务，但远没有成为成熟标准。

**错误 Spec 会被更快放大。** 无人值守流程会沿着错误方向继续生成代码、测试和 Review，因此 clarify、reject premise 和 human judgment 必须是一等状态。

**实现与验证可能共享同一个错误。** 同一个 Agent 写实现、写测试、解释为什么测试通过，很容易形成自洽循环。独立上下文、不同模型和确定性检查只能降低风险，不能替代真正的测试 oracle。

**Review backlog 仍然存在。** 如果 Agent 生成 PR 的速度超过团队吸收速度，Factory 只是把 backlog 从 issue 列表搬到 review queue。

**外部副作用比 Git 难恢复。** Branch 可以丢弃，数据库迁移和外部 API 写操作不一定可逆。超时后不知道动作是否成功时，需要幂等键、回执和“结果未知”状态，不能直接重试。

**Factory 配置也会退化。** Prompt、Skill、模型路由和权限都是新的软件供应链，需要 owner、版本、回滚和 regression eval。

## 普通团队如何开始

![普通团队从仓库可读、单一低风险流程、Artifact、恢复语义到 Eval 指标的五步落地路径](assets/22-adoption-ladder.png)

第一条流程可以是 backport、依赖升级、文档同步、issue triage，或者有稳定测试覆盖的低风险 bug。不要一开始就挑战跨仓库架构调整和生产数据库迁移。

至少记录这些指标：

- 可审核结果的成功率，而不是进程正常退出率；
- 每个被接受任务的成本；
- 人工介入次数和等待时间；
- 一次通过率与修改轮数；
- 重试、放弃和结果未知比例；
- 合并后的返工、回滚与 escaped defect。

当某种失败反复出现，再把它变成工具、环境、Skill、Hook 或 eval。先跑通一条真实流程，再扩大自动化边界。

## Software Factory 还不是标准产品类别

Software Factory 尚未形成统一标准，产品边界也还在变化。

Anthropic 提供了完整的 AI Native SDLC 流程语言；Vercel 展示了公开仓库中的生产实践；Warp 将它产品化成可配置控制面；OpenAI 则把 Task、Run、Workspace、重试和恢复写进 Orchestrator 规范。

这些实践还不足以支撑“自动经营复杂软件产品”，却已经把问题从“Agent 能写多少代码”推进到“任务状态、执行环境、验证、权限、失败和反馈如何落到系统里”。

当这些缺口被写成可观察的状态、可执行的策略和可复核的证据，Software Factory 才从宣传词变成工程系统。

## 资料与延伸阅读

### 核心材料

- Anthropic：The AI-Native SDLC Playbook — https://claude.com/blog/the-ai-native-sdlc-playbook
- Anthropic / Warp：How Warp builds self-improving agents on Claude — https://claude.com/blog/how-warp-builds-self-improving-agents-on-claude
- Vercel：Building a software factory for AI SDK — https://vercel.com/blog/building-a-software-factory-for-ai-sdk
- Vercel Labs：eve Software Factory Template — https://github.com/vercel-labs/eve-software-factory-template
- Warp：Introducing Warp Factories — https://www.warp.dev/blog/open-infrastructure-for-building-a-software-factory
- Warp：Closing the loop with self-improving cloud software factories — https://www.warp.dev/blog/agent-self-improving-software-factories
- OpenAI：Harness engineering — https://openai.com/index/harness-engineering/
- OpenAI：Symphony — https://openai.com/index/open-source-codex-orchestration-symphony/
- OpenAI：Symphony SPEC.md — https://github.com/openai/symphony/blob/main/SPEC.md

### 补充案例

- Ramp：Why We Built Our Own Background Agent — https://engineering.ramp.com/post/why-we-built-our-background-agent
- Spotify：What we've learned scaling AI coding agents — https://portal.spotify.com/blog/introducing-xirp
- GitHub：About GitHub Agentic Workflows — https://docs.github.com/en/copilot/concepts/agents/about-github-agentic-workflows
- GitHub：Agentic Engineering System — https://github.com/resources/insights/agentic-engineering-system
- DORA：State of AI-assisted Software Development 2025 — https://dora.dev/research/2025/dora-report/
