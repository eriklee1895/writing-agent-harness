### TurnSteerParams struct — the turn/steer request wire payload

/Users/eriklee/code/coding-agent/codex/codex-rs/app-server-protocol/src/protocol/v2/turn.rs 154-175

```rust
#[derive(
    Serialize, Deserialize, Debug, Default, Clone, PartialEq, JsonSchema, TS, ExperimentalApi,
)]
#[serde(rename_all = "camelCase")]
#[ts(export_to = "v2/")]
pub struct TurnSteerParams {
    pub thread_id: String,
    #[ts(optional = nullable)]
    pub client_user_message_id: Option<String>,
    pub input: Vec<UserInput>,
    /// Optional turn-scoped Responses API client metadata.
    #[experimental("turn/steer.responsesapiClientMetadata")]
    #[ts(optional = nullable)]
    pub responsesapi_client_metadata: Option<HashMap<String, String>>,
    /// Optional client-provided context fragments keyed by an opaque source identifier.
    #[experimental("turn/steer.additionalContext")]
    #[ts(optional = nullable)]
    pub additional_context: Option<HashMap<String, AdditionalContextEntry>>,
    /// Required active turn id precondition. The request fails when it does not
    /// match the currently active turn.
    pub expected_turn_id: String,
}
```

The steer request carries the target thread, the input to inject, optional metadata/context, and a required expected_turn_id used as an optimistic-concurrency precondition against the active turn.

### TurnSteerResponse struct — the turn/steer reply

/Users/eriklee/code/coding-agent/codex/codex-rs/app-server-protocol/src/protocol/v2/turn.rs 177-182

```rust
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export_to = "v2/")]
pub struct TurnSteerResponse {
    pub turn_id: String,
}
```

On success the server returns only the id of the active turn that absorbed the steered input.

### Analogous turn/interrupt params and response (the requested 'analogous turn/interrupt params')

/Users/eriklee/code/coding-agent/codex/codex-rs/app-server-protocol/src/protocol/v2/turn.rs 184-195

```rust
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export_to = "v2/")]
pub struct TurnInterruptParams {
    pub thread_id: String,
    pub turn_id: String,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, JsonSchema, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export_to = "v2/")]
pub struct TurnInterruptResponse {}
```

Interrupt targets a specific (thread_id, turn_id) and returns an empty acknowledgement, contrasting with steer which appends input rather than aborting.

### SteerInputError enum — core-internal error taxonomy for steering

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/mod.rs 232-238

```rust
#[derive(Debug, PartialEq)]
pub enum SteerInputError {
    NoActiveTurn(Vec<UserInput>),
    ExpectedTurnMismatch { expected: String, actual: String },
    ActiveTurnNotSteerable { turn_kind: NonSteerableTurnKind },
    EmptyInput,
}
```

The four failure modes of steering; NoActiveTurn carries back the rejected input so callers (e.g. turn-start) can re-route it into a new task.

### SteerInputError::to_error_event — maps internal errors to client-facing ErrorEvent/CodexErrorInfo

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/mod.rs 240-269

```rust
impl SteerInputError {
    fn to_error_event(&self) -> ErrorEvent {
        match self {
            Self::NoActiveTurn(_) => ErrorEvent {
                message: "no active turn to steer".to_string(),
                codex_error_info: Some(CodexErrorInfo::BadRequest),
            },
            Self::ExpectedTurnMismatch { expected, actual } => ErrorEvent {
                message: format!("expected active turn id `{expected}` but found `{actual}`"),
                codex_error_info: Some(CodexErrorInfo::BadRequest),
            },
            Self::ActiveTurnNotSteerable { turn_kind } => {
                let turn_kind_label = match turn_kind {
                    NonSteerableTurnKind::Review => "review",
                    NonSteerableTurnKind::Compact => "compact",
                };
                ErrorEvent {
                    message: format!("cannot steer a {turn_kind_label} turn"),
                    codex_error_info: Some(CodexErrorInfo::ActiveTurnNotSteerable {
                        turn_kind: *turn_kind,
                    }),
                }
            }
            Self::EmptyInput => ErrorEvent {
                message: "input must not be empty".to_string(),
                codex_error_info: Some(CodexErrorInfo::BadRequest),
            },
        }
    }
}
```

Only ActiveTurnNotSteerable surfaces a structured CodexErrorInfo variant; the other three collapse to BadRequest.

### NonSteerableTurnKind enum — defined in codex-protocol, NOT in core session module

/Users/eriklee/code/coding-agent/codex/codex-rs/protocol/src/protocol.rs 1606-1613

```rust
/// Turn kinds that reject same-turn steering.
#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, JsonSchema, TS)]
#[serde(rename_all = "snake_case")]
#[ts(rename_all = "snake_case")]
pub enum NonSteerableTurnKind {
    Review,
    Compact,
}
```

Review and Compact turns cannot accept same-turn steering; this enum is shared on the wire and imported into core via codex_protocol::protocol::NonSteerableTurnKind (mod.rs:348).

### CodexErrorInfo::ActiveTurnNotSteerable — the client-facing variant carrying NonSteerableTurnKind

/Users/eriklee/code/coding-agent/codex/codex-rs/protocol/src/protocol.rs 1643-1647

```rust
    /// Returned when `turn/start` or `turn/steer` is submitted while the current active turn
    /// cannot accept same-turn steering, for example `/review` or manual `/compact`.
    ActiveTurnNotSteerable {
        turn_kind: NonSteerableTurnKind,
    },
```

This is how the non-steerable failure is communicated to clients over the protocol, embedding which turn kind blocked steering.

### Session::steer_input — the real implementation and full validation chain

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/mod.rs 3240-3313

```rust
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

        if let Some(expected_turn_id) = expected_turn_id
            && expected_turn_id != active_turn_id
        {
            return Err(SteerInputError::ExpectedTurnMismatch {
                expected: expected_turn_id.to_string(),
                actual: active_turn_id.clone(),
            });
        }

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

        let additional_context_input = {
            let mut state = self.state.lock().await;
            state.additional_context.merge(additional_context)
        };

        if let Some(responsesapi_client_metadata) = responsesapi_client_metadata {
            active_task
                .turn_context
                .turn_metadata_state
                .set_responsesapi_client_metadata(responsesapi_client_metadata);
        }

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

Validates active-turn existence, expected-turn-id precondition, turn-kind steerability (Regular only), and non-empty input, then merges context and appends to the turn's pending input under the held active_turn lock for atomicity.

### Thin Session/Codex wrapper steer_input that delegates to the real implementation

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/mod.rs 764-781

```rust
    pub async fn steer_input(
        &self,
        input: Vec<UserInput>,
        additional_context: BTreeMap<String, AdditionalContextEntry>,
        expected_turn_id: Option<&str>,
        client_user_message_id: Option<String>,
        responsesapi_client_metadata: Option<HashMap<String, String>>,
    ) -> Result<String, SteerInputError> {
        self.session
            .steer_input(
                input,
                additional_context,
                expected_turn_id,
                client_user_message_id,
                responsesapi_client_metadata,
            )
            .await
    }
```

A second steer_input (on the outer Codex handle) that simply forwards to the inner Session implementation at mod.rs:3240 — not mentioned in the task's stated line range.

### TurnInput and TurnInputQueue data structures (the pending-input element + container)

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs 12-25

```rust
#[derive(Clone, Debug, PartialEq)]
pub(crate) enum TurnInput {
    UserInput {
        content: Vec<UserInput>,
        client_id: Option<String>,
    },
    ResponseItem(ResponseItem),
}

/// Turn-local pending input storage owned by the input queue flow.
#[derive(Default)]
pub(crate) struct TurnInputQueue {
    items: Vec<TurnInput>,
}
```

TurnInput is either a batch of user input (with optional client id) or a raw ResponseItem; TurnInputQueue is just an ordered Vec of these used as the turn-local pending buffer.

### InputQueue::extend_pending_input_and_accept_mailbox_delivery_for_turn_state — the function steer_input calls

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs 143-159

```rust
    pub(super) async fn extend_pending_input_and_accept_mailbox_delivery_for_turn_state(
        &self,
        turn_state: &Mutex<TurnState>,
        input: Vec<TurnInput>,
    ) {
        let mut turn_state = turn_state.lock().await;
        turn_state.pending_input.items.extend(input);
        turn_state.accept_mailbox_delivery_for_current_turn();
    }

    pub(crate) async fn extend_pending_input_for_turn_state(
        &self,
        turn_state: &Mutex<TurnState>,
        input: Vec<TurnInput>,
    ) {
        turn_state.lock().await.pending_input.items.extend(input);
    }
```

The mailbox-aware extend variant (used by steer_input) appends to pending_input.items AND marks the current turn as accepting mailbox delivery; the plain variant only appends. Both extend the same turn_state.pending_input.items Vec.

### InputQueue::get_pending_input — how the running turn drains the steered input (consumer side)

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs 168-204

```rust
    #[expect(
        clippy::await_holding_invalid_type,
        reason = "active turn checks and turn state updates must remain atomic"
    )]
    pub(crate) async fn get_pending_input(
        &self,
        active_turn: &Mutex<Option<ActiveTurn>>,
    ) -> Vec<TurnInput> {
        let (pending_input, accepts_mailbox_delivery) = {
            let mut active = active_turn.lock().await;
            match active.as_mut() {
                Some(active_turn) => {
                    let mut turn_state = active_turn.turn_state.lock().await;
                    (
                        turn_state.pending_input.items.split_off(0),
                        turn_state.accepts_mailbox_delivery_for_current_turn(),
                    )
                }
                None => (Vec::new(), true),
            }
        };
        if !accepts_mailbox_delivery {
            return pending_input;
        }
        let mailbox_items = self
            .drain_mailbox_input_items()
            .await
            .into_iter()
            .map(TurnInput::ResponseItem);
        if pending_input.is_empty() {
            mailbox_items.collect()
        } else {
            let mut pending_input = pending_input;
            pending_input.extend(mailbox_items);
            pending_input
        }
    }
```

The turn loop drains pending_input via split_off(0) and, when the turn accepts mailbox delivery, appends drained mailbox items — this is where steered input rejoins the model loop.

### TurnState struct showing the pending_input field (the actual location of the pending_input member)

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/state/turn.rs 86-100

```rust
#[derive(Default)]
pub(crate) struct TurnState {
    pending_approvals: HashMap<String, oneshot::Sender<ReviewDecision>>,
    pending_request_permissions: HashMap<String, PendingRequestPermissions>,
    pending_user_input: HashMap<String, oneshot::Sender<RequestUserInputResponse>>,
    pending_elicitations: HashMap<(String, RequestId), oneshot::Sender<ElicitationResponse>>,
    pending_dynamic_tools: HashMap<String, oneshot::Sender<DynamicToolResponse>>,
    pub(crate) pending_input: TurnInputQueue,
    mailbox_delivery_phase: MailboxDeliveryPhase,
    granted_permissions_by_environment_id: HashMap<String, AdditionalPermissionProfile>,
    strict_auto_review_enabled: bool,
    pub(crate) tool_calls: u64,
    pub(crate) has_memory_citation: bool,
    pub(crate) token_usage_at_turn_start: TokenUsage,
}
```

The pending_input: TurnInputQueue field that steer_input ultimately mutates lives on TurnState in core/src/state/turn.rs:93, not in input_queue.rs as the task implied.

### App-server/turn handler reusing steer_input and falling back on NoActiveTurn (control-flow evidence)

/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/handlers.rs 219-238

```rust
    match sess
        .steer_input(
            items.clone(),
            additional_context.clone(),
            /*expected_turn_id*/ None,
            client_user_message_id.clone(),
            responsesapi_client_metadata.clone(),
        )
        .await
    {
        Ok(_) => {
            current_context.session_telemetry.user_prompt(&items);
        }
        Err(SteerInputError::NoActiveTurn(items)) => {
```

The turn-submission handler first attempts to steer into any active turn; if there is no active turn it consumes the returned input (items) and starts a fresh task instead.

## Control flow

Client sends turn/steer (TurnSteerParams) -> app-server maps it to a core call. CodexThread::steer_input (codex_thread.rs:262) and the Session-facing wrapper Session::steer_input at session/mod.rs:764 both delegate to the real implementation Session::steer_input at session/mod.rs:3240. That implementation locks active_turn, then validates in order: (a) active turn exists else NoActiveTurn (mod.rs:3249/3253), (b) expected_turn_id matches the active task sub_id else ExpectedTurnMismatch (mod.rs:3258-3265), (c) TaskKind must be Regular; Review/Compact return ActiveTurnNotSteerable with the corresponding NonSteerableTurnKind (mod.rs:3267-3279), (d) input non-empty else EmptyInput (mod.rs:3281-3283). On success it merges additional_context into session state, optionally sets responsesapi client metadata, builds a Vec<TurnInput> (context entries as TurnInput::ResponseItem then the user batch as TurnInput::UserInput), and calls InputQueue::extend_pending_input_and_accept_mailbox_delivery_for_turn_state (input_queue.rs:143) which extends turn_state.pending_input.items and accepts mailbox delivery for the current turn, returning the active turn id (-> TurnSteerResponse.turn_id). The running turn later drains these via get_pending_input / take_pending_input_for_turn_state. Note: SteerInputError is the core-internal error type; it is converted to client-facing errors via SteerInputError::to_error_event (mod.rs:241) which maps ActiveTurnNotSteerable to CodexErrorInfo::ActiveTurnNotSteerable. handlers.rs:220 shows the turn-start path reusing steer_input and falling back to a new task when NoActiveTurn is returned.

## Corrections

Several path/line-range claims in the task were imprecise; corrections below. (1) TurnSteerParams/TurnSteerResponse: the file is correct (app-server-protocol/src/protocol/v2/turn.rs). TurnSteerParams is at lines 154-175 and TurnSteerResponse at 177-182; the "analogous turn/interrupt params" (TurnInterruptParams/TurnInterruptResponse) are at 184-195. There is no separate TurnSteerResponse struct beyond the simple { turn_id } shown. (2) Session::steer_input validation chain: the claimed range "core/src/session/mod.rs ~3240-3313" is correct for the real implementation (mod.rs:3240-3313). However there are TWO additional steer_input entry points that the range omits: a thin Session/Codex wrapper at mod.rs:764-781 and CodexThread::steer_input at core/src/codex_thread.rs:262-275 — both just delegate to mod.rs:3240. (3) SteerInputError enum: it lives in core/src/session/mod.rs:232-238 (definition) with its to_error_event impl at 240-269 — NOT alongside NonSteerableTurnKind. NonSteerableTurnKind is NOT in the core session module; it is defined in codex-protocol at codex-rs/protocol/src/protocol.rs:1606-1613 and re-used in core via `use codex_protocol::protocol::NonSteerableTurnKind` (mod.rs:348). So the task's grouping of "SteerInputError and NonSteerableTurnKind enums" spans two different crates/files. (4) InputQueue + pending_input/TurnInput: input_queue.rs is correct. extend_pending_input is actually two functions — extend_pending_input_and_accept_mailbox_delivery_for_turn_state (input_queue.rs:143-151, the one steer_input calls) and extend_pending_input_for_turn_state (input_queue.rs:153-159). TurnInput and TurnInputQueue are defined in input_queue.rs:12-25. The `pending_input` FIELD itself is NOT in input_queue.rs; it is a field of TurnState in core/src/state/turn.rs:93 (TurnState struct at state/turn.rs:86-100). The task's phrase "the pending_input / TurnInput data structures (core/src/session/input_queue.rs)" is therefore only partly right: TurnInput/TurnInputQueue are in input_queue.rs, but the pending_input field is in state/turn.rs.
