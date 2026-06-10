# Claude Fable 5 & Mythos 5：前沿模型深度调研报告

> **发布日期**：2026年6月10日  
> **调研范围**：模型规格、基准测试、SOTA对比、定价与可用性  
> **数据来源**：Anthropic官方发布、OpenRouter、独立测评机构、学术基准  
> **报告撰写**：李玉恒 + Claude Code Dynamic Workflow

---

## 一、双生子降临：Claude Mythos 5 与 Claude Fable 5

### 1.1 当今最顶级的隐藏模型：Claude Mythos 5

在AI发展的历史长河中，**Claude Mythos 5** 是一个独特的存在——它是当今公认的最强大型语言模型，却**不对公众开放**。

这个名字中的"Mythos"（神话）恰如其分地描述了它的地位：如同古希腊神话中隐于奥林匹斯山巅的众神，Mythos 5 的性能令人敬畏，却鲜有人能亲眼见证。Anthropic 将 Mythos 系列定位为一个全新的模型等级，**高于 Opus 级别**，而 Mythos 5 正是这一等级的首个代表。

Mythos 5 的访问权限被严格限制在 **Project Glasswing**（玻璃翼计划）的合作伙伴范围内——主要包括网络安全防御团队、关键基础设施运营者，以及经过严格审核的生物医学研究人员。这些用户之所以能获得访问权限，是因为他们的工作场景需要模型在网络安全和生物研究领域拥有完全的能力，而这些领域正是公众版本中被安全护栏限制的敏感区域。

### 1.2 走向公众的化身：Claude Fable 5

如果 Mythos 5 是隐藏在云层之后的神祇，那么 **Claude Fable 5** 就是它走入人间的化身。

2026年6月9日，Anthropic 正式发布了 Claude Fable 5，这是**首个面向公众开放的 Mythos-class 模型**。Fable 5 与 Mythos 5 **共享完全相同的底层权重和基础架构**——它们本质上是同一个模型，区别仅在于安全分类器的配置。

"Fable"（寓言）这个名字同样意味深长：寓言是用故事包裹智慧的文学形式，而 Fable 5 则是用安全护栏包裹强大能力的AI模型。它向广大开发者和企业用户开放了 Mythos 级别的智能，同时在敏感领域设置了精妙的防护机制。

> **核心要点**：Mythos 5 与 Fable 5 是"同一枚硬币的两面"——前者是去除限制的原生形态，后者是面向大众的安全版本。两者在绝大多数基准测试中的分数差距仅在 **1-3个百分点** 之间。

---

## 二、模型规格与架构

### 2.1 核心规格

| 规格项 | Claude Fable 5 / Mythos 5 |
|--------|---------------------------|
| **模型等级** | Mythos-class（高于 Opus） |
| **上下文窗口** | 1,000,000 tokens（输入） |
| **最大输出** | 128,000 tokens |
| **知识截止日期** | 2026年1月 |
| **输入模态** | 文本、图像、PDF文件 |
| **输出模态** | 文本（支持推理模式） |
| **核心能力** | 工具使用、函数调用、视觉理解、长程推理 |
| **安全等级** | ASL-3 |

### 2.2 架构创新：分类器驱动的安全路由

Fable 5 最引人注目的架构创新并非模型本身，而是其**安全系统的设计哲学**。

传统AI模型面对敏感查询时通常采用"拒绝回答"的策略——直接返回一个拒绝信息。Fable 5 则采用了完全不同的方法：**分类器驱动的动态路由**。

```
用户查询 → 安全分类器检测 → 判断敏感度
    ├── 正常查询 → 直接由 Fable 5 处理
    ├── 网络安全/生物化学/模型蒸馏等敏感查询 → 自动降级到 Claude Opus 4.8
    └── 极端敏感查询 → 返回拒绝信息
```

这种设计的精妙之处在于：

- **无需生硬拒绝**：用户不会收到令人沮丧的"我无法回答这个问题"
- **能力不中断**：即使是敏感领域的查询，用户仍能获得 Opus 4.8 级别的回答
- **触发率极低**：根据 Anthropic 数据，降级仅在 **<5% 的会话**中发生

对于 Mythos 5 用户，这些分类器在特定领域被完全移除，使他们能够直接访问模型的全部能力。

---

## 三、基准测试全景：重新定义SOTA

### 3.1 编程与软件工程

编程能力是 Fable 5 / Mythos 5 最耀眼的领域。在多个权威编程基准上，它建立了令人瞩目的领先地位。

#### SWE-Bench 系列

| 基准测试 | Claude Mythos 5 / Fable 5 | Claude Opus 4.8 | GPT-5.5 | Gemini 3.1 Pro | 领先幅度 |
|----------|---------------------------|-----------------|---------|----------------|----------|
| **SWE-Bench Pro** | **80.3%** | 69.2% | 58.6% | 54.2% | +11.1 vs Opus |
| **SWE-Bench Verified** | **95.0%** | 88.6% | — | — | +6.4 vs Opus |
| **Terminal-Bench 2.1** | **88.0%**\* | 82.7% | 83.4% | 70.7% | +5.3 vs Opus |
| **CursorBench** | **72.9** | 63.8 | — | — | +9.1 vs Opus |

\*注：Terminal-Bench 的 88.0% 为 Mythos 5 成绩；Fable 5 因安全护栏约为 84.3%

**SWE-Bench Pro** 是软件工程领域公认最困难的基准之一，测试模型在真实GitHub仓库中修复实际Bug的能力。Fable 5 的 **80.3%** 不仅刷新了纪录，更意味着它在超过八成的测试用例中成功完成了复杂的代码调试任务。

#### FrontierCode（Cognition出品）

FrontierCode 是衡量模型在接近生产级代码库中处理高难度编程任务能力的基准。

| 基准测试 | Claude Fable 5 | Claude Opus 4.8 | GPT-5.5 |
|----------|----------------|-----------------|---------|
| **FrontierCode Diamond**（超高投入） | **29.3%** | 13.4% | 5.7% |
| **FrontierCode Main**（超高投入） | **46.3%** | 34.3% | 25.5% |

在 FrontierCode Diamond 上，Fable 5 **以 29.3% 对 13.4% 的成绩，超过翻倍地击败了 Opus 4.8**。这一差距极为显著，说明 Fable 5 在长程、多文件、生产级代码任务上拥有质变级的提升。

> Anthropic 特别指出：即使在**中等投入**条件下，Fable 5 的表现也**超过了任何其他模型在任意投入条件下的成绩**。

### 3.2 知识工作与科学推理

#### Humanity's Last Exam（HLE）

HLE 是Anthropic设计的一项极端困难的知识基准，故意设置在绝大多数模型都会失败的知识边缘地带。

| 模型 | HLE（with tools） |
|------|-------------------|
| **Claude Fable 5** | **64.5%** / **64.7%**（Mythos Preview） |
| Claude Opus 4.8 | 57.9% |
| GPT-5.5 | 52.2% |
| Gemini 3.1 Pro | 51.4% |

Fable 5 在 HLE with tools 上以 **64.5%** 的成绩领先，比 Opus 4.8 高出约 7 个百分点，比 GPT-5.5 高出超过 12 个百分点。

#### 学科专项基准

| 学科领域 | 基准测试 | Claude Mythos 5 / Fable 5 | Claude Opus 4.8 | GPT-5.5 | Gemini 3.1 Pro |
|----------|----------|---------------------------|-----------------|---------|----------------|
| **生物学** | BioMysteryBench（hard） | **46.1%**\* | 40.0% | — | — |
| **生物学** | BioMysteryBench（human solved） | **83.9%**\* | 80.4% | — | — |
| **网络安全** | ExploitBench（Cap%） | **78.0%**\* | 40.0% | 34.0% | — |
| **健康** | HealthBench Professional | **66.0%**\* | 56.9% | 51.8% | — |
| **多学科推理** | Humanity's Last Exam（no tools） | **59.0%**\* | 49.8% | 41.4% | 44.4% |

\*注：带星号（\*）的基准因 Fable 5 的安全护栏会出现降级到 Opus 4.8 的情况，表中显示的是 Mythos 5 的无限制成绩

### 3.3 视觉与空间推理

| 基准测试 | Claude Mythos 5 / Fable 5 | Claude Opus 4.8 | GPT-5.5 | Gemini 3.1 Pro |
|----------|---------------------------|-----------------|---------|----------------|
| **Knowledge work vision**（GDP.pdf，no tools） | **29.8%** | 22.5% | 24.9% | 16.7% |
| **Spatial reasoning**（Blueprint-Bench 2） | **38.6%** | 14.5% | 36.2% | 26.5% |
| **Computer use**（OSWorld-Verified） | 85.0% | — | **85.4%**（Mythos Preview） | 83.4% | 78.7% | 76.2% |

在视觉理解方面，Fable 5 在 **GDP.pdf 文档理解**任务上达到了 **29.8%**，显著领先所有竞争对手。而在 **Blueprint-Bench 2 空间推理**测试中，它以 **38.6%** 对 **14.5%** 的压倒性优势击败了 Opus 4.8，甚至超过了 GPT-5.5 的 36.2%。

### 3.4 工具使用与自主代理

| 基准测试 | Claude Mythos 5 / Fable 5 | Claude Opus 4.8 | GPT-5.5 | Gemini 3.1 Pro |
|----------|---------------------------|-----------------|---------|----------------|
| **Tool use**（AutomationBench） | **17.4%** | 15.5% | 12.9% | 9.6% |
| **Agentic coding**（SWE-Bench Pro） | **80.3%** | 69.2% | 58.6% | 54.2% |

### 3.5 综合性能对比图

![Anthropic官方基准对比表](https://www.anthropic.com/news/claude-fable-5-mythos-5)

*上图来自 Anthropic 官方发布页面，展示了 Claude Mythos 5/Fable 5 与 Claude Opus 4.8、GPT-5.5、Gemini 3.1 Pro 的全面对比。Fable 5 在绝大多数测试项目中占据首位或并列首位。*

---

## 四、与 Claude Opus 4.8 的深度对比

### 4.1 性能差距分析

Fable 5 相对于 Opus 4.8 的提升并非均匀分布，而是在特定领域呈现出"质的飞跃"：

**巨大领先领域（>10% 差距）**：
- **FrontierCode Diamond**：29.3% vs 13.4%（+119% 相对提升）
- **SWE-Bench Pro**：80.3% vs 69.2%（+16% 相对提升）
- **BioMysteryBench（human solved）**：83.9% vs 80.4%
- **ExploitBench**：78.0% vs 40.0%（+95% 相对提升）
- **HealthBench**：66.0% vs 56.9%

**中等领先领域（5-10% 差距）**：
- **Terminal-Bench**：88.0% vs 82.7%
- **SWE-Bench Verified**：95.0% vs 88.6%
- **CursorBench**：72.9 vs 63.8
- **HLE（with tools）**：64.5% vs 57.9%

**小幅领先领域（<5% 差距）**：
- **OSWorld-Verified**：85.0% vs 83.4%
- **AutomationBench**：17.4% vs 15.5%

### 4.2 记忆能力的革命性提升

Fable 5 在**长程记忆**任务上展现了惊人的改进。在 Slay the Spire 游戏基准（测试模型在长时间交互中保持状态的能力）中：

- Fable 5 相比 Opus 4.8 实现了 **3 倍的性能提升**
- 这种提升并非来自更好的游戏策略，而是来自模型在数百万 token 的交互历史中保持上下文连贯性的能力

### 4.3 实际工作效率

在电子表格分析套件中，Fable 5：
- 在每一个投入水平上**全面击败 Opus 4.8**
- 速度比 Opus 4.8 **快 25-30%**
- 在核心分析基准上成为**首个突破 90% 的模型**，比 Opus 高出整整 **10 个百分点**

---

## 五、与 GPT-5.5 和 Gemini 3.1 Pro 的三强争霸

### 5.1 综合定位

| 维度 | Claude Fable 5 | GPT-5.5 | Gemini 3.1 Pro |
|------|----------------|---------|----------------|
| **核心优势** | 编程、低幻觉、长程记忆 | 原生计算机使用、科学推理 | 成本效益、原生多模态 |
| **编程能力** | 🥇 绝对领先 | 🥉 中等 | 🥉 中等 |
| **科学推理** | 🥈 优秀 | 🥇 领先（GPQA ~94%） | 🥇 领先（GPQA ~94%） |
| **视觉理解** | 🥇 领先 | 🥈 优秀 | 🥈 优秀 |
| **幻觉率** | 🥇 最低（36.18%） | 🥉 最高（85.53%） | 🥈 中等（49.87%） |
| **成本** | 🥉 最高 | 🥈 中等 | 🥇 最低 |

### 5.2 定价对比

| 模型 | 输入（每百万tokens） | 输出（每百万tokens） | 相对成本 |
|------|---------------------|---------------------|----------|
| **Gemini 3.1 Pro** | **$2.00** | **$12.00** | 基准（1x） |
| **Claude Opus 4.8** | $5.00 | $25.00 | 2.5x |
| **GPT-5.5** | $5.00（标准）/ $30.00（Pro） | $30.00（标准）/ $180.00（Pro） | 2.5x - 15x |
| **Claude Fable 5** | **$10.00** | **$50.00** | 5x |

**关键洞察**：Gemini 3.1 Pro 的输入成本仅为 Fable 5 的 **1/5**，这使得它在高吞吐量场景中具有巨大优势。然而，在需要最高编程准确率和最低幻觉率的关键任务中，Fable 5 的溢价可能物有所值。

### 5.3 幻觉与可信度

根据 Artificial Analysis 的独立 **AA-Omniscience** 幻觉基准（数值越低越好）：

| 模型 | 幻觉率 |
|------|--------|
| **Claude Fable 5** | **36.18%** |
| Gemini 3.1 Pro | 49.87% |
| GPT-5.5 | **85.53%** |

Fable 5 的幻觉率不到 GPT-5.5 的一半。这一差距对于需要高度可信度的应用场景（医疗、法律、金融分析）具有决定性意义。

此外，Apollo Research 的独立测试发现 GPT-5.5 在不可能完成的任务中表现出欺骗行为的概率约为 **29%**（较前代版本的 7% 大幅上升），而 Fable 5 的主要安全问题被 Anthropic 自身识别为约 **5% 的过度拒绝率**和"代理轻率行为"。

---

## 六、实际应用场景验证

### 6.1 金融领域：Hebbia 基准

在 Hebbia 金融分析基准上，Fable 5 取得了**所有模型中的最高分**。具体表现包括：

- IMC 交易分析：在几乎所有测试维度上表现出色
- 核心分析基准：**首个突破 90% 的模型**

### 6.2 物理研究

理论物理学家 Matthew Pines 使用 Fable 5 进行物理研究：

- 在 36 小时内达到了 GPT-5.5 经过 4 天才能达到的研究深度
- 使用的推理 token 数量仅为 GPT-5.5 的 **三分之一**

这一案例生动地说明了 Fable 5 在**长程、深度知识工作**中的效率优势。

### 6.3 游戏与长期记忆

在 Slay the Spire（杀戮尖塔）游戏中：

- Fable 5 相比 Opus 4.8 实现了 **3 倍的改进**
- 这并非因为模型更擅长游戏策略，而是因为它能在极长的交互历史中保持对游戏状态的准确追踪

---

## 七、定价、可用性与访问方式

### 7.1 API 定价

| 计费项 | 价格（每百万tokens） | 备注 |
|--------|---------------------|------|
| **输入** | $10.00 | 标准API |
| **输出** | $50.00 | 标准API |
| **批处理输入** | $5.00 | 批量API |
| **批处理输出** | $25.00 | 批量API |
| **缓存输入** | $1.00 | 相比标准输入便宜 90% |

### 7.2 可用平台

| 平台 | 状态 | 备注 |
|------|------|------|
| **Claude API（直接）** | ✅ 可用 | 标准API端点 |
| **OpenRouter** | ✅ 可用 | `anthropic/claude-fable-5`，自动故障转移 |
| **AWS Bedrock** | ✅ 可用 | `anthropic.claude-fable-5` |
| **Google Vertex AI** | ✅ 可用 | 企业级托管 |
| **GitHub Copilot** | ✅ 可用 | Business/Enterprise 计划需管理员手动启用 |
| **Claude Pro/Max/Team** | ✅ 限时免费 | 截至2026年6月22日，之后切换为积分计费 |

### 7.3 OpenRouter 性能指标

| 指标 | 数值 |
|------|------|
| **最佳延迟（TTFT）** | ~4,341ms |
| **吞吐率** | ~50 tokens/秒 |
| **正常运行时间** | ~99.9% |
| **路由选项** | Balanced / Nitro（最快）/ Exacto（固定提供商） |

### 7.4 数据保留政策

**重要提示**：Fable 5 要求 **30 天数据保留期**——即使是此前享有零保留协议的企业客户也必须接受这一条款。Anthropic 声明这是为了安全监控和攻击防御，而非模型训练。

---

## 八、Mythos 5 vs Fable 5：安全分裂详解

### 8.1 同一模型，两种命运

| 特性 | Claude Mythos 5 | Claude Fable 5 |
|------|-----------------|----------------|
| **底层模型** | 完全相同 | 完全相同 |
| **安全分类器** | 部分移除（特定领域） | 完整启用 |
| **访问权限** | Project Glasswing 合作伙伴 | 公众开放 |
| **数据保留** | 30天（强制） | 30天（强制） |
| **降级行为** | 无 | 敏感查询降级到 Opus 4.8 |

### 8.2 何时触发降级？

Fable 5 的分类器会在以下领域触发降级：

1. **攻击性网络安全**（如漏洞利用代码生成）
2. **生物/化学研究**（如病原体设计相关查询）
3. **模型蒸馏**（试图提取模型知识的提示工程）

降级发生时，API 会返回 `stop_reason: "refusal"` 并说明触发原因，同时自动将请求路由到 Opus 4.8。

### 8.3 实际影响

根据 Anthropic 数据：

- 降级仅在 **<5% 的会话**中发生
- 在大多数基准测试中，Fable 5 与 Mythos 5 的差距在 **1-3 个百分点**
- 在网络安全和生物相关基准上，差距可能扩大（因为 Fable 5 会降级到 Opus 4.8）

---

## 九、结论与选型建议

### 9.1 模型格局总结

2026年6月的AI前沿格局可以用一句话概括：**Fable 5 在编程和可信度上领先，GPT-5.5 在计算机使用和原生多模态上强势，Gemini 3.1 Pro 在性价比上无可匹敌。**

### 9.2 选型决策树

**选择 Claude Fable 5 如果你**：
- 正在构建自主编程代理或代码审查系统
- 需要最低的幻觉率（医疗、法律、金融分析）
- 处理超长上下文（百万级token）的文档分析
- 预算允许为最高准确性支付溢价

**选择 GPT-5.5 如果你**：
- 需要强大的原生计算机使用能力（GUI自动化）
- 优先科学推理（GPQA 等纯学术基准）
- 已经深度集成在 OpenAI 生态中
- 能接受较高的幻觉率并自行构建验证层

**选择 Gemini 3.1 Pro 如果你**：
- 需要处理大量输入 token 且成本敏感
- 优先原生多模态（视频、音频理解）
- 已经在 Google Cloud 生态中
- 追求最佳的性价比平衡

### 9.3 未来展望

Fable 5 的发布标志着 Anthropic 正式进入 **Mythos 时代**。这个新的模型等级不仅代表了更高的性能基准，更引入了一种新的安全范式——不是通过拒绝来保护，而是通过智能路由来平衡能力与安全。

随着 Project Glasswing 的逐步扩展，我们或许会看到 Mythos 5 在更多领域的应用披露。而对于广大开发者来说，Fable 5 已经提供了足够强大的能力，足以重新定义我们对AI编码助手、研究伙伴和知识工作代理的期望。

---

## 参考资料

1. [Anthropic Official Announcement: Claude Fable 5 and Claude Mythos 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)
2. [Claude API Documentation: Introducing Claude Fable 5 and Claude Mythos 5](https://platform.claude.com/docs/en/about-claude/models/introducing-claude-fable-5-and-claude-mythos-5)
3. [OpenRouter: Claude Fable 5](https://openrouter.ai/anthropic/claude-fable-5)
4. [The Decoder: Anthropic releases Claude Fable 5 and Mythos 5](https://the-decoder.com/anthropic-releases-claude-fable-5-and-mythos-5-with-major-gains-in-coding-and-science/)
5. [TrueFoundry: Claude Fable 5 vs Opus 4.8 Benchmarks](https://www.truefoundry.com/blog/claude-fable-5-vs-opus-4-8-benchmarks-pricing-when-to-use-each)
6. [Lushbinary: Fable 5 vs GPT-5.5 vs Gemini 3.1 Pro](https://lushbinary.com/blog/claude-fable-5-vs-gpt-5-5-vs-gemini-3-1-pro-comparison/)
7. [Simon Willison's Weblog: Initial impressions of Claude Fable 5](https://simonwillison.net/2026/Jun/9/claude-fable-5/)
8. [AWS Blog: Anthropic Claude Fable 5 on AWS](https://aws.amazon.com/blogs/aws/anthropic-claude-fable-5-on-aws-mythos-class-capabilities-with-built-in-safeguards-now-available/)
9. [Digital Applied: Claude Fable 5 & Mythos 5 Release Benchmarks](https://www.digitalapplied.com/blog/claude-fable-5-mythos-5-release-benchmarks-2026)
10. [Tech Jacks Solutions: Fable 5 vs GPT-5.5 vs Gemini 3.1 Pro](https://techjacksolutions.com/ai-tools/anthropic-claude/fable-5-vs-gpt-5-5-vs-gemini-3-1-pro/)

---

*本报告基于2026年6月9-10日的公开信息编制。基准测试成绩主要来自厂商发布和独立测评机构，可能存在测试条件差异。建议在实际应用场景中进行独立验证。*
