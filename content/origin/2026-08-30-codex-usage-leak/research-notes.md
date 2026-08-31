# Research Notes：Codex 隐形用量泄漏

研究日期：2026-08-30（Asia/Shanghai）

Codex 源码基线：`/Users/eriklee/code/coding-agent/codex`，`main@88f776588f5e73467e7659c268f8358a9a2378b6`。

本文只读分析该仓库。研究期间仓库工作区干净，没有自动 pull，也没有修改源码。

## 一手来源

1. Tibo Sottiaux，2026-08-29：[Codex usage limits update](https://x.com/thsottiaux/status/2093801758665715784)。这是八类问题、10%～50%、15%～70%、约五分之一、15000 次检查等数字的唯一直接来源。
2. OpenAI Docs：[GPT-5.2 compaction guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2)。官方把 compaction 定义为长会话的 loss-aware compression，并建议在里程碑而不是每一轮执行。
3. OpenAI API Reference：[Compact a response](https://developers.openai.com/api/reference/java/resources/responses/methods/compact)。返回对象包含 compacted items 和本次 compaction 的 token usage。
4. OpenAI Developer Community：[Codex Community](https://developers.openai.com/community)。只用于说明用户侧对长任务、compaction 和额度的体验，不证明实现。
5. OpenAI Codex GitHub：本文列出的 PR、当前源码和回归测试。

## 社区问题报告（体验证据）

- [#24388：remote compaction deadlocks when input_image payloads remain](https://github.com/openai/codex/issues/24388)。报告展示了历史 `input_image` 进入 replacement history 后，再次触发超限与压缩失败的循环。它是公开用户报告，不等于 OpenAI 对根因的官方确认，但与 retained-image budgeting 的修复方向一致。
- [#34095：repeated auto-compaction degrades execution frontier](https://github.com/openai/codex/issues/34095)。报告记录 24 次 compaction 后任务不断回到相似“最后步骤”，适合作为“能记住事实但失去收敛边界”的案例。
- [#41220：abnormal usage/quota depletion tracker](https://github.com/openai/codex/issues/41220)。汇总多类异常用量报告，只用于说明用户为何开始怀疑后台工作和用量归集，不使用其中未经核验的换算数字。
- [OpenAI Developer Community：20 Million+ Codex users reset thread](https://community.openai.com/t/20-million-codex-users-a-free-banked-reset-for-everyone/1391683/11)。保留了 Tibo 在 8 月 23 日对图片多次压缩、Computer History p95+ 和标题生成消耗的早期说明。

## 八项修复的证据矩阵

| 修复项 | 证据 | 代码锚点 | 结论边界 |
| --- | --- | --- | --- |
| Compaction | PR [#40280](https://github.com/openai/codex/pull/40280)、[#40994](https://github.com/openai/codex/pull/40994)、[#41003](https://github.com/openai/codex/pull/41003) | `compact_remote_v2_images.rs:15-99`；`compact_remote_v2.rs:589-682` | **A**：图片被纳入 retained-message token budget，图片及标签按原子组处理，从新到旧保留，超预算停止回填。10% 是 Tibo 的生产统计，不由单元测试证明。 |
| Memory | PR [#40587](https://github.com/openai/codex/pull/40587) | `hooks/src/events/stop.rs:41-93`；`core/src/hook_runtime.rs`；`memories/write/src/phase2.rs` | **A**：`MemoryConsolidation` 使用独立 Stop target，排除 user/project/session/plugin hooks，只保留 managed policy 与 executor cleanup。15000 次是事故样本，不在代码里。 |
| Goals | PR [#41454](https://github.com/openai/codex/pull/41454)、[#40628](https://github.com/openai/codex/pull/40628)、[#41562](https://github.com/openai/codex/pull/41562)、[#41183](https://github.com/openai/codex/pull/41183) | `ext/goal/src/accounting.rs:102-205`；`extension.rs:274-305`；`runtime.rs:268-315` | **A**：成功工具调用清零失败计数；默认 `exec` 连续失败三轮后把 goal 置为 blocked；descendant token 计入根目标。15%～70% 是 Tibo 的生产样本。 |
| Automations | 当前仓库仅公开 schedule schema、thread source 与本地 automation gate | `app-server-protocol/.../plugin.rs:724-773`；`features/src/lib.rs:240-243` | **C**：可以确认支持 hourly/daily/weekdays/weekly 描述，但不能看到真正触发任务的 scheduler，因此不能解释“为什么执行得更频繁”的具体修复。 |
| Subagents | PR [#41308](https://github.com/openai/codex/pull/41308)、[#41183](https://github.com/openai/codex/pull/41183) | `agent/control/service_tier.rs:1-17`；`agent/control/spawn.rs:418`；`multi_agents_v2/spawn.rs:123-145` | **A/B**：root service tier 由整棵 Agent tree 共享，覆盖存量/新子 Agent 与 compaction；小模型擅自选择更强 helper 的完整选择策略没有在同一提交中直接出现。 |
| Computer History | Tibo 公告与社区体验 | 当前仓库无完整 Computer History 采集、窗口去重或摘要实现 | **C**：只能讨论“重叠历史反复摘要”这一 failure mode，不能声称知道 OpenAI 的具体去重算法。 |
| Rolling summaries | Tibo 说旧 rolling task summaries 已禁用；当前仓库另有 PR [#40705](https://github.com/openai/codex/pull/40705) | `tui/src/app/recap.rs:33-38,464-613` | **B/C**：TUI recap 是相邻但不能证明相同的机制。它至少三次 completed turns、距离上次两轮、失焦三分钟才触发，并带 revision、retry 和 single-flight 状态。 |
| MCP | PR [#40737](https://github.com/openai/codex/pull/40737)、[#41421](https://github.com/openai/codex/pull/41421) | `protocol/src/models.rs:2243-2384`；`core/src/tools/context.rs:150-179`；`config/src/mcp_types.rs` | **A/B**：非结构化 MCP content 转成 typed content items；structured content 只序列化一次；history 使用独立 token budget。工具说明截断后重取的完整路径没有在这两个提交里直接证明。 |

## 关键实现摘要

### 1. Retained image budgeting

`content_item_token_count` 不再把图片当作零成本内容，而是通过 `estimate_image_bytes` 估算，再折算成近似 token。`truncate_message_to_token_budget` 从消息尾部向前处理，把图片和相邻 harness 标签视为一个不可拆分的组。

外层 `truncate_retained_messages` 同样从最新 history group 向旧 history group 迭代。一个图片组装不下时，代码把剩余预算归零，避免丢掉当前边界后又回填更旧消息。这解决的不只是“少带一张图”，而是 replacement history 的边界稳定性。

### 2. Memory consolidation Stop scope

普通 session 的 Stop hook 回答“用户任务能否结束”；memory consolidation 的 Stop hook 回答“内部维护任务能否结束”。旧问题本质是把这两个生命周期混在一起。

新 `StopHookTarget::MemoryConsolidation` 明确排除来自 User、Project、SessionFlags 和 Plugin 的 handler；System、MDM、CloudRequirements 等 managed policy 仍保留，executor cleanup 也会运行。隔离的不是安全策略，而是项目级“任务完成了吗”检查与用户通知。

### 3. Goal failure circuit breaker

Goal accounting 只把已实际进入 handler 的默认 `exec` 失败记为 execution failure。任意成功工具调用会清零失败计数。相同 goal 连续三轮满足“没有成功工具 + exec 失败”后，runtime 使用 `ExecutionUnavailable` 把目标置为 `Blocked`。

这一设计避免单次偶发错误过早终止，也避免模型在执行宿主坏掉时无限 continuation。子 Agent token 进入 root accounting，意味着目标预算开始覆盖完整委派树，而不只覆盖根线程。

### 4. Root-owned service tier

`AgentControl` 保存 root-owned service tier；spawn/reload 时子 Agent 读取这一值，V2 spawn 不再接受 per-spawn service tier 覆盖。角色配置仍能锁定 model/reasoning，但不能私自把路由切到 Fast/Priority。

这是典型的层级策略：模型与推理强度属于子任务能力选择，service tier 属于用户在根任务上选择的成本/延迟策略。

### 5. MCP representation and budget

旧路径可能把整个 MCP content array 序列化成文本；现在 text/image/audio/encrypted content 被转换为对应的 `FunctionCallOutputContentItem`。只有 `structured_content` 存在且非空时才序列化该结构化对象。

MCP 输出在进入 history 前应用 token budget，并保留约 20% 的 serialization allowance；Code Mode 仍可得到 raw result。它把“机器处理的原始结果”和“再次送入模型上下文的表示”分开。

## Focused test results

执行日期：2026-08-31。

目标测试：

- `codex-core`: `image_only_boundary_is_atomic_and_does_not_backfill_older_messages`
- `codex-hooks`: `memory_consolidation_stop_preserves_policy_and_executor_cleanup`
- `codex-goal-extension`: `execution_failures_do_not_transfer_to_a_replacement_goal`
- `codex-core`: `root_service_tier_change_updates_existing_subagent` 的 3 个参数化用例
- `codex-protocol`: `converts_unstructured_mcp_content_to_items`

第一次直接运行 nextest：4 个用例通过，3 个 subagent service-tier 用例因为测试线程 stack overflow 被 `SIGABRT` 终止，最终退出码 100。它们不是 assertion failure。

仓库根 `justfile` 的标准测试配置设置 `RUST_MIN_STACK=8388608` 与 `NEXTEST_PROFILE=local`。使用相同设置重新运行全部目标用例：

```text
Summary [0.931s] 7 tests run: 7 passed, 4489 skipped
exit code: 0
```

构建阶段存在一条与本文目标无关的 warning：`core/tests/suite/openai_file_mcp.rs` 有 unused import `wiremock::matchers::body_json`。没有修改源码或运行 `cargo fix`。

## 写作时必须保留的限定

- “修复了”来自 Tibo；“开源代码展示了相同/相邻的机制”来自本地源码。两者不能自动画等号。
- 当前源码晚于部分事故发生时间，只能用 commit/PR 时间建立演进关系，不能证明每一项已经部署到所有产品表面。
- `Computer History`、automation scheduler 与旧 rolling summaries 的生产实现不在当前仓库。
- 社区 issue 是具名、可复核的用户报告，不是总体样本。
