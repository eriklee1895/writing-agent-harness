#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
"""
volcengine-web-search — Volcano Engine web search CLI.

Search the web via Volcano Engine's Doubao Search API. Supports web search and
image search with structured JSON output for agent consumption.

Usage:
    uv run search.py "query" [OPTIONS]

Examples:
    uv run search.py "北京三日游攻略" --json
    uv run search.py "latest AI research" --type web --count 5 --time-range month
    uv run search.py "故宫雪景" --type image --count 3
    uv run search.py "site:github.com transformers" --sites "github.com"
    uv run search.py "金融政策" --industry finance --authoritative-only
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import requests

API_BASE_URL = "https://open.feedcoopapi.com/search_api/web_search"
DEFAULT_COUNT = 10
MAX_WEB_COUNT = 50
MAX_IMAGE_COUNT = 5
SUMMARY_PREVIEW_LIMIT = 800

# ── API key resolution ──────────────────────────────────────────────


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and blank lines."""
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def resolve_api_key(cli_key: Optional[str]) -> str:
    """Resolve API key in priority order:
    1. --api-key CLI argument
    2. VOLC_WEB_SEARCH_API_KEY environment variable
    3. .env file in the same directory as this script
    4. .env file in the current working directory
    """
    if cli_key:
        return cli_key

    env_key = os.environ.get("VOLC_WEB_SEARCH_API_KEY")
    if env_key:
        return env_key

    script_dir = Path(__file__).resolve().parent
    script_env = load_env_file(script_dir / ".env")
    if "VOLC_WEB_SEARCH_API_KEY" in script_env:
        return script_env["VOLC_WEB_SEARCH_API_KEY"]

    cwd_env = load_env_file(Path.cwd() / ".env")
    if "VOLC_WEB_SEARCH_API_KEY" in cwd_env:
        return cwd_env["VOLC_WEB_SEARCH_API_KEY"]

    sys.exit(
        "Error: No API key found.\n"
        "  Set VOLC_WEB_SEARCH_API_KEY environment variable, or\n"
        "  pass --api-key KEY, or\n"
        "  create a .env file with VOLC_WEB_SEARCH_API_KEY=your-key\n"
        "  Get an API key at: https://console.volcengine.com/search-infinity/api-key"
    )


# ── API client ───────────────────────────────────────────────────────


def search(api_key: str, params: dict, timeout: int = 30) -> dict:
    """Execute a search request against the Volcano Engine API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        API_BASE_URL, json=params, headers=headers, timeout=timeout
    )
    data = response.json()

    # Surface API-level errors
    error = data.get("ResponseMetadata", {}).get("Error")
    if error:
        code = error.get("Code", "unknown")
        message = error.get("Message", "Unknown error")
        sys.exit(f"API error [{code}]: {message}")

    return data


# ── Output formatters ────────────────────────────────────────────────


def format_human(data: dict, search_type: str, elapsed: float) -> str:
    """Format search results for human consumption."""
    result = data.get("Result", {})
    count = result.get("ResultCount", 0)
    query = result.get("SearchContext", {}).get("OriginQuery", "")

    lines = [f"🔍 搜索: \"{query}\" ({count} 条结果, {elapsed:.1f}s)\n"]

    if search_type == "image":
        images = result.get("ImageResults", [])
        for i, img in enumerate(images, 1):
            image = img.get("Image", {})
            lines.append(
                f"{i}. {img.get('Title', '无标题')}\n"
                f"   📎 {img.get('SiteName', '?')} | "
                f"{image.get('Width', '?')}×{image.get('Height', '?')} | "
                f"{img.get('BlurDes', '?')}\n"
                f"   🔗 {image.get('Url', '')}\n"
            )
    else:
        results = result.get("WebResults", [])
        for i, item in enumerate(results, 1):
            score = item.get("RankScore", 0)
            stars = "⭐" * min(5, int(score * 5 + 1))
            published = item.get("PublishTime", "")[:10] if item.get("PublishTime") else "?"
            authority = item.get("AuthInfoDes", "")

            lines.append(f"{i}. {item.get('Title', '无标题')}")
            meta_parts = [f"📎 {item.get('SiteName', '?')}"]
            if published:
                meta_parts.append(f"🕐 {published}")
            if score:
                meta_parts.append(f"{stars} {score:.2f}")
            if authority:
                meta_parts.append(f"🏛 {authority}")
            lines.append(f"   {' | '.join(meta_parts)}")

            summary = item.get("Summary") or item.get("Snippet", "")
            if summary:
                truncated = summary[:SUMMARY_PREVIEW_LIMIT]
                if len(summary) > SUMMARY_PREVIEW_LIMIT:
                    truncated += "…"
                lines.append(f"   {truncated}")

            url = item.get("Url", "")
            if url:
                lines.append(f"   🔗 {url}")
            lines.append("")

    return "\n".join(lines)


def format_json(data: dict, elapsed: float) -> str:
    """Output results as JSON, adding CLI metadata."""
    output = {
        "elapsed_ms": int(elapsed * 1000),
        "api_response": data,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# ── CLI argument parsing ─────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="volcengine-web-search",
        description="Search the web via Volcano Engine's Doubao Search API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run search.py "北京三日游攻略" --json
  uv run search.py "AI research" --count 5 --time-range month
  uv run search.py "故宫雪景" --type image --count 3
  uv run search.py "金融政策" --industry finance --authoritative-only
  uv run search.py "site:github.com transformers" --sites "github.com"

API key sources (checked in order):
  --api-key CLI argument
  VOLC_WEB_SEARCH_API_KEY environment variable
  .env file in script directory
  .env file in current working directory

Output formats:
  Default: human-readable text with emoji markers
  --json:   structured JSON for agent/programmatic consumption
        """,
    )

    parser.add_argument(
        "query",
        type=str,
        help="Search query (1–100 characters, truncated if longer).",
    )
    parser.add_argument(
        "--type",
        dest="search_type",
        choices=["web", "image"],
        default="web",
        help="Search type: web (default) or image.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=f"Number of results. Max {MAX_WEB_COUNT} for web, {MAX_IMAGE_COUNT} for image. (default: {DEFAULT_COUNT})",
    )
    parser.add_argument(
        "--time-range",
        type=str,
        default=None,
        help="Time filter: day, week, month, year, or YYYY-MM-DD..YYYY-MM-DD range.",
    )
    parser.add_argument(
        "--sites",
        type=str,
        default=None,
        help="Restrict search to specific domains, separated by |. Max 20.",
    )
    parser.add_argument(
        "--block-sites",
        type=str,
        default=None,
        help="Block domains from results, separated by |. Max 5.",
    )
    parser.add_argument(
        "--need-content",
        action="store_true",
        default=False,
        help="Return full page content (larger response).",
    )
    parser.add_argument(
        "--need-summary",
        action="store_true",
        default=False,
        help="Return query-relevant summaries alongside snippets.",
    )
    parser.add_argument(
        "--authoritative-only",
        action="store_true",
        default=False,
        help="Return only highly authoritative sources.",
    )
    parser.add_argument(
        "--industry",
        choices=["finance", "game"],
        default=None,
        help="Industry-specific search context.",
    )
    parser.add_argument(
        "--query-rewrite",
        action="store_true",
        default=False,
        help="Enable server-side query rewriting (adds latency).",
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="Output results as structured JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override the API key (otherwise read from env/file).",
    )

    return parser


def validate_args(args: argparse.Namespace):
    """Validate and adjust arguments against API constraints."""
    if args.search_type == "image" and args.count > MAX_IMAGE_COUNT:
        print(
            f"Warning: Image search max count is {MAX_IMAGE_COUNT}, clamping --count from {args.count} to {MAX_IMAGE_COUNT}.",
            file=sys.stderr,
        )
        args.count = MAX_IMAGE_COUNT
    elif args.search_type == "web" and args.count > MAX_WEB_COUNT:
        print(
            f"Warning: Web search max count is {MAX_WEB_COUNT}, clamping --count from {args.count} to {MAX_WEB_COUNT}.",
            file=sys.stderr,
        )
        args.count = MAX_WEB_COUNT

    if len(args.query) > 100:
        print(
            f"Warning: Query truncated from {len(args.query)} to 100 characters.",
            file=sys.stderr,
        )
        args.query = args.query[:100]


# ── Time range normalization ─────────────────────────────────────────

TIME_RANGE_MAP = {
    "day": "OneDay",
    "week": "OneWeek",
    "month": "OneMonth",
    "year": "OneYear",
}


def normalize_time_range(value: str) -> str:
    """Convert CLI-friendly time range to API format."""
    if value is None:
        return None
    lowered = value.lower()
    if lowered in TIME_RANGE_MAP:
        return TIME_RANGE_MAP[lowered]
    # Pass through as-is (custom date range like 2025-01-01..2025-06-01)
    return value


# ── Main ─────────────────────────────────────────────────────────────


def main():
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)

    api_key = resolve_api_key(args.api_key)

    # Build request payload
    payload: dict = {
        "Query": args.query,
        "SearchType": args.search_type,
        "Count": args.count,
    }

    time_range = normalize_time_range(args.time_range)
    if time_range:
        payload["TimeRange"] = time_range

    if args.sites:
        payload["Sites"] = args.sites
    if args.block_sites:
        payload["BlockHosts"] = args.block_sites
    if args.need_content:
        payload["NeedContent"] = True
    if args.need_summary:
        payload["NeedSummary"] = True
    if args.authoritative_only:
        payload["AuthInfoLevel"] = 1
    if args.industry:
        payload["Industry"] = args.industry
    if args.query_rewrite:
        payload["QueryRewrite"] = True

    # Execute search
    start = time.monotonic()
    try:
        data = search(api_key, payload)
    except requests.exceptions.Timeout:
        sys.exit("Error: Request timed out after 30 seconds.")
    except requests.exceptions.ConnectionError:
        sys.exit(
            "Error: Could not connect to the API. Check your network connection."
        )
    elapsed = time.monotonic() - start

    # Output
    if args.json_output:
        print(format_json(data, elapsed))
    else:
        print(format_human(data, args.search_type, elapsed))


if __name__ == "__main__":
    main()
