#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4>=4.12",
#   "lxml>=5.0",
#   "markdownify>=1.1",
#   "playwright>=1.50",
# ]
# ///

"""
Fetch Volcano Engine (火山引擎) documentation pages as clean Markdown.

Uses Playwright (headless Chromium) as the default method with Firecrawl
as an automatic fallback. Supports single and multi-URL concurrent fetching
with local caching.

Usage:
    uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032"
    uv run scripts/fetch.py --output-dir ./docs/ url1 url2 url3
    uv run scripts/fetch.py --method firecrawl --no-cache "https://..."
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

CACHE_DIR = Path.home() / ".cache" / "volcengine-docs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# CSS selector for the doc content area on volcengine.com/docs pages.
# Uses fuzzy class matching because Volcengine uses CSS modules with hashed
# class names (e.g., "content-skqm contentdoc-wqiC"). This selector has been
# verified across multiple product doc pages (豆包语音, 火山方舟, etc.).
CONTENT_SELECTOR = '[class*="content"][class*="doc"]'

# Noise selectors — DOM nodes to remove before Markdown conversion.
# These are UI chrome elements that are not part of the documentation content.
NOISE_SELECTORS = [
    ".breadcrumb-jjpG",          # Breadcrumb navigation
    ".btnBox-Vox6",              # Toolbar buttons (copy, download, favorite)
    ".primaryRow-pOm_",          # Toolbar row container
    ".toolbar-QUz9",             # Toolbar wrapper
    '[class*="feedback"]',       # "Was this page helpful?" widget
    ".doc-feedback",             # Alternative feedback class
    ".prev-next",                # Previous/Next navigation
    '[class*="prevNext"]',       # Alternative prev/next class
    ".ask-ai",                   # "Ask AI assistant" button
    '[class*="askAi"]',          # Alternative ask AI class
]


def url_to_slug(url: str) -> str:
    """Derive a filesystem-safe slug from a volcengine docs URL.

    Example: 'https://www.volcengine.com/docs/6561/163032' -> '6561-163032'
    Example: 'https://www.volcengine.com/docs/6561/2499930?lang=zh' -> '6561-2499930'
    """
    # Extract the docs path: /docs/{product_id}/{doc_id}
    match = re.search(r"/docs/(\d+)/(\d+)", url)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    # Fallback: hash the URL
    return hashlib.md5(url.encode()).hexdigest()[:12]


def cache_path(url: str) -> tuple[Path, Path]:
    """Return (markdown_cache_path, meta_cache_path) for a URL."""
    slug = url_to_slug(url)
    return (
        CACHE_DIR / f"{slug}.md",
        CACHE_DIR / f"{slug}.meta.json",
    )


def read_cache(url: str, ttl: int) -> Optional[dict]:
    """Check cache for a URL. Returns dict with markdown+meta if valid, None if miss."""
    md_path, meta_path = cache_path(url)
    if not md_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
        age = time.time() - meta.get("fetched_at", 0)
        if age > ttl:
            return None
        return {
            "markdown": md_path.read_text(),
            "title": meta.get("title", ""),
            "method": meta.get("method", "cached"),
            "cached": True,
            "fetched_at": meta.get("fetched_at", ""),
        }
    except (json.JSONDecodeError, OSError):
        return None


def write_cache(url: str, result: dict) -> None:
    """Write fetched result to cache."""
    md_path, meta_path = cache_path(url)
    md_path.write_text(result["markdown"])
    meta = {
        "url": url,
        "title": result.get("title", ""),
        "method": result.get("method", ""),
        "fetched_at": result.get("fetched_at", time.time()),
        "slug": url_to_slug(url),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))


def clean_html(html: str) -> str:
    """Clean the extracted doc HTML before Markdown conversion.

    Steps:
    1. Parse with BeautifulSoup (lxml)
    2. Remove noise DOM nodes (breadcrumbs, toolbars, feedback widgets)
    3. Return cleaned HTML string
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    # Remove noise elements
    for selector in NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()

    return str(soup)


def html_to_markdown(html: str) -> str:
    """Convert cleaned HTML to Markdown, then post-process."""
    from markdownify import markdownify as md

    markdown = md(html, heading_style="ATX")

    # Post-processing
    # 1. Remove zero-width spaces (used as empty table cell values)
    markdown = re.sub(r"​", "", markdown)

    # 2. Remove inline base64 image references (SVG/PNG icons)
    markdown = re.sub(r"!\[.*?\]\(data:image/[^)]+\)", "", markdown)

    # 3. Collapse 3+ consecutive blank lines into 2
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    # 4. Strip leading/trailing whitespace per line while preserving structure
    lines = [line.rstrip() for line in markdown.splitlines()]
    markdown = "\n".join(lines)

    return markdown.strip() + "\n"


async def fetch_playwright(url: str, timeout: int) -> dict:
    """Fetch a Volcengine doc page using Playwright headless Chromium.

    Returns dict with: markdown, title, method, cached, fetched_at
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)

            title = await page.title()
            # Remove the trailing "--火山引擎" suffix from title
            title = re.sub(r"--火山引擎$", "", title).strip()

            # Extract the doc content area
            content_el = await page.query_selector(CONTENT_SELECTOR)
            if not content_el:
                raise ValueError(
                    f"Could not find doc content area with selector: {CONTENT_SELECTOR}"
                )

            html = await page.evaluate("el => el.innerHTML", content_el)

            # Clean and convert
            cleaned_html = clean_html(html)
            markdown = html_to_markdown(cleaned_html)

            if not markdown.strip():
                raise ValueError("Extracted content is empty")

            return {
                "markdown": markdown,
                "title": title,
                "method": "playwright",
                "cached": False,
                "fetched_at": time.time(),
            }
        finally:
            await browser.close()


def fetch_firecrawl(url: str) -> dict:
    """Fetch a Volcengine doc page using Firecrawl CLI.

    Uses --wait-for 5000 to handle JS rendering on SPA pages.

    Returns dict with: markdown, title, method, cached, fetched_at
    """
    result = subprocess.run(
        [
            "firecrawl",
            "scrape",
            url,
            "--only-main-content",
            "--wait-for",
            "5000",
            "--format",
            "markdown",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Firecrawl failed: {result.stderr.strip()}")

    markdown = result.stdout.strip()
    if not markdown:
        raise ValueError("Firecrawl returned empty content")

    # Extract title from first H1 in markdown
    title = ""
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    if title_match:
        title = title_match.group(1)

    return {
        "markdown": markdown + "\n",
        "title": title,
        "method": "firecrawl",
        "cached": False,
        "fetched_at": time.time(),
    }


async def fetch_single(
    url: str,
    method: str = "auto",
    timeout: int = 30,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> dict:
    """Fetch a single URL, returning structured result dict.

    The result dict always has: url, markdown, title, method, cached, fetched_at.
    On error: url, error.
    """
    # Check cache first
    if use_cache:
        cached = read_cache(url, cache_ttl)
        if cached:
            cached["url"] = url
            return cached

    # Determine which method(s) to try
    errors = []

    if method in ("auto", "playwright"):
        try:
            result = await fetch_playwright(url, timeout)
            result["url"] = url
            if use_cache:
                write_cache(url, result)
            return result
        except Exception as e:
            errors.append(f"Playwright: {e}")
            if method == "playwright":
                return {"url": url, "error": f"Playwright failed: {e}"}

    if method in ("auto", "firecrawl"):
        if method == "auto":
            print(
                f"⚠️  Playwright failed, falling back to Firecrawl: {errors[-1]}",
                file=sys.stderr,
            )
        try:
            result = fetch_firecrawl(url)
            result["url"] = url
            if use_cache:
                write_cache(url, result)
            return result
        except Exception as e:
            errors.append(f"Firecrawl: {e}")
            return {"url": url, "error": f"All methods failed: {'; '.join(errors)}"}

    return {"url": url, "error": f"Unknown method: {method}"}


async def fetch_multiple(
    urls: list[str],
    method: str = "auto",
    timeout: int = 30,
    concurrency: int = 3,
    use_cache: bool = True,
    cache_ttl: int = 3600,
) -> list[dict]:
    """Fetch multiple URLs concurrently with a concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_fetch(url: str) -> dict:
        async with semaphore:
            return await fetch_single(url, method, timeout, use_cache, cache_ttl)

    tasks = [bounded_fetch(url) for url in urls]
    return await asyncio.gather(*tasks)


def output_stdout(results: list[dict], json_mode: bool = False) -> None:
    """Print results to stdout."""
    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for i, result in enumerate(results):
        if "error" in result:
            print(f"# Error: {result['url']}\n\n{result['error']}\n")
        else:
            if result.get("title"):
                print(f"# {result['title']}\n")
            print(result["markdown"])
        # Separator between URLs
        if i < len(results) - 1:
            print("---\n")


def output_files(results: list[dict], output_dir: Path) -> None:
    """Write results to files in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        slug = url_to_slug(result["url"])
        if "error" in result:
            print(f"⚠️  {slug}: {result['error']}", file=sys.stderr)
            continue

        md_path = output_dir / f"{slug}.md"
        meta_path = output_dir / f"{slug}.meta.json"

        md_path.write_text(result["markdown"])
        meta = {
            "url": result["url"],
            "title": result.get("title", ""),
            "method": result.get("method", ""),
            "cached": result.get("cached", False),
            "fetched_at": result.get("fetched_at", time.time()),
            "slug": slug,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        print(f"✓ {slug}.md ({result.get('method', 'unknown')})")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Volcano Engine documentation pages as clean Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/fetch.py "https://www.volcengine.com/docs/6561/163032"
  uv run scripts/fetch.py --output-dir ./docs/ url1 url2 url3
  uv run scripts/fetch.py --method firecrawl --no-cache "https://..."
  uv run scripts/fetch.py --json --concurrency 5 url1 url2
        """,
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more Volcano Engine doc URLs to fetch",
    )
    parser.add_argument(
        "--method",
        choices=["auto", "playwright", "firecrawl"],
        default="auto",
        help="Fetch method: auto (Playwright first, Firecrawl fallback), "
        "playwright (Playwright only), firecrawl (Firecrawl only). Default: auto",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Save output to directory instead of stdout. "
        "Each URL gets {slug}.md and {slug}.meta.json",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache, force re-fetch",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=3600,
        help="Cache TTL in seconds (default: 3600 = 1 hour)",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=3,
        help="Max concurrent fetches for multi-URL (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON to stdout instead of Markdown",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Page load timeout in seconds (default: 30)",
    )

    args = parser.parse_args()

    use_cache = not args.no_cache
    results = asyncio.run(
        fetch_multiple(
            args.urls,
            method=args.method,
            timeout=args.timeout,
            concurrency=args.concurrency,
            use_cache=use_cache,
            cache_ttl=args.cache_ttl,
        )
    )

    if args.output_dir:
        output_files(results, args.output_dir)
    else:
        output_stdout(results, json_mode=args.json)

    # Exit with error if any URL failed
    errors = [r for r in results if "error" in r]
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
