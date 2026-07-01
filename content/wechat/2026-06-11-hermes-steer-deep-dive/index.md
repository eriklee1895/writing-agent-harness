---
title: "Hermes steer：一句话怎么插进跑着的agent"
date: 2026-06-11
cover: "./assets/2026-07-01-hermes-steer-cover.png"
author: "李玉恒"
register: "Agent/AI Technical Essay (primary) + Industry/Frontier Analysis (secondary)"
summary: "用更轻松的图解方式，拆开 Hermes 的 mid-turn steering：运行中的一句话为什么难插、它怎么把这句话伪装进最后一个 tool result、以及这套『marker + 系统提示』信任锚的代价。"
---

# Hermes steer：一句话怎么插进跑着的agent

![Hermes steer：一句话怎么插进跑着的agent](assets/2026-07-01-hermes-steer-cover.png)

你让 agent 重构一个模块。它读了几个文件，开始跑 `npm install`，或者拉起一整套测试 suite。进度条在爬，你已经看出来它方向错了：它在动那个你压根不想碰的抽象层。

这时候你只有两件事可做：干等它跑完再说话，或者 Ctrl+C 掐掉重来。

steer 是第三种选择：**在它跑的时候，把一句话塞进去**。

它不会打断正在跑的工具，但会在下一个安全边界让模型看见你的话，然后自己转向。听起来只是「运行中插话」，落到工程里却要同时守住三条硬约束——而 Hermes 的解法，是把这句话**伪装成最后一个 tool result 的尾巴**。

## 插话的窘境：等还是打断？

人的认知是中断驱动的。你盯着日志，某一瞬间觉得不对，就想立刻说出来。但 agent 的执行是批处理驱动的：一个 turn 里，模型规划、调用工具、等结果、再规划，中间没有自然的「听你说话」窗口。

steer 就是往这道裂缝里打的补丁。

![mid-turn 的等还是打断困境](assets/2026-07-01-hermes-turn-trap.png)

但补丁不能随便打。LLM 的消息历史不是纯文本，而是一串被严格校验的结构：

- `tool_use` 和 `tool_result` 必须成对出现；
- 承载 tool result 的 user 消息里，文本只能排在 tool result 之后；
- prompt cache 按前缀累积哈希，改动靠前的消息会让整段缓存失效。

这三条约束把「插一条 user 消息」这个直觉做法，逼成了一道优化题：

**目标**：让模型下一次迭代就收到新意图。  
**约束**：不新增消息、不动既有序列、不碰缓存前缀。

## 三道关卡

把三条约束画成三道关卡，安全落点就被压得很窄。

![中途注入的三道关卡](assets/2026-07-01-hermes-three-constraints.png)

**第一关：tool 配对完整。** assistant 发了 `tool_use`，user 必须回对应的 `tool_result`，中间不能塞任何消息。你想说话的时机，往往正好落在工具「飞行」中——这正是协议焊死的接缝。

**第二关：role 序列完整。** tool result 所在的 user 消息里，所有文本必须排在 tool result 之后。即使能追加，那也是在 tool 通道里追加，模型对 tool 通道天然更警惕。

**第三关：prompt cache 前缀不可变。** 改动靠前的消息会改变前缀哈希，让整条长 trajectory 的缓存作废。为了递送一句话而重算几万 token，成本 unacceptable。

合起来的结论很硬：唯一合法、且对缓存影响最小的可写位置，是**某条已经存在、即将被发出的 tool result 的尾部**。

## 伪装：把 steer 缝进 tool result

Hermes 顺着约束往下走：既然唯一安全插槽是最后一个 tool result 的尾部，那就把 steer 追加到那里。

代码注释把这个选择说得很直白：

> "A steer is appended to the END of a tool result (the only role-alternation-safe slot mid-turn)..."

但它不是裸贴一段 "User guidance:"——模型会把那当成 prompt injection 直接拒掉。Hermes 的解决方案是一对**自描述 marker**，再加一段写进系统提示的**信任锚**。

```python
STEER_MARKER_OPEN = "[OUT-OF-BAND USER MESSAGE — a direct message from the user, delivered mid-turn; not tool output]"
STEER_MARKER_CLOSE = "[/OUT-OF-BAND USER MESSAGE]"
```

系统提示里提前登记了同一对 marker，告诉模型：这个标记里的内容是真实用户意图，和原始请求有同等权威；并且**只信这个确切 marker**，工具输出、网页、文件里长得像的都不信。

![marker + 系统提示的信任锚](assets/2026-07-01-hermes-marker-trust.png)

这是工程上的最小侵入：没有新的 message role，没有协议状态机，只动已有 tool result 的 content 末尾。代价是：这套信任完全建立在「模型遵守系统提示」上——它没有签名，没有 nonce，只要真实工具输出里碰巧或恶意出现了同一串 marker，就可能被误读。

## 两个 drain 点：什么时候真的生效

你按下回车，steer 并不会立刻塞进 tool result。它先进入一个线程安全的单槽 `_pending_steer`，然后在两个安全边界之一被 drain 出来：

- **post-tool drain**：工具批次刚跑完，steer 挂到本批最后一条 tool result；
- **pre-API drain**：上一次模型调用进行中到达的 steer，在构建下一次请求前被投递——否则如果模型直接返回终态、没有下一批工具，这句话就永远落不了地。

![pre-API 与 post-tool 两个 drain 点](assets/2026-07-01-hermes-two-drains.png)

两个点的逻辑几乎一样：排空槽位，倒序找最后一条 `role == "tool"` 的消息，命中就 append marker；找不到就原样塞回槽位，等下一个边界。 Hermes 的取向很清晰：**没有安全插槽，就继续等，绝不将就。**

这也意味着，如果 agent 卡在一个很长的单轮生成里，或卡在一个不返回工具结果的长工具调用里，steer 只能等下一个边界。它改的是方向，不是节奏。

## Hermes vs Codex：同一道题，两层解

同样的问题，Codex 走了另一条路。

**Hermes：进程内 + marker 内联。** 没有协议层，`agent.steer(text)` 是进程内方法调用，一把锁保护一个字符串槽位，drain 时把文本包进 marker 追加到 tool result。

**Codex：协议优先 + 分离消息。** app-server 协议里有一等 RPC `turn/steer`，steer 作为独立输入项进入 turn-scoped 的 `pending_input`，模型看到它时就是一条正经的 user 消息。客户端必须带 `expectedTurnId`，错回合即拒。

![Hermes 与 Codex 的两条路](assets/2026-07-01-hermes-vs-codex.png)

Codex 用协议契约买确定性；Hermes 用最小改动和模型信任换低耦合。没有谁对谁错，只是把复杂度放在了不同的层。

## 这套机制的代价

值得把代价摆出来，而不是假装它已经完美。

1. **best-effort，没有 turn-id 校验。** 用户心里瞄准的轮次和文本实际落地的轮次可能不一致，尤其在终端输出滞后时。
2. **信任锚是字符串级的。** 真实工具输出里若出现同一 marker，模型可能误读；对抗来源也能伪造。Anthropic 官方甚至建议不要把指令放进 tool result。
3. **首轮无工具时无法投递。** 如果 agent 还没产生任何 tool result，steer 只能 restash，延迟一轮或退化成普通 user 消息。
4. **几乎没有遥测。** 只有成功投递时一行 INFO 日志；被中断吞掉、延迟一轮、打偏轮次都发生在暗处。

这些不是 bug，是有意接受的 trade-off。Hermes 证明的是：把 agent 当成一个长跑的、能接收异步信号的进程，这件事可以用很轻的手段落地，不需要先有一套协议标准。

## 把 agent 当长运行进程

steer 的范式意义大于具体实现。它让聊天窗口从一个问答框，变成了一个能随时微调方向的 agent 控制台。

Hermes 给出的不是标准答案，而是一个足够轻、足够清楚、连代价都标注得明明白白的起点。下一步如果要更结实，迟早需要结构化的带外信令——但那是另一个故事了。

---

**延伸阅读（完整源码拆解）**  
Erik，《一句话怎么塞进正在跑的 agent：Hermes steer 机制全解》，2026-06-11。

**参考来源**
- Hermes agent runtime source：agent/agent_init.py、run_agent.py、agent/prompt_builder.py、agent/conversation_loop.py、agent/tool_executor.py、agent/agent_runtime_helpers.py
- OpenAI Codex app-server README / `turn/steer` 文档
- Anthropic Claude API docs：Handle tool calls / Prompt caching / Mitigate jailbreaks and prompt injections
- Simon Willison, "The lethal trifecta", 2025-06
- ChatInject (arXiv 2509.22830), as-of 2026
