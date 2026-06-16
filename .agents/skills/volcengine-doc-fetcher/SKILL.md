---
name: volcengine-doc-fetcher
description: >
  Fetch Volcano Engine (火山引擎) official documentation pages as clean Markdown. Use this skill whenever the user provides a volcengine.com/docs/ URL, wants to look up a Volcano Engine API reference, needs to check API parameters, models, or product documentation from 火山引擎, or mentions 火山引擎文档/火山引擎API/火山引擎接口文档. Also use when the user says "查一下火山引擎的...", "帮我看一下豆包/方舟/Seedance 的 API 文档", or pastes any volcengine.com URL. Supports single and multi-URL concurrent fetching with Playwright (default, free) and Firecrawl (fallback). This skill should ALWAYS be used for fetching Volcano Engine doc pages — never use WebFetch, firecrawl-scrape, or raw curl directly for volcengine.com URLs.
---

# Volcengine Doc Fetcher

Fetch Volcano Engine official documentation pages as clean, structured Markdown. Handles JS-rendered SPA pages that return empty content with simple HTTP requests.

## Quick Start

```bash
# Single URL — outputs clean Markdown to stdout
uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032"

# Multiple URLs — concurrent fetch
uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032" "https://www.volcengine.com/docs/6561/1257544"

# Save to directory
uv run scripts/fetch.py --output-dir ./volcengine-docs/ "https://www.volcengine.com/docs/6561/2499930"
```

## Script

The core implementation is `scripts/fetch.py` — a PEP 723 inline-dependency Python script.

**Always run with `uv run`** — it auto-creates an isolated environment from the inline metadata. Never use bare `python` or `pip`.

Dependencies: `playwright`, `beautifulsoup4`, `markdownify`, `lxml`. Playwright browsers must be installed (`playwright install chromium`).

## Prerequisites

- `uv` (Python package manager)
- `playwright` with Chromium installed: `uv run playwright install chromium`
- Google Chrome or Chromium available on the system

## Fetch Strategy

The script uses a two-tier strategy controlled by `--method`:

| Method | Behavior |
|--------|----------|
| `auto` (default) | Playwright first, auto-fallback to Firecrawl on failure |
| `playwright` | Playwright only, fail if unavailable |
| `firecrawl` | Firecrawl only, fail if unavailable |

**Playwright** is the default and recommended method: launches headless Chromium, waits for JS rendering, extracts the doc content area, cleans noise, and converts to Markdown. Free, local, unlimited.

**Firecrawl** is the fallback: uses `firecrawl scrape --wait-for 5000` to handle JS rendering. Requires Firecrawl CLI to be installed and authenticated. Consumes credits.

When `auto` falls back from Playwright to Firecrawl, a warning is printed to stderr.

## CLI Reference

```
uv run scripts/fetch.py [OPTIONS] URL [URL...]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `URL` | One or more Volcano Engine doc URLs to fetch |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--method` | `auto` | Fetch method: `auto`, `playwright`, `firecrawl` |
| `--output-dir`, `-o` | — | Save output to directory instead of stdout. Each URL gets `{slug}.md` and `{slug}.meta.json` |
| `--no-cache` | — | Bypass cache, force re-fetch |
| `--cache-ttl` | `3600` | Cache TTL in seconds (default: 1 hour) |
| `--concurrency`, `-c` | `3` | Max concurrent fetches for multi-URL |
| `--json` | — | Output JSON to stdout (includes metadata). Without `--json`, outputs Markdown |
| `--timeout` | `30` | Page load timeout in seconds |

## Output Format

### Default (stdout Markdown)

When no `--output-dir` is given, each URL's Markdown is printed to stdout, separated by `---` dividers:

```
# Page Title

Page content in clean Markdown...

---
# Second Page Title

Second page content...
```

### JSON mode (`--json`)

```json
[
  {
    "url": "https://www.volcengine.com/docs/6561/163032",
    "title": "产品简介--豆包语音-火山引擎",
    "method": "playwright",
    "cached": false,
    "markdown": "# 产品简介\n\n...",
    "fetched_at": "2026-06-16T15:30:00+08:00"
  }
]
```

### File mode (`--output-dir`)

```
<output-dir>/
  {slug}.md            # Clean Markdown body
  {slug}.meta.json     # Metadata sidecar
```

The slug is derived from the URL path (e.g., `docs/6561/163032` → `6561-163032`).

Metadata sidecar:
```json
{
  "url": "https://www.volcengine.com/docs/6561/163032",
  "title": "产品简介--豆包语音-火山引擎",
  "method": "playwright",
  "cached": false,
  "fetched_at": "2026-06-16T15:30:00+08:00",
  "slug": "6561-163032"
}
```

## Content Cleaning

The script performs these cleaning steps on the fetched HTML:

1. **DOM targeting**: Extracts only the doc content area (`[class*="content"][class*="doc"]`), discarding navigation, sidebars, headers, and footers
2. **Noise removal**: Strips breadcrumbs, toolbar buttons (copy, download, favorite), feedback widgets, and prev/next navigation
3. **HTML → Markdown**: Converts via `markdownify` with ATX headings, preserving tables, code blocks, and links
4. **Post-processing**: Removes zero-width spaces (`​`), strips inline base64 icon images, normalizes whitespace

The output is clean, readable Markdown suitable for direct agent consumption.

## Caching

Fetched pages are cached at `~/.cache/volcengine-docs/` with a configurable TTL (default: 1 hour). Cache keys are URL hashes.

- Cache hits return instantly — no network or browser overhead
- Use `--no-cache` to force a fresh fetch
- Use `--cache-ttl` to adjust the TTL (e.g., `--cache-ttl 86400` for 24 hours)
- Cache is shared across projects, so fetching the same URL in different repos reuses the cached version

## Error Handling

- **Playwright failure** (browser not found, timeout, empty content): In `auto` mode, falls back to Firecrawl automatically. In `playwright` mode, exits with error
- **Firecrawl failure** (not installed, auth error, credit exhausted): Reports error with specific guidance
- **URL not found** (404): Reports error for that URL, continues with others
- **Timeout**: Configurable with `--timeout`, defaults to 30s
- **Concurrent fetch errors**: Failed URLs report errors individually; successful ones continue independently

## When to Use This Skill

- User provides a `volcengine.com/docs/` URL
- User wants to check Volcano Engine API parameters, models, or product docs
- User mentions 火山引擎文档, 火山引擎API, 火山引擎接口, 豆包 API, 方舟 API, Seedance API
- User says "查一下火山引擎的...", "帮我看一下这个接口文档", "这个 API 怎么用"
- User needs up-to-date Volcano Engine documentation for coding

## When NOT to Use

- General web search about Volcano Engine — use `volcengine-web-search` or `byted-web-search`
- Non-Volcano Engine URLs — use `firecrawl-scrape` or `WebFetch`
- Volcano Engine TTS voice generation — use `volcengine-tts`
- Volcano Engine image/video generation — use `seedream-image-gen` or `seedance-video-gen`
