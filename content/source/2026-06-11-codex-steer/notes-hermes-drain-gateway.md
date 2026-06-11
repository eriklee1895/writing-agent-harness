### Drain point 1 of 4: PRE-API steer drain. Runs at the top of each agent loop iteration before api_messages is built, so a steer that arrived during the previous API call lands on THIS iteration by injecting into the last tool-role message. If no tool message exists, it is re-stashed under the lock for a later drain.

/Users/eriklee/code/agent/hermes-agent/agent/conversation_loop.py:522-571

```python
        # ── Pre-API-call /steer drain ──────────────────────────────────
        # If a /steer arrived during the previous API call (while the model
        # was thinking), drain it now — before we build api_messages — so
        # the model sees the steer text on THIS iteration.  Without this,
        # steers sent during an API call only land after the NEXT tool batch,
        # which may never come if the model returns a final response.
        #
        # We scan backwards for the last tool-role message in the messages
        # list.  If found, the steer is appended there.  If not (first
        # iteration, no tools yet), the steer stays pending for the next
        # tool batch — injecting into a user message would break role
        # alternation, and there's no tool output to piggyback on.
        _pre_api_steer = agent._drain_pending_steer()
        if _pre_api_steer:
            _injected = False
            for _si in range(len(messages) - 1, -1, -1):
                _sm = messages[_si]
                if isinstance(_sm, dict) and _sm.get("role") == "tool":
                    from agent.prompt_builder import format_steer_marker
                    marker = format_steer_marker(_pre_api_steer)
                    existing = _sm.get("content", "")
                    if isinstance(existing, str):
                        _sm["content"] = existing + marker
                    else:
                        # Multimodal content blocks — append text block
                        try:
                            blocks = list(existing) if existing else []
                            blocks.append({"type": "text", "text": marker})
                            _sm["content"] = blocks
                        except Exception:
                            pass
                    _injected = True
                    logger.debug(
                        "Pre-API-call steer drain: injected into tool msg at index %d",
                        _si,
                    )
                    break
            if not _injected:
                # No tool message to inject into — put it back so
                # the post-tool-execution drain picks it up later.
                _lock = getattr(agent, "_pending_steer_lock", None)
                if _lock is not None:
                    with _lock:
                        if agent._pending_steer:
                            agent._pending_steer = agent._pending_steer + "\n" + _pre_api_steer
                        else:
                            agent._pending_steer = _pre_api_steer
                else:
                    existing = getattr(agent, "_pending_steer", None)
                    agent._pending_steer = (existing + "\n" + _pre_api_steer) if existing else _pre_api_steer
```

This is the FIRST drain point. It uses _drain_pending_steer() (not _apply_...) because at this stage it manually scans for the last tool message and injects a formatted steer marker. The key safety behavior: if no tool message exists yet, it re-stashes the steer under _pending_steer_lock so it is not lost — it will be picked up by the per-tool/per-batch drains.

### Drain points 2 & 3 of 4 (PARALLEL executor): per-tool drain after each collected result, and per-batch drain after budget enforcement.

/Users/eriklee/code/agent/hermes-agent/agent/tool_executor.py:747-766

```python
        _tool_content = agent._tool_result_content_for_active_model(name, function_result)
        messages.append(make_tool_result_message(name, _tool_content, tc.id))

        # ── Per-tool /steer drain ───────────────────────────────────
        # Same as the sequential path: drain between each collected
        # result so the steer lands as early as possible.
        agent._apply_pending_steer_to_tool_results(messages, 1)

    # ── Per-turn aggregate budget enforcement ─────────────────────────
    num_tools = len(parsed_calls)
    if num_tools > 0:
        turn_tool_msgs = messages[-num_tools:]
        enforce_turn_budget(turn_tool_msgs, env=get_active_env(effective_task_id))

    # ── /steer injection ──────────────────────────────────────────────
    # Append any pending user steer text to the last tool result so the
    # agent sees it on its next iteration. Runs AFTER budget enforcement
    # so the steer marker is never truncated. See steer() for details.
    if num_tools > 0:
        agent._apply_pending_steer_to_tool_results(messages, num_tools)
```

In execute_tool_calls_concurrent. Per-tool drain is line 753 (_apply_pending_steer_to_tool_results(messages, 1) inside the per-result loop). Per-batch drain is line 766 (passes num_tools so it can target the whole batch's tool messages). The per-batch one is deliberately placed AFTER enforce_turn_budget so the steer marker is never truncated by budget enforcement.

### Drain points 2 & 3 of 4 (SEQUENTIAL executor): per-tool drain after each tool result, and per-batch drain after budget enforcement.

/Users/eriklee/code/agent/hermes-agent/agent/tool_executor.py:1378-1420

```python
        _tool_content = agent._tool_result_content_for_active_model(function_name, function_result)
        messages.append(make_tool_result_message(function_name, _tool_content, tool_call.id))

        # ── Per-tool /steer drain ───────────────────────────────────
        # Drain pending steer BETWEEN individual tool calls so the
        # injection lands as soon as a tool finishes — not after the
        # entire batch.  The model sees it on the next API iteration.
        agent._apply_pending_steer_to_tool_results(messages, 1)

        if not agent.quiet_mode:
            if agent.verbose_logging:
                print(f"  ✅ Tool {i} completed in {tool_duration:.2f}s")
                print(agent._wrap_verbose("Result: ", function_result))
            else:
                _fr_str = function_result if isinstance(function_result, str) else str(function_result)
                response_preview = _fr_str[:agent.log_prefix_chars] + "..." if len(_fr_str) > agent.log_prefix_chars else _fr_str
                print(f"  ✅ Tool {i} completed in {tool_duration:.2f}s - {response_preview}")

        if agent._interrupt_requested and i < len(assistant_message.tool_calls):
            remaining = len(assistant_message.tool_calls) - i
            agent._vprint(f"{agent.log_prefix}⚡ Interrupt: skipping {remaining} remaining tool call(s)", force=True)
            for skipped_tc in assistant_message.tool_calls[i:]:
                skipped_name = skipped_tc.function.name
                messages.append(make_tool_result_message(
                    skipped_name,
                    f"[Tool execution skipped — {skipped_name} was not started. User sent a new message]",
                    skipped_tc.id,
                ))
            break

        if agent.tool_delay > 0 and i < len(assistant_message.tool_calls):
            time.sleep(agent.tool_delay)

    # ── Per-turn aggregate budget enforcement ─────────────────────────
    num_tools_seq = len(assistant_message.tool_calls)
    if num_tools_seq > 0:
        enforce_turn_budget(messages[-num_tools_seq:], env=get_active_env(effective_task_id))

    # ── /steer injection ──────────────────────────────────────────────
    # See _execute_tool_calls_parallel for the rationale. Same hook,
    # applied to sequential execution as well.
    if num_tools_seq > 0:
        agent._apply_pending_steer_to_tool_results(messages, num_tools_seq)
```

In execute_tool_calls_sequential. Per-tool drain is line 1385 (drain BETWEEN individual tool calls). Per-batch drain is line 1420 (num_tools_seq), again after enforce_turn_budget. This is the sequential mirror of the 753/766 parallel pair — the task's '~1385-1420' is this sequential block, not a second parallel block.

### Drain point 4 of 4: final/leftover stray drain in turn finalization. Any steer that landed after the final assistant turn (no more tool batches to drain into) is handed back to the caller via result['pending_steer'].

/Users/eriklee/code/agent/hermes-agent/agent/turn_finalizer.py:357-363

```python
    # If a /steer landed after the final assistant turn (no more tool
    # batches to drain into), hand it back to the caller so it can be
    # delivered as the next user turn instead of being silently lost.
    _leftover_steer = agent._drain_pending_steer()
    if _leftover_steer:
        result["pending_steer"] = _leftover_steer
    agent._response_was_previewed = False
```

The FOURTH/final drain. Unlike the per-tool/per-batch hooks, this uses _drain_pending_steer() and stores the result in result['pending_steer'] rather than injecting into messages — because the turn has ended and there is no tool message left to attach to. This guarantees a late steer becomes the next user turn instead of being silently lost.

### Gateway routing decision (_handle_active_session_busy_message): steer-vs-queue-vs-interrupt with #30170 subagent protection (demote interrupt->queue) and the steer fall-back-to-queue path.

/Users/eriklee/code/agent/hermes-agent/gateway/run.py:3621-3697

```python
        running_agent = self._running_agents.get(session_key)

        effective_mode = self._busy_input_mode
        busy_text_mode = getattr(self, "_busy_text_mode", "interrupt")
        if (
            event.message_type == MessageType.TEXT
            and busy_text_mode == "queue"
            and effective_mode != "steer"
        ):
            return False

        # Steer mode: inject mid-run via running_agent.steer() instead of
        # queueing + interrupting.  If the agent isn't running yet
        # (sentinel) or lacks steer(), or the payload is empty, fall back
        # to queue semantics so nothing is lost.
        # #30170 — Subagent protection. ``AIAgent.interrupt()`` cascades
        # to every entry in the parent's ``_active_children`` list and
        # aborts in-flight ``delegate_task`` work. Demote ``interrupt``
        # to ``queue`` when the parent is currently driving subagents so
        # a conversational follow-up doesn't destroy minutes of subagent
        # work. Explicit ``/stop`` and ``/new`` slash commands go through
        # ``_interrupt_and_clear_session`` and are unaffected — the
        # operator still has a way to force-cancel everything.
        demoted_for_subagents = (
            effective_mode == "interrupt"
            and self._agent_has_active_subagents(running_agent)
        )
        if demoted_for_subagents:
            logger.info(
                "Demoting busy_input_mode 'interrupt' to 'queue' for session %s "
                "because the running agent has active subagents (#30170)",
                session_key,
            )
            effective_mode = "queue"
        steered = False
        if effective_mode == "steer":
            steer_text = (event.text or "").strip()
            can_steer = (
                steer_text
                and running_agent is not None
                and running_agent is not _AGENT_PENDING_SENTINEL
                and hasattr(running_agent, "steer")
            )
            if can_steer:
                try:
                    steered = bool(running_agent.steer(steer_text))
                except Exception as exc:
                    logger.warning("Gateway steer failed for session %s: %s", session_key, exc)
                    steered = False
            if not steered:
                # Fall back to queue (merge into pending messages, no interrupt)
                effective_mode = "queue"

        # Store the message so it's processed as the next turn after the
        # current run finishes (or is interrupted).  Skip this for a
        # successful steer — the text already landed inside the run and
        # must NOT also be replayed as a next-turn user message.
        if not steered:
            merge_pending_message_event(
                adapter._pending_messages,
                session_key,
                event,
                merge_text=event.message_type == MessageType.TEXT,
            )

        is_queue_mode = effective_mode == "queue"
        is_steer_mode = effective_mode == "steer"

        # If not in queue/steer mode, interrupt the running agent immediately.
        # This aborts in-flight tool calls and causes the agent loop to exit
        # at the next check point.
        if effective_mode == "interrupt" and running_agent and running_agent is not _AGENT_PENDING_SENTINEL:
            try:
                running_agent.interrupt(event.text)
            except Exception:
                pass  # don't let interrupt failure block the ack
```

Primary routing decision. Subagent protection (demoted_for_subagents) is lines 3644-3654 — slightly BEFORE the cited ~3656; it demotes interrupt->queue when _agent_has_active_subagents(running_agent) is true. The steer attempt + fall-back-to-queue is lines 3656-3672 (matches ~3656-3672): steer() failure / empty text / sentinel / missing steer() => effective_mode='queue'. A SUCCESSFUL steer (steered=True) skips merge_pending_message_event so the text is not also replayed as a next-turn message. Interrupt fires at 3692 only when effective_mode stayed 'interrupt'.

### Gateway PRIORITY routing path: queue short-circuit, steer with steer-fallback-to-queue, and PRIORITY subagent protection (#30170) demoting interrupt to queue.

/Users/eriklee/code/agent/hermes-agent/gateway/run.py:6865-6908

```python
            if self._busy_input_mode == "queue":
                logger.debug("PRIORITY queue follow-up for session %s", _quick_key)
                self._queue_or_replace_pending_event(_quick_key, event)
                return None
            if self._busy_input_mode == "steer":
                # Steer mode: inject text into the running agent mid-run via
                # agent.steer().  Falls back to queue semantics if the payload
                # is empty, the agent lacks steer(), or steer() rejects.
                steer_text = (event.text or "").strip()
                steered = False
                if steer_text and hasattr(running_agent, "steer"):
                    try:
                        steered = bool(running_agent.steer(steer_text))
                    except Exception as exc:
                        logger.warning("PRIORITY steer failed for session %s: %s", _quick_key, exc)
                        steered = False
                if steered:
                    logger.debug("PRIORITY steer for session %s", _quick_key)
                    return None
                logger.debug("PRIORITY steer-fallback-to-queue for session %s", _quick_key)
                self._queue_or_replace_pending_event(_quick_key, event)
                return None
            # #30170 — Subagent protection (PRIORITY path). Same rationale
            # as ``_handle_active_session_busy_message``: an interrupt
            # cascades through ``_active_children`` and aborts in-flight
            # delegate_task work. Demote to queue semantics when the
            # parent is currently driving subagents so a conversational
            # follow-up doesn't destroy minutes of subagent progress.
            # /stop reaches its dedicated handler above, so the operator
            # still has a clean escape hatch.
            if self._agent_has_active_subagents(running_agent):
                logger.info(
                    "PRIORITY interrupt demoted to queue for session %s "
                    "because the running agent has active subagents (#30170)",
                    _quick_key,
                )
                self._queue_or_replace_pending_event(_quick_key, event)
                return None
            logger.debug("PRIORITY interrupt for session %s", _quick_key)
            running_agent.interrupt(event.text)
            # NOTE: self._pending_messages was write-only (never consumed).
            # The actual interrupt message is delivered via adapter._pending_messages
            # which is read by _run_agent. Removed to prevent unbounded growth.
            return None
```

The PRIORITY mirror of the main routing. queue mode short-circuit is 6865-6868; the steer branch + steer-fallback-to-queue is 6869-6886 (matches ~6869-6886) — on steer() failure it calls _queue_or_replace_pending_event. The PRIORITY subagent protection is 6887-6902 (just after the cited 6886): if _agent_has_active_subagents it demotes the interrupt to a queue. Actual interrupt is 6904. /stop is handled earlier (6841) so the operator keeps an escape hatch.

### The _agent_has_active_subagents helper used by both subagent-protection demotions.

/Users/eriklee/code/agent/hermes-agent/gateway/run.py:3486-3522

```python
    @staticmethod
    def _agent_has_active_subagents(running_agent: Any) -> bool:
        """Return True when *running_agent* is currently driving subagents
        via the ``delegate_task`` tool.

        Background (#30170): ``AIAgent.interrupt()`` cascades through the
        parent's ``_active_children`` list and calls ``interrupt()`` on
        every child synchronously, which aborts in-flight subagent work
        and produces a fallback cascade with no actionable signal.
        Demoting ``busy_input_mode='interrupt'`` to ``queue`` semantics
        whenever this helper returns True protects subagent work from
        conversational follow-ups while leaving the explicit ``/stop``
        path (which goes through ``_interrupt_and_clear_session``)
        untouched. Safe-by-default: returns False on any attribute or
        lock error so a missing/broken parent never blocks the existing
        interrupt path.
        """
        if running_agent is None or running_agent is _AGENT_PENDING_SENTINEL:
            return False
        children = getattr(running_agent, "_active_children", None)
        # AIAgent always initialises this as a concrete list (see
        # agent/agent_init.py). Reject anything that isn't a real
        # collection — this guards against ``MagicMock()._active_children``
        # auto-creating a truthy stub in tests and triggering the demotion
        # against an agent that doesn't actually have subagents.
        if not isinstance(children, (list, tuple, set)):
            return False
        if not children:
            return False
        lock = getattr(running_agent, "_active_children_lock", None)
        try:
            if lock is not None:
                with lock:
                    return bool(children)
            return bool(children)
        except Exception:
            return False
```

This @staticmethod (line 3487) is the predicate driving both subagent-protection branches. It reads running_agent._active_children under _active_children_lock, returning True only when that is a real non-empty list/tuple/set. It is safe-by-default (returns False on any error or on the pending sentinel) so a broken/missing parent never blocks the normal interrupt path, and it explicitly rejects non-collection stubs to avoid false demotions in tests.

## Control flow

DRAIN SIDE (agent loop): Each iteration of the conversation loop first calls agent._drain_pending_steer() PRE-API (conversation_loop.py:534) — if a steer arrived while the model was thinking, it is injected into the last tool-role message so the model sees it THIS iteration; if there is no tool message to inject into (e.g. first iteration), it is put back under the lock for a later drain. After the model returns tool calls, the executor runs them: in BOTH the parallel (tool_executor.py) and sequential paths, _apply_pending_steer_to_tool_results(messages, 1) is called PER-TOOL right after each tool result is appended (lines 753 and 1385) so a steer lands the moment a tool finishes rather than after the whole batch; then after per-turn budget enforcement, _apply_pending_steer_to_tool_results(messages, num_tools) is called PER-BATCH (lines 766 and 1420) — run AFTER budget enforcement so the steer marker is never truncated. Finally, turn_finalizer.py:360 does a leftover _drain_pending_steer(): if a steer landed after the final assistant turn (no more tool batches to drain into), it is attached to the finalized result as result["pending_steer"] so it can be delivered as the next user turn instead of being lost.

GATEWAY SIDE (routing): When a message arrives for a busy session, the gateway computes effective_mode = self._busy_input_mode. TEXT messages can short-circuit to queue if _busy_text_mode=='queue' and mode!='steer'. Before acting on 'interrupt', it checks _agent_has_active_subagents(running_agent); if true and mode=='interrupt' it DEMOTES to 'queue' (#30170) so a follow-up doesn't cascade-abort delegate_task subagents. If effective_mode=='steer', it tries running_agent.steer(text); on empty text / missing agent / sentinel / exception / steer() returning False it FALLS BACK to queue (effective_mode='queue'). Successful steers skip the merge_pending_message_event replay. If still 'interrupt', it calls running_agent.interrupt(event.text). The PRIORITY path (~6865+) mirrors this: queue mode -> _queue_or_replace_pending_event; steer mode -> steer() with steer-fallback-to-queue; otherwise subagent check demotes to queue, else interrupt.

## Corrections

Paths and line numbers are essentially accurate. Precise corrections: (1) conversation_loop.py pre-API drain is exactly line 534 (matches ~534). (2) tool_executor.py PARALLEL path: per-tool drain is line 753 and per-batch is line 766 (task said ~750-766, correct). The SECOND block (~1385-1420) is the SEQUENTIAL path, not a second parallel block: per-tool line 1385, per-batch line 1420 (matches). (3) turn_finalizer.py leftover drain is line 360 (matches ~360). (4) gateway/run.py: the steer-vs-queue-vs-interrupt block in _handle_active_session_busy_message spans ~3623-3697; the steer attempt + fall-back-to-queue is lines 3656-3672 (matches), but the subagent-protection demotion (demoted_for_subagents) is at lines 3644-3654, slightly BEFORE the cited 3656 range. (5) The PRIORITY path: steer + steer-fallback-to-queue is lines 6869-6886 (matches), queue-mode short-circuit at 6865-6868, and PRIORITY subagent protection (interrupt demoted to queue) is at lines 6887-6902 — just AFTER the cited 6886 range — with the actual interrupt at 6904. (6) The _agent_has_active_subagents helper is a @staticmethod defined at line 3487.
