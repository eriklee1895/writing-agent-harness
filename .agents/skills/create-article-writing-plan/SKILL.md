---
name: create-article-writing-plan
description: "将 writing brief 转化为可执行的写作计划。Use after article-ideation when the user confirms the direction and is ready to plan execution — especially for articles involving research, visuals, or multiple phases. Also use when the user says 写个计划/定个方案/怎么执行/下一步先做什么."
---

# Create Article Writing Plan

## Overview

把 `article-ideation` 确认的 writing brief 和写作方向，转化为一份轻量的、开放性的写作执行计划，落盘到 `content/drafts/YYYY-MM-DD-<slug>/writing-plan.md`。

**核心原则：约束意图，不约束做法。保存决策，不拆分步骤。给 agent 目标，不给算法。**

写作不同于 coding——创造性是核心资产。这份 plan 的作用是防止 context lost、沉淀决策和偏好，而不是把 agent 变成流水线工人。

## When To Use

Use this skill when:

- `article-ideation` 已经产出 writing brief，用户确认了基本方向，准备开始写作。
- 用户暗示或明确表示担心 context 丢失，或任务涉及多步骤（research + draft + visuals + polish）。
- 用户说"先做个计划""定个方案""下一步怎么执行"。

Skip this skill when:

- 任务很轻量（一篇简短博客、一次直接写完的短文），且用户说"直接开始写"。
- 用户已经在 writing brief 之外不需要额外上下文。

## Input

在执行前，先确认这些信息可用：

- `writing-brief.md`（来自 `article-ideation`，应该在 `content/drafts/YYYY-MM-DD-<slug>/writing-brief.md`）
- `SOUL.md`（repo 根目录，用于确认 register 和作者气质）

**如果 brief 还没有落盘：** 先用 `article-ideation` 的 Writing Brief 模板保存 brief 到 `content/drafts/YYYY-MM-DD-<slug>/writing-brief.md`，再继续生成 plan。不要在没有 brief 的情况下生成 plan。

## Workflow

### 1. Confirm Scope

从 writing brief 中确认：

- 这篇文章的目标格式（Markdown 报告 / HTML DeepResearch / 微信公众号 / 博客 / 散文）？
- 用户是否表达过格式/呈现标准/图表偏好？
- 是否需要 research、visuals、多渠道发布？

如果用户只想快速开始、明确说不需要 plan，尊重用户的意愿，不要强行生成。

### 2. Draft The Plan

基于 brief 和与用户的讨论，生成 `writing-plan.md`。以下是推荐结构——每一节都是**提示性的、可选的**，根据文章需要调整或省略。

```markdown
---
working_title: "..."
slug: "..."
brief_source: "./writing-brief.md"
created: YYYY-MM-DD
title_status: working
primary_register: "..."
---

# Writing Plan: <working title>

## 1. What We Think We Know

> 从 brief 提炼的核心决策。这些是 plan 阶段的假设，执行过程中可以修正。

**Central question:** ...

**Thesis:** ...

**Target reader:** ...

**Angle:** ...

**Why now:** ...

**Anti-goals:** ...

## 2. Output Guidelines

> 目标格式和呈现偏好。以下是**偏好**，不是硬性规格。

- **Format:** Markdown 技术报告 / HTML DeepResearch / 微信公众号 / 博客 / 散文 / 其他
- **Target length:** 大致预期（如 ~4000 字）
- **Media:** 配图/图表/视频的偏好（如不需要则标注"不需要图表"）

**Format-specific preferences:**

| 格式 | 图表/视觉建议 |
|------|-------------|
| HTML DeepResearch 报告 | 单页静态 HTML，富文本排版。可选用 GSAP 动画、CSS 动画、SVG 插图、数据表格（可用 JS 图表库）、`article-illustration` 配图，让报告可视化不 boring。 |
| Markdown 技术报告 | 技术概念用 Mermaid 图表辅助理解；复杂流程/架构用 SVG；封面和关键插图用 `article-illustration`。 |
| 微信公众号 | 交 `wechat-article-renderer` 排版。正文插图用 `article-illustration`。 |
| 生活散文 | 按文章气质随性配图，数量不拘。 |

## 3. Voice & Register Notes

> 来自 SOUL.md 的简要提示，帮助执行 agent 快速对齐作者气质。**不要重复 SOUL.md 全文。**

- **Primary register:** 从 SOUL.md 的 Writing Registers 中选择（如 `Agent / AI Technical Essay`、`Literary Essay`、`Industry / Frontier Analysis`）
- **Key voice notes：** 从 SOUL.md 挑出与本文最相关的 2-3 条，优先选：
  - 与该 register 直接对应的作者姿态描述（如"像真正做过 AI agent 系统的人"）
  - 与该题材最相关的 anti-style（如技术文章避免"智能体将重塑一切"）
  - 不影响其他体裁的全局约束（如"避免 AI 式漂亮句"）
- **Notable anti-style for this piece：** 本篇尤其需要避免的 1-2 条写法

## 4. Possible Structure

> 建议的文章结构。这是探索性的，写作过程中可以调整和偏离。

1. Opening: ...
2. Context: ...
3. Core argument: ...
4. Evidence / cases: ...
5. Implications: ...
6. Closing: ...

如果需要视觉插入点或阅读节奏提示，在这里标注。

## 5. Research & Fact-Check Notes

> 可选。如果文章需要查证事实，这里列出研究方向和已知考量。

- **Deep research 是否需要：** 根据主题判断——current events、技术细节、公司/产品事实通常需要；个人经验/散文通常不需要。如果需要，标注"需要先做广泛 deep research"。
- **需要查证的问题：** ...
- **已知可信来源：** ...
- **需要避免的无根据断言：** ...

## 6. Suggested Flow

> 建议的执行阶段。根据文章需要自由调整、跳过或重新排序。

1. **Deep research**（如需要）—— 广泛搜索、查证事实、收集来源
2. **Draft** —— 根据可能的结构和 brief 自由写作
3. **Visuals**（如需要）—— 生成封面、插图、图表
4. **Polish** —— 用 `polish-article` 打磨
5. **Channel packaging** —— 根据 distribution 渠道派生版本
6. **Preview & review** —— 用户审核预览
7. **Publish** —— 发布或创建草稿
8. **Closeout** —— 用 `writing-task-closeout` 收尾

## 7. Open Questions

> plan 阶段还没想清楚、需要执行中探索的问题。执行 agent 可以在写作过程中寻找答案。

- ...
```

### 3. Save The Plan

保存到：

```
content/drafts/YYYY-MM-DD-<slug>/writing-plan.md
```

用 frontmatter 中的 `brief_source: "./writing-brief.md"` 指回同目录的 brief。

### 4. Confirm With User

展示 plan **摘要**，不要贴全文。摘要只包含：

```text
Plan 已保存。核心要点：
- 格式：...
- Register：...
- 研究需求：是否需要 deep research
- 建议执行顺序：...
- Open questions：...

如果方向 OK，下一步可以从 deep research（如果需要）或 draft 开始。
```

如果用户对某个 section 有异议，修改后再确认。

## Example

完整示例见 `references/example-plan.md`。首次使用时建议先读取这个示例，理解每个 section 填充后的深度和语气。示例是一篇 Agent/AI 技术文章的 writing-plan.md，展示了所有 7 个 section 应该如何填写。

## Output Rules

- Plan 是**轻量文档**，不是合同。所有内容都是"建议"和"偏好"。
- 不要拆分成过于具体的小步骤；写作不是 sprint 任务。
- 不要使用"必须""不得""应该""required""must""shall"等强制性语言。用"建议""可选""偏好"。
- 保留 agent 创造空间：plan 写方向，不写具体做法。
- 如果用户明确表示不需要某些 section（如 Research 或 Visuals），省略它们。
- 如果文章是即兴的、随性的、个人随笔，plan 可以更短更自由，不必填满所有 section。
- `Output Guidelines` 中的 format-specific preferences 只写与本文相关的格式行，不相关的可以删除。

## Handoff

- 需要执行 plan：agent 读取 `writing-plan.md`，根据 phase 自行推进。
- 需要查证资料：直接进入 research。
- 需要写初稿：参考 plan 中的 structure 和 voice notes，但不要被锁死。
- 需要润色：交给 `polish-article`。
- 需要微信公众号排版：交给 `wechat-article-renderer`。
- 任务收尾：交给 `writing-task-closeout`。
