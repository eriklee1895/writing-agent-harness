# 2026-10-26 Claude Duet 前沿报告多渠道发布复盘

## 任务概览

- 输入：Notion 研究笔记（2026-10-22 资料截止）+ 8 个附件（6 图 + 2 交互 HTML）
- 交付：个人博客长文（已上线）+ 微信公众号稿（草稿终审通过）+ harness PR #34
- 特殊环节：16-agent deep research workflow（8 路检索 → 35 条声明对抗核查 → 完备性批评，457 次工具调用、3.4M tokens、约 42 分钟）
- 封面迭代两版后通过：无品牌抽象版被否 → 官方 Duet 图标 identity reference 多图 edit 原生重绘版

## 做对的事

1. **先研究、后写作**。Notion 原稿工程主干（auto mode 数字、Managed Agents、Tag 模型）经对抗核查全部准确，但抓到 3 处硬伤：Grok Bot 价格用了 8 月 Cursor 旧价（$120–200，实际 10-12 后 X Premium $30 起附赠）、Agent SDK「5-13 已恢复」实际是宣布日与生效日混用且 6-15 当天被暂停、以及两处被时间推翻的「安全细节未公布 / 无第三方实测」。没有这一步，三篇里会带着确定错误发布。
2. **事实分档纪律**：官方写明 / 工程判断 / 存疑三档贯穿全文，核查产出能直接映射为「标注社区佐证」「标注 VentureBeat 推断」这类定点修订。
3. **确定性渲染信息图**：公众号宽表转竖版卡片（竞品对比、安全六层、五道闸门）全部手写 HTML + Playwright @2x 截图，零错字、字号在 390px 可读；交互 embed 同法静态化（注入 CSS 隐藏 tab/播放控件再截图）。
4. **品牌标识保真**：从官方 og 图裁图标 → 多参考图 edit 让模型原生重绘，避免了「模型自己画 logo」和「PIL 硬拼」两个坑（用户明确否掉硬拼方案）。

## 失败与处理

- **图片编号引用必须独立成段**：`![图](x)正文` 同行写法导致 renderer 漏解析两张图（imageCount 4 而非 6），靠 imageCount 数字对账才发现。规则：markdown 图片独占段落，图后另起段落放正文。
- **Astro/Sharp 首构建竞态**：封面第一次 build 产出 1728×73 的坏 webp（高度 1/10），clean rebuild 后正常；发布前应逐档核对 dist webp 真实像素，不能只看 build 退出码。
- **公众号首稿仍带 `[n]` 标记**：直接沿用博客体例，用户反馈正文显乱。公众号渠道稿正文应默认无内联标记，只保留文末编号参考表。

## Contrastive

1. **与上次同类任务（10-15 Codex Cloud / 10-25 Qilin）的不同**：这是第一次在写作前跑重型对抗核查 workflow。对比以往「写完自查」模式，收益集中在时效性强的竞品事实（价格、可得性、发布日期）——这类信息靠作者记忆最容易过期；工程类主干事实反而零错误。结论：对抗核查应优先覆盖「别人的产品」而非「自己的论证」。
2. **上次 closeout 改进方向的验证**：Qilin closeout 建立的「origin canonical → 博客 adapter → public/embeds」链路本次零修改复用；embed 静态化方法（390 CSS px @DPR2、隐藏控件）是新积累，可沉淀。
3. **重复模式**：`![图](x)紧跟正文导致解析失败` 在 renderer 体系里属于第二次因图片相邻语法返工（见 2026-09-29 wechat-two-column-image-upload）。已登记为 skill staleness，建议 renderer 对「图片后紧跟非空白文本」给 warning。

## Skill / 流程建议

- wechat-article-renderer：imageCount 对账已是有效防线；补一条 markdown lint：图片语法不独占段落时告警。
- gpt-image-api：品牌 logo 场景的标准路径已验证——官方素材页 og:image 取标识 → identity-reference edit 原生重绘，比生成后合成好。值得在该 skill 或 visuals 文档补一段「brand mark in cover」。
- deep research workflow 模板（sweep/verify/critic + schema 结构化 + journal 落盘）可复用：/private/tmp 大输出改为脚本抽取 verdict/error/new-development，341K 结果不必进上下文。

## 剩余人工动作

- 公众号群发（旧草稿 appmsgid 100001525 待手动删除，终稿见 publish-status.md）
- PR #34 合并
- 观察项：Duet 进入 Team/Enterprise、打扰判断量化数据、信息流分类器误拦率
