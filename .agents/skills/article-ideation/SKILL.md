---
name: article-ideation
description: "把模糊写作灵感打磨成清晰 writing brief 和 outline。Use whenever the user says 我想写一篇/有个想法/帮我理一下/脑暴/选题/文章思路/outline, or provides rough notes before drafting. This skill should run before research/draft/polish when the article angle, thesis, target reader, or structure is not yet clear."
---

# Article Ideation

## Overview

这个 skill 用于写作最早期：把用户的灵感、零散素材、情绪判断或模糊选题，变成可执行的 `writing brief`、`research questions` 和初版 `outline`。

目标不是马上写正文，而是先帮 Erik 想清楚：这篇文章到底要写什么、为什么值得写、写给谁、判断是什么、不该写成什么样。

## When To Use

Use this skill before drafting when:

- 用户说“我想写一篇……”“我有个想法”“帮我理一下思路”“脑暴一下”“这个选题怎么看”。
- 用户给了灵感、素材、链接、截图或几段想法，但还没有清晰 thesis。
- 文章的 target reader、angle、tone、distribution channel 还不明确。
- 用户想先确定 outline，再进入 research / draft。
- Agent 准备主动写作，但还不确定用户真正想表达的锋芒和边界。

If the user already provides a complete draft and asks for polish, use `polish-article` instead. If the user asks for WeChat formatting, use `wechat-article-renderer` after the article content is ready.

## Core Principle

不要急着写文章。先通过几轮高质量问题和建议，帮助用户把想法从“灵感”推进到“可写作的设计”。

好的 ideation 应该同时做到：

- 理解用户已经想到的点；
- 补充用户可能没想到的角度；
- 澄清文章的中心问题；
- 形成明确 thesis；
- 识别事实查证需求；
- 给出可执行 outline。

## Workflow

### 1. Restate The Spark

先用自己的话复述用户的灵感，确认你理解的是同一件事：

```text
我理解你想写的不是 X，而是 Y：……
这篇文章可能真正有价值的地方在于：……
```

如果用户的信息很少，先问 1-2 个关键问题，不要一次抛出长问卷。

### 2. Calibrate The Article

围绕这些维度脑暴和校准：

- `central question`: 这篇文章要回答什么问题？
- `target reader`: 写给谁？他们已经知道什么？最关心什么？
- `thesis`: 作者最想表达的判断是什么？
- `angle`: 从哪个切口进入最有新意？
- `stakes`: 这件事为什么重要？影响谁？
- `tone`: 专业分析、技术博客、个人观察、文学化散文，还是微信公众号长文？
- `anti-goal`: 不想写成什么样？不要落入什么俗套？
- `distribution`: 博客、微信公众号、其他平台是否需要不同包装？

### 3. Offer Better Angles

主动提供 2-4 个可选角度，并说明 trade-off。

示例：

```text
方向 A：事件解读。优点是及时，缺点是容易像新闻复述。
方向 B：产业结构分析。优点是有深度，缺点是需要更多事实支撑。
方向 C：个人经验切入。优点是有辨识度，缺点是需要控制主观性。
```

Lead with your recommendation, but keep space for the user's taste.

### 4. Produce A Writing Brief

当思路基本清楚后，输出这个模板：

```markdown
## Writing Brief

**Working title:** ...

**One-line idea:** ...

**Central question:** ...

**Target reader:** ...

**Thesis:** ...

**Why now:** ...

**Angle:** ...

**Tone / register:** ...

**Anti-goals:** ...

**Key points:**
- ...

**Research questions:**
- ...

**Likely sources / evidence:**
- ...

**Distribution notes:**
- Blog: ...
- WeChat: ...
```

### 5. Draft The Outline

基于 writing brief 给出初版 outline。优先给清晰信息路径，而不是漂亮标题。

```markdown
## Draft Outline

1. Opening: ...
2. Context: ...
3. Core argument: ...
4. Evidence / cases: ...
5. Implications: ...
6. Closing: ...
```

For WeChat longform, include reading rhythm: where to add summary card, reader map, tables, or visuals.

### 6. Ask For Confirmation

结束时让用户确认 brief 和 outline。如果任务较重（多步骤、跨多轮 agent 执行），可以建议用户把 brief 和 outline 先落盘到 `content/drafts/YYYY-MM-DD-<slug>/writing-brief.md`，防止 context 丢失。

确认方向后，下一步就是直接开始写作。agent 在写作前应读取 [docs/reference/format-standards.md](../../docs/reference/format-standards.md) 了解不同输出格式的写作方法论和视觉手段。

## Output Rules

- 不要在 ideation 阶段直接生成完整正文，除非用户明确要求。
- 如果用户只是想快速聊想法，可以先轻量输出，不强制完整模板。
- 对 current events、company/product facts、pricing、laws、fast-moving tech topics，只提出 research questions，不凭记忆定论。
- 保留用户个人判断和表达锋芒，不要把选题打磨成无风险的泛泛话题。
- 如果一个想法不值得写，直接说，并提出更值得写的改法。

## Handoff

- 需要查证资料：进入 research，并记录具体日期和来源。
- 需要写初稿：使用 writing brief 和 outline 作为约束。写作前读取 [docs/reference/format-standards.md](../../docs/reference/format-standards.md)。
- 需要润色已有稿件：交给 `polish-article`。
- 需要微信公众号排版：内容完成后交给 `wechat-article-renderer`。
