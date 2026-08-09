---
title: "我跑了 Gauntlet Loop，发现独立 critic 才是杠杆"
subtitle: "11 组实验 + 一款能玩的国风消消乐，拆穿"多智能体一夜做 3A"的神话"
date: 2026-08-10
source: "../../origin/2026-08-10-gauntlet-loop-critic/index.md"
topic: gauntlet-loop-critic
tags: ["ai-agent", "claude-code", "gauntlet-loop", "software-engineering"]
register: "wechat-longform"
style: "warm-editorial"
summary: "我把 viral 的 Gauntlet Loop 跑了 11 组对照实验，又用它迭代 8 轮做了款国风消消乐。结论：魔法不在 prompt 里，在持续集成、具体的 bar，和"不许作者给自己 merge PR"。"
cover: assets/cover.png
---

# 我跑了 Gauntlet Loop，发现独立 critic 才是杠杆

> 一个 prompt，5 万行代码，一夜做出 3A 游戏。真的吗？我去读了源码，还自己跑了 11 组实验。

![Critic is the Lever](assets/cover.png)

## 先讲个星期二的事

2026 年 7 月 25 号，一个叫 Matt Shumer 的人在 X 上发了段 30 秒录屏。

左边终端黑底白字在狂刷日志：

```
[spawned sub-agent: weapons-vfx]
[critic: comparing A/B blind]
[imagediff: 0.4% regression]
```

右边浏览器里是个第一人称射击游戏——有枪、有阴影、粒子爆炸、HUD，能玩。

配文一行字：

> 55k lines of JS from one prompt. It plays worse than Call of Duty, but it ships.

翻译过来：一个 prompt，Claude Code 自己生娃、自己当评委、自己逐像素查回归，十几个小时吐出 5 万 5 千行 Three.js，从 0 做出个能打的射击游戏。

这就是后来的 **Claude of Duty**。两天后有人 24 小时复刻了太空探索版；一周内社区 fork 出卡丁车、打僵尸、塔防、Fall Guys……二十多种游戏。

中文科技媒体口径高度一致：

> "Opus 5 + 多智能体辩论 + /loop 自检 = 一夜做 3A，奇点到了。"

我第一反应也是"卧槽"。

第二反应是：**这听上去太好了，好到我得去读读那个 repo 到底在干嘛。**

读完我发现：所有人都在讲"多智能体辩论"，但源码里真正在干活的东西，根本不是那么回事。

于是我干了两件事：

1. 把这套方法在**两个任务**上跑了 **11 组对照实验**；
2. 用同一套方法，**自己迭代 8 轮**做了个能玩的国风消消乐《消长录》。

这篇讲我发现了什么。先把结论拍桌上：

> **让 AI 连干一下午不翻车的秘密，不是更聪明的模型，是一套会说"不"的外部评委。而"另一个 AI"只是其中最弱的那个评委。**

游戏我部署上线了，手机电脑直接打开就能玩：**[xiaozhanglu.vercel.app](https://xiaozhanglu.vercel.app)**。边玩边读这篇，体验更佳。

![三道裂缝](assets/infographic-cracks.png)

## 一、116 个词，和一座不在那里的大厦

先看那段"封神"的 prompt 到底多长。我从开源仓库搬过来，全文如下：

> I want you to build a first-person shooter at the level of the most recent Call of Duty...
> Fan out sub-agents... /loop on each item with a separate sub-agent checking it blind...
> Don't stop until it looks triple A. Fan out sub-agents and ultracode.

数一下：**116 个词**。

没有 system prompt 脚手架，没有 `.claude/skills`，没有任何"高级 prompt engineering"。"ultracode"只是个触发动态工作流的关键词。

这就有意思了。如果 116 个词能产出 5 万行 3D，那魔法肯定不在你能 copy-paste 的咒语里——**它在咒语背后的架构契约**。

契约写在 `ARCHITECTURE.md`。我把最关键的几条抽出来：

- **目录所有制**：11 个子系统各管各的目录，不许 cross-import，运行时通过 `ctx.get('fx')` 互相访问；
- **确定性**：禁用 `Math.random()`，必须用 `ctx.rng`；每帧不许 new 对象；
- **真正的评委不是 AI**：critic 是 `tools/imagediff.mjs`（逐像素对比 baseline）、`tools/profile.mjs`（量 p99 帧时）、一个 17 项的确定性校验。LLM 盲审只是**辅助**，而且评分自己还在飘（3.59 → 4.14 → 4.05 → 5.05）。

停一下。

你脑子里那个"几个 AI 围坐一桌、互相 review 代码、投票达成共识"的画面——那是 viral 叙事喂给你的。

源码里实际发生的是：**持续集成 + 像素回归测试 + 帧时 profiler。**

**你以为你在看 AI 开会，其实你在看 CI。**

## 二、三道裂缝

viral 版本和真实工程之间，裂了三道缝。每一道都对应一个常见的坑。

### 裂缝 1：那个评委，根本不是 AI

所有人都以为 critic 是"另一个 Opus 在 blind A/B"。Matt 的教程也这么写。

但 Claude of Duty 里，真正决定"过没过"的是逐像素 diff 和测试脚本。Anshu 在复刻版里留了句话，特别精辟：

> "It looks flat" is not actionable; "0.00% of pixels clip and the 99th percentile is 165" is.

翻译：**"看起来有点平"不是反馈，"0% 像素过曝、99 百分位亮度 165"才是。**

最好的评委是数字，不是意见。

### 裂缝 2："并行 fan out"—— viral 的部分，恰恰不 work

Matt 的 prompt 让你"fan out sub-agents"，社区二十多个 wrapper 全把"并行"当卖点。

但 Claude of Duty 自己的 README 里藏了一行，我读第三遍才反应过来它有多重要：

> 三轮并行（每轮 6 个 agent）让分数只涨 0.46，缺陷却从 60 变 47 又变 **66**——因为光照、天空、间接光耦合在一起。改成串行单 owner，分数涨 1.00，缺陷从 66 砍到 26。

**并行在耦合子系统上，就是抖动配方（thrash recipe）。**

为什么？因为耦合的东西共享坐标、状态、视觉语言。一个 agent 改光照、一个改材质、一个改天空，每个人都觉得"我只动了自己的目录"，但 tonemapping 是个全局函数，三个人的改动叠起来没人能预测。

我自己的实验把这个数字钉死了：18 个合并冲突，缺陷分 **13 → 39 → 14**，最后都没回到第一轮的水平。

### 裂缝 3：游戏，从来没赢过 Call of Duty

第三个裂缝最诚实，也最容易在 hype 里漏掉。README 原句：

> The goal was to match a modern Call of Duty. It does not. Every critic in every round picked the real CoD frame.

每一轮、每一个评委，都选了真的 CoD。Shumer 是在"它还在进步"的时候手动喊停的。

**成功指标从来不是"won"，而是"still improving"。**

这听着反高潮，但 framing 本身就是范式转换：别把质量当一条要跨过的终点线，把它当一条你不断逼近的渐近线。critic 永远能挑出毛病，你要么手动停，要么跑到预算见底。

## 三、我跑了 11 组实验

光读源码不够——我想知道这些反直觉的发现是不是普适规律，还是只在 3D 射击游戏上成立。

我设计了两个任务：

- **消消乐**：Canvas 游戏，视觉 + 逻辑 + 性能三维度，耦合度高；
- **数据图表**：SVG 柱状图，视觉 + 数据准确，耦合度中。

每个任务跑四种评委架构（外加一个"故意给错目标"的对照组 E）：

| 代号 | 在测什么 |
|---|---|
| A | 单次 prompt，做完就停 |
| B | 同上下文自评自改（self-refine） |
| C | 全新上下文的 LLM 盲审评委 |
| D | 确定性工具评委（像素 diff + 测试 + profiler），拆成串行 / 并行两版 |
| E | **故意给错目标**（最大化粒子数/饱和度）看它怎么把东西做崩 |

每轮硬 cap 8 轮、同种子、用 Playwright 截图量帧时和逻辑错误。全部代码和数据在 GitHub 上，可复现。

![11 组实验结果](assets/infographic-results.png)

几个我没料到的结果：

**第一，"独立评委吊打自评"——居然要看任务。**

消消乐上，全新 LLM 评委和自评打平（37.3% vs 36.1%），但帧时被它搞到 83ms。它连续五轮执着地说"糖果质感太平、不够 3D"——可我用的是 Canvas 2D，不引入预渲染素材根本做不到 ray-traced 果冻。Builder 四次无视它，四次都对。

但在数据图表上，独立评委**赢了**（13.7% vs 17%），还早 4 轮就收敛。它说了句自评永远说不出口的话："参考图那种 glossy 3D 柱子是过时的 PPT 风，别学。"

**规律是：当评委掌握 builder 看不到的"语义/审美真相"时它有用；当缺口只是 builder 早就知道的技术限制时，它只是噪声。**

**第二，确定性工具评委，碾压 LLM 评委，但它是" taste 盲"。**

工具评委串行版：8 轮逻辑全绿、p99 稳在 25ms，中途有个 ReferenceError 瞬间被数字抓到。但它的审美分反而差——因为它不管你选什么美术风格，只管你别崩。

所以正确的分层是：**工具先把门（正确性/性能），LLM 盲审只在最上层做审美判断。** Claude of Duty 源码就是这么搭的。把顺序反过来，就是 C 条件那种"反馈很勤奋但方向错了"的灾难。

**第三，并行 fan out 又一次翻车，而且赢家是个" holistic agent"。**

数据图表并行组跑出了 13.45% 的最好成绩——但 agent 自己承认：赢的那次根本不是六个 agent 合并出来的，是**一个能跨子系统协调修改的 holistic agent** 单独跑的。六 agent 那轮反而回退了。

**"并行优化独立子问题"在有窄接口时成立；在共享坐标/视觉语言的地方，它摧毁一致性。**

**第四，错的目标，能高效生产精美的垃圾。**

E 对照组最触目惊心。图表的柱子被画到 99%–160%（真实数据是 5%–71%），数据肉眼完全读不出来，可我的 `__checkData()` **每一轮都返回绿灯**——因为我只检查了 state 里存的数字对不对，没检查它实际画了多高。

p99 从 58ms 飙到 232ms，满屏 emoji、跑马灯、假二维码。每一轮都是"让它更 pop"的合理局部响应，全局结果是灾难。

> **绿色的对勾，防不住你没测的东西。** 一个窄目标 + Gauntlet Loop = 高度抛光的错误。

## 四、这不是新发明，是软件工程 101

我知道有人要说"这不就是 CI/CD 吗"。

是的。就是。

把这套和软件业的家谱对一下：

- Builder = 写代码的开发
- 确定性测试套件 = CI
- 全新上下文的盲审 = code review / design critique
- 人类刹车 = tech lead
- 具体的 bar（参考图、p99 目标、测试通过）= 验收标准
- "不停改进、人喊停才停" = 持续改进文化

Shumer 自己写的那六条 prompt 法则，每一条都和人类团队管理一一对应（别微管理、给验收标准别给形容词、信任 IC 只在判断点介入……）。那条"从不打破"的规矩——"做东西的人不能给自己打分"——就是 code review 的铁律：**作者不能 merge 自己的 PR。**

反直觉的是：**LLM 让"自己给自己打分"变得更危险，而不是更安全。**

人类给自己 code review 至少还会脸红。LLM 没有羞耻感，它 rationalize 自己的决策比人类丝滑得多——它是真心相信"这代码没问题"，因为写每一行时它都给自己解释过为什么对。

Anshu 在 GAIA 基准上有个很冷冰冰的数据：难题上直接问成功率 30.6%，加了 critic-builder loop 反而掉到 23.5%。当评委拿不到 builder 看不到的 ground truth 时，它只是在**自信地往错方向迭代**。

这也是为什么 Anthropic 把 gauntlet 做进产品时，底层全是确定性工具（lint / type-check / test / 安全扫描），LLM review 只在工具够不着的语义层兜底。

**真正做工程的人都在用确定性评委，社区却在吵多智能体。**

![三层评委](assets/infographic-critics.png)

## 五、所以你今晚就能用的四条

不是让你也写 116 词 prompt 做 3A。大部分人不做游戏。但不管你用 Claude Code、Cursor 还是自研框架，这四条直接搬：

**1. 写个确定性检查脚本，比找第二个 AI 当评委 ROI 高 10 倍。**

先问：这个 review 能不能用一个 assert、一个像素 diff、一个 profiler 确定性化？LLM 盲审是最后一层 taste filter，不是第一道 correctness gate。

但确定性测试也有盲区——这次我做游戏，桌面鼠标点击坏了六轮没人发现，因为 e2e 测试只走拖拽、无障碍测试只走方向键。**测试是张网，网眼你定，漏的鱼照游。**

**2. 耦合的子系统串行，窄接口的才并行。**

拆任务前先问：这俩会不会改同一块？共享坐标/状态/视觉语言就串行，纯函数/独立文件/offscreen 活才并行。判据一句话：**如果两个 agent 改完要 merge 同一个函数的同一片区域，它们就不该并行。**

**3. 目标必须多维，你自己是最后的刹车。**

单维度目标会把其他一切砸了换自己的指标涨。验收至少包含：正确性、性能、可读性/审美、数据和呈现一致。Agent 不知道"够了"——到轮次上限或质量拐点，你喊停。

**4. 让别人/新 agent/脚本给你 review，别 merge 自己的 PR。**

新鲜眼睛能看到你看了太多遍而瞎掉的东西。哪怕是另起一个会话把截图丢给它、让它挑毛病，都比你自己盯着强。

## 六、我做了个能玩的游戏

光说不练假把式。我用这套 Gauntlet Loop 方法论，**自己迭代了 8 轮**，做了个国风消消乐叫《消长录》。

![游戏内的盲审判官面板](assets/judge-panel.png)

核心机制就是这篇文章的 thesis：**每走 5 步，一个判官面板弹出来，给你看两张匿名棋盘，标着"甲"和"乙"。你选哪个更好看。**

判官不是做手脚的。我写了个 `boardBeauty()` 函数，用棋子颜色分布的熵 + 当前可走步数给棋盘打分，谁高判官选谁——所以**有时候你自己的棋盘真的更好看**，选对了就触发全屏清屏（"极！"）。连续判对攒"明察"连击。

这设计是故意的：真实的独立评委有你没有的 ground truth，但它也可能错，你偶尔得敢驳回它。我实验里那个 builder 四次 defy critic 全对，就是因为评委在逼它做 Canvas 2D 做不到的事。

游戏有三关，通关解锁四个主题。所有棋子图都是 Seedream 生成的水彩/油画/浮世绘/新艺术作品，古筝竹笛 BGM 是 BigMusic 生成的，p99 帧时 10ms 上下。

- 🏮 **国风院景**（默认）：青花瓷盏、荷花、牡丹、铜钱、香炉、黑猫墨玉
- 🌳 **森之画境**：吉卜力风森林、橡果、蘑菇、萤火虫
- 🌊 **浮世绘卷**：北斋浪、富士山、樱花、折鹤、狐狸
- 🦚 **新艺术梦**：Mucha 金线、孔雀羽、蝴蝶、鸢尾

**👉 直接玩：[xiaozhanglu.vercel.app](https://xiaozhanglu.vercel.app)**（手机电脑都行，不用装）

![森之画境主题](assets/ghibli-theme.png)

### 它本身也是 Gauntlet Loop 的产物

更重要的是，**这游戏不是一次写完的，是我用同一套方法迭代了 8 轮的结果**，每一轮都有 Playwright 截图 + 逻辑断言 + 帧时 profiler 当确定性评委：

视觉 → 手感 → 移动端+关卡 → 诚实判官 → 引导/设置/音效 → 无障碍 → 边界加固 → 最终抛光。

逻辑断言从 14 个涨到 28 个，p99 始终压在 33ms 以下。

**R7 那轮抓到一个特别值得讲的 bug**：桌面端鼠标点击选棋子是坏的——点一下"选中又立刻取消"。这 bug 从 R1 活到 R6，六轮里所有自动化测试全绿。为什么？因为 e2e 测试走的是拖拽、无障碍测试走的是方向键，**没一个测试走鼠标点击**。

这就是对"确定性评委比 LLM 好"的重要修正：它只抓你设计它去抓的鱼。你量什么它保证什么，你没量的——一个没被走到的交互路径、一个"绿色但画到 160%"的柱子、一个你以为不会崩的音频权限——它心安理得地绿着。

还有个工程教训：迭代到 R4，builder agent 在最终验证阶段撞上配额限制直接死了，退出状态是 failed。但代码早就写完落盘了——我重跑一遍检查全绿，手动补个版本号就收工。**在评委跑之前就 checkpoint 你的产物，因为 runner 可以独立于 builder 而挂掉。** 别因为 agent 退出状态是 failed 就以为它白干了。

完整代码、11 组实验数据、每轮的 POLISH 笔记都在 GitHub：[github.com/eriklee1895/gauntlet-loop-experiment](https://github.com/eriklee1895/gauntlet-loop-experiment)。

我做这个游戏一半是手痒，一半是想让你**身体记住**这个论点：当判官问你"甲还是乙"，你会发现自己经常选错——你以为你棋盘上那片粒子海很热闹，和一个 balanced layout 并排才发现自己早就审美疲劳了。

Blind A/B 是你在自己项目上**永远对自己做不出来的判断**，因为你看了它太多遍。

这就是为什么 builder 永远不该给自己 merge PR。这就是为什么 code review 要找 fresh eyes。这就是为什么"独立评委才是杠杆"不是 AI 时代的发明——只是我们这个行业，又一次重新学会了同一个教训。

## 七、不是结尾

viral 叙事告诉你：魔法在 prompt 里，多 agent 并行就有奇迹，LLM 互相辩论就能达到 AAA。

源码告诉你：魔法在 CI 里，并行在耦合处会翻车，LLM 不能给自己当评委，人必须在刹车的位置。

下一个五年，不是谁的模型更聪明，而是**谁的 builder 和 grader 分得更开、bar 更具体、verification 更确定。** 这和 1968 年 NATO 会议讨论"软件工程"时是同一个故事，只是角色换成了 agent。

希望你下次让 AI 干活时：

- 先写确定性检查，再谈 LLM review；
- 耦合的地方串行，别被"fan out"诱惑；
- 设多维目标，别当窄指标的奴隶；
- 让新鲜眼睛给你 review，别 merge 自己的 PR；
- 你自己当刹车，别当副驾。

剩下的，《消长录》里见。**👉 [xiaozhanglu.vercel.app](https://xiaozhanglu.vercel.app)**

---

*实验代码、截图、原始数据都在 [GitHub](https://github.com/eriklee1895/gauntlet-loop-experiment)，MIT 协议。配套实操手册《让 Claude Code 连干八小时》在 repo 的 `methodology.md`，这篇讲为什么，那篇讲怎么做。感谢 Matt Shumer 开源 Claude of Duty，Anshu 开源 The Long Silence，Anthropic 公开 gauntlets 工程实践。*
