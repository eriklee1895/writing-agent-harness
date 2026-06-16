---
name: wechat-article-fetcher
description: 提取微信公众号文章（mp.weixin.qq.com）为结构化 Markdown + assets，用于 AI 写作素材收集。Use when the user provides a WeChat article URL and wants to extract its content for research, reference, or writing material.
---

# WeChat Article Fetcher

提取微信公众号文章为结构化 Markdown + assets，用于 AI 写作素材收集和参考引用。

Use this skill when the user provides a WeChat article URL (`mp.weixin.qq.com/s/...`) and wants to extract its content for research, reference, or writing material.

## When To Use

- 用户给了一个公众号文章链接，要求提取内容作为写作参考
- 需要把公众号文章整理成可追踪的本地素材
- 收集公众号文章中的数据、观点、案例用于后续写作

Do not use this skill for / 禁止场景：
- Discovering articles by topic or keyword (no search capability) — 不支持按主题或关键词搜索文章
- Batch processing multiple URLs — 暂不支持批量处理多个链接
- Extracting video cards or embedded media — 暂不支持提取视频卡片或嵌入式媒体
- Republishing or redistributing content without permission — 禁止无授权转载或再分发

## Prerequisites

- `uv` 必须可用；依赖由脚本 PEP 723 inline metadata 自声明，`uv run` 自动安装
- `playwright`、`beautifulsoup4`、`markdownify` 和 `lxml` Python 包已安装（运行时自动检查；`lxml` 是可选 fallback，没装会自动回退到 `html.parser`）
- Google Chrome 已安装（macOS 默认路径 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`）
- Chrome 已登录微信（首次使用会弹出交互式登录引导）

禁止导出、打印、存储或提交浏览器 Cookie 和登录态数据。

## Default Command

```bash
# 默认输出到 ./wechat-articles/YYYY-MM-DD-<slug>/
uv run scripts/fetch.py <url>

# 指定输出目录（项目级用法）
uv run scripts/fetch.py <url> --output-dir content/inbox/articles/

# 快速提取，不下载图片
uv run scripts/fetch.py <url> --no-images
```

## Output

每次提取生成一个文件夹：

```text
<output-dir>/
└── YYYY-MM-DD-<slug>/      # <slug> 为裸 topic，目录名带日期前缀
    ├── article.md          # Markdown 正文，含 YAML frontmatter
    ├── manifest.json       # 结构化元数据和图片索引
    ├── sources.md          # 来源声明和合规提醒
    └── assets/
        ├── img-001.jpg
        └── ...
```

### article.md

Contains YAML frontmatter with `title`, `account`, `publish_time`, `source_url`, followed by the article body in Markdown. Images reference `assets/` via relative paths.

包含 YAML frontmatter（`title`, `account`, `publish_time`, `source_url`），后跟 Markdown 正文。图片通过相对路径引用 `assets/` 目录。

### manifest.json

Structured metadata including title, account, publish time, fetch timestamp, content length, and an array of image records with `original_url`, `local_path`, and `alt` text.

结构化元数据，包括标题、公众号名、发布时间、抓取时间戳、内容长度，以及图片记录数组（含 `original_url`, `local_path`, `alt`）。

### sources.md

Records source URL, account, fetch date, and a compliance reminder for personal research use only.

记录来源 URL、公众号名、抓取日期，以及个人研究用途的合规提醒。

## Login Flow

首次使用或 Cookie 过期时，如果未检测到微信登录态：

1. 浏览器窗口打开文章页面
2. 脚本提示：`"未检测到微信登录态。请在弹出的浏览器窗口中登录（扫码或密码），完成后按回车继续..."`
3. 用户完成登录后按回车
4. 脚本自动刷新页面并继续提取

如果登录后仍无法获取内容，返回错误码 `LOGIN_FAILED`。

## Error Handling

| Error Code | Meaning |
|------------|---------|
| `CONTENT_NOT_RENDERED` | `#js_content` not found after timeout |
| `VERIFICATION_REQUIRED` | Page shows verification or captcha |
| `ARTICLE_DELETED` | Article appears deleted or not found |
| `LOGIN_FAILED` | Login attempted but content still unavailable |

错误以 JSON 形式返回，包含 `error_code` 和 `message` 字段。

## Follow-Ups

提取完成后，可以建议下一步：

- Read `article.md` for content summary or key points
- Move the folder to `content/inbox/articles/YYYY-MM-DD-<slug>/` or `content/origin/YYYY-MM-DD-<slug>/` if it becomes canonical material.
- Use `article-illustration` to generate companion visuals
- Reference the article in a new draft with proper attribution

除非用户明确要求，否则不要自动执行这些后续操作。
