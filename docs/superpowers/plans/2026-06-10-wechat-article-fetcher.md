# WeChat Article Fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现微信公众号文章提取 skill，输入 URL 输出结构化素材包。

**Architecture:** Playwright + 本地持久化 Profile 提取正文，requests 下载图片，markdownify 转 Markdown，轻量格式清洗。

**Tech Stack:** Python, Playwright, markdownify, requests, uv

---

## File Structure

```text
.agents/skills/wechat-article-fetcher/
├── SKILL.md              # skill 定义和使用说明
└── scripts/
    └── fetch.py          # 主提取脚本

pyproject.toml            # 新增 playwright + markdownify 依赖
```

---

## Task 1: 项目依赖配置

**Files:**
- Modify: `pyproject.toml`
- Run: `uv sync`

- [ ] **Step 1: 添加依赖到 pyproject.toml**

在 `[project] dependencies` 中追加：

```toml
dependencies = [
    # ... existing
    "playwright>=1.43.0",
    "markdownify>=1.1.0",
]
```

- [ ] **Step 2: 同步依赖**

```bash
uv sync
```

---

## Task 2: 核心提取脚本

**Files:**
- Create: `.agents/skills/wechat-article-fetcher/scripts/fetch.py`
- Create: `.agents/skills/wechat-article-fetcher/SKILL.md`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p .agents/skills/wechat-article-fetcher/scripts
```

- [ ] **Step 2: 实现主提取脚本**

`fetch.py` 职责分解：

1. **CLI 参数解析**（`argparse`）
   - `url`: 公众号文章 URL
   - `--output-dir`: 输出目录，默认 `./wechat-articles/`
   - `--no-images`: 不下载图片

2. **依赖检查**（启动时）
   - 检查 `playwright` 是否安装 → 未安装报错提示 `uv sync`
   - 检查 `markdownify` 是否安装
   - 检查本机 Chrome 是否存在 → 未找到报错提示安装 Chrome

3. **Playwright 浏览器启动**
   - `launch_persistent_context`:
     - `user_data_dir`: `~/.config/wechat-article-fetcher/profile/`（macOS 自动映射到 `~/Library/Application Support/`）
     - `executable_path`: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
     - `headless=False`
     - `args=["--disable-blink-features=AutomationControlled"]`

4. **页面导航**
   - `page.goto(url, wait_until="networkidle", timeout=30000)`
   - `page.wait_for_selector("#js_content", timeout=15000)`

5. **登录态检测**
   - 如果 `#js_content` 未出现且页面有登录相关元素：
     - 打印提示："未检测到微信登录态。请在弹出的浏览器窗口中登录，完成后按回车继续..."
     - `input()` 阻塞等待
     - `page.reload()`
     - 再次检查 `#js_content`
     - 仍失败 → 返回 `LOGIN_FAILED`

6. **元数据提取**
   - 标题：`#activity-name`
   - 公众号：`#js_name`
   - 发布时间：`#publish_time`（失败时从 `var ct` 或 meta 兜底）

7. **正文提取**
   - `page.locator("#js_content").inner_html()`
   - HTML 预清洗：修复 `<pre>` 内 `<p>` 标签结构
   - `markdownify(html, heading_style="ATX")`
   - Markdown 后清洗：压缩连续空行

8. **图片处理**（如果 `--no-images` 则跳过）
   - 提取 `#js_content img` 的 `data-src`
   - 用 `requests` 下载到 `assets/img-{index}.{ext}`
   - 请求头：`Referer: https://mp.weixin.qq.com/`
   - Markdown 中替换为 `assets/img-{index}.jpg`
   - 下载失败记录 warning，不阻断主流程

9. **素材包写入**
   - `article.md`：frontmatter + 正文
   - `manifest.json`：元数据 + 图片清单
   - `sources.md`：来源声明、抓取日期
   - `assets/`：图片目录

10. **错误码**
    - `CONTENT_NOT_RENDERED`: `#js_content` 超时
    - `VERIFICATION_REQUIRED`: 验证码页
    - `ARTICLE_DELETED`: 文章已删除
    - `LOGIN_FAILED`: 登录后仍无法获取

- [ ] **Step 3: 创建 SKILL.md**

参考 `.agents/skills/video-material-ingest/SKILL.md` 格式：
- frontmatter: `name`, `description`
- When To Use
- Prerequisites
- Default Command
- Output
- Follow-Ups

---

## Task 3: 端到端验证

**Files:**
- Run: `.agents/skills/wechat-article-fetcher/scripts/fetch.py`

- [ ] **Step 1: 验证成功提取**

```bash
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py \
  "https://mp.weixin.qq.com/s?__biz=MzkxNjcyMDE0MQ==&mid=2247488445&idx=1&sn=77e6db996c5feaf0b676385c515a5cd8"
```

预期：成功输出素材包到 `./wechat-articles/`，包含 `article.md`, `manifest.json`, `assets/`。

- [ ] **Step 2: 验证 --output-dir**

```bash
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py \
  "https://mp.weixin.qq.com/s?__biz=MzkxNjcyMDE0MQ==&mid=2247488445&idx=1&sn=77e6db996c5feaf0b676385c515a5cd8" \
  --output-dir content/inbox/articles/
```

预期：素材包出现在 `content/inbox/articles/YYYY-MM-DD-<slug>/`。

- [ ] **Step 3: 验证 --no-images**

```bash
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py \
  "https://mp.weixin.qq.com/s?__biz=MzkxNjcyMDE0MQ==&mid=2247488445&idx=1&sn=77e6db996c5feaf0b676385c515a5cd8" \
  --no-images
```

预期：`assets/` 目录不存在或为空。

- [ ] **Step 4: 验证错误处理**

```bash
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py \
  "https://mp.weixin.qq.com/s?__biz=INVALID&mid=0"
```

预期：返回明确错误码（如 `ARTICLE_DELETED` 或 `CONTENT_NOT_RENDERED`）。

- [ ] **Step 5: 验证登录态引导**

首次使用或 Cookie 过期时：
- 脚本暂停，提示"请在弹出的浏览器窗口中登录"
- 用户登录后按回车
- 脚本自动继续

---

## Task 4: 清理与提交

- [ ] **Step 1: git add**

```bash
git add pyproject.toml uv.lock .agents/skills/wechat-article-fetcher/
```

- [ ] **Step 2: commit**

```bash
git commit -m "feat: add wechat-article-fetcher skill

- Playwright + 本地持久化 Profile 提取公众号文章
- 支持标题/正文/公众号名/发布时间/图片提取
- 交互式登录态引导
- --output-dir 和 --no-images CLI 选项
- 素材包结构：article.md + manifest.json + sources.md + assets/"
```

---

## Self-Review Checklist

### Spec Coverage

| 设计文档需求 | 对应任务 |
|-------------|---------|
| Playwright + 持久化 Profile | Task 2 Step 2 |
| 单 URL 输入 | Task 2 Step 2 CLI |
| 素材包结构 | Task 2 Step 2 第 9 步 |
| 图片落地 | Task 2 Step 2 第 8 步 |
| `--output-dir` / `--no-images` | Task 2 Step 2 第 1 步 |
| 登录态交互式引导 | Task 2 Step 2 第 5 步 |
| 格式清洗 | Task 2 Step 2 第 7 步 |
| 错误码 | Task 2 Step 2 第 10 步 |
| 依赖检查（不自动安装）| Task 2 Step 2 第 2 步 |
| uv 工具链 | 所有 `uv run` 命令 |

### Placeholder Scan

- [x] 无 TBD/TODO
- [x] 所有步骤有具体命令和预期输出
- [x] 文件路径具体
- [x] 代码职责明确分解

### Type Consistency

- [x] `manifest.json` 字段名与设计文档一致
- [x] CLI 参数名与设计文档一致
- [x] 错误码常量与 spec 一致
