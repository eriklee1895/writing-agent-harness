# Agent Real-Time Intervention Deep Dive: From Codex Steer to Full Ecosystem Steering Paradigm

> **Version**: v1.1  
> **Date**: 2026-06-11  
> **Scope**: Codex v0.139.0 + Hermes v0.16.0 + OpenClaw + Pi + Manus + Claude Code  
> **Classification**: Agent Architecture / Real-time Control / Human-in-the-Loop  
> **Steer Feature GA**: Codex CLI v0.98.0 (2026/02/06), commit [openai/codex#10690](https://github.com/openai/codex/pull/10690)

---

![Cover](assets/cover.png)

---

## Table of Contents

1. [The Problem: Why Agent Needs Steering](#1-the-problem-why-agent-needs-steering)
2. [Codex Steer: Protocol-Level Real-time Injection](#2-codex-steer-protocol-level-real-time-injection)
3. [Hermes Agent Steer: Application-Level Tool Result Append](#3-hermes-agent-steer-application-level-tool-result-append)
4. [Architecture Comparison](#4-architecture-comparison)
5. [Implementation Deep Dive](#5-implementation-deep-dive)
6. [The Paradigm Shift](#6-the-paradigm-shift)
7. [Full Agent Ecosystem Steering Landscape](#7-full-agent-ecosystem-steering-landscape)
8. [Future Directions](#8-future-directions)

---

## 1. The Problem: Why Agent Needs Steering

### 1.1 The Synchronous Turn Trap

![Codex Steer UI](assets/codex-steer-ui-screenshot.png)

*Figure 0: Codex Steer feature in the actual UI — while the Agent is working on a task, the user can type "wait i meant REWRITE" in the input box and click the **Steer** button to inject this new intent into the currently executing turn, without waiting for the current turn to complete. Source: OpenAI Academy — [Working with Codex](https://openai.com/academy/working-with-codex/).*



Traditional conversational AI operates on a **turn-based model**: user sends input → model processes → model responds → user waits for completion before sending next input. This pattern, inherited from chatbot interfaces, breaks down catastrophically when applied to long-running agent tasks.

Consider a Codex agent executing a multi-step refactoring:

```
User: "Refactor the auth module to use JWT"
[Agent begins: 1. reading files → 2. analyzing dependencies → 3. planning changes → 4. applying patches → 5. running tests]

User (5 minutes later, watching agent go wrong): "STOP! Don't touch the OAuth2 flow, only the session manager!"
[User must wait for current turn to complete or issue hard interrupt]
```

The fundamental asymmetry: **human cognition is interrupt-driven; agent execution is batch-driven**. When an agent runs for minutes (or hours), the user's mental model of the task evolves in real-time, but the agent's execution context is frozen at the moment of turn initiation.

### 1.2 The Steering Gap

![Steering Gap Concept](assets/batch-vs-streaming-model.png)

*Figure 1: Batch Model vs Streaming Model — Steering breaks the traditional turn-based boundary, allowing real-time user intent injection during Agent execution.*

Three specific failure modes emerge:

| Failure Mode | Description | Example |
|-------------|-------------|---------|
| **Direction Drift** | Agent misinterprets intent and proceeds down wrong path | "Implement caching" → agent starts adding Redis when user meant in-memory LRU |
| **Context Lag** | New information arrives mid-execution but cannot be incorporated | User sees error message in terminal that agent hasn't noticed |
| **Scope Creep** | Agent extends work beyond intended boundaries | "Fix this bug" → agent begins refactoring entire module |

The "Steer" mechanism addresses all three by allowing **asynchronous user input injection into an actively executing turn**.

---

## 2. Codex Steer: Protocol-Level Real-time Injection

### 2.1 Protocol Surface

![Codex Steer Flow](assets/codex-steer-flow.png)

*Figure 3: Codex Steer Protocol Flow — From Client's `turn/steer` request through to Session state machine, showing optimistic concurrency guards and Turn type validation checkpoints.*

Codex exposes steering through a first-class JSON-RPC protocol method:

```rust
// codex-rs/app-server-protocol/src/protocol/common.rs:771-775
TurnSteer => "turn/steer" {
    params: v2::TurnSteerParams,
    inspect_params: true,
    serialization: thread_id(params.thread_id),
    response: v2::TurnSteerResponse,
}
```

The `TurnSteerParams` carries:

```rust
pub struct TurnSteerParams {
    pub thread_id: String,
    pub client_user_message_id: Option<String>,
    pub input: Vec<UserInput>,           // The actual steer content
    pub additional_context: Option<HashMap<String, AdditionalContextEntry>>,
    pub expected_turn_id: String,        // Safety check
    pub responsesapi_client_metadata: Option<HashMap<String, String>>,
}
```

Key design decision: **`expected_turn_id` acts as an optimistic concurrency guard**. The client declares which turn it believes is active; if the server disagrees (turn completed, different turn active), the steer is rejected with `ExpectedTurnMismatch`.

### 2.2 Request Processing Flow

The app-server's `turn_steer_inner` method implements the gatekeeping logic:

```rust
// codex-rs/app-server/src/request_processors/turn_processor.rs:782-889
async fn turn_steer_inner(
    &self,
    request_id: &ConnectionRequestId,
    params: TurnSteerParams,
) -> Result<TurnSteerResponse, JSONRPCErrorError> {
    // 1. Load and validate thread
    let (_, thread) = self.load_thread(&params.thread_id).await?;
    self.ensure_direct_input_allowed(request_id, thread.as_ref()).await?;

    // 2. Validate turn ID is not empty
    if params.expected_turn_id.is_empty() {
        return Err(invalid_request("expectedTurnId must not be empty"));
    }

    // 3. Validate input size limits
    if let Err(error) = Self::validate_v2_input_limit(&params.input) {
        return Err(error);
    }

    // 4. Map inputs and forward to core thread
    let mapped_items: Vec<CoreInputItem> = params.input.into_iter().map(V2UserInput::into_core).collect();
    let additional_context = map_additional_context(params.additional_context);

    let turn_id = thread
        .steer_input(mapped_items, additional_context, Some(&params.expected_turn_id), ...)
        .await
        .map_err(|err| {
            // Detailed error classification for analytics
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

### 2.3 Core Session State Machine

At the heart of Codex's steering is the session's `steer_input` method:

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

    // Concurrency guard: expected turn must match actual
    if let Some(expected_turn_id) = expected_turn_id
        && expected_turn_id != active_turn_id
    {
        return Err(SteerInputError::ExpectedTurnMismatch {
            expected: expected_turn_id.to_string(),
            actual: active_turn_id.clone(),
        });
    }

    // Turn type guard: not all turns are steerable
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

    // Merge additional context into session state
    let additional_context_input = {
        let mut state = self.state.lock().await;
        state.additional_context.merge(additional_context)
    };

    // Update turn metadata
    if let Some(responsesapi_client_metadata) = responsesapi_client_metadata {
        active_task.turn_context.turn_metadata_state
            .set_responsesapi_client_metadata(responsesapi_client_metadata);
    }

    // Build pending input queue and inject
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

**Critical insight**: Codex's steering is **deeply integrated into the session state machine**. The input is not merely appended to a message buffer—it enters the `input_queue` as `TurnInput::UserInput` and `TurnInput::ResponseItem`, becoming part of the active turn's pending mailbox. This means the model will see the steer on its **next iteration**, not after the current turn completes.

### 2.4 The Goal Extension System

Codex goes beyond simple message injection by providing **semantic steering templates** through the Goal extension:

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

These generate structured prompts like:

```markdown
<!-- goals/continuation.md -->
The objective is: {{objective}}
Tokens used so far: {{tokens_used}} / {{token_budget}}
Remaining tokens: {{remaining_tokens}}

Continue working toward the objective. If the remaining token budget is 
insufficient to complete the task, summarize what you've done and what 
remains, then stop.
```

This is **steering with semantic awareness**—the system doesn't just inject raw user text; it can inject structured, templated guidance that maintains narrative continuity.

### 2.5 Error Taxonomy

Codex defines a precise error hierarchy for steering:

```rust
#[derive(Debug, PartialEq)]
pub enum SteerInputError {
    NoActiveTurn(Vec<UserInput>),                           // No turn running
    ExpectedTurnMismatch { expected: String, actual: String }, // Race condition
    ActiveTurnNotSteerable { turn_kind: NonSteerableTurnKind }, // Review/Compact turns
    EmptyInput,                                             // Validation
}
```

Each error maps to both a user-facing message and an analytics event:

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

## 3. Hermes Agent Steer: Application-Level Tool Result Append

### 3.1 Design Philosophy

Hermes Agent takes a different approach. Rather than building steering into a protocol-level state machine, it implements steering as an **application-layer message manipulation** within the Python agent loop.

### 3.2 The Lock-Based Pending Buffer

At the core is a simple locked string buffer:

```python
# run_agent.py:2379-2413
class AIAgent:
    def __init__(self, ...):
        # Initialized in __init__
        self._pending_steer: Optional[str] = None
        self._pending_steer_lock: threading.Lock = threading.Lock()

    def steer(self, text: str) -> bool:
        """
        Inject a user message into the next tool result without interrupting.

        Unlike interrupt(), this does NOT stop the current tool call. The
        text is stashed and the agent loop appends it to the LAST tool
        result's content once the current tool batch finishes.
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
        """Return the pending steer text (if any) and clear the slot."""
        with self._pending_steer_lock:
            text = self._pending_steer
            self._pending_steer = None
            return text
```

**Key difference**: Hermes stores steer text in a **raw string buffer**, not as structured input items. There's no turn ID validation, no state machine integration, no protocol serialization.

### 3.3 Delivery Mechanism: Tool Result Masquerading

![Hermes Tool Result Masquerading](assets/hermes-tool-result-masquerading.png)

*Figure 4: Tool Result Masquerading — How Hermes disguises user steer as part of tool output, injecting via `[USER STEER]` marker into the last tool message to bypass role alternation constraints.*

The critical implementation is in `apply_pending_steer_to_tool_results`:

```python
# agent/agent_runtime_helpers.py:2371-2432
def apply_pending_steer_to_tool_results(agent, messages: list, num_tool_msgs: int) -> None:
    """Append any pending /steer text to the last tool result in this turn.

    Called at the end of a tool-call batch, before the next API call.
    The steer is appended to the last role:"tool" message's content
    with a clear marker so the model understands it came from the user
    and NOT from the tool itself.
    """
    if num_tool_msgs <= 0 or not messages:
        return
    steer_text = agent._drain_pending_steer()
    if not steer_text:
        return

    # Find the last tool-role message in the recent tail
    target_idx = None
    for j in range(len(messages) - 1, max(len(messages) - num_tool_msgs - 1, -1), -1):
        msg = messages[j]
        if isinstance(msg, dict) and msg.get("role") == "tool":
            target_idx = j
            break

    if target_idx is None:
        # No tool result in this batch; put the steer back for fallback
        with agent._pending_steer_lock:
            if agent._pending_steer:
                agent._pending_steer = agent._pending_steer + "\n" + steer_text
            else:
                agent._pending_steer = steer_text
        return

    # Append with marker
    marker = format_steer_marker(steer_text)
    existing_content = messages[target_idx].get("content", "")
    if not isinstance(existing_content, str):
        # Anthropic multimodal content blocks
        blocks = list(existing_content) if existing_content else []
        blocks.append({"type": "text", "text": marker.lstrip()})
        messages[target_idx]["content"] = blocks
    else:
        messages[target_idx]["content"] = existing_content + marker
```

**Critical insight**: Hermes **masquerades the steer as tool output**. Instead of injecting a true user message (which would violate role alternation), it appends the steer text to the last tool result with a special marker:

```python
# agent/prompt_builder.py (inferred)
def format_steer_marker(text: str) -> str:
    return f"\n\n[USER STEER]: {text}\n[/USER STEER]\n"
```

The model sees this as part of the tool result, not as a new user turn. This preserves message sequence invariants while still conveying user intent.

### 3.4 Interrupt Supersedes Steer

Hermes handles the race between steer and interrupt:

```python
# run_agent.py:2370-2377
# A hard interrupt supersedes any pending /steer — the steer was
# meant for the agent's next tool-call iteration, which will no
# longer happen. Drop it instead of surprising the user with a
# late injection on the post-interrupt turn.
_steer_lock = getattr(self, "_pending_steer_lock", None)
if _steer_lock is not None:
    with _steer_lock:
        self._pending_steer = None
```

This is a **conservative design**: if the user interrupts, any pending steer is discarded because the execution context has fundamentally changed.

---

## 4. Architecture Comparison

### 4.1 Design Philosophy Matrix

![Architecture Comparison](assets/architecture-comparison.png)

*Figure 2: Protocol-Level vs Application-Level Architecture — Left side shows Codex's layered protocol stack with state machine integration; right side shows Hermes' lightweight Agent Loop with string buffer design.*

| Dimension | Codex Steer | Hermes Agent Steer |
|-----------|-------------|-------------------|
| **Abstraction Level** | Protocol / State Machine | Application / Message Loop |
| **Concurrency Model** | Async/await + Mutex | Threading.Lock |
| **Input Representation** | Structured `TurnInput` enum | Raw string buffer |
| **Delivery Mechanism** | Mailbox queue injection | Tool result masquerading |
| **Turn Safety** | Expected turn ID validation | None (best-effort) |
| **Turn Type Guards** | Review/Compact turns rejected | N/A (no turn types) |
| **Error Taxonomy** | 4 structured error variants | Boolean return + silent drop |
| **Analytics** | Full event telemetry | INFO log only |
| **Context Integration** | `additional_context` merge | None |
| **Goal Awareness** | Continuation/budget templates | None |

### 4.2 Sequence Diagram Comparison

#### Codex: Protocol-Level Steering

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

#### Hermes: Application-Level Steering

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

### 4.3 Trade-off Analysis

| Trade-off | Codex Approach | Hermes Approach |
|-----------|---------------|-----------------|
| **Correctness** | High: type-safe, validated, state machine integrated | Medium: string manipulation, no validation |
| **Latency** | Low: direct queue injection, no waiting | Medium: waits for tool batch completion |
| **Flexibility** | Low: rigid protocol, strict turn semantics | High: simple buffer, any text anytime |
| **Observability** | High: structured errors, analytics events | Low: logs only |
| **Implementation Cost** | High: requires protocol, state machine, async runtime | Low: ~50 lines of Python |
| **Portability** | Low: tied to Codex protocol | High: generic to any tool-loop agent |

---

## 5. Implementation Deep Dive

### 5.1 Codex: The Input Queue Architecture

Codex steering depends on a sophisticated input queue system:

```rust
// Conceptual model from session/mod.rs
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

The method `extend_pending_input_and_accept_mailbox_delivery_for_turn_state` does two things:

1. **Extends pending input**: Adds new items to the queue
2. **Accepts mailbox delivery**: Signals the active turn that new input is available, potentially waking a suspended async task

This is a **push-based notification model**—the steer doesn't poll; it triggers.

### 5.2 Hermes: The Tool Result Camouflage

Hermes's approach is fundamentally limited by the chat API contract. LLM APIs enforce strict role alternation (user → assistant → user → assistant). You cannot inject a user message between an assistant's tool call and its subsequent reasoning.

The solution: **hide the steer inside the tool result**, which is still part of the assistant's "turn":

```
Before steer:
  {"role": "assistant", "content": "I'll use read_file", "tool_calls": [...]}
  {"role": "tool", "content": "file contents...", "tool_call_id": "call_123"}

After steer:
  {"role": "assistant", "content": "I'll use read_file", "tool_calls": [...]}
  {"role": "tool", "content": "file contents...\n\n[USER STEER]: Wait, also check the config\n[/USER STEER]", "tool_call_id": "call_123"}
```

The model reads this as: "The tool returned its output, and also mentioned that the user wants me to check the config." This is semantically valid because tool outputs can contain arbitrary text.

### 5.3 Concurrency Model Differences

| Aspect | Codex (Rust) | Hermes (Python) |
|--------|-------------|-----------------|
| **Synchronization** | `tokio::sync::Mutex` on `active_turn` | `threading.Lock` on `_pending_steer` |
| **Granularity** | Coarse: entire active turn | Fine: single string buffer |
| **Blocking** | Async await, non-blocking | Thread blocking (GIL-held) |
| **Scalability** | Many concurrent steers per thread | One steer buffer per agent instance |

---

## 6. The Paradigm Shift

### 6.1 From Batch to Stream

Steering represents a fundamental shift in human-agent interaction:

![Paradigm Shift](assets/black-box-to-glass-box.png)

*Figure 5: From Black Box to Glass Box — Left panel shows traditional "fire-and-forget" mode where users cannot see inside; right panel shows Steering-enabled transparent interaction where users observe, intervene, and redirect Agent execution in real-time.*

### 6.2 From Black Box to Glass Box

Before steering, agents were **black boxes**—you sent input, waited, and hoped. Steering makes them **glass boxes**—you can observe, correct, and redirect mid-flight.

This has profound implications for:

| Dimension | Black Box Era | Glass Box Era |
|-----------|---------------|---------------|
| **Trust** | Errors compound before discovered | Real-time correction, errors don't spread |
| **Agency** | All-or-nothing delegation | Precise intervention granularity |
| **Efficiency** | Wrong direction needs full restart | Lightweight redirect, continue execution |

### 6.3 The Emergence of "Agent as Process"

Steering treats the agent not as a function call but as a **long-running process** that accepts signals. This is the Unix philosophy applied to AI:

```bash
# Traditional: one-shot
$ codex "refactor auth"          # Blocks until complete

# With steering: daemon-like
$ codex start "refactor auth"    # Returns immediately
$ codex steer "skip OAuth"       # Async signal
$ codex steer "use bcrypt"       # Another signal
$ codex status                   # Check progress
$ codex interrupt                # SIGINT equivalent
```

### 6.4 Steer vs Queue vs Interrupt: Complete Semantics

In Codex's actual interaction, users have three choices:

| Intent | Key | Behavior | When Applied | Best For |
|--------|-----|----------|--------------|----------|
| **Steer** | Enter | Modify current task direction | Next model/tool boundary | Correction, additional constraints |
| **Queue** | Tab | Schedule next task | After current task completes | Subsequent independent needs |
| **Interrupt** | Ctrl+C / ESC | Terminate current task | Immediately | Completely wrong direction |

Mental model: **Steer = adjusting the steering wheel while driving; Queue = execute at next intersection; Interrupt = emergency brake.**

### 6.5 Safe Insertion Point

Steer **does not interrupt a running tool call** (e.g., a test in progress or npm install), but waits for the **next model call boundary**:

```
Model thinks → calls tool/runs command → gets result → [SAFE INSERTION POINT] → injects Steer → thinks again...
```

This guarantees tool call inputs/outputs won't be disrupted mid-execution, and is the key to Codex's ability to "correct while running" without breaking execution consistency.

---

## 7. Full Agent Ecosystem Steering Capability Landscape

### 7.1 Horizontal Comparison

| Product | Steering Capability | Implementation Mechanism | Maturity |
|---------|-------------------|------------------------|----------|
| **Codex App / CLI** | ✅ Native Steer (button / Enter shortcut) | `turn/steer` protocol + state machine | ⭐⭐⭐⭐⭐ |
| **OpenClaw** | ✅ `/steer` + multiple queue modes | steer / steer-backlog / followup / collect / interrupt | ⭐⭐⭐⭐⭐ |
| **Pi Runtime** | ✅ Model boundary check queued steering | Assistant batch → turn end → flush steer → append as user msg | ⭐⭐⭐⭐ |
| **Hermes Agent** | ✅ `queue_mode: steer` / `/steer` | Tool result masquerading + string buffer | ⭐⭐⭐⭐ |
| **Manus AI** | ✅ True mid-stream injection | Pause/resume during generation (soft steer benchmark) | ⭐⭐⭐⭐ |
| **Claude Code** | ❌ No explicit Steer | Closer to Interrupt → replan | ⭐⭐ |

> Design philosophy difference: Claude Code's chat window ≈ Agent itself; Codex's chat window = Agent console (task scheduler). Steer is the product of the latter philosophy.

### 7.2 OpenClaw: The Most Complete Steering System

OpenClaw makes steering a first-class citizen with a complete mode system:

| Mode | Active Run Behavior | Follow-up Behavior |
|------|-------------------|-------------------|
| `/steer` (default) | Inject all queued messages at next runtime boundary | Fallback to follow-up only when steer unavailable |
| `/queue` | Inject one by one (Pi at each model boundary; Codex sends separate `turn/steer`) | Fallback to follow-up only when steer unavailable |
| `steer-backlog` | Same as `steer` | Additionally preserve same message for subsequent follow-up turns |
| `followup` | Don't steer current run | Run queued messages after current run completes |
| `collect` | Don't steer current run | After debounce window, merge compatible messages into one follow-up turn |
| `interrupt` | Abort active run, start latest message | None |

Example:
```
Agent: Analyzing project...

You: /steer don't modify tests directory

OpenClaw: Injects message at next model boundary without restarting task
```

### 7.3 Claude Code: Single-threaded Master Loop, No Native Steer

As of June 2026, Claude Code has no public "Steer current running task" mechanism. Entering a new message is closer to:

```
Interrupt
    ↓
End current execution
    ↓
Replan
```

Rather than Codex's:

```
Steer
    ↓
Continue current execution
    ↓
Dynamic correction
```

Claude Code's architecture is a classic single master thread + single flat message history, deliberately avoiding multi-threading/multi-persona. Messages sent during execution are **queued** and processed after the current step/task completes (not injected mid-flight).

### 7.4 Manus AI: The Frontier of True Mid-stream Injection

Manus AI supports true **mid-stream injection** — clean pause/resume during generation, considered the "soft steer" benchmark.

Current mainstream (Codex / OpenClaw / Pi) remains at **tool/model boundary injection**: during long single-generation or long tool calls, messages still wait for the next boundary.

---

## 8. Future Directions

![Future Directions](assets/future-agent-control-protocol.png)

*Figure 6: Agent Control Protocol (ACP) Vision — A centralized protocol hub connecting Meta-Agent and multiple sub-agents, supporting semantic Steering, conditional triggers, and cross-agent collaborative scheduling.*

### 8.1 Protocol Standardization

Codex's `turn/steer` JSON-RPC method could become a standard. The key primitives are:

- `turn/start`: Begin execution
- `turn/steer`: Inject mid-flight guidance
- `turn/interrupt`: Hard stop
- `turn/status`: Query progress

A cross-platform "Agent Control Protocol" (ACP) could emerge, similar to LSP for IDEs.

### 8.2 Semantic Steering

Current implementations inject raw text. Future systems could support:

- **Structured steer**: JSON patches to agent's plan/goal
- **Conditional steer**: "If you reach step 3, do X instead of Y"
- **Scoped steer**: "Apply this only to the auth module"

### 8.3 Autonomous Steering

The ultimate evolution: agents that steer **each other**. A meta-agent monitors sub-agents and issues steers to optimize parallel execution:

```
Meta-Agent: "Agent-1, steer: prioritize API compatibility"
Meta-Agent: "Agent-2, steer: pause until Agent-1 finishes interface"
```

This is already hinted at in Codex's multi-agent v2 architecture, where sub-agents receive directives through similar mechanisms.

---

## Appendix A: Codex Steer Error Reference

| Error | Code | Trigger |
|-------|------|---------|
| `NoActiveTurn` | `-32600` | Thread exists but no turn in progress |
| `ExpectedTurnMismatch` | `-32600` | `expected_turn_id` doesn't match active turn |
| `ActiveTurnNotSteerable` | `-32600` | Turn is Review or Compact type |
| `EmptyInput` | `-32602` | `input` array is empty |
| `InputTooLarge` | `-32602` | Text exceeds `MAX_USER_INPUT_TEXT_CHARS` |

## Appendix B: Hermes Steer API

```python
class AIAgent:
    def steer(self, text: str) -> bool:
        """Thread-safe steer injection. Returns True if accepted."""
        ...

    def _drain_pending_steer(self) -> Optional[str]:
        """Internal: consume pending steer. Called by agent loop."""
        ...
```

No exceptions are raised; empty text returns `False`, all other cases return `True`.

---

## References

### Source Code & Official Docs
1. OpenAI Codex v0.139.0 Source Code (`codex-rs/`)
2. Hermes Agent v0.16.0 Source Code (`run_agent.py`, `agent/agent_runtime_helpers.py`)
3. [OpenAI Academy — Working with Codex](https://openai.com/academy/working-with-codex/)
4. [A Practical Codex App: Steer Workflow](https://community.openai.com/t/a-practical-codex-app-steer-workflow-splitting-a-task-into-staged-follow-ups/1377757)
5. Codex Release Notes: https://github.com/openai/codex/releases
6. Hermes Agent Release Notes: https://github.com/NousResearch/hermes-agent/releases
7. Codex Steer Feature Commit: https://github.com/openai/codex/pull/10690
8. Codex Changelog v0.98.0: https://changelogs.directory/tools/codex/releases/0.98.0

### OpenClaw & Pi Runtime
9. [Steer · OpenClaw](https://docs.openclaw.ai/tools/steer)
10. [Steering Queue · OpenClaw](https://docs.openclaw.ai/concepts/queue-steering)
11. [GitHub Copilot SDK — Steering and Queueing](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/steering-and-queueing)

### Community Analysis
12. [Claude Code Architecture](https://github.com/anthropics/claude-code) (related issue #36326)

---

*This report was generated on 2026-06-11 based on source-code analysis of Codex v0.139.0 and Hermes Agent v0.16.0. All code excerpts are used under fair use for technical analysis and educational purposes.*
