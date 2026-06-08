---
name: polish-article
description: "润色和打磨文章写作。Use when the user asks to polish/精修/润色/压缩/扩写/restructure a blog post, essay, industry analysis, technical article, Agent/AI article, or Chinese/bilingual draft; improve logic, remove repetition, strengthen voice, raise professional depth, and adapt writing style to the genre while preserving the author's perspective."
---

# Polish Article

## Overview

这个 skill 用于把 draft 打磨成 publishable writing。它不只是去掉错别字或 AI 味，而是让文章匹配题材应有的气质：行业分析要像专业分析师，散文要有文学家的优雅和节制，互联网技术博客要有专业视野，Agent/AI 技术文章要体现对 agent systems 的深入理解。

`Markdown source` 是 canonical source。打磨时保留作者判断、语气、锋芒和知识密度；不要把文章抹平成中庸、柔软、无风险的通用稿。

如果 repo 根目录存在 `SOUL.md`，润色前必须先读取它，并按其中的作者声音契约对齐 register、审美边界和 anti-style。`SOUL.md` 优先约束作者气质；本 skill 负责执行具体编辑。

## 先判断文章类型

先识别文章应采用的 writing register：

- `industry-analysis`: 像专业分析师。重视 thesis、证据链、产业格局、因果关系、风险边界和时间点。
- `technical-blog`: 像有实战经验的技术作者。重视准确术语、工程取舍、上下文、可复用经验和读者认知路径。
- `agent-ai-essay`: 像理解 agent systems 的技术观察者。重视 workflow、tool use、context、evaluation、autonomy、failure modes，而不是泛泛谈 AI。
- `literary-essay`: 像优雅的文学作者。重视节奏、意象、留白、质感和克制，不要堆形容词。
- `personal-blog`: 像有个人判断的人。可以有第一人称、犹豫、锋芒和具体感受，但不能散。
- `wechat-longform`: 面向移动端长文阅读。段落短、节奏稳、标题路径清晰，方便后续交给 `wechat-article-renderer`。

如果用户没有指定类型，根据标题、内容和分发渠道自行判断；不确定时在回复里说明采用了哪种 register。

## 打磨目标

重点修这些问题：

- 逻辑不清：thesis 模糊、section order 错乱、因果跳跃、背景信息出现太晚。
- 重复信息：相同判断换说法重复出现，或者段落只是在延长语气。
- 语言太软：只有“可能、值得关注、具有意义”，缺少明确判断和专业力度。
- 语言太空：大词、套话、营销腔、AI 味转场、没有具体对象和动作。
- 专业不足：概念没定义，术语不准，判断没有证据边界，行业/技术视角不够。
- 文学不足：节奏单调，句子太说明书，缺少气息、质感和余味。

## Workflow

1. 通读全文，识别：
   - target reader；
   - article register；
   - core thesis；
   - section map；
   - strongest paragraphs；
   - weak/redundant/risky paragraphs。
2. 读取并应用 `SOUL.md`（如存在）：确认主 register、反风格规则和作者声音边界。
3. 检查信息依赖关系。文章内容应像 DAG：读者理解后文所需的概念、背景和判断，应该先出现。
4. 判断是否需要先确认结构：
   - 大幅改 section order、删除整节、改变 thesis 时，先给 short editorial plan。
   - 局部润色、收紧、错别字、表达增强时，直接编辑。
5. 按 register 打磨正文：
   - 每段只承担一个主要意思；
   - 移动端长文段落通常不超过约 240 Chinese chars；
   - 删除重复铺垫、空泛结论、AI 味套话；
   - 把软判断改成有边界的明确判断；
   - 保留具体日期、数字、机构名、产品名和原始引用边界；
   - 不编造事实、来源、引语、链接。
6. 结束前检查：
   - title / subtitle / opening 是否承接 thesis；
   - section headings 是否形成清晰阅读路径；
   - conclusion 是否收束，而不是机械 CTA；
   - Markdown links、images、frontmatter、tables 是否没被破坏；
   - 对 current events 或 high-uncertainty facts 是否标明需要查证。

## Register Guidance

### Industry Analysis

写得像专业分析师：少情绪，多判断；少口号，多结构。

- 明确判断：发生了什么、为什么重要、影响谁、下一步看什么。
- 区分 fact、inference、speculation。
- 使用时间、公司、产品、交易、生态位置等具体锚点。
- 避免“标志着时代到来”这类空泛宏大叙事，除非后面有充分论证。

### Technical Blog

写得像真正做过工程的人：准确、具体、有取舍。

- 保留术语精度：`runtime`、`toolchain`、`agent`、`context window`、`evaluation` 等不必强行中文化。
- 多写 trade-off、failure mode、workflow impact。
- 少写“提升效率、降低成本”这种泛化收益，改成具体场景和机制。

### Agent / AI Writing

写 Agent 文章时，要体现对 agent 的深入理解，而不是把 agent 当成 chatbot 的新名字。

- 关注 task decomposition、tool use、memory、context management、verification、handoff、autonomy boundary。
- 讨论 agent 能力时，同时写清 evaluation 和 failure modes。
- 避免泛泛使用“智能体将重塑一切”。让判断落到具体 workflow 和组织变化上。

### Literary Essay

写散文时，重点不是显得“华丽”，而是有气息。

- 句子长短要有呼吸。
- 意象要少而准，不堆叠。
- 留白比解释更有力量。
- 避免 AI 式漂亮句：看似金句，实际没有生活经验。

## Anti-Slop Rules

这个 skill 已吸收独立“去 AI 味”工具的核心目标：去掉 AI 写作痕迹，但目标更高，不只是“像人”，而是“像有判断、有功底、有专业经验的人”。

重点删除或改写：

- “值得注意的是 / 更重要的是 / 不可忽视的是”这类空泛转场；
- “不仅仅是……而是……”的公式句；
- 三段式堆砌；
- 模糊归因：“行业人士认为”“有观点指出”；
- 广告腔：“重塑格局”“赋能生态”“开启新篇章”；
- 没有证据的宏大结尾：“未来已来”“让我们拭目以待”。

## Fact Boundaries

润色不是 research。遇到以下内容，不要凭记忆修事实：

- current events；
- company/product facts；
- pricing；
- laws/regulations；
- fast-moving AI / developer tooling news；
- quoted statements。

如果事实可能变动，先标记需要查证；如果本轮任务包含事实更新，则先 research 后 polish。

## 与其他 skills 的边界

- 需要微信公众号排版：打磨完成后交给 `wechat-article-renderer`。
- 需要微信公众号草稿/发布：交给 `wechat-publish-workflow`。
- 需要生成封面或插图：优先用系统 `$imagegen`。

## Output Rules

如果用户给的是文件路径并要求直接处理，优先在原 Markdown 上做 scoped edit；重大改动前先备份或说明编辑范围。

如果用户只是让你“看看/评估”，先给 editorial findings：结构问题、内容问题、事实风险、可删减位置和建议动作。不要在没有必要时贴整篇重写稿。
