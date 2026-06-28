#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
"""
Article fetch dispatcher for article-to-notion skill.

Routes by URL:
  - mp.weixin.qq.com  → wechat-article-fetcher (Playwright, persistent profile)
  - everything else   → tavily (preferred for reliability, especially behind
                        anti-bot walls) → firecrawl (fallback)

Output: a structured fetch directory containing article.md + manifest.json +
assets/. The fetch directory path is printed to stdout (last line) so the
caller can chain to compose.py.

Usage:
  uv run scripts/fetch_article.py <url>
  uv run scripts/fetch_article.py <url> --output-dir <dir>
  uv run scripts/fetch_article.py <url> --no-images
  uv run scripts/fetch_article.py <url> --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


# ────────────────────────────────────────────────────────────────────
# URL detection
# ────────────────────────────────────────────────────────────────────

def detect_source(url: str) -> str:
    """Return 'wechat' or 'generic'."""
    hostname = (urlparse(url).hostname or "").lower()
    if hostname == "mp.weixin.qq.com":
        return "wechat"
    return "generic"


# ────────────────────────────────────────────────────────────────────
# WeChat path: delegate to wechat-article-fetcher
# ────────────────────────────────────────────────────────────────────

def _find_wechat_fetcher() -> Path | None:
    """Locate the wechat-article-fetcher fetch.py in the same project."""
    # Walk up from this script to find .agents/skills/
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "wechat-article-fetcher" / "scripts" / "fetch.py"
        if candidate.exists():
            return candidate
        # When this skill is symlinked to ~/.claude/skills, the sibling structure
        # may not exist; also check via .agents/skills root
        candidate2 = parent / ".agents" / "skills" / "wechat-article-fetcher" / "scripts" / "fetch.py"
        if candidate2.exists():
            return candidate2
    return None


def fetch_wechat(url: str, output_dir: Path, no_images: bool) -> dict[str, Any]:
    wechat_script = _find_wechat_fetcher()
    if not wechat_script:
        return {
            "error_code": "MISSING_DEPENDENCY",
            "message": "wechat-article-fetcher script not found. Ensure the sibling skill exists.",
        }

    cmd = ["uv", "run", str(wechat_script), url, "--output-dir", str(output_dir)]
    if no_images:
        cmd.append("--no-images")

    print(f"→ Running wechat-article-fetcher (this may take 30-60s)...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {
            "error_code": "FETCH_FAILED",
            "message": f"wechat-article-fetcher exit {result.returncode}",
            "stderr": result.stderr[-1500:],
        }

    # The fetcher prints "Article saved to: <path>" then a JSON manifest summary.
    saved_match = re.search(r"Article saved to:\s*(.+)", result.stdout)
    if not saved_match:
        # Fallback: try to parse JSON; the fetcher prints manifest to stdout
        try:
            data = json.loads(result.stdout.split("Article saved to:")[-1].split("{", 1)[-1])
        except Exception:
            return {
                "error_code": "FETCH_FAILED",
                "message": "Could not parse wechat-article-fetcher output",
                "stdout": result.stdout[-1500:],
            }
        article_dir = output_dir / data.get("article_dir", "")
    else:
        article_dir = Path(saved_match.group(1).strip())

    if not article_dir.exists():
        return {
            "error_code": "FETCH_FAILED",
            "message": f"Output directory not found: {article_dir}",
        }

    return {
        "source": "wechat",
        "article_dir": str(article_dir),
    }


# ────────────────────────────────────────────────────────────────────
# Generic path: tavily first (works well for WeChat-like JS-heavy pages),
# firecrawl as fallback.
# ────────────────────────────────────────────────────────────────────

def _find_in_user_shell(cmd_name: str) -> str | None:
    """Try `which <cmd>` first; if not found, fall back to an interactive zsh."""
    import shutil
    direct = shutil.which(cmd_name)
    if direct:
        return direct
    try:
        result = subprocess.run(
            ["zsh", "-i", "-c", f"which {cmd_name}"],
            capture_output=True, text=True, timeout=10,
        )
        path = result.stdout.strip()
        if path and Path(path).exists():
            return path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w一-鿿\s-]", "", text.strip().lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:80] or "article"


def fetch_generic(url: str, output_dir: Path, no_images: bool) -> dict[str, Any]:
    errors: list[str] = []

    # Try tavily first
    tvly = _find_in_user_shell("tvly")
    if tvly:
        cmd = [tvly, "extract", url, "--extract-depth", "advanced", "--json"]
        if not no_images:
            cmd.append("--include-images")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                results = data.get("results", [])
                if results and results[0].get("raw_content"):
                    parsed = _parse_tavily(results[0])
                    return _write_generic_output(url, parsed, output_dir, "tavily")
            except json.JSONDecodeError:
                pass
        errors.append(f"tavily: {result.stderr[:200] or result.stdout[:200]}")
    else:
        errors.append("tavily: not installed")

    # Firecrawl fallback
    firecrawl = _find_in_user_shell("firecrawl")
    if firecrawl:
        cmd = [firecrawl, "scrape", url, "--only-main-content", "-f", "markdown", "-o", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            parsed = {"title": None, "markdown": result.stdout, "images": []}
            return _write_generic_output(url, parsed, output_dir, "firecrawl")
        errors.append(f"firecrawl: {result.stderr[:200] or result.stdout[:200]}")
    else:
        errors.append("firecrawl: not installed")

    return {
        "error_code": "FETCH_FAILED",
        "message": "All generic fetchers failed",
        "details": errors,
    }


def _parse_tavily(result: dict) -> dict[str, Any]:
    content = result.get("raw_content", "")
    # Tavily prepends "# Title\n\n" sometimes; first line as title heuristic
    title = None
    lines = content.split("\n", 3)
    if lines and lines[0].startswith("# "):
        title = lines[0].lstrip("# ").strip()
    return {
        "title": title,
        "markdown": content,
        "images": result.get("images", []),
    }


def _write_generic_output(
    url: str,
    parsed: dict,
    output_dir: Path,
    source_tag: str,
) -> dict[str, Any]:
    title = parsed.get("title") or "untitled"
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    slug = _slugify(title)
    article_dir = output_dir / f"{date_prefix}-{slug}"
    article_dir.mkdir(parents=True, exist_ok=True)

    md = parsed["markdown"]
    article_path = article_dir / "article.md"
    frontmatter = (
        f"---\n"
        f'title: "{title}"\n'
        f'source_url: "{url}"\n'
        f'fetcher: "{source_tag}"\n'
        f"---\n\n"
    )
    article_path.write_text(frontmatter + md, encoding="utf-8")

    manifest = {
        "title": title,
        "source_url": url,
        "fetcher": source_tag,
        "fetched_at": datetime.now().isoformat(),
        "content_markdown_path": "article.md",
        "content_length": len(md),
        "images": [{"index": i + 1, "original_url": img, "local_path": None}
                   for i, img in enumerate(parsed.get("images") or [])],
    }
    (article_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "source": source_tag,
        "article_dir": str(article_dir),
    }


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR = Path.home() / ".cache" / "article-to-notion" / "fetches"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a web article to local cache.")
    parser.add_argument("url", help="Article URL")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory root (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument("--no-images", action="store_true",
                        help="Skip image download (only for generic / WeChat)")
    parser.add_argument("--json", action="store_true",
                        help="Print structured JSON instead of plain text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source = detect_source(args.url)
    if source == "wechat":
        result = fetch_wechat(args.url, args.output_dir, args.no_images)
    else:
        result = fetch_generic(args.url, args.output_dir, args.no_images)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if "error_code" in result:
            print(f"ERROR: {result['error_code']}: {result.get('message', '')}", file=sys.stderr)
            if "details" in result:
                for d in result["details"]:
                    print(f"  - {d}", file=sys.stderr)
        else:
            # Last line of stdout is the path, for easy chaining.
            print(f"source: {result.get('source')}", file=sys.stderr)
            print(result["article_dir"])

    return 0 if "error_code" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
