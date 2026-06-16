#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4>=4.15",
#   "lxml>=6.1",
#   "markdownify>=1.1",
#   "playwright>=1.60",
#   "requests>=2.34",
# ]
# ///
"""
WeChat Article Fetcher

Extract WeChat public account articles to structured Markdown + assets.
Usage:
    uv run .agents/skills/wechat-article-fetcher/scripts/fetch.py <url>
    uv run .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --output-dir ./content/inbox/articles/
    uv run .agents/skills/wechat-article-fetcher/scripts/fetch.py <url> --no-images
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import html as html_mod
import requests

# ── Startup dependency checks ──────────────────────────────────────────

try:
    import playwright
except ImportError:
    print("ERROR: playwright not installed. Run: uv run script.py (PEP 723 handles deps)", file=sys.stderr)
    sys.exit(1)

try:
    import markdownify
except ImportError:
    print("ERROR: markdownify not installed. Run: uv run script.py (PEP 723 handles deps)", file=sys.stderr)
    sys.exit(1)

from playwright.sync_api import sync_playwright

CHROME_PATH = os.environ.get("CHROME_EXECUTABLE", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
if not os.path.exists(CHROME_PATH):
    print(f"ERROR: Chrome not found at {CHROME_PATH}. Please install Google Chrome or set CHROME_EXECUTABLE env var.", file=sys.stderr)
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────────────

USER_DATA_DIR = Path.home() / ".config" / "wechat-article-fetcher" / "profile"
DEFAULT_OUTPUT_DIR = Path("wechat-articles")
REFERER = "https://mp.weixin.qq.com/"

# ── Error helpers ──────────────────────────────────────────────────────

def error_json(error_code: str, message: str) -> dict[str, Any]:
    return {"error_code": error_code, "message": message}

# ── Slug generation ────────────────────────────────────────────────────

def normalize_wechat_url(raw: str) -> str:
    """Normalize a pasted WeChat article URL.
    Handles zsh backslash escapes, HTML entities, quote wrappers, bare hostnames.
    """
    s = str(raw or "").strip()
    if not s:
        return s

    # Strip wrapping quotes / angle brackets
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()

    # Remove backslash escapes before URL-significant characters
    s = re.sub(r"\\+([:/&?=#%])", r"\1", s)

    # Decode HTML entities
    s = html_mod.unescape(s)

    # Allow bare hostnames
    if s.startswith("mp.weixin.qq.com/") or s.startswith("//mp.weixin.qq.com/"):
        s = "https://" + s.lstrip("/")

    # Force https for mp.weixin.qq.com
    parsed = urlparse(s)
    if parsed.scheme in ("http", "https") and (parsed.hostname or "").lower() == "mp.weixin.qq.com":
        from urllib.parse import urlunparse
        s = urlunparse(("https", "mp.weixin.qq.com", parsed.path, parsed.params, parsed.query, parsed.fragment))

    return s


def generate_slug(url: str, title: str | None = None) -> str:
    """Generate a URL-safe slug for the article directory name.

    Priority:
      1. Cleaned title (most readable for human browsing of the corpus)
      2. biz+mid from URL (unique per article, but base64-encoded and
         unreadable — only used as fallback when title is missing)
      3. URL path (very last resort)
    """
    parsed = urlparse(url)
    query = parsed.query
    if title:
        return _clean_slug(title)
    # WeChat uses both `__biz=` and `biz=`; match either. The double-
    # underscore form is the modern one in canonical mp.weixin.qq.com URLs.
    biz_match = re.search(r"(?:__)?biz=([^&]+)", query)
    mid_match = re.search(r"(?:__)?mid=([^&]+)", query)
    if biz_match and mid_match:
        biz = _clean_slug(biz_match.group(1))
        mid = _clean_slug(mid_match.group(1))
        return f"{biz}-{mid}"
    return _clean_slug(parsed.path.strip("/").replace("/", "-")) or "article"

def _clean_slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")

# ── HTML pre-cleaning ──────────────────────────────────────────────────

# WeChat public account HTML noise: editor-specific tags, profile cards,
# "read original" CTAs, and rich-text leftover wrappers. Class names are
# stable in mp.weixin.qq.com articles as of 2026-06.
#
# NOTE: `mpcover` is a legitimate media card container in newer articles —
# it often wraps a captioned image. Do NOT add it to REMOVE_SELECTORS.
WECHAT_NOISE_SELECTORS = (
    "script",
    "style",
    ".qr_code_pc",
    ".reward_area",
    ".original_area_primary",   # "阅读原文" card at article end
    ".wx_profile_card_inner",   # 公众号名片卡
    ".mp-video-player",         # 视频播放器外层 Vue 组件
    ".video_iframe_area",       # 视频 iframe 容器
    ".video_player_card",       # 视频播放器卡片
    ".txp_video_controls",      # 微信内置视频控件
    ".js_mpvedio",              # 视频弹层
    ".video_full-screen",       # 全屏控制条
    ".video_btn",               # 视频按钮
    ".video_switch",            # 倍速切换
    ".video_desc",              # 视频描述
    "mpcps",
    "mp-common-profile",
    "mp-miniprogram",
    "mp-weapp",
    "mpvoice",
    "mpprofile",
    "video",                    # 直接的视频标签
    # NOTE: <iframe> is handled specially above (we insert a `[视频]`
    # placeholder before deleting, so readers know the original article
    # had a video). All non-video <iframe> elements are also caught by
    # that pass.
)


def _get_bs4_parser() -> str:
    """Prefer lxml when available (4x faster, more robust on WeChat rich text);
    fall back to pure-Python html.parser if lxml is not installed.
    """
    try:
        import lxml  # noqa: F401
        return "lxml"
    except ImportError:
        return "html.parser"


# CSS class signatures that mark a <video> or <iframe> as a "WeChat video
# player" — every parent in this list is part of the player chrome and will
# be removed by the noise selectors below, so we walk past them to find
# where to safely place the `[视频]` marker.
_VIDEO_WRAPPER_CLASSES = (
    "js_mpvedio",
    "page_video_wrapper",
    "mp-video-player",
    "js_page_video",
    "page_video",
    "js_inner",
    "video_poster",
    "js_video_poster",
    "video_mask",
    "video_fill",
    "video_iframe",
    "video_iframe_area",
    "video_player_card",
    "txp_video_controls",
)


def _is_video_wrapper(node) -> bool:
    """True if a Tag is part of a WeChat video player chrome that we will
    later remove. Used by `pre_clean_html` to walk past nested wrappers
    before placing the `[视频]` placeholder.
    """
    if not hasattr(node, "get"):
        return False
    classes = node.get("class") or []
    for cls in classes:
        if cls in _VIDEO_WRAPPER_CLASSES:
            return True
    return False


def pre_clean_html(html: str) -> str:
    """Pre-process HTML before markdownify: fix <pre> blocks, remove noise elements."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, _get_bs4_parser())

    # Step 1: Mark video iframes with a `[视频]` placeholder BEFORE removing
    # them, so the Markdown reader knows the original article had a video.
    #
    # WeChat wraps <video> elements in deeply-nested divs (e.g. .js_mpvedio,
    # .video_iframe, .mp-video-player). The noise selectors below will delete
    # those wrapper divs — and would take our placeholder with it if we
    # inserted the marker as a sibling of the <video>. So we insert the
    # marker OUTSIDE the outermost wrapper, by walking up the parent chain
    # until we find a tag that is NOT one of the noise-targeted wrappers.
    for tag in soup.select("iframe, video"):
        if tag.find_parent("mpcps") is not None:
            # Handled in Pass 1b below
            continue
        # Find the outermost video wrapper: walk up while the parent will be
        # removed by the noise selectors. The placeholder goes BEFORE that
        # outermost wrapper, so it survives the noise-removal step.
        outermost = tag
        while True:
            parent = outermost.parent
            if parent is None or not _is_video_wrapper(parent):
                break
            outermost = parent
        outermost.insert_before(soup.new_string("\n\n[视频]\n\n"))
        # Now decompose the video subtree
        tag.decompose()

    # Step 1b: <iframe>/<video> nested inside <mpcps> — mark the mpcps
    # itself, so the marker survives the mpcps noise removal.
    for mpcps in soup.select("mpcps"):
        if mpcps.select_one("iframe, video"):
            mpcps.insert_before(soup.new_string("\n\n[视频]\n\n"))

    # Step 2: Remove other noise elements
    for sel in WECHAT_NOISE_SELECTORS:
        for tag in soup.select(sel):
            tag.decompose()

    # Fix <pre> blocks: WeChat rich-text editor nests <span>/<p>/<div>/<section>
    # inside <pre> for "fake" line breaks, which markdownify would emit as
    # inline content with no structure. Strategy:
    #   1. Walk all <span> descendants in document order. For each, look
    #      at ALL previous siblings (including text nodes) to decide
    #      whether to insert a "\n" before it:
    #        - any sibling <br> is present → don't insert (markdownify
    #          will emit `  \n` from the <br>, which already breaks the line)
    #        - any sibling text node contains "\n" → don't insert
    #        - otherwise (last sibling was another span that we just
    #          replaced with its text) → insert "\n" so the implicit
    #          WeChat line break between adjacent spans is preserved.
    #      Then replace the span with its inner text.
    #   2. Replace <br> tags inside <pre> with "\n" (markdownify would
    #      render <br> as a hard break "  \n" but for code blocks we
    #      want a real line break). Especially important for the
    #      code-snippet__js class structure: one <code> wraps many
    #      lines, each separated by <br><br>.
    #   3. Replace direct-child <p>/<div>/<section>/<code> with text + "\n"
    #      (these are WeChat's "soft line break" markers and should always
    #      produce a real line break in Markdown). The <code> case matters
    #      for the code-snippet__js class that WeChat uses for pasted code:
    #      each line is wrapped in its own <code> element, and markdownify
    #      treats <code> as inline.
    for pre in soup.find_all("pre"):
        # Step 1: unwrap spans, inserting "\n" between adjacent spans that
        # are not separated by an explicit break signal (<br>).
        #
        # We look BACKWARDS through previous siblings, skipping text nodes
        # (which may include the "\n" we previously inserted), to find the
        # nearest element-level sibling. If that element is a <br>, the
        # break signal is already there and we don't insert "\n" before
        # the span. For any other element (span/p/div/etc.), insert "\n"
        # to preserve the implicit WeChat line break.
        #
        # We deliberately do NOT replace <br> with "\n" here. markdownify
        # renders <br> as a hard-break "  \n" which looks wrong inside a
        # code block, but we need <br> to STAY so Step 1 can detect it.
        # The "\n" that markdownify will emit from the <br> after Step 1
        # is acceptable in a code block (renders as a blank line).
        for span in list(pre.find_all("span")):
            prev_siblings = list(span.previous_siblings)
            # No previous sibling at all → first child, no need to insert
            if not prev_siblings:
                span.replace_with(span.get_text())
                continue
            has_break = False
            for sibling in prev_siblings:
                # Skip text nodes (including "\n" we inserted earlier)
                if not hasattr(sibling, "name") or sibling.name is None:
                    continue
                # Found an element sibling
                if sibling.name == "br":
                    has_break = True
                # Any other element (span/p/div/etc.) → no explicit break;
                # the loop ends here either way
                break
            if not has_break:
                span.insert_before("\n")
            span.replace_with(span.get_text())
        # Step 2: <br> -> "\n" inside <pre> (after unwrap so it stays)
        for br in pre.find_all("br"):
            br.replace_with("\n")
        # Step 3: direct-child block elements
        for child in list(pre.children):
            if getattr(child, "name", None) in ("p", "div", "section", "code"):
                child.replace_with(child.get_text() + "\n")

    return str(soup)

# ── Markdown post-cleaning ─────────────────────────────────────────────

def post_clean_markdown(md: str) -> str:
    """Post-process Markdown: clean nbsp, trailing whitespace, compress blank lines."""
    md = md.replace(" ", " ")
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md

# ── Metadata extraction ────────────────────────────────────────────────

def extract_metadata(page) -> dict[str, str]:
    """Extract title, account, and publish_time from page."""
    meta = {}

    title_el = page.query_selector("#activity-name")
    meta["title"] = title_el.inner_text().strip() if title_el else ""

    account_el = page.query_selector("#js_name")
    meta["account"] = account_el.inner_text().strip() if account_el else ""

    time_el = page.query_selector("#publish_time")
    if time_el:
        meta["publish_time"] = time_el.inner_text().strip()
    else:
        html = page.content()
        ts = _extract_create_time(html)
        if ts:
            meta["publish_time"] = _format_timestamp(ts)
        else:
            # Final fallback: meta tags
            meta["publish_time"] = page.evaluate("""
                () => {
                    const el = document.querySelector('meta[name="publish_time"]') ||
                               document.querySelector('meta[property="article:published_time"]');
                    return el ? el.content : "";
                }
            """)

    return meta


def _extract_create_time(html: str) -> int | None:
    """Extract Unix timestamp from WeChat article HTML (multiple formats)."""
    # JsDecode format
    m = re.search(r"create_time\s*:\s*JsDecode\('([^']+)'\)", html)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    # Single-quoted number
    m = re.search(r"create_time\s*:\s*'(\d+)'", html)
    if m:
        return int(m.group(1))
    # Unquoted or double-quoted, with colon or equals
    m = re.search(r'create_time\s*[:=]\s*["\']?(\d+)["\']?', html)
    if m:
        return int(m.group(1))
    # Legacy var ct
    m = re.search(r'var\s+ct\s*=\s*["\']?(\d+)["\']?', html)
    if m:
        return int(m.group(1))
    return None


def _format_timestamp(ts: int) -> str:
    """Unix timestamp (seconds) -> 'YYYY-MM-DD HH:mm:ss' (Asia/Shanghai, UTC+8)."""
    from datetime import timedelta
    tz = timezone(timedelta(hours=8))
    dt = datetime.fromtimestamp(ts, tz=tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ── Image handling ─────────────────────────────────────────────────────

def download_images(content_html: str, base_path: Path, no_images: bool) -> tuple[str, list[dict]]:
    """Download images from mmbiz.qpic.cn and return updated HTML + image manifest."""
    if no_images:
        return content_html, []

    assets_dir = base_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content_html, _get_bs4_parser())
    images = []
    img_index = 0

    for img in soup.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        # Only download real article images; skip WeChat video covers/thumbnails
        # hosted on mpvideo.qpic.cn (out of scope: writing material, not video republish).
        if not src or "mmbiz.qpic.cn" not in src or "mpvideo.qpic.cn" in src:
            continue

        img_index += 1
        alt = img.get("alt", "") or ""
        ext = _guess_ext(src)
        local_name = f"img-{img_index:03d}.{ext}"
        local_path = assets_dir / local_name
        rel_path = f"assets/{local_name}"

        try:
            resp = requests.get(src, headers={"Referer": REFERER}, timeout=30)
            resp.raise_for_status()
            # Re-evaluate extension from Content-Type if needed
            ext = _ext_from_content_type(resp.headers.get("Content-Type", ""), ext)
            local_name = f"img-{img_index:03d}.{ext}"
            local_path = assets_dir / local_name
            rel_path = f"assets/{local_name}"
            local_path.write_bytes(resp.content)
            img["src"] = rel_path
            images.append({
                "index": img_index,
                "original_url": src,
                "local_path": rel_path,
                "alt": alt,
            })
        except Exception as exc:
            print(f"WARNING: Failed to download image {src}: {exc}", file=sys.stderr)
            images.append({
                "index": img_index,
                "original_url": src,
                "local_path": None,
                "alt": alt,
            })

    return str(soup), images

def _guess_ext(url: str) -> str:
    path = urlparse(url).path
    if "." in path:
        ext = path.split(".")[-1].lower()
        if ext in ("jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"):
            return "jpg" if ext == "jpeg" else ext
    return "jpg"

def _ext_from_content_type(ct: str, fallback: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/svg+xml": "svg",
        "image/bmp": "bmp",
    }
    for key, val in mapping.items():
        if key in ct:
            return val
    return fallback

# ── Main fetch logic ───────────────────────────────────────────────────

def fetch_article(url: str, output_dir: Path, no_images: bool) -> dict[str, Any]:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Validate output directory is writable
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except OSError as exc:
        return error_json("OUTPUT_NOT_WRITABLE", f"Cannot write to output directory: {exc}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            executable_path=CHROME_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = context.new_page()

            # Navigate
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as exc:
                return error_json("CONTENT_NOT_RENDERED", f"Navigation failed: {exc}")

            # Wait for content or login
            try:
                page.wait_for_selector("#js_content", state="visible", timeout=15000)
            except Exception:
                # Check for login indicators
                login_indicators = [
                    "login", "登录", "扫码", "weui_btn_primary", "btn_login",
                ]
                page_text = page.inner_text("body") or ""
                has_login = any(ind in page_text for ind in login_indicators)

                if has_login:
                    print("未检测到微信登录态。请在弹出的浏览器窗口中登录（扫码或密码），完成后按回车继续...")
                    try:
                        input()
                    except EOFError:
                        return error_json("LOGIN_FAILED", "Non-interactive environment: cannot prompt for login. Please login manually in Chrome first.")
                    page.reload()
                    try:
                        page.wait_for_selector("#js_content", state="visible", timeout=15000)
                    except Exception:
                        return error_json("LOGIN_FAILED", "Login attempted but content still unavailable.")
                else:
                    # Check for other error states
                    body_text = page.inner_text("body") or ""
                    if "验证码" in body_text or "captcha" in body_text.lower():
                        return error_json("VERIFICATION_REQUIRED", "Verification or captcha required.")
                    if "删除" in body_text or "not found" in body_text.lower() or "404" in body_text:
                        return error_json("ARTICLE_DELETED", "Article appears deleted or not found.")
                    return error_json("CONTENT_NOT_RENDERED", "#js_content not found after timeout.")

            # Extract metadata
            meta = extract_metadata(page)
            title = meta.get("title") or "Untitled"
            account = meta.get("account") or ""
            publish_time = meta.get("publish_time") or ""

            # Extract content
            content_el = page.query_selector("#js_content")
            if not content_el:
                return error_json("CONTENT_NOT_RENDERED", "#js_content disappeared after initial detection.")

            raw_html = content_el.inner_html()
        finally:
            context.close()

    # HTML pre-cleaning
    cleaned_html = pre_clean_html(raw_html)

    # Download images (before markdownify so we can update HTML src attributes)
    slug = generate_slug(url, title)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    article_dir = output_dir / f"{date_prefix}-{slug}"
    article_dir.mkdir(parents=True, exist_ok=True)

    updated_html, image_manifest = download_images(cleaned_html, article_dir, no_images)

    # Convert to Markdown
    md = markdownify.markdownify(updated_html, heading_style="ATX")
    md = post_clean_markdown(md)

    # Write article.md
    article_path = article_dir / "article.md"
    article_path.write_text(
        f"---\n"
        f'title: "{title}"\n'
        f'account: "{account}"\n'
        f'publish_time: "{publish_time}"\n'
        f'source_url: "{url}"\n'
        f"---\n\n"
        f"# {title}\n\n"
        f"{md}\n",
        encoding="utf-8",
    )

    # Write manifest.json
    manifest = {
        "title": title,
        "account": account,
        "publish_time": publish_time,
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_markdown_path": "article.md",
        "content_length": len(md),
        "images": image_manifest,
    }
    manifest_path = article_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write sources.md
    sources_path = article_dir / "sources.md"
    today = datetime.now().strftime("%Y-%m-%d")
    sources_path.write_text(
        f"# Source: {title}\n\n"
        f"- **Source URL**: {url}\n"
        f"- **Account**: {account}\n"
        f"- **Fetch Date**: {today}\n"
        f"- **Tool**: wechat-article-fetcher\n\n"
        f"## Compliance Note\n\n"
        f"This article was fetched for personal research and writing reference only.\n"
        f"Respect copyright: cite source when referencing. Do not redistribute or commercialize.\n",
        encoding="utf-8",
    )

    print(f"Article saved to: {article_dir}")
    return manifest

# ── CLI ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch WeChat articles to Markdown")
    parser.add_argument("url", help="WeChat article URL")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--no-images", action="store_true", help="Skip image download")
    args = parser.parse_args()

    normalized_url = normalize_wechat_url(args.url)
    if normalized_url != args.url:
        print("已自动清理 URL 中的转义字符 / HTML 实体。", file=sys.stderr)
    if not normalized_url.startswith("https://mp.weixin.qq.com/"):
        print("错误：请输入有效的微信文章 URL (mp.weixin.qq.com)", file=sys.stderr)
        sys.exit(1)

    result = fetch_article(normalized_url, args.output_dir, args.no_images)
    if "error_code" in result:
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
