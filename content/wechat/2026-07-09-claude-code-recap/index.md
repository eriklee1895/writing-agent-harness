---
title: "Claude Code 新功能探秘：Session Recap"
subtitle: "一行 `* recap: Goal: ...`，底下叠了四套机制"
date: 2026-07-09
topic: claude-code-recap
tags: ["claude-code", "agent", "ui-ux", "anthropic"]
summary: "最近用 Claude Code 发现输入框上方多了一行灰色小字，精准告诉你现在在干嘛、下一步是什么。顺着好奇心翻 changelog 和源码，发现它根本不是一个功能，是四套独立机制咬合出来的。"
authors: ["Erik Lee"]
author: "Erik"
cover: ../../origin/2026-07-09-claude-code-recap-teardown/assets/cover.png
style: agent-flow
channel: wechat
origin: ../../origin/2026-07-09-claude-code-recap-teardown/index.md
---

# Claude Code 新功能探秘：Session Recap

> 一行 `※ recap: Goal: ...`，底下叠了四套独立演化的机制。

![一行 Recap · Claude Code 上下文锚点机制拆解](../../origin/2026-07-09-claude-code-recap-teardown/assets/cover.png)

你最近开 Claude Code 的时候有没有注意到——输入框上方多了一行灰色小字？

长得像这样：

![真实终端里的 recap：上面一行 `✻ Worked for 2m 57s`，下面一行 `※ recap: Goal: remove /api/v1/video-gen/health noise from Loki... Next action: ... (disable recaps in /config)`](../../origin/2026-07-09-claude-code-recap-teardown/assets/screenshot-session-recap.png)

第一眼看到它我没太在意，以为就是个 loading 文案。直到那天我开了五个终端排 license 过期的问题，在窗口之间来回切——切到哪个窗口，那行字就告诉我那个窗口在干嘛、下一步要做什么。我重新锚定上下文的速度，比滚上一轮对话快了好几倍。

这时候我才认真看了它一眼。然后发现它不是"一行字"，是两行；那两个星号长得很像其实不是同一个符号；"Worked" 这个动词是随机抽的，下一个窗口可能是 "Baked" 或者 "Sautéed"；末尾还贴心留了个 "disable recaps in /config" 的逃生舱。

好奇心被勾起来了。我去翻了 changelog、官方文档、甚至一份 v2.1.88 的 leak 源码，想搞清楚它到底什么时候上线的、怎么做的、为什么好用。

结果发现——**这东西根本不是一个功能，是四套独立演化的机制在 2026 年 6 月的一个版本里突然咬在一起**。计时器是计时器，回会话摘要是回会话摘要，每轮锚点是每轮锚点，上下文压缩是上下文压缩。它们在 UI 上挤在输入框上方几毫米高的灰色区域里，看上去像"一行灰字"。

## 先把"谁是谁"认清楚

在往下讲之前，先把这堆东西理一下。输入框上方那块区域，至少挤着六条独立演化的消息：

| 名字 | 长什么样 | 什么时候出现 | 谁写的 |
|---|---|---|---|
| 计时器（老住户） | `✻ Worked for 2m 57s` | turn 思考中和结束后 | 纯前端，零模型调用 |
| 回会话摘要 | `※ 你之前在做 XXX...` | 你离开终端 ≥3 分钟再回来 | Haiku 小模型 |
| 每轮锚点（就是你看到的那行 recap） | `※ recap: Goal: XXX... Next action: XXX` | 每轮回答结束后自动出现 | 主模型，零额外调用 |
| 上下文压缩 | 系统消息"Context compacted" | 上下文快满了自动触发 | 主模型+thinking |
| 模型自用小抄 | 看不见 | 每轮结束时悄悄塞给下一轮自己 | 主模型 |
| 手动 `/recap` | `└ Goal: XXX...` | 你敲 `/recap` | 主模型 |

前缀三种不同符号——`✻`（像星号但不是）、`※`（就是回览/参考号那个）、`└`（直角角标）——分别对应三种消息类型。用户看上去都是"灰字一行"，底下其实是三套系统。

![四层 Recap 机制：从底层的上下文压缩到顶层用户可见的 End-of-Turn 锚点](../../origin/2026-07-09-claude-code-recap-teardown/assets/layers-diagram.png)

下面按上线顺序挨个说。

## 第一个版本：你离开座位回来告诉你"刚才发生了啥"

Recap 第一次出现在官方 changelog 是 v2.1.108，2026 年 4 月 14 日。原文：

> Added recap feature to provide context when returning to a session, configurable in `/config` and manually invocable with `/recap`.

翻译成人话：你离开终端一段时间再回来，它给你一行字——刚才你在干嘛、下一步是什么。

这是它的**第一个版本**，内部代号 Away Summary。触发条件还挺细的：

- 离开至少 3 分钟
- 这段对话至少聊了 3 轮（新会话不弹）
- 终端得是失焦状态（你真的走开了，不是盯着屏幕等）
- 每次离开只弹一次，不刷屏
- 你用 `-p`、管道、脚本跑的时候完全跳过（没意义给脚本看）
- **它在你离开的时候后台就生成好了**，切回来直接看，不用等

模型选的是 Haiku——最便宜最快的小模型，成本比主模型低两个数量级，可以"免费"触发。

Prompt 写得也很克制：

> 用户走了又回来了。写 1-3 句短句。先说大方向在干什么，别说代码细节。再说下一步具体做什么。不要写状态汇报、不要写 commit 流水账。

特别有意思的是最后那句——"不要写 commit 流水账"。因为早期的版本最容易产出这种垃圾："changed 3 files, modified 127 lines, added 4 functions"，跟 `git log --oneline` 差不多没用。Anthropic 吃过这个亏，直接在 prompt 里禁掉了。

然后代码 4 月 14 号 ship，官方在 "What's new" 里宣传是 4 月 20-24 号那周。**先悄悄上线修几天 bug，再发公告**——这是 Anthropic 一贯的节奏。

对了，Simon Willison 五天前（4 月 9 号）还发过一个 prompt hack：让 Claude 每思考 30 秒主动发一条进度消息。那是用户层面的土法炼钢，Anthropic 一周后就把它做成原生功能了。

## 计时器升级和思考提示

跟这事儿没直接关系，但顺便提一下——4 月 15 号 v2.1.109 给思考指示器加了 rotating progress hint，后来的版本（5 月 27 日 v2.1.152）改成了 live 递增的 "Thinking for Ns"，6 月 6 号又加了 "still thinking / thinking more / almost done thinking" 的文字提示。

这些都不是 recap，但说明 Anthropic 那段时间在认真打磨"等待"这件事的体验——长思考是 agent 工具最大的焦虑源之一。

## 重头戏：每轮结束自动告诉你"我干了啥"

真正让 recap 变成"每轮都能看到"的功能，是 v2.1.186，2026 年 6 月 22 号才上线。Changelog 只有一行：

> Fixed background session recaps being duplicated; **the agent's own end-of-turn summary now shows as the recap line**.

注意这个 "**now shows as**"——翻译过来是"现在终于显示出来了"。这句话暗示了两件事：

1. 那份"本轮总结"在这之前**就已经生成了**，但对用户不可见；
2. v2.1.186 只是把它从"模型自用"接到了"用户能看到"的 UI 槽位上。

这是整篇文章里我觉得最妙的一个细节。后面我会专门展开。

技术上它走的是 Claude 的 StructuredOutput——模型在正经回答完之后，被强制按一个 JSON schema 再输出一份结构化的小抄：

```json
{
  "goal": "修复 BOE 集群过期的 License",
  "status": "completed",
  "summary": "License 临时续到 2031，vkb-deploy MR 已推",
  "nextAction": "决定是否要回滚 chart 改动，把公钥烤进镜像",
  "blockedBy": null
}
```

前端拿到这个 JSON 再拼字：`※ recap: Goal: <goal>. <summary>. Next action: <nextAction>. (disable recaps in /config)`。模型不负责拼字符串，前端用固定模板渲染——这样格式永远稳定，不会被模型发挥带偏。

v2.1.196（6 月 29 日，就是一周后）就修了一个 bug：StructuredOutput schema 校验失败重试时，新旧两行 recap 会同时显示，变成双行。再过三天 v2.1.199 又修了一次"后台子 agent 也输出了一份导致双行"的 bug。多 agent 场景下这个功能的事件关系相当复杂，Anthropic 自己也踩了两轮。

## 最老的一层：上下文压缩

recap 这个词在 Claude Code 里最早出现，是为了**续命**——不是给人看的，是给 context window 腾地方。

你可能见过系统消息 "Context compacted"。触发时机是上下文用到约 93% 的时候，流程相当重：

1. 旧消息分段写磁盘，全量历史不丢，模型之后可以用工具重新读；
2. 主模型（带 thinking，v2.1.198 起还继承你当前的 effort 级别）生成一份结构化总结，包含 9 个区块：主要任务、关键技术概念、看过的文件、修过的错、解决过程、用户所有原话（verbatim）、待办、当前进度、可选下一步；
3. 这份总结打包成一条特殊的 user message 插回对话；
4. 重新把最近读过的 5 个文件（每个 ≤5k tokens）、plan、已调用的 skills、后台 agent 状态等重新 hydrate 回去，总预算 50k tokens；
5. 给模型一句话："Continue directly — no apology, no recap of what you were doing."（直接继续，别道歉、别复述你刚才在干嘛。）

最后那句特别好玩——意思是你都有这么详细的总结了，别再回我"好的我们继续处理刚才的 XXX 问题"。这句话在 v2.1.88 的 leak 源码里就有，在 `query.ts:1226`。

## 最隐蔽的一层：模型写给自己的小抄

这是四层里最早、也最看不见的一层。Anthropic 在多份 agent 设计文档里都推荐过一个 prompt pattern：让模型在每个 turn 结束时，用第三人称过去式写一句 summary——我刚才做了什么、还差什么没做。

它不是给你看的，是**给下一轮的模型自己看的**。

防 agent 死循环一般有两种做法：跑一个独立的 critic 模型盯着（贵、复杂），或者检测到循环就打断（滞后、误判多）。这个 trick 的思路很朴素：让模型在**快要结束 turn 的那一刻**自己写一句话——"我刚才做了啥、接下来干啥"。这个时间点写出来的东西最准，因为模型自己最清楚哪里卡住了。用一条 prompt 就把 critic 的部分职责内化进主模型，省掉一个独立调用。

Anthropic 在 Sonnet 4.5 / Opus 4.x 的 SWE-bench 沟通里多次提到，这代模型"能识别自己在循环并换方向"是 coding reliability 提升的重要来源之一——这种 turn-end self-reminder 就是配套的 prompt 侧加固。

而 v2.1.186 做的事情，就是把这份模型本来就要写给自己看的小抄，用 StructuredOutput 结构化了之后**顺便显示给你看**。一次输出，两处用途——内部给模型当下一轮 context，外部给你当锚点。零额外成本，零额外延迟。

## 计时器："Brewed for 1m 22s"

最上面那行动词 + 时长，其实是比 recap 老得多的独立组件，前缀是 `✻`（U+273B，不是键盘上的星号，视觉上很像而已）。

它的工作很简单：turn 开始挑一个动词，思考中显示"动词…"，结束定格"动词 for Xm Ys"，后面跟 token 用量和会话总时长。

```
✻ Worked for 2m 57s · 137.2k/1000.0k (14%) · 573m 35s
```

它跟 recap 唯一的关系是——视觉上挨在一起。turn 结束时计时器先停，视觉上形成一个"终止符"，你的视线顺着它就自然读到了旁边的 recap。两个独立功能搭出了一个挺舒服的视觉节奏。

`/config` 里 "Show turn duration" 可以关。

## 手动 `/recap`：随时问一句"我在干嘛"

除了自动弹的，你也可以随时敲 `/recap` 让它立刻说一遍现在在干嘛。

命令面板里长这样：

![在命令面板里输入 `/recap`：描述是 "Generate a one-line session recap now"](../../origin/2026-07-09-claude-code-recap-teardown/assets/screenshot-显式recap指令.png)

执行的时候会复用主 spinner：

![`/recap` 执行中：spinner 位置显示 `✻ Vibing…`](../../origin/2026-07-09-claude-code-recap-teardown/assets/screenshot-显式recap指令执行中.png)

结果是 `└` 前缀的一行英文：

![`/recap` 执行结果：`└ Goal: Understand how to generate images using Seedream...` 英文输出，`└` 前缀](../../origin/2026-07-09-claude-code-recap-teardown/assets/screenshot-显式执行recap指令效果.png)

这里有个挺容易踩的细节——手动 `/recap` **永远输出英文**，不跟随对话语言。自动的 end-of-turn recap 是跟语言走的（中文对话就出中文），但 `/recap` 走的是 slash command 通道，它是 assistant 回复的一部分、不是系统消息，前缀 `└` 也不一样。同名叫 recap，两套行为——这是"不同版本/不同模块拼起来"的典型痕迹。

## 怎么关

![`/config` 过滤 "recap" 只显示一个开关：Session recap = true](../../origin/2026-07-09-claude-code-recap-teardown/assets/screenshot-config.png)

```bash
# 关自动 away summary + end-of-turn recap（共用一个开关）
/config                       # → "Session recap" toggle off
# 或 settings.json: "awaySummaryEnabled": false
# 或环境变量: export CLAUDE_CODE_ENABLE_AWAY_SUMMARY=0

# 关自动 compact（不推荐）
/config                       # → "Auto-compact when context is full" off
# 或 export DISABLE_AUTO_COMPACT=1

# 关计时器行
/config                       # → "Show turn duration" off
# 或 settings.json: "showTurnDuration": false

# 全关（连手动 /compact 都关，不推荐）
export DISABLE_COMPACT=1
```

## 这东西为什么好用

技术拆完了，回到感受。这行 recap 好用，核心是它解决了一个我之前没意识到的问题——**多个 AI 窗口并行时的上下文重定向**。

大模型有百万 token 上下文，人类没有。开 3-5 个 Claude Code 窗口并行是常态——一个排障、一个 review MR、一个写新功能、一个部署 staging。每个窗口隔几分钟才回去看一眼，每次切回去都要花 10-30 秒扫上一轮对话想起来"我在这干嘛"。

10-30 秒 × 5 个窗口 × 一天几十次切换，这个认知摩擦非常具体。终端 title 和 tmux pane 名字只能给你一个项目名，给不了"下一步是什么"。

recap 做对了三件事：

1. **只有一行**。away summary prompt 硬约束 "exactly 1-3 short sentences"，end-of-turn 也是一段。超过三行就变成你不想读的墙。
2. **固定格式**：`Goal: ... <现状>. Next action: ...`。每次按这个模板输出，你肌肉记忆能直接跳到 "Next action:"，不用扫。
3. **dim 灰色、输入框上方**——不抢焦点，用外围视觉一 catch 就有。它不是主内容区大字报，是眼睛余光能接住的锚点。

## 它也不是没有槽点

**1. 早期版本有延迟问题。** 5 月底到 6 月初有人反馈每次 turn 结束多卡 1-2 分钟，社区一度流传 `ANTHROPIC_DISABLE_AUTO_PLAN_SUMMARY=true` 的 workaround。原因是 end-of-turn summary 早期用了独立的 LLM 调用（还没切到 StructuredOutput 方案），每次 turn 结束多一次模型往返。v2.1.186 把它并入主 response 后这个问题基本消失。

**2. 准确性偶尔翻车。** 但它是给下一轮模型当快速锚定用的，不是给用户做 ground truth 的，下一轮有完整上下文可以纠正，容错率比直觉高。

**3. 多 agent 场景下出过重复行 bug。** v2.1.186 和 v2.1.199 连着修了两次——第一次是子 agent 和父 agent 各输出一份，第二次是 schema 校验失败重试时新旧两份一起渲染。

**4. 配置入口散。** 四个相关功能共用 "recap" 这个词，但散在三个开关、两个环境变量里，第一次想关它得绕一圈。

**5. 自动 recap 跟语言走，手动 `/recap` 永远英文。** 同一个功能名，两种行为。

## 一个 prompt trick 怎么长成 UX 范式

回头看整个故事我觉得最有意思的是——**这几个功能不是一次性设计出来的，是几条独立线索在不同时间被接上 UI，在 v2.1.186 突然咬合的**：

- 2025 年：compact 为 context window 续命；
- 2025 底–2026 初：prompt 级 turn-end summary 防死循环（给模型自己看）；
- 2026-04-14：away summary 解决"离开再回来"的场景；
- 2026-04-14：`/recap` 手动命令上线；
- 2026-06-22：把那份模型本来就要写给自己看的 summary 结构化了显示给用户。

计时器在 recap 之前就存在，是独立 UI；recap 只是恰好接到它旁边，视觉上看着像一组。

最后这步最有设计感。其他几层都是"为了解决一个具体功能问题而做"——续命、防循环、离开再回来、手动触发。但把模型内部本来就在输出的结构化状态**顺手显示给用户看**，是另一类动作。做 agent 系统的人应该熟悉这个模式：进度条、当前文件、plan 展示、tool 调用展开——这些好用的 UX，本质上都是**把内部已有的状态加个渲染**，不是专门为 UX 再造一份。

抽出来就是一条可以复用的经验：**如果你在 agent 系统里已经让模型为了 self-correction、planning、memory 输出了某种结构化中间状态，几乎总是应该顺便也显示给用户**。成本已经付了，边际成本只是一行渲染代码，边际收益是可观察性和信任感。反过来，专门为了 UX 让模型多输出一份什么，大概率会掉进延迟/成本/准确性的三角坑。

传统 UI 产品思路是"用户需要看 X，所以让模型生成 X"；Claude Code 的思路是"模型本来就在生成 X 给自己用，顺便给用户看看"。两条路径出来的质感完全不同——前者容易感觉"贴上去的"、慢半拍、跟正文脱节；后者感觉原生、零成本、对得上正文，因为它本来就是正文的一部分。

那行 `※ recap: Goal: ...` 是这个设计哲学最小的展品。

---

## 附：关键版本时间线

| 日期 | 版本 | 事件 |
|---|---|---|
| 2026-03-30 | v2.1.88 | leak 基准；只有计时器 + compact，无 recap |
| 2026-04-14 | v2.1.108 | **Session Recap 初登场**（`/recap` + away summary，Haiku） |
| 2026-04-15 | v2.1.110 | Away summary 对 Bedrock/Vertex/Foundry 开放 |
| 2026-04-15 | v2.1.109 | 思考指示器加 rotating hint |
| 2026-04-17 | v2.1.113 | 修复"用户打字时 recap 弹出"的竞态 |
| 2026-04-20~24 | Week 17 digest | 官方首次在 "What's new" 宣传 Session recap |
| 2026-05-27 | v2.1.152 | 思考计时器改成 live "Thinking for Ns" |
| 2026-06-17 | v2.1.181 | `/recap` model switch bug 修复 |
| 2026-06-22 | v2.1.186 | **End-of-Turn Recap 上线**——agent 内 summary 接上 UI 槽位 |
| 2026-06-29 | v2.1.196 | 修复 StructuredOutput schema reject 导致的双行 recap |
| 2026-07-01 | v2.1.198 | Compact 继承 session extended thinking config |
| 2026-07-02 | v2.1.199 | 修复 background session 双行 recap（第二次） |
| 2026-07-08 | v2.1.205 | 本文截图所用版本 |

## 参考资料

- Claude Code 官方 changelog: https://code.claude.com/docs/en/changelog
- "What's new" Week 17 (Apr 20-24, 2026): https://code.claude.com/docs/en/whats-new/2026-w17
- Interactive Mode 文档（Session recap 章节）: https://code.claude.com/docs/en/interactive-mode#session-recap
- CLI 命令参考（`/recap`）: https://code.claude.com/docs/en/commands
- Anthropic Engineering — Building Effective Agents: https://www.anthropic.com/engineering/building-effective-agents
- Simon Willison — "New trick for Claude Code running long, slow tasks" (2026-04-09): https://simonwillison.net/2026/Apr/9/claude-code-slow-tasks/
- Claude Code v2.1.88 leaked source（`src/services/compact/`, `src/constants/turnCompletionVerbs.ts`, `src/query.ts` 等）
