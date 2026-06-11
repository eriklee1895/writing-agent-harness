---
name: wechat-article-fetcher
description: 提取微信公众号文章（mp.weixin.qq.com）为结构化 Markdown + assets，用于 AI 写作素材收集。Use when the user provides a WeChat article URL and wants to extract its content for research, reference, or writing material.
---

# WeChat Article Fetcher / 微信公众号文章提取

提取微信公众号文章为结构化 Markdown + assets，用于 AI 写作素材收集和参考引用。

Use this skill when the user provides a WeChat article URL (`mp.weixin.qq.com/s/...`) and wants to extract its content for research, reference, or writing material.

## When To Use / 使用场景

- 用户给了一个公众号文章链接，要求提取内容作为写作参考
- 需要把公众号文章整理成可追踪的本地素材
- 收集公众号文章中的数据、观点、案例用于后续写作

Do not use this skill for:
- Discovering articles by topic or keyword (no search capability) — 不支持搜索发现
- Batch processing multiple URLs — MVP 只支持单篇
- Extracting video cards or embedded media — 暂不支持视频卡片
- Republishing or redistributing content without permission — 禁止无授权转载

## Prerequisites / 前置条件

- `uv` 必须可用，且项目依赖已同步 (`uv sync`)
- `playwright` 和 `markdownify` Python 包已安装（运行时自动检查）
- Google Chrome 已安装（macOS 默认路径 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`）
- Chrome 已登录微信（首次使用会弹出交互式登录引导）

Never export, print, store, or commit browser cookies or login state data.
禁止导出、打印、存储或提交浏览器 Cookie 和登录态数据。

## Default Command / 默认命令

```bash
# 默认输出到 ./wechat-articles/YYYY-MM-DD-<slug>/
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url>

# 指定输出目录（项目级用法）
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --output-dir content/inbox/articles/

# 快速提取，不下载图片
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --no-images
```

## Output / 产物结构

每次提取生成一个文件夹：

```text
<output-dir>/
└── YYYY-MM-DD-<slug>/
    ├── article.md          # Markdown 正文，含 YAML frontmatter
    ├── manifest.json       # 结构化元数据和图片索引
    ├── sources.md          # 来源声明和合规提醒
    └── assets/
        ├── img-001.jpg
        └── ...
```

### article.md

包含 YAML frontmatter（`title`, `account`, `publish_time`, `source_url`），后跟 Markdown 正文。图片通过相对路径引用 `assets/` 目录。

### manifest.json

结构化元数据，包括标题、公众号名、发布时间、抓取时间戳、内容长度，以及图片记录数组（含 `original_url`, `local_path`, `alt`）。

### sources.md

记录来源 URL、公众号名、抓取日期，以及个人研究用途的合规提醒。

## Login Flow / 登录流程

首次使用或 Cookie 过期时，如果未检测到微信登录态：

1. 浏览器窗口打开文章页面
2. 脚本提示：`"未检测到微信登录态。请在弹出的浏览器窗口中登录（扫码或密码），完成后按回车继续..."`
3. 用户完成登录后按回车
4. 脚本自动刷新页面并继续提取

如果登录后仍无法获取内容，返回错误码 `LOGIN_FAILED`。

## Error Handling / 错误处理

| Error Code | Meaning / 含义 |
|------------|---------------|
| `CONTENT_NOT_RENDERED` | `#js_content` 渲染超时，正文未出现 |
| `VERIFICATION_REQUIRED` | 页面出现验证码或人机验证 |
| `ARTICLE_DELETED` | 文章已删除或不存在 |
| `LOGIN_FAILED` | 尝试登录后仍无法获取内容 |

错误以 JSON 形式返回，包含 `error_code` 和 `message` 字段。

## Follow-Ups / 后续建议

提取完成后，可以建议下一步：

- 阅读 `article.md` 了解文章要点和关键信息
- 如果文章成为核心素材，将文件夹移动到 `content/source/<slug>/`
- 使用 `article-illustration` 生成配套插图
- 在新建草稿中引用该文章并注明来源

Do not perform these follow-ups unless the user asks.
除非用户要求，否则不自动执行这些后续操作。
