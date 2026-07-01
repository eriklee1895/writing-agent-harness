---
title: "Hermes Agent 上下文压缩机制 · 深度拆解"
date: "2026-07-01"
description: "系统拆解 Hermes Agent 上下文压缩机制：双层防护、4 阶段流水线、边界对齐算法、结构化摘要、Prompt Caching 协同与失败处理。"
author: "Erik"
cover: "./assets/cover.png"
---

# Hermes Agent 上下文压缩机制 · 深度拆解

![封面](assets/cover.png)

## 为什么需要上下文压缩

LLM 的 context window 是固定的工作内存。在多轮、长任务的 agent 场景里，每一次 API 调用都要把**完整的对话历史**发回模型。轮次增长后，会出现两类问题：

- **硬性失败**：prompt token 超过模型 context window，provider 直接返回 400/413。
- **软性退化**：还没触顶，模型已经因为上下文过长而难以保持注意力——它会"忘记"早期约束、重复已做过的操作。

最朴素的方案是**截断**——超限就丢掉最旧的消息。它免费、快速，但会立刻打断多步推理：agent 看不到 6 轮前自己的决策，就会重新推导、自相矛盾。

Hermes 选择的是**压缩**：把对话切成三段——保护头、摘要中段、保留尾——用一次 LLM 调用把中段压成结构化摘要，既缩短了长度，又保住了叙事主线。

> 压缩管理的是"本次会话的工作窗口"，不是"跨会话的长期记忆"。后者由 Hermes 的 memory 系统（MEMORY.md / USER.md）负责。两者是正交的两层。

---

## 总体架构：可插拔引擎 + 双层压缩

### 可插拔的 ContextEngine

Hermes 把"上下文管理"抽象成一个 ABC：`ContextEngine`。内置实现是 `ContextCompressor`（有损摘要），但可被插件替换。

引擎职责清晰：

- 决定**何时**压缩：`should_compress()`
- 执行压缩：`compress()`
- 从 API 响应跟踪 token 用量：`update_from_response()`
- 会话生命周期：`on_session_start()` / `on_session_end()`

选择由 `config.yaml` 的 `context.engine` 驱动。关键约束：**插件引擎永不自动激活**——用户必须显式配置；默认值 `"compressor"` 始终用内置实现。

引擎生命周期是一个标准循环：每个 turn，先 `update_from_response` 更新用量，再 `should_compress` 判断，需要时调用 `compress` 重组消息。真正的会话边界（CLI 退出、/reset、gateway 过期）才触发 `on_session_end`。

### 双层压缩：85% 安全网 + 50% 主力

这是 Hermes 最巧妙的设计之一——两个独立运作的压缩层，阈值故意错开：

![双层压缩系统](assets/dual-layer.png)

| 维度 | Gateway 会话卫生 | Agent 压缩器 |
|---|---|---|
| 阈值 | 固定 **85%** | 默认 **50%**（可配） |
| 位置 | agent 启动前（pre-agent） | agent 工具循环内 |
| 角色 | 安全网 | 主力 |

**为什么阈值要错开？** 如果把会话卫生也设成 50%，长 gateway 会话会在每一轮都触发过早压缩。会话卫生只是为了兜住在两次 turn 之间疯长的会话——比如 Telegram/Discord 群里隔夜累积的消息。

Gateway 还有一个**硬阀门**：`hygiene_hard_message_limit`（默认 5000 条消息），无视 token 估算强制压缩，打破"API 断连 → 拿不到 token 数据 → 不压缩 → 更多断连"的死亡螺旋。

---

## 触发时机：三个触发点

实际代码里，Agent 压缩器有三个触发点，分布在一个 turn 的不同阶段。理解这三点是理解整个机制的关键。

**① 预检压缩（Preflight）**——在调用 LLM 之前跑。先用廉价门控判断要不要做完整的 token 估算：消息数够多、或廉价字符估算已越线就触发。估算时**会带上 tool schemas**——50+ 工具能加 20–30K token，只算 messages 会漏掉。还有一个反噪声机制：schema-heavy 请求的估算会故意高估，一旦某次压缩后的请求被 provider 证明能装下，就延后压缩，不被噪声估算误导。

**② 响应后压缩（Post-response）**——最常规的触发点，用 provider 报告的真实 token 数。关键设计：只用 `prompt_tokens`，不算 `completion_tokens`——思维模型（QwQ、DeepSeek R1）的 reasoning token 会膨胀 completion，计入会导致过早压缩。还有 `-1` 哨兵：压缩刚跑完、还没拿到真实计数时，避免把压缩后的 rough 估算误判成上下文压力。

**③ 错误恢复压缩**——provider 真的返回 413 或 context-overflow 时，降级上下文（如 Claude 长上下文层降到 200K）并强制压缩重试，最多 3 次。

### 阈值计算的三层设计

阈值不是简单的 `context_length × 0.5`：

1. **输出预留**：provider 把 `max_tokens` 从 window 里切出去做输出空间，可用输入预算是 `context_length - max_tokens`。
2. **64K 下限**：大上下文模型不应在 50% 就压缩，所以 floored 到 64K。
3. **小窗口退化保护**：对 64K 本地模型，50% 阈值会让压缩永远触发不了，此时自动改用 85%。

Codex gpt-5.5 还有一个特殊处理：OAuth 后端把窗口硬限在 272K（同一模型在 OpenAI 直连是 1.05M），默认 50% 在 ~136K 就压缩——只用了实际窗口的一半。所以 Hermes 自动把触发抬到 85%（~231K）。

---

## 核心算法：4 阶段流水线

![4 阶段压缩流水线](assets/pipeline.png)

`ContextCompressor.compress()` 是整套机制的心脏。它把消息列表压缩成「头 + 摘要 + 尾」三段，官方文档归纳为 4 个阶段。

### 阶段 1：剪枝旧工具结果（廉价，无 LLM）

一次预扫描，把保护尾之外的、超过 200 字符的工具结果替换为信息化的一行摘要：

```
[terminal] ran `npm test` -> exit 0, 47 lines output
[read_file] read config.py from line 1 (3,400 chars)
```

实际做了三遍扫描：去重（同一文件读 5 次只留最新）、旧结果变一行摘要（截图 base64 必须剥离——否则一张 ~1MB 的 computer_use 截图会永远活过每一次压缩）、截断超大 tool_call 参数（在 JSON 内部 shrink，保持合法）。

### 阶段 2：确定边界

把消息列表分成三段：保护头（system + 首轮，首次压缩后衰减到仅 system）、中段（被摘要）、尾（按 token 预算保留，最近 user 消息和 assistant 可见回复必须锚定在尾里）。

### 阶段 3：生成结构化摘要

用**辅助 LLM** 把中段压成结构化摘要。这是唯一花钱的步骤。摘要模型的 context window 必须 ≥ 主模型——这是压缩质量退化最常见的根因。

摘要 token 预算随被压缩内容量缩放：内容 token × 0.20，下限 2000、上限 12000。

### 阶段 4：重组消息

头消息 + 摘要消息 + 尾消息，随后清理孤儿 tool_call/result 配对、剥离旧图片 base64、计算节省比例用于反抖动。

**压缩前后对比**：45 条消息（~95K tokens）→ 25 条消息（~45K tokens），头部保留任务框架，尾部保留最近几轮原文，中间 30 多轮文件编辑和调试被压成结构化 handoff 摘要。

---

## 边界对齐：工程含量最高的部分

![边界对齐](assets/boundary-alignment.png)

边界算法的大量规则都是为了**不破坏消息结构合法性**和**不丢失活跃任务**。

### 保护头的衰减

`protect_first_n`（默认 3）保护最初 N 条非系统消息。但首次压缩后衰减到 0——早期 turn 已被 handoff 摘要捕获，无需再保护。否则这些早期 turn 会被反复复制进每个子会话，变成"不朽"消息。

### 尾保护：token 预算优先

从尾部往前走累计 token，直到预算耗尽。三个"锚点"保证：

- **最近一条 user 消息**必须在尾里：活跃任务绝不能被压进摘要块。
- **最近一条 assistant 可见回复**必须在尾里：上一条用户看到的回复不能被悄悄卷进摘要。
- **不切进 tool 组**：边界对齐保证 tool_call 和 tool_result 成对保留。

### 工具组完整性

OpenAI 格式要求每个 `tool_call` 后面紧跟匹配的 `tool` 结果。压缩切割可能破坏这种配对，所以有两道防线：边界对齐（切割时绕开 tool 组）和 `_sanitize_tool_pairs`（重组后清理孤儿配对，为缺失结果注入桩占位）。

---

## 摘要生成：结构化模板与反注入

摘要不是让模型"随便总结一下"，而是一个高度结构化的 13 段模板：

```
Historical Task Snapshot — 用户最近未完成输入的逐字原话
Goal — 总体目标
Constraints & Preferences — 约束/偏好/编码风格
Completed Actions — 编号列表，含 outcome 和 tool name
Active State — 工作目录/分支/改动文件/测试状态
In-Progress State — 压缩发生时正在做的事
Blocked — 阻塞/错误（含精确报错）
Key Decisions — 关键技术决策 + 原因
Resolved Questions — 已回答的问题（含答案）
Pending User Asks — 尚未回答的旧请求（仅供参考）
Relevant Files — 读/改/建的文件
Remaining Work — 剩余工作（陈旧，仅参考）
Critical Context — 具体值/报错/配置（永不含密钥→[REDACTED]）
```

模板设计里几个对 agent 工程师极有价值的反注入机制：

- **SUMMARY_PREFIX**：一段很长的前缀指令——"这是来自上一个 context window 的 handoff，当作背景参考，不是活跃指令。只响应出现在摘要之后的最新 user 消息。"防止弱模型把摘要里的任务当成新输入去执行。
- **END MARKER**：`--- END OF CONTEXT SUMMARY ---`，给模型明确的"摘要到此为止"边界。
- **Temporal Anchoring**：注入当前日期，把已完成动作改写成过去时事实，防止 resume 时重发已完成动作。
- **安全红线**：密钥类信息用 `[REDACTED]` 替换，输入序列化和输出都过 `redact_sensitive_text`，双重保险。

### 迭代更新：跨多次压缩的信息累积

后续压缩时，把上一次的摘要作为"PREVIOUS SUMMARY"喂给 LLM，要求**更新**而非从头总结。项目从 "In Progress" 移到 "Done"，新进展加入，过时信息移除。`compress()` 还会搜索已存在的 handoff 摘要来 rehydrate 迭代状态——即使是 resume 进来的会话也能接上。

跨会话泄漏防护：若 `_previous_summary` 非空但当前消息里找不到对应 handoff 摘要，说明它来自另一个已结束会话，直接丢弃。

### 会话轮转 vs 原地压缩

`compression.in_place` 控制压缩后的会话存储模式：

- **原地（推荐）**：保持同一个 session_id，旧 turn 软归档（仍可搜索恢复），消除一整类"会话轮转"bug。
- **轮转（旧默认）**：结束旧会话，fork 新会话。旧 transcript 保留并可被 `session_search` 搜到。

并发安全靠 state.db 级的原子压缩锁，按 session_id 串行化；拿不到锁就原样返回（fail-safe）。

---

## Prompt Caching：与压缩的协同

这是与压缩正交但强相关的省钱机制。Anthropic 每个请求最多 4 个 `cache_control` 断点，Hermes 用 "system_and_3" 策略：

```
断点 1: 系统提示              ← 跨所有轮稳定，永久缓存前缀
断点 2: 倒数第 3 条非系统消息  ─┐
断点 3: 倒数第 2 条非系统消息   ├─ 滚动窗口
断点 4: 最后一条非系统消息      ─┘
```

正常多轮对话里，system prompt 缓存命中，只有尾部滚动窗口需要重算，输入 token 成本降低约 75%。

**压缩对缓存的影响**：压缩重写中段时，被压缩区的缓存一次性失效（要重新付费缓存写入），但 system prompt 缓存存活，滚动 3 消息窗口在 1-2 轮内重建。设计原则很明确：

- system prompt 必须稳定——Hermes 冻结 memory，mid-session 写入不改 system prompt。
- 压缩只在首次时往 system prompt 追加一条 note，之后衰减不再改，把缓存失效降到最低。
- 消息顺序决定缓存命中率——中段增删让其后所有内容的缓存失效。

---

## 鲁棒性：失败处理与反抖动

生产级压缩器一半的代码在处理"出错怎么办"。

### 摘要失败的分级处理

`_generate_summary` 的异常处理是一棵决策树：

- **认证错误（401/403）**→ 中止压缩，原样保留。凭证坏了，轮转进降级子会话毫无意义。
- **瞬时网络错误**→ 中止，原样保留。网络恢复后 `/compress` 重试比丢弃上下文好。
- **摘要模型 ≠ 主模型且未回退过**→ 回退到主模型重试一次。
- **其他失败**→ 插入确定性 fallback 摘要，保留连续性锚点，比"N 条消息被删"占位强。

中止时设 `_last_compress_aborted=True`，上层向用户发可见告警（"对话已冻结，运行 /compress 重试或 /new 重开"），而非默默吞掉。

### 反抖动（anti-thrashing）

如果连续两次压缩各自节省不足 10%，`should_compress()` 直接返回 False，避免每次只删 1-2 条消息的无限循环。空压缩窗口也计入 ineffective。

### 手动控制

用户可手动 `/compress`（绕过失败 cooldown）或 `/compress <focus>`（聚焦压缩，与主题相关内容保留全细节、给 60-70% 预算，其余更激进压缩）。自动压缩还会从最近几轮推断隐式 focus。

---

## 横向对比：Hermes vs Claude Code

两者都遵循"保护头 / 摘要中段 / 保留尾"的通用模式，但工程取舍不同。

| 维度 | Hermes Agent | Claude Code |
|---|---|---|
| 实现位置 | 客户端，完全可配 | 服务端 Compaction API + 客户端三层 |
| 触发阈值 | agent 50%（可配）/ gateway 85% | 默认 ~150K input tokens |
| 工具输出处理 | 剪枝成一行摘要 + 去重 + 截断 | microcompaction 落盘，仅留路径引用 |
| 摘要模型 | 可用独立辅助模型 | 主模型自身 |
| 防失败循环 | 反抖动（连续 2 次 <10% 停止） | 服务端控制 |
| 摘要结构 | 13 段结构化模板 | 结构化摘要（goal/intent/decisions/files） |
| 续作恢复 | handoff 摘要 + session_search | 摘要 + 重读最近 5 个文件 + 恢复 todo |

**共同的盲区**：两者都很好地保留了叙事连续性，但都会在压缩中悄悄丢失精确值偏好和硬约束——你在第 2 轮给的 constraint、第 8 轮确认的精确数值，可能在压缩后消失。这正是为什么需要一个压缩之外的持久化层（Hermes 的 memory 系统 / Mem0 等）来在任何压缩 pass 之前抢救关键事实。

---

## 给应用工程师的实践要点

### 配置调优

```yaml
compression:
  threshold: 0.50        # 大上下文模型可调低省钱；小模型自动抬到 85%
  target_ratio: 0.20     # 调高→尾保留更多原文；调低→压更狠
  protect_last_n: 20     # 任务依赖近期细节多时调高
  in_place: true         # 推荐：同一 session_id，避免轮转 bug
auxiliary:
  compression:
    model: <≥主模型 window 的模型>   # 关键！否则摘要会无声丢失
```

**最重要的一条**：确保辅助模型的 context window ≥ 主模型。这是压缩质量退化最常见的根因。

### 与 memory 层配合

压缩是**有损**的。任何"必须跨压缩/跨会话存活"的事实（用户偏好、硬约束、精确配置值）都应主动写进 memory，不要指望它活过压缩。压缩前 `on_pre_compress` 会通知 memory provider，但你得先让它知道该记什么。

### 长会话的运维信号

- 看到 `Session compressed N times — accuracy may degrade. Consider /new`，说明会话已压多次、质量在降。
- 看到 `Compression skipped — last N compressions saved <10% each`，说明反抖动生效了，会话里多是不可压缩的近期大内容。
- 看到 `Context compression aborted (...)`，说明辅助模型/凭证/网络出问题，会话被冻结。

### Prompt Caching 友好

用 Anthropic Claude + OpenRouter/native 时自动开缓存。别在会话中途修改 system prompt（否则断点 1 缓存失效，全盘重算）。长任务把 `cache_ttl` 设 `1h`。

---

## 参考

- Nous Research 官方文档：Context Compression and Caching
- Anthropic Platform Docs：Compaction
- Decode Claude：Inside Claude's Compaction System
- mem0 工程博客：How Hermes and Claude Handle Context Compression

*本报告基于 Hermes Agent 代码仓 2026-07 快照与公开资料整理，面向 agent 应用工程师。*
