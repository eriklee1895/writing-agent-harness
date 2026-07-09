# 微信公众号版本改写规划

## 目标

把 [content/origin/2026-07-08-claude-tool-search-deep-dive/index.md](../origin/2026-07-08-claude-tool-search-deep-dive/index.md) 改写成适合微信公众号传播的版本：科普化、趣味化、多图、弱化 API trace，保留核心机制洞察。

## 读者差异

| 维度 | Origin / 博客版 | 微信公众号版 |
|---|---|---|
| 读者预期 | AI builder，能接受代码和 schema | 泛技术读者，想看懂概念和趋势 |
| 长度 | 长文，约 5000+ 中文字符 | 2500-3500 中文字符，分小节 |
| 节奏 | 由浅入深，完整链路 | 先给结论和画面，再补一层机制 |
| 代码/API | 完整 JSON 示例、Mermaid 图 | 极简化代码片段或伪代码，重在示意 |
| 视觉 | 一张封面 + 一张流程图 | 封面 + 2-3 张信息图/插图 + 长图 |

## 标题方案

- 主标题：**Claude 的“工具雷达”是怎么工作的？**
- 副标题：当 AI 接了 100 多个工具，它怎么知道该调用哪一个
- 备选：**Claude Tool Search 揭秘：AI 如何在百个工具里秒找目标**

> 注意：Origin / 博客版标题为 **Claude Tool Search 深度揭秘：当 AI 拥有 100 个工具时，它如何秒找目标？** 微信公众号标题可更口语化、更比喻化。

## 核心比喻

把 Claude Tool Search 比作 **“快递分拣中心的智能索引”**：

- 仓库里堆满包裹 = 成百上千个 MCP 工具
- 传统方式：每次送货前把所有包裹清单念一遍 = upfront 加载所有 schema
- Tool Search 方式：先给一个分类目录，收到订单后再查索引、只取相关包裹
- `tool_reference` = 取货单/扫码枪
- `defer_loading` = 包裹先不进传送带，等叫号

## 结构改写

### 1. Hook（约 300 字）
- 场景：你问 Claude Code “帮我看看线上 5xx”
- 冲突：它背后接了 100+ 工具
- 悬念：它怎么知道该调用 Prometheus 和 GitHub，而不是 Slack、Jira？

### 2. 一张主图：工具仓库 vs 工具索引
- 信息图：左右对比
  - 左：所有工具 schema  upfront 进大脑，模型“撑爆”
  - 右：只留目录，按需搜索，模型“清爽”

### 3. 核心机制：4 步看懂

用“快递分拣中心”比喻讲 4 步：

1. **贴标签**：`defer_loading` 把大多数工具标记为“暂不入场”
2. **下订单**：Claude 判断需要啥，发起 `server_tool_use` 搜索
3. **扫码取货**：返回 `tool_reference` 小纸条
4. **正式出库**：API 把小纸条展开成完整工具定义，Claude 调用

每一步配一张小图或一个图标卡片。

### 4. Claude Code 的开关

- `ENABLE_TOOL_SEARCH`：控制是“全量念清单”还是“按需查索引”
- `auto` 模式：工具描述超过上下文 10% 自动开启
- `alwaysLoad`：常用工具直接放传送带

### 5. 三个真实 query 的 Tool Search 实录（卡通/故事化）

把 origin 里的三个例子改造成微信友好版本：

- **查天气**：一页漫画/卡片，展示 Claude 拿到 query → 搜索 → 找到 `get_weather` → 调用
- **GitHub Actions + issue**：展示一次搜索召回 3 个工具，然后按顺序调用
- **5xx 监控 + 自动建 issue**：最复杂场景，强调“跨领域 + 条件分支”

每个例子用 1 张图 + 200 字说明即可，不要完整 JSON。

### 6. 开发者小建议（偏产品化）

- 工具名要写清楚“谁 + 做什么”
- 描述里要包含触发场景
- 高频工具别偷懒 defer

### 7. 一句话总结

> Claude Tool Search 的意义，是让 AI agent 的工具上下文从“仓库”变成“索引”。

## 视觉节奏

| 位置 | 图类型 | 说明 |
|---|---|---|
| 封面 | 公众号头条封面 2.35:1 | 已生成 `cover.png`，可直接复用或裁剪 |
| 第 2 节 | 左右对比信息图 | 仓库 vs 索引 |
| 第 3 节 | 4 步流程长图 | 可用 Excalidraw 手绘风 |
| 第 5 节 | 三个 query 故事卡片/漫画 | 每个 query 1 张图 |
| 第 6 节 | 小卡片/插图 | 工具描述好坏对比 |

## 需要新增的图

1. `assets/wechat-warehouse-vs-index.png` — 仓库 vs 索引对比
2. `assets/wechat-4-steps.png` — 4 步流程长图
3. `assets/wechat-query-weather.png` — 查天气故事卡片
4. `assets/wechat-query-github-actions.png` — GitHub Actions + issue 故事卡片
5. `assets/wechat-query-5xx.png` — 5xx 监控 + 自动建 issue 故事卡片
6. `assets/wechat-good-vs-bad-description.png` — 工具描述好坏对比

## 需要弱化的内容

- 第 2 章完整的 API schema 示例
- “一个贴近 Claude Code 的完整例子”章节中的完整多工具配置 JSON
- “三个真实 query”章节中的完整 JSON，改为故事卡片/伪代码
- 第 8 章多个 GitHub issue 的详细 bug 描述（保留 1-2 个最生动的）
- 开发者建议用更口语化表达

## 需要保留的锋芒

- 指出 Tool Search 不是银弹：HTTP MCP 不 defer、代理兼容性、1M 上下文阈值反直觉
- 与 ChatGPT 的差异一句话点出：OpenAI 是“静态工具箱”，Claude 是“动态索引”

## 输出路径

```text
content/wechat/2026-07-08-claude-tool-search-deep-dive/
├── article.md
├── article.wechat-preview.html
└── assets/
    ├── cover.png                          # 从 origin 复用
    ├── wechat-warehouse-vs-index.png
    ├── wechat-4-steps.png
    ├── wechat-query-weather.png
    ├── wechat-query-github-actions.png
    ├── wechat-query-5xx.png
    └── wechat-good-vs-bad-description.png
```

## 下一步动作

1. 用户确认微信版本方向后，生成上述 3 张插图。
2. 用 origin 文章改写出 `content/wechat/2026-07-08-claude-tool-search-deep-dive/article.md`。
3. 用 `wechat-article-renderer` 生成 HTML preview。
4. 本地 preview 检查移动端效果。
5. 按需进入 `wechat-publish-workflow`。

---

*Created: 2026-07-08*
