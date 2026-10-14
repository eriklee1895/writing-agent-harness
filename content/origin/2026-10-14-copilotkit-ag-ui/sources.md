# 来源与编辑核对记录

资料核对日期：2026-10-14（Asia/Shanghai）。状态：初稿编辑记录，非发布验收。

## 证据使用边界

- 框架与云平台资料用于确认文档化的接入支持，未做运行兼容测试。
- 1.0 正式发布与冻结日使用维护者 9 月 18 日记录，区分 9 月 30 日博客公告。
- 公司与投资方的产品、收入主张保留明确归因；没有可核验的 ARR 或续费数据。
- CLiF 以 Agent 轨迹已可用、产品操作轨迹 early access 的官方区分描述，不引用未复现的效果数字。
- Agno 的兼容问题来自维护方更新，本文未复现；Thoughtworks 是外部工程评价。
- 公司成长、标准化价值和商业路径为作者分析，不写成已发生的经营结果。
- 本文引用公开原始来源；ChatGPT 分享对话仅用于发现线索，不作为事实结论来源。

## 正文引用的原始来源

1. [Copilot 开发工具](https://www.geekwire.com/2026/seattles-copilotkit-raises-27m-as-some-of-the-biggest-names-in-tech-adopt-its-ai-agent-protocol/)
2. [投资文章](https://glilotcapital.com/cyberhubs/why-we-led-copilotkits-27m-series-a-building-the-user-interface-layer-for-the-agentic-era/)
3. [1.0 规范](https://docs.ag-ui.com/spec/1.0)
4. [Google A2UI v0.9 展示经 AG-UI 连接不同框架](https://developers.googleblog.com/a2ui-v0-9-generative-ui/)
5. [ACP 官方介绍](https://agentclientprotocol.com/get-started/introduction)
6. [协议概览](https://agentclientprotocol.com/protocol/v1/overview)
7. [AWS AgentCore Runtime 支持 AG-UI](https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-bedrock-agentcore-runtime-ag-ui-protocol/)
8. [CrewAI](https://www.copilotkit.ai/blog/crewai-is-fully-agui-compatible)
9. [Mastra](https://www.copilotkit.ai/blog/mastra-agui-compatible)
10. [AG-UI 1.0 正式发布并冻结](https://github.com/ag-ui-protocol/ag-ui/discussions/2792)
11. [官方介绍微软贡献的第一方 .NET SDK](https://www.copilotkit.ai/blog/agui-dotnet-sdk)
12. [Microsoft](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/)
13. [Google ADK](https://adk.dev/integrations/ag-ui/)
14. [LangChain](https://docs.langchain.com/oss/python/deepagents/ag-ui)
15. [Pydantic AI](https://pydantic.dev/docs/ai/integrations/ui/ag-ui)
16. [Agno](https://docs.agno.com/agent-os/interfaces/ag-ui/introduction)
17. [assistant-ui](https://www.assistant-ui.com/docs/runtimes/ag-ui/overview)
18. [Mastra 的教程](https://mastra.ai/integrations/agentic-ui/openui)
19. [Angular 公告](https://www.copilotkit.ai/blog/copilotkit-for-angular)
20. [Vue 文档](https://docs.copilotkit.ai/reference/vue)
21. [Enterprise Intelligence 平台介绍](https://www.copilotkit.ai/blog/copilotkit-enterprise-intelligence-platform)
22. [Channels SDK](https://www.copilotkit.ai/blog/channels-sdk)
23. [React Native SDK 公告](https://www.copilotkit.ai/blog/react-native-your-agent-inside-your-mobile-app)
24. [WebMCP 接入](https://www.copilotkit.ai/blog/introducing-webmcp-for-copilotkit)
25. [Inspector 更新](https://www.copilotkit.ai/blog/inspector-upgrades)
26. [Open Intelligent UI](https://www.copilotkit.ai/blog/introducing-open-intelligent-ui)
27. [aimock](https://www.copilotkit.ai/blog/aimock-model-misbehavior)
28. [OpenBot](https://www.copilotkit.ai/openbot)
29. [CopilotKit 仓库](https://github.com/CopilotKit/CopilotKit)
30. [AG-UI 仓库](https://github.com/ag-ui-protocol/ag-ui)
31. [LangSmith 以 closed beta 发布](https://www.langchain.com/blog/announcing-langsmith)
32. [LangGraph 的发布介绍](https://www.langchain.com/blog/langgraph)
33. [LangGraph Cloud](https://www.langchain.com/blog/langgraph-cloud)
34. [v1.0 公告](https://www.copilotkit.ai/blog/copilotkit-v1-launch)
35. [三年回顾](https://www.langchain.com/blog/three-years-langchain)
36. [Channels 产品页](https://www.copilotkit.ai/channels)
37. [定价页](https://www.copilotkit.ai/pricing)
38. [CLiF 的发布说明](https://www.copilotkit.ai/blog/introducing-clif)
39. [v2](https://www.langchain.com/blog/langsmith-engine-v2-redteam)
40. [Agno 9 月 23 日的更新](https://www.agno.com/articles/the-ag-ui-interface-supports-ag-ui-protocol-1-0)
41. [Thoughtworks 的技术雷达](https://www.thoughtworks.com/en-br/radar/platforms/ag-ui-protocol)

## 本轮生态与轨迹补充

- AG-UI 历史计数、五个固定 README 提交及排除规则见 [assets/README.md](assets/README.md)。
- 10→15 是去重后的目录覆盖数；不混入云平台、语言绑定和进行中项目，不外推市场份额。
- GitHub 关注度快照记录在 [github-snapshot.json](assets/github-snapshot.json)。
- CopilotKit v1（2024-07-08）已有 Cloud beta；不能写成 2026 年才开始商业化。
- LangSmith（2023-07-18）早于 LangGraph（2024-01-17）发布；发展轨迹相似不等于产品推出顺序相同。
- 产品生态图是当前产品范围的结构示意，CLiF 产品操作轨迹 early access；各节点不视为同等成熟。

## 文稿状态

正文已按随笔叙述与行业洞察润色。按用户反馈删去法律主体及核验过程说明，正文现引用 41 个来源。原有增长数据图保留，产品生态图已按用户要求重新生成；氛围图已停用，当前使用内置 image_gen 生成的连接层概览封面、CLiF 信息流、协议职责对比、公司发展轨迹对照，共六幅视觉。图内文字、日期、箭头及成熟度区分已目视检查。生成与修改提示词、文件校验值见 assets/manifest.json。标题已由用户确认为“CopilotKit: 会成为下一个LangChain吗？”。

## ACP 补充核查（2026-10-14）

- ACP 在本文指 Agent Client Protocol。官方介绍以编辑器与编码 Agent 的解耦为起点；协议概览明确客户端也可以是其他 UI。
- 官方 v1 概览确认双向 JSON-RPC 方法与通知、会话、流式更新及权限请求。文件和终端是按能力协商提供的宿主功能，不能写成所有 ACP 客户端都必备。
- AG-UI 1.0 以运行输入与类型化事件流规范用户侧交互；两者在会话、更新、工具和人参与上重叠。侧重比较是基于规范的分析，不是互斥分类。
- 不将 ACP 写成只能用于 IDE，也不把 AG-UI 写成客户端交互层的唯一协议。原四行图已停用，替换为五行图，总视觉数量仍为六张。

## 本轮文字精修（2026-10-14）

- 沿用随笔叙述与行业洞察，保留用户确认的标题、两个指定小标题与全部章节顺序。
- 收紧重复的协议价值说明、泛泛感想与来源核查口吻；CLiF 的定义和可用性先于例子与信息图出现。
- 结尾直接回应公司成长问题，区分已具备的条件与尚待验证的经营结果。
- 原有 41 个来源链接、数据、图片引用保持；未新增事实、模型调用或发布动作。
