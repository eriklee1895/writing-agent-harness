# Jev / TypeSafe 官方直连研究记录

## 任务边界

- 研究日期：2026-09-21（Asia/Shanghai）
- 官方直连端点：`https://api.typesafe.ai/v1/systemone`
- 模型：探索时验证 `jev-latest`，文章示例和固定测试使用 `jev-1.13.0`
- 认证：读取工作区 `.env` 中的 `TYPESAFE_API_KEY`，不把密钥写入文件、不写入文章
- 本文没有把 OpenRouter、Vercel、Cloudflare 或其他网关的响应混入官方 API 测试
- 所有延迟均为本机端到端 spot check，不是 SLA 或压力测试

## 官方资料

| 主题 | 来源 | 关键事实 |
| --- | --- | --- |
| 发布与定位 | https://typesafe.ai/blog/introducing-system-one-models-and-jev | System One / Jev 定位为给软件直接使用的结构化决策模型；官方介绍 RLCD、并行评估和类型化输出 |
| Quick start | https://docs.typesafe.ai/introduction/quickstart | 官方端点、curl 请求体、Python SDK、三种问题原语 |
| 当前模型 | https://docs.typesafe.ai/models | 当前 `jev-1.13.0`；`jev-latest` 与 `jev-preview` 别名；价格、限速、上下文、文本输入限制 |
| System One | https://docs.typesafe.ai/concepts/system-one | state + typed questions -> typed answers and probabilities；说明与传统 LLM 的输出契约差异 |
| 失效模式 | https://docs.typesafe.ai/model-jaggedness/jev-1.13 | 字面理解、算数/计数、日期比较、间接推理、无关 state、对抗性内容、结构不变量、生成等边界 |
| AI primer | https://docs.typesafe.ai/introduction/machine-learning-primer | RLHF / RLVR / RLCD 的官方解释，以及 calibration 是群体统计性质而非单条保证 |

## API 探针

### Probe A：一条中文工单，三种原语

请求概要：

- `state`：同一会员订阅被扣款两次，客户要求退款，已经等待两天
- `Choice`：`team`，候选为 `billing`、`technical`、`account`
- `Noul`：`refund_requested`
- `Score`：`urgency`，等级为低 / 中 / 高

响应摘要（2026-09-21）：

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
        "account": 0.0,
        "technical": 0.0
      }
    },
    "refund_requested": {
      "type": "noul",
      "noul": 0.98
    },
    "urgency": {
      "type": "score",
      "score": 1.03,
      "confidence": 0.95,
      "legend": {
        "0": "低：没有时间压力",
        "1": "中：希望尽快处理",
        "2": "高：明确影响业务或要求马上处理"
      },
      "probabilities": {
        "0": 0.0,
        "1": 0.97,
        "2": 0.03
      }
    }
  },
  "usage": {
    "input_tokens": 471,
    "output_tokens": 70
  }
}
```

HTTP 状态：`200`。

### Probe B：不完整状态

`state`：

> 广场上出现了一个没有来历的包裹。材料没有描述包裹外观、收件人、来源或内容。

问题与结果：

| 问题 | 返回 |
| --- | --- |
| 包裹外面是否写着收件人的姓名？ | `noul = 0.17` |
| 这个包裹是否危险？ | `noul = 0.40` |
| 一个谨慎的人更可能怎么做？ | `choice = wait`，`probabilities.wait = 0.81`，`confidence = 0.72` |

HTTP 状态：`200`。

解释边界：这是一个小探针，不足以证明模型对缺失信息的稳定行为；它只说明“没有显式 unknown 类型”这一接口事实，以及不同问题的概率会不同。官方 jaggedness 文档对 literal reading、irrelevant state 和 adversarial content 的警告更适合做长期设计依据。

### Probe C：一个问题与十个问题的端到端 spot check

同一份英文状态，每组 5 次，直接走官方 HTTPS：

| 组别 | 样本 | 成功 | 中位端到端时间 | 观测范围 |
| --- | ---: | ---: | ---: | ---: |
| 1 个 Noul | 5 | 5/5 | 0.763 秒 | 0.712–2.033 秒 |
| 10 个 Noul | 5 | 5/5 | 0.760 秒 | 0.715–0.816 秒 |

这不是性能基准。样本小，包含网络、连接和服务端排队；十问题请求的输入 token 也更长。它仅用于验证本文对“一个请求可以并行问多个问题”的工程直觉没有在当前服务上立刻失效。正式选型仍需在自己的网络和并发模型下测 p50 / p95 / p99。

## `jev-town` 项目审阅

审阅仓库： https://github.com/eriklee1895/jev-town

审阅版本：`9145ce0768a2e4c330cb6a6c1e78c1b9a9c32b81`（2026-09-21）

关键实现事实：

- 12 个居民，5 个地点；居民根据所在位置获得不同的可见 state
- 每个居民每刻一次 Jev 请求，问题包含 `noticed` / `caution` / `action`
- `ThreadPoolExecutor(max_workers=12)` 并行触发居民调用
- 第 8 刻创建没有来历的包裹；第 25 刻让阿绣进入 blindfold 状态
- UI 通过 SSE 接收实时决策流，支持时间轴回放和从某刻分叉重跑
- 当前公开版本的居民调用使用 OpenRouter Decisions API，模型为 `~typesafe/jev-latest`
- 街区观察者是可选的兼容 Responses API 的生成模型，默认配置为 MiniMax-M3

因此文章将它作为“把局部 state、概率决策和生成式观察者组合起来”的架构案例，而不是官方直连 API benchmark。

## 社区资料与口径

- Vercel 的 adoption 文章： https://vercel.com/blog/ai-gateway-jev-model-launch
- LangChain 的 middleware / harness 文章： https://www.langchain.com/blog/building-a-harness-with-jev
- LiteLLM 路由分类 benchmark： https://docs.litellm.ai/blog/jev-auto-router-benchmark
- OpenJev（接口复刻，不等于 TypeSafe Jev）： https://github.com/razorback16/openjev
- Jev 公开 claim ledger / calibration audit： https://github.com/SamuelSacco/jev-exploration

LiteLLM 文章的关键口径：80 个用例，每个分类器 3 次；Jev p50 126.814470ms、Haiku p50 688.395634ms；Jev 与作者预设 tier 的匹配率 95.00%，Haiku 73.75%；文章明确说明标签没有独立标注，不能推成通用准确率。

SamuelSacco 的项目是独立社区审计，不是 TypeSafe 官方结论；它对校准的否定性判断仍应随仓库的新数据变化。本文采用它作为风险提示，不把它写成最终裁决。

## OpenRouter Jev Router 研究记录（2026-09-27）

官方来源：

- 模型页：https://openrouter.ai/typesafe/jev-router
- Typesafe 模型集合：https://openrouter.ai/typesafe
- Auto Router 文档：https://openrouter.ai/docs/guides/routing/routers/auto-router
- Jev Lab：https://openrouter.ai/labs/jev

关键事实：`typesafe/jev-router` 于 2026-09-25 上线；OpenRouter 将它描述为“由 Jev 为每个请求选择模型与 reasoning effort”，并随着对话演进调整。它通过 OpenRouter 的统一 API 返回普通生成结果，不是 TypeSafe `/v1/systemone` 的 typed decision API。模型页当前列出 Chat Completions、Responses、Anthropic Messages 入口，支持文本、图片、音频、视频和文件，context window 为 1M；路由模型自身标价为 $0，但最终下游模型可能产生费用。

仓库 OpenRouter key 的小规模 live probe（2026-09-27，北京时间；不作为 benchmark）：

- “解释 cache stampede” → `stealth/space-bunny-alpha`，cost `0`，reasoning tokens `0`。
- “证明素数倒数之和发散” → `openai/gpt-6-sol`，cost `$0.00834`，reasoning tokens `459`。
- 同一 `session_id` 的定义 + 生产缓解方案两轮均落到 `stealth/space-bunny-alpha`；只说明本次会话没有切换，不能证明所有长对话的 stickiness 或自适应策略。

解释边界：OpenRouter 页面展示的 Top models used by Jev Router 是使用分布，不是质量 benchmark；正文因此把它写成生态信号，不把它写成模型能力排名。正式评估需要和手工规则、`openrouter/auto`、固定强模型比较端到端成功率、实际成本、p50/p95 延迟、切换率、缓存命中率和人工升级率。

## 原稿保留：Rerank 实测

原稿中的 rerank 实验是本文最有价值的原创证据之一，本轮重构保留并重新组织为独立章节：

Benchmark 口径：SciFact、NFCorpus、T2Retrieval 各抽 100 条 query；对完整文档库做 BM25（`k1=1.2`、`b=0.75`），保留每条 query 的 top-50 候选；Jev 与 `Qwen/Qwen3-Reranker-8B` 使用相同 query、候选文档、文本截断和指标；主实验让 Jev 在一次请求中为 50 个候选各问一个问题，并用 query 级配对 bootstrap 2000 次报告 95% CI。中文文档受 Jev 的 `state + 最长问题` 共享 32K 预算限制，统一截到每篇 600 字符；英文统一 2000 字符。

绝对 `nDCG@10`：SciFact 为 Qwen `0.7488`、Jev plain `0.7594`、task `0.7483`、score `0.7478`；NFCorpus 为 Qwen `0.3496`、Jev plain `0.3473`、task `0.3480`、score `0.3545`；T2Retrieval 为 Qwen `0.8047`、Jev plain `0.7777`、task `0.7527`、score `0.7695`。

- SciFact 英文：Jev plain − Qwen `+0.0106`，95% CI `[-0.019, +0.042]`；三种 Jev 主写法均打平。Jev 主写法 p50 为 405–438ms，Qwen 为 3594ms。
- NFCorpus 英文：三种配对 CI 全部跨零，没有稳定胜负；Jev 主写法 p50 为 422–474ms，Qwen 为 3469ms。
- T2Retrieval 中文：Jev 相对 Qwen 低 `0.0270–0.0520`，三条 CI 均排除零；Jev 主写法 p50 为 402–492ms，Qwen 为 3826ms，但 Jev token 更多、单 query 成本更高。
- 调用形状：SciFact 中，一次请求问完 50 个候选（`plain`）为 `0.7594`，每个候选单独请求（`pointwise`）为 `0.6569`；前者每条 query 墙钟 65ms、成本 `$0.000807`，后者为 1014ms、`$0.001363`。这说明 state 的组织方式本身会影响质量。

限制：中文组 100 条查询、单次运行，没有多种子重复和显著性校正；这组数据支持“中文不要直接外推”的方向性判断，不支持跨领域的普遍结论。

## 参考图审阅结论

本轮新增视觉不再只做抽象封面，参考了用户提供的 Feishu / 微信文章的图文方法：

- 场景截图：让读者先看到一个真实业务问题；
- 对比信息图：把 System One 与 LLM 的工作方式放在同一张图上；
- 原语卡片：逐个解释 Choice / Score / Noul；
- 系统架构图：显示 LLM、Jev、业务系统和工具的分工；
- API 图：显示 State、Questions、endpoint 和 answers 的关系；
- 数字与口径图：把官方数字和 caveat 放在同一画面；
- 阈值分流图：说明 confidence 如何进入自动化、复核和人工路径。

这些图的目标是承担解释工作，而不是为文章增加装饰性图片。

## 原稿处理说明

飞书原稿里已有大量早期实验数字和社区转述。新版只保留能够在当前资料、源码或本轮官方直连探针中解释清楚的内容；没有在本轮重新复现、且缺少同目录原始数据的数字，不作为新版结论。原稿中的图片没有直接复用，新增视觉资产见 `assets/manifest.json`。
