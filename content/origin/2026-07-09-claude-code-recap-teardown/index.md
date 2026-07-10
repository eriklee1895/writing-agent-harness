---
title: "一行 Recap，半壁江山：拆解 Claude Code 的上下文锚点机制"
date: 2026-07-09
topic: claude-code-recap
tags: ["claude-code", "agent", "context-management", "ui-ux", "anthropic"]
summary: "最近用 Claude Code 发现输入框上方多了一行 `※ recap: Goal: ...` 灰色小字。顺着好奇心往下挖，发现这行字底下叠了四层独立机制——不是一个功能，是四条演化线索咬在一起。"
authors: ["Erik Lee"]
cover: assets/cover.png
---

![一行 Recap · Claude Code 上下文锚点机制拆解](assets/cover.png)

## Recap：一个实用的新功能

最近用 Claude Code 的时候，注意到输入框上方多了一行 dim 灰色小字：

![真实终端里的 recap：计时器行 `✻ Worked for 2m 57s`，下面是 `※ recap: Goal: remove /api/v1/video-gen/health noise from Loki... Next action: ... (disable recaps in /config)`](assets/screenshot-session-recap.png)

上面一行 "Worked for 2m 57s" 我认识，是 Claude Code 标志性的随机动词计时器——从 Baked、Brewed 到 Sautéed、Worked，每个 turn 结束随机抽一个过去式动词，进行中是 Vibing/Brewing 之类的现在分词，主要是缓解长思考时的等待感，跟功能本身关系不大。

真正勾住我的是下面那行 `※ recap: Goal: ...`——它精准复述当前窗口在干什么、进展到哪、下一步是什么。我那天开着五个终端排 license 过期的问题，窗口之间跳的时候，靠这行字重定向注意力的速度，比重新扫上一轮对话快得多。末尾还贴心留了个 "disable recaps in /config"。

这不是什么 flagship feature 的发布公告，是悄悄长出来的 UX 细节。我好奇它什么时候上线的、怎么做的、为什么有效。顺着这个问题翻 changelog 和源码挖下去，发现 "recap" 在 Claude Code 里根本不是一个功能——是**四层独立演化、后来咬合在一起的机制**，加上计时器那一行，输入框上方那块几毫米高的灰色区域叠了五套不同时间上线的逻辑。

这篇文章把它们一层层剥开。

---

## Overview

术语先清。Claude Code 的源码、changelog、用户嘴里的 "recap" 至少指四件不同的东西；加上输入框上方那行计时器，输入框上方那块区域其实挤着几条独立演化的消息：

| 名字 | 前缀 | 触发时机 | 模型 | 备注 |
|---|---|---|---|---|
| **计时器（Brewed/Worked…）** | `✻` U+273B（视觉上像 `*`） | turn 进行中 + 结束定格 | 纯前端 | recap 出现之前就存在的独立 UI，随机抽动词 + 时长，缓解等待焦虑，和 recap 本身无关 |
| **Session Recap（回会话摘要）** | `※` U+203B | 终端失焦 ≥3 分钟、会话 ≥3 轮，用户回来时触发；非交互模式完全跳过 | Haiku | v2.1.108（2026-04-14）上线，内部代号 Away Summary |
| **End-of-Turn Recap（每轮锚点）** | `※` U+203B | 每个 assistant turn 结束时——截图里的 `※ recap: Goal:` 就是它 | 主模型，StructuredOutput | v2.1.186（2026-06-22）上线，嵌在主模型 response 内，零额外调用；跟随对话语言输出 |
| **Compaction Summary（上下文压缩）** | （system message） | context window 用到约 93% 时 | 主模型（继承 thinking config） | 最老一层（2025 年已有），为 context window 续命 |
| **Prompt 级 Recap Line（自校正 trick）** | UI 不可见 | 每个 response 结尾写一行 recap 注入下一轮 context | 主模型 | turn-end self-reminder pattern |
| **`/recap` 手动命令输出** | `└` U+2514 | 用户显式输入 `/recap` | 主模型 | 走 slash command 通道，永远英文；v2.1.108 同步上线 |

计时器不算 recap 的一层，但它和 recap 共享输入框上方的视觉空间，又都带"星号"前缀，用户直觉里常把它们当成一组。

![四层 Recap 机制：从底层的上下文压缩到顶层用户可见的 End-of-Turn 锚点](assets/layers-diagram.png)

图：四层 recap 机制叠合示意（计时器不算 recap 层，是独立的 UI 组件）。最顶层橙色高亮的 End-of-Turn Recap 就是截图里那行 `※ recap: Goal: ...`，底下三层（Away Summary / Prompt 自校正 / Compaction）分别沿着"离席/防死循环/续命"三条独立需求演化，最终在 v2.1.186 接到同一个 UI 槽位；手动 `/recap` 走 slash command 通道，以 `└` 前缀单独渲染。

---

## 时间线

### 2026-04-14 · v2.1.108 — Session Recap 初登场

changelog 原文：

> Added recap feature to provide context when returning to a session, configurable in `/config` and manually invocable with `/recap`; force with `CLAUDE_CODE_ENABLE_AWAY_SUMMARY` if telemetry disabled.

这是 Anthropic **第一次把 "recap" 放进 changelog**。目标非常具体："provide context when returning to a session"——**你离开一段时间回来时，告诉你之前在干嘛**。

代码落地比市场宣传早约一周。4 月 20-24 日的 Week 17 "What's new" digest（v2.1.114→v2.1.119）才把它作为 feature card 放出来，文案：

> "Switch focus away from a session and come back to a one-line recap of what happened while you were gone. Helpful for staying in flow while running several Claude sessions at once."

先悄悄 ship、修两天 bug、再发公告——这是 Anthropic 的标准节奏。

内部代号 **Away Summary**，env 变量 `CLAUDE_CODE_ENABLE_AWAY_SUMMARY`。触发条件在正式版比 v2.1.88 源码里看到的更细：
- 距离最后一个 completed turn 过去至少 **3 分钟**
- 终端 unfocused
- 会话至少 **3 个 turn**（新会话不弹）
- 每次 away 周期只弹**一次**，不连发
- **非交互模式跳过**
- **失焦期间后台预生成**，切回来时已经 ready，不用再等

prompt 核心：

> "The user stepped away and is coming back. Write exactly 1-3 short sentences. Start by stating the high-level task — what they are building or debugging, not implementation details. Next: the concrete next step. Skip status reports and commit recaps."

几个关键取舍：
1. **用 Haiku，不用主模型**——成本差两个数量级，可以"免费"触发。
2. **只在 away 后生成**，不每轮生成。
3. **不写 commit 流水账**——直接给 goal + next step，不然就是 "changed 3 files" 那种没用的 git log。

v2.1.110（次日，4-15）修了 focus mode 不显示的 bug，并把它对 Bedrock/Vertex/Foundry 用户开放（最初版本要求 telemetry 开启）；v2.1.113（4-17）修了"用户正在打字时 recap 弹出来"的竞态。

Simon Willison 4 月 9 日写过一条 [CLAUDE.md 注入技巧](https://simonwillison.net/2026/Apr/9/claude-code-slow-tasks/)——让 Claude 每思考 30 秒主动发一条进度消息。这是用户层面的 prompt hack，比官方 recap 早五天。Anthropic 一周后把这个需求原生做了进去。

### 2026-04-15 · v2.1.109 — 思考计时器升级

> Improved the extended-thinking indicator with a rotating progress hint.

跟 recap 没直接关系，但这是 "Brewed for" 从单纯计时器走向"思考过程可视化"的起点。v2.1.152（5-27）改成 live 递增的 "Thinking for Ns"，v2.1.166（6-06）加了 "still thinking / thinking more / almost done thinking" 的文字 hint。

### 2026-06-22 · v2.1.186 — End-of-Turn Recap 上线

这是截图里那行 `※ recap: Goal: ...` 真正出现的版本。changelog 一行：

> Fixed background session recaps being duplicated; **the agent's own end-of-turn summary now shows as the recap line**.

注意这个 "now shows as"。它暗示两件事：
1. "end-of-turn summary" **在之前就已经生成了**（给 agent 自校正用，见下一节），但**对用户不可见**。
2. v2.1.186 把它**接到了 recap 这个 UI 槽位上**——把 agent 内部用的结构化输出，变成用户能看到的锚点。

v2.1.196（6-29）紧接着修了 "schema-rejected StructuredOutput 导致重复渲染两行 recap" 的 bug——这证实 end-of-turn recap 走 **StructuredOutput** 通道：模型被要求输出固定 schema 的 JSON，渲染层读字段拼字。v2.1.199（7-02）又修了一次 background session 的重复行。

到这里，截图里的 `※ recap: Goal: ...` 才算完整成型：Brewed 计时器 + 主模型生成的结构化 end-of-turn summary，两个独立发展的功能在 UI 上接到了同一块区域。

---

## 技术实现

### 层 0：Brewed 计时器（纯前端，recap 之前就存在）

严格说它不是 recap 的一层，但因为和 recap 共享输入框上方的 UI 区域、又都带"星号"前缀，很容易被当成同一个东西。

纯前端实现：turn 开始随机挑一个动词显示进行态（`✻ Brewing…` 之类），`setInterval` 每秒累加时长；turn 结束时定格为过去式 + 时长。渲染组件 `TurnDurationMessage`，dim 颜色、前缀 `✻`（U+273B）：

```
✻ Worked for 2m 57s · 137.2k/1000.0k (14%) · 573m 35s
```

后面两个字段分别是 token 用量和会话总时长。`/config` → `showTurnDuration` 可关。计时器负责"我刚才想了多久"，recap 负责"我刚才干了什么"——两条独立消息在视觉上挨在一起，构成了截图里的"两行灰字"。

### 层 1：Session Recap / Away Summary（小模型触发）

触发链：
1. `useAwaySummary` hook 监听终端 focus 事件（`DECFOCUS` escape sequence 或 TUI blur）。
2. 失焦 3 分钟、会话 ≥3 轮时**后台启动**生成，所以用户切回来时大概率已 ready。
3. 每 away 周期只生成一次。
4. `buildAwaySummaryPrompt()` 取最近消息 window + session memory，送 Haiku（`getSmallFastModel()`，可通过 `ANTHROPIC_SMALL_FAST_MODEL` 覆盖），thinking disabled，无 tools。
5. 返回 1-3 句，`createAwaySummaryMessage()` 包装成 `※` 前缀插到输入框上方。
6. 用户发下一条消息时消失。
7. `-p`、`--output-format stream-json`、管道输入下完全跳过。

一个容易忽略的细节：v2.1.88 源码里 `BLUR_DELAY_MS = 5 * 60_000`（5 分钟），正式版调到 3 分钟并加了 3-turn 门槛和不连发去重。上线后根据真实数据做过一轮调优。

### 层 2：End-of-Turn Recap（主模型 StructuredOutput）

技术上最有意思的一层。它走 Claude 的 **StructuredOutput**——模型在 text/tool use 之外，被要求额外输出一份符合 schema 的 JSON：

```json
{
  "goal": "fix the BOE cluster's expired License and harden the mechanism",
  "status": "completed",          // "in_progress" | "blocked" | "waiting"
  "summary": "License fixed live (valid to 2031), vkb-deploy MR pushed",
  "nextAction": "decide whether to revert chart changes and bake public key into image instead",
  "blockedBy": null
}
```

字段是从 v2.1.186/v2.1.199 的 bug-fix 描述反推的。几个实现要点：

- **不是额外的 LLM 调用**。end-of-turn summary 是主模型 response 的一部分，forced StructuredOutput 让模型在正文 answer 后再输出一个结构化块。零额外 latency、零额外成本——这也是它比 away summary 准确得多的原因。
- **渲染层拼字符串，不让模型直接拼**。前端根据字段用固定模板渲染：`※ recap: Goal: <goal>. <summary>. Next action: <nextAction>. (disable recaps in /config)`。这样格式永远一致，不会被模型的发挥带偏。
- **跟 prompt 级 Recap Line 是同一份信息**。v2.1.186 之前，这份 summary 只注入下一轮 context；v2.1.186 之后，schema 约束后同时渲染给用户看。

控制入口：`/config` 的 "Session recap" toggle，或 settings.json `"awaySummaryEnabled": false`，或环境变量 `CLAUDE_CODE_ENABLE_AWAY_SUMMARY=0`。away summary 和 end-of-turn recap **目前共用一个开关**，不能独立关——这是个粗糙的地方。

### 层 3：Compaction Summary（上下文压缩）

最老的一层，目的跟"给人看的 recap"不同——**给 context window 续命**。

触发：
- 自动：token 使用达 `context_window - 13,000`（`AUTOCOMPACT_BUFFER_TOKENS`，留 13k 给 summary 输出）。
- 手动：`/compact`。
- 兜底：API 返回 prompt-too-long 时 reactively compact。

流程：
1. 旧消息打成 segment 落盘（`writeSessionTranscriptSegment`）——全量历史**不丢**，模型随时用 FileReadTool 重读。
2. **主模型**（带 thinking，v2.1.198 起继承 session 的 effort 级别）生成结构化总结，prompt 要求输出 9 个区块：Primary Request、Key Technical Concepts、Files and Code Sections（含片段）、Errors and fixes、Problem Solving、All user messages（verbatim）、Pending Tasks、Current Work、Optional Next Step。
3. summary 包成 synthetic user message 插回 message 数组，前加 `compact_boundary` 系统消息。
4. 重新 attach 最近读的 5 个文件（每个 ≤5k tokens）、plan 文件、已调用 skills、async agent 状态等，总预算 50k tokens。
5. 给模型一条 resume 指令："Continue directly — no apology, no recap of what you were doing"（v2.1.88 源码 query.ts:1226 能看到这句话）。

Compaction 是三层 recap 机制里**最重**的——主模型 + thinking + 上千 tokens 的结构化输出 + 重新 hydrate 附件。产物渲染成"Context compacted"系统消息。`DISABLE_AUTO_COMPACT=1` 关自动；`DISABLE_COMPACT=1` 连手动也关。

---

## UX 视角：为什么这行Recap很实用

技术拆完了，回到 UX。这行 `※ recap: Goal: ...` 让人觉得好用，是因为它解决了一个之前所有 AI coding 工具都没认真解决的问题：**多 session 并行时的上下文重定向**。

### 人体工学：工作记忆不等于可视觉回忆

大模型有百万 token context window，**人类没有**。当你开 3-5 个 Claude Code 窗口并行——一个在跑 license，一个在 MR review，一个在写功能，一个在 deploy staging——每个窗口都是隔几分钟才回来看一眼。每次切回去，要花 10-30 秒扫上一轮对话重新锚定"我在这干嘛"。

10-30 秒 × 5 个窗口 × 一天几十次切换，这个认知摩擦非常具体。终端 title、tmux pane 名字、你自己的记忆——都只能给一个项目名，给不了"下一步是什么"。

### 为什么是"一行"而不是"一段"

recap 的克制就是它好用的原因：

1. **只有一行**（away summary prompt 硬约束 "exactly 1-3 short sentences"；end-of-turn 也是单段）。超过三行就变成一段你不想读的墙。
2. **固定 schema**：`Goal: ... . <现状>. Next action: ...`。每次按这个模板输出，用户肌肉记忆能直接跳到 "Next action:"，不用扫。
3. **dim 灰色，输入框上方**——视觉层级上"不抢焦点，外围视觉一 catch 就有"。不是主内容区大字报，是 perifoveal vision 能接住的锚点。

### 跟计时器绑定的心理学

把 recap 和计时器放同一行是个视觉上的小 trick。计时器（"Worked for 2m 57s" 之类）本来是 turn 结束的终止符，告诉用户"思考停了"；recap 接在它旁边，视线自然从"花了多久"过渡到"做完了什么"——两个信息都属于"上一轮结束"这个事件，不需要额外分组。

---

## 争议和粗糙的地方

recap 不是没有问题。

**1. 早期的成本和延迟**
5 月底到 6 月初，Reddit 和 HN 上有零散反馈说 "Turn summary makes Claude unusable — 1-2 minutes of extra latency after every prompt"。一度有环境变量 workaround（社区流传的 `ANTHROPIC_DISABLE_AUTO_PLAN_SUMMARY=true`）。根因是 auto-compact 阈值偏低加上 end-of-turn summary 早期**用了独立的 LLM 调用**（还没切到 StructuredOutput 方案），每次 turn 结束多一次模型往返。v2.1.186 切到 StructuredOutput 把它并入主 response 后，这个问题基本消失。

**2. 准确性偶尔翻车**
重启 session 时的 suggested prompts 有时不准——这是 LLM-generated summary 的通病。但它是**给下一轮模型看的**，不是**给用户做 ground truth** 的，容错率比直觉高：下一轮有完整 context，recap 只做快速锚定，不会被当成事实。

**3. Background session 的重复行**
v2.1.186 和 v2.1.199 连着修了两次"两行 recap"——第一次子 agent 和父 agent 各输出一份；第二次 StructuredOutput schema 校验失败重试时新旧两份都被渲染。说明在多 agent 场景下，这个功能的事件订阅关系相当复杂，Anthropic 自己也踩了几轮。

**4. 配置入口散**
- Away summary：`/config` Session recap toggle / `awaySummaryEnabled: false` / `CLAUDE_CODE_ENABLE_AWAY_SUMMARY=0`
- End-of-turn recap：同一个 toggle（v2.1.199 起带内联提示）
- Auto-compact：单独开关 / `DISABLE_AUTO_COMPACT=1`
- Turn duration：单独 `showTurnDuration`

四个东西共用 "recap" 这个词，散在三个开关、两个环境变量里，新用户第一次找关闭入口会绕一圈。

**5. 自动 vs 手动的语言行为不一致**
自动 end-of-turn recap 会跟随对话语言输出（中文对话→中文 recap），但手动 `/recap` 命令走 slash command 通道，结果永远是英文、前缀用 `└` 而非 `※`。同一个功能名、两个视觉通道、两套语言规则——这种细节不一致是典型的"不同团队/不同版本拼起来的功能"的残留痕迹。

---

## 一个 prompt trick 怎样长成 UX 范式

回头看整个演化路径，最值得注意的一件事：**recap 这几层不是一次性设计出来的，是几条独立线索在 v2.1.186 突然咬合的**。

- Compact（2025 年）：为 context window 续命。
- Prompt 级 Recap Line（2025 底–2026 初，配合 SWE-bench 优化）：防死循环。
- Away Summary（2026-04-14）：解决用户离开再回来的场景。
- `/recap` 手动命令（2026-04-14 与 away summary 同步上线）：给用户主动触发的通道。
- End-of-Turn Recap（2026-06-22）：把给下一轮用的 summary 提上 UI。

计时器（"Brewed for" 那行）在 recap 出现之前就存在，是独立演化的 UI 组件；recap 只是恰好接到了它旁边的位置，视觉上让两者看起来像一组。

其中最有"设计感"的是 End-of-Turn 这一步。前面几层都是功能性的——续命、防循环、away 后重定向、手动触发；但把主模型本来就要输出的那份隐式结构化 summary 拎出来给用户看，是一个典型的**"把内部状态暴露成 UX"**动作。做 agent 系统的人应该熟悉这个模式：进度条、当前文件、plan 展示、tool 调用展开——这些好用的 UX，本质上都是把内部已有的状态**加个渲染**，不是专门为 UX 再造一份。

这里抽一条可以复用的经验：**如果你在 agent 系统里为了 self-correction、planning、memory 已经让模型输出了某种结构化中间状态，几乎总是应该把它也显示给用户**。成本已经付了，边际成本只是一行渲染代码，边际收益是显著的可观察性和信任感。反过来，专门为了 UX 让模型多输出一份什么，大概率会掉进延迟/成本/准确性的三角坑。

---

## 怎么用 recap

基于 v2.1.205（2026-07-08）：

### 自动触发（不需要操作）

- **Away summary**：离开终端 ≥3 分钟回来时自动弹出（需要会话 ≥3 turn）。后台预生成，切回来直接能看。
- **End-of-turn recap**：每个 assistant turn 结束自动显示 `※ recap: Goal: ...`，跟随对话语言（中文对话就是中文 recap，英文对话就是英文）。

### 手动触发：`/recap`

任何时候输入 `/recap` 可以立刻让模型生成一行"此刻我在干嘛"的摘要——不等失焦，不等 turn 结束。

![在命令面板里输入 `/recap`：描述是 "Generate a one-line session recap now"](assets/screenshot-显式recap指令.png)

命令执行过程中复用主 spinner（turn 进行中那条动效），和普通思考中一样显示一个随机动词 + 省略号，这张截图里刚好显示 "Vibing…"：

![`/recap` 执行中：spinner 位置显示 `✻ Vibing…`](assets/screenshot-显式recap指令执行中.png)

生成完成后，结果会以 `└`（box-drawing L 形角标）前缀插在命令下方，**永远是英文**，不跟随对话语言——这是 `/recap` 手动命令和自动 end-of-turn recap 一个容易忽略的差异：

![`/recap` 执行结果：`└ Goal: Understand how to generate images using Seedream...` 英文输出，`└` 前缀](assets/screenshot-显式执行recap指令效果.png)

这里有个值得一提的细节：手动 `/recap` 输出走的是 slash command 通道（和 `/bug`、`/commit` 一类），它不是 SystemTextMessage，而是作为 assistant 回复的一部分渲染，因此用了 `└`（U+2514，box-drawing light up and right）前缀而不是自动 recap 的 `※`，也不遵守会话语言。away summary 和 end-of-turn recap 是两个独立触发路径，计时器又是第三条路径——三种前缀符号（`✻` / `※` / `└`）分别对应三种内部消息类型，UI 却把它们都摆到输入框上方同一块区域，用户看上去都是"一行灰字"。

### 怎么关

![`/config` 过滤 "recap" 只显示一个开关：Session recap = true](assets/screenshot-config.png)

```bash
# 关自动 away summary + end-of-turn recap（两者共用一个开关）
/config                        # → "Session recap" toggle off（如上图）
# 或 settings.json: "awaySummaryEnabled": false
# 或环境变量: export CLAUDE_CODE_ENABLE_AWAY_SUMMARY=0

# 关自动 compact（不推荐）
/config                        # → "Auto-compact when context is full" off
# 或 export DISABLE_AUTO_COMPACT=1

# 关计时器行（"Worked for Xm Ys" 等）
/config                        # → "Show turn duration" off
# 或 settings.json: "showTurnDuration": false

# 全关（连手动 /compact 都关，不推荐）
export DISABLE_COMPACT=1
```

---

## 总结

那行看起来随手加上的灰色小字，底下叠着 turn-end self-reminder prompt trick、Haiku 低成本 away summary、主模型 StructuredOutput 锚点、context window 压缩四套机制，花了 Anthropic 小半年，沿着不同需求各自演化，在 2026 年 6 月的一个版本里咬合成一个好用的 UX 锚点。

Anthropic 在 Claude Code 上的打法不是先画好 UX 蓝图再做功能，而是让 agent 系统的内部结构自己"长"出可以暴露的状态，然后在合适的时机接上 UI。这跟传统 UI 产品思路是反的——传统做法是"用户需要看 X，所以让模型生成 X"；Claude Code 的做法是"模型本来就在生成 X 给自己用，顺便给用户看看"。

两条路径出来的 UI 质感完全不同。前者容易感觉"贴上去的"、慢半拍、跟正文脱节；后者感觉原生、零成本、对得上正文——因为它本来就是正文的一部分。

一行 recap，是这个设计哲学最小的展品。

---

## 附：关键版本时间线

| 日期 | 版本 | 事件 |
|---|---|---|
| 2026-03-30 | v2.1.88 | leak 基准；只有 Brewed 计时器 + compact，无 recap |
| 2026-04-14 | v2.1.108 | **Session Recap 软着陆**（`/recap` + away summary，Haiku） |
| 2026-04-15 | v2.1.110 | Away summary 对 Bedrock/Vertex/Foundry 开放，移除 telemetry gate |
| 2026-04-15 | v2.1.109 | Extended thinking indicator 加 rotating hint |
| 2026-04-17 | v2.1.113 | 修复"用户打字时 recap 弹出"的竞态 |
| 2026-04-20~24 | Week 17 digest | 官方首次在 "What's new" 宣传 Session recap |
| 2026-05-27 | v2.1.152 | 思考计时器改成 live "Thinking for Ns" |
| 2026-06-17 | v2.1.181 | `/recap` model switch bug 修复 |
| 2026-06-22 | v2.1.186 | **End-of-Turn Recap 上线**——agent 内 summary 接上 UI 槽位 |
| 2026-06-29 | v2.1.196 | 修复 StructuredOutput schema reject 导致的双行 recap |
| 2026-07-01 | v2.1.198 | Compact 继承 session extended thinking config |
| 2026-07-02 | v2.1.199 | 修复 background session 双行 recap（第二次） |
| 2026-07-08 | v2.1.205 | 本文截图所用版本；`/config` 中 Session recap 为单一开关 |

## 参考资料

- Claude Code 官方 changelog: https://code.claude.com/docs/en/changelog
- "What's new" Week 17 (Apr 20-24, 2026): https://code.claude.com/docs/en/whats-new/2026-w17
- Interactive Mode 文档（Session recap 章节）: https://code.claude.com/docs/en/interactive-mode#session-recap
- CLI 命令参考（`/recap`）: https://code.claude.com/docs/en/commands
- GitHub CHANGELOG.md: https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
- Anthropic Engineering — Building Effective Agents (prompt patterns, incl. third-person recap pattern): https://www.anthropic.com/engineering/building-effective-agents
- Anthropic Engineering — Claude Opus 4.7: Building reliability into coding (2025-05-22): https://www.anthropic.com/engineering/claude-opus-4-7-building-reliability-into-coding
- Simon Willison — "New trick for Claude Code running long, slow tasks" (2026-04-09): https://simonwillison.net/2026/Apr/9/claude-code-slow-tasks/
- npm registry @anthropic-ai/claude-code（版本日期核对）
- Claude Code v2.1.88 leaked source（`src/services/compact/`, `src/constants/turnCompletionVerbs.ts`, `src/query.ts` 等）：基准版本实现参考；v2.1.108+ 的触发阈值已从 5min 调到 3min 并加了 3-turn 门槛
- 本文 version/date/config key 等事实性 claim 经 deep-research workflow 对 changelog / interactive-mode docs / commands reference / npm registry / Week 17 digest 做 primary-source 交叉核对；prompt 级 Recap Line 的具体措辞和 loop-error 下降比例 Anthropic 未单独成文披露，文中仅描述机制方向，不附具体百分比
