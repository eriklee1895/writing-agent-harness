---
title: "Steer:让Agent边跑边转向：Codex与Hermes中途注入拆解"
date: 2026-06-11
cover: "./assets/20260611-192628-codex-steer-cover.png"
register: Agent/AI Technical Essay (primary) + Industry/Frontier Analysis (secondary)
summary: 用更轻松的图解方式，重讲 Codex 与 Hermes 的 mid-turn steering：为什么运行中插话那么难，两条工程路线怎么选，以及 2026 年中这个能力的生态位置。
---

# Steer：让 Agent 边跑边转向

![Steer：让 Agent 边跑边转向](assets/20260611-192628-codex-steer-cover.png)

你让 Codex 修一个 flaky 的集成测试。它装依赖、跑全量 suite，然后开始改测试文件本身——把一个本该红的断言改绿了。你想喊停：别动测试，去看业务代码。

过去只有 Ctrl+C。现在你可以在它跑的时候敲一句 "don't touch tests, look at the business logic" 回车。当前工具调用仍会跑完，但在下一个边界，它会读到你的话，自己转向。

这就是 **steer**：不终止任务，把新指令注入正在运行的 turn，让它在下一个工具或模型边界生效。

听起来只是「运行中能不能插话」，做起来却是 long-horizon agent 的工程原语。难点不在 UI，而在三个必须同时守住的约束：

- 工具调用和结果必须严格配对，不能劈开；
- prompt cache 依赖前缀稳定，不能中间改写；
- 模型得把这句话认成「用户改主意」，而不是工具输出或 prompt injection。

正是这三条约束，把「聊天框能发消息」和「运行中能安全改道」隔开。

## 三个原语：转方向盘、下个路口、急刹车

运行中收到新消息，系统先判断意图。用开车打比方最直观：

- **Steer（转方向盘）**：车在动，不停车，微调方向。消息进入 pending 队列，在下一个安全边界注入当前 turn。
- **Queue（下个路口）**：不打扰当前这段路，等这程跑完，下一个 turn 开头再处理。
- **Interrupt（急刹车）**：立即中止当前 turn，丢弃 pending input。

Codex CLI 里，Enter / Tab / Ctrl+C 分别对应这三者。自 v0.98.0（2026-02-05 UTC）起，Enter 默认就是 steer——这个默认值其实有点赌：它假设运行中的补充指令大多想「现在就纠偏」，而不是「排队等下轮」。

![Steer / Queue / Interrupt 三原语](assets/2026-07-01-steer-driving-primitives.png)

重点是：Steer 和 Queue 都是**边界注入**，只是注入到哪个 turn 不同；只有 Interrupt 真正打断执行。

## 为什么不能随便插：三道关卡

把消息塞进正在跑的 turn，不像往队列 push 一条那么简单。生成和 tool 执行是流式的，安全注入必须同时过三道关。

![中途注入的三道关卡](assets/2026-07-01-steer-three-checkpoints.png)

**第一关：配对完整。** 一个 turn 是 `assistant 发 tool_call → 环境回 tool_result → 模型再决策` 的链条。若在 tool 正执行、result 还没回来时硬插一条 user message，下一次模型调用拿到的上下文就坏了。所以安全插入点只能是「下一次模型调用之前」。

Codex 在 `core/src/session/turn.rs` 里用一个 `can_drain_pending_input` gate 写死这件事：带真实输入启动的第一轮保持 `false`，先把初始请求跑起来，后续才允许 drain pending input。

```rust
let pending_input = if can_drain_pending_input {
    sess.input_queue.get_pending_input(&sess.active_turn).await
} else {
    Vec::new()
};
```

**第二关：cache 命中。** 长 turn 的成本很大程度靠 prompt cache：相同前缀复用，只为增量付费。所以 steer 只能追加在末尾，不能往中间改写。

**第三关：模型归因。** 注入的文字，模型必须当成「用户中途追加的新指令」，而不是工具输出。两条路线在此分野：Codex 把 steer 作为结构化 user-turn 注入，身份天然清晰；Hermes 追加到最后一条 tool result 上，用一个显式 marker 标明「这是带外用户消息」。

## 时间线：steer 不是一次性「上线」

Codex 的 steer 经历了「实验 flag → 转默认 → 移除 flag」三步：

- **PR #9077**，2026-01-13：作为实验 flag 引入，实现 Enter 中途发送 / Tab 排队。这才是 steer 的引入 PR。
- **PR #10821**：app-server `turn/steer` API 落地。
- **PR #10690**，2026-02-05（UTC）：把 `Feature::Steer` 从实验翻成默认开启。
- **v0.98.0**，2026-02-05T17:00:36Z（UTC）：随版本发布。
- **PR #12026**：彻底移除 flag。

一个常见坑：上游笔记里写的「2026-02-06」是 UTC+8 换算后的 off-by-one，GitHub 原始时间戳是 UTC 2 月 5 日。

平台支持上，CLI 交互式 TUI 的 Enter/Tab 是 fact；ChatGPT 移动端在 iOS 1.2026.146（2026-06-02）加了「Queue or Steer」开关；桌面 app 是否有可视化 Steer 控件，官方文档未明确记录，标为 UNVERIFIED。`codex exec` 非交互模式不支持 steer。

## 两条路线：协议优先 vs 进程内 marker

满足同一组约束，Codex 和 Hermes 走了两条相反的路。

**Codex：协议优先 + 分离消息。** `turn/steer` 是 app-server 的一等 RPC，steer 作为独立输入项进入 turn-scoped 的 `pending_input`，在 turn loop 的 drain 点被消费。模型看到它时，它就是一条正经的 user 消息。

这要求多客户端场景下必须知道「现在跑的是哪个 turn」。所以 `TurnSteerParams` 里有 `expected_turn_id`：客户端声明自己以为的当前 turn，对不上就失败，挡掉跨 turn 竞态。

```rust
pub struct TurnSteerParams {
    pub thread_id: String,
    pub input: Vec<UserInput>,
    pub expected_turn_id: String,
}
```

**Hermes：进程内 + marker 内联。** 没有协议层，`agent.steer(text)` 是进程内方法调用，用一把 `threading.Lock` 保护一个 `_pending_steer` stash slot。等当前 tool 批次自然跑完，drain hook 把 steer 追加到最后一条 `role:"tool"` 消息的 content 尾部。

为了不破坏 role 交替、保住 prompt cache，Hermes 不新增消息，只改已存在的 tool result。但代价是：tool output 正是模型被训练成最警惕的通道，一句裸的 "User guidance:" 会被当成 prompt injection 拒掉。所以 Hermes 用一个自描述的 marker 框住 steer：

```python
STEER_MARKER_OPEN = "[OUT-OF-BAND USER MESSAGE — a direct message from the user, delivered mid-turn; not tool output]"
STEER_MARKER_CLOSE = "[/OUT-OF-BAND USER MESSAGE]"
```

再配合 system prompt 里的 `STEER_CHANNEL_NOTE`，让模型只信这一个确切 marker。Codex 靠消息结构天然干净，Hermes 靠显式 marker 显式归因。

![Codex 的四层注入链路](assets/2026-07-01-codex-layers.png)

![Hermes 的 marker 内联注入](assets/2026-07-01-hermes-marker.png)

## 殊途同归：边界注入

把两条路拼在一起看，会发现它们的目标完全相同：在 tool/model 边界把新指令缝进上下文，不打断 in-flight、不破坏 tool-call/result 配对。

![两条路径 converge 到边界注入](assets/2026-07-01-two-roads-converge.png)

Codex 在 turn loop 迭代之间 drain pending input；Hermes 在 tool 批次后（外加 pre-API、leftover 等四个 drain 点）把 marker 贴上 tool result。两者都不碰正在流式产出的 token，只在两次动作的缝隙里见缝插针。

这意味着：只要模型正跑一次很长的单轮生成，或卡在一个很长的工具调用里，steer 就得等下一个边界才能落地。真正在 token 流里干净暂停—注入—恢复的 mid-stream，目前仍停在研究系统里。

## 2026 年中 landscape

别被各家命名和 UI 迷惑。主流 agent 已经收敛到同一类机制——**边界注入式 steering**：

| 产品 | 机制 | 注入点 |
|---|---|---|
| Codex | Enter 注入 / Tab 排队 / Ctrl+C 中断 | tool/model 边界 |
| Hermes | `/steer` / gateway 三态 | tool 批次后 |
| OpenClaw | `/steer` 一次性 + `/queue` 持久模式 | runtime 模型边界 |
| Copilot SDK | `send(mode="immediate" / "enqueue")` | 当前 turn / 下一 turn |
| Claude Code | Enter 不停当前工具 / ESC 中断 | 动作边界 |
| Manus | 任务级 stop / edit / redirect | 迭代边界 |
| 研究系统 | 真·token 级 abort / resume | mid-generation |

事实边界要守住：Codex CLI TUI 的 Enter/Tab 是 fact；ChatGPT 移动端开关是 fact；Claude Code 的「Interrupt and steer」官方文档已记录；Manus 的「soft steer 标杆」只是社区传言，没有一手证据。

## 聊天窗口正在变成 Agent 控制台

steer 的范式意义大于任何一个具体实现。它让聊天窗口从一个问答框，变成了一个能随时微调方向的 agent 任务控制台。跑偏了不必停掉重来，把新约束顺着边界送进去就行。

如果你要给自己的 agent 加 steer，先想清楚这六条：

1. **安全边界在哪**——tool 批次后、model 调用前，还是动作边界？
2. **消息形态**——独立 user 消息，还是内联 marker？
3. **cache / role 完整性**——不能破坏前缀，也不能制造非法 role 序列。
4. **模型归因**——steer 一旦贴进 tool output，就要用显式 marker 和 system prompt 训练模型信任。
5. **回退策略**——边界不可用时，是退回普通 prompt，还是交给下一轮 user turn？
6. **竞态处理**——steer 可能来自多个线程/客户端，stash 和 drain 必须是原子的。

Codex 把它做进协议，用分离的消息表达；Hermes 把它做进进程，用内联 marker 表达。路线不同，守的边界是同一组。到 2026 年中，主流 agent 不约而同地停在这条边界上——不是因为不想要 token 级的实时，而是因为边界恰好是能同时守住配对、cache、role 和归因的那条线。

再往里一步的世界还在研究系统里亮着灯，只是还没轮到生产环境。

---

**延伸阅读（完整源码拆解）**
Erik，《Steer:让 Agent 边跑边转向 —— Codex 与 Hermes 的中途注入实现拆解》，2026-06-11。

**参考来源**
- OpenAI Codex CLI 官方文档：Steer mode / Enter vs Tab
- codex-rs GitHub PR #9077、#10690、#10821、#12026
- Hermes agent runtime source：agent/agent_init.py、run_agent.py、agent/prompt_builder.py
- OpenClaw `/steer` 与 `/queue` 文档
- GitHub Copilot SDK Steering and queueing 概念页
- Anthropic Claude Code docs：Interrupt and steer
