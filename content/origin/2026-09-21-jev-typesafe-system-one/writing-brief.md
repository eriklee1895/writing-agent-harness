# Writing Brief

**Working title:** Jev：AI 开始不说话，只做决定

**One-line idea:** Jev 是 TypeSafe AI 的 System One 决策模型：不生成文本，只把有边界的判断和概率交给代码。

**Central question:** 一个不生成文本的模型，为什么会成为 Agent 系统里的新决策层？

**Target reader:** 已经在使用 LLM / Agent，但还没有实际调用过 Jev 的工程师。

**Thesis:** Jev 的价值不在于替代普通 LLM，而在于把高频、短、可枚举、可回滚的判断从生成模型里拆出来；真正的生产工作是设计 state、问题空间、阈值、确定性 gate、回退和评测。

**Primary register:** technical-blog；secondary register: agent-ai-essay。

**Anti-goals:**

- 不写成产品发布稿或“新范式”宣传稿。
- 不把官方性能倍数写成跨任务结论。
- 不把 `confidence` 当成正确率或自动授权。
- 不把 OpenRouter / 社区复刻结果混进官方直连测试。
- 不用原稿中没有本轮证据支撑的实验数字做核心论据。

**Evidence boundary:**

- Official facts: TypeSafe official docs and launch materials.
- Local tests: direct `api.typesafe.ai/v1/systemone` calls on 2026-09-21.
- Community cases: LangChain, LiteLLM, OpenJev, and independent audit, each keeping its original scope.
- Own project case: `jev-town` source review; current public version uses OpenRouter for resident calls.

**Outline:**

1. What Jev is: System One, typed decisions, and three primitives.
2. Why it is a different model species: probability as interface, parallel fan-out, and confidence-gated routing.
3. Practical value and real scenarios: routing, guardrails, RAG, extraction, monitoring, and high-frequency loops.
4. Jev Town as a local-state / two-layer-agent case study.
5. TypeSafe official API guide: HTTP, Python SDK, versioning, retries, and response fields.
6. Official direct probes and evidence boundaries.
7. Community cases, independent calibration skepticism, and open replicas.
8. Failure modes, deterministic verification boundaries, and a narrow conclusion.
