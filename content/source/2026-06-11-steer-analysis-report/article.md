---
title: "Agent 实时干预机制深度拆解：从 Codex Steer 到全生态 Steering 范式演进"
description: "从 Codex Steer 的协议级实时注入到 Hermes 的工具结果伪装，拆解 Agent 实时干预（Steering）的实现差异、范式转移与全生态能力全景。"
pubDate: 2026-06-11
updatedDate: 2026-06-11
tags:
  - Agent
  - Codex
  - Steering
  - Human-in-the-Loop
  - Agent 架构
draft: false
wechatStyle: agent-flow
---

# Agent 实时干预机制深度拆解：从 Codex Steer 到全生态 Steering 范式演进

> **版本**: v1.1  
> **日期**: 2026-06-11  
> **范围**: Codex v0.139.0 + Hermes Agent v0.16.0 + OpenClaw + Pi + Manus + Claude Code  
> **分类**: Agent 架构 / 实时控制 / Human-in-the-Loop  
> **Steer 功能上线**: Codex CLI v0.98.0 (2026/02/06), commit [openai/codex#10690](https://github.com/openai/codex/pull/10690)

---

![封面](assets/cover.png)

---

## 目录

1. [问题背景：Agent 为什么需要 Steering](#1-问题背景agent-为什么需要-steering)
2. [Codex Steer：协议级实时注入](#2-codex-steer协议级实时注入)
3. [Hermes Agent Steer：应用级工具结果追加](#3-hermes-agent-steer应用级工具结果追加)
4. [架构对比](#4-架构对比)
5. [实现深度剖析](#5-实现深度剖析)
6. [范式转移与交互语义](#6-范式转移与交互语义)
7. [全 Agent 生态 Steering 能力全景](#7-全-agent-生态-steering-能力全景)
8. [未来方向](#8-未来方向)

---

## 1. 问题背景：Agent 为什么需要 Steering

### 1.1 同步 Turn 陷阱

![Codex Steer UI](assets/codex-steer-ui-screenshot.png)

*图 0：Codex Steer 功能在 UI 中的真实呈现 —— 当 Agent 正在处理一个任务时，用户可以在输入框中追加 "wait i meant REWRITE" 并点击 **Steer** 按钮，将这个新意图注入到当前正在执行的 turn 中，而不需要等待当前轮次完成。图片来源：OpenAI Academy — [Working with Codex](https://openai.com/academy/working-with-codex/)。*



传统的对话式 AI 基于 **turn-based model（回合制模型）**：用户发送输入 → 模型处理 → 模型响应 → 用户等待完成后再发送下一条。这种模式继承自聊天机器人界面，但在应用到长时间运行的 Agent 任务时会灾难性地崩溃。

想象一下 Codex Agent 正在执行一次多步重构：

```
用户: "把 auth 模块重构为使用 JWT"
[Agent 开始执行: 1. 读取文件 → 2. 分析依赖 → 3. 规划修改 → 4. 应用 patch → 5. 运行测试]

用户（5 分钟后，看着 Agent 走向错误方向）: "停下！别碰 OAuth2 流程，只改 session manager！"
[用户必须等待当前 turn 完成，或者发出硬中断]
```

根本性的不对称：**人类认知是中断驱动的（interrupt-driven），而 Agent 执行是批处理驱动的（batch-driven）**。当 Agent 运行数分钟（甚至数小时）时，用户对任务的认知模型会实时演化，但 Agent 的执行上下文在 turn 启动的那一刻就被冻结了。

### 1.2 Steering Gap（干预缺口）

三种具体的失败模式由此产生：

![Steering Gap 示意](assets/batch-vs-streaming-model.png)

*图 1：批处理模型 vs 流式模型 —— Steering 打破了传统的回合制边界，允许在 Agent 执行期间实时注入用户意图。*

| 失败模式 | 描述 | 示例 |
|---------|------|------|
| **方向漂移（Direction Drift）** | Agent 误解意图，走向错误路径 | "实现缓存" → Agent 开始加 Redis，但用户指的是内存 LRU |
| **上下文滞后（Context Lag）** | 执行过程中新信息出现，但无法被纳入 | 用户在终端看到错误信息，但 Agent 还没注意到 |
| **范围蔓延（Scope Creep）** | Agent 将工作扩展到预期边界之外 | "修这个 bug" → Agent 开始重构整个模块 |

"Steer" 机制通过允许 **异步用户输入注入到正在执行的 turn 中**，同时解决了这三个问题。

---

## 2. Codex Steer：协议级实时注入

### 2.1 协议接口

![Codex Steer 流程](assets/codex-steer-flow.png)

*图 3：Codex Steer 协议流程 —— 从 Client 的 `turn/steer` 请求到 Session 状态机的完整处理链路，展示了乐观并发守卫和 Turn 类型验证的关键节点。*

Codex 通过一个一等公民的 JSON-RPC 协议方法暴露 steering：

```rust
// codex-rs/app-server-protocol/src/protocol/common.rs:771-775
TurnSteer => "turn/steer" {
    params: v2::TurnSteerParams,
    inspect_params: true,
    serialization: thread_id(params.thread_id),
    response: v2::TurnSteerResponse,
}
```

`TurnSteerParams` 携带的参数：

```rust
pub struct TurnSteerParams {
    pub thread_id: String,
    pub client_user_message_id: Option<String>,
    pub input: Vec<UserInput>,           // 实际的 steer 内容
    pub additional_context: Option<HashMap<String, AdditionalContextEntry>>,
    pub expected_turn_id: String,        // 安全检查
    pub responsesapi_client_metadata: Option<HashMap<String, String>>,
}
```

**关键设计决策**：`expected_turn_id` 充当**乐观并发守卫（optimistic concurrency guard）**。客户端声明它认为哪个 turn 是活跃的；如果服务端不同意（turn 已完成，或不同的 turn 活跃），steer 会被拒绝并返回 `ExpectedTurnMismatch`。

### 2.2 请求处理流程

App Server 的 `turn_steer_inner` 方法实现了网关逻辑：

```rust
// codex-rs/app-server/src/request_processors/turn_processor.rs:782-889
async fn turn_steer_inner(
    &self,
    request_id: &ConnectionRequestId,
    params: TurnSteerParams,
) -> Result<TurnSteerResponse, JSONRPCErrorError> {
    // 1. 加载并验证 thread
    let (_, thread) = self.load_thread(&params.thread_id).await?;
    self.ensure_direct_input_allowed(request_id, thread.as_ref()).await?;

    // 2. 验证 turn ID 不为空
    if params.expected_turn_id.is_empty() {
        return Err(invalid_request("expectedTurnId must not be empty"));
    }

    // 3. 验证输入大小限制
    if let Err(error) = Self::validate_v2_input_limit(&params.input) {
        return Err(error);
    }

    // 4. 映射输入并转发到核心 thread
    let mapped_items: Vec<CoreInputItem> = params.input.into_iter().map(V2UserInput::into_core).collect();
    let additional_context = map_additional_context(params.additional_context);

    let turn_id = thread
        .steer_input(mapped_items, additional_context, Some(&params.expected_turn_id), ...)
        .await
        .map_err(|err| {
            // 详细的错误分类，用于分析
            let (message, data, error_type) = match err {
                SteerInputError::NoActiveTurn(_) => (...),
                SteerInputError::ExpectedTurnMismatch { expected, actual } => (...),
                SteerInputError::ActiveTurnNotSteerable { turn_kind } => (...),
                SteerInputError::EmptyInput => (...),
            };
            ...
        })?;
    Ok(TurnSteerResponse { turn_id })
}
```

### 2.3 核心 Session 状态机

Codex steering 的核心是 session 的 `steer_input` 方法：

```rust
// codex-rs/core/src/session/mod.rs:3240-3313
pub async fn steer_input(
    &self,
    input: Vec<UserInput>,
    additional_context: BTreeMap<String, AdditionalContextEntry>,
    expected_turn_id: Option<&str>,
    client_user_message_id: Option<String>,
    responsesapi_client_metadata: Option<HashMap<String, String>>,
) -> Result<String, SteerInputError> {
    let mut active = self.active_turn.lock().await;
    let Some(active_turn) = active.as_mut() else {
        return Err(SteerInputError::NoActiveTurn(input));
    };

    let Some(active_task) = active_turn.task.as_ref() else {
        return Err(SteerInputError::NoActiveTurn(input));
    };
    let active_turn_id = &active_task.turn_context.sub_id;

    // 并发守卫：expected turn 必须匹配 actual
    if let Some(expected_turn_id) = expected_turn_id
        && expected_turn_id != active_turn_id
    {
        return Err(SteerInputError::ExpectedTurnMismatch {
            expected: expected_turn_id.to_string(),
            actual: active_turn_id.clone(),
        });
    }

    // Turn 类型守卫：不是所有 turn 都可以 steer
    match active_task.kind {
        crate::state::TaskKind::Regular => {}
        crate::state::TaskKind::Review => {
            return Err(SteerInputError::ActiveTurnNotSteerable {
                turn_kind: NonSteerableTurnKind::Review,
            });
        }
        crate::state::TaskKind::Compact => {
            return Err(SteerInputError::ActiveTurnNotSteerable {
                turn_kind: NonSteerableTurnKind::Compact,
            });
        }
    }

    if input.is_empty() {
        return Err(SteerInputError::EmptyInput);
    }

    // 将 additional context 合并到 session 状态
    let additional_context_input = {
        let mut state = self.state.lock().await;
        state.additional_context.merge(additional_context)
    };

    // 更新 turn 元数据
    if let Some(responsesapi_client_metadata) = responsesapi_client_metadata {
        active_task.turn_context.turn_metadata_state
            .set_responsesapi_client_metadata(responsesapi_client_metadata);
    }

    // 构建 pending input queue 并注入
    let mut pending_input = additional_context_input
        .into_iter()
        .map(ResponseItem::from)
        .map(TurnInput::ResponseItem)
        .collect::<Vec<_>>();
    pending_input.push(TurnInput::UserInput {
        content: input,
        client_id: client_user_message_id,
    });
    self.input_queue
        .extend_pending_input_and_accept_mailbox_delivery_for_turn_state(
            active_turn.turn_state.as_ref(),
            pending_input,
        )
        .await;
    Ok(active_turn_id.clone())
}
```

**关键洞察**：Codex 的 steering **深度集成在 session 状态机中**。输入不仅仅是追加到消息缓冲区——它以 `TurnInput::UserInput` 和 `TurnInput::ResponseItem` 的形式进入 `input_queue`，成为活跃 turn 的 pending mailbox 的一部分。这意味着模型会在它的**下一次迭代**中看到 steer，而不是在当前 turn 完成后。

### 2.4 Goal Extension 系统

Codex 超越了简单的消息注入，通过 Goal extension 提供**语义 steering 模板**：

```rust
// codex-rs/ext/goal/src/steering.rs
pub(crate) fn budget_limit_steering_item(goal: &ThreadGoal) -> ResponseItem {
    goal_context_input_item(budget_limit_prompt(goal))
}

pub(crate) fn objective_updated_steering_item(goal: &ThreadGoal) -> ResponseItem {
    goal_context_input_item(objective_updated_prompt(goal))
}

pub(crate) fn continuation_steering_item(goal: &ThreadGoal) -> ResponseItem {
    goal_context_input_item(continuation_prompt(goal))
}
```

这些生成结构化的 prompts，例如：

```markdown
<!-- goals/continuation.md -->
目标是：{{objective}}
已使用的 tokens：{{tokens_used}} / {{token_budget}}
剩余 tokens：{{remaining_tokens}}

继续朝着目标工作。如果剩余的 token budget 不足以完成任务，
请总结已完成的工作和剩余的部分，然后停止。
```

这是**带语义感知的 steering**——系统不仅仅注入原始用户文本；它可以注入结构化、模板化的引导，保持叙事连贯性。

### 2.5 错误分类体系

Codex 为 steering 定义了精确的错误层级：

```rust
#[derive(Debug, PartialEq)]
pub enum SteerInputError {
    NoActiveTurn(Vec<UserInput>),                           // 没有运行的 turn
    ExpectedTurnMismatch { expected: String, actual: String }, // 竞态条件
    ActiveTurnNotSteerable { turn_kind: NonSteerableTurnKind }, // Review/Compact turn
    EmptyInput,                                             // 验证失败
}
```

每个错误同时映射到用户可见消息和分析事件：

```rust
SteerInputError::ActiveTurnNotSteerable { turn_kind } => {
    let error = TurnError {
        message: "cannot steer a review turn".to_string(),
        codex_error_info: Some(CodexErrorInfo::ActiveTurnNotSteerable {
            turn_kind: turn_kind.into(),
        }),
        additional_details: None,
    };
}
```

---

## 3. Hermes Agent Steer：应用级工具结果追加

### 3.1 设计哲学

Hermes Agent 采用了不同的方法。与其将 steering 构建到协议级状态机中，它将其作为 Python Agent 循环内的**应用层消息操作**来实现。

### 3.2 基于锁的 Pending 缓冲区

核心是一个简单的带锁字符串缓冲区：

```python
# run_agent.py:2379-2413
class AIAgent:
    def __init__(self, ...):
        # 在 __init__ 中初始化
        self._pending_steer: Optional[str] = None
        self._pending_steer_lock: threading.Lock = threading.Lock()

    def steer(self, text: str) -> bool:
        """
        将用户消息注入到下一个 tool result 中，而不中断执行。

        与 interrupt() 不同，这不会停止当前 tool call。
        文本被暂存，Agent 循环在当前 tool batch 完成后
        将其追加到最后一个 tool result 的内容中。
        """
        if not text or not text.strip():
            return False
        cleaned = text.strip()
        with self._pending_steer_lock:
            if self._pending_steer:
                self._pending_steer = self._pending_steer + "\n" + cleaned
            else:
                self._pending_steer = cleaned
        return True

    def _drain_pending_steer(self) -> Optional[str]:
        """返回 pending 的 steer 文本（如果有的话）并清空槽位。"""
        with self._pending_steer_lock:
            text = self._pending_steer
            self._pending_steer = None
            return text
```

**关键差异**：Hermes 将 steer 文本存储在**原始字符串缓冲区**中，而不是结构化的输入项。没有 turn ID 验证，没有状态机集成，没有协议序列化。

### 3.3 投递机制：工具结果伪装

![Hermes Tool Result Masquerading](assets/hermes-tool-result-masquerading.png)

*图 4：Tool Result Masquerading —— 展示了 Hermes 如何将用户 steer 伪装成 tool 输出的一部分，通过 `[USER STEER]` 标记注入到最后一个 tool message 中，从而绕过 role alternation 限制。*

关键实现在 `apply_pending_steer_to_tool_results` 中：

```python
# agent/agent_runtime_helpers.py:2371-2432
def apply_pending_steer_to_tool_results(agent, messages: list, num_tool_msgs: int) -> None:
    """将任何 pending 的 /steer 文本追加到本 turn 的最后一个 tool result。

    在 tool-call batch 结束时调用，在下一个 API 调用之前。
    steer 被追加到 role:"tool" 消息的内容中，
    并带有清晰的标记，以便模型理解它来自用户而非 tool 本身。
    """
    if num_tool_msgs <= 0 or not messages:
        return
    steer_text = agent._drain_pending_steer()
    if not steer_text:
        return

    # 在最近的尾部中找到最后一个 tool-role 消息
    target_idx = None
    for j in range(len(messages) - 1, max(len(messages) - num_tool_msgs - 1, -1), -1):
        msg = messages[j]
        if isinstance(msg, dict) and msg.get("role") == "tool":
            target_idx = j
            break

    if target_idx is None:
        # 本 batch 中没有 tool result；放回以便 fallback 路径
        with agent._pending_steer_lock:
            if agent._pending_steer:
                agent._pending_steer = agent._pending_steer + "\n" + steer_text
            else:
                agent._pending_steer = steer_text
        return

    # 追加标记
    marker = format_steer_marker(steer_text)
    existing_content = messages[target_idx].get("content", "")
    if not isinstance(existing_content, str):
        # Anthropic 多模态内容块
        blocks = list(existing_content) if existing_content else []
        blocks.append({"type": "text", "text": marker.lstrip()})
        messages[target_idx]["content"] = blocks
    else:
        messages[target_idx]["content"] = existing_content + marker
```

**关键洞察**：Hermes **将 steer 伪装成 tool 输出**。与其注入一个真正的用户消息（这会违反 role alternation），它把 steer 文本追加到最后一个 tool result 中，并带有特殊标记：

```python
# agent/prompt_builder.py（推断）
def format_steer_marker(text: str) -> str:
    return f"\n\n[USER STEER]: {text}\n[/USER STEER]\n"
```

模型将其视为 tool result 的一部分，而不是新的用户 turn。这在保持消息序列不变性的同时，仍然传达了用户意图。

### 3.4 中断优先于 Steer

Hermes 处理了 steer 和中断之间的竞态：

```python
# run_agent.py:2370-2377
# 硬中断取代任何 pending 的 /steer —— steer 是为 Agent 的
# 下一个 tool-call 迭代准备的，而那个迭代不会再发生了。
# 丢弃它，而不是让用户在 post-interrupt turn 上感到意外。
_steer_lock = getattr(self, "_pending_steer_lock", None)
if _steer_lock is not None:
    with _steer_lock:
        self._pending_steer = None
```

这是一种**保守设计**：如果用户中断，任何 pending 的 steer 都会被丢弃，因为执行上下文已经根本改变了。

---

## 4. 架构对比

### 4.1 设计哲学矩阵

![架构对比](assets/architecture-comparison.png)

*图 2：协议级 vs 应用级架构对比 —— 左侧展示 Codex 的分层协议栈和状态机，右侧展示 Hermes 的轻量级 Agent Loop 和字符串缓冲区设计。*

| 维度 | Codex Steer | Hermes Agent Steer |
|------|-------------|-------------------|
| **抽象层级** | 协议 / 状态机 | 应用 / 消息循环 |
| **并发模型** | Async/await + Mutex | Threading.Lock |
| **输入表示** | 结构化的 `TurnInput` enum | 原始字符串缓冲区 |
| **投递机制** | Mailbox queue 注入 | 工具结果伪装 |
| **Turn 安全性** | Expected turn ID 验证 | 无（尽力而为） |
| **Turn 类型守卫** | Review/Compact turn 被拒绝 | N/A（无 turn 类型） |
| **错误分类** | 4 种结构化错误变体 | Boolean 返回 + 静默丢弃 |
| **分析能力** | 完整的事件遥测 | 仅 INFO 日志 |
| **上下文集成** | `additional_context` 合并 | 无 |
| **目标感知** | Continuation/budget 模板 | 无 |

### 4.2 时序图对比

#### Codex：协议级 Steering

```mermaid
sequenceDiagram
    participant C as Client
    participant A as App Server
    participant T as CodexThread
    participant S as Session

    C->>A: turn/steer(params)
    A->>A: validate thread_id
    A->>A: ensure_direct_input_allowed
    A->>A: validate input size
    A->>T: steer_input(mapped_items, context, expected_turn_id)
    T->>S: lock active_turn
    S->>S: check turn_id match
    S->>S: validate TaskKind != Review/Compact
    S->>S: merge additional_context
    S->>S: queue TurnInput
    S->>T: unlock + return turn_id
    T->>A: Ok(turn_id)
    A->>C: TurnSteerResponse
    note over S: [agent loop continues]<br/>processes queued input<br/>on next iteration
```

#### Hermes：应用级 Steering

```mermaid
sequenceDiagram
    participant C as Client
    participant A as AIAgent
    participant L as Agent Loop
    participant M as LLM API

    C->>A: steer("text")
    A->>A: acquire lock
    A->>A: append to buffer
    A->>A: release lock
    A->>C: True

    L->>L: execute tools
    L->>L: build messages
    L->>A: apply_pending_steer()
    A->>A: drain buffer
    A->>L: append to last tool msg
    L->>M: API call
    M->>M: sees steer as tool output
```

### 4.3 权衡分析

| 权衡 | Codex 方案 | Hermes 方案 |
|------|-----------|------------|
| **正确性** | 高：类型安全、已验证、状态机集成 | 中：字符串操作、无验证 |
| **延迟** | 低：直接 queue 注入，无需等待 | 中：等待 tool batch 完成 |
| **灵活性** | 低：严格的协议、严格的 turn 语义 | 高：简单的缓冲区，任何文本随时可用 |
| **可观测性** | 高：结构化错误、分析事件 | 低：仅日志 |
| **实现成本** | 高：需要协议、状态机、async runtime | 低：~50 行 Python |
| **可移植性** | 低：绑定到 Codex 协议 | 高：通用到任何 tool-loop agent |

---

## 5. 实现深度剖析

### 5.1 Codex：Input Queue 架构

Codex steering 依赖于一个精密的输入队列系统：

```rust
// 来自 session/mod.rs 的概念模型
pub(crate) struct TurnInputQueue {
    pending_input: Vec<TurnInput>,
    turn_states: HashMap<String, TurnState>,
}

pub(crate) enum TurnInput {
    UserInput {
        content: Vec<UserInput>,
        client_id: Option<String>,
    },
    ResponseItem(ResponseItem),
}
```

方法 `extend_pending_input_and_accept_mailbox_delivery_for_turn_state` 做两件事：

1. **扩展 pending input**：向队列添加新项
2. **接受 mailbox 投递**：向活跃 turn 发出新输入可用的信号，可能唤醒挂起的 async 任务

这是**基于推送的通知模型**——steer 不轮询；它触发。

### 5.2 Hermes：Tool Result 伪装

Hermes 的方法根本上受限于 chat API 的契约。LLM API 强制执行严格的 role alternation（user → assistant → user → assistant）。你不能在 assistant 的 tool call 和其后续 reasoning 之间注入一个用户消息。

解决方案：**将 steer 藏在 tool result 中**，这仍然是 assistant 的 "turn" 的一部分：

```json
{
  "role": "tool",
  "content": "file contents...\n\n[USER STEER]: Wait, also check the config\n[/USER STEER]",
  "tool_call_id": "call_123"
}
```

模型读取时理解为："tool 返回了它的输出，还提到了用户想让我检查配置。" 这在语义上是有效的，因为 tool 输出可以包含任意文本。

### 5.3 并发模型差异

| 方面 | Codex（Rust） | Hermes（Python） |
|------|-------------|-----------------|
| **同步机制** | `tokio::sync::Mutex` 在 `active_turn` 上 | `threading.Lock` 在 `_pending_steer` 上 |
| **粒度** | 粗：整个活跃 turn | 细：单个字符串缓冲区 |
| **阻塞** | Async await，非阻塞 | 线程阻塞（持有 GIL） |
| **可扩展性** | 每个 thread 可并发多个 steer | 每个 agent 实例一个 steer 缓冲区 |

---

## 6. 范式转移

### 6.1 从批处理到流式

Steering 代表了人机交互的根本性转变：

![范式转移](assets/black-box-to-glass-box.png)

*图 5：从黑盒到玻璃盒 —— 左侧面板展示传统的 "发送后等待" 模式，用户无法窥见 Agent 内部状态；右侧面板展示 Steering 带来的透明化交互，用户可以实时观察、干预和纠正 Agent 的执行过程。*

### 6.2 从黑盒到玻璃盒

在 steering 之前，Agent 是**黑盒**——你发送输入，等待，然后希望。Steering 使它们成为**玻璃盒**——你可以观察、纠正和重新定向。

这对以下方面有深远影响：

| 维度 | 黑盒时代 | 玻璃盒时代 |
|------|---------|-----------|
| **信任（Trust）** | 错误累积后才被发现 | 实时修正，错误不扩散 |
| **掌控（Agency）** | 要么全权委托，要么微观管理 | 恰到好处的干预粒度 |
| **效率（Efficiency）** | 方向错了要完全重启 | 轻量 redirect，继续执行 |

### 6.3 "Agent as Process" 的出现

Steering 将 Agent 不是视为函数调用，而是视为**接受信号的长运行进程**。这是应用于 AI 的 Unix 哲学：

```bash
# 传统：一次性
$ codex "refactor auth"          # 阻塞直到完成

# 有 steering：类守护进程
$ codex start "refactor auth"    # 立即返回
$ codex steer "skip OAuth"       # 异步信号
$ codex steer "use bcrypt"       # 另一个信号
$ codex status                   # 检查进度
$ codex interrupt                # SIGINT 等价物
```

---

## 6.5 Steer vs Queue vs Interrupt 的完整语义

在 Codex 的实际交互中，用户有三个选择：

| 意图 | 按键 | 行为 | 生效时间 | 适合场景 |
|------|------|------|---------|---------|
| **Steer** | Enter | 修改当前任务方向 | 下一个模型/工具边界 | 纠偏、补充约束 |
| **Queue** | Tab | 安排下一个任务 | 当前任务结束后 | 后续独立需求 |
| **Interrupt** | Ctrl+C / ESC | 终止当前任务 | 立即 | 方向完全错误、需重来 |

心智模型：**Steer = 正在开车转一下方向盘；Queue = 下一个路口再执行；Interrupt = 急刹车。**

```
Codex 正在干活
    ↓
你发现方向错了
    ↓
Enter
    ↓
Steer 当前任务

你只是想追加后续任务
    ↓
Tab
    ↓
Queue 到下一轮
```

### 6.6 安全插入点（Safe Insertion Point）

Steer **不会中途打断正在运行的工具调用**（比如正在跑的测试或 npm install），而是等到**下一个模型调用前的安全边界**再注入：

```
模型思考 → 调工具/跑命令 → 拿到结果 → 【安全插入点】 → 注入 Steer → 再思考...
```

这保证了工具调用的输入输出不会被中途改指令打乱，是 Codex 实现"边跑边纠偏"而不破坏执行一致性的关键。

---

## 7. 全 Agent 生态 Steering 能力全景

### 7.1 横向对比

| 产品 | 类似 Steer 能力 | 实现机制 | 成熟度 |
|------|----------------|---------|--------|
| **Codex App / CLI** | ✅ 原生 Steer（按钮 / Enter 快捷键） | `turn/steer` 协议 + 状态机 | ⭐⭐⭐⭐⭐ |
| **OpenClaw** | ✅ `/steer` + 多种 queue mode | steer / steer-backlog / followup / collect / interrupt | ⭐⭐⭐⭐⭐ |
| **Pi Runtime** | ✅ 模型边界检查 queued steering | 助手消息批次 → 回合结束 → 清空 steer → 追加为 user 消息 | ⭐⭐⭐⭐ |
| **Hermes Agent** | ✅ `queue_mode: steer` / `/steer` | 工具结果伪装 + 字符串缓冲区 | ⭐⭐⭐⭐ |
| **Manus AI** | ✅ 真·mid-stream 注入 | 生成中途可暂停/恢复（soft steer 标杆） | ⭐⭐⭐⭐ |
| **Claude Code** | ❌ 无明确 Steer | 更接近 Interrupt → 重新规划 | ⭐⭐ |

> 设计哲学差异：Claude Code 的聊天窗口 ≈ Agent 本身；Codex 的聊天窗口 = Agent 控制台（任务调度器），Steer 正是这种思路下的产物。

### 7.2 OpenClaw：功能最完整的 Steering 体系

OpenClaw 把 steering 做成一等公民，定义了完整的模式系统：

| 模式 | 活动运行行为 | 后续跟进行为 |
|------|-------------|-------------|
| `/steer`（默认） | 下一个 runtime 边界一起注入所有排队消息 | 仅当 steer 不可用时回退跟进 |
| `/queue` | 逐条注入（Pi 每个模型边界注入一条；Codex 发单独 `turn/steer`） | 仅当 steer 不可用时回退跟进 |
| `steer-backlog` | 与 `steer` 相同 | 额外为后续跟进回合保留同一条消息 |
| `followup` | 不 steer 当前运行 | 当前运行结束后再跑排队消息 |
| `collect` | 不 steer 当前运行 | 防抖窗口后，把兼容消息合并成一个跟进回合 |
| `interrupt` | 中止活动运行，启动最新消息 | 无 |

示例：
```
Agent: 正在分析项目...

你: /steer 不要修改 tests 目录

OpenClaw: 在下一次模型边界把消息注入当前运行，而不会重启任务
```

### 7.3 Claude Code：单线程 Master Loop，无原生 Steer

截至 2026 年 6 月，Claude Code 没有公开的「Steer 当前运行任务」机制。输入新消息时更接近：

```
Interrupt
    ↓
结束当前执行
    ↓
重新规划
```

而非 Codex 的：

```
Steer
    ↓
继续当前执行
    ↓
动态修正
```

Claude Code 的架构是经典的单主线程 + 单条扁平 message history，刻意不做多线程/多 persona。运行中发消息会**排队**，等当前 step/task 结束后处理（而非中途注入）。

### 7.4 Manus AI：真·中途注入的前沿

Manus AI 支持真正的 **mid-stream 注入**——生成中途即可干净暂停/中止当前生成、注入消息、带着新输入恢复，被视为 "soft steer" 标杆。

当前主流（Codex / OpenClaw / Pi）都还停在**工具/模型边界注入**：长时间单次生成或长工具调用期间，消息仍要等到下一个边界。

---

## 8. 未来方向

![未来方向](assets/future-agent-control-protocol.png)

*图 6：Agent Control Protocol (ACP) 愿景 —— 中心化的协议枢纽连接 Meta-Agent 和多个子 Agent，支持语义 Steering、条件触发和跨 Agent 协作调度。*

### 8.1 协议标准化

Codex 的 `turn/steer` JSON-RPC 方法可以成为标准。关键原语是：

- `turn/start`：开始执行
- `turn/steer`：注入飞行中的引导
- `turn/interrupt`：硬停止
- `turn/status`：查询进度

一个跨平台的 "Agent Control Protocol"（ACP）可能出现，类似于 IDE 的 LSP。

### 8.2 语义 Steering

当前实现注入原始文本。未来的系统可以支持：

- **结构化 steer**：JSON patch 到 Agent 的计划/目标
- **条件 steer**："如果你到达第 3 步，做 X 而不是 Y"
- **作用域 steer**："只把这个应用到 auth 模块"

### 8.3 自主 Steering

终极演化：Agent 相互 **steer**。一个元 Agent 监控子 Agent 并发出 steers 以优化并行执行：

```
Meta-Agent: "Agent-1, steer: prioritize API compatibility"
Meta-Agent: "Agent-2, steer: pause until Agent-1 finishes interface"
```

这在 Codex 的 multi-agent v2 架构中已有暗示，其中子 Agent 通过类似机制接收指令。

---

## 附录 A：Codex Steer 错误参考

| 错误 | 代码 | 触发条件 |
|------|------|---------|
| `NoActiveTurn` | `-32600` | Thread 存在但没有正在进行的 turn |
| `ExpectedTurnMismatch` | `-32600` | `expected_turn_id` 与活跃 turn 不匹配 |
| `ActiveTurnNotSteerable` | `-32600` | Turn 是 Review 或 Compact 类型 |
| `EmptyInput` | `-32602` | `input` 数组为空 |
| `InputTooLarge` | `-32602` | 文本超过 `MAX_USER_INPUT_TEXT_CHARS` |

## 附录 B：Hermes Steer API

```python
class AIAgent:
    def steer(self, text: str) -> bool:
        """线程安全的 steer 注入。如果接受则返回 True。"""
        ...

    def _drain_pending_steer(self) -> Optional[str]:
        """内部：消费 pending 的 steer。由 agent loop 调用。"""
        ...
```

不抛出异常；空文本返回 `False`，所有其他情况返回 `True`。

---

## 参考资料

### 源码与官方文档
1. OpenAI Codex v0.139.0 源代码 (`codex-rs/`)
2. Hermes Agent v0.16.0 源代码 (`run_agent.py`, `agent/agent_runtime_helpers.py`)
3. [OpenAI Academy — Working with Codex](https://openai.com/academy/working-with-codex/)
4. [A Practical Codex App: Steer Workflow](https://community.openai.com/t/a-practical-codex-app-steer-workflow-splitting-a-task-into-staged-follow-ups/1377757)
5. Codex Release Notes: https://github.com/openai/codex/releases
6. Hermes Agent Release Notes: https://github.com/NousResearch/hermes-agent/releases
7. Codex Steer 功能 Commit: https://github.com/openai/codex/pull/10690
8. Codex Changelog v0.98.0: https://changelogs.directory/tools/codex/releases/0.98.0

### OpenClaw 与 Pi Runtime
9. [Steer · OpenClaw](https://docs.openclaw.ai/tools/steer)
10. [Steering Queue · OpenClaw](https://docs.openclaw.ai/concepts/queue-steering)
11. [GitHub Copilot SDK — Steering and Queueing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/steering-and-queueing)

### 社区分析
12. [Claude Code Architecture Analysis](https://github.com/anthropics/claude-code) (相关 issue #36326)

---

*本报告于 2026-06-11 基于 Codex v0.139.0 和 Hermes Agent v0.16.0 的源代码分析生成。所有代码摘录均在合理使用范围内，用于技术分析和教育目的。*
