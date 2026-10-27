# SpaceX–Cursor 文章视觉方案

## 原则

- 全部服务于理解，不使用氛围插图。
- 视觉风格：financial editorial infographic / flat vector / Swiss grid / white or off-white surface / charcoal ink / restrained blue-green-orange accents。
- 1536×1024（3:2）正文图；封面另按博客 hero 使用相同比例，保持系列统一。
- 手机阅读优先：短标签、大字号、少节点；复杂表格和精确长文本交给 HTML。
- Logo 按语义出现，不堆满每张图；马斯克只用单人线性肖像或标识，不做多人场景。
- 所有数字、标签、箭头关系必须逐张验收；每张图保留 prompt 与 CLI metadata。
- 生图统一使用 `gpt-image-2.5-sunburst`，先 `quality=auto`，只有观察到具体质量问题才调整。

## 章节映射

| 章节 | 载体 | 内容 |
| --- | --- | --- |
| Cover | `hero-cover-v2.png` | SpaceX 股票作为收购货币，600 亿美元问题入口；品牌与股权交换结构 |
| Home lead | `hero-cover-v2-wechat-regenerated.png` | 首页复用微信原生 2.35:1 regenerate；主标题、股票关系和三项标签保留，桌面与手机均完整显示，不做低裁；文章 hero 不变 |
| 1. 收购前 Cursor | `ch01-growth-constraints.png` | 高增长与算力/模型成本/竞争约束；不把不同收入口径连成增长曲线 |
| 2. SpaceX 动因 | `ch02-strategic-fit-v2.png` | SpaceX/xAI/Grok/X 与 Cursor 的双向互补， Musk 单元素 |
| 3. 专业术语 | `ch03-stock-acquisition-terms.png` | 怎么付、为何此时付、两种理论解释；股票支付不等于必然高估或收割 |
| 4. 合同账 | `ch04-vwap-exchange-ratio.png` + `acquisition-timeline.html` | 假设算例说明固定隐含价值与浮动股数；HTML 展示 4→10 月交易时间线 |
| 5. 兑现账 | `shareholder-liquidity.html` | 不同股东/RSU/Revest/二级投资者的权益和限制，三个价格时点，注册不等于销售 |
| 6. 会计账 | `ch06-three-prices.png` | 600 亿、424.74 亿、233.76 亿及 366.46 亿商誉，明确不可相加 |
| 7. 谁承担风险 | `ch07-risk-allocation.png` | 老股东、Cursor 股东、员工、SpaceX、二级市场各自成本与风险 |
| 8. 全链条未来 | `ch08-orbital-full-stack-v2.png` + `spacex-full-stack.html` | 当前产品整合、地面算力、2028 初始部署预期与长期 100GW 目标分层 |
| Closing | `closing-starship-orbital-dawn.png` | 无字宽幅艺术性想象图：Starship、地球晨线与轨道卫星星座，作为全文视觉收尾 |

## HTML 交互

- 同源 `/embeds/2026-10-26-spacex-cursor-stock-deal/*.html`，自包含、无外部依赖。
- 支持键盘、按钮点击、移动端堆叠、亮暗主题、reduced motion；正文即使无 JS 也有核心信息。
- 不使用生图 Logo 代替 HTML 中的精确文字；HTML 主要使用简洁文字徽章，避免不准确的品牌图形。
- 不把计划写成已发生，不把注册写成实际销售，不把不同价格时点混用。

## 验收门槛

1. 文字逐项与 allowlist 对照，禁止额外可读文案、假数据、虚构 Logo 或错误箭头。
2. 视觉检查整张图，不只看构图；中文错字、数字错误、Logo 变形均判失败。
3. 生图不用于承载长段落、复杂表格或精确多层级小字。
4. HTML 通过桌面/移动、亮/暗、键盘和 console 检查；文章 MDX 构建后再检查实际 iframe。

## 微信 Cover 派生与再生对比（2026-10-27）

- 母版：`hero-cover-v2.png`，不改变 Blog hero / OG。
- `hero-cover-v2-wechat-crop.png`：1080×460 center crop。1080×460、900×383、360×153 三个尺寸均切掉主标题与底部分析标签，**rejected**。
- `hero-cover-v2-wechat-pad.png`：1080×460 contain/pad。保留完整构图，曾通过基线验收；但与原生再生版同尺寸比较后，标题和视觉重心偏弱，降为 **superseded 备选**。
- `hero-cover-v2-wechat-regenerated.png`：原生 1728×736 重新构图，使用原 Prompt、标题修正与 crop/pad 失败原因。主标题、股票关系和三项标签在小卡上更有冲击力，用户确认 **used / visual_review approved**。电脑前人物接受为 Cursor 开发者工作流提示，不再额外精修。
- QA 对照：`previews/wechat-cover-candidates-qa.png` 与 `previews/wechat-pad-vs-regenerated-qa.png`。
- 本轮确定的效果原则：模型调用成本低时，crop/pad 只作快速基线；原生再生是常规优化路径，以实际展示效果而非最少调用次数决定最终版本。

## 微信公众号原生排版（2026-10-27）

- 长截图只作过渡 QA，不作为最终公众号交付。用户反馈长图在手机阅读体验不佳后，三部分全部改为原生 HTML 短卡片。
- 时间线：6 个短节点，替代宽表与长图。
- 股东：3 个价格卡 + 6 个身份卡 + 边界说明。
- 全链条：当前事实、公司规划、验收指标三个短分区，不再拆成三张长图。
- 最终渠道 HTML：`content/wechat/2026-10-26-spacex-cursor-stock-deal/index.wechat-preview.html`。白底 `agent-flow`，390px 无横向溢出，正文图片 8 张，封面使用 regenerate。
- 最新原生排版草稿已由用户在微信公众号后台手工正式发布；早期长图草稿保留，未删除。
