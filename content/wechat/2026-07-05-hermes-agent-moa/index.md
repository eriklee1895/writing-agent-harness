---
title: "Mixture of Agents揭秘：Hermes Agent让三个模型围坐开会，答案更准了"
date: 2026-07-05
tags: [agent, mixture-of-agents, hermes, llm, architecture]
source: content/wechat/2026-07-05-hermes-agent-moa/index.md
status: draft
---

# Mixture of Agents揭秘：Hermes Agent让三个模型围坐开会，答案更准了

![封面：Hermes Agent × 多模型 pipeline——dark premium editorial，brand mark + 模型 logo + 天平 verdict。](assets/cover.png)

*封面：Hermes Agent × 多模型 pipeline。*

## 一个问题：总有一个模型差一口气

如果你经常用 AI 写代码、审方案、做复杂判断，大概经历过这种时刻——

同一个难题，扔给 Claude，它太保守；扔给 GPT，深度不够；扔给 DeepSeek，工具调用又有点飘。你换了一圈，发现每个模型都差那么一口气。

于是很自然地想：能不能让几个模型一起想？

不是投票选最好的答案，而是让它们各自出一份意见，再让一个最强的模型把这些意见揉成一个新答案。这就是 **Mixture of Agents（MoA）** 的核心想法。

MoA 不是新概念。2024 年 Together AI 的论文就验证过一件事，他们把它叫做 **collaborativeness**：

> 一个强模型在看到其他模型的回答后，往往能写出更好的回答——即使那些模型单独看比它弱。

换句话说，三个模型围坐开会，最后合成的答案可能比单打独斗更好。

![Collaborativeness：三个大小不一的 reference 圆汇入 aggregator，弱者也有贡献。](assets/collaborativeness.png)

*collaborativeness：弱者也帮忙——AlpacaEval 2.0 上开源 MoA 比单模型 GPT-4o 高 7.6 个点。*

## Hermes 的做法：把 MoA 伪装成一个模型

很多 MoA 实现是一条独立的流水线：你输入 prompt，它跑完 proposer → aggregator，吐一个答案。但 Hermes Agent 是个完整的 agent runtime，有工具调用、多轮对话、记忆、缓存、消息网关。

如果 MoA 是独立流水线，那 agent 的这些能力就断了。MoA 跑的回合不能调工具，不能 resume，缓存也对不上。

Hermes 的解法很干净：**把 MoA 伪装成一个虚拟模型 provider，叫 `moa`**。

选了 `moa` 这个 provider，agent loop 完全不变。它照样调 `chat.completions.create`，但这一次调用被 MoAClient 拦截：内部先并行跑几个 reference 模型，把它们的输出塞进 aggregator 的上下文，再由 aggregator 真正发起一次带工具的调用。

关键结论是：**aggregator 就是 acting model**。它不是"先合成再交给 agent"——它自己就是 agent，能调工具、能多轮。reference 模型只是顾问，没有工具权限。

这意味着，MoA 从"一条独立 pipeline"变成了"agent 的一种模型选择"。tool use、memory、缓存、session resume 全部原样工作。

## 看委员会 deliberation，而不是直接读 verdict

Hermes 把 MoA 做进 agent loop 后，带来两个很妙的 UX 效果：

**第一，每个 reference 的推理都可见。**

MoA 跑起来时，你能先看到 GPT-5.5 怎么想、DeepSeek 怎么想、Grok 怎么想，然后再看 aggregator 怎么综合。release notes 的说法是："you get to watch the committee deliberate, not just read the verdict"。

![Transparency：三个 reference 面板 + AGGREGATING 分隔 + VERDICT 面板。](assets/concept-deliberation.png)

*"看委员会 deliberation，再读 verdict"——透明性是 MoA 区别于黑盒 routing 的独立价值。*

**第二，aggregator 实时流式输出。**

最终答案不是等所有 reference 跑完再一起蹦出来，而是边想边流。这直接缓解了 MoA 2× 延迟的体感。

这两点不只是打磨。对生产 agent 来说，**透明性**是个真实差异：你能审计每个 advisor 说了什么、aggregator 在哪几个轴上没采纳。debug 和向 stakeholders 解释模型为什么这样答，都更容易。

## 怎么开启 MoA：三种调用方式

MoA 在 Hermes 里就是个 model，用法和选普通模型一样。

**三种触发方式：**

```bash
# 1) 持久切换：整个 session 用某个 preset
/model default --provider moa

# 2) 一次性：单个 prompt 走默认 preset，跑完恢复原模型
/moa review this migration plan for race conditions

# 3) CLI / 脚本：-z one-shot + --provider moa
hermes -z "<prompt>" --provider moa -m default
```

`/moa` 是 one-shot sugar，不是 model switch——文档原话："`/moa` is deliberately not a model switch, so a normal prompt can never accidentally change your model"。你不会因为一个 prompt 意外把整个 session 切到 MoA 上烧钱。

**preset 管理：**

```bash
hermes moa list                 # 看现有 preset
hermes moa configure [name]     # 交互式建/改 preset
hermes moa delete <name>        # 删
```

我本地重新配了一个全部用中文区可用 provider 的 preset：

```yaml
moa:
  default_preset: default
  presets:
    default:
      reference_models:
        - provider: doubao
          model: deepseek-v4-pro-260425
        - provider: minimax
          model: MiniMax-M3
        - provider: kimi
          model: kimi-for-coding
      aggregator:
        provider: doubao
        model: doubao-seed-2-1-pro-260628
      reference_temperature: 0.6
      aggregator_temperature: 0.4
      max_tokens: 4096
      reference_max_tokens: 600   # 压 advisor 输出上限，降延迟
      fanout: per_iteration       # 或 user_turn
      enabled: true
```

reference 选了三个不同家族：豆包火山 DeepSeek、MiniMax、Kimi。aggregator 用豆包 Seed 2.1 Pro。

几个关键旋钮：

- `reference_max_tokens`：建议设 600 左右，aggregator 只需要要点。
- `fanout`：`per_iteration`（每次 tool 迭代重跑 reference，看最新状态）/ `user_turn`（每个 user turn 只跑一次，省 token）。
- `enabled: false`：aggregator 单独跑，等于关掉这个 preset 的 MoA。
- 递归禁止：reference 或 aggregator 不能再是另一个 `provider: moa`。

## 我的实测结果

我用上面的 preset 跑了一个真实任务：设计一个 flaky LLM gateway 的重试 + 退避 + 熔断策略。prompt 末尾加了约束"只输出文本回答，不要创建文件"，避免模型把代码写进文件导致输出不可比。

| 指标 | DeepSeek v4-pro 单模型 | 豆包 Seed 2.1 Pro 单模型 | MoA（3 refs → Seed 2.1 Pro） |
|---|---|---|---|
| 墙钟时间 | **99s** | **131s** | **215s**（1.6× vs Seed） |
| 输出词数 | 1848 | 2718 | 1716 |
| reference 失败 | — | — | 无，3 个全部成功 |

三个发现：

1. **延迟没有想象中那么高**。MoA 比同 aggregator 单模型慢约 60%，不是简单的 2-3×。dominant cost 是最慢的 reference，但 reference 是并行跑。
2. **输出更精炼**。MoA 输出 1716 词，比 Seed 单模型的 2718 词少很多——aggregator 综合三个视角后做了取舍，没有照搬某一个模型的全部展开。
3. **没有 reference 失败**。三个 provider 的 key 都配对了，fan-out 全部成功。

### 合成而非选择

单跑时，DeepSeek v4-pro 给的是：4 attempts / base 1s / cap 30s / full jitter / 5-consecutive-failure breaker / open 30s。

豆包 Seed 2.1 Pro 单跑时给的是更完整的分类学：先分 failure taxonomy，再给参数表，结构更重。

MoA 最终输出取了中间路线：4 attempts / base 0.5s / cap 30s / **full jitter** / **rolling 30s window breaker** / open 15s / half-open 2 probes。

它既没有照搬 DeepSeek，也没有照搬 Seed。它用了 DeepSeek 的 4 attempts 和 full jitter，但把 base 降到 0.5s、breaker 改成滑动窗口、recovery timeout 压到 15s。这些折中在任何一个单模型输出里都不是完整出现的。

这就是"合成而非选择"：不是投票选最好的方案，而是把多个顾问的判断揉成一个新方案。

## 生产里的一个好处：失败隔离

Hermes 的设计承诺是：单个 reference 凭证/网络挂了，失败信息会写进 reference guidance block，aggregator 继续跑。

![Failure isolation：一个 reference 失败，其余 + aggregator 照常产出 verdict。](assets/failure-isolation.png)

*生产可靠性：单个 reference 凭证/网络挂了，其余 + aggregator 照常出 verdict。*

生产里这意味着：你 fan-out 到 3 个 provider，一个挂了，剩下两个 + aggregator 仍能产出。这是多 provider 架构的实际价值。

## 什么时候值得用？

先说代价：

- 延迟 ≈ 1.6-2.2×（取决于最慢的 reference）
- token ≈ 2-3×
- 增益随 reference 数量递减

所以它不适合：实时聊天、简单任务、reference 池同质化、token 预算紧。

适合的场景：

1. **硬推理 / 高 stakes 决策**：架构评审、安全审计、复杂 bug 根因分析。HermesBench 数据：Opus+GPT-5.5 MoA 拿 0.8202，Opus 单独 0.7607——MoA 比最强组件高 6 个点。
2. **代码生成质量**：用本地能跑通的模型配 preset 一样有效。
3. **对齐 / 验证层 + 透明审计**：多 reference 天然是"第二意见"机制，且每个 reference 的推理可见。
4. **长程 agent 里的硬 turn**：用 `/moa` 临时触发一次，平时单模型。

一句话：**MoA 是用额外延迟和 2-3× token，换硬任务上的质量上限 + 过程透明**。它不是默认开的东西，是一个按需触发的"重炮"。

## 如果不用 Hermes，核心模式只有三步

自己实现一个最小 MoA 也就几十行，关键是三件事：

1. **reference 拿裁剪视角**：去掉 agent 的 system prompt、工具 schema，只保留对话文本，避免噪音和 provider 拒绝。
2. **尾部追加 guidance**：把 reference 输出放在对话末尾，不破坏前面的 prompt cache。
3. **aggregator 带 tools 当 actor**：它才是真正的 agent，reference 只是顾问。

Hermes 多做的——多 provider 混用、按模型计价、失败隔离、fanout 节奏、trace——是生产化打磨。核心就上面三步。

## 收尾

单模型撞 ceiling 时怎么办？MoA 给的答案不是"挑一个更强的模型"，而是"让多个模型协作，aggregator 合成"。

Hermes 聪明的地方在于：它没把 MoA 当默认，而是做成一个**可按 turn 触发的 model 选择**。`/moa` 一炮，平时单模型。这把 MoA 从"全开或全关"变成 cost/quality 轴上的一个 dial。

如果你有硬 stakes 的评审/决策场景，且能接受 1.6-2.2× 延迟，MoA 值得作为"重炮"按需触发。如果你只是想让日常 chat 更聪明一点，挑一个更好的单模型回报更高。

---

**参考**：

- Hermes Agent MoA 文档：https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents
- Hermes Agent v0.18.0 release notes：https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.1
- Together AI MoA 论文（Wang et al. 2024）：https://arxiv.org/abs/2406.04692
- Together AI MoA blog：https://www.together.ai/blog/together-moa
