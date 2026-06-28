#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Compose final Notion content from a cleaned markdown file, using ntn CLI.

Inputs:
  - Cleaned markdown (already structured + summarized by the agent)
  - Path to manifest.json from fetch_article.py (for image local paths + article metadata)
  - Notion target URL (page / database / database row)
  - Optional: cover image path, metadata overrides, emoji icon

Flow:
  1. Probe Notion target via ntn CLI → determine kind (page / data_source / database)
  2. Read cleaned markdown; rewrite `![alt](path)` references to NTN_IMG_MARKER_<idx>
     sentinels and collect (idx → local_path) mapping
  3. For plain-page targets, prepend a quote-block article card (title/source/date/url)
  4. Upload images + create page (create-page-with-images) OR clear existing page
     and re-append content (for existing-page overwrite)
  5. Upload + set cover (if provided)
  6. Set properties (for data_source rows — uses property_mapper.py to build payload
     from metadata, then PATCHes via ntn set-properties)
  7. Print result JSON: {ok, page_id, url, images_uploaded, properties_set, cover_set}

The cleaning/summarization is NOT done here; the agent does that and passes
in the final markdown via --content-file. This script is purely "compose +
upload + write".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────────
# Paths: locate ntn_cli.py helper from notion-cli skill (sibling skill)
# ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
NOTION_CLI_HELPER = SKILL_DIR.parent / "notion-cli" / "scripts" / "ntn_cli.py"

if not NOTION_CLI_HELPER.exists():
    sys.stderr.write(
        f"Error: notion-cli helper not found at {NOTION_CLI_HELPER}. "
        "Ensure the notion-cli skill is installed alongside article-to-notion.\n"
    )
    sys.exit(1)


def _run(*args: str, input_text: str | None = None,
         timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run ntn_cli.py helper and return CompletedProcess (text mode)."""
    cmd = ["uv", "run", str(NOTION_CLI_HELPER), *args]
    kw: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
    }
    if input_text is not None:
        kw["input"] = input_text
    else:
        kw["stdin"] = subprocess.DEVNULL
    proc = subprocess.run(cmd, **kw)
    if check and proc.returncode != 0:
        sys.stderr.write(f"Error running: {' '.join(cmd)}\n")
        sys.stderr.write(f"stderr: {proc.stderr}\n")
        sys.stderr.write(f"stdout: {proc.stdout}\n")
        sys.exit(2)
    return proc


def _json(*args: str, timeout: int = 60) -> Any:
    proc = _run(*args, timeout=timeout)
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Expected JSON from {' '.join(args)}, got:\n{out[:500]}\n")
        raise


# ────────────────────────────────────────────────────────────────────
# Image rewrite in markdown
# ────────────────────────────────────────────────────────────────────

# Match ![alt](path) — path may be a local filesystem path, relative path, or http(s) URL.
# We only rewrite local paths; external URLs are left untouched (Notion will create
# external image blocks for them — acceptable for non-WeChat sources).
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

# Common WeChat/public-account tail boilerplate patterns to strip before upload.
# Matched case-insensitively against the paragraph text; entire paragraph is removed.
BOILERPLATE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"本公众号.*?(关注|分享|免费分享|实战案例|干货|更多)"),
    re.compile(r"欢迎关注(公众号|我的公众号)"),
    re.compile(r"扫码.*?(关注|加入|星球|群)"),
    re.compile(r"点击(上方|右下角).*?(关注|在看|星标)"),
    re.compile(r"往期推荐|相关阅读|推荐阅读|精选文章"),
    re.compile(r"未经授权.*?转载"),
    re.compile(r"加入.*?知识星球"),
)


def _normalize_markdown(markdown: str) -> str:
    """Defensive markdown normalization before handing to ntn:

    - Merge multi-line quoted blocks separated by blank `>` lines into a single
      quote block separated by <br> (ntn splits `>` lines into independent quote
      blocks — see gotcha). Any run of consecutive `>` lines (optionally
      separated by `>` empty lines) becomes one `>` line joined with <br>.
    - Drop a leading H1 that duplicates the article title (the article card
      already shows the title; a second H1 in the body is redundant).
    - Strip known tail boilerplate paragraphs (公众号 promotional text).
    """
    lines = markdown.split("\n")

    # 1. Merge quoted blocks
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith(">"):
            # Collect a run of quoted lines (possibly including empty `>` or `> ` lines)
            quoted_pieces: list[str] = []
            while i < len(lines):
                s = lines[i].lstrip()
                if not s.startswith(">"):
                    break
                content = s[1:] if s.startswith("> ") else (s[1:] if s.startswith(">") else "")
                if content.strip():
                    quoted_pieces.append(content.strip())
                i += 1
            if quoted_pieces:
                out.append("> " + "<br>".join(quoted_pieces))
            # (drop empty `>` breaks entirely — they contributed no content)
        else:
            out.append(line)
            i += 1

    md = "\n".join(out)

    # 2. Drop leading H1 if present (redundant with article card).
    #    Match optional leading whitespace + "# " + title text at start.
    md = re.sub(r"^\s*#\s+[^\n]+\n+", "", md, count=1)

    # 3. Strip tail boilerplate paragraphs: iterate non-empty lines from bottom
    #    and drop contiguous paragraphs at the END that match boilerplate patterns.
    #    (Don't remove paragraphs mid-article.)
    md = _strip_tail_boilerplate(md)

    return md


def _strip_tail_boilerplate(markdown: str) -> str:
    """Remove known public-account promotional / nav-list blocks from the tail.

    Iterate non-empty blocks from the bottom and drop contiguous blocks that
    look like boilerplate: promo paragraphs, "推荐阅读"-style section headers,
    or lists of WeChat album links. Stops as soon as a real-content block is
    encountered. Mid-article blocks are never touched.
    """
    blocks = re.split(r"\n\s*\n", markdown)

    def _is_image_block(b: str) -> bool:
        s = b.strip()
        return s.startswith("![") or "NTN_IMG_MARKER_" in s

    def _is_promo_text(b: str) -> bool:
        flat = re.sub(r"[*_`>#\-]", "", b).strip()
        if not flat or len(flat) < 2:
            return True  # empty block
        return any(p.search(flat) for p in BOILERPLATE_PATTERNS)

    def _is_album_link_list(b: str) -> bool:
        """Detect blocks that are entirely lists of WeChat album/推荐 links,
        or bold-only section headers like **推荐阅读** that introduce them."""
        lines = [ln.strip() for ln in b.strip().splitlines() if ln.strip()]
        if not lines:
            return False
        has_album_link = False
        for ln in lines:
            m = re.match(r"^[*\-]\s*\[([^\]]+)\]\(([^)]+)\)$", ln) or \
                re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", ln)
            if m:
                url = m.group(2)
                if "appmsgalbum" in url or "/mp/profile_ext" in url or "mp/homepage" in url:
                    has_album_link = True
                    continue
                return False  # a link to somewhere else — real content
            # Bold-only section header (e.g. **推荐阅读**) is fine only if it's short
            if re.fullmatch(r"\*\*[^*]{1,20}\*\*", ln):
                continue
            return False  # arbitrary text, not an album list
        # Block only qualifies as boilerplate if it actually has an album link
        # (otherwise a lone bold short line like **要点** would get wrongly dropped)
        return has_album_link

    def _is_boilerplate_header(b: str) -> bool:
        """Bold-only headers like **推荐阅读** / **往期推荐** (when they stand alone)."""
        s = b.strip()
        if not re.fullmatch(r"\*\*[^*]{1,20}\*\*", s):
            return False
        flat = re.sub(r"[*_`>#\-]", "", s).strip()
        return any(p.search(flat) for p in BOILERPLATE_PATTERNS)

    # Walk from the end. Tail image blocks (e.g. a QR code after promo text)
    # shouldn't stop boilerplate removal — we pop promo/album/header blocks,
    # then stop at the first real-content block. Images are preserved either
    # way (we don't auto-delete images; QR filtering is the agent's job).
    tail_images: list[str] = []
    # First, collect trailing image blocks so we can re-append after stripping
    while blocks and _is_image_block(blocks[-1].strip()):
        tail_images.insert(0, blocks.pop())
    while blocks:
        last = blocks[-1].strip()
        if not last:
            blocks.pop()
            continue
        if _is_promo_text(last) or _is_album_link_list(last) or _is_boilerplate_header(last):
            blocks.pop()
            continue
        break
    blocks.extend(tail_images)
    return "\n\n".join(blocks)


def _is_local_path(src: str) -> bool:
    if src.startswith(("http://", "https://", "data:", "file:")):
        return False
    return True


def _resolve_local_path(src: str, content_dir: Path, fetch_dir: Path | None) -> Path | None:
    """Resolve a markdown image src to an existing local file."""
    p = Path(src)
    if p.is_absolute() and p.exists():
        return p
    # relative to content file
    if content_dir and (content_dir / p).exists():
        return (content_dir / p).resolve()
    # relative to fetch_dir/assets
    if fetch_dir:
        for base in (fetch_dir, fetch_dir / "assets"):
            cand = base / p.name if not p.is_absolute() else p
            if cand.exists():
                return cand.resolve()
            # also try src as bare filename
            cand2 = base / Path(src).name
            if cand2.exists():
                return cand2.resolve()
    return None


def rewrite_images(
    markdown: str,
    content_dir: Path,
    fetch_dir: Path | None,
) -> tuple[str, dict[str, str]]:
    """Replace local `![alt](path)` with NTN_IMG_MARKER_<idx> sentinels.
    Returns (new_markdown, {str(idx): abs_path_str}).
    External images are left as-is.
    """
    images: dict[str, str] = {}
    counter = 0

    def _replace(m: re.Match) -> str:
        nonlocal counter
        alt = m.group(1)
        src = m.group(2).strip()
        if not _is_local_path(src):
            return m.group(0)  # leave external as-is
        local = _resolve_local_path(src, content_dir, fetch_dir)
        if local is None:
            sys.stderr.write(f"Warning: image not found locally: {src!r}, keeping as external.\n")
            return m.group(0)
        idx = str(counter)
        images[idx] = str(local)
        counter += 1
        return f"\n\nNTN_IMG_MARKER_{idx}\n\n"

    new_md = IMG_RE.sub(_replace, markdown)
    return new_md, images


# ────────────────────────────────────────────────────────────────────
# Metadata → article card quote block (for plain pages)
# ────────────────────────────────────────────────────────────────────

def build_article_card(meta: dict[str, Any]) -> str:
    """Build a single-quote-block article card prepended to plain pages.

    ntn's markdown parser treats each `>` line as a separate quote block when
    lines are separated by newlines (CommonMark soft breaks are not grouped into
    one quote block by this parser). To keep the metadata visually grouped in
    a SINGLE quote block, join lines with `<br>` on a single `>` paragraph.

    Output (single line):
        > **标题**：《...》<br>**来源**：...<br>**发布时间**：YYYY-MM-DD<br>**原文**：[链接](URL)
    """
    parts: list[str] = []
    title = meta.get("title") or "(无标题)"
    author = meta.get("author") or meta.get("source") or ""
    date = meta.get("date") or meta.get("published") or ""
    url = meta.get("url") or ""

    parts.append(f"**标题**：《{title}》")
    if author:
        parts.append(f"**来源**：{author}")
    if date:
        date_str = str(date)[:10] if len(str(date)) >= 10 else str(date)
        parts.append(f"**发布时间**：{date_str}")
    if url:
        parts.append(f"**原文**：[链接]({url})")
    return "> " + "<br>".join(parts) + "\n\n"


# ────────────────────────────────────────────────────────────────────
# Main compose
# ────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compose a Notion page from cleaned markdown + local images, using ntn CLI."
    )
    parser.add_argument("--notion-target", required=True,
                        help="Notion URL or page/database/data-source ID")
    parser.add_argument("--content-file", required=True,
                        help="Path to cleaned markdown file")
    parser.add_argument("--fetch-dir",
                        help="Directory with assets/ from fetch_article.py (for image resolution)")
    parser.add_argument("--metadata",
                        help="Path to metadata JSON (title/url/summary/tags/author/date/cover)")
    parser.add_argument("--cover",
                        help="Local path to cover image, or 'none' to skip")
    parser.add_argument("--icon-emoji", help="Emoji icon for the page")
    parser.add_argument("--mode", choices=["auto", "append", "overwrite", "create"],
                        default="auto",
                        help="How to write: auto (create new if target is database/data_source or "
                             "plain page URL points to a container; overwrite existing page). "
                             "append: append to existing page. overwrite: clear and rewrite. "
                             "create: always create new child page.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be done without calling Notion")
    parser.add_argument("--output-json", action="store_true", default=True,
                        help="Print JSON result on stdout (default)")
    args = parser.parse_args(argv)

    content_path = Path(args.content_file).resolve()
    content_dir = content_path.parent
    markdown = content_path.read_text(encoding="utf-8")

    # Strip YAML frontmatter (ntn pages create does NOT parse frontmatter into
    # properties; a leading --- block would render as a divider + field list).
    # Metadata is taken from --metadata or manifest.json, so we safely drop it.
    if markdown.startswith("---\n"):
        end = markdown.find("\n---\n", 4)
        if end != -1:
            markdown = markdown[end + 5:].lstrip("\n")

    # Defensive normalization: merge split quote blocks, drop duplicate H1,
    # strip tail boilerplate.
    markdown = _normalize_markdown(markdown)

    fetch_dir = Path(args.fetch_dir).resolve() if args.fetch_dir else None
    if fetch_dir and not fetch_dir.exists():
        sys.stderr.write(f"Warning: --fetch-dir {fetch_dir} doesn't exist, ignoring.\n")
        fetch_dir = None

    # Load metadata (from --metadata JSON, or manifest.json in fetch_dir)
    meta: dict[str, Any] = {}
    if args.metadata:
        meta = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    elif fetch_dir and (fetch_dir / "manifest.json").exists():
        meta = json.loads((fetch_dir / "manifest.json").read_text(encoding="utf-8"))

    # Normalize common field-name variants (fetch_article.py uses different keys
    # than the semantic schema expected by build_article_card / property_mapper)
    meta.setdefault("title", meta.get("title") or "")
    if not meta.get("author"):
        meta["author"] = meta.get("account") or meta.get("source") or ""
    if not meta.get("date"):
        date_raw = meta.get("publish_time") or meta.get("published") or meta.get("fetched_at") or ""
        # Normalize "2026年6月24日 19:38" / "2026-06-24T..." / "2026-06-24" → YYYY-MM-DD
        m = re.search(r"(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})", str(date_raw))
        if m:
            meta["date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        else:
            meta["date"] = str(date_raw)[:10] if date_raw else ""
    if not meta.get("url"):
        meta["url"] = meta.get("source_url") or ""

    # 1. Probe target
    probe_result = _json("probe", args.notion_target)
    target_kind = probe_result["kind"]
    target_id = probe_result["id"]
    sys.stderr.write(f"[probe] target={target_kind} id={target_id}\n")

    # 2. Rewrite local images to sentinel markers
    processed_md, image_map = rewrite_images(markdown, content_dir, fetch_dir)
    sys.stderr.write(f"[images] found {len(image_map)} local image(s) to upload\n")

    # 3. For plain-page creation, prepend article card
    # If target is a data_source (row create), the article card becomes part of content;
    # database will have properties for that metadata. But we still add the card for
    # discoverability inside the page body.
    if target_kind in ("page", "database") or (target_kind == "data_source" and not meta.get("_no_card")):
        # Only add card when creating new pages or overwriting (not appending)
        if args.mode in ("auto", "create", "overwrite"):
            card = build_article_card(meta)
            processed_md = card + processed_md

    # Resolve parent / target-page for create vs overwrite
    parent_ref: str | None = None
    existing_page_id: str | None = None
    is_overwrite = False

    if target_kind == "page":
        if args.mode == "create":
            parent_ref = f"page:{target_id}"  # create a child page under it
        elif args.mode == "append":
            parent_ref = f"page:{target_id}"
            existing_page_id = target_id
        elif args.mode == "overwrite":
            # Clear existing content and rewrite the SAME page
            is_overwrite = True
            existing_page_id = target_id
        else:  # auto: treat page URL as parent container for a new clipped page
            parent_ref = f"page:{target_id}"
    elif target_kind == "data_source":
        parent_ref = f"data-source:{target_id}"
    elif target_kind == "database":
        if not probe_result.get("default_data_source_id"):
            sys.stderr.write(
                "Error: database target has multiple data sources; pass the data-source ID directly.\n"
            )
            return 3
        parent_ref = f"data-source:{probe_result['default_data_source_id']}"
    else:
        sys.stderr.write(f"Error: unsupported target kind {target_kind}\n")
        return 3

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "target_kind": target_kind,
            "parent_ref": parent_ref,
            "existing_page_id": existing_page_id,
            "is_overwrite": is_overwrite,
            "images_to_upload": image_map,
            "markdown_length": len(processed_md),
            "metadata_keys": list(meta.keys()),
        }, ensure_ascii=False, indent=2))
        return 0

    # 4. Write markdown + images: either create new page or overwrite existing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(processed_md)
        md_tmp = Path(tf.name)

    try:
        if is_overwrite:
            assert existing_page_id is not None
            create_args = ["overwrite-page-with-images", "--page-id", existing_page_id,
                           "--content-file", str(md_tmp)]
        else:
            assert parent_ref is not None
            create_args = ["create-page-with-images", "--parent", parent_ref,
                           "--content-file", str(md_tmp)]
        for k, path in image_map.items():
            create_args += ["--image", f"{k}={path}"]
        result = _json(*create_args, timeout=180)
        page_id = result["page_id"]
        file_ids = result["file_upload_ids"]
        sys.stderr.write(f"[write] page_id={page_id}, images={len(file_ids)} (mode={'overwrite' if is_overwrite else 'create'})\n")
    finally:
        md_tmp.unlink(missing_ok=True)

    # 5. Set cover
    cover_set = False
    cover_path = None
    if args.cover and args.cover.lower() != "none":
        cover_path = Path(args.cover)
    elif meta.get("cover_local_path"):
        cover_path = Path(meta["cover_local_path"])
    if cover_path and cover_path.exists():
        cover_id = _json("upload-file", str(cover_path),
                         "--filename", cover_path.name,
                         "--content-type", "image/png" if cover_path.suffix.lower() == ".png" else "image/jpeg",
                         timeout=120)
        # upload-file in JSON mode returns {"file_upload_id": "..."} when called with --json;
        # our helper outputs raw ID by default when not in --json. Check.
        if isinstance(cover_id, dict):
            cover_id = cover_id.get("file_upload_id")
        _run("set-cover", page_id, "--file-id", str(cover_id), timeout=30)
        cover_set = True
        sys.stderr.write(f"[cover] set ({cover_path.name})\n")

    # 6. Set icon
    icon_set = False
    if args.icon_emoji:
        _run("set-icon", page_id, "--emoji", args.icon_emoji, timeout=15)
        icon_set = True

    # 7. Set properties (when the written page is a database row)
    properties_set: list[str] = []
    # Determine the data_source_id for this page, if it's a database row.
    ds_id: str | None = None
    if target_kind in ("data_source", "database"):
        ds_id = (target_id if target_kind == "data_source"
                 else probe_result.get("default_data_source_id"))
    elif target_kind == "page" and (is_overwrite or args.mode == "append"):
        # Overwriting an existing page — if it lives in a data_source, set properties too.
        ds_id = probe_result.get("data_source_id") or probe_result.get("parent_id") \
            if probe_result.get("parent_type") == "data_source_id" else None

    if ds_id and meta:
        # Use property_mapper.py to build Notion-shaped properties from metadata
        props_dir = Path(__file__).parent
        pm_script = props_dir / "property_mapper.py"
        if pm_script.exists():
            # Fetch schema via probe (we need the raw properties schema)
            ds_info = _json("probe", f"data-source:{ds_id}", timeout=30)
            # property_mapper expects schema in Notion API's original shape
            # (type-specific options nested); our probe's simplified form doesn't
            # contain options nested under {type: {options:...}}.
            # Build the raw schema shape by fetching data source directly.
            ds_raw = _run_api_get(f"v1/data_sources/{ds_id}")
            raw_schema = ds_raw.get("properties", {})

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as sf:
                json.dump(raw_schema, sf, ensure_ascii=False)
                schema_tmp = Path(sf.name)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as mf:
                json.dump(meta, mf, ensure_ascii=False)
                meta_tmp = Path(mf.name)
            try:
                pm_proc = subprocess.run(
                    ["uv", "run", str(pm_script),
                     "--schema", str(schema_tmp), "--metadata", str(meta_tmp)],
                    capture_output=True, text=True, timeout=30,
                )
                if pm_proc.returncode == 0:
                    pm_out = json.loads(pm_proc.stdout)
                    props_payload = pm_out["properties"]
                    report = pm_out["report"]
                    if props_payload:
                        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as pf:
                            json.dump(props_payload, pf, ensure_ascii=False)
                            props_tmp = Path(pf.name)
                        try:
                            _run("set-properties", page_id,
                                 "--properties-file", str(props_tmp),
                                 "--data-source-id", ds_id,
                                 timeout=30)
                            properties_set = list(props_payload.keys())
                            sys.stderr.write(f"[properties] set: {properties_set}\n")
                            for s in report.get("skipped", []):
                                sys.stderr.write(f"[properties] skip {s['semantic']}: {s['reason']}\n")
                        finally:
                            props_tmp.unlink(missing_ok=True)
                else:
                    sys.stderr.write(f"[properties] mapper failed: {pm_proc.stderr}\n")
            finally:
                schema_tmp.unlink(missing_ok=True)
                meta_tmp.unlink(missing_ok=True)

    # 8. Fetch the page to get its URL
    page = _json("get-page", page_id, "--json", timeout=30)
    url = page.get("page", {}).get("url", "") if isinstance(page, dict) else ""

    result = {
        "ok": True,
        "page_id": page_id,
        "url": url,
        "images_uploaded": len(file_ids),
        "cover_set": cover_set,
        "icon_set": icon_set,
        "properties_set": properties_set,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _run_api_get(path: str) -> dict:
    """Direct ntn api GET (not through ntn_cli wrapper which has specific
    output shaping). Uses subprocess with ntn directly to get raw JSON."""
    ntn = shutil.which("ntn")
    if not ntn:
        sys.stderr.write("Error: `ntn` CLI not found in PATH.\n")
        sys.exit(2)
    proc = subprocess.run(
        [ntn, "api", path],
        capture_output=True, text=True, timeout=30,
        stdin=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"ntn api {path} failed: {proc.stderr}\n")
        sys.exit(2)
    return json.loads(proc.stdout)


import shutil  # noqa: E402 — needed for _run_api_get


if __name__ == "__main__":
    raise SystemExit(main())
