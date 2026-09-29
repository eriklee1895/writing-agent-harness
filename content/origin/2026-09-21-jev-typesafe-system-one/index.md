---
title: "Jev：TypeSafe AI 的 System One，到底是什么？"
date: 2026-09-22
register: technical-blog
tags: [AI, Agent, Jev, TypeSafe, System One]
summary: "从模型定义、真实场景、官方 API 到社区案例，完整解释 Jev 这种面向软件的决策模型。"
cover: assets/jev-cover-redesign.png
---

# Jev：TypeSafe AI 的 System One，到底是什么？

![Jev、SYSTEM ONE 与 TypeSafe AI](assets/jev-cover-redesign.png)

*Jev 不生成字符串。它把一个有边界的判断，变成代码可以继续处理的结果。*

最近几天，Jev 在开发者社区里快速升温。

它的产品介绍很容易让人误会：这是一个 AI 模型，却不聊天、不写文章、不写代码，也不返回一段解释。你给它一份状态和几个问题，它返回一个选项、一个分数、一个概率，或者一组概率分布。

第一眼看，像是模型主动放弃了最吸引人的部分。换到软件里看，事情正好反过来：大量程序并不需要 AI 写一段话，只需要它回答一个窄问题——该走哪个分支？这次调用是否危险？这条结果是否相关？这个任务需不需要更强的模型？

这就是 Jev 想占据的位置。

> **一句话定义**：Jev 是 TypeSafe AI 的第一个 System One 模型，面向软件返回带概率的类型化决策，而不是面向人生成字符串。

本文按一条完整的认知路径展开：先解释 Jev 是什么，再解释为什么它可以被看作一种新的模型物种；然后给出真实使用场景、我的 Jev 小镇项目、TypeSafe 官方 API 和 SDK 使用方法，最后放上官方直连实测、社区案例与边界。

## 一、Jev 是什么？

### 1.1 从“给人看的语言”到“给软件用的判断”

普通 LLM 的工作方式可以概括为：

```text
state + prompt → Transformer → token → token → token → 一段字符串
```

这条路径非常强大。它能写代码、做解释、生成方案、和人对话，也因此天然带着一些软件不喜欢的东西：输出长度不稳定、需要解析、可能出现 schema 之外的内容，还很难从一句“我有 90% 把握”推断它到底应该不应该被信任。

Jev 的输入输出契约不同：

```text
state + questions → typed decisions + probabilities
```

`state` 是模型可以看到的证据，可以是一段文本、JSON 对象或文本数组。`questions` 由开发者定义，规定问题、答案空间和每个候选项的含义。模型不负责写解释，也不负责调用函数；它只返回判断。

![System One 与 System Two 的工作方式对比](assets/jev-comparison.png)

*图 1：左边是 LLM 的串行生成，右边是 Jev 的并行评估。这里的重点不是“谁更聪明”，而是输出能不能直接进入软件流程。*

![Jev 的 System One 决策流水线](assets/jev-system-one-redesign.png)

*图 2：从状态、问题，到概率和代码分支。画面中的文字只保留 Jev 的核心原语和接口概念。*

这不是“同一个 LLM 少输出几个 token”。它更像是在模型接口层做了一次重新分工：把自然语言理解留下，把自由文本生成从主链路中拿掉。

### 1.2 关键事实速查

以下信息以 2026 年 9 月 22 日能查到的官方文档和发布信息为准；限速、价格和开放状态属于快速变化信息，接入前仍应看控制台和官方文档。

| 项目 | 当前信息 |
| --- | --- |
| 产品 | TypeSafe AI 的首个 System One 模型 Jev |
| 发布 | 2026-09-15 |
| 创始团队 | 前 OpenAI 研究员 Diogo Almeida 等人 |
| 模型形态 | 闭源托管模型，非聊天模型 |
| 输入 | 文本、JSON 对象、文本数组；不接收图像、音频、视频 |
| 当前稳定版本 | `jev-1.13.0` |
| 常用别名 | `jev-latest`、`jev-preview` |
| 上下文 | 每请求 64K；`state` 与最长问题共享 32K 预算 |
| 价格 | 输入 `$0.042 / MTok`，输出免费 |
| 限速 | 官方文档当前列出 250K tokens/s、1200 RPM，且说明会动态调整 |
| API | `POST https://api.typesafe.ai/v1/systemone` |

TypeSafe 把这条路线称为 **Machine Native Intelligence**：AI 的输出不是先给人读，再由程序猜意思，而是直接给软件消费。

![Jev 的官方数字与引用口径](assets/jev-numbers.png)

*图 3：官方数字和引用时必须带上的口径应该放在一起看。尤其是“schema 内 0% 错误”不等于业务判断 0% 出错。*

### 1.3 三种原语：Noul、Choice、Score

Jev 的问题空间目前由三个基本原语组成。

| 原语 | 本质 | 例子 | 主要返回值 |
| --- | --- | --- | --- |
| `Noul` | 二分类 | “客户是否要求退款？” | 一个 `0–1` 的 `noul` 概率 |
| `Choice` | 多分类 | “这张工单交给哪个团队？” | `choice`、各选项 `probabilities`、`confidence` |
| `Score` | 序数评分 | “客户有多生气？” | 连续 `score`、概率分布、`legend`、`confidence` |

三种原语可以在一次请求中混用：

```text
一张客服工单
  ├── 是否涉及退款？       Noul
  ├── 该交给哪个团队？     Choice
  ├── 紧迫程度如何？       Score
  └── 是否需要人工复核？   Noul
```

几个接入细节值得提前记住：

- `Choice` 的 `criteria` 是 `{key: description}` 映射。
- `Score` 的 `criteria` 是从低到高的数组，通常 2–10 档。
- `Noul` 返回的是 `noul`，没有单独的 `confidence` 字段。
- `Choice` 是“在候选项中相对选择一个”；多个 `Noul` 是多个绝对问题，不能默认它们互相构成补集。
- `Score` 的连续值适合表达“更接近哪一档”，不应该被当成精确测量仪。

### 1.4 它是不是 LLM？

这个问题要分两层回答。

从 inference 形态看，Jev 不是传统的自回归聊天 LLM：它不做 next-token generation，也不输出解释文本。TypeSafe 自己把它描述为 transformer-based 的 System One model，但没有公开完整架构。

从训练谱系看，它和 LLM 又属于同一棵树。TypeSafe 把 RLHF、RLVR 和 RLCD 画成三条 post-training 路径：RLHF 更接近聊天，RLVR 更接近可验证推理，RLCD 则针对 calibrated decisions。

因此，把 Jev 简化成“一个更小的 LLM”不准确；把它说成“完全和语言模型无关”也不准确。更稳妥的说法是：**它理解自然语言，但把输出目标从字符串改成了类型化决策。**

![三个原子原语：Choice、Score、Noul](assets/jev-primitives.png)

*图 4：三个原语的答案空间不同，但都返回可以被代码消费的决策结果。*

### 1.5 技术门槛到底在哪里？

如果只看 API，Jev 很容易被复刻：三个原语、一个 JSON endpoint、几个概率字段，一天就可以做出一个兼容接口。真正困难的部分不在接口，而在于模型是否能同时满足三个条件：

1. **零样本定义新任务**：调用时才用自然语言定义标签和标准。
2. **变形 schema 的并行输出**：一次请求可以有多个问题、多个类型、不同数量的候选项。
3. **跨任务概率校准**：没有为每个业务任务单独训练，却希望概率能帮助代码做阈值分流。

传统分类器靠“任务固定、标签写死、拥有标注数据”把问题变简单；Jev 试图把这三个前提拿掉。TypeSafe 把训练路线称为 RLCD（Reinforcement Learning for Calibrated Decisions），并表示训练数据主要由合成数据构造；具体架构、数据生成和训练细节仍未公开。

所以，Jev 的技术护城河如果成立，应该在训练数据、概率校准、并行 sampler 和服务成本曲线，而不是 `Choice` 这个名字本身。开源复刻能复刻接口，却不能自动继承 Jev 的能力。

## 二、为什么说它像一种新的模型物种？

### 2.1 不是新的 JSON，而是新的输出责任

传统 LLM 加 JSON mode，解决的是“让生成内容长得像 JSON”。程序仍然要处理：

- 字段可能缺失；
- 枚举值可能越界；
- 数字可能变成字符串；
- 模型说自己很确定，但没有可比较的概率依据。

Jev 从设计上规定了答案空间。`Choice` 只能从你给的候选项中选，`Score` 只能落在你给的有序等级上，`Noul` 只返回一个二元判断概率。

这解决的是**类型安全和可组合性**，不是业务正确性。Jev 仍然可能把一张正常工单判成高风险，只是它不会额外发明一个 `maybe_billing_but_also_technical` 这样的字段。

### 2.2 传统分类器、Jev 和 LLM 的区别

| 能力 | 传统 intent classifier | Jev / System One | 普通 LLM |
| --- | --- | --- | --- |
| 标签何时定义 | 训练时固定 | 推理时定义 | 推理时定义 |
| 新任务是否需要训练 | 通常需要 | 通常不需要 | 不需要 |
| 输入 | 固定特征或文本 | 自然语言 state + typed questions | message / prompt |
| 输出 | 固定类别 | 动态 typed decision + probability | 任意字符串 |
| 并行多问题 | 需自行编排 | 接口原生支持 | 需要多次调用或自行设计 |
| 概率 | 常见 softmax，需要另做 calibration | 作为核心输出 | 通常不可靠 |
| 生成与推理 | 弱 | 弱 | 强 |
| 私有化 | 通常可以 | 官方 Jev 不提供权重 | 取决于模型 |

Jev 的真正难点不在 `Noul / Choice / Score` 三个名字，而在于同时摆脱传统分类器的三个前提：任务固定、标签写死、拥有专门标注数据。

它试图在推理时用自然语言定义标签，在没有任务专属训练的情况下返回概率，并且一次前向同时评估一组不同形状的问题。跨任务校准如果真的成立，这才是有研究价值的部分；但这件事目前仍需要外部评测和业务数据验证。

### 2.3 概率真正进入了 if 语句

Jev 最有意思的产品假设，是把不确定性直接交给代码：

```text
高置信 + 低风险 → 自动执行
中置信 / 高代价 → 人工确认
低置信 / 开放问题 → 升级给普通 LLM
```

这就是 confidence-gated routing。

![置信度分级路由示意](assets/jev-routing.png)

*图 5：90 / 70 是一个便于理解的示例阈值，不是 TypeSafe 的官方默认值。真正的阈值要用业务数据标定。*

它不是让模型自己判断“要不要问人”，而是把概率、候选项和上下文交还给程序。阈值、权限、人工接管、重试和 fallback 都仍然是系统设计的一部分。

但 `confidence` 不能被理解为正确率，更不能被理解为授权令牌。官方说 RLCD 的目标是 calibrated decisions；社区独立审计则认为公开材料还不足以证明它已经跨任务稳定校准。生产系统必须用自己的标注集测：置信度是否真的能区分“可以自动处理”和“应该升级”的样本。

## 三、这种决策模型有什么价值？

### 3.1 模型路由：决定这次任务值得用多贵的模型

不是每个请求都值得交给最强模型。简单改写、局部提取、固定格式转换，可以走便宜模型；架构设计、复杂调试和高风险任务，才需要强模型。

Jev 可以先给任务做难度或风险判断：

```text
任务描述 → Jev 判断难度 / 风险 / 是否需要推理
         → 小模型 / 大模型 / 人工
```

路由器的价值不是把每个任务分得多漂亮，而是前置判断足够快、足够便宜，并且不会把简单任务误送进昂贵路径。

### 3.2 工具调用门控：在 Agent 动手之前多一道语义检查

Agent 的风险通常不在于它会不会说错，而在于它会不会真的执行一个不该执行的动作。

Jev 可以在工具调用前检查：

- 是否包含删除、发版、转账等高风险动作；
- 参数是否和当前任务一致；
- 是否需要人工确认；
- 连续失败后是否应该停止或重新规划。

但 Jev 不应拥有真正的权限。最终的 allow / deny / review 仍然要由代码、权限系统和人工流程决定。

### 3.3 RAG 与结构化抽取：先枚举，再让模型选择

Jev 不适合自由生成一个新答案，却适合从候选集合里选一个。

做检索后重排时，可以先由 BM25 或 embedding 召回 top-30，再让 Jev 对每段文本做相关性判断。做结构化抽取时，也可以先用正则或生成模型得到候选项，再让 `Choice` 从候选中选择。这样值域天然受控，少一层“模型自己编了一个不存在的值”的风险。

### 3.4 高频循环：游戏、语音、表单和 trace

当一次判断的延迟和成本降下来，AI 才能进入一些以前“不值得调用模型”的地方：

- 语音助手判断用户是不是在对它说话；
- 游戏角色在多个合法动作中选择下一步；
- 表单每次点击后判断是否需要改变流程；
- Agent 每一步对工具结果做轻量验收；
- 对大量 trace 做风险或质量筛选。

这些场景并不要求 Jev 负责规划。答案空间由代码枚举，Jev 负责在空间里做选择；需要文字、推理和失败重规划时，仍然升级给普通 LLM。

### 3.5 生产场景速查

| 场景 | Jev 负责什么 | 代码 / LLM 负责什么 |
| --- | --- | --- |
| 工单分流 | 团队、紧急程度、是否升级 | 业务规则、通知、人工队列 |
| 工具调用审批 | 是否危险、是否需要复核 | 权限、白名单、真实执行 |
| RAG 重排 | 候选段落相关性、优先级 | 召回、去重、最终截断 |
| 结构化抽取 | 从候选值中选择 | 候选生成、格式校验、入库 |
| 模型路由 | 难度、风险、是否需要推理 | 调用哪个模型、预算控制 |
| Trace 监控 | 是否异常、是否值得保留 | 日志、告警、人工复盘 |
| 实时 Agent / 游戏 | 在合法动作中选下一步 | 状态更新、规划、失败重试 |

### 3.6 一个典型的工具调用架构

一个更通用的 Agent 结构是：LLM 负责理解任务和规划动作，Jev 在工具真正执行之前做快速语义门控，确定性 Policy Code 负责权限与硬规则，最后才调用工具。

例如，Coding Agent 准备执行一个生产部署命令时，Jev 可以判断这是不是生产或不可逆动作、是否需要人工确认；但 Jev 不拥有权限，真正的执行权仍然在 Policy Code 和平台权限系统手里。

![Agent 工具调用：LLM 规划，Jev 门控，代码执行](assets/jev-tool-gate.png)

*图 6：Jev 提供语义信号，不拥有权限。这个边界比“让模型自己决定能不能执行”更重要。*

### 3.7 真实调用通常有三种形状

社区的 [Jev Lab](https://openrouter.ai/labs/jev) 案例里，真正值得观察的不是场景名字，而是请求如何组织。大致有三种调用形状：

| 调用形状 | 例子 | 适合解决的问题 |
| --- | --- | --- |
| 多问题 × 单 state | 工单分流、表单、工具审批 | 一份材料里同时问多个独立判断 |
| 单问题 × 多 state | feed 过滤、批量打标、RAG 重排 | 对大量候选逐个判断同一个问题 |
| 高频循环内联 | 语音门控、游戏动作、逐步 guardrail | 把短判断放进每一步交互循环 |

Jev Lab 给出的示例包括：95 条客服消息一次问 5 个问题、24 个工具调用一次做 4 项检查、对 40 个帖子做自然语言过滤、对 12 个字段做候选选择。这些数字来自 OpenRouter 的公开 recipe，不是本文的官方直连实测，引用时要把口径分开。

这三种形状背后的共同点是：**不要让模型决定整个世界，只让它回答一个已经被代码切窄的问题。**

## 四、TypeSafe 官方 API 使用指南

### 4.1 官方直连是这次文章的唯一测试入口

截至 2026 年 9 月 22 日，官方文档列出的稳定模型是 `jev-1.13.0`，常用别名是 `jev-latest`。官方直连端点是：

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer $TYPESAFE_API_KEY
Content-Type: application/json
```

探索时可以使用 `jev-latest`，生产调阈值时建议固定到 `jev-1.13.0`，并把响应里的 `model` 一起写入日志。

![TypeSafe 官方 API：State + Questions → Answers](assets/jev-api-guide.png)

*图 7：官方 API 的核心不是一个长 prompt，而是 State、Questions 和 Answers 三个明确部分。*

### 4.2 cURL 请求

下面这段就是最小可用请求：

```bash
curl -sS https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jev-1.13.0",
    "state": "客户说：同一笔会员订阅被扣了两次，已经等了两天，希望尽快退款。",
    "questions": {
      "team": {
        "type": "choice",
        "instructions": "这条工单应该交给哪个团队？",
        "criteria": {
          "billing": "付款、扣款、发票或退款",
          "technical": "产品故障、性能或集成问题",
          "account": "登录、权限或账户信息"
        }
      },
      "refund_requested": {
        "type": "noul",
        "instructions": "客户是否明确要求退款？"
      },
      "urgency": {
        "type": "score",
        "instructions": "客户的紧迫程度如何？",
        "criteria": [
          "低：没有时间压力",
          "中：希望尽快处理",
          "高：明确影响业务或要求马上处理"
        ]
      }
    }
  }'
```

响应的核心结构如下：

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "team": {
      "type": "choice",
      "choice": "billing",
      "confidence": 1.0,
      "probabilities": {
        "billing": 1.0,
        "technical": 0.0,
        "account": 0.0
      }
    },
    "refund_requested": {
      "type": "noul",
      "noul": 0.98
    },
    "urgency": {
      "type": "score",
      "score": 1.03,
      "confidence": 0.95
    }
  }
}
```

有一个很容易写错的细节：`Noul` 返回的是 `noul`，没有单独的 `confidence` 字段；`Choice` 和 `Score` 才会返回分布和 `confidence`。不要把三种结果强行塞进同一个读取逻辑。

### 4.3 Python SDK

TypeSafe 官方提供 Python SDK。当前项目使用 `uv` 管理依赖：

```bash
uv add typesafe-sdk
```

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient()

response = client.system_one(
    state="A customer was charged twice and asks for a refund.",
    questions={
        "department": Choice(
            instructions="Which team should handle this?",
            criteria={
                "billing": "Payment or subscription issues",
                "technical": "Bugs or integration problems",
                "account": "Login, permissions, or account data",
            },
        ),
        "is_urgent": Noul(
            instructions="Does the message express urgency?"
        ),
        "frustration": Score(
            instructions="How frustrated is the customer?",
            criteria=["Calm", "Frustrated but civil", "Very angry"],
        ),
    },
)

print(response.answers["department"].choice)
print(response.answers["is_urgent"].noul)
print(response.answers["frustration"].score)
```

SDK 的默认模型是 `jev-latest`。如果你已经围绕某个版本调过阈值，要固定版本，并在升级时重新跑一遍标注集。

### 4.4 接入时要自己负责的事情

- `429`：官方限速会动态变化；SDK 默认会做退避，裸 HTTP 要自己尊重 `retry-after`。
- `state`：它是证据，不是现实世界。先过滤无关内容，别把整段上下文一股脑塞进去。
- `criteria`：描述要具体，最好显式加 `other`，承接“都不匹配”的情况。
- 版本：日志记录 `model`、输入摘要、问题版本、输出概率和最终人工结果。
- 阈值：按动作的犯错代价分别设，不存在一个全局阈值。

### 4.5 官方直连和其他入口有什么区别？

社区已经把 Jev 接入多个网关，但它们的价值不同：

| 入口 | 适合什么 | 需要注意什么 |
| --- | --- | --- |
| TypeSafe 官方 | 原生 API、完整上下文、版本和限速优先 | 自己处理账号、重试和成本记录 |
| Vercel AI Gateway | 已经使用 Vercel，想统一计费和 trace | 多了一层网关，model ID 不同 |
| OpenRouter | 已经把多模型都放在 OpenRouter | 使用自己的 Decisions API，不等同于官方请求体 |
| Cloudflare / Netlify 等网关 | 已经在对应平台部署 | 上下文、版本和可用能力以网关文档为准 |

本文的使用指南和实测只走 TypeSafe 官方直连；其他入口只在生态部分作为接入选项讨论。

## 五、官方直连实测

这次测试于 2026 年 9 月 21 日完成，所有请求都直接访问 `api.typesafe.ai/v1/systemone`。它不是大规模 benchmark，目的是确认接口、字段和几种典型行为。

### 5.1 一次请求混合三种原语

中文客服工单的实际结果：

| 判断 | 结果 |
| --- | --- |
| 团队 | `billing`，`confidence = 1.0` |
| 是否要求退款 | `noul = 0.98` |
| 紧迫程度 | `score = 1.03`，`confidence = 0.95` |

HTTP 状态为 200，响应中的实际模型是 `jev-1.13.0`，输入 token 为 471，输出 token 为 70。

这证明接口可以工作，不证明所有客服工单都有 98% 的正确率。单条样例没有统计意义，`confidence` 也不是“可以直接执行”的许可证。

### 5.2 不完整状态的探针

我又发了一段刻意不完整的状态：

> 广场上出现了一个没有来历的包裹。材料没有描述包裹外观、收件人、来源或内容。

实际结果是：

| 问题 | 返回 |
| --- | --- |
| 包裹外面是否写着收件人的姓名？ | `noul = 0.17` |
| 这个包裹是否危险？ | `noul = 0.40` |
| 一个谨慎的人更可能怎么做？ | `wait`，概率 `0.81`，`confidence = 0.72` |

这次调用没有返回显式的 `unknown` 类型。它提醒了我一个工程事实：材料里没有写，不等于现实里不存在。对属性型问题，必须在自己的数据和任务上验证 Jev 是否会把缺失误读成否定。

### 5.3 多问题 fan-out

同一份英文状态下，我分别测试 1 个问题和 10 个问题，每组 5 次，10 次全部成功：

| 请求 | p50 端到端时间 | 观测范围 |
| --- | ---: | ---: |
| 1 个 `Noul` | 0.763 秒 | 0.712–2.033 秒 |
| 10 个 `Noul` | 0.760 秒 | 0.715–0.816 秒 |

这不是性能基准，样本太小，也包含网络和服务端排队。但在这次 spot check 里，问题数从 1 增加到 10 没有带来线性延迟增长。这正是 Jev 的主要使用形状：把多个独立判断一次问完，再由代码决定哪些结果重要。

## 六、社区生态支持

### 6.1 LangChain：Model Router 和 Auto Mode

[LangChain 的集成文章](https://www.langchain.com/blog/building-a-harness-with-jev) 给了两个清晰案例：`ModelRouterMiddleware` 用 Jev 评估任务难度，`AutoModeMiddleware` 在工具执行前检查风险。

这个案例的重点不是“框架已经替你解决了生产问题”，而是把分工放对了：普通 LLM 负责理解和生成，Jev 负责已定义答案空间里的廉价判断。

### 6.2 基础设施和框架的快速接入

Jev 发布后，支持它的并不是只有一两个 SDK，而是很快形成了多层接入生态：

| 层级 | 代表入口 | 主要价值 |
| --- | --- | --- |
| 官方 API / SDK | TypeSafe 官方直连、Python SDK、JavaScript SDK | 原生 `systemone` 语义、版本和限速优先 |
| 模型网关 | Vercel AI Gateway、OpenRouter、Cloudflare、Netlify | 多模型统一计费、trace、平台级部署 |
| Agent 框架 | LangChain、Pydantic AI、LiteLLM | 把 Jev 放进路由、工具门控和运行时 middleware |
| 社区工具 | MCP wrapper、reranker、CLI、开源复刻 | 将决策模型封装成开发者日常工具 |

这里要区分“支持”与“同构”。Vercel、Cloudflare、Netlify 等平台解决的是网关和运维接入；OpenRouter 还额外设计了自己的 Decisions API，请求体不完全等同于 TypeSafe 官方 API。本文的 HTTP / SDK 示例与实测只针对官方直连。

Vercel 在发布后很快公布了采用数据，LangChain 直接提供了 `ModelRouterMiddleware` 和 `AutoModeMiddleware`。这说明 Jev 的价值很快被理解为 Agent 基础设施的一层，而不是又一个聊天模型。

## 七、社区案例

### 7.1 OpenRouter Jev Lab：把小判断批量化

OpenRouter 的 Jev Lab 展示了几种可以直接抄架构的 recipe：客服消息分流、工具调用审批、不会编的结构化抽取、自然语言 feed 过滤和高频游戏决策。

这些案例的共同点不是“让 Jev 更聪明”，而是把问题切成许多独立小判断：95 条消息一次问 5 个问题，24 个工具调用一次做 4 项检查，12 个候选字段让模型从已有选项中选择。Jev 负责回答，代码负责执行。

### 7.2 LiteLLM：路由分类器

[LiteLLM 的公开基准](https://docs.litellm.ai/blog/jev-auto-router-benchmark) 使用 80 个用例、每个分类器重复 3 次。Jev 的 p50 分类延迟为 126.81ms，Claude Haiku 为 688.40ms；在作者预先写好的 tier 标签上，Jev 匹配率为 95%，Haiku 为 73.75%。

这个结果只支持一个窄命题：在这套配置里，Jev 适合作为快速路由层。标签来自同一位作者，没有独立标注，也没有评估后续模型的最终回答质量。

### 7.3 Browser Use：Jev 负责动作选择，LLM 负责文字输入

[Browser Use 的 `jev-ultrafast` 项目](https://github.com/browser-use/jev-ultrafast) 给了一个很具体的混合架构：先把当前页面转成带编号的可操作元素和动作，再让 Jev 在一次请求里选择 operation 和 target；只有遇到 `TYPE_TEXT` 时，才调用小模型生成要输入的文字，浏览器执行、页面刷新和目标校验交给代码完成。

这个案例的价值不在于一个漂亮数字，而在于分工足够清楚：Jev 不负责独立完成规划、文字生成、执行和验证，而是负责其中最适合类型化的问题——“下一步做哪个动作、作用于哪个元素”。这比把 Jev 当作完整的聊天式 browser agent 更符合它的输出边界。

这再次说明，Jev 的问题不是“能不能替代 LLM”，而是“这一小步是不是一个已经被代码定义好的选择题”。

### 7.4 OpenJev：接口可以复刻，能力不能默认继承

[OpenJev](https://github.com/razorback16/openjev) 用开源模型实现了兼容 TypeSafe 形状的 `/v1/systemone` 接口。它说明 `state + typed questions → probabilities` 这个接口本身并不神秘。

但接口兼容不等于训练质量兼容。OpenJev 的答案质量取决于底层开源模型；它不能自动继承 TypeSafe 对校准、延迟和服务稳定性的承诺。

### 7.5 OpenRouter 的 Jev Router：Jev 可能真正适合做的事

9 月 25 日，OpenRouter 的 Typesafe 页面上线了一个新的模型入口：[`typesafe/jev-router`](https://openrouter.ai/typesafe/jev-router)。它和前面介绍的 `typesafe/jev-1.13` 不是一回事。

`jev-1.13` 是一个直接返回 `Noul`、`Choice`、`Score` 和概率的决策模型；`jev-router` 则把 Jev 放在模型调用链的前面，让 Jev 先判断“这次请求应该交给哪个模型、用多深的 reasoning effort”，然后由被选中的模型生成最终回答。应用看到的仍然是普通的文本结果，而不是 Jev 的 typed decision。

这件事很重要，因为它把 Jev 从“某个 Agent 里的一个判断节点”推到了更大的基础设施位置：**Jev 不一定要替代 LLM，它可以负责决定下一次应该调用哪个 LLM。**

![OpenRouter Jev Router benchmark 图](assets/media/jev-router-announcement/jev-router-benchmark.jpg)

*图 11：OpenRouter 官方 X 帖子中的 Jev Router benchmark 配图。原始帖子还配有一条发布说明视频，已作为本节的本地媒体素材保存。*

[查看 OpenRouter Jev Router 发布说明视频](assets/media/jev-router-announcement/jev-router-intro.mp4)

在配图对应的官方帖子里，OpenRouter 宣称 Jev Router 在四个 Agent benchmark 上完成了 `237 / 423` 个任务，而 OpenRouter Auto Router 为 `130 / 423`，并称前者多完成 82%。这是厂商公开宣传口径，不是本文独立复现的 benchmark；真正上线前仍应按自己的任务回放集重测。

#### 能力与优势

| 维度 | 公开能力 | 对工程的意义 |
| --- | --- | --- |
| 路由对象 | 同时选择下游模型和 reasoning effort | 比固定“快 / 慢模型”更细 |
| 统一入口 | Chat Completions、Responses、Anthropic Messages | 业务代码不用反复适配 provider |
| 输入能力 | 文本、图片、音频、视频、文件；页面列出 1M context | 适合长上下文和多模态 Agent |
| 计费 | 路由模型页面标价为 $0 | 最终仍按被选中的下游模型计费 |

它和 OpenRouter 自己的 [`openrouter/auto`](https://openrouter.ai/docs/guides/routing/routers/auto-router) 不同：Auto Router 是 OpenRouter 的市场信号路由器；Jev Router 是由 Jev 驱动的 TypeSafe 路由模型。两者都能减少手工维护模型路由表，但策略、可控方式和产品归属不同。

#### 小规模探针：路由确实发生了，但还不是 benchmark

业务代码只需要把模型名换成 `typesafe/jev-router`，并记录响应里的实际 `model`、usage 和 cost。2026-09-27 的小探针结果如下：

| 请求 | 实际模型 | 成本 | 观察 |
| --- | --- | ---: | --- |
| 一句话解释 cache stampede | `stealth/space-bunny-alpha` | `$0` | 简单请求走免费模型 |
| 证明素数倒数之和发散 | `openai/gpt-6-sol` | `$0.00834` | 复杂请求走强模型，459 reasoning tokens |
| 同一 session 连续两轮 | 两轮均为 `stealth/space-bunny-alpha` | `$0` | 本次没有切换，不代表所有长对话都固定模型 |

这证明路由不是固定转发，但没有证明它比人工规则或 `openrouter/auto` 更准确。正式评估仍要用真实回放集比较端到端成功率、成本和延迟。

#### 结论与边界

模型路由可能是 Jev 最自然的应用方向：它本质上是一个有限候选集里的选择题，Jev 负责选择模型和 effort，OpenRouter 负责执行，应用负责预算、权限、fallback 和结果评估。

它的优势是降低模型选择的维护成本；它的风险是路由漂移、下游能力不一致、成本不可只看路由器标价，以及选择正确不等于回答正确。真正上线前，要用自己的回放集比较手工规则、`openrouter/auto`、Jev Router 和固定强模型，记录成功率、实际成本、p50/p95 延迟、模型切换率和人工升级率。

## 八、我的两个案例

### 8.1 Jev 小镇：局部 state 如何产生不同判断

我做的 [Jev 小镇](https://github.com/eriklee1895/jev-town)，是一个把“机器如何做判断”变成可观察场景的小实验。

小镇里有 12 个居民和 5 个地点：集市、广场、酒馆、码头和后巷。每个居民拿到的 state 不一样，只能看到自己所在位置可见的区域；每一刻，程序给每个居民发起一次 Jev 请求，问三件事：有没有注意到异常、戒备程度如何、下一步最可能做什么。

第 8 刻，广场出现一个没有来历的包裹。第 25 刻，阿绣被蒙住眼睛，之后仍然会继续做判断。前一个事件用来观察“材料里没写的东西会怎样影响判断”，后一个事件则把上下文边界变成了一个 UI 状态。

![Jev Town：局部 state 如何产生不同判断](assets/jev-town-flat.png)

*图 8：Jev Town 的平面信息图。它把局部视野、中央事件和不同的概率判断放在同一张图里。*

![Jev 小镇当前版本的真实界面](assets/jev-town-ui.jpg)

*图 9：项目当前版本的真实界面。右侧是居民最近一次判断的概率分布，底部是事件和街区观察者的叙述。*

这个项目里有两层模型：居民层用 Jev 做快而局部的判断；每隔几刻，再让一个普通生成模型从结构化摘要里写一段街区简报。一个负责局部反应，一个负责全局叙事。

需要说明的是，项目当前公开版本的居民调用走的是 OpenRouter Decisions API；本文的官方 API 实测只走 TypeSafe 官方直连。小镇是架构案例，不冒充官方 benchmark。

### 8.2 Rerank 与专用 reranker 的 PK 实测

这组实验是本文最重要的原创数据之一。它不是把两个 API 各调用几次，然后凭体感说“这个更快”；而是先固定一条检索链路，再问一个更窄、更容易复核的问题：**在完全相同的 query、候选集、文档文本和指标下，Jev 能不能承担 reranker 的工作？**

#### 先把实验对象说清楚

检索系统里至少有三个环节：先从全量文档里召回候选，再对候选排序，最后把排在前面的内容交给生成模型。这里测的只有中间的 rerank，不把 BM25 的召回能力、生成模型的回答能力混进来。

对照模型是 `Qwen/Qwen3-Reranker-8B`。两边都实现成 `rerank(query, docs) -> scores[]`：输入完全相同的 query 和 BM25 候选集，输出每篇候选的相关性分数，再统一排序。

Jev 主实验测了三种写法：

- `plain`：每个候选一个 `Noul`，问题是“候选文档是否与查询相关”；
- `task`：把问题改成“候选文档能否为查询提供有用信息”，用于观察措辞敏感度；
- `score`：使用 `Score` 原语，把相关程度分成四级，再把分数归一化。

另有一条 `pointwise` 实验臂：每个候选单独发起一次 Jev 请求。它只用于观察“一个请求问 50 个问题”和“50 个候选发 50 次请求”的调用形状差异，不和主实验的三种 Jev 写法混在一起。

#### Benchmark 怎么做

| 实验环节 | 具体设置 | 为什么要固定 |
| --- | --- | --- |
| 数据集 | SciFact、NFCorpus、T2Retrieval；每个数据集按固定种子抽取 100 条 query | 同时观察英文和中文，不让单一语料决定结论 |
| 候选集 | BM25（`k1=1.2`、`b=0.75`）对完整文档库排序，取 top-50 | 未命中 query 的文档也保留，避免把“召回失败”误当成“重排失败” |
| 输入契约 | 两个模型使用完全相同的 query、候选文档、文档截断和指标算法 | 排除输入长度、候选顺序和预处理造成的偏差 |
| 文档长度 | 英文每篇 2000 字符；中文每篇 600 字符 | 中文 50 篇放入 Jev 的 `state` 会撞上 `state + 最长问题` 共享的 32K 预算 |
| Jev 主调用 | 一个请求放入 50 个候选，每个候选对应一个问题；主实验并发度为 8 | 测量 Jev 的多问题 fan-out，而不是用 50 次网络请求惩罚它 |
| Qwen 调用 | `Qwen/Qwen3-Reranker-8B` 对相同的 50 个 query-document pair 打分，并发度为 8 | 让两条主实验臂的并发条件可比 |
| 质量指标 | MRR、nDCG@5、nDCG@10、MAP、Recall@10 | 同时看首个相关结果、前 5/10 名和整体排序质量 |
| 显著性 | query 级配对 bootstrap 2000 次，报告 95% CI | 判断 Jev 与 Qwen 的差异是否稳定 |
| 成本与延迟 | 记录输入 token、成本、p50/p90 和每条 query 的墙钟时间 | 速度和成本都只代表这次实验口径，不是 SLA |

#### 先看绝对质量：Jev 和 Qwen 到底各得了多少分

下面这张表先不讲“赢了还是输了”，只把同一个指标下两边的绝对结果摆在一起。`BM25` 是不做 rerank 的基线；`Jev plain / task / score` 是三种主调用写法。

| 数据集 | BM25 nDCG@10 | Qwen nDCG@10 | Jev plain | Jev task | Jev score | 直接观察 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SciFact（英） | 0.6132 | 0.7488 | **0.7594** | 0.7483 | 0.7478 | Jev plain 最高，但差异需要看 CI |
| NFCorpus（英） | 0.2804 | 0.3496 | 0.3473 | 0.3480 | **0.3545** | 三种 Jev 写法都与 Qwen 很接近 |
| T2Retrieval（中） | 0.6618 | **0.8047** | 0.7777 | 0.7527 | 0.7695 | Qwen 在三种 Jev 写法上都更高 |

如果只看 `nDCG@10`，很容易把 SciFact 的 `0.7594 vs 0.7488` 读成“Jev 赢了”，也容易把 NFCorpus 的 `0.3545 vs 0.3496` 读成“Jev 赢了”。所以还要看 query 级配对差值和置信区间。

完整指标如下。它们都来自同一批 100 条 query、同一份 top-50 候选集：

| 数据集 | 方案 | MRR | nDCG@5 | nDCG@10 | MAP | Recall@10 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SciFact | BM25 | 0.5903 | 0.5868 | 0.6132 | 0.5780 | 0.7275 |
| SciFact | Qwen3-Reranker-8B | 0.7363 | 0.7403 | 0.7488 | 0.7157 | 0.8325 |
| SciFact | Jev plain | 0.7415 | 0.7433 | **0.7594** | 0.7263 | 0.8475 |
| SciFact | Jev task | 0.7264 | 0.7311 | 0.7483 | 0.7111 | 0.8475 |
| SciFact | Jev score | 0.7336 | 0.7303 | 0.7478 | 0.7175 | 0.8275 |
| NFCorpus | BM25 | 0.4758 | 0.2913 | 0.2804 | 0.1412 | 0.1697 |
| NFCorpus | Qwen3-Reranker-8B | 0.5489 | 0.3767 | 0.3496 | 0.1728 | 0.2058 |
| NFCorpus | Jev plain | 0.5448 | 0.3779 | 0.3473 | 0.1766 | 0.1995 |
| NFCorpus | Jev task | 0.5585 | 0.3816 | 0.3480 | 0.1777 | 0.1951 |
| NFCorpus | Jev score | 0.5757 | 0.3907 | **0.3545** | 0.1848 | 0.1976 |
| T2Retrieval | BM25 | 0.8269 | 0.6632 | 0.6618 | 0.5864 | 0.6399 |
| T2Retrieval | Qwen3-Reranker-8B | 0.9383 | 0.8376 | **0.8047** | 0.7397 | 0.7569 |
| T2Retrieval | Jev plain | 0.9125 | 0.8042 | 0.7777 | 0.7103 | 0.7352 |
| T2Retrieval | Jev task | 0.8880 | 0.7773 | 0.7527 | 0.6804 | 0.7223 |
| T2Retrieval | Jev score | 0.9049 | 0.7933 | 0.7695 | 0.6991 | 0.7339 |

#### 再看 Jev vs Qwen：差值、CI 和“赢了几次”

这里的 `平均 Δ` 是 Jev 的 `nDCG@10` 减去 Qwen 的 `nDCG@10`；“赢 / 输”按 100 条 query 逐条比较，bootstrap 重采样 2000 次。

| 数据集 | Jev 写法 | Qwen nDCG@10 | Jev nDCG@10 | 平均 Δ | 95% CI | 赢 / 输 | 判断 |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| SciFact | plain | 0.7488 | 0.7594 | +0.0106 | [-0.019, +0.042] | 13 / 10 | 打平，区间跨零 |
| SciFact | task | 0.7488 | 0.7483 | -0.0004 | [-0.029, +0.029] | 10 / 10 | 打平，区间跨零 |
| SciFact | score | 0.7488 | 0.7478 | -0.0010 | [-0.033, +0.030] | 13 / 9 | 打平，区间跨零 |
| NFCorpus | plain | 0.3496 | 0.3473 | -0.0022 | [-0.021, +0.018] | 21 / 25 | 打平，区间跨零 |
| NFCorpus | task | 0.3496 | 0.3480 | -0.0016 | [-0.021, +0.019] | 22 / 24 | 打平，区间跨零 |
| NFCorpus | score | 0.3496 | 0.3545 | +0.0049 | [-0.015, +0.027] | 23 / 24 | 打平，区间跨零 |
| T2Retrieval | plain | 0.8047 | 0.7777 | -0.0270 | [-0.053, -0.003] | 21 / 25 | Qwen 更好，区间排除零 |
| T2Retrieval | task | 0.8047 | 0.7527 | -0.0520 | [-0.082, -0.023] | 14 / 36 | Qwen 更好，区间排除零 |
| T2Retrieval | score | 0.8047 | 0.7695 | -0.0352 | [-0.061, -0.013] | 15 / 31 | Qwen 更好，区间排除零 |

![Jev 做 Rerank：英文打平，中文落后](assets/jev-rerank.png)

*图 10：Rerank 实测的方向性结论。英文语料上，三种 Jev 主写法与 Qwen 的质量差异都没有稳定跨过零；中文语料上，Qwen 在三种写法中都更高。*

#### 延迟、token 和成本：Jev 快，但不总是更便宜

| 数据集 | 方案 | 输入 token / query | p50 | p90 | 墙钟 / query | 成本 / query |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SciFact | Qwen | 21,023 | 3,594ms | 6,872ms | 585ms | $0.000841 |
| SciFact | Jev plain | 19,214 | 405ms | 649ms | 65ms | $0.000807 |
| SciFact | Jev task | 19,514 | 413ms | 799ms | 70ms | $0.000820 |
| SciFact | Jev score | 21,264 | 438ms | 598ms | 66ms | $0.000893 |
| NFCorpus | Qwen | 20,193 | 3,469ms | 9,335ms | 825ms | $0.000808 |
| NFCorpus | Jev plain | 18,804 | 447ms | 681ms | 70ms | $0.000790 |
| NFCorpus | Jev task | 19,104 | 422ms | 664ms | 68ms | $0.000802 |
| NFCorpus | Jev score | 20,854 | 474ms | 1,221ms | 84ms | $0.000876 |
| T2Retrieval | Qwen | 20,759 | 3,826ms | 6,441ms | 682ms | $0.000830 |
| T2Retrieval | Jev plain | 26,621 | 402ms | 667ms | 65ms | $0.001118 |
| T2Retrieval | Jev task | 26,921 | 419ms | 1,010ms | 70ms | $0.001131 |
| T2Retrieval | Jev score | 28,671 | 492ms | 1,241ms | 84ms | $0.001204 |

主实验的结论因此要拆成两句：**延迟上，Jev 主写法大约比 Qwen 快 7–9 倍；成本上，英文两组接近或略低，中文组反而更高。** 中文 token 密度和 Jev 的共享 32K state 预算，让“更快”与“更便宜”不再是同一件事。

#### 调用形状本身就是实验变量

SciFact 还额外跑了一条 `pointwise`：每篇候选单独发起一次 Jev 请求。它的单次子请求 p50 只有 310ms，但一条 query 的 50 个请求合起来，墙钟为 1,014ms，输入 token 和成本也明显上升：

| Jev 调用形状 | nDCG@10 | 每条 query 墙钟 | 成本 / query | 解释 |
| --- | ---: | ---: | ---: | --- |
| 一次请求问完 50 个候选（`plain`） | **0.7594** | 65ms | $0.000807 | query 和 50 个候选在同一份 state 中，50 个问题并行求值 |
| 每个候选单独请求（`pointwise`） | 0.6569 | 1,014ms | $0.001363 | 每次只看到一篇文档，靠代码侧汇总 50 个分数 |

这次实验里，批量请求不仅更快，质量也更高，差距约 `0.10`。它说明对 Jev 来说，候选是否共享同一个 state 不是纯粹的网络优化，而是模型输入的一部分。不能把一次请求问 50 个问题简单理解成“50 次独立调用的廉价并发版”。

#### 这次实验踩过的坑

这组结果不是第一轮就得到的。几个问题如果不先修正，表格看起来会很漂亮，但实际测到的是实验装置的差异：

1. **两条实验臂拿到的材料长度不一样。** 第一轮给 Jev 的文档截断到 1200 字符，给 Qwen 的是 2000 字符；那测的是“谁看得多”，不是谁判断得准。后来统一英文 2000、中文 600 字符，才保留结果。
2. **两条实验臂并发度不一样。** 第一轮 Qwen 串行、Jev 并发 8，墙钟差异里混入了并发配置；正式主实验把两边并发度统一为 8。
3. **BM25 的空候选集会污染重排指标。** 如果 BM25 只返回命中词项的文档，未命中的 query 会得到空集合；那时算出来的是召回失败率，不是 reranker 的质量。修正后对完整文档库排序，未命中的文档仍然以 0 分进入候选。
4. **Jev 的 32K 限制是 `state + 最长问题` 的共享预算。** 中文实验一开始沿用英文文本长度，直接撞到 `400 max_tokens_exceeded`。50 篇中文文档最终只能统一截到每篇 600 字符；这个限制也意味着中文组的绝对分数不能直接和英文组横比。

这组结果有三个工程结论。

第一，**英文上可以把 Jev 当作低延迟 reranker 候选，但不能写成“显著超过 Qwen”**。SciFact 和 NFCorpus 的三种主写法，配对 CI 都跨零；绝对分数有高有低，但没有稳定胜负。

第二，**中文不要直接替换专用 reranker**。在 T2Retrieval 上，Qwen 的 `nDCG@10` 为 `0.8047`，三种 Jev 写法为 `0.7777 / 0.7527 / 0.7695`，三个 CI 都排除零。速度优势存在，但质量和成本都不能忽略。

第三，**rerank benchmark 必须把调用形状写进实验定义**。query、候选集合、文档长度、问题措辞、批量方式、并发度和统计方法，任何一个变化都可能改变结论。真正准备上线时，至少要在自己的数据上重新测 `nDCG@10`、P95/P99 延迟、失败率和单次成本，并保留人工或规则 fallback。

## 九、边界：什么时候不要用 Jev

官方文档已经列出 Jev 1.13 的失效边缘：字面理解、算数和计数、日期比较、间接推理、无关 state、对抗性内容、矛盾的 instructions / criteria、结构不变量，以及生成文本。

我再把它翻成选型语言：

- 需要写文字、代码和解释：用生成模型。
- 需要多步推理、规划和失败重试：用 reasoning LLM 和确定性 workflow。
- 需要算金额、日期、数量和排序：交给代码。
- 需要保护不可逆动作：Jev 可以做前置语义信号，但不能替代权限、规则和人工确认。
- 需要中文长文本判断：先拿自己的数据测，不要把英文结果直接外推。
- 需要图片、音频或视频输入：当前官方 Jev 是纯文本模型，先做外部转写或视觉分析。

还有一个实际取舍：固定意图、数据稳定、有足够标注数据的任务，微调一个小模型往往更便宜、更可控，也能私有化。Jev 的优势区间是几十上百个异质、变化快、没有专门标注数据的碎判断。

### 9.1 官方列出的失效模式，以及工程上的补救

| 失效模式 | 常见表现 | 更稳妥的做法 |
| --- | --- | --- |
| 字面理解 | 问题写得含糊，模型按字面回答另一件事 | 把条件和边界写进 instructions / criteria |
| 算数、计数、数字比较 | 对数量、金额、日期差不可靠 | 计算和排序放到代码里 |
| 间接推理 | 需要多跳关系或双重否定 | 拆成多个直接问题 |
| 无关 state 太多 | 上下文变长后注意力被稀释 | 先检索、裁剪，只发送相关字段 |
| 对抗性内容 | state 中的文本反过来影响判断 | 把外部内容当不可信数据，先做安全处理 |
| 结构不变量 | 两个看似互补的问题概率不一定相加为 1 | 每个问题直接问清楚，恒等式由代码保证 |
| 生成文本 | 让 Jev 写解释、代码或回复 | 交给普通生成模型 |

Jev 当前也是闭源托管模型：没有公开权重，不支持按客户数据 fine-tune / LoRA。领域适配主要靠三件事完成：把材料放进 `state`，把边界写进 `instructions` / `criteria`，再把多个原子判断在代码里组合。

## 十、结论：Jev 的价值是让软件多一个“判断层”

我不会把 Jev 写成下一代 LLM，也不会把它当成一个神秘的新范式。

它更像一种新的模型接口：让 AI 在软件里不必每次都先写一段话，再让程序猜它是什么意思。答案空间由开发者定义，模型返回局部判断和概率，代码负责组合、验证、授权和回退。

这条路线的价值不在于替代 LLM，而在于把 LLM 不该承担的那一部分工作拿出来：路由、门控、筛选、评分、验收和高频循环。

如果你要试，别从“让 Jev 接管整个 Agent”开始。挑一条高频、答案空间有限、错误可回滚的真实决策链；固定模型版本；保留规则和人工 fallback；记录概率、最终结果和人工纠正。三周后，你会比任何一张官方倍率表更清楚它是否值得留下。

Jev 真正有意思的地方，是它让一个问题变得无法回避：

> 这一步真的需要生成一段话吗？还是只需要一个有边界、可记录、可以被代码组合的判断？

如果答案是后者，Jev 才有位置。

## 参考资料

- [TypeSafe AI：Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- [TypeSafe AI Docs：Quick start](https://docs.typesafe.ai/introduction/quickstart)
- [TypeSafe AI Docs：Models](https://docs.typesafe.ai/models)
- [TypeSafe AI Docs：System One](https://docs.typesafe.ai/concepts/system-one)
- [TypeSafe AI Docs：Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- [Vercel：Jev is the fastest-adopted model in AI Gateway history](https://vercel.com/blog/ai-gateway-jev-model-launch)
- [LangChain：Building a Harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev)
- [LiteLLM：JEV Classifier benchmark](https://docs.litellm.ai/blog/jev-auto-router-benchmark)
- [OpenJev](https://github.com/razorback16/openjev)
- [Samuel Sacco：jev-exploration](https://github.com/SamuelSacco/jev-exploration)
- [OpenRouter：Jev Router](https://openrouter.ai/typesafe/jev-router)
- [OpenRouter：Typesafe 模型页](https://openrouter.ai/typesafe)
- [OpenRouter：Auto Router 文档](https://openrouter.ai/docs/guides/routing/routers/auto-router)
- [OpenRouter：Jev Lab](https://openrouter.ai/labs/jev)
- [Erik Lee：jev-town](https://github.com/eriklee1895/jev-town)

---

*本文的官方 API 测试于 2026-09-21 完成，使用 TypeSafe 官方 `api.typesafe.ai/v1/systemone`，没有把网关或第三方代理的响应混入测试结果。社区数字均保留原始来源和口径，不视为对所有任务的普遍保证。*
