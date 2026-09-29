# Writing Brief

**Working title:** Anthropic 的 AI-Native 实践，真正难的都在代码之外

**One-line idea:** Anthropic 的关键不是让 Claude 写更多代码，而是用可执行产物、反馈回路和硬权限重写软件交付的控制面。

**Central question:** 当 coding agent 让代码供给变得充裕，团队怎样重构从意图、设计、验证、授权到生产反馈的整条链路，既接住速度，又不放大错误？

**Target reader:** 已经在真实项目中使用 Codex、Claude Code、Cursor 等 coding agent 的工程师、技术负责人、平台工程与安全团队。

**Thesis:** AI-native SDLC 不是一套“更会提示 Claude”的技巧，也不是把传统六阶段换成六个 Markdown 文件。它是一套为非确定性执行者建立的工程控制面：稳定的权威产物负责传递状态，自动反馈负责提供证据，硬权限与风险分层负责限制动作，生产信号负责把问题送回下一轮意图。Anthropic 的方法值得学，但它对需求工程的处理偏薄，而且其 8 倍代码交付量、80% AI 编写比例都属于特殊组织条件下的内部数据，不能当成普遍生产力基准。

**Why now:** Anthropic 在 2026 年 7 月 21 日发布安全实践，8 月 21 日发布完整 Playbook。与此同时，DORA、Faros、GitHub Spec Kit 与开发者社区都从不同方向指向同一现象：代码生成更快后，瓶颈移动到需求、评审、验证和治理。

**Angle:** 不按 Plan / Design / Build / Test / Deploy / Maintain 逐章翻译，而是抽象成五个工程问题：状态如何传递、证据如何生成、权限如何约束、人的判断放在哪里、反馈如何回流。用官方图解释原方法，再用社区批评校正适用边界。

**Primary register:** Agent / AI Technical Essay

**Secondary register:** Industry / Frontier Analysis

**Anti-goals:**

- 不写成 Anthropic 产品功能清单或中文转述。
- 不把“代码交付量 8 倍”写成“工程师生产力 8 倍”。
- 不假设所有团队都已经进入“代码不再是瓶颈”的阶段。
- 不把提示词、Skills 或 `CLAUDE.md` 描述成不可绕过的安全边界。
- 不把人类参与简化成含糊的 human-in-the-loop；写清谁在什么风险下对什么决定负责。

**Key points:**

1. Amdahl 定律解释了为什么局部编码加速不等于端到端交付加速。
2. `intent.md → spec.md → plan.md → diff/tests → PR → incident` 的价值是状态传递与审计，不是 Markdown 本身。
3. Instructions、evidence、authorization 是三个不同层次；Skills 是软约束，hooks/identity/sandbox/branch protection 才是硬边界。
4. 多 agent review 的价值来自职责分离、独立上下文与可验证证据，不是“再问一次模型”。
5. 人类注意力应按风险分配到意图、架构、不可逆动作和异常，而不是平均摊在每一行代码上。
6. 社区最有力的批评是左侧需求工程不足：多利益相关者、NFR、领域模型、需求到测试的 traceability 不能被一轮对话替代。
7. 最小落地不是复制 Anthropic 全套，而是选一条低风险、重复、高可验证的 change path，建立权威产物、自动证据、明确 Gate 与回流指标。

## Draft Outline

1. Opening：代码生成只占整条交付链的一段，局部加速会暴露其他排队点。
2. 两篇官方文章合起来才完整：Playbook 讲流转，安全篇讲边界。
3. 第一层：Artifact chain——把聊天变成可追踪状态。
4. 第二层：Evidence loop——让完成由测试、构建、截图、eval 与 proof 证明。
5. 第三层：Authorization plane——软规则、确定性门禁、身份与隔离分层。
6. 第四层：Human judgment——从逐行审查转向风险和异常决策。
7. 第五层：Production feedback——事故、扫描与运行指标写回下一轮意图。
8. 社区校正：需求工程太薄、Markdown 官僚化、AI 审 AI 的相关性失败、特殊组织条件不可复制。
9. 一条适合普通团队的最小实施路径与度量表。
10. Closing：AI-native 的对象不是代码，而是整套交付系统。
