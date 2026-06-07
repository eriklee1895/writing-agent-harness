# 2026-06-07 第2篇发布复盘：《半生雪》

## Context

第2篇微信公众号文章《半生雪》，从 ideation 到草稿箱发布全流程跑通。相比第1篇（Cloudflare/Vite 技术评论），这篇文章是**个人散文**，对 pipeline 提出了不同要求：更克制的排版、艺术性插图、避免技术文章的 UI 标签。

核心考核目标：验证 AI 写作 + 微信公众号 agent 自动化发布流程在**不同文体**下的通用性。

## What's New This Time

### 1. article-ideation：从技术评论到个人散文

- 用户带着明确灵感进入（给女儿找歌 → 发现两个版本 → 扒出故事）
- ideation 的核心工作是**校准文体**，而不是生成选题
- 关键决策：个人散文，不要网文化，不要鸡汤，要有文学质感和留白
- 标题经过多轮迭代，最终找到了克制且有信息量的方案

### 2. article-illustration：从技术图到艺术插画 ⭐ 最大变化

**问题**：`article-illustration` 脚本只为技术图表设计，所有 prompt 被包进 "technical infographic" 框架。

**修复**：

| 改动 | 文件 |
|------|------|
| 新增 `watercolor-illustration` 风格 | `scripts/generate_doc_illustration.py` |
| 艺术风格跳过技术图表 prompt 框架 | 同上 |
| 新增 `cover-hd` (1792x1024) | 同上 |
| 时间戳精度从分钟→秒+碰撞检测 | 同上（修复同秒覆写 bug） |
| 艺术风格文档 | `references/style-profiles.md` |

**发现**：微信公众号封面比例 2.35:1 (1080x460px)，但 GPT Image API 最宽只支持 1792x1024 (约 1.75:1)。实际上需要生成后手动裁剪。

**决定**：放弃新闻照片（版权问题），全部用 AI 生成水彩插画。效果出乎意料好。

### 3. wechat-article-renderer：适配散文排版

**问题**：`impact-rational` 风格硬编码了"趋势观察""一句话总结""文章大纲"等 tech 标签，跟个人散文完全不搭。

**修复**：

| 改动 | 说明 |
|------|------|
| 顶部标签："趋势观察"→"个人随笔" | 文体识别 |
| 大纲标题："文章大纲"→"阅读地图" | 更中性 |
| 摘要标签："一句话总结"→"作者想说" | 更散文 |
| 摘要区改为条件渲染 | 无摘要则不显示该区块 |
| deck 条件渲染 | 空 deck 不显示描述行 |
| 移除 tech 回退 deck | 原来硬编码 "一篇关于 AI 时代工具链…" |

### 4. 发布流程优化

| 问题 | 解决 |
|------|------|
| 第一次忘记 `--submit` | 草稿没保存，重新执行加 `--submit` |
| Markdown H1 太长生成了错误标题 | 使用 `--title "半生雪"` 显式覆盖 |
| 自动摘要从正文首段落抓取，不理想 | 使用 `--summary` 显式传入 120 字精炼版 |

**教训**：散文的标题和摘要往往需要手动精炼，不应依赖自动提取。发布时 `--title` 和 `--summary` 应该每次都显式传入。

## What Worked

- 端到端流水线再次跑通，且适配了完全不同的文体
- AI 生成插图质量令人满意，避免了版权问题
- ideation → draft → illustration → render → publish 各阶段衔接流畅
- 修改 skill 而不是绕过 skill，保持了工具的通用性
- `wechat-publish-workflow` 编排发布，`baoyu-post-to-wechat` CDP 执行，分工清晰

## Pitfalls

- `article-illustration` 脚本的设计假设（技术图表）限制了首次使用，需要先修脚本
- 时间戳碰撞 bug 导致两张图生成在同一秒时互相覆写
- 封面图比例知识没有提前沉淀，依赖 web search 实时查证
- Markdown 标题是 `# 半生雪: ...` 但微信标题应该是 `半生雪`，需要显式传参

## Knowledge Deposited

| 位置 | 内容 |
|------|------|
| `docs/reference/visuals.md` | 微信公众号封面图尺寸规范（头条 2.35:1, 1080x460） |
| `scripts/generate_doc_illustration.py` | `watercolor-illustration` 风格、`cover-hd` 尺寸、碰撞检测 |
| `references/style-profiles.md` | 新增艺术风格文档 |
| `scripts/render-wechat-article.mjs` | 散文适配：条件渲染、标签中性化 |
| 本次复盘 | `docs/retrospectives/2026-06-07-banshengxue.md` |

## Pipeline Maturity

当前流水线状态：

```
灵感 → article-ideation     ✅ 技术评论 + 个人散文
     → polish-article       ✅ (本次未使用，直接手写)
     → article-illustration ✅ 新增水彩风格
     → wechat-article-renderer ✅ 新增散文模式
     → wechat-publish-workflow ✅ CDP 发布
     → 草稿箱                ✅ appmsgid: 100000062
     → 人工 review + 发布    ⏳ 待用户确认
```

下次可以从 ideation 开始更顺畅——不需要再修脚本了。

## Open Questions

- 是否需要给 `wechat-article-renderer` 增加 `--style` 参数区分 tech/essay 模式，而不是共用 `impact-rational`？
- 封面图裁剪（1792x1024 → 1080x460）是否需要自动化脚本？
- 是否要把 `--title` 和 `--summary` 显式传入写进 `wechat-publish-workflow` 的标准流程？
