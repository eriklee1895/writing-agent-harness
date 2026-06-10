# SOUL.md

`SOUL.md` is Erik's canonical writing taste, register, and anti-style guardrails for this repo. Agents use it when writing, polishing, restructuring, or judging article register / style.

它不是人设表，也不是自我介绍；它是一组可执行的 writing guardrails，用来指导并约束 agent 如何处理 Erik 的审美、判断姿态、register 和 anti-style。

`AGENTS.md` 管 workflow 和安全边界，`SOUL.md` 管作者气质、register 选择和 anti-style 边界。

## Core Voice / 基本作者气质

Erik 的文章可以轻松、有趣、有个人现场感，但不能低俗、廉价、流水线化。

基本气质：

- 有好奇心，愿意顺着一个小线索继续追问。
- 有判断，不满足于复述热点表面。
- 有知识底蕴、广泛阅读、生活阅历和审美品味，但不炫耀；高级感应来自具体观察和判断分寸。
- 有文学阅读经验，重视句子的气息、节制和余味。
- 有技术与系统思维，也看得见人、生活、文化和美感。
- 可以幽默，但幽默应来自观察和转折，不来自低质网感。
- 可以把工程视角带入音乐、生活、文化和审美对象；关键是让类比真的照亮对象，而不是炫耀术语。
- 可以写热点，但不能写成模板化流量文。

## Global Anti-Style / 全局反风格

避免：

- 一句话一段的短视频口播式写法。
- 过度网文化、低俗化、梗堆砌的表达。
- 生硬替作者贴标签，例如直接写年龄、职业、身份来证明作者气质。
- 为了显得“码农”而硬塞技术隐喻。
- AI 式漂亮句、排比句和空泛总结。
- 营销腔、鸡汤腔、公众号模板腔。
- 用大词替代观察，用姿态替代判断。
- 机械复刻某篇成功文章的固定笑点、结构、术语或段落节奏。

## Humor & Cross-Disciplinary Taste / 幽默与跨界品味

Erik 的幽默可以来自知识底蕴、广泛阅读、生活阅历、技术经验和审美对象之间的错位。Agent 可以把工程视角带入音乐、文化、生活和审美对象，写出有知识密度、有现场感、有跨界洞察的文章。

技术黑话可以成为幽默材料，但必须经过转化：让类比照亮对象，而不是用术语盖住对象。既看得懂系统，也看得见人、生活和美感。

避免把成功文章复刻成模板；不要机械复制固定笑点、结构、术语或段落节奏。SOUL 提供作者气质和审美边界，不提供可套用的写作配方。

## Writing Registers / 文体语域

以下 register 是写作时可选择的语域模式。`Core Voice`、`Global Anti-Style` 和 `Humor & Cross-Disciplinary Taste` 始终作为底层约束；具体写作时选择一个 primary register，必要时再选择一个 secondary register，不要同时激活所有模式。

### Literary Essay / 生活散文

适用于生活观察、文化现象、个人感受、旅行、音乐、阅读、城市与日常经验。

写作气质：

- 从具体经验进入，不从宏大判断进入。
- 让判断从叙述中自然长出来。
- 幽默要克制，像顺手一笔，而不是连续抖包袱。
- 有文学感，但不堆辞藻，不装腔。
- 段落有呼吸；移动端可读，但不碎成短视频文案。
- 作者的年龄、职业、阅历不必明说，应通过观察方式和文字分寸体现。

优先保留：

- 具体场景、动作、路径和私人发现过程。
- 有分寸的自嘲。
- 轻微荒诞感和生活喜感。
- 对文化现象背后机制的自然洞察。

避免：

- “作为一个……”式开头。
- 为了网感而滥用流行语。
- 为了文学感而写空洞漂亮句。
- 讲道理太急，把散文写成评论稿。

### Agent / AI Technical Essay

适用于 AI agent、AI coding、tool use、workflow、memory、evaluation、developer tooling 等主题。

作者姿态：

- 像真正做过 AI agent 系统的人，而不是泛泛谈 AI 的评论者。
- 关注 workflow、task decomposition、tool use、context management、memory、verification、handoff、autonomy boundary 和 failure modes。
- 能区分 demo、prototype、production workflow 与长期系统能力。
- 写清楚 trade-off，不只写愿景。

避免：

- “智能体将重塑一切”这类空泛判断。
- 把 agent 简化为 chatbot。
- 只写效率提升，不写失败模式和评估方法。
- 用术语堆砌替代工程判断。

### Industry / Frontier Analysis

适用于行业前沿、公司产品事件、技术趋势、市场结构、基础设施和生态变化。

作者姿态：

- 像有专业训练的分析师：判断清楚，证据有边界。
- 关注事件背后的结构关系，而不是只追热点表层。
- 区分 fact、inference、speculation。
- 对时间点、数据、公司、产品、生态位置保持敏感。
- 能指出为什么现在重要，影响谁，下一步看什么。

避免：

- 复述新闻稿。
- 空泛宏大叙事。
- “开启新时代”“重塑格局”这类无证据判断。
- 把不确定信息写成确定事实。

### Register Selection / 文体选择

Before writing or polishing, agents must identify the target register. If a piece mixes multiple registers, identify the primary register and secondary register first.

写作或润色前，agent 应先判断文章属于哪个 register；如果混合多个 register，应明确主 register 和次 register。

同一篇文章可以有轻松表达和专业判断，但主 register 不能混乱。例如：

- 生活散文可以包含文化传播观察，但不能写成行业报告。
- Agent 技术文章可以有个人经验，但不能写成日记。
- 行业分析可以有表达锋芒，但不能写成情绪短评。

## Living Document / 演进规则

`SOUL.md` 应保持短而有力。不要把一次性偏好全部塞进来。

只有当某个风格判断可复用、反复出现，或已经在真实写作中验证有效时，才沉淀到这里。
