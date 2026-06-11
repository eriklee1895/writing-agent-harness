# WeChat Article Fetcher Skill Design

## 结论先行

**技术路线：Playwright + 本地持久化 Profile**

验证结果：4/4 公众号文章 URL 全部成功提取，无验证码，标题/正文/公众号名/发布时间/图片数全部正常。复用 profile 后启动时间从 14.7s 降至 7.8s。CDP 路线因进程生命周期管理复杂、代码量更大，不优于 Playwright，不采用。

## 需求

为 writing-agent-harness 增加微信公众号文章提取能力，用于 AI 写作素材收集阶段。

- **输入**：单个微信公众号文章 URL（`mp.weixin.qq.com/s/...`）
- **输出**：结构化素材包（Markdown 正文 + 元数据 + 落地图片）
- **触发场景**：用户给 agent 一个公众号链接，要求提取内容做写作参考

### 不在 MVP 范围

- 搜索引擎发现文章（主题 → URL）
- 批量 URL 处理
- 视频卡片提取
- 降级链路（Jina Reader 等）

## 技术选型

| 方案 | 实测成功率 | 代码复杂度 | 结论 |
|------|-----------|-----------|------|
| **Playwright + 持久化 Profile** | 4/4 成功 | 低（~80 行核心） | **采用** |
| CDP 直连本机 Chrome | 未通过（进程管理复杂） | 高（>150 行） | 不采用 |
| Jina Reader | N/A（第三方云服务） | 极低 | 不考虑 |

### Playwright 关键参数

- `headless=False`：有头模式更稳
- `user_data_dir`：复用本机 Cookie/登录态。默认 `~/.config/wechat-article-fetcher/profile/`（macOS 映射到 `~/Library/Application Support/wechat-article-fetcher/profile/`）
- `executable_path`：指向本机 Chrome（macOS 默认 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`）
- `--disable-blink-features=AutomationControlled`：降低反自动化检测
- `wait_for_selector("#js_content", timeout=15000)`：等待正文渲染

## 产物结构

```text
wechat-articles/                          # 默认输出目录（可覆盖）
└── YYYY-MM-DD-<slug>/
    ├── article.md          # Markdown 正文，图片引用 assets/ 相对路径
    ├── manifest.json       # 结构化元数据
    ├── sources.md          # 来源声明、抓取日期、合规提醒
    └── assets/
        ├── img-001.jpg
        ├── img-002.png
        └── ...
```

### manifest.json

```json
{
  "title": "...",
  "author": "...",
  "account": "...",
  "publish_time": "...",
  "source_url": "https://mp.weixin.qq.com/s/...",
  "fetched_at": "2026-06-10T21:30:00+08:00",
  "content_markdown_path": "article.md",
  "content_length": 3842,
  "images": [
    {
      "index": 1,
      "original_url": "https://mmbiz.qpic.cn/sz_mmbiz_png/...",
      "local_path": "assets/img-001.jpg",
      "alt": "图片描述"
    }
  ]
}
```

### article.md

```markdown
---
title: "文章标题"
account: "公众号名称"
publish_time: "2026年6月10日 20:00"
source_url: "https://mp.weixin.qq.com/s/..."
---

# 文章标题

正文内容...

![图片描述](assets/img-001.jpg)
```

## CLI 接口

```bash
# 默认输出到 ./wechat-articles/YYYY-MM-DD-<slug>/
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url>

# 指定输出目录（项目级用法）
uv run python .../fetch.py <url> --output-dir content/inbox/articles/

# 快速提取，不下载图片
uv run python .../fetch.py <url> --no-images
```

## 依赖

项目 `pyproject.toml` 增加：

```toml
dependencies = [
    # ... existing
    "playwright>=1.43.0",
    "markdownify>=1.1.0",
]
```

执行 `uv sync` 安装 Python 库。**不需要**额外 `playwright install chromium`——skill 直接复用本机已安装的 Chrome：`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`（macOS）。

### 依赖检查

脚本启动时检查：
1. `playwright` Python 包是否已安装（未安装则报错并提示 `uv sync`）
2. 本机 Chrome 是否存在（未找到则报错并提示安装 Chrome）
3. `markdownify` 是否已安装

不自动安装依赖。安装是一次性项目准备操作，不应在每次运行时隐式触发。

### 登录态处理

首次使用或 Cookie 过期时，文章页面可能显示登录提示而非正文。

**处理流程**：
1. 脚本访问目标 URL，等待 `#js_content` 或登录相关元素
2. 如果检测到未登录状态（无 `#js_content` 但有登录提示）：
   - 打印提示：`"未检测到微信登录态。请在弹出的浏览器窗口中登录（扫码或密码），完成后按回车继续..."`
   - 调用 `input()` 阻塞等待用户操作
   - 用户登录后按回车，脚本自动 `page.reload()`
3. 重新检查 `#js_content` 是否存在：
   - 存在 → 继续提取
   - 仍不存在 → 返回错误码 `LOGIN_FAILED`

**为什么是交互式而非静默失败**：
- 首次登录是低频事件，一次交互式引导值得
- 用户看到弹出的浏览器窗口，自然知道要操作什么
- 登录后自动继续，不需要重新运行命令

## 实现要点

### 正文提取

| 字段 | 选择器 | 备注 |
|------|--------|------|
| 正文 | `#js_content` | 由 JS 渲染，需等待 |
| 标题 | `#activity-name` | 稳定 |
| 公众号 | `#js_name` | 稳定 |
| 发布时间 | `#publish_time` | 部分由 JS 注入，失败时从 `var ct` 或 meta 兜底 |

### 图片处理

- 提取 `#js_content img` 的 `data-src` 属性（`mmbiz.qpic.cn` 域名）
- 用 `requests` 下载到 `assets/img-{index}.{ext}`，带 `Referer: https://mp.weixin.qq.com/` 头绕过防盗链
- Markdown 中替换为相对路径 `assets/img-001.jpg`
- 失败图片记录到 `manifest.json` 并保留原始 URL，不阻断主流程

### 格式清洗

markdownify 转换后需做轻量后处理：

| 清洗项 | 处理方式 | 优先级 |
|--------|----------|--------|
| 图片路径替换 | `data-src` → `assets/img-{index}.jpg` | P0 |
| 代码块粘连 | `<pre>` 内 `<p>` 标签换行修复 | P0 |
| 多余空行 | 连续 `\n\n\n+` 压缩为 `\n\n` | P1 |
| 底部推广/卡片 | 识别并移除公众号底部推广模块 | P1 |
| 颜色/字体/背景样式 | 忽略（Markdown 不支持） | 不做 |
| 语义改写 | 不修改内容结构和表达 | 不做 |

清洗阶段在 markdownify 之后，分两步：HTML 预清洗（修复代码块结构）→ Markdown 后清洗（空行、图片路径）。

### 外部链接

保留原始 `href`。这是素材提取，不是发布，外链是写作研究线索。

### 错误处理

- `#js_content` 超时未出现 → 返回错误码 `CONTENT_NOT_RENDERED`
- 验证码页 → 返回错误码 `VERIFICATION_REQUIRED`
- 文章已删除 → 返回错误码 `ARTICLE_DELETED`
- 图片下载失败 → 记录 warning，不阻断主流程

## 与项目工作流集成

```text
用户给 URL
  ↓
agent 调用 fetch.py --output-dir content/inbox/articles/
  ↓
产物进入 content/inbox/articles/YYYY-MM-DD-<slug>/
  ↓
写作时引用 article.md 和 assets/ 中的图片
  ↓
定稿后写作 agent 负责决定是否搬运到 content/source/<slug>/
```

## 文件布局

```text
.agents/skills/wechat-article-fetcher/
├── SKILL.md
└── scripts/
    └── fetch.py
```

## 测试验证清单

- [ ] Playwright 能成功渲染 `#js_content`
- [ ] 标题、公众号名、发布时间正确提取
- [ ] Markdown 正文与浏览器打开内容一致
- [ ] 图片下载到 `assets/` 且 Markdown 引用正确
- [ ] `--no-images` 模式不下载图片
- [ ] `--output-dir` 参数生效
- [ ] 错误文章（已删除/验证码）返回明确错误码
- [ ] 项目级用法 `uv run python .../fetch.py` 正常执行

## 风险与合规

- 仅抓取公开文章，遵守平台协议
- 引用注明来源（标题/公众号/链接），避免大规模转载或商用分发
- 控制频率，避免触发风控封禁
- 不打印、提交或泄漏浏览器 Cookie、登录态数据
