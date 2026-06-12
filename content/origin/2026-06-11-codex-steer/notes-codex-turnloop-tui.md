### Core turn loop: can_drain_pending_input gate initialized so fresh turn input is sampled before any pending steer is drained.

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/turn.rs` lines 166-169

```rust
    let mut can_drain_pending_input = input.is_empty();
    if run_hooks_and_record_inputs(&sess, &turn_context, &input).await {
        return None;
    }
```

The boolean starts true only when there is no fresh input; with real turn input it stays false for the first iteration, deferring the drain until after the first sampling request.

### Core turn loop body: conditional drain of pending input and the hooks/record pass before building the next model request.

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/turn.rs` lines 201-222

```rust
    loop {
        // Note that pending_input would be something like a message the user
        // submitted through the UI while the model was running. Though the UI
        // may support this, the model might not.
        let pending_input = if can_drain_pending_input {
            sess.input_queue.get_pending_input(&sess.active_turn).await
        } else {
            Vec::new()
        };

        if run_hooks_and_record_inputs(&sess, &turn_context, &pending_input).await {
            break;
        }

        // Construct the input that we will send to the model.
        let sampling_request_input: Vec<ResponseItem> = async {
            sess.clone_history()
                .await
                .for_prompt(&turn_context.model_info.input_modalities)
        }
        .instrument(trace_span!("run_turn.prepare_sampling_request_input"))
        .await;
```

Each iteration drains pending input into history (only when the gate is open), runs inspection hooks, then snapshots the full history for the model. A steer that arrived during the previous sampling request is folded in here.

### Core turn loop: after sampling, recompute needs_follow_up from model + pending input; auto-compact and the can_drain reset.

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/turn.rs` lines 240-297

```rust
            Ok(sampling_request_output) => {
                let SamplingRequestResult {
                    needs_follow_up: model_needs_follow_up,
                    last_agent_message: sampling_request_last_agent_message,
                } = sampling_request_output;
                can_drain_pending_input = true;
                let (has_pending_input, token_status, estimated_token_count) = async {
                    let has_pending_input =
                        sess.input_queue.has_pending_input(&sess.active_turn).await;
                    let token_status =
                        auto_compact_token_status(sess.as_ref(), turn_context.as_ref()).await;
                    let estimated_token_count =
                        sess.get_estimated_token_count(turn_context.as_ref()).await;
                    (has_pending_input, token_status, estimated_token_count)
                }
                .instrument(trace_span!("run_turn.collect_post_sampling_state"))
                .await;
                let needs_follow_up = model_needs_follow_up || has_pending_input;
                let token_limit_reached = token_status.token_limit_reached;

                trace!(
                    turn_id = %turn_context.sub_id,
                    total_usage_tokens = token_status.active_context_tokens,
                    auto_compact_scope_tokens = token_status.auto_compact_scope_tokens,
                    estimated_token_count = ?estimated_token_count,
                    auto_compact_scope_limit = token_status.auto_compact_scope_limit,
                    auto_compact_limit_scope = ?turn_context.config.model_auto_compact_token_limit_scope,
                    auto_compact_window_ordinal = ?token_status.auto_compact_window_ordinal,
                    auto_compact_window_prefill_tokens = ?token_status.auto_compact_window_prefill_tokens,
                    full_context_window_limit = ?token_status.full_context_window_limit,
                    full_context_window_limit_reached = token_status.full_context_window_limit_reached,
                    token_limit_reached,
                    model_needs_follow_up,
                    has_pending_input,
                    needs_follow_up,
                    "post sampling token usage"
                );

                // as long as compaction works well in getting us way below the token limit, we shouldn't worry about being in an infinite loop.
                if token_limit_reached && needs_follow_up {
                    if let Err(err) = run_auto_compact(
                        &sess,
                        &turn_context,
                        &mut client_session,
                        InitialContextInjection::BeforeLastUserMessage,
                        CompactionReason::ContextLimit,
                        CompactionPhase::MidTurn,
                    )
                    .await
                    {
                        let error = err.to_codex_protocol_error();
                        sess.emit_turn_error_lifecycle(turn_context.as_ref(), error.clone())
                            .await;
                        return None;
                    }
                    can_drain_pending_input = !model_needs_follow_up;
                    continue;
                }
```

`can_drain_pending_input = true` (line 245) re-opens the gate after sampling. `needs_follow_up = model_needs_follow_up || has_pending_input` (257) means a steer that arrived during the sampling request forces another loop iteration. After mid-turn auto-compact, the gate is reopened only if the model itself does not need to continue (`!model_needs_follow_up`, line 295), so tool/model continuation resumes before any steer.

### Core turn loop: terminal condition — only stop the turn when nothing (model or steer) needs follow-up.

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/turn.rs` lines 299-344

```rust
                if !needs_follow_up {
                    last_agent_message = sampling_request_last_agent_message;
                    let stop_outcome = run_turn_stop_hooks(
                        &sess,
                        &turn_context,
                        stop_hook_active,
                        last_agent_message.clone(),
                    )
                    .await;
                    if stop_outcome.should_block {
                        if let Some(hook_prompt_message) =
                            build_hook_prompt_message(&stop_outcome.continuation_fragments)
                        {
                            sess.record_conversation_items(
                                &turn_context,
                                std::slice::from_ref(&hook_prompt_message),
                            )
                            .await;
                            stop_hook_active = true;
                            continue;
                        } else {
                            sess.send_event(
                                &turn_context,
                                EventMsg::Warning(WarningEvent {
                                    message: "Stop hook requested continuation without a prompt; ignoring the block.".to_string(),
                                }),
                            )
                            .await;
                        }
                    }
                    if stop_outcome.should_stop {
                        break;
                    }
                    if run_legacy_after_agent_hook(
                        &sess,
                        &turn_context,
                        &sampling_request_input,
                        last_agent_message.clone(),
                    )
                    .await
                    {
                        return None;
                    }
                    break;
                }
                continue;
```

If neither the model nor pending input needs follow-up, the turn runs stop hooks and breaks. Otherwise (`continue`, line 344) the loop re-enters and drains the steer into the next request.

### Core: run_hooks_and_record_inputs — per-item inspection hooks, recording, and the full-block abort decision (the function at turn.rs ~407 the task asked about).

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/turn.rs` lines 406-433

```rust
async fn run_hooks_and_record_inputs(
    sess: &Arc<Session>,
    turn_context: &Arc<TurnContext>,
    input: &[TurnInput],
) -> bool {
    let mut blocked_input = false;
    let mut accepted_user_input = false;
    for input_item in input {
        let hook_outcome = inspect_pending_input(sess, turn_context, input_item).await;
        if hook_outcome.should_stop {
            blocked_input = true;
            record_additional_contexts(sess, turn_context, hook_outcome.additional_contexts).await;
        } else {
            if matches!(input_item, TurnInput::UserInput { content, .. } if !content.is_empty()) {
                accepted_user_input = true;
            }
            record_pending_input(
                sess,
                turn_context,
                input_item.clone(),
                hook_outcome.additional_contexts,
            )
            .await;
        }
    }
    blocked_input && !accepted_user_input
}
```

Returns true (turn loop breaks / aborts) only when every item was blocked by a hook AND no non-empty user input survived. Blocked items still contribute their additional contexts; accepted items are recorded into pending input.

### Core: get_pending_input — the actual implementation drained by the turn loop (CORRECTION: lives in input_queue.rs, not turn.rs).

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs` lines 172-204

```rust
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

Atomically splits off the active turn's queued pending_input items and, when the turn accepts mailbox delivery, appends drained inter-agent mailbox items. This is what `run_turn` calls at turn.rs line 206.

### Core: has_pending_input — checks the same queue + mailbox; turn.rs uses it to set needs_follow_up after sampling.

`/Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs` lines 210-231

```rust
    pub(crate) async fn has_pending_input(&self, active_turn: &Mutex<Option<ActiveTurn>>) -> bool {
        let (has_turn_pending_input, accepts_mailbox_delivery) = {
            let active = active_turn.lock().await;
            match active.as_ref() {
                Some(active_turn) => {
                    let turn_state = active_turn.turn_state.lock().await;
                    (
                        !turn_state.pending_input.items.is_empty(),
                        turn_state.accepts_mailbox_delivery_for_current_turn(),
                    )
                }
                None => (false, true),
            }
        };
        if has_turn_pending_input {
            return true;
        }
        if !accepts_mailbox_delivery {
            return false;
        }
        self.has_pending_mailbox_items().await
    }
```

Returns true if the turn has queued input items or (when allowed) pending mailbox items. Called at turn.rs line 248 to compute `has_pending_input`, which is OR'd with the model's own follow-up flag.

### TUI steer-vs-queue decision: render_in_history derived from whether an agent turn is running.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/input_submission.rs` lines 148-149

```rust
        let render_in_history = !self.turn_lifecycle.agent_turn_running;
        let mut items: Vec<UserInput> = Vec::new();
```

The single source of truth for steer-vs-fresh-turn: if a turn is running the message is treated as a steer (not rendered, becomes a PendingSteer); otherwise it starts a fresh user turn rendered in history.

### TUI: PendingSteer construction (only when !render_in_history) and push into the pending_steers queue after the op submits.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/input_submission.rs` lines 322-390

```rust
        let pending_steer = (!render_in_history).then(|| PendingSteer {
            user_message: UserMessage {
                text: text.clone(),
                local_images: local_images.clone(),
                remote_image_urls: remote_image_urls.clone(),
                text_elements: text_elements.clone(),
                mention_bindings: mention_bindings.clone(),
            },
            history_record: history_record.clone(),
            compare_key: Self::pending_steer_compare_key_from_items(&items),
        });
        let personality = self
            .config
            .personality
            .filter(|_| self.config.features.enabled(Feature::Personality))
            .filter(|_| self.current_model_supports_personality());
        let service_tier = self.service_tier_update_for_core();
        let active_permission_profile = self.config.permissions.active_permission_profile();
        let op = AppCommand::user_turn(
            items,
            self.config.cwd.to_path_buf(),
            AskForApproval::from(self.config.permissions.approval_policy.value()),
            active_permission_profile,
            effective_mode.model().to_string(),
            effective_mode.reasoning_effort(),
            /*summary*/ None,
            service_tier,
            /*final_output_json_schema*/ None,
            collaboration_mode,
            personality,
        );

        if !self.submit_op(op.clone()) {
            return (false, None);
        }
        if render_in_history {
            self.input_queue.user_turn_pending_start = true;
        }

        // Persist the submitted text to cross-session message history. Mentions are encoded into
        // placeholder syntax so recall can reconstruct the mention bindings in a future session.
        let encoded_mentions = mention_bindings
            .iter()
            .map(|binding| LinkedMention {
                sigil: binding.sigil,
                mention: binding.mention.clone(),
                path: binding.path.clone(),
            })
            .collect::<Vec<_>>();
        let history_text = match &history_record {
            UserMessageHistoryRecord::UserMessageText if !text.is_empty() => {
                Some(encode_history_mentions(&text, &encoded_mentions))
            }
            UserMessageHistoryRecord::Override(history) if !history.text.is_empty() => {
                Some(encode_history_mentions(&history.text, &encoded_mentions))
            }
            UserMessageHistoryRecord::UserMessageText | UserMessageHistoryRecord::Override(_) => {
                None
            }
        };
        if let Some(history_text) = history_text {
            self.append_message_history_entry(history_text);
        }

        if let Some(pending_steer) = pending_steer {
            self.input_queue.pending_steers.push_back(pending_steer);
            self.transcript.saw_plan_item_this_turn = false;
            self.refresh_pending_input_preview();
        }
```

Both the steer and the fresh-turn path submit the same `user_turn` op to core. The difference: a steer creates a PendingSteer (carrying the user_message, history_record and a compare_key for later de-duping against the committed history) and pushes it to `pending_steers`; the fresh-turn path instead sets `user_turn_pending_start`. The compare_key lets the UI later recognise when core commits this steer into history so it can drop the pending copy.

### TUI three-queue InputQueueState struct: the three queues plus the interrupt-coupling flag.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/input_queue.rs` lines 21-45

```rust
#[derive(Debug, Default)]
pub(super) struct InputQueueState {
    /// User inputs queued while a turn is in progress.
    pub(super) queued_user_messages: VecDeque<QueuedUserMessage>,
    /// History records for queued user messages. Slash commands such as `/goal`
    /// can render history that differs from the text submitted to core, so this
    /// stays in lockstep with `queued_user_messages`, with missing entries
    /// treated as user-message text.
    pub(super) queued_user_message_history_records: VecDeque<UserMessageHistoryRecord>,
    /// A user turn has been submitted to core, but `TurnStarted` has not arrived yet.
    pub(super) user_turn_pending_start: bool,
    /// User messages that tried to steer a non-regular turn and must be retried first.
    pub(super) rejected_steers_queue: VecDeque<UserMessage>,
    /// History records for rejected steers. Slash commands such as `/goal` can
    /// render history that differs from the text submitted to core, so this stays
    /// in lockstep with `rejected_steers_queue`, with missing entries treated as
    /// user-message text.
    pub(super) rejected_steer_history_records: VecDeque<UserMessageHistoryRecord>,
    /// Steers already submitted to core but not yet committed into history.
    pub(super) pending_steers: VecDeque<PendingSteer>,
    /// When set, the next interrupt should resubmit all pending steers as one
    /// fresh user turn instead of restoring them into the composer.
    pub(super) submit_pending_steers_after_interrupt: bool,
    pub(super) suppress_queue_autosend: bool,
}
```

Three message queues with parallel history-record VecDeques: `queued_user_messages` (typed before session ready / autosend), `rejected_steers_queue` (steers core refused for a non-regular turn — retried first), `pending_steers` (steers in flight to core, awaiting commit). `submit_pending_steers_after_interrupt` couples Esc to steers.

### TUI interrupt-x-steer: review-mode rejection guard, then the arming branch that sets submit_pending_steers_after_interrupt and submits interrupt.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/interaction.rs` lines 115-140

```rust
        const REVIEW_STEER_UNAVAILABLE_MESSAGE: &str = "Steer messages aren't supported during /review. Press Ctrl+C now to cancel the review.";

        if self.chat_keymap.interrupt_turn.is_pressed(key_event)
            && self.review.is_review_mode
            && (!self.input_queue.pending_steers.is_empty()
                || !self.input_queue.rejected_steers_queue.is_empty())
            && self.bottom_pane.is_task_running()
            && self.bottom_pane.no_modal_or_popup_active()
            && !self.should_handle_vim_insert_escape(key_event)
        {
            self.add_warning_message(REVIEW_STEER_UNAVAILABLE_MESSAGE.to_string());
            return;
        }

        if self.chat_keymap.interrupt_turn.is_pressed(key_event)
            && !self.input_queue.pending_steers.is_empty()
            && self.bottom_pane.is_task_running()
            && self.bottom_pane.no_modal_or_popup_active()
            && !self.should_handle_vim_insert_escape(key_event)
        {
            self.input_queue.submit_pending_steers_after_interrupt = true;
            if !self.submit_op(AppCommand::interrupt()) {
                self.input_queue.submit_pending_steers_after_interrupt = false;
            }
            return;
        }
```

If the interrupt key is pressed while steers exist during a running /review, it is rejected with a warning. Otherwise, with pending steers and a running task, the flag is armed and `interrupt()` is submitted; the flag is rolled back if the op fails to submit. This is the SET half of the interrupt-x-steer handshake (the field, not a function, is named submit_pending_steers_after_interrupt).

### TUI interrupt-x-steer consume side: on_interrupted_turn reads the flag and resubmits drained pending steers as one fresh turn.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/input_restore.rs` lines 138-187

```rust
    pub(super) fn on_interrupted_turn(&mut self, reason: TurnAbortReason) {
        let cancelled_prompt = self.take_armed_cancel_edit_prompt(reason);
        // Finalize, log a gentle prompt, and clear running state.
        self.finalize_turn();
        let send_pending_steers_immediately =
            self.input_queue.submit_pending_steers_after_interrupt;
        self.input_queue.submit_pending_steers_after_interrupt = false;
        if cancelled_prompt.is_none()
            && self.interrupted_turn_notice_mode != InterruptedTurnNoticeMode::Suppress
        {
            if send_pending_steers_immediately {
                self.add_to_history(history_cell::new_info_event(
                    "Model interrupted to submit steer instructions.".to_owned(),
                    /*hint*/ None,
                ));
            } else {
                self.add_to_history(history_cell::new_error_event(
                    self.interrupted_turn_message(reason),
                ));
            }
        }

        // The server has already discarded pending input by the time the
        // interrupted turn reaches the UI, so any unacknowledged steers still
        // tracked here must be restored locally instead of waiting for a later commit.
        if send_pending_steers_immediately {
            let pending_steers = self
                .input_queue
                .pending_steers
                .drain(..)
                .map(|pending| (pending.user_message, pending.history_record))
                .collect::<Vec<_>>();
            if !pending_steers.is_empty() {
                let (user_message, history_record) =
                    merge_user_messages_with_history_record(pending_steers);
                self.submit_user_message_with_history_record(user_message, history_record);
            } else if let Some(combined) = self.drain_pending_messages_for_restore() {
                self.restore_user_message_to_composer(combined);
            }
        } else if let Some(combined) = self.drain_pending_messages_for_restore() {
            self.restore_user_message_to_composer(combined);
        }
        self.refresh_pending_input_preview();
        if let Some(prompt) = cancelled_prompt {
            self.app_event_tx
                .send(AppEvent::RestoreCancelledTurn(prompt));
        }

        self.request_redraw();
    }
```

When the aborted turn returns and the flag was armed, all pending steers are drained, merged into one message, and resubmitted as a fresh user turn (shown with a benign 'Model interrupted to submit steer instructions.' notice). If the flag was NOT armed, an ordinary Esc, drained pending/queued messages are instead restored into the composer for the user to edit. Note the comment: core has already discarded server-side pending input, so the UI must re-drive these locally.

### TUI: enqueue_rejected_steer — moves a steer core refused (non-regular turn) from pending_steers into rejected_steers_queue.

`/Users/eriklee/code/coding-agent/codex/codex-rs/tui/src/chatwidget/input_restore.rs` lines 117-132

```rust
    pub(crate) fn enqueue_rejected_steer(&mut self) -> bool {
        let Some(pending_steer) = self.input_queue.pending_steers.pop_front() else {
            tracing::warn!(
                "received active-turn-not-steerable error without a matching pending steer"
            );
            return false;
        };
        self.input_queue
            .rejected_steers_queue
            .push_back(pending_steer.user_message);
        self.input_queue
            .rejected_steer_history_records
            .push_back(pending_steer.history_record);
        self.refresh_pending_input_preview();
        true
    }
```

When core signals the running turn is not steerable, the front pending steer is reclassified into rejected_steers_queue (with its history record). pop_next_queued_user_message later always drains rejected steers before queued_user_messages, so the rejected steer is retried as a fresh turn first.

## Control flow

CORE turn loop (turn.rs run_turn, lines 201-385):
1. can_drain_pending_input = input.is_empty()  (line 166) — fresh input sampled first.
2. loop {
3.   pending_input = can_drain_pending_input ? get_pending_input() : Vec::new()  (205-209)
4.   run_hooks_and_record_inputs(pending_input) -> break on full-block  (211-213)
5.   build sampling_request_input from history snapshot  (216-222)
6.   run_sampling_request(...)
7.     Ok: can_drain_pending_input = true  (245)
8.          has_pending_input = input_queue.has_pending_input()  (247-248)
9.          needs_follow_up = model_needs_follow_up || has_pending_input  (257)
10.         if token_limit_reached && needs_follow_up { auto_compact; can_drain_pending_input = !model_needs_follow_up; continue }  (279-297)
11.         if !needs_follow_up { stop hooks; break }  (299-343)
12.         else continue (loop again to drain the steer)  (344)
13.     Err(TurnAborted) => break  (346-349)
}

TUI submit (input_submission.rs submit_user_message_with_history_and_shell_escape_policy):
1. render_in_history = !agent_turn_running  (148)
2. build UserInput items (text/images/skills/mentions)  (149-293)
3. pending_steer = (!render_in_history).then(|| PendingSteer{...})  (322-332)
4. submit_op(user_turn)  (354)
5. if render_in_history { user_turn_pending_start = true }  (357-359)
6. if let Some(pending_steer) { pending_steers.push_back(pending_steer); refresh_preview }  (386-390)
7. if render_in_history { record_cancel_edit_candidate; on_user_message_display }  (392-417)

Core rejects a steer the running (non-regular) turn cannot accept -> enqueue_rejected_steer (input_restore.rs 117-132): pops front of pending_steers, pushes its user_message+history into rejected_steers_queue. rejected_steers always drain BEFORE queued_user_messages (pop_next_queued_user_message, input_restore.rs 55-93).

INTERRUPT x STEER:
1. interrupt key + !pending_steers.is_empty() + task running (interaction.rs 129-134)
2.   submit_pending_steers_after_interrupt = true; submit_op(interrupt())  (135-138)
3. TurnAborted reaches UI -> on_interrupted_turn (input_restore.rs 138):
4.   read+clear submit_pending_steers_after_interrupt flag  (142-144)
5.   if flag: drain pending_steers, merge_user_messages_with_history_record, resubmit as fresh turn  (163-176)
6.   else: restore drained pending/queued messages into composer  (177-179)

## Corrections

1. `get_pending_input`, `has_pending_input`, `take_pending_input_for_turn_state`, and `drain_mailbox_input_items` are NOT defined in core/src/session/turn.rs (~407+) as the task assumed. turn.rs only CALLS them (lines 206, 248). Their verbatim definitions are in a sibling file: /Users/eriklee/code/coding-agent/codex/codex-rs/core/src/session/input_queue.rs — `get_pending_input` at lines 172-204, `has_pending_input` at lines 210-231. The function actually at turn.rs ~407 is `run_hooks_and_record_inputs` (lines 407-433), which IS present as requested. There is no `needs_follow_up` function; `needs_follow_up` is a local boolean computed at turn.rs line 257.

2. The `can_drain_pending_input` gate (not mentioned in the task) is the real mechanism that defers draining pending input: declared at line 166, reset at 245, and conditioned after auto-compact at 295. The loop comment at lines 196-199 documents the two defer cases.

3. TUI `render_in_history = !agent_turn_running` is at input_submission.rs line 148 (matches ~148). PendingSteer construction is at lines 322-332 and the push at 386-390 (task said ~321-387 — accurate, construction+push span 322-390).

4. The three-queue struct is `InputQueueState` in tui/src/chatwidget/input_queue.rs lines 22-45 (matches ~22-44, with `suppress_queue_autosend` at line 44 as a 4th non-queue field). Fields: `queued_user_messages` (24), `rejected_steers_queue` (33), `pending_steers` (40). `submit_pending_steers_after_interrupt` is at line 43.

5. The interrupt-x-steer flag is SET in tui/src/chatwidget/interaction.rs (handle_key_event, lines 129-140), and CONSUMED in tui/src/chatwidget/input_restore.rs (on_interrupted_turn, lines 138-187). The task named a function `submit_pending_steers_after_interrupt` "in interaction.rs" — that is a struct FIELD (input_queue.rs line 43), not a function; the logic is split across interaction.rs (arm) and input_restore.rs (resubmit).
