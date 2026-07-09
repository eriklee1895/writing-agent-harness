# 技术图表插画风格（technical-diagram）

用于系统架构文章、SaaS 解释图、开发者文档、工作流教程和方法论文章。目标是清晰、层次结构和干净的结构。

本 preset 提供的是**脚手架而非模具**：它默认使用纯白背景和现代科技配色，但当用户 brief 已经带有强烈视觉概念时，只保留结构 guardrails。

我们按信息密度分成两个层级，避免把简单概述画成密集架构图，也避免把需要解释的 pipeline 画成几枚通用图标。

- **简单/ overview：** [`technical-diagram-simple`](#1-technical-diagram-simple) —— 干净的等距/扁平 overview，模块关系图，落地页头图。
- **详细/ architecture：** [`technical-diagram-architecture`](#2-technical-diagram-architecture) —— 带编号步骤、组件标签、数据流和图例的分层架构图。

## 结构模板（除非 brief 覆盖，否则保留）

| Guardrail | 默认 Prompt 关键词 |
|---|---|
| 媒介 | `clean isometric illustration`, `modern flat illustration`, `technical diagram`, `information design` |
| 背景 | `crisp white background`, `minimal or no texture`, `no dark vignette` |
| 构图 | `layered modules`, `left-to-right data flow`, `numbered steps`, `labeled components`, `legend row` |
| 硬约束 | `避免写实照片感`, `避免3D渲染感`, `避免深色背景`, `避免装饰性元素`, `避免大段正文` |

## 灵感默认（当 brief 自带风格/氛围/配色时可被覆盖）

| 维度 | 默认方向 |
|---|---|
| 色彩 | `现代科技配色`, `蓝和青色`, `柔和灰`, `深海军蓝点缀` |
| 风格 | `现代 SaaS 审美`, `干净信息图设计` |

> **覆盖规则：** 如果用户指定了不同的配色、渲染风格或氛围，就放弃灵感默认，只保留结构模板（纯白背景、分层/流程构图、硬约束）。

---

## 1. Technical diagram — simple

干净的高层级 overview。当你需要一张可读的小缩略图或头图，传达结构而不需要密集标签时使用。

**核心公式：**
```
Clean isometric illustration, [系统名称] overview diagram, [N] 个分层模块, color-coded blocks, arrows showing data flow, modern tech palette, white background, minimal or no text
```

**与 article-illustration 一起使用：**

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --style-profile flat-tech-infographic \
  --size doc-hd \
  --title "Microservices Overview" \
  --brief "Clean isometric illustration of a microservices architecture overview, 4 layers (client apps, API gateway, service layer, data layer), color-coded blocks in blue and teal, arrows showing request flow, modern tech palette, crisp white background, minimal bilingual labels" \
  --language zh-en \
  --output-dir output/article-illustration/technical-diagram
```

**最适合：** 产品 overview、模块关系图、落地页头图

---

## 2. Technical diagram — architecture

带明确步骤、组件标签和数据流注释的详细架构图。当文章需要解释*如何*工作而不只是*长什么样*时使用。

**核心公式：**
```
Detailed technical architecture diagram, [系统名称], [N] 个编号步骤或分层, labeled components, arrows showing data flow, legend row, modern flat or isometric style, white background
```

**与 article-illustration 一起使用：**

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --style-profile flat-tech-infographic \
  --size doc-2k \
  --title "RAG Architecture" \
  --brief "Detailed technical architecture diagram explaining Retrieval-Augmented Generation (RAG). 5 numbered steps left-to-right: 1 User Query, 2 Retrieve from Knowledge Base, 3 Augment Prompt, 4 LLM Generate, 5 Generated Answer. Each step shows a labeled component box with a simple icon. Arrows connect the steps. A bottom legend row explains each component. Clean modern flat style, crisp white background, blue and teal palette, concise bilingual labels" \
  --language zh-en \
  --output-dir output/article-illustration/technical-diagram
```

**最适合：** 架构深入解析、方法论解释、工作流教程、开发者文档

---

## 3. Clean process infographic

带图标和简洁标签的逐步时间线或流程图。适合需要展示有序步骤的场景。

**核心公式：**
```
Clean process infographic, [流程名称], [N] 个步骤从左到右, 每步配简单图标和短标签, modern flat style, white background
```

**与 article-illustration 一起使用：**

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --style-profile flat-tech-infographic \
  --size doc-hd \
  --title "Beer Brewing Process" \
  --brief "Clean process infographic explaining the beer brewing process, 5 steps left-to-right (Mashing, Boiling, Fermentation, Conditioning, Bottling), each step with a simple icon and a short bilingual label. Warm brown and amber palette, modern flat style, crisp white background, professional information design" \
  --language zh-en \
  --output-dir output/article-illustration/technical-diagram
```

**最适合：** 工作流教程、方法论解释、步骤指南

---

## 4. Blueprint / line-art schematic

白底上的青色或深色线条技术图。适合开发者文档、API 设计、CI/CD 图、工程博客。

**核心公式：**
```
Blueprint style technical schematic, [系统/工具] diagram, line-art layout, [cyan/dark] lines on white, clean engineering feel, minimal labels
```

**与 article-illustration 一起使用：**

```bash
uv run .agents/skills/article-illustration/scripts/generate_article_illustration.py \
  --style-profile soft-tech-diagram \
  --size doc-hd \
  --title "Kubernetes Blueprint" \
  --brief "Blueprint style technical schematic of a Kubernetes cluster, line-art layout showing Master nodes and Worker nodes with connecting lines, cyan lines on white background, clean engineering feel, minimal icons, no paragraphs of text, concise labels" \
  --language zh-en \
  --output-dir output/article-illustration/technical-diagram
```

**最适合：** 开发者文档、基础设施图、API 设计

---

## 通用技巧

1. **匹配密度与意图。** 简单 overview 用 `flat-tech-infographic` + `doc-hd`；需要解释 pipeline 的用 `flat-tech-infographic` + `doc-2k`。
2. **技术图优先 landscape。** `doc-hd`、`doc-2k`、`blog-banner` 都比 portrait 更适合。
3. **标签重要时用 `doc-2k` 或 `doc-4k`。** 小标签在更高分辨率下更清晰。
4. **保持标签简短。** 每个标签一两个词，长句在小尺寸下无法阅读。
5. **明确写 `white background` 和 `no dark vignette`。** 技术图容易默认出深色渐变背景。
6. **不要混用 3D 渲染和扁平图。** 选定一种视觉语言并保持一致。
7. **架构图要明确要求编号步骤、图例行和标签组件。** 否则模型容易把图退化成几个通用图标。
8. 当用户 brief 已自带配色或渲染风格时，放弃灵感默认，只保留结构 guardrails。
