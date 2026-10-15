# 生态图表：数据与复现

资料截至：2026-10-14。图表为本文的确定性绘图产物，不使用 AI 生图。

> **最终交付快照（2026-10-15）**：全文有效视觉为 7 幅（1 张封面、6 张正文图）。其中增长统计图是确定性绘图，其余为用户选定的内置 imagegen 信息图。以下生成过程记录中的数量属于当时版本；当前使用状态与归档路径以 [manifest.json](manifest.json) 为准。

本机已归档实际使用的 7 个 PNG（含增长图渠道副本）和增长 SVG；PNG 工作路径保留相对软链接，SVG 继续由 Git 追踪。[交付与恢复说明](../delivery-notes.md)记录渠道链接及跨机器恢复方法。

## 图 1：AG-UI 目录中的受支持后端

指标是 **上游 README 记录为 Supported 的后端框架 / SDK 数量**。

| 截止日 | 数量 | 实际 README 提交日期（UTC） | 固定来源 |
| --- | ---: | --- | --- |
| 2025-12-31 | 10 | 2025-12-29 | [1ab1f2d4](https://github.com/ag-ui-protocol/ag-ui/blob/1ab1f2d4bff2eed48e917313e8323de3589cc122/README.md) |
| 2026-03-31 | 11 | 2026-03-26 | [0bffef9c](https://github.com/ag-ui-protocol/ag-ui/blob/0bffef9c14d32ba3da4cf03806c253a1251d9ab7/README.md) |
| 2026-06-30 | 12 | 2026-04-28 | [d49eb382](https://github.com/ag-ui-protocol/ag-ui/blob/d49eb3820cc7164679c6921819e88efa0e7616c0/README.md) |
| 2026-09-30 | 13 | 2026-08-19 | [27b4150c](https://github.com/ag-ui-protocol/ag-ui/blob/27b4150cf5dc86d29a778a6a461e39f58309761f/README.md) |
| 2026-10-14 | 15 | 2026-10-13 | [d3c1146e](https://github.com/ag-ui-protocol/ag-ui/blob/d3c1146e2c0788dd800f4fbc91ea8c8f0bb8ad31/README.md) |

### 统一口径

1. 只取 Frameworks 区块内标为 Supported 的外部后端条目。
2. LangGraph 与后续改名的 LangChain 合并为一项。
3. AWS Bedrock AgentCore 是部署平台，曾出现在 Frameworks、后又移出，因此所有快照均排除。此举避免分类迁移造成虚假增长或下降。
4. 排除内置 Agent / Direct-to-LLM、A2A、Oracle Agent Spec、生成式 UI 规范、语言 SDK、客户端与部署平台。
5. 排除 In Progress 和 Help Wanted。社区集成计入，但不称为厂商原生支持。
6. 后端不同语言的绑定不重复计数。本指标衡量有限目录内的覆盖范围，不是全行业框架总量。
7. README 更新可能滞后。快照日期不代表新集成首次发布日，目录记录不代表真实生产采用、完整互通或市场份额。

### 当前 15 项

AG2、AWS Strands Agents、Agno、Claude Agent SDK、Claude Managed Agents SDK、Cloudflare Agents、CrewAI、Google ADK、Google Antigravity、LangChain / LangGraph、Langroid、LlamaIndex、Mastra、Microsoft Agent Framework、Pydantic AI。

### 相邻快照的新记录

- 2026 Q1：Langroid。
- 2026 Q2：Claude Agent SDK。
- 2026 Q3：Claude Managed Agents SDK。
- 2026-10-14：Google Antigravity、Cloudflare Agents。

采用离散柱状图，纵轴从零开始；不对快照之间的增长时点作线性插值。

## 图 2：CopilotKit 产品生态

此图按用户界面、开发工作流、生产与渠道、应用与学习四类整理当前公开产品。它是结构示意，不是产品成熟度评分或市场规模图。

- 四类前端 SDK / 绑定：React、Vue、Angular、React Native。以官方 Vue API 和 Angular / React Native 公告、当前 SDK 文档核对。
- 开发工具：CLI、Inspector、aimock；各有不同定位。
- 生产与渠道：Intelligence 与 Channels；Slack / Teams 正式提供，不能把其他 coming soon 渠道计入 GA 数量。
- 应用与学习：OpenBot、Open Intelligent UI、CLiF；CLiF 产品操作轨迹 early access。
- AG-UI 是开放协议，不因它出现在图中就将所有独立实现归为 CopilotKit 的自有产品。

源页面与日期见文章正文及 [sources.md](../sources.md)。

## 文件与复现

- [agui-ecosystem-data.json](agui-ecosystem-data.json)：完整计数规则、各快照条目、固定 SHA 与来源 URL。
- [agui-ecosystem-data.csv](agui-ecosystem-data.csv)：图 1 的五个数据点和提交信息。
- [github-snapshot.json](github-snapshot.json)：正文使用的两仓库关注度快照，不能相加作为独立用户数。
- [build_ecosystem_data.py](build_ecosystem_data.py)：从本机研究缓存或固定 SHA 的公开 README 重新计算。
- [render_figures.py](render_figures.py)：读取本地数据，生成 SVG 与 PNG。
- 两张 SVG 为正文引用；PNG 是方便查看和渠道派生的本机副本，受全局二进制忽略规则覆盖。

在 repo 根目录执行：

```sh
uv run content/origin/2026-10-14-copilotkit-ag-ui/assets/build_ecosystem_data.py
uv run content/origin/2026-10-14-copilotkit-ag-ui/assets/render_figures.py
```

绘图依赖使用 PEP 723 声明。当前字体优先使用 macOS Hiragino Sans GB；其他系统需安装中文字体再调整脚本字体配置。SVG 输出将字体转路径，查看时不依赖本机字体。

## 核对范围

数据计数已与每个固定 README 的条目逐项核对，绘图基于本地 JSON；SVG / PNG 已渲染并检查。图表不构成 SDK 兼容、客户收入或生产部署验证。

## 已停用的氛围图（保留生成记录）

使用用户指定的 gpt-image-api skill，通过 OFOX 的 OpenAI-compatible Images API 生成两幅概念插图，模型为 gpt-image-2.5-flare，quality=auto。两次请求均成功，实际返回尺寸与请求一致。

- [hero-editorial.png](hero-editorial.png)：2048×1152 博客封面，三个独立工作空间由共同通道连接；用于 frontmatter.cover。
- [human-agent-collaboration.png](human-agent-collaboration.png)：1536×1024 正文插图，用于“用户留下的那一半经验”一节。
- [manifest.json](manifest.json)：用途、alt、provider / model、尺寸、文件校验值与使用状态。
- [generation-jobs.jsonl](generation-jobs.jsonl)：两次请求的完整参数。
- prompts/ 下保存可单独阅读的提示词；同名 .json 保存 skill 自动输出的生成元数据。

两图已目视检查：没有可读的额外文字或品牌标志，构图和配色协调。它们是编辑概念插图，不是产品截图、流程证明或实测结果。原有两幅确定性图表继续承担数据与结构说明。

用户随后明确要求带文字、有信息量的技术配图。上述两幅氛围图现已从文章引用中移除，manifest 标为 rejected_by_user；文件保留，不删除。

## 当前采用的技术信息图

- [hero-technical-v2.png](hero-technical-v2.png)：AG-UI 连接层概览；区分开放协议、CopilotKit 产品栈、用户界面及 Intelligence 平台服务。
- [clif-information-flow-v2.png](clif-information-flow-v2.png)：两侧轨迹 → 分析与技能建议 → 人工审阅 → 应用到 Agent；标注用户操作轨迹 early access，分开列出评估与训练材料的延伸方向。
- 本轮按用户指定的 imagegen skill 使用内置 image_gen 工具，未走 CLI。精确模型 ID 未由工具披露，不沿用上一轮 Flare / OFOX 的模型记录。
- 两图先生成，再针对文字与连线定向编辑；封面追加一次标签修正，将“可选服务”改为“平台服务”，避免把不同配置的服务依赖一概标成可选。初始与编辑提示词保存在 prompts/，同名 JSON 保存尺寸、校验值和视觉核对记录。
- 两张确定性证据图继续使用，全文有效视觉仍为四张。

## 后续补充的两幅信息图

- [protocol-scopes-acp-v2.png](protocol-scopes-acp-v2.png)：五种协议的连接对象与侧重，补入 Agent Client Protocol，并突出 ACP 与 AG-UI 的能力重叠。原四行 protocol-scopes.png 已被替换，manifest 标记 superseded。放在“让后端与界面各自演进”之后。
- [company-development-paths.png](company-development-paths.png)：两家公司各自按时间排序的发展节点；保留早期 Cloud beta 与 CLiF early access 的区分，不将位置等同为同一时间尺度。放在 LangChain 类比一节，替代重复的成长对照表。
- 两图均为用户要求的内置 image_gen 产物，图内文字与结构已核对；提示词、同名元数据和 manifest 记录已保存。全文当前有效视觉为六张：一张封面、五张正文图。

## 产品生态图重设计

用户不满意旧版四条横向列表。当前改用 [copilotkit-ecosystem-v2.png](copilotkit-ecosystem-v2.png)：以 CopilotKit 为中心、四类产品分组的总览，保留十二个产品标签和 CLiF 用户操作轨迹 early access 标识。连线只表示分组关系，不表示运行依赖或数据流。

使用内置 image_gen 重新生成，提示词见 [copilotkit-ecosystem-v2.txt](prompts/copilotkit-ecosystem-v2.txt)，尺寸和校验记录见同名 JSON。旧 copilotkit-ecosystem-map.svg 与渲染脚本保留为历史记录，文章不再引用；增长数据图仍使用确定性 SVG。

## 末节收尾图

[open-ecosystem-business.png](open-ecosystem-business.png)用于“开放之后，生意从哪里来”：开放生态引入开发者，生产阶段可自建、选择其他产品或购买平台服务；列出核心流程、独立实现协作、跨前端付费三个观察点。箭头表示可能路径，不代表已验证的商业转化率或收入。提示词、同名 JSON 和 manifest 均已保存。

