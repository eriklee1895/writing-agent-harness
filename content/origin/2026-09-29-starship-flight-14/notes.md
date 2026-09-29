# 写作约定与事实依据

## 已确认的方向

- 标题：星舰第14次试飞，向星辰大海再进一步。
- 文体：个人随笔；保留壮阔、振奋和对探索的敬意，表达自然，避免矫情。
- 结构：试飞来龙去脉、发射过程的戏剧性、壮观返回，随后抒发对 Musk 和 SpaceX 的敬意及人类探索宇宙的向往。
- 用户明确表达的体验：一度以为发射会失败，随后发生反转；感到不可思议、振奋；一直佩服 Musk 和 SpaceX 的探索精神。
- 不添加用户未提供的生活经历、观看地点、童年故事或现场动作。
- 本轮交付为完整初稿，未做渠道排版或发布。

## 2026-09-29 核对的来源

1. SpaceX，Starship Flight 14，任务日期 2026-09-28。
   https://www.spacex.com/launches/starship-flight-14
   本地研究副本：`.firecrawl/starship14-official-refresh.md`。
   - 助推器33台发动机起飞点火，其中一台在上升途中关闭。
   - 返场点火31/33台，着陆点火高推力阶段11/13台，随后逐步减少工作发动机数量。
   - 助推器着陆点火结束后触发飞行终止系统，官方称为安全硬件演示。
   - 飞船一台真空发动机提前关闭，其余五台延长工作达到预定安全亚轨道轨迹。
   - 飞控确认后续需要的三台海平面发动机健康，单台海平面发动机完成入轨点火。
   - 26颗卫星全部部署并取得联系；服务前仍需在轨检查和升轨。
   - 出于对发动机异常的谨慎，提前离轨，选择预先协调过的北太平洋溅落区。
   - 三台海平面发动机完成着陆点火与翻转，飞船在目标区域溅落。

2. Reuters，2026-09-28，Starship 首次入轨报道。
   https://www.reuters.com/business/media-telecom/spacexs-starship-launches-14th-flight-first-headed-orbit-2026-09-28/
   本地研究副本：`.firecrawl/starship14-news-selected.md`。
   - 直播解说曾宣布不再尝试入轨，几分钟后依据工程团队更新改口。
   - 任务由计划约十小时缩短至约三小时。
   - Reuters 对故障发动机的分类表述与官方不完全一致；发动机类型以官方复盘为准。

3. Spaceflight Now，2026-09-28，Starship returns to Earth; rocket splashes down north of Hawaii after three-hour flight。
   https://spaceflightnow.com/2026/09/28/starship-returns-to-earth-rocket-splashes-down-north-of-hawaii-after-three-hour-flight/
   本地研究副本：`.firecrawl/spaceflightnow-flight14-report.md`。
   - 记录再入、翻转、受控溅落，以及飞船落水后倾倒爆炸。
   - 其发射时间与官方有分钟级差异；文章采用北京时间当晚，不依赖该分钟值。

4. CNN，2026-09-28，试飞直播记录。
   https://www.cnn.com/2026/09/28/science/live-news/spacex-starship-flight-14-launch
   本地研究副本：`.firecrawl/starship14-news-selected.md`。
   - 补充再入与海面着陆演练的过程。
   - 记录2008-09-28猎鹰1号在前三次失败后首次成功入轨，与此次星舰首次入轨相隔十八年。

## 写作中的准确性边界

- 本次首次入轨是星舰的里程碑，不等于人类首次实现该能力，也不直接称为刷新整个人类航天的上限。
- 发动机异常确实同时出现在助推器和飞船；不能把用户最初提到的助推器异常全部纠正成飞船异常。
- 再点火入轨是飞控评估发动机状态后的决定，不写成盲目冒险或凭意志挽救飞行。
- 海面溅落不等于塔架捕获或完整回收复用；助推器安全系统触发与飞船落水后爆炸分别说明。
- 任务提前结束、未完成全部预定时长，与已实现的关键目标同时交代。

## 2026-09-29 配图与时间线

- 在用户审阅通过的正文中插入两组双栏新闻照片、时间线、AI概念插画；原有叙述段落保留。时间线初版六节点，后经起点核查扩为八节点。
- 两组照片为本次试飞的发射 / 在轨、再入 / 海面着陆，原始图像由 SpaceX 发布，具体来源与下载 URL 见 `assets/manifest.json`。
- 用户提供的四张图片均已查看：猎鹰9号、猎鹰重型各一张，星舰两张。前两张未混入本次飞行；后两张的具体架次与摄影来源未独立确认，暂作候选，正文使用架次明确的报道配图。
- 概念图用用户指定的内置 image_gen 生成并修正飞船外形，已标注 AI概念插画。完整提示词保存在 `assets/imagegen-prompts.json`。
- 时间线使用可编辑的 HTML 生成 PNG，确保日期与中文准确；数据和逐项来源见 `assets/timeline-data.json`。`node assets/build-timeline.mjs` 重建 HTML，以1080px视口截图全文生成 PNG。
- 时间线现选编2016年 ITS 公开方案、2019年 Starhopper 150米试飞、SN15、第1、4、5、10、14次试飞，不表示完整研发史或完整飞行记录；日期采用事件发生地当地日期。
- 表格置于文末附录，用三列说明日期、节点、进展与限制，保持随笔主体的阅读节奏。
- 双栏使用现有 renderer 的 `::compare` 语法，未改动共享 renderer。`node render-preview.mjs` 重新生成 origin 预览及微信渠道 HTML。
- 本地浏览器检查：320px、390px无横向溢出，六张正文图片全部加载；390px两组图片分别保持同一行。1280px桌面截图已人工查看。
- 微信 HTML 没有外部链接 href、script 或 table 标签；表格由 inline flex div 渲染。真实微信编辑器保存后的显示尚未验证，本轮没有上传草稿或发布。

## 时间线起点纠正

- 用户指出初版以2021年开头容易使人误以为星舰始于2021。SN15日期本身正确，但原图选编范围不足以表达项目来龙去脉。
- 新图题为「从公开方案，到首次入轨」，范围2016—2026；明确标注公开方案不等于研发起点。
- 2016-09-27：SpaceX 官方演讲 Making Humans a Multiplanetary Species，https://www.youtube.com/watch?v=H7Uyfqi_TE8 。此时介绍的是 ITS 前身方案，不将它表述为今日星舰设计已经定型。
- 2019-08-27：SpaceX 官方视频 150 Meter Starhopper Test，https://www.youtube.com/watch?v=bYb3bfA6_sQ 。这是150米低空跳跃，不称为 Starhopper 的首次飞行。
- 同步更新原始数据、可编辑图源、PNG、正文图注、附表及微信本地预览。
