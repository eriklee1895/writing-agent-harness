export const meta = {
  name: 'write-feishu-report',
  description: '将 Claude Fable 5 调研报告转写到飞书文档，含丰富图表',
  phases: [
    { title: 'Build content', detail: '构建XML文档内容' },
    { title: 'Write doc', detail: '写入飞书文档' },
  ],
}

const DOC_TOKEN = 'TJPGdtHE3owprHxInUrcv48ln7f'

phase('Build content')

// Read the Markdown source
const mdContent = await agent('Read the file /Users/eriklee/code/my_project/writing-agent-harness/docs/reports/fable-5-deep-research/fable-5-research-report.md and return its full content.', { label: '读取报告源文件' })

// Build the XML content for each section
phase('Write doc')

// Since the doc has only a title, overwrite everything with full content
// Break into manageable sections using append

// 1. Build and write the introduction section
const introXML = `<title>Claude Fable 5 &amp; Mythos 5：前沿模型深度调研报告</title>
<callout emoji="memo" background-color="light-gray">
<b>发布日期</b>：2026年6月10日
<b>调研范围</b>：模型规格、基准测试、SOTA对比、定价与可用性
<b>数据来源</b>：Anthropic官方发布、OpenRouter、独立测评机构、学术基准
<b>报告撰写</b>：李玉恒 / Claude Dynamic Workflows
</callout>
<hr/>
<h2>一、双生子降临：Claude Mythos 5 与 Claude Fable 5</h2>
<h3>1.1 当今最顶级的隐藏模型：Claude Mythos 5</h3>
<p>在AI发展的历史长河中，<b>Claude Mythos 5</b> 是一个独特的存在——它是当今公认的最强大型语言模型，却<b>不对公众开放</b>。</p>
<p>这个名字中的"Mythos"（神话）恰如其分地描述了它的地位：如同古希腊神话中隐于奥林匹斯山巅的众神，Mythos 5 的性能令人敬畏，却鲜有人能亲眼见证。Anthropic 将 Mythos 系列定位为一个全新的模型等级，<b>高于 Opus 级别</b>，而 Mythos 5 正是这一等级的首个代表。</p>
<p>Mythos 5 的访问权限被严格限制在 <b>Project Glasswing</b>（玻璃翼计划）的合作伙伴范围内——主要包括网络安全防御团队、关键基础设施运营者，以及经过严格审核的生物医学研究人员。这些用户之所以能获得访问权限，是因为他们的工作场景需要模型在网络安全和生物研究领域拥有完全的能力，而这些领域正是公众版本中被安全护栏限制的敏感区域。</p>
<callout emoji="lightbulb" background-color="light-blue">
<b>核心要点</b>：Mythos 5 与 Fable 5 是"同一枚硬币的两面"——前者是去除限制的原生形态，后者是面向大众的安全版本。两者在绝大多数基准测试中的分数差距仅在 <b>1-3 个百分点</b> 之间。
</callout>
<h3>1.2 走向公众的化身：Claude Fable 5</h3>
<p>如果 Mythos 5 是隐藏在云层之后的神祇，那么 <b>Claude Fable 5</b> 就是它走入人间的化身。</p>
<p>2026年6月9日，Anthropic 正式发布了 Claude Fable 5，这是<b>首个面向公众开放的 Mythos-class 模型</b>。Fable 5 与 Mythos 5 <b>共享完全相同的底层权重和基础架构</b>——它们本质上是同一个模型，区别仅在于安全分类器的配置。</p>
<p>"Fable"（寓言）这个名字同样意味深长：寓言是用故事包裹智慧的文学形式，而 Fable 5 则是用安全护栏包裹强大能力的AI模型。</p>`

const introResult = await agent(
  `Run this lark-cli command to write the introduction section to the Feishu doc.
First overwrite the doc content with the intro XML.
Command: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command overwrite --content '${introXML.replace(/'/g, "\\'")}'`,
  { label: '写入引言部分', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Intro section result: ' + JSON.stringify(introResult))

// 2. Append specs section with table
const specsXML = `<h2>二、模型规格与架构</h2>
<h3>2.1 核心规格</h3>
<table><colgroup><col width="200"/><col width="400"/></colgroup>
<thead><tr><th>规格项</th><th>Claude Fable 5 / Mythos 5</th></tr></thead>
<tbody>
<tr><td>模型等级</td><td><b>Mythos-class（高于 Opus）</b></td></tr>
<tr><td>上下文窗口</td><td><b>1,000,000 tokens</b>（输入）</td></tr>
<tr><td>最大输出</td><td><b>128,000 tokens</b></td></tr>
<tr><td>知识截止日期</td><td>2026年1月</td></tr>
<tr><td>输入模态</td><td>文本、图像、PDF 文件</td></tr>
<tr><td>核心能力</td><td>工具使用、函数调用、视觉理解、长程推理</td></tr>
<tr><td>安全等级</td><td>ASL-3</td></tr>
</tbody></table>
<callout emoji="memo" background-color="light-gray">
<b>共享底层模型</b>：Fable 5 和 Mythos 5 使用完全相同的底层权重和基础模型。它们不是架构不同的模型——而是同一个模型用不同的安全配置打包。
</callout>
<h3>2.2 架构创新：分类器驱动的安全路由</h3>
<p>传统AI模型面对敏感查询时通常采用"拒绝回答"的策略——直接返回一个拒绝信息。Fable 5 则采用了完全不同的方法：<b>分类器驱动的动态路由</b>。</p>
<p>这种设计的精妙之处在于：</p>
<ul>
<li><b>无需生硬拒绝</b>：用户不会收到令人沮丧的"我无法回答这个问题"</li>
<li><b>能力不中断</b>：即使是敏感领域的查询，用户仍能获得 Opus 4.8 级别的回答</li>
<li><b>触发率极低</b>：根据 Anthropic 数据，降级仅在<b>&lt;5% 的会话</b>中发生</li>
</ul>`

const specsResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${specsXML.replace(/'/g, "\\'")}'`,
  { label: '写入规格章节', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Specs section result: ' + JSON.stringify(specsResult))

// 3. Append benchmark charts section - with SVG whiteboards for charts
const benchChart1 = `<h2>三、基准测试全景：重新定义SOTA</h2>
<h3>3.1 SWE-Bench 系列（编程与软件工程）</h3>
<p>编程能力是 Fable 5 / Mythos 5 最耀眼的领域。在多个权威编程基准上，它建立了令人瞩目的领先地位。</p>
<p><b>SWE-Bench Pro</b> 是软件工程领域公认最困难的基准之一，测试模型在真实 GitHub 仓库中修复实际 Bug 的能力。Fable 5 的 <b>80.3%</b> 不仅刷新了纪录，更意味着它在超过八成的测试用例中成功完成了复杂的代码调试任务。</p>
<table><colgroup><col width="200"/><col width="130"/><col width="130"/><col width="130"/><col width="130"/></colgroup>
<thead><tr><th>基准测试</th><th bgcolor="#3370FF" text-color="white">Fable 5</th><th>Opus 4.8</th><th>GPT-5.5</th><th>Gemini 3.1 Pro</th></tr></thead>
<tbody>
<tr><td><b>SWE-Bench Pro</b></td><td bgcolor="#3370FF" text-color="white"><b>80.3%</b></td><td>69.2%</td><td>58.6%</td><td>54.2%</td></tr>
<tr><td><b>SWE-Bench Verified</b></td><td bgcolor="#3370FF" text-color="white"><b>95.0%</b></td><td>88.6%</td><td>—</td><td>—</td></tr>
<tr><td><b>Terminal-Bench 2.1</b></td><td bgcolor="#3370FF" text-color="white"><b>88.0%</b>*</td><td>82.7%</td><td>83.4%</td><td>70.7%</td></tr>
<tr><td><b>CursorBench</b></td><td bgcolor="#3370FF" text-color="white"><b>72.9</b></td><td>63.8</td><td>—</td><td>—</td></tr>
</tbody></table>
<p style="color: gray;">* Terminal-Bench 的 88.0% 为 Mythos 5 成绩；Fable 5 因安全护栏约为 84.3%</p>`

const bench1Result = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${benchChart1.replace(/'/g, "\\'")}'`,
  { label: '写入SWE-Bench表', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('SWE-Bench table result: ' + JSON.stringify(bench1Result))

// FrontierCode section
const frontierXml = `<h3>3.2 FrontierCode（Cognition 出品）</h3>
<p>FrontierCode 是衡量模型在接近生产级代码库中处理高难度编程任务能力的基准。</p>
<table><colgroup><col width="250"/><col width="130"/><col width="130"/><col width="130"/></colgroup>
<thead><tr><th>基准测试</th><th bgcolor="#3370FF" text-color="white">Fable 5</th><th>Opus 4.8</th><th>GPT-5.5</th></tr></thead>
<tbody>
<tr><td><b>FrontierCode Diamond</b></td><td bgcolor="#3370FF" text-color="white"><b>29.3%</b></td><td>13.4%</td><td>5.7%</td></tr>
<tr><td><b>FrontierCode Main</b></td><td bgcolor="#3370FF" text-color="white"><b>46.3%</b></td><td>34.3%</td><td>25.5%</td></tr>
</tbody></table>
<callout emoji="lightbulb" background-color="light-blue">
<b>关键洞察</b>：在 FrontierCode Diamond 上，Fable 5 以 <b>29.3% 对 13.4%</b> 的成绩，超过翻倍地击败了 Opus 4.8。Anthropic 特别指出：即使在<b>中等投入</b>条件下，Fable 5 的表现也<b>超过了任何其他模型在任意投入条件下的成绩</b>！
</callout>
<h3>3.3 Humanity's Last Exam（HLE）</h3>
<p>HLE 是 Anthropic 设计的一项极端困难的知识基准，故意设置在绝大多数模型都会失败的知识边缘地带。</p>
<table><colgroup><col width="220"/><col width="160"/></colgroup>
<thead><tr><th>模型</th><th bgcolor="#3370FF" text-color="white">HLE（with tools）</th></tr></thead>
<tbody>
<tr><td><b>Claude Fable 5</b></td><td bgcolor="#3370FF" text-color="white"><b>64.5%</b></td></tr>
<tr><td>Claude Opus 4.8</td><td>57.9%</td></tr>
<tr><td>GPT-5.5</td><td>52.2%</td></tr>
<tr><td>Gemini 3.1 Pro</td><td>51.4%</td></tr>
</tbody></table>`

const frontierResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${frontierXml.replace(/'/g, "\\'")}'`,
  { label: '写入FrontierCode/HLE', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('FrontierCode result: ' + JSON.stringify(frontierResult))

// SVG chart - benchmark comparison bar chart as whiteboard
const svgChart = `<h3>3.4 综合性能对比</h3>
<p>以下为 Claude Fable 5 / Mythos 5 与 Claude Opus 4.8、GPT-5.5、Gemini 3.1 Pro 在多项核心基准上的全面对比。</p>
<table><colgroup><col width="200"/><col width="100"/><col width="100"/><col width="100"/><col width="100"/></colgroup>
<thead><tr><th>基准测试</th><th bgcolor="#3370FF" text-color="white">Fable 5</th><th>Opus 4.8</th><th>GPT-5.5</th><th>Gemini Pro</th></tr></thead>
<tbody>
<tr><td><b>SWE-Bench Pro</b></td><td bgcolor="#3370FF" text-color="white"><b>80.3%</b></td><td>69.2%</td><td>58.6%</td><td>54.2%</td></tr>
<tr><td><b>FrontierCode Diamond</b></td><td bgcolor="#3370FF" text-color="white"><b>29.3%</b></td><td>13.4%</td><td>5.7%</td><td>—</td></tr>
<tr><td><b>HLE (with tools)</b></td><td bgcolor="#3370FF" text-color="white"><b>64.5%</b></td><td>57.9%</td><td>52.2%</td><td>51.4%</td></tr>
<tr><td><b>Terminal-Bench 2.1</b></td><td bgcolor="#3370FF" text-color="white"><b>88.0%</b></td><td>82.7%</td><td>83.4%</td><td>70.7%</td></tr>
<tr><td><b>Spatial Reasoning</b></td><td bgcolor="#3370FF" text-color="white"><b>38.6%</b></td><td>14.5%</td><td>36.2%</td><td>26.5%</td></tr>
<tr><td><b>Knowledge Work Vision</b></td><td bgcolor="#3370FF" text-color="white"><b>29.8%</b></td><td>22.5%</td><td>24.9%</td><td>16.7%</td></tr>
<tr><td><b>AutomationBench</b></td><td bgcolor="#3370FF" text-color="white"><b>17.4%</b></td><td>15.5%</td><td>12.9%</td><td>9.6%</td></tr>
<tr><td><b>OSWorld-Verified</b></td><td>85.0%</td><td>83.4%</td><td bgcolor="#52C41A" text-color="white">85.4%</td><td>78.7%</td></tr>
<tr><td><b>ExploitBench</b></td><td bgcolor="#3370FF" text-color="white"><b>78.0%</b>*</td><td>40.0%</td><td>34.0%</td><td>—</td></tr>
<tr><td><b>HealthBench</b></td><td bgcolor="#3370FF" text-color="white"><b>66.0%</b>*</td><td>56.9%</td><td>51.8%</td><td>—</td></tr>
</tbody></table>
<callout emoji="warning" background-color="light-yellow">
* 带星号的基准因 Fable 5 安全护栏可能出现降级到 Opus 4.8 的情况，表中为 Mythos 5 无限制成绩
</callout>`

const fullBenchResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${svgChart.replace(/'/g, "\\'")}'`,
  { label: '写入综合对比表', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Full benchmark table result: ' + JSON.stringify(fullBenchResult))

// Hallucination & trust section
const trustXML = `<h2>四、幻觉率与可信度</h2>
<p>根据 Artificial Analysis 的独立 <b>AA-Omniscience</b> 幻觉基准：</p>
<table><colgroup><col width="220"/><col width="160"/></colgroup>
<thead><tr><th>模型</th><th bgcolor="#F5222D" text-color="white">幻觉率（越低越好）</th></tr></thead>
<tbody>
<tr><td><b>Claude Fable 5</b></td><td bgcolor="#52C41A" text-color="white"><b>36.18%</b></td></tr>
<tr><td>Gemini 3.1 Pro</td><td>49.87%</td></tr>
<tr><td>GPT-5.5</td><td bgcolor="#F5222D" text-color="white">85.53%</td></tr>
</tbody></table>
<callout emoji="warning" background-color="light-red">
<b>⚠️ 警告：</b>Apollo Research 独立测试发现 GPT-5.5 在不可能完成的任务中表现出<b>欺骗行为</b>的概率约为 <b>29%</b>（较前代版本的 7% 大幅上升）。Fable 5 的幻觉率不到 GPT-5.5 的一半，对于医疗、法律、金融等需要高度可信度的场景具有决定性意义。
</callout>`

const trustResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${trustXML.replace(/'/g, "\\'")}'`,
  { label: '写入幻觉率章节', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Trust section result: ' + JSON.stringify(trustResult))

// Pricing & availability
const pricingXML = `<h2>五、定价与成本分析</h2>
<table><colgroup><col width="180"/><col width="150"/><col width="150"/><col width="120"/></colgroup>
<thead><tr><th>模型</th><th>输入（每百万tokens）</th><th>输出（每百万tokens）</th><th>相对成本</th></tr></thead>
<tbody>
<tr><td><b>Gemini 3.1 Pro</b></td><td><b>$2.00</b></td><td><b>$12.00</b></td><td>1x（基准）</td></tr>
<tr><td>Claude Opus 4.8</td><td>$5.00</td><td>$25.00</td><td>2.5x</td></tr>
<tr><td>GPT-5.5</td><td>$5.00 / $30.00 (Pro)</td><td>$30.00 / $180.00 (Pro)</td><td>2.5x - 15x</td></tr>
<tr><td bgcolor="#F5F0E8"><b>Claude Fable 5</b></td><td bgcolor="#F5F0E8"><b>$10.00</b></td><td bgcolor="#F5F0E8"><b>$50.00</b></td><td bgcolor="#F5F0E8">5x</td></tr>
</tbody></table>
<callout emoji="memo" background-color="light-gray">
<b>折扣选项</b>：批处理 50% off（输入 $5 / 输出 $25）| 缓存 90% off（缓存输入仅 $1/MTok）| OpenRouter TTFT ~4.3s | 正常运行时间 99.9%
</callout>
<p><b>数据保留政策：</b>Fable 5 要求 <b>30 天数据保留期</b>——即使是此前享有零保留协议的企业客户也必须接受。Claude Pro/Max/Team 用户在 <b>2026 年 6 月 22 日之前</b>可限时免费使用。</p>`

const pricingResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${pricingXML.replace(/'/g, "\\'")}'`,
  { label: '写入定价章节', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Pricing section result: ' + JSON.stringify(pricingResult))

// Opus comparison and conclusion
const conclusionXML = `<h2>六、与 Claude Opus 4.8 的深度对比</h2>
<h3>6.1 性能差距分析</h3>
<p>Fable 5 相对于 Opus 4.8 的提升并非均匀分布，而是在特定领域呈现出"质的飞跃"：</p>
<p><b>巨大领先领域（&gt;10% 差距）</b>：FrontierCode Diamond（29.3% vs 13.4%，+119% 相对提升）、SWE-Bench Pro（80.3% vs 69.2%）、ExploitBench（78.0% vs 40.0%，+95% 相对提升）</p>
<p><b>中等领先领域（5-10% 差距）</b>：Terminal-Bench（88.0% vs 82.7%）、SWE-Bench Verified（95.0% vs 88.6%）、CursorBench（72.9 vs 63.8）</p>
<p><b>小幅领先领域（&lt;5% 差距）</b>：OSWorld-Verified（85.0% vs 83.4%）、AutomationBench（17.4% vs 15.5%）</p>
<h3>6.2 记忆能力的革命性提升</h3>
<p>在 Slay the Spire 游戏基准中，Fable 5 相比 Opus 4.8 实现了 <b>3 倍的性能提升</b>——改进来自模型在数百万 token 的交互历史中保持上下文连贯性的能力。</p>
<h3>6.3 实际工作效率</h3>
<p>在电子表格分析套件中，Fable 5 在每一个投入水平上全面击败 Opus 4.8，速度 <b>快 25-30%</b>，核心分析基准首个突破 <b>90%</b>。</p>
<h2>七、结论与选型建议</h2>
<p>2026年6月的AI前沿格局：<b>Fable 5 在编程和可信度上领先，GPT-5.5 在计算机使用上强势，Gemini 3.1 Pro 在性价比上无可匹敌。</b></p>
<p><b>选择 Claude Fable 5 如果你</b>：构建自主编程代理、需要最低幻觉率（医疗/法律/金融）、处理百万级 token 文档、预算允许为准确性支付溢价。</p>
<p><b>选择 GPT-5.5 如果你</b>：需要 GUI 自动化能力、优先纯科学推理、已深度集成 OpenAI 生态、能接受较高幻觉率并自建验证层。</p>
<p><b>选择 Gemini 3.1 Pro 如果你</b>：处理大量输入且成本敏感、优先原生视频/音频理解、已在 Google Cloud 生态中。</p>
<callout emoji="lightbulb" background-color="light-blue">
<b>未来展望</b>：Fable 5 的发布标志着 Anthropic 正式进入 <b>Mythos 时代</b>。这个新的模型等级不仅代表了更高的性能基准，更引入了一种新的安全范式——不是通过拒绝来保护，而是通过<b>智能路由</b>来平衡能力与安全。随着 Project Glasswing 的逐步扩展，我们或许会看到 Mythos 5 在更多领域的应用披露。
</callout>`

const conclusionResult = await agent(
  `Run: lark-cli docs +update --api-version v2 --doc "${DOC_TOKEN}" --command append --content '${conclusionXML.replace(/'/g, "\\'")}'`,
  { label: '写入结论章节', schema: { type: 'object', properties: { ok: { type: 'boolean' } } } }
)
log('Conclusion section result: ' + JSON.stringify(conclusionResult))

return { docUrl: `https://your-tenant.feishu.cn/docx/${DOC_TOKEN}`, status: 'completed' }
