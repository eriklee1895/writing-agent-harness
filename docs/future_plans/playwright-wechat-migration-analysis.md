# 微信公众号发布：从 CDP 迁移到 Playwright 的技术分析与路线图

## 执行摘要（TL;DR）

**结论**：Playwright 是比当前 CDP（baoyu-post-to-wechat）更优、更可靠的浏览器自动化方案。

| 维度 | CDP（当前） | Playwright（目标） |
|------|------------|-------------------|
| 核心代码量 | ~742 行（wechat-browser.ts） | 预估 ~200-300 行 |
| 文件上传复杂度 | primary + fallback 两套手动拦截逻辑 | `locator.setInputFiles()` 一行 |
| 等待/重试策略 | 手写 `sleep` + 轮询 | 内建 auto-wait |
| 编辑器交互可靠性 | 鼠标坐标模拟，易被微信编辑器忽略 | 高阶 API，自动处理 focus 与 synthetic event |
| 同域验证结果 | 文章提取已跑通（4/4 成功，无验证码） | — |
| 启动性能（复用 profile） | 14.7s → 7.8s | — |

**决策**：在下一个空闲周末启动 Playwright 发布 PoC；若验证成功，逐步淘汰 baoyu CDP 方案，将微信公众号发布迁移至统一 Playwright 技术栈。

---

## 背景与动机

### 当前链路

```text
Markdown source
  → polish-article
  → wechat-article-renderer
  → wechat-publish-workflow
  → baoyu-post-to-wechat（CDP 模式）
  → 微信公众号草稿箱
```

`baoyu-post-to-wechat` 基于 `baoyu-chrome-cdp` 包，直接通过 Chrome DevTools Protocol（CDP）操控浏览器：

- `Runtime.evaluate` 执行 JavaScript
- `DOM.querySelector` / `DOM.querySelectorAll` 定位元素
- `Input.dispatchMouseEvent` 模拟鼠标点击
- `Page.setInterceptFileChooserDialog` + `DOM.setFileInputFiles` 处理文件上传

### 触发本次分析的问题

1. **已验证的替代方案**：2026-06-10 完成的 [wechat-article-fetcher](../superpowers/specs/2026-06-10-wechat-article-fetcher-design.md) 明确对比了 Playwright 与 CDP，结论为"CDP 因进程生命周期管理复杂、代码量更大而不采用"。
2. **已记录的稳定性问题**：[memory](../../memory/baoyu-browser-draft-save-issue.md) 记录"CDP 点击保存为草稿按钮可能不被微信编辑器响应"——低阶事件模拟与前端框架事件系统不匹配。
3. **统一技术栈需求**：未来 web search、视频素材剪辑等场景也需要浏览器自动化，统一至 Playwright 可降低长期维护成本。

---

## 现状：CDP 方案详细评估

### 实现概况

| 文件 | 行数 | 职责 |
|------|------|------|
| `scripts/wechat-browser.ts` | 742 | 图文发布主流程（贴图/图文） |
| `scripts/wechat-article.ts` | — | 文章发布主流程（文章） |
| `scripts/cdp.ts` | 256 | CDP 连接、Chrome 启动、页面会话管理 |
| `scripts/wechat-image-processor.ts` | — | 图片上传处理 |

### CDP 核心痛点

#### 1. 文件上传异常复杂

`wechat-browser.ts` 中文件上传实现（第 361-480 行）：

```text
primary: Page.setInterceptFileChooserDialog 拦截 dialog
  → Runtime.evaluate 调用 input.click()
  → 等待 Page.fileChooserOpened 事件
  → DOM.setFileInputFiles 通过 backendNodeId 设置文件
  → 若失败 → fallback: 直接 DOM.querySelector 找 input
    → DOM.setFileInputFiles 通过 nodeId 设置
    → 手动 dispatch change/input event
```

两套逻辑、多步 fallback，任何一步被微信 UI 改版打断即失效。

#### 2. 编辑器检测与切换脆弱

微信编辑器可能在新标签页打开，也可能在当前页导航。当前实现：

- 预先记录 `initialIds`（targetId 集合）
- 轮询 `Target.getTargets` 查找新标签页或 `appmsg` URL
- 若为新标签页，需 `Target.attachToTarget` 重新建立 session
- 重新 enable `Page` / `Runtime` / `DOM`

这个过程完全依赖微信后台的 target 管理行为，一旦弹窗逻辑变化即需重写。

#### 3. 鼠标事件模拟不可靠

```typescript
await cdp.send('Input.dispatchMouseEvent', {
  type: 'mousePressed',
  x: pos.x, y: pos.y,
  button: 'left', clickCount: 1,
});
await sleep(50);
await cdp.send('Input.dispatchMouseEvent', {
  type: 'mouseReleased',
  x: pos.x, y: pos.y,
  button: 'left', clickCount: 1,
});
```

只发了 `mousePressed` 和 `mouseReleased`，没有 `mouseMoved`，没有 hover，没有 `click` 事件。微信编辑器如果依赖 React synthetic event 或 focus-trap，这段代码会"点了但没反应"。

#### 4. 等待策略原始

大量使用 `sleep(3000)`、`sleep(2000)` 等固定延时，而非元素状态驱动的等待。慢网络下可能超时，快网络下浪费时间。

---

## 候选方案：Playwright

### 已验证的事实

2026-06-10 的 wechat-article-fetcher 验证：

| 验证项 | 结果 |
|--------|------|
| `mp.weixin.qq.com` 域名访问 | 4/4 成功 |
| 验证码出现 | 无 |
| `#js_content` 渲染等待 | `wait_for_selector` 15s 内稳定 |
| 标题/正文/公众号名/发布时间 | 全部正常提取 |
| 图片下载（带 Referer） | 正常 |
| Profile 复用启动时间 | 14.7s → 7.8s |

### Playwright 关键优势（针对发布场景）

| CDP 痛点 | Playwright 解法 |
|----------|----------------|
| 手写鼠标坐标点击 | `page.click()` / `locator.click()` — 自动 scroll into view、自动 wait for visible、自动处理 focus |
| 文件上传两套 fallback | `locator.setInputFiles()` — 一行，底层处理所有 dialog 拦截 |
| 编辑器标签页切换手动管理 | `context.wait_for_event('page')` 或 `page.expect_popup()` — 声明式 |
| `sleep` 固定延时 | `page.wait_for_selector()`、`locator.wait_for()`、`expect().to_be_visible()` — 状态驱动 |
| 进程管理（`baoyu-chrome-cdp` 封装） | `playwright.chromium.launch_persistent_context()` — 官方维护，文档完善 |
| 反检测 | `--disable-blink-features=AutomationControlled` + `user_agent` 定制 — 成熟方案 |

### 预估代码量对比

| 模块 | CDP 实现 | Playwright 预估 |
|------|----------|----------------|
| Chrome 启动 + 登录态复用 | ~50 行（cdp.ts） | ~10 行 |
| 页面导航 + 登录检查 | ~30 行 | ~10 行 |
| "图文"菜单点击 | ~40 行（坐标计算 + mouse event） | ~3 行 |
| 编辑器检测/切换 | ~60 行 | ~5 行 |
| 文件上传 | ~120 行（两套 fallback） | ~3 行 |
| 标题/内容填写 | ~60 行 | ~10 行 |
| 保存草稿 | ~40 行 | ~5 行 |
| 错误处理/重试 | 分散在各处 | 结构化 `try/except` + screenshot on failure |
| **总计** | **~742 行** | **~200-300 行** |

---

## 技术选型：为什么不是 AI Agent 框架

考虑过 Browser-Use、Stagehand、Skyvern 等 AI agent 浏览器控制框架，结论：**不采用**。

| 框架 | 为什么不适合微信发布 |
|------|---------------------|
| Browser-Use | 设计目标是"让 LLM 看网页并决策"，微信发布是确定性流程，不需要 LLM 介入点击哪个按钮 |
| Stagehand | 强调自然语言指令（"点击保存按钮"），但微信编辑器 DOM 结构复杂，自然语言映射不可靠 |
| Skyvern | 强调自主导航和多步骤决策，发布流程路径固定，自主决策反而引入不确定性 |

**原则**：确定性流程用确定性自动化（Playwright），探索性/研究性任务才考虑 AI agent 框架。

---

## 迁移路线图

### Phase 0：文档与准备（当前）

- [x] 完成本技术分析文档
- [ ] 确认周末空闲窗口（用户自行安排）
- [ ] 备份当前 baoyu CDP 相关代码（已入 Git，天然备份）

### Phase 1：PoC 验证 ✅ 已完成（2026-06-11）

**目标**：用 Playwright 实现最小可行发布流程，验证核心链路是否跑通。

**实际范围**（计划原写图文，执行时按用户需求改为"文章"流程——这是项目真实产出路径）：
- 覆盖"文章"（长图文）发布流程，ProseMirror 编辑器
- 纯文本测试文章（无图），不覆盖图片/封面/多账号/主题——留给 Phase 2
- 独立 profile（`~/.config/wechat-article-publisher/profile/`），与 baoyu 解耦

**验收结果**：

| 验收标准 | 结果 |
|----------|------|
| 独立 profile 登录并复用 | ✅ 首次 14.2s 扫码登录；第二次 `login_wait 0.00s`（免扫码） |
| 声明式捕获文章编辑器新标签页 | ✅ `context.expect_page()` 首次成功，editor `type=77` |
| 填写 title/author/正文 | ✅ ProseMirror `execCommand insertHTML`，editor innerText=1329 chars |
| 保存草稿出现 `appmsgid` | ✅ `appmsgid=100000229`，首次成功 |
| 无硬编码 `sleep` | ✅ 全程 `wait_for_url` / `wait_for_selector` / `expect_page` |

**产物**：
- [`scripts/poc_wechat_publish_playwright.py`](../../scripts/poc_wechat_publish_playwright.py)（307 行）

### Phase 1 验证报告：决策门 G1

**三轴对比（PoC vs baoyu CDP 文章流程）**：

| 维度 | Playwright PoC | baoyu CDP | 结论 |
|------|---------------|-----------|------|
| 代码行数（文章流程） | **307 行**（含 CLI/计时/错误处理） | 1482 行（`wechat-article.ts` 1227 + `cdp.ts` 255） | Playwright 约 1/5 |
| 端到端耗时（profile 复用热跑） | **11.5s**（启动 2.7 + 进编辑器 4.6 + 填充 0.03 + 存草稿 1.1） | 偏慢（大量固定 `sleep`，无精确头对头测量） | Playwright 更快 |
| 交互可靠性 | 菜单点击 / 正文注入 / 存草稿**均首次成功** | 已记录"保存草稿按钮可能不被响应"低阶事件问题 | Playwright 更稳 |

**G1 判定**：三轴 Playwright 全部明显更优 → **通过，进入 Phase 2**。

**关键发现**：
- 文件上传痛点（baoyu 双 fallback ~120 行）在 PoC 中不存在——但 PoC 首轮是无图文章，图片上传作为 Phase 2 真实缺口已单独验证（见下）。
- ProseMirror `execCommand('insertHTML')` 在 Playwright `page.evaluate` 下照搬 baoyu 即可用，无需 clipboard。
- profile 复用让登录态在第二次运行后 `login_wait=0`，扫码只需一次。

### Phase 1.5 验证：正文图片上传（2026-06-11）

用 `半生雪`（2 张本地图，各约 3MB）验证图片缺口：

| 项 | 结果 |
|----|------|
| 内联图片解析 → 占位符 → 定位删除 → `set_input_files` | ✅ 2/2 插入，编辑器内图片计数 0→2 |
| 上传到微信 CDN | ✅ 2/2 变成 `https://mmbiz.qpic.cn/sz_mmbiz_png/...` |
| 带图存草稿 | ✅ `appmsgid=100000237` |
| 正文图片输入框 | 仅 1 个 `input[type=file][accept*=image]`，`.first` 无歧义（对齐 baoyu） |

**两个必须固化进 skill 的坑**：
1. **存草稿前必须等图片 CDN 上传完成**。`set_input_files` 后 `<img>` 立即出现但 src 还是本地 blob；过早点保存会卡住。需轮询直到所有 `<img>.src` 含 `mmbiz.qpic.cn` 再保存（PoC 已加 `wait_for_cdn`）。
2. **`appmsgid` 判定不要 gate 在 `!isLoading`**。带大图时保存按钮可能长时间停留 loading 态，而 `appmsgid` 其实已写入——一次 90s 误判即因此而来。改为 `appmsgid` 一旦出现即视为成功。
3. 观察到保存耗时存在波动（1s vs 偶发长时间），Phase 2 skill 应加 save 重试 / 编辑器 idle 等待加固。

### Phase 2：完整功能对等（PoC 成功后 1-2 周内）

**目标**：Playwright 版本功能上与 CDP 版本完全对等。

**任务**：
- [ ] 覆盖"文章"（长图文）发布流程 ✅ 已验证基础链路
- [ ] 支持多账号切换（读取 EXTEND.md 配置）
- [ ] 支持主题/颜色选择
- [ ] 支持封面图上传
- [x] 支持正文图片批量上传（已验证 `set_input_files` + CDN 等待）
- [ ] 支持摘要/作者填写 ✅ 已验证
- [ ] 错误处理：登录态失效提示、图片上传失败重试、保存失败截图
- [ ] 集成 `wechat-article-renderer` 产出的 HTML（提取 `#output`）
- [ ] 与 `wechat-publish-workflow` skill 集成

**验收标准**：
- [ ] 任意一篇文章能用 Playwright 版本走完从 Markdown → 草稿箱的完整流程
- [ ] 与 CDP 版本输出等价（同一篇文章，两个方案都产生有效的草稿 `appmsgid`）

### Phase 3：切换与淘汰（功能对等后）

**目标**：正式替换 CDP 方案。

**任务**：
- [ ] 更新 `wechat-publish-workflow` skill，默认调用 Playwright 版本
- [ ] 更新 AGENTS.md 和 workflow 文档，移除 baoyu CDP 主路径描述
- [ ] 保留 CDP 代码 1-2 个月作为 fallback（但不维护新功能）
- [ ] 观察 2-3 次真实发布，确认稳定性
- [ ] 若无问题，删除 baoyu-post-to-wechat 相关代码和依赖
- [ ] 更新项目依赖：移除 `baoyu-chrome-cdp`，确认 `playwright` 已在 `pyproject.toml`

---

## Playwright 统一技术栈扩展（浅层提及）

本次迁移不只是解决微信发布问题，而是建立统一的浏览器自动化技术栈。未来以下场景可复用同一套 Playwright 基础设施：

### Web Search（网页搜索与信息提取）

- **场景**：AI 写作研究阶段，需要搜索最新资料、打开搜索结果页、提取正文
- **为什么用 Playwright**：搜索引擎结果页高度动态（JavaScript 渲染），静态 HTTP 客户端拿不到完整内容；Playwright 能等渲染完成再提取
- **复用点**：profile 复用（保持搜索登录态）、`wait_for_selector` 模式、反检测配置

### 视频素材剪辑（browser-based 操作）

- **场景**：某些视频平台（Bilibili、YouTube）的创作者后台操作，或在线剪辑工具的自动化
- **为什么用 Playwright**：这些平台大多依赖前端框架渲染，且需要登录态
- **复用点**：同一套 `launch_persistent_context`、cookie/profile 管理、截图/录屏能力

### 其他潜在场景

- **平台内容同步**：同一篇文章分发到多个平台（知乎、掘金、Medium）
- **数据监控**：定期检查某些网页的状态变化（价格、内容更新）
- **自动化测试**：微信公众号 renderer 的回归测试（用 Playwright 验证生成 HTML 在各平台的渲染效果）

**原则**：所有确定性浏览器自动化统一用 Playwright；只有探索性、需要 LLM 实时决策的任务才考虑 AI agent 框架。

---

## 风险与应对

| 风险 | 可能性 | 影响 | 应对 |
|------|--------|------|------|
| Playwright PoC 失败（微信风控升级） | 中 | 高 | 保留 CDP fallback；分析失败原因，可能需调整反检测策略 |
| 微信 UI 改版导致 Playwright 选择器失效 | 高 | 中 | 选择器用语义化定位（role/label），减少依赖具体 class name；建立快速修复流程 |
| Playwright 与现有 Node/Bun 生态集成问题 | 低 | 中 | Python 版 Playwright 已验证可用；若项目偏好 TS，用 `playwright` npm 包 |
| 迁移期间需要紧急发布 | 中 | 低 | Phase 1-2 期间 CDP 继续可用；Phase 3 保留 fallback 窗口 |
| baoyu-chrome-cdp 停止维护 | 中 | 低 | 这正是迁移的动机之一；即使不停维护，技术债也在累积 |

---

## 附录

### A. 相关文档索引

| 文档 | 内容 |
|------|------|
| [../../docs/superpowers/specs/2026-06-10-wechat-article-fetcher-design.md](../../docs/superpowers/specs/2026-06-10-wechat-article-fetcher-design.md) | Playwright vs CDP 的已验证对比数据 |
| [../../docs/workflows/wechat-writing-publishing.md](../../docs/workflows/wechat-writing-publishing.md) | 当前发布流程完整文档 |
| [../../docs/retrospectives/2026-06-05-wechat-publish.md](../../docs/retrospectives/2026-06-05-wechat-publish.md) | CDP 发布复盘 |
| [../../docs/retrospectives/2026-06-06-wechat-cdp-only-decision.md](../../docs/retrospectives/2026-06-06-wechat-cdp-only-decision.md) | CDP Only 决策记录（将被本方案替代） |
| [../../memory/baoyu-browser-draft-save-issue.md](../../memory/baoyu-browser-draft-save-issue.md) | CDP 点击不响应的具体问题记录 |
| [../../.agents/skills/baoyu-post-to-wechat/scripts/wechat-browser.ts](../../.agents/skills/baoyu-post-to-wechat/scripts/wechat-browser.ts) | CDP 图文发布实现（742 行） |
| [../../.agents/skills/baoyu-post-to-wechat/scripts/cdp.ts](../../.agents/skills/baoyu-post-to-wechat/scripts/cdp.ts) | CDP 连接管理实现（256 行） |

### B. Playwright 核心参考代码（来自已验证的 wechat-article-fetcher）

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="./chrome-profile",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    page.goto(url)
    page.wait_for_selector("#js_content", timeout=15000)
    # ... extract content
```

### C. 决策日志

| 日期 | 决策 | 上下文 |
|------|------|--------|
| 2026-06-06 | CDP Only | 当时 API 需要 IP 白名单，个人 harness 维护成本太高 |
| 2026-06-10 | Playwright > CDP for 文章提取 | 验证成功，明确记录"CDP 因进程管理复杂、代码量大而不采用" |
| 2026-06-11 | 启动 Playwright 迁移分析 | 用户提问，结合已验证数据和 CDP 稳定性问题，确认迁移方向 |
| 2026-06-11 | Phase 1 PoC 完成，G1 通过 | 文章流程跑通：307 行 / 11.5s 热跑 / `appmsgid=100000229` 首次成功；三轴优于 CDP，进入 Phase 2 |
| 2026-06-11 | Phase 1.5 图片上传验证通过 | `半生雪` 2 图上 `mmbiz.qpic.cn` CDN，`appmsgid=100000237` |
| 2026-06-11 | Phase 2 skill 落地 | 新建 Playwright 发布 skill，renderer HTML 输入 + 正文图片 + 草稿保存全链路验证；切换 `wechat-publish-workflow` 默认，baoyu 降级 fallback |
| 2026-06-11 | Phase 2.1 改名 + 修核心 bug | 经 grill-me 定稿：skill 改名 `wechat-article-publisher`（延续 article 家族）；加 `config.toml`（`default_author=李玉恒`）；元数据权威源改为 source `.md` frontmatter。**修标题 bug**：`#title` 是隐藏 textarea，可见标题是独立 `#js_title_main .ProseMirror`，改为点击+键入再回读校验。**修多图 bug**：串行化上传（每图等 CDN 完成再传下一张），banshengxue 2/2 上 CDN，`appmsgid=100000256`，标题截图目视确认。hero 大标题从正文剔除。封面 best-effort（开弹窗但未稳定跑通）→ 文档化为手动。 |
| 2026-06-11 | Phase 2.2 验证 frontmatter 权威源 + 修图-caption 空行 | 存量文章 `cloudflare-vite-astro`（frontmatter title≠正文H1 + 5 图）端到端：标题取 frontmatter（非正文 H1）、作者李玉恒、5/5 图上 CDN、`appmsgid=100000267`。**修图-caption 空行**：renderer 的 `<figure>` 被抽走图片后残留嵌套空 `<span>`（baoyu 当年漏掉的正是这个嵌套节点）→ 提取时拆 figure 成占位符段+caption 段，上传后清理空段，截图确认 caption 紧贴图片。 |
| 2026-06-11 | 封面自动化两次尝试后定为 opt-in 手动 | 拿到封面弹窗结构后补全「本地上传→等加载→完成」，两次实测都停在 `uploaded-unconfirmed`（自定义拖拽+裁剪控件，文件没落地，错误「必须插入一张图片」）。封面弹窗另有「从正文选择」更稳路径（仅限正文图）。结论：封面**默认手动**，`--try-cover` 保留实验入口，不阻塞保存、不默认拖慢发布。 |
