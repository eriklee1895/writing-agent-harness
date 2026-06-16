---
name: volcengine-web-search
description: 火山引擎联网搜索 API — 网页搜索和图片搜索。Use when the user wants to search the web, find articles, look up Chinese-language information, get recent news, or says 搜一下/查一下/搜索/找找/网上有没有/搜图片/中文搜索/国内信息. 基于火山引擎 Doubao Search API，中文内容覆盖和时效性优于通用搜索引擎。Trigger on any web search intent, especially Chinese-language or China-focused queries.
allowed-tools: Bash(uv run:*)
---

# Volcano Engine Web Search

Search the web via Volcano Engine's Doubao Search API. Run the CLI script to get web or image results, then synthesize an answer from the output.

## Quick start

```bash
uv run scripts/search.py "query" --json
```

Always use `--json` for structured output that includes all API fields. The script auto-discovers the API key from `VOLC_WEB_SEARCH_API_KEY` env var, the project `.env` file, or `--api-key`.

## Common patterns

### Web search (default)
```bash
uv run scripts/search.py "搜索关键词" --json --count 10 --need-summary
```

- `--need-summary` returns a query-relevant summary for each result (recommended for LLM consumption).
- `--count` max 50, default 10.

### Time-filtered search
```bash
uv run scripts/search.py "query" --json --time-range week
```
Values: `day`, `week`, `month`, `year`, or `YYYY-MM-DD..YYYY-MM-DD`.

### Authoritative sources only
```bash
uv run scripts/search.py "query" --json --authoritative-only
```

### Domain filtering
```bash
# Restrict to specific sites
uv run scripts/search.py "query" --json --sites "github.com|zhihu.com"

# Block specific sites
uv run scripts/search.py "query" --json --block-sites "spam.com"
```

### Image search
```bash
uv run scripts/search.py "query" --type image --count 5 --json
```
Max 5 image results. Returns URLs, dimensions, clarity info.

### Industry context
```bash
uv run scripts/search.py "query" --json --industry finance
```
Options: `finance`, `game`.

### Full page content
```bash
uv run scripts/search.py "query" --json --need-content
```
Returns full page text (larger response, use sparingly).

## Output format

`--json` output wraps the full API response with CLI metadata:

```json
{
  "elapsed_ms": 532,
  "api_response": {
    "Result": {
      "ResultCount": 10,
      "WebResults": [
        {
          "Title": "...",
          "Url": "...",
          "SiteName": "...",
          "Snippet": "...",
          "Summary": "...",
          "Content": "...",
          "PublishTime": "2026-06-15T01:01:49+08:00",
          "RankScore": 0.81,
          "AuthInfoDes": "正常权威",
          "AuthInfoLevel": 2
        }
      ]
    }
  }
}
```

Key fields for synthesizing answers:
- `Summary` — query-relevant summary (500-1000 chars), preferred over `Snippet`
- `Snippet` — short excerpt (~200 chars), may be truncated
- `Content` — full page text (only with `--need-content`)
- `RankScore` — relevance 0-1
- `PublishTime` — ISO 8601 with timezone
- `AuthInfoDes` — authority level: 非常权威/正常权威/一般权威/一般不权威

## API key

The script resolves the API key in this order:
1. `--api-key` CLI argument
2. `VOLC_WEB_SEARCH_API_KEY` environment variable
3. `.env` file in the script directory
4. `.env` file in the current working directory

Get an API key at: https://console.volcengine.com/search-infinity/api-key

## Best practices

- Always use `--json` so the output is machine-parseable.
- Include `--need-summary` for richer context in web searches.
- Prefer `--time-range` when the user's question implies recency.
- Use `--authoritative-only` when factual accuracy is critical.
- For image searches, always set `--type image` explicitly.
- Keep queries under 100 characters (API limit).
- If results look low-quality, try `--authoritative-only` or restrict `--sites`.
