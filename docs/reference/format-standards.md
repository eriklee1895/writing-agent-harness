# Format Standards

写作 agent 的格式偏好和视觉标准 reference。Agent 在拿到 writing brief 后、开始写作前读取本文，理解不同输出格式的写作方法论、视觉手段和质量标准。

本文是 **reference doc**，不是 skill。它提供知识和方法论，不定义执行步骤。Agent 应根据文章主题、读者和气质自由选择和组合这些手段。

## Which Format To Choose

| 场景 | 推荐格式 | 典型读者 |
|---|---|---|
| 技术分析、行业评论、架构思考 | Markdown 技术报告 | 开发者、架构师、技术决策者 |
| Deep research、多维度调研、需要强视觉呈现的复杂主题 | HTML 单页报告 | 泛技术读者、决策者、需要传播的人 |
| 个人散文、随笔 | Markdown → 微信公众号 | 泛读者 |
| 文化评论、城市/音乐/文旅 | Markdown → 微信公众号 | 泛读者 |
| 微信公众号分发（任何内容） | 最终通过 `wechat-article-renderer` 转换 | 微信读者 |

Agent 默认从 Markdown 开始，除非用户明确要求 HTML 报告。

---

## Markdown 技术报告

### 核心原则

- **信息密度优先**：Markdown 的优势是清晰的信息架构，不要用不必要的装饰稀释它。
- **图表服务于理解**：技术概念、架构、流程和对比关系用 Mermaid 图表辅助，但不要为了"漂亮"加图。
- **代码块保持精确**：不要为了可读性改写真实代码；注释可以加，但不要改变源码语义。
- **术语保持精度**：`context window`、`token budget`、`tool use` 等技术术语不必强行中文化。

### 图表手段

**Mermaid 场景**：
- 架构图：多组件、多层的系统结构
- 流程图：有时间顺序的步骤或决策树
- 时序图：多角色交互（API 调用、协议握手）
- ER 图：数据模型关系
- 状态图：状态机或生命周期
- 类图：面向对象设计或类型关系

**Mermaid 反模式**：
- 不要为简单的一对一关系画图
- 不要在一个图表里塞超过 8-10 个节点
- 不要用 Mermaid 做时间线叙事（列表更清晰）

**article-illustration 场景**：
- 封面图：给文章一个视觉入口
- 概念插图：抽象概念需要具象化表达（如"上下文窗口衰减"）
- 章节分隔视觉元素

**SVG 场景**（手写或生成）：
- 需要精确控制布局的复杂架构图
- 需要标注和数据标签的对比图
- Mermaid 无法表达的视觉结构

### 结构惯例

```
1. Opening: 从一个具体场景、数据点或矛盾切入
2. Context: 为不熟悉背景的读者建立坐标系
3. Core argument: 核心论点展开
4. Evidence / cases: 案例、数据、对比
5. Implications: 这个分析意味着什么
6. Closing: 回到开头的张力，带着解决方案的视角
```

这不是模板，是方向。Agent 应根据主题自由调整、跳过或重排。

### 配图节奏

- 封面：1 张，用 `article-illustration`
- 正文插图：每 1500-2000 字左右可考虑一张概念插图，但不是硬性指标
- 架构/流程图：按需，不要因为"这里可以画图"而画图

---

## HTML 单页报告

### 何时选择 HTML

- 主题需要强视觉层次和多维度信息呈现
- 数据密集，适合用表格、卡片、时间线等形式
- 需要 CSS 动画或 GSAP 增强叙事节奏
- 预期读者会分享链接（HTML 静态页面可以直接托管）

### 核心原则

- **排版即叙事**：HTML 的 typography、spacing、color 和 animation 都是叙事手段，不只是容器。
- **富文本但不浮夸**：用视觉手段增强理解，不是替代内容。
- **单文件自包含**：所有 CSS、JS、图片 base64 内联，产出单个 HTML 文件，可以直接打开或托管。
- **图片 base64 内联**：用 WEBP 格式内联可省 ~8x 体积。
- **渐进增强**：先保证内容在无 CSS 时清晰可读，再加视觉层。

### 视觉手段

**CSS 排版**：
- 合理的 `max-width`（70-80ch）保证正文可读性
- 清晰的 heading hierarchy（h1 → h2 → h3）
- 代码块风格与正文区分
- blockquote、callout、aside 用于强调和补充

**CSS 动画**（可选）：
- `@keyframes` 用于滚动渐显、数据高亮、流程演示
- `animation-timeline: scroll()` 用于滚动驱动的叙事节奏
- 保持动画克制：每个页面 2-3 处关键动画足够
- 尊重 `prefers-reduced-motion`

**GSAP**（高级场景）：
- 复杂时间线动画（多元素协调入场）
- ScrollTrigger 驱动的叙事章节
- 数据可视化动画
- 仅在内容确实需要时使用，不要因为"可以做"而做

**Mermaid**（HTML 中）：
- 可以 `<pre class="mermaid">` 内联，通过 CDN 加载 mermaid.js 渲染
- 或在构建阶段预渲染为 SVG 再内联

**article-illustration 配图**：
- 封面 hero image
- 章节配图
- 概念插图和信息图
- 数据可视化辅助

**数据可视化**（可选）：
- 轻量图表库（如 Chart.js）通过 CDN 加载
- 或预渲染 SVG 内联
- 表格在 HTML 中可以直接用 `<table>` + CSS 美化

### 构建与 QA

- 构建过程应该是确定性的：Markdown → HTML 的转换规则清晰
- 长页（>8000px）建议分段 QA
- 用 headless Chrome 验证渲染效果
- 检查 `prefers-color-scheme` 在亮/暗模式下的表现

### 文件输出

```
content/origin/YYYY-MM-DD-<slug>/index.html
content/origin/YYYY-MM-DD-<slug>/assets/   # 配图、封面等
```

---

## 微信公众号

微信公众号有独特的格式约束和读者行为，详见：

- 排版：`wechat-article-renderer` skill（5 种 style preset）
- 发布流程：`wechat-publish-workflow` skill
- 详细 runbook：[docs/workflows/wechat-writing-publishing.md](../workflows/wechat-writing-publishing.md)

### 关键约束

- Markdown → HTML 转换后，所有外部 `<a href>` 需移除
- 正文图片通过 `wechat-article-publisher` 上传到微信 CDN，不要 base64 内联
- 代码块在微信编辑器中渲染行为复杂（3 种不同 HTML 结构），需要 `wechat-article-renderer` 专门处理
- 默认 style 偏好 `agent-flow`（纯白底、无卡片、扇形流式排版），原因：微信夜间模式自动反色时浅色卡片很亮

---

## Cross-Format Rules

### 图片管理

- 单篇文章的图片放在 `content/origin/YYYY-MM-DD-<slug>/assets/`
- 不同渠道版本引用 origin assets 而非复制
- 大体积二进制默认不提交 Git

### 写作品质

- 无论什么格式，都先想清楚 thesis 和 central question 再动笔
- Current events、公司/产品事实、定价、法律、快速变化的 tech topics 必须查证并写清日期
- 保留作者锋芒和判断，不要打磨成无风险的泛泛话题

### 不要做的事

- 不要为了"看起来漂亮"而加无关图表或动画
- 不要在 Markdown 中模仿 HTML 的排版效果（Markdown 的价值是简洁）
- 不要在 HTML 中写得像 Markdown（HTML 的价值是视觉叙事）
- 不要在没有想清楚文章论点时就纠结格式和视觉效果
- 不要把格式偏好当成硬性规范——根据内容自由发挥
