#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""preprocess.py — Markdown → Feishu-ready Markdown with placeholders.

This script does the *minimum* preprocessing needed before sending a markdown
article to Feishu via `lark-cli docs +update --doc-format markdown`.

Why hybrid Markdown (not full XML conversion)?
  Feishu's server-side Markdown renderer handles ~90% of GFM natively (headings,
  lists, code blocks, tables, blockquotes, inline emphasis). We only need to
  rewrite the parts where Markdown semantics don't reach Feishu blocks:
    - local image references → <img> tags with placeholder tokens we replace
      after `+media-insert` returns real file_tokens
    - ```mermaid blocks → kept as mermaid code blocks by default; opt in via
      --mermaid-mode whiteboard to emit <whiteboard type="mermaid"> inline tags

The script runs in two modes:

  prepare (default):
    --input <article.md> --workdir <dir>
    Reads frontmatter + body, emits:
      <workdir>/processed.md   markdown with placeholders
      <workdir>/manifest.json  {"title", "frontmatter", "images":[...], "mermaid_count"}

  finalize:
    --finalize --workdir <dir>
    Reads <workdir>/manifest.json (now with "file_token" filled in for each image)
    and produces <workdir>/final.md with placeholders replaced by real tokens.

Dependencies: stdlib + PyYAML (declared in PEP 723 inline metadata).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    print(
        "ERROR: PyYAML not installed.\n"
        "  uv run scripts/preprocess.py ...   # PEP 723 inline deps handle this",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter dict, body). If no frontmatter, fm is {} and body == text."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_raw = m.group(1)
    body = text[m.end() :]
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"frontmatter YAML parse error: {exc}")
    if not isinstance(fm, dict):
        raise SystemExit(
            f"frontmatter must be a mapping, got {type(fm).__name__}: {fm!r}"
        )
    return fm, body


def derive_title(fm: dict[str, Any], body: str, fallback: str) -> str:
    """Prefer frontmatter `title`; else first H1; else fallback (file basename)."""
    if isinstance(fm.get("title"), str) and fm["title"].strip():
        return fm["title"].strip()
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback


# ---------------------------------------------------------------------------
# image extraction
# ---------------------------------------------------------------------------

# Match GFM image syntax: ![alt](url "optional title")
# We handle both inline images and reference-style images is left out for v1
# (rare in our writing-agent-harness articles).
IMAGE_RE = re.compile(
    r"""
    !\[(?P<alt>[^\]]*)\]    # ![alt]
    \(
      \s*
      (?P<url>[^)\s]+)      # url (no spaces, no closing paren)
      (?:\s+"(?P<title>[^"]*)")?  # optional "title"
      \s*
    \)
    """,
    re.VERBOSE,
)


def is_remote_url(url: str) -> bool:
    return url.startswith(("http://", "https://"))


def _get_image_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) for PNG/JPEG without external dependencies."""
    try:
        data = path.read_bytes()
    except OSError:
        return None

    # PNG: IHDR chunk appears within first ~64 bytes.
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        cursor = 8
        while cursor + 12 < len(data):
            length = int.from_bytes(data[cursor : cursor + 4], "big")
            chunk_type = data[cursor + 4 : cursor + 8]
            if chunk_type == b"IHDR" and cursor + 8 + 8 <= len(data):
                width = int.from_bytes(
                    data[cursor + 8 : cursor + 12], "big"
                )
                height = int.from_bytes(
                    data[cursor + 12 : cursor + 16], "big"
                )
                return width, height
            if chunk_type == b"IDAT":
                break
            cursor += 12 + length
        return None

    # JPEG: scan SOF0/2/15 markers.
    if data[:2] == b"\xff\xd8":
        cursor = 2
        while cursor + 2 < len(data):
            if data[cursor] != 0xFF:
                cursor += 1
                continue
            marker = data[cursor + 1]
            if marker in (0xC0, 0xC2, 0xC1, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                if cursor + 9 < len(data):
                    height = int.from_bytes(data[cursor + 5 : cursor + 7], "big")
                    width = int.from_bytes(data[cursor + 7 : cursor + 9], "big")
                    return width, height
                return None
            # Skip marker segment.
            if marker in (0xD8, 0xD9):
                cursor += 2
                continue
            if marker == 0xFF:
                cursor += 1
                continue
            if cursor + 4 > len(data):
                break
            seg_len = int.from_bytes(data[cursor + 2 : cursor + 4], "big")
            cursor += 2 + seg_len
        return None

    return None


def collect_and_rewrite_images(
    body: str, source_md_path: Path
) -> tuple[str, list[dict[str, Any]]]:
    """Replace local image refs with <img src="__PLACEHOLDER_N__"/> placeholders.

    Remote URLs are passed through as `<img href="...">` (Feishu downloads them).
    Local paths are resolved relative to source_md_path.parent.

    Returns:
        (rewritten body, manifest_images)
        manifest_images is a list of
        {"placeholder", "local_path", "alt", "title", "missing"}.
        Missing local files are still listed in the manifest so the caller can
        decide what to do; in the output they are downgraded to a plain-text alt
        line to avoid breaking the rest of the article.
    """
    images: list[dict[str, Any]] = []
    base_dir = source_md_path.parent.resolve()

    def repl(m: re.Match[str]) -> str:
        url = m.group("url")
        alt = m.group("alt") or ""
        title = m.group("title") or ""
        if is_remote_url(url):
            # Feishu's `+update --doc-format markdown` will download remote images,
            # so we just emit a clean <img href> tag (works in both md and xml modes).
            attrs = f'href="{url}"'
            if alt:
                attrs += f' caption="{_xml_escape(alt)}"'
            return f"<img {attrs}/>"
        # local file
        local = (base_dir / url).resolve()
        missing = not local.exists()
        size = _get_image_size(local) if not missing else None
        placeholder = f"__PLACEHOLDER_{len(images)}__"
        images.append(
            {
                "placeholder": placeholder,
                "local_path": str(local),
                "alt": alt,
                "title": title,
                "missing": missing,
                "width": size[0] if size else None,
                "height": size[1] if size else None,
                "file_token": None,  # filled in by orchestrator after media-insert
            }
        )
        if missing:
            # Downgrade to a visible caption line so the reader knows something
            # was supposed to be here; do NOT emit a broken <img src> tag.
            warn_text = f"[图片缺失: {alt}]" if alt else f"[图片缺失: {url}]"
            return f"\n\n> ⚠️ {warn_text}\n\n"
        # Note: src=PLACEHOLDER will be replaced by file_token in finalize step.
        attrs = f'src="{placeholder}"'
        if size:
            attrs += f' width="{size[0]}" height="{size[1]}"'
        if alt:
            # Strip leading/trailing newlines from caption to avoid weird spacing.
            clean_alt = alt.strip().replace("\n", " ")
            attrs += f' caption="{_xml_escape(clean_alt)}"'
        return f"<img {attrs}/>"

    return IMAGE_RE.sub(repl, body), images


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# ---------------------------------------------------------------------------
# HTML sanitisation for Feishu markdown mode
# ---------------------------------------------------------------------------

# Feishu's markdown renderer recognises a subset of inline XML tags (<b>, <u>,
# <img>, <whiteboard>, etc.) and treats some real HTML tags as parse errors that
# can poison the whole document. The known problematic tags are media/active
# content: <video>, <source>, <embed>, <iframe>, <object>, <track>, plus
# <script>, <style>, and HTML comments.
#
# We do NOT remove arbitrary unknown tags like <umbrella> because markdown
# authors often use angle brackets as conceptual notation; removing them would
# silently corrupt the article text. Only the tags below are stripped.
# See: luolebai-handanxuebu test (2026-06-13).

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_VIDEO_RE = re.compile(r"<video[^>]*>.*?</video>", re.DOTALL | re.IGNORECASE)
HTML_SOURCE_RE = re.compile(r"<source\b[^>]*/?>", re.IGNORECASE)
# Void tags that can break Feishu markdown rendering.
HTML_BAD_VOID_TAGS: set[str] = {
    "embed", "iframe", "object", "track", "script", "style",
    "link", "meta", "input", "textarea", "form", "button",
}
HTML_BAD_VOID_RE = re.compile(
    r"<(" + "|".join(HTML_BAD_VOID_TAGS) + r")\b[^>]*/?>",
    re.IGNORECASE,
)
# Paired tags that can break Feishu markdown rendering.
HTML_BAD_PAIRED_TAGS: set[str] = {"script", "style", "iframe", "object"}
HTML_BAD_PAIRED_RE = re.compile(
    r"<(" + "|".join(HTML_BAD_PAIRED_TAGS) + r")\b[^>]*>.*?</\1>",
    re.DOTALL | re.IGNORECASE,
)


def sanitize_html_for_feishu(body: str) -> tuple[str, list[str]]:
    """Remove/downgrade known problematic HTML tags for Feishu markdown mode.

    Returns (cleaned_body, warnings).
    """
    warnings: list[str] = []

    # 1. Strip HTML comments entirely (they are publishing notes, not content).
    body = HTML_COMMENT_RE.sub("", body)

    # 2. Replace <video>...</video> blocks with a placeholder caption.
    video_count = len(HTML_VIDEO_RE.findall(body))
    if video_count:
        body = HTML_VIDEO_RE.sub(
            "\n\n> 🎬 视频素材（飞书文档不直接支持嵌入，请在微信/网页渠道查看）\n\n",
            body,
        )
        warnings.append(
            f"{video_count} <video> block(s) downgraded to placeholder text."
        )

    # 3. Remove <source .../> tags that are paired with videos.
    source_count = len(HTML_SOURCE_RE.findall(body))
    if source_count:
        body = HTML_SOURCE_RE.sub("", body)

    # 4. Remove known bad void tags.
    removed_void: set[str] = set()

    def remove_void(m: re.Match[str]) -> str:
        removed_void.add(m.group(1).lower())
        return ""

    body = HTML_BAD_VOID_RE.sub(remove_void, body)

    # 5. Remove known bad paired tags.
    removed_pair: set[str] = set()

    def remove_pair(m: re.Match[str]) -> str:
        removed_pair.add(m.group(1).lower())
        return ""

    body = HTML_BAD_PAIRED_RE.sub(remove_pair, body)

    removed = removed_void | removed_pair
    if removed:
        warnings.append(
            f"Potentially unsafe HTML tag(s) removed: {', '.join(sorted(removed))}."
        )

    return body, warnings


# ---------------------------------------------------------------------------
# mermaid extraction
# ---------------------------------------------------------------------------

# Match ```mermaid ... ``` fenced code blocks (multiline, lazy).
# We deliberately keep this simple — no nested fences, no indented blocks.
MERMAID_RE = re.compile(
    r"^```mermaid\s*\n(?P<code>.*?)\n```\s*$",
    re.MULTILINE | re.DOTALL,
)


MERMAID_MODES = ("whiteboard", "code")


def rewrite_mermaid(body: str, mode: str = "code") -> tuple[str, int]:
    """Handle ```mermaid blocks according to `mode`.

    Modes:
      - "whiteboard": replace with `<whiteboard type="mermaid">...</whiteboard>`
        inline XML. Feishu's markdown renderer creates a real whiteboard block
        server-side. IMPORTANT: do NOT XML-escape mermaid contents — Mermaid
        syntax uses `-->`, `==>`, `&` etc. literally; escaping `>` to `&gt;`
        causes Feishu to return warning code 2107 ("Whiteboard content parse
        failed"). Also do NOT insert `<br/>` HTML tags for newlines; use `\\n`
        (Mermaid newline syntax), otherwise the whiteboard parser fails.
      - "code" (default): leave as a fenced ```mermaid code block. Feishu
        renders this as a syntax-highlighted code block with language label
        "mermaid"; the diagram source is preserved verbatim and readers can
        copy it. Use this when you want the source to stay readable/editable,
        or when the Mermaid is complex (subgraphs, notes, long labels) and
        whiteboard rendering is lossy.
    """
    if mode not in MERMAID_MODES:
        raise ValueError(
            f"unknown mermaid mode {mode!r}; expected one of {MERMAID_MODES}"
        )

    count = 0

    def repl_whiteboard(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        code = m.group("code")
        return f'<whiteboard type="mermaid">\n{code}\n</whiteboard>'

    def repl_code(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        # Leave the fence intact; Feishu's markdown renderer preserves it as a
        # code block with language "mermaid". No transformation needed.
        return m.group(0)

    repl = repl_whiteboard if mode == "whiteboard" else repl_code
    return MERMAID_RE.sub(repl, body), count


# ---------------------------------------------------------------------------
# highlight markers (==text==) → Feishu callout
# ---------------------------------------------------------------------------

# Some writing-agent-harness articles use the markdown-like ==highlight text==
# convention for key takeaway lines. Feishu markdown mode does not understand
# this syntax, so it renders the literal == markers. Convert them to a
# <callout> block with a light-yellow background.
HIGHLIGHT_RE = re.compile(r"^==([^=\n]+)==\s*$", re.MULTILINE)


def rewrite_highlights(body: str) -> tuple[str, int]:
    """Replace standalone ==text== lines with Feishu callout blocks."""
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        text = m.group(1).strip()
        return (
            '\n<callout emoji="💡" background-color="light-yellow" border-color="yellow">\n'
            f'  <p>{text}</p>\n'
            '</callout>\n'
        )

    return HIGHLIGHT_RE.sub(repl, body), count


# ---------------------------------------------------------------------------
# warnings / lint
# ---------------------------------------------------------------------------

WARN_PATTERNS: list[tuple[str, str]] = [
    (r"^\$\$.*?\$\$", "Block-level LaTeX ($$...$$) downgrades to inline; complex math may lose fidelity."),
    (r"<details>", "<details> blocks are not supported by Feishu; will render as plain text."),
    (r"\[\^[\w-]+\]:", "Footnotes are not natively supported; will render as plain text."),
    (r"<kbd>", "<kbd> tags are not supported by Feishu; will render as plain text."),
]


def lint(body: str) -> list[str]:
    warnings = []
    for pat, msg in WARN_PATTERNS:
        if re.search(pat, body, re.MULTILINE | re.DOTALL):
            warnings.append(msg)
    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_prepare(args: argparse.Namespace) -> int:
    src = Path(args.input).resolve()
    if not src.exists():
        print(f"ERROR: input file not found: {src}", file=sys.stderr)
        return 2
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    text = src.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    title = derive_title(fm, body, fallback=src.stem)

    body, html_warnings = sanitize_html_for_feishu(body)
    body, images = collect_and_rewrite_images(body, src)
    body, mermaid_count = rewrite_mermaid(body, mode=args.mermaid_mode)
    body, highlight_count = rewrite_highlights(body)
    warnings = lint(body) + html_warnings
    if highlight_count:
        warnings.append(f"{highlight_count} highlight line(s) converted to Feishu callout.")
    if args.mermaid_mode == "code" and mermaid_count:
        warnings.append(
            f"{mermaid_count} mermaid block(s) kept as ```mermaid code blocks "
            "(not converted to whiteboard; use --mermaid-mode whiteboard to render as diagrams)."
        )

    processed_md = workdir / "processed.md"
    processed_md.write_text(body.lstrip("\n"), encoding="utf-8")

    manifest = {
        "source": str(src),
        "title": title,
        "frontmatter": fm,
        "images": images,
        "mermaid_count": mermaid_count,
        "mermaid_mode": args.mermaid_mode,
        "warnings": warnings,
    }
    manifest_path = workdir / "manifest.json"
    # default=str handles datetime.date / datetime.datetime that PyYAML returns
    # for ISO-formatted dates in frontmatter (e.g. `date: 2026-06-12`).
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # Compact summary to stdout for the agent to read.
    missing_count = sum(1 for i in images if i.get("missing"))
    print(json.dumps(
        {
            "ok": True,
            "title": title,
            "processed_md": str(processed_md),
            "manifest": str(manifest_path),
            "image_count": len(images),
            "missing_images": missing_count,
            "mermaid_count": mermaid_count,
            "warnings": warnings,
        },
        ensure_ascii=False,
    ))
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    workdir = Path(args.workdir).resolve()
    manifest_path = workdir / "manifest.json"
    processed_md = workdir / "processed.md"
    final_md = workdir / "final.md"

    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    if not processed_md.exists():
        print(f"ERROR: processed.md not found: {processed_md}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    body = processed_md.read_text(encoding="utf-8")

    missing = []
    replaced = 0
    skipped_missing = 0
    for img in manifest.get("images", []):
        token = img.get("file_token")
        placeholder = img["placeholder"]
        if img.get("missing"):
            skipped_missing += 1
            continue
        if not token:
            missing.append(placeholder)
            continue
        if placeholder in body:
            body = body.replace(placeholder, token)
            replaced += 1

    if missing:
        print(
            f"ERROR: {len(missing)} image(s) have no file_token in manifest: {missing}",
            file=sys.stderr,
        )
        return 3

    final_md.write_text(body, encoding="utf-8")
    print(json.dumps(
        {
            "ok": True,
            "final_md": str(final_md),
            "images_replaced": replaced,
            "images_missing": skipped_missing,
        },
        ensure_ascii=False,
    ))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="finalize mode: replace placeholders in processed.md using manifest.json",
    )
    parser.add_argument(
        "--input",
        help="input markdown path (prepare mode)",
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="working directory for processed.md / manifest.json / final.md",
    )
    parser.add_argument(
        "--mermaid-mode",
        choices=MERMAID_MODES,
        default="code",
        help=(
            "how to handle ```mermaid blocks: 'code' (default) keeps them as "
            "fenced mermaid code blocks; 'whiteboard' converts them to Feishu "
            "whiteboard inline XML (rendered as diagrams, may fail on complex syntax)."
        ),
    )
    args = parser.parse_args()

    if args.finalize:
        return cmd_finalize(args)
    if not args.input:
        parser.error("--input is required in prepare mode")
    return cmd_prepare(args)


if __name__ == "__main__":
    raise SystemExit(main())
