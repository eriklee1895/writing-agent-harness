# Example Filled Writing Plan

以下是一个 Agent/AI 技术文章的 writing-plan.md 示例，展示填充后的深度和语气。

```markdown
---
working_title: "Agent 上下文管理：从单轮到长任务"
slug: agent-context-management
brief_source: "./writing-brief.md"
created: 2026-06-13
title_status: working
primary_register: "Agent / AI Technical Essay"
---

# Writing Plan: Agent 上下文管理：从单轮到长任务

## 1. What We Think We Know

> 从 brief 提炼的核心决策。这些是 plan 阶段的假设，执行过程中可以修正。

**Central question:** 当 agent 任务从单轮扩展到多轮/长任务时，上下文管理和记忆策略应该如何设计？

**Thesis:** 当前 agent 框架对"长任务上下文管理"的讨论还不够——大多数方案只处理了单轮内的 context window，而没有考虑跨轮/跨 session 的记忆、压缩和恢复。真正可工作的长任务 agent 需要在 token budget、选择性遗忘、外部 memory 和 handoff 协议四个维度上同时设计。

**Target reader:** 做过 AI agent 系统、对 context window 和 tool use 有基本理解的开发者/架构师。

**Angle:** 从实战踩坑切入，而不是从论文或概念切入。

**Why now:** 2026 年上半年 agent 框架的"长任务"能力成为竞争焦点，但大部分讨论停留在 benchmark 层面，缺少工程实践的解剖。

**Anti-goals:** 不要写成论文综述；不要空泛地谈"上下文很重要"；不要给具体产品的 benchmark 对比表。

## 2. Output Guidelines

> 目标格式和呈现偏好。以下是**偏好**，不是硬性规格。

- **Format:** Markdown 技术报告 → 微信公众号
- **Target length:** ~5000 字
- **Media:** 需要配图

**Format-specific preferences:**

| 格式 | 图表/视觉建议 |
|------|-------------|
| Markdown 技术报告 | 核心概念（如 token budget 衰减、memory 分层）用 Mermaid 图表；整体架构用 `article-illustration` 生成插图。 |
| 微信公众号 | 交 `wechat-article-renderer` 排版，style 默认 `agent-flow`。 |

## 3. Voice & Register Notes

> 来自 SOUL.md 的简要提示，帮助执行 agent 快速对齐作者气质。不重复 SOUL.md 全文。

- **Primary register:** Agent / AI Technical Essay
- **Key voice notes：**
  - 像真正做过 AI agent 系统的人，关注 workflow、task decomposition、context management、failure modes
  - 写清楚 trade-off，不只写愿景
  - 保留术语精度：`context window`、`token budget`、`memory compaction` 不必强行中文化
- **Notable anti-style for this piece：** 避免"智能体将重塑一切"类空泛判断；避免把 agent 简化为 chatbot

## 4. Possible Structure

> 建议的文章结构。这是探索性的，写作过程中可以调整和偏离。

1. Opening: 从一个具体的"agent 在长任务中丢失上下文"的踩坑场景切入
2. Context: 当前 agent 框架的上下文管理现状（单轮内解决方案的局限）
3. Core argument: 长任务上下文管理的四个维度——token budget、选择性遗忘、外部 memory、handoff 协议
4. Evidence / cases: 具体工程案例和设计取舍
5. Implications: 这对 agent 框架设计者和使用者的意义
6. Closing: 回到开头的场景，但带着解决方案的视角

视觉插入点：第 3 节核心论点处可配架构图；第 4 节案例处可配流程图。具体数量和位置随文章需要自由发挥。

## 5. Research & Fact-Check Notes

> 可选。如果文章需要查证事实，这里列出研究方向和已知考量。

- **Deep research 是否需要：** 需要。搜索 2026 年 agent 框架在 context management 和 long-task 方面的最新进展和讨论。
- **需要查证的问题：**
  - 主流 agent 框架在 long-task 上下文管理上的最新能力
  - 相关的 memory/compaction 技术方案
- **已知可信来源：** Anthropic 的 context window 文档、各 agent 框架的源码和设计文档
- **需要避免的无根据断言：** 不要声称某个框架"不支持"长任务，除非有确切证据。

## 6. Suggested Flow

> 建议的执行阶段。根据文章需要自由调整、跳过或重新排序。

1. **Deep research** —— 搜索 agent context management 最新进展
2. **Draft** —— 根据 possible structure 自由写作
3. **Visuals** —— 生成架构图和流程图
4. **Polish** —— 用 `polish-article` 打磨
5. **WeChat packaging** —— 用 `wechat-article-renderer` 排版
6. **Preview & review** —— 用户审核
7. **Publish** —— 用 `wechat-publish-workflow` 创建草稿
8. **Closeout** —— 用 `writing-task-closeout` 收尾

## 7. Open Questions

> plan 阶段还没想清楚、需要执行中探索的问题。执行 agent 可以在写作过程中寻找答案。

- 是否需要对比几个具体 agent 框架的实现？还是保持通用讨论？
- 四个维度的组织结构是平级对比还是递进关系？写 draft 时根据手感决定。
```
