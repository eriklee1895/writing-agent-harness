---
name: wechat-article-fetcher
description: Fetch WeChat public account articles (mp.weixin.qq.com) into structured Markdown + assets for writing research and reference.
---

# WeChat Article Fetcher

Use this skill when the user provides a WeChat article URL (`mp.weixin.qq.com/s/...`) and wants to extract its content for research, reference, or writing material.

Do not use this skill for:
- Discovering articles by topic or keyword (no search capability)
- Batch processing multiple URLs
- Extracting video cards or embedded media
- Republishing or redistributing content without permission

## Prerequisites

- `uv` must be available and project dependencies synced (`uv sync`)
- `playwright` and `markdownify` Python packages must be installed (checked at runtime)
- Google Chrome must be installed at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (macOS)
- Chrome must be logged into WeChat (interactive login prompt on first use)

Never export, print, store, or commit browser cookies or login state data.

## Default Command

```bash
# Default output to ./wechat-articles/YYYY-MM-DD-<slug>/
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url>

# Specify output directory (project-level usage)
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --output-dir content/inbox/articles/

# Skip image download for faster extraction
uv run python .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --no-images
```

## Output

Each fetch creates a folder:

```text
<output-dir>/
└── YYYY-MM-DD-<slug>/
    ├── article.md          # Markdown content with YAML frontmatter
    ├── manifest.json       # Structured metadata and image index
    ├── sources.md          # Source citation and compliance note
    └── assets/
        ├── img-001.jpg
        └── ...
```

### article.md

Contains YAML frontmatter with `title`, `account`, `publish_time`, `source_url`, followed by the article body in Markdown. Images reference `assets/` via relative paths.

### manifest.json

Structured metadata including title, account, publish time, fetch timestamp, content length, and an array of image records with `original_url`, `local_path`, and `alt` text.

### sources.md

Records source URL, account, fetch date, and a compliance reminder for personal research use only.

## Login Flow

If WeChat login is not detected:

1. A browser window opens with the article page
2. The script prints: `"未检测到微信登录态。请在弹出的浏览器窗口中登录（扫码或密码），完成后按回车继续..."`
3. User logs in and presses Enter
4. The script reloads the page and continues extraction

If content is still unavailable after login, returns error code `LOGIN_FAILED`.

## Error Handling

| Error Code | Meaning |
|------------|---------|
| `CONTENT_NOT_RENDERED` | `#js_content` not found after timeout |
| `VERIFICATION_REQUIRED` | Page shows verification or captcha |
| `ARTICLE_DELETED` | Article appears deleted or not found |
| `LOGIN_FAILED` | Login attempted but content still unavailable |

Errors are returned as JSON with `error_code` and `message` fields.

## Follow-Ups

After fetching, suggest the next useful step:

- Read `article.md` for content summary or key points
- Move the folder to `content/source/<slug>/` if it becomes canonical material
- Use `article-illustration` to generate companion visuals
- Reference the article in a new draft with proper attribution

Do not perform these follow-ups unless the user asks.
