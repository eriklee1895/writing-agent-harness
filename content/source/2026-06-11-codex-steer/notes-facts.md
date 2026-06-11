# notes-facts.md — Codex Steer 报告 研究与核查底稿

> 生成于 2026-06-11。本文件是写作的事实底稿。所有写作 agent 必须以本文件 + 同目录 `notes-codex-*.md` / `notes-hermes-*.md`(verbatim 源码)为准。
> **凡与上游 Notion 笔记冲突处,以本文件为准** —— 笔记里有 4 处已被一手来源推翻(见 B 节)。

---

## A. 已核实关键事实(写作直接引用,务必带日期/来源)

### A1. Codex Steer 的完整生命周期(一手:GitHub release + PR,gh CLI 核验)

| 阶段 | PR / 版本 | 日期(UTC) | 做了什么 |
|---|---|---|---|
| **引入(实验)** | **PR #9077** "Send message by default mid turn. queue messages by tab" (@aibrahim-oai) | created 2026-01-12 / **merged 2026-01-13** | 加入 `steer_enabled` feature flag(features.rs),在 TUI chat composer(tui + tui2)实现 Enter 中途发送 / Tab 排队,并加 pending_input 测试套件。**这才是 Steer 的"上线/引入"PR。** |
| 提交键修正 | PR #9218 "fix(tui2): align Steer submit keys" | merged 2026-01-14 | Enter 在 Steer 启用时立即提交 |
| app-server API | **PR #10821** | Jan/Feb 2026 | app-server 协议层 `turn/steer` API 落地 |
| **提升为稳定+默认** | **PR #10690** "Make steer stable by default" (@aibrahim-oai) | created 2026-02-04 / **merged 2026-02-05T07:13Z**(merge commit cd5f49a) | 仅改 **1 个文件** `codex-rs/core/src/features.rs (+2/-6)`:`Feature::Steer` 从 `Stage::Experimental{default_enabled:false}` → `Stage::Stable{default_enabled:true}`。**它没有"上线"功能,只是把已存在的实验特性翻成默认开。** |
| 随版本发布 | **v0.98.0 (rust-v0.98.0)** | **published 2026-02-05T17:00:36Z**(tag created 16:12:44Z) | Release note 原文(## New Features):"Steer mode is now stable and enabled by default, so `Enter` sends immediately during running tasks while `Tab` explicitly queues follow-up input. (#10690)"。版本摘要行:"Steer mode stable, fixes model instruction handling and resume bugs"。 |
| 移除 flag | **PR #12026** "Remove steer feature flag" | 2026(晚于上) | 彻底删除 steer feature flag |

> **日期更正**:Notion 笔记写的 "2026-02-06" 是 **off-by-one**。GitHub 时间戳是 2026-02-05 17:00 UTC;按 UTC+8(亚太)换算正好落到 2026-02-06。**报告统一记 2026-02-05(UTC),并可一句话点明时区差异**。
> **PR 更正**:笔记把 #10690 当成"Steer 上线 commit"。正确表述:**#9077 引入(2026-01-13,实验 flag)→ #10690 转稳定默认(2026-02-05)→ #12026 移除 flag**。

### A2. 官方文案的两个不同 surface(别混为一谈)

- **OpenAI Academy「Working with Codex」**(页面日期 2026-04-23,GUI 语境,讲的是可点击的 "Steer" 按钮):
  > "If you forget to mention something, you do not have to stop Codex and start over. Type in your new instruction and select **Steer** to course correct while it is working."
  - ⚠️ Academy 页面**只字未提 Enter/Tab 键位**。
- **Codex CLI features docs**(developers.openai.com/codex/cli/features,终端 TUI 语境):
  > "Press **Enter** while Codex is running to inject new instructions into the current turn, or press **Tab** to queue follow-up input for the next turn."
- 结论:**GUI = "Steer" 按钮(Academy);CLI TUI = Enter 注入当前 turn / Tab 排到下一 turn**。两个 surface 文案不同。

### A3. `/fork` 时间线 + 平台矩阵(更正笔记)

- `/fork`:底层 fork 协议/app-server endpoints 在 **v0.80.0(2026-01-09, PR #8866)**;用户可见的 `/fork the current session` 命令在 **v0.88.0(2026-01-21, PR #9385)**。笔记的 "v0.81–0.87 alongside steer" 只能算早期开发窗口的粗略说法。
- 平台:Steer 支持 **CLI 交互式 TUI**(Enter/Tab,自 v0.98.0 默认);**ChatGPT 移动端**(iOS 在 1.2026.146 / 2026-06-02 加入 "Queue or Steer" 默认跟进开关)。**Desktop app(macOS/Windows)官方文档未明确记录 app 内 steer 控件 —— 对桌面版"可视化 Steer 按钮"的说法 UNVERIFIED**,不要当确定事实写(Academy 的按钮是 ChatGPT/Codex web/app GUI 语境)。
- `codex exec`(非交互)**不支持 Steer(CONFIRMED)**:无 `--steer` flag;stdin 仅在启动时一次性消费;输出是单向流;要改方向只能用 `resume` 子命令开新 run。**Nuance**:exec 内部用 `InProcessAppServerClient` 跑同一套定义了 `turn/steer` 的 app-server 协议,但**不对外暴露任何 steer 入口**。(fork 同样 TUI-only;exec-fork PR #13537 closed unmerged;issue #11750 / #17568 open。)

---

## B. 对抗式核查结论(6 条;4 条 refuted)

| 论断 | 结论 | 更正 / 要点 | 一手来源 |
|---|---|---|---|
| v0.98.0 于 2026-02-06 发布并使 Steer 稳定默认 | **refuted(日期错)** | 日期应为 **2026-02-05 UTC**;Steer 稳定默认部分正确 | github.com/openai/codex/releases/tag/rust-v0.98.0 |
| PR #10690 是"上线 Steer"的 PR | **refuted** | #10690 只把 Experimental→Stable+默认;Steer 由 **#9077(2026-01-13)** 引入 | github.com/openai/codex/pull/10690 |
| Manus 支持真·mid-stream(token 级暂停/恢复注入) | **refuted** | Manus 是 append-only event-stream,在**迭代/turn 边界**注入(与 Codex/Hermes 同级);"soft steer 标杆"是社区传言(源自 OpenClaw issue #10960 的无据 "reportedly") | manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus |
| Claude Code 截至 2026-06 无原生 steer | **refuted** | 官方 docs 有 **"Interrupt and steer"** 段:输入修正 + Enter 不停当前工具发送,Claude 在当前动作完成后读取并在下一步前调整(保留已完成工作);ESC 中断;`/btw` 侧聊。**Claude Code 已有原生 steer(动作边界注入)** | code.claude.com/docs/en/how-claude-code-works ; /commands ; /interactive-mode |
| OpenClaw /queue 有 6 个 mode | **refuted** | 当前英文 canonical = **4 个**:steer(默认)/followup/collect/interrupt。"queue" 是命令名+legacy 别名(迁移成 steer);"steer-backlog" 是 deprecated 别名(规范化成 followup)。笔记的 6 项匹配的是**过时 zh-CN 翻译** | github.com/openclaw/openclaw/blob/main/src/config/types.queue.ts |
| `codex exec` 不支持 Steer | **confirmed** | 见 A3 nuance(协议层有,用户面无入口) | developers.openai.com/codex/noninteractive |

> **Claude Code 的措辞冲突需注意**:claude-code-guide agent 说"Enter 排队到当前动作完成后投递(非动作中)";对抗 verify 引官方 docs 称其为"Interrupt and steer / Enter-to-steer"。**二者其实是同一机制的不同叫法**——消息都在**下一个动作/工具边界**投递(不打断正在跑的工具)。写作时按官方 docs 用 "steer" 这个词,但精确说明它发生在动作边界、不中断当前工具。**这反而是报告的新洞察:到 2026 年中,全行业(Codex/Hermes/OpenClaw/Copilot SDK/Claude Code)都收敛到"边界注入式 steering";真·token 级 mid-stream 仍主要停留在研究系统(AgentScope asyncio 取消、AIOS context snapshot/restore、ChipChat KV-cache 清理),并非 Manus。** Notion 笔记两头(Claude Code 无 steer / Manus 真 mid-stream)都已过时。

---

## C. 8 个研究主题 summary(verbatim,写作素材)

### C1. codex-release
All three questions verified against primary sources. (a) YES — Steer mode marked stable + default in v0.98.0 via PR #10690 ("Make steer stable by default", @aibrahim-oai). (b) Exact release date 2026-02-05 (UTC): GitHub publishedAt = 2026-02-05T17:00:36Z, tag createdAt = 2026-02-05T16:12:44Z. Notion 的 2026-02-06 是 UTC+8 时区导致的 off-by-one。(c) Verbatim release note: "Steer mode is now stable and enabled by default, so `Enter` sends immediately during running tasks while `Tab` explicitly queues follow-up input. (#10690)"。术语用 "Steer mode"。注:changelogs.directory 403,用 firecrawl 抓取;权威数据来自 gh CLI 查 tag rust-v0.98.0。developers.openai.com/codex/changelog 现在只显示 ~0.136–0.140(2026-06),v0.98.0 不在窗口内,靠查具体 tag 确认。

### C2. pr-10690
#10690 IS about Steer 但没"上线"它,只把 Experimental→Stable+默认。Title "Make steer stable by default"。Author aibrahim-oai。created 2026-02-04, merged 2026-02-05T07:13:00Z(merge commit cd5f49a)。diff 只动 1 文件 `codex-rs/core/src/features.rs (+2/-6)`,把 `Feature::Steer` 从 `Stage::Experimental{default_enabled:false}` 改成 `Stage::Stable{default_enabled:true}`。真正引入 Steer 的是 **#9077**(@aibrahim-oai, "Send message by default mid turn. queue messages by tab", created 2026-01-12, merged 2026-01-13):加 steer_enabled flag + 跨 TUI chat composer 实现 Enter-中途发送/Tab-排队 + 新 pending_input 测试(24 文件大 diff)。Steer 自 2026-01 中旬作为实验特性存在;#10690 在约 3 周后设为默认。

### C3. academy-doc
OpenAI Academy "Working with Codex"(页面日期 2026-04-23)是请求的来源。它用两句话+一个例子描述 Steer,全部围绕 app/ChatGPT GUI 里可点击的 "Steer" 按钮——**不提任何 Enter/Tab 键位**。Verbatim: "If you forget to mention something, you do not have to stop Codex and start over. Type in your new instruction and select Steer to course correct while it is working." Enter/Tab 区分在另一处官方 CLI features docs(developers.openai.com/codex/cli/features,针对终端 TUI):"Press Enter while Codex is running to inject new instructions into the current turn, or press Tab to queue follow-up input for the next turn." 两个不同官方 surface。Academy 页面无版本号/PR/发布日,唯一日期是 2026-04-23。(403,用 firecrawl 抓取。)

### C4. fork-platforms
(a) 时间线:fork 协议/app-server endpoints 在 v0.80.0(2026-01-09, PR #8866);用户可见 "/fork the current session" 在 v0.88.0(2026-01-21, PR #9385)——在 v0.81–0.87 "忙碌周"(Jan 14–16)之后。Steer TUI 工作在 v0.81 窗口合入(#9218 merged 2026-01-14),但直到 v0.98.0(2026-02-05)才作为 release-note 特性宣布(stable+默认, #10690)。(b) Surfaces:CLI TUI(Enter 立即/Tab 排队,自 v0.98.0 默认)+ ChatGPT 移动端(iOS "Queue or Steer" 跟进开关,1.2026.146, 2026-06-02)。Desktop app 是 macOS+Windows 但官方文档未明确记录 app 内 "steer" 控件(app docs 里 "steer" 指移动端驱动 steering 连接的 host)——桌面 UNVERIFIED。codex exec 不支持 steer 论据充分(steer 靠交互 Tab/Enter,exec 没有);fork 也 TUI-only(报错 "stdin is not a terminal"),exec-fork PR #13537 closed unmerged 2026-04-17,issue #11750 / #17568 OPEN。

### C5. openclaw
对照 OpenClaw canonical docs。两个权威英文源一致(GitHub raw main: docs/concepts/queue.md, queue-steering.md, tools/steer.md;以及 live 英文站 docs.openclaw.ai)。live 中文页(docs.openclaw.ai/zh-CN/concepts/queue)是 STALE/分叉翻译。**关键更正**:当前英文 canonical 定义**恰好 4 个 /queue mode** —— steer(默认)/followup/collect/interrupt,**不是 6 个**。"queue"(legacy)和 "steer-backlog"/"steer+backlog" 不在当前英文 docs 或 GitHub main 出现;它们只出现在过时 zh-CN 页(仍记 6-mode)。**默认 mode = steer**(verbatim: mode "steer", debounceMs 500, cap 20, drop "summarize")。早前 WebFetch 说默认 "collect" 是 summarizer 幻觉,被 raw markdown 推翻。**Pi runtime**:当前英文 docs 不再用 "Pi runtime",改称 "OpenClaw"/"the active runtime"。model-boundary 注入算法(5 步)有记录但归于 "OpenClaw"。zh-CN 仍把同样步骤归给 "Pi"(并用 runEmbeddedPiAgent)。原因:merged PR #85341("refactor: internalize OpenClaw agent runtime", steipete, 2026-05-27)"remove pi runtime internals" 并把 Pi-shaped surface 改名为 OpenClaw agent runtime、删除过时 Pi docs。所以 **"Pi" 是旧内部 runtime 名(源自 pi-mono),现已改名内化**;zh-CN 反映改名前术语。/steer vs /queue:/steer 是显式一次性命令,尝试在下一个支持的 runtime 边界把消息注入活动 run,无视存储的 /queue 设置,注入不可用则退回普通 prompt;/queue steer 是持久 per-session 模式,让未来所有普通入站消息都尝试 steering。

### C6. copilot-sdk
确认:GitHub Copilot SDK 有 "Steering and queueing" 页,明确区分 steering(注入当前/活动 LLM turn)vs queueing(缓冲到当前 turn 结束后处理)。URL https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/steering-and-queueing 是 live canonical(200);/use-copilot-sdk/ 是 301 别名。两种行为通过**单个 send 方法**(session.send / SendAsync / Send)的 MessageOptions 上 `mode` 字段暴露——**没有独立 steer()/queue() 方法**。mode="immediate" = steering(注入当前 turn);mode="enqueue" = queueing(默认;FIFO,每条消息一个完整新 turn)。session idle 时两者行为相同(立即开新 turn)。若 turn 在 steering 消息被消费前结束,它退回到下一 turn 队列的队首。内部名 ImmediatePromptProcessor(中等置信)。无 SDK 版本号/日期/PR(docs 未给)。与 DeepWiki 镜像(github/copilot-sdk,索引 2026-05-21, commit 477834f8)交叉确认 immediate/enqueue 区分。

### C7. manus
VERDICT:强论断无一手证据支持,应标 **SPECULATION**。未找到任何 Manus 一手来源(engineering blog 2025-07-18、官方 docs、open.manus.ai API docs、Manus 1.5 release 2025-10)描述技术意义上的真·mid-stream 注入(token 流中途干净暂停/中止+注入+恢复)。最可能来源:第三方 GitHub feature request **openclaw/openclaw issue #10960**("Feature request: Mid-stream message injection (soft steer)", opened 2026-02-07),其 "Prior art" 写 "Manus AI has this feature and it's reportedly very useful…" —— 无链接、无证据、带 "reportedly"。这是把 Manus 当**未经证实的 prior art** 引用的 feature request,不是 Manus 的文档。well-attested 的是:(1) Manus 让用户在**任务级**停止/编辑/重定向运行中的任务(App Store 营销;task.sendMessage/task.stop API);(2) 架构上(逆向 + Manus blog)Manus 在 agent-loop/迭代**边界**经 event stream 处理新输入(一次一个 tool action,请求变了就 re-plan)。Manus blog 唯一相关说法("用户给新输入时 Manus 必须立即回复")用的是 turn **开始**处的 logit masking——边界机制,与 mid-token 中断相反。**底线**:Manus 支持运行中任务的边界级 steering(fact,中高置信);真·token 级 mid-generation 暂停/中止/注入/恢复 unverified、无支持,标 speculation,为真的置信 LOW。文献里真正记录 token 级 abort/resume 的是**别的系统**(AgentScope asyncio cancellation、AIOS context snapshot/restore、ChipChat KV-cache clearing),不是 Manus。

### C8. claude-code(注:此为 claude-code-guide agent 的结论,与 B 节对抗 verify 有措辞冲突,以官方 docs/verify 为准)
Claude Code 截至 2026-06,在用户面 UI 上"无 native mid-turn steer"(该 agent 措辞)。官方文档:ESC 立即中断;ENTER 把消息排队到当前 tool action 完成后投递(非动作中)。/btw 命令(2026-03 上线)用侧聊机制提问而不打断主任务。内部:社区逆向(PromptLayer, DeepWiki)记录单线程 master loop 代号 'nO' 跑 `while(tool_call)`,配一个 async 双缓冲队列 'h2A' 支持 pause/resume。但这些内部名和架构细节**非 Anthropic 官方文档**,是社区推断。Anthropic 官方更泛地描述为 'agentic loop'。
> ⚠️ **写作取舍**:对抗 verify(引官方 "How Claude Code works" 的 "Interrupt and steer" 段)显示 Claude Code **确有** Enter-to-steer(动作边界注入,不停当前工具)。两个 source 描述的是同一边界机制,只是是否叫它 "steer" 不同。**报告按官方术语承认 Claude Code 有 steer**,但精确指出它在动作边界生效、不中断当前工具,与 Codex/Hermes 同属"边界注入"类。nO/h2A 仅作社区逆向、需标注。

---

## D. 源码路径/行号更正(写作引用 file:line 必须用这里的精确值)

> verbatim 代码见同目录 `notes-codex-protocol-core.md` / `notes-codex-turnloop-tui.md` / `notes-hermes-core.md` / `notes-hermes-drain-gateway.md`。仓库根:Codex = `/Users/eriklee/code/coding-agent/codex/codex-rs/`,Hermes = `/Users/eriklee/code/agent/hermes-agent/`。

### D1. codex-protocol-core
- `TurnSteerParams` = `app-server-protocol/src/protocol/v2/turn.rs:154-175`;`TurnSteerResponse`(就一个 `{ turn_id }`)= `:177-182`;`TurnInterruptParams/Response` = `:184-195`。
- `Session::steer_input` 主体 = `core/src/session/mod.rs:3240-3313`(正确)。另有两个 entry point:Session/Codex 薄包装 `mod.rs:764-781`、`CodexThread::steer_input` `core/src/codex_thread.rs:262-275`,都 delegate 到 3240。
- `SteerInputError` enum = `core/src/session/mod.rs:232-238`(`to_error_event` impl `:240-269`)。**`NonSteerableTurnKind` 不在 core**,在 `codex-protocol`:`codex-rs/protocol/src/protocol.rs:1606-1613`,core 通过 `use codex_protocol::protocol::NonSteerableTurnKind`(`mod.rs:348`)复用。**跨两个 crate,别写成同一文件。**
- `InputQueue`:`extend_pending_input_and_accept_mailbox_delivery_for_turn_state` = `input_queue.rs:143-151`(steer_input 调的是这个);`extend_pending_input_for_turn_state` = `:153-159`。`TurnInput`/`TurnInputQueue` = `input_queue.rs:12-25`。**`pending_input` 字段本身不在 input_queue.rs**,是 `TurnState` 的字段,在 `core/src/state/turn.rs:93`(TurnState struct `:86-100`)。

### D2. codex-turnloop-tui
- `get_pending_input` / `has_pending_input` 等**定义在 `core/src/session/input_queue.rs`**(`get_pending_input:172-204`、`has_pending_input:210-231`),turn.rs 只是**调用**(turn.rs:206, 248)。**没有 `needs_follow_up` 函数**;`needs_follow_up` 是 turn.rs:257 的局部 bool。
- turn.rs ~407 处确实是 `run_hooks_and_record_inputs`(`:407-433`)。
- 真正延迟 drain 的机制是 `can_drain_pending_input` gate:声明 turn.rs:166,reset :245,auto-compact 后条件化 :295;循环注释 :196-199 记录两种 defer。
- TUI `render_in_history = !agent_turn_running` = `input_submission.rs:148`。`PendingSteer` 构造 `:322-332`,push `:386-390`。
- 三队列 struct `InputQueueState` = `tui/src/chatwidget/input_queue.rs:22-45`:`queued_user_messages`(24)、`rejected_steers_queue`(33)、`pending_steers`(40)、`submit_pending_steers_after_interrupt`(43)、`suppress_queue_autosend`(44)。
- interrupt×steer:flag 在 `interaction.rs`(handle_key_event `:129-140`)**置位**,在 `input_restore.rs`(on_interrupted_turn `:138-187`)**消费/重发**。`submit_pending_steers_after_interrupt` 是**字段**(input_queue.rs:43)不是函数。

### D3. hermes-core
- 路径行号全部精确匹配。`steer()` = `run_agent.py:2379-2413`,`_drain_pending_steer()` = `:2415-2429`。
- `run_agent.py` 另有薄转发 `_apply_pending_steer_to_tool_results`(带前导下划线)= `:2687-2690`,delegate 到 `agent/agent_runtime_helpers.py` 的真实实现 `apply_pending_steer_to_tool_results`(`:2371` 起)。
- `_pending_steer` / `_pending_steer_lock` init = `agent/agent_init.py:451`。marker 常量 + `format_steer_marker` + `STEER_CHANNEL_NOTE` = `agent/prompt_builder.py:452-472`。

### D4. hermes-drain-gateway
- pre-API drain = `conversation_loop.py:534`。
- `tool_executor.py` **并行路径**:per-tool `:753`,per-batch `:766`;**顺序路径**(不是第二个并行块):per-tool `:1385`,per-batch `:1420`。
- leftover drain = `turn_finalizer.py:360`。
- gateway `gateway/run.py`:steer-vs-queue-vs-interrupt 块在 `_handle_active_session_busy_message` `~3623-3697`;steer 尝试+回退 queue `:3656-3672`;subagent 保护降级(demoted_for_subagents)`:3644-3654`。PRIORITY 路径:steer+回退 `:6869-6886`,queue-mode 短路 `:6865-6868`,PRIORITY subagent 保护(interrupt 降级 queue)`:6887-6902`,实际 interrupt `:6904`。`_agent_has_active_subagents` @staticmethod `:3487`。

---

## E. Landscape(已更正)+ 写作 hedge 清单

### 更正后的横向 landscape(写作用)
| 产品 | steer 机制 | 注入点 | 备注(均已核实) |
|---|---|---|---|
| Codex (CLI/App) | Enter 注入当前 turn / Tab 排队 / Ctrl+C 中断;app-server `turn/steer` | tool/model 边界(turn loop drain pending_input) | 自 v0.98.0(2026-02-05)默认;Review/Compact turn 拒绝 same-turn steer |
| Hermes | `agent.steer()` / `/steer`;gateway `_busy_input_mode`=steer/queue/interrupt | tool 批次后(多点 drain),追加到最后 tool result + `[OUT-OF-BAND]` marker | 进程内 + Lock;无 tool result 时回退下轮 user 消息 |
| OpenClaw | `/steer` 一次性 + `/queue` 持久模式 | runtime 模型边界 | **4 mode**:steer(默认)/followup/collect/interrupt;debounce 500ms,cap 20 |
| Copilot SDK | `send(mode=...)` | immediate=当前 turn / enqueue=下一 turn(默认) | 单 send 方法 + mode 字段;无独立 steer() |
| Claude Code | "Interrupt and steer":Enter 修正不停工具 / ESC 中断 / `/btw` 侧聊 | 当前动作完成后(动作边界) | **已有原生 steer(2026-06 官方 docs)**;nO/h2A 是社区逆向 |
| Manus | 任务级 stop/edit/redirect | 迭代/turn 边界(append-only event stream) | **非 token 级 mid-stream**;"soft steer 标杆" = 社区传言无据 |
| (研究系统) | 真·token 级 abort/resume | mid-generation | AgentScope(asyncio cancel)/ AIOS(context snapshot)/ ChipChat(KV-cache clear) |

### 写作必须 hedge / 标注的点
- **桌面版 Codex "Steer 按钮"**:UNVERIFIED,不要写成确定。Academy 按钮是 web/app GUI 语境。
- **Manus "真 mid-stream"**:明确标为**社区传言/推断**(源自 OpenClaw issue #10960 无据 "reportedly"),并给出 Manus 实际是边界注入的一手依据。
- **Claude Code "无 steer"**:**不要写**;官方已有 "Interrupt and steer"。精确表述为动作边界 steer。
- **nO / h2A**:社区逆向命名,非官方,需标注。
- **OpenClaw "Pi"**:旧内部 runtime 名(pi-mono),已于 #85341(2026-05-27)改名内化为 "OpenClaw runtime";笔记/zh-CN 的 "Pi" 是改名前术语。提到时点明。
- **OpenClaw 6 mode / 默认 collect**:错的;用 4 mode、默认 steer。
- **日期**:Codex steer 相关统一用 **2026-02-05 (UTC)** + 必要时点明 UTC+8 off-by-one;引入是 **#9077 / 2026-01-13**。
- 凡 file:line 一律用 D 节更正值。
