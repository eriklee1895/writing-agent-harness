#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Sync canonical origin articles into Erik Lee's Astro blog posts directory.

This is intentionally a one-way adapter: content/origin remains the source of
truth, and eriklee-blog receives rendered publishing copies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<yaml>.*?)\n---\s*\n?", re.DOTALL)
DEFAULT_ARTICLE_NAMES = ("index.md", "article.md")
NON_ARTICLE_STEMS = {
    "notes",
    "note",
    "readme",
    "sources",
    "source",
    "outline",
    "brief",
    "draft",
}
MDX_VOID_TAGS = "area|base|br|col|embed|hr|img|input|link|meta|param|source|track|wbr"


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    return parse_simple_yaml(match.group("yaml")), text[match.end() :]


def parse_simple_yaml(raw: str) -> dict[str, object]:
    """Parse the small YAML subset used by this repo's article frontmatter."""

    data: dict[str, object] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines):
                child = lines[j]
                if not child.startswith((" ", "\t")):
                    break
                stripped = child.strip()
                if stripped.startswith("- "):
                    items.append(unquote(stripped[2:].strip()))
                j += 1
            data[key] = items if items else ""
            i = j
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [unquote(part.strip()) for part in inner.split(",") if part.strip()]
        elif value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        else:
            data[key] = unquote(value)
        i += 1
    return data


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def yaml_list(values: object) -> list[str]:
    if not isinstance(values, list):
        values = ["others"] if not values else [str(values)]
    lines = ["tags:"]
    for item in values:
        lines.append(f"  - {yaml_scalar(item)}")
    return lines


def yaml_optional_string(key: str, value: object) -> str:
    if value in (None, ""):
        return ""
    return f"{key}: {yaml_scalar(value)}"


def coerce_pub_datetime(value: object) -> str:
    if not value:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    text = str(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00Z"
    if text.endswith("Z"):
        return text
    if re.search(r"T\d{2}:\d{2}", text):
        return text
    return f"{text}T00:00:00Z"


def date_from_slug(slug: str) -> str | None:
    match = re.match(r"(\d{4}-\d{2}-\d{2})-", slug)
    return match.group(1) if match else None


def first_heading_title(body: str) -> str:
    for line in body.splitlines():
        match = re.match(r"#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return ""


def first_paragraph_excerpt(body: str) -> str:
    body_without_images = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body)
    for block in re.split(r"\n\s*\n", body_without_images):
        block = block.strip()
        if not block or block.startswith(("#", "```", "|", "- ", "* ")):
            continue
        block = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", block)
        block = re.sub(r"[*_`>#]", "", block)
        block = " ".join(block.split())
        if block:
            return block[:180]
    return ""


def strip_duplicate_title_heading(body: str, title: object) -> str:
    title_text = str(title or "").strip()
    if not title_text:
        return body
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip() == f"# {title_text}":
        lines.pop(0)
        if lines and not lines[0].strip():
            lines.pop(0)
        return "\n".join(lines).lstrip("\n")
    return body


def normalize_asset_path(value: object, slug: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.removeprefix("./")
    if text.startswith("assets/"):
        return f"./assets/{slug}/{text.removeprefix('assets/')}"
    return text


def source_asset_exists(source_dir: Path, value: object) -> bool:
    """Whether an asset reference resolves to a file **in the origin tree**.

    Use this only when the answer gates a destructive action — see
    `strip_leading_cover_image`. For "should I write this frontmatter field?",
    use `asset_exists_in_source_or_destination` instead.
    """
    text = str(value or "").strip().removeprefix("./")
    if not text.startswith("assets/"):
        return True
    return (source_dir / text).exists()


def asset_exists_in_source_or_destination(
    source_dir: Path, value: object, destination_assets_dir: Path
) -> bool:
    """Whether an asset reference is resolvable by *either* repository.

    Frontmatter fields like `cover` must not be blanked just because the origin
    working tree lacks the file. Image binaries are gitignored, so a clean
    checkout legitimately has none of them while the blog still serves its own
    committed copy — blanking on that basis deletes `heroImage`/`ogImage` from
    published posts and requires hand-repair that the next sync destroys again.

    This is the same source-OR-destination idiom `replace_missing_asset_refs`
    uses below, and it is justified by the same reasoning as the "deliberately
    additive" comment in `sync_article`.

    Do NOT collapse this into `source_asset_exists`, and do NOT "unify" the two
    call sites. They answer different questions: this one gates writing a field,
    the other gates deleting an image from the body. The strict one must stay
    strict.
    """
    text = str(value or "").strip().removeprefix("./")
    if not text.startswith("assets/"):
        return True
    relative = text.removeprefix("assets/")
    return (source_dir / text).exists() or (destination_assets_dir / relative).exists()


def rewrite_asset_links(body: str, slug: str) -> str:
    """Point article-local assets at the shared Astro posts/assets/<slug>/ dir."""

    body = body.replace("(./assets/", f"(./assets/{slug}/")
    body = body.replace("(assets/", f"(./assets/{slug}/")
    body = body.replace('src="./assets/', f'src="./assets/{slug}/')
    body = body.replace('src="assets/', f'src="./assets/{slug}/')
    return body


def replace_missing_asset_refs(
    body: str,
    source_dir: Path,
    destination_assets_dir: Path,
    slug: str,
) -> str:
    def is_external_url(url: str) -> bool:
        return bool(re.match(r"^(https?:|mailto:|data:|#)", url))

    def replace_markdown_image(match: re.Match[str]) -> str:
        alt = match.group(1).strip() or "image"
        url = match.group(2).strip()
        if is_external_url(url):
            return match.group(0)
        local = url.removeprefix("./")
        prefix = f"assets/{slug}/"
        if local.startswith(prefix):
            source_rel = "assets/" + local.removeprefix(prefix)
            destination_rel = local.removeprefix(prefix)
            if not (source_dir / source_rel).exists() and not (destination_assets_dir / destination_rel).exists():
                return f"*Image pending: {alt}*"
            return match.group(0)
        if not local.startswith("/"):
            return f"*Image pending: {alt}*"
        return match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_markdown_image, body)


def find_local_archive_root(source_dir: Path) -> Path | None:
    for candidate in [Path.cwd(), *source_dir.parents]:
        archive = candidate / ".local-archive"
        if archive.exists():
            return archive
    return None


def find_local_archive_image(source_dir: Path, url: str) -> Path | None:
    local = url.removeprefix("./")
    resolved = (source_dir / local).resolve()
    if resolved.exists() and resolved.is_file():
        return resolved

    archive_root = find_local_archive_root(source_dir)
    if not archive_root:
        return None

    basename = Path(local).name
    matches = sorted(
        path
        for path in archive_root.rglob(basename)
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    )
    return matches[0] if matches else None


def materialize_local_image_refs(
    body: str,
    source_dir: Path,
    destination_assets_dir: Path,
    slug: str,
) -> str:
    """Copy referenced local archive images into the blog asset directory."""

    def is_external_url(url: str) -> bool:
        return bool(re.match(r"^(https?:|mailto:|data:|#)", url))

    def rewrite_markdown_image(match: re.Match[str]) -> str:
        alt = match.group(1)
        url = match.group(2).strip()
        if is_external_url(url):
            return match.group(0)

        local = url.removeprefix("./")
        prefix = f"assets/{slug}/"
        if local.startswith(prefix) and (source_dir / "assets" / local.removeprefix(prefix)).exists():
            return match.group(0)

        image_source = find_local_archive_image(source_dir, url)
        if not image_source:
            return match.group(0)

        destination_assets_dir.mkdir(parents=True, exist_ok=True)
        destination_name = image_source.name
        destination_path = destination_assets_dir / destination_name
        if not destination_path.exists() or image_source.stat().st_size != destination_path.stat().st_size:
            shutil.copy2(image_source, destination_path)
        return f"![{alt}](./assets/{slug}/{destination_name})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", rewrite_markdown_image, body)


# `<callout emoji="…">…</callout>` is the block syntax used by the upstream /
# forum export of some origin sources. The blog has no <callout> component, and
# MDX treats an unknown lowercase tag as a literal HTML element, so it renders
# unstyled. rehype-callouts IS configured, so translate to the GitHub alert
# syntax it understands. The canonical source keeps its own markup untouched.
_CALLOUT_BLOCK_RE = re.compile(
    r"^[ \t]*<callout\b[^>]*?emoji=\"([^\"]*)\"[^>]*>\s*(.*?)\s*</callout>[ \t]*$",
    re.S | re.M,
)
_EMOJI_TO_ALERT = {
    "🎁": "note", "📌": "note", "📝": "note",
    "💡": "tip", "✅": "tip",
    "⚠️": "warning", "⚠": "warning",
    "❗": "important", "‼️": "important",
    "🚨": "caution",
}


def convert_callouts_to_alerts(body: str) -> str:
    """Rewrite `<callout emoji="…">…</callout>` blocks into `> [!type]` alerts."""

    def inner_to_markdown(inner: str) -> list[str]:
        paragraphs = re.findall(r"<p>(.*?)</p>", inner, re.S) or [inner]
        lines: list[str] = []
        for para in paragraphs:
            text = para.strip()
            text = re.sub(r"</?b>", "**", text)
            text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.S)
            text = re.sub(r"<[^>]+>", "", text)
            if text:
                lines.append(text)
        return lines

    def replace(match: re.Match[str]) -> str:
        kind = _EMOJI_TO_ALERT.get(match.group(1).strip(), "note")
        lines = inner_to_markdown(match.group(2))
        if not lines:
            return ""
        out = [f"> [!{kind}]"]
        out.extend(f"> {line}" if line else ">" for line in lines)
        return "\n".join(out)

    return _CALLOUT_BLOCK_RE.sub(replace, body)


def escape_mdx_text(body: str) -> str:
    """Escape Markdown prose that MDX would otherwise parse as JSX."""

    def close_void_tag(match: re.Match[str]) -> str:
        tag = match.group(1)
        attrs = match.group(2).rstrip()
        if attrs.endswith("/"):
            return match.group(0)
        return f"<{tag}{attrs} />"

    escaped_blocks: list[str] = []
    in_fence = False
    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_fence = not in_fence
            escaped_blocks.append(line)
            continue
        if in_fence:
            escaped_blocks.append(line)
            continue
        if line.strip().startswith("<!--") and line.strip().endswith("-->"):
            continue
        line = re.sub(rf"<({MDX_VOID_TAGS})([^>]*)>", close_void_tag, line)
        line = re.sub(r"<(?=[0-9=%])", "&lt;", line)
        line = line.replace("{", r"\{").replace("}", r"\}")
        escaped_blocks.append(line)
    return "".join(escaped_blocks)


# Canonical-source `register` → (blog category, article type) defaults.
# Kept in sync with SOUL.md's register list; registers not listed here (e.g.
# technical-blog, industry-analysis, agent-ai-essay) fall through to the
# existing heuristics.
_REGISTER_TAXONOMY = {
    "literary-essay": ("Culture & Media", "文化随笔"),
    "cultural-essay": ("Culture & Media", "文化随笔"),
    "personal-essay": ("Culture & Media", "随笔"),
}


def infer_taxonomy(source_meta: dict[str, object], slug: str) -> tuple[str, str | None, list[str]]:
    title = str(source_meta.get("title") or "")
    raw_tags = source_meta.get("tags") or []
    tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else [str(raw_tags)]
    haystack = " ".join([slug, title, *tags]).lower()

    category = "AI Engineering"
    series: str | None = None

    # `register` in the canonical source is a reliable genre signal. Without
    # it, any new non-technical essay falls through to the AI Engineering
    # default below and has to be fixed by hand after every sync.
    register = str(source_meta.get("register") or "").strip().lower()
    if register in _REGISTER_TAXONOMY:
        category = _REGISTER_TAXONOMY[register][0]

    # Token heuristics: specific past articles and topic keywords. These stay
    # last-wins so existing articles re-sync to the same category as before.
    if any(token in haystack for token in ("spacex", "ipo", "narrative", "poniai", "openmontage")):
        category = "AI Frontier"
    if any(token in haystack for token in ("banshengxue", "luolebai", "handanxuebu", "左手指月")):
        category = "Culture & Media"
    if any(token in haystack for token in ("writing", "wechat", "公众号", "ai-dialogue", "common-terms")):
        category = "Writing System"
    if any(token in haystack for token in ("cloudflare", "astro", "vite", "tanstack", "copilotkit", "langchain")):
        category = "Web & AI Tooling"

    # An explicit `category:` in the canonical source always wins.
    declared = str(source_meta.get("category") or "").strip()
    if declared:
        category = declared

    if "claude-code" in haystack or "claude code" in haystack:
        series = "Claude Code Notes"
    elif "codex" in haystack:
        series = "Codex Notes"
    elif "hermes" in haystack:
        series = "Hermes Notes"
    elif "langchain" in haystack:
        series = "LangChain Notes"
    elif "tanstack" in haystack:
        series = "TanStack Notes"
    elif "copilotkit" in haystack:
        series = "CopilotKit Notes"

    return category, series, tags or ["others"]


def build_blog_frontmatter(
    source_meta: dict[str, object],
    body: str,
    source_path: Path,
    args: argparse.Namespace,
    destination_assets_dir: Path,
) -> str:
    title = source_meta.get("title") or first_heading_title(body) or source_path.parent.name
    description = (
        args.description
        or source_meta.get("description")
        or source_meta.get("subtitle")
        # `summary` is the canonical one-liner in origin frontmatter and is what
        # the published posts already use as their description. Without it here
        # a re-sync silently replaces a hand-written summary with the article's
        # opening paragraph.
        or source_meta.get("summary")
        or first_paragraph_excerpt(body)
        or str(title)
    )
    status = str(source_meta.get("status", "")).lower()
    draft = args.draft if args.draft is not None else status in {"draft", "wip"}
    date_value = (
        source_meta.get("pubDatetime")
        or source_meta.get("pubDate")
        or source_meta.get("date")
        or date_from_slug(source_path.parent.name)
    )
    category, series, tags = infer_taxonomy(source_meta, source_path.parent.name)
    register = str(source_meta.get("register") or "").strip().lower()
    default_type = _REGISTER_TAXONOMY.get(register, ("", "技术笔记"))[1]
    article_type = source_meta.get("type") or default_type
    cover = (
        source_meta.get("ogImage")
        or source_meta.get("coverImage")
        or source_meta.get("cover")
    )
    # Gate on source-OR-destination, never on the origin tree alone: covers are
    # gitignored, so a clean checkout is *expected* to be missing them while the
    # blog still holds its own copy. Blanking on a missing local file silently
    # deletes heroImage/ogImage from published posts.
    if cover and not asset_exists_in_source_or_destination(
        source_path.parent, cover, destination_assets_dir
    ):
        cover = ""

    source_ref = display_source_path(source_path)
    lines = [
        "---",
        f"title: {yaml_scalar(title)}",
        f"description: {yaml_scalar(description)}",
        f"pubDatetime: {coerce_pub_datetime(date_value)}",
        "author: \"Erik Lee\"",
        f"draft: {yaml_scalar(draft)}",
        f"category: {yaml_scalar(category)}",
        yaml_optional_string("series", series),
        f"type: {yaml_scalar(article_type)}",
        f"canonicalURL: {yaml_scalar(args.canonical_url)}" if args.canonical_url else "",
        f"ogImage: {normalize_asset_path(cover, source_path.parent.name)}" if cover else "",
        # heroImage — not ogImage — is what the blog's post-list thumbnail and
        # the in-article hero render from (src/pages/posts/index.astro:18 and
        # [...slug].astro:74). ogImage only feeds <meta og:image>. Without this
        # line every synced post shows a text placeholder instead of a thumbnail.
        f"heroImage: {normalize_asset_path(cover, source_path.parent.name)}" if cover else "",
        *yaml_list(tags),
        f"source: {yaml_scalar(source_ref)}",
        "---",
    ]
    return "\n".join(line for line in lines if line != "") + "\n\n"


def display_source_path(source_path: Path) -> str:
    try:
        return source_path.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return source_path.name


def resolve_destination(args: argparse.Namespace, slug: str) -> Path:
    if args.output_dir:
        posts_dir = Path(args.output_dir)
    elif args.blog_root:
        posts_dir = Path(args.blog_root) / "src" / "content" / "posts"
    else:
        raise SystemExit("Provide --blog-root or --output-dir.")
    return posts_dir / f"{slug}.{args.extension}"


def resolve_source_path(source: str) -> Path:
    source_path = Path(source).resolve()
    if source_path.is_file():
        return source_path
    candidate = choose_article_file(source_path)
    if candidate:
        return candidate
    raise SystemExit(f"Source article not found: {source_path}")


def choose_article_file(article_dir: Path) -> Path | None:
    for filename in DEFAULT_ARTICLE_NAMES:
        candidate = article_dir / filename
        if candidate.exists():
            return candidate

    candidates = [
        path
        for path in sorted(article_dir.glob("*.md"))
        if path.stem.lower() not in NON_ARTICLE_STEMS
        and not path.name.startswith("notes-")
        and not path.name.endswith(".en.md")
    ]
    if len(candidates) == 1:
        return candidates[0]

    article_named = [
        path
        for path in candidates
        if "article" in path.stem.lower()
        or "report" in path.stem.lower()
        or "analysis" in path.stem.lower()
    ]
    if len(article_named) == 1:
        return article_named[0]

    return None


_IMAGE_URL_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
_EXTERNAL_URL_RE = re.compile(r"^(https?:|mailto:|data:|#)")


def referenced_asset_names(body: str, meta: dict[str, object]) -> set[str]:
    """Basenames of the assets an article actually references.

    The sync only needs these in the blog repo. Without this filter the whole
    assets/ directory is copied verbatim, which drags generation-time leftovers
    into a public repo: superseded image drafts (hero-cover-v1.png, …), prompt
    files, and per-image metadata JSON.
    """
    names: set[str] = set()
    for url in _IMAGE_URL_RE.findall(body):
        if _EXTERNAL_URL_RE.match(url):
            continue
        names.add(Path(url.removeprefix("./")).name)
    for key in ("cover", "ogImage", "coverImage"):
        value = str(meta.get(key) or "").strip()
        if value and not _EXTERNAL_URL_RE.match(value):
            names.add(Path(value).name)
    return names


def strip_leading_cover_image(body: str, cover: object, source_dir: Path) -> str:
    """Drop a leading body image that is the same file as the frontmatter cover.

    The blog renders the cover as `heroImage` above the body, so keeping the
    identical markdown image at the top of the body renders it twice (the bug
    visible on the lanhua and meta-muse posts). Only strips when the cover
    actually resolves to a local asset, so a broken cover reference can never
    delete the only copy of an image.

    Deliberately stays strict on `source_asset_exists`. Do not switch this to
    `asset_exists_in_source_or_destination`: if the destination has the file but
    the origin does not, stripping would remove the body image while the blog's
    own copy may be the only one left.
    """
    cover_ref = str(cover or "").strip()
    if not cover_ref or _EXTERNAL_URL_RE.match(cover_ref):
        return body
    if not source_asset_exists(source_dir, cover_ref):
        return body
    stripped = body.lstrip("\n")
    match = re.match(r"!\[[^\]]*\]\(([^)\s]+)\)[ \t]*\n+", stripped)
    if not match:
        return body
    if Path(match.group(1).removeprefix("./")).name != Path(cover_ref).name:
        return body
    return stripped[match.end():]


def sync_article(args: argparse.Namespace) -> Path:
    source_path = resolve_source_path(args.source)

    source_text = source_path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(source_text)
    if not args.keep_title_heading:
        body = strip_duplicate_title_heading(body, meta.get("title"))
    body = strip_leading_cover_image(
        body,
        meta.get("ogImage") or meta.get("coverImage") or meta.get("cover"),
        source_path.parent,
    )

    slug = args.slug or source_path.parent.name
    destination = resolve_destination(args, slug).resolve()
    destination_assets_dir = destination.parent / "assets" / slug

    if args.dry_run:
        print(f"Would write: {destination}")
        print(f"Would copy assets: {source_path.parent / 'assets'} -> {destination_assets_dir}")
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = source_path.parent / "assets"
    # Deliberately additive: never rmtree the destination first. Image binaries
    # are gitignored, so an origin assets/ dir restored from git can be missing
    # files the blog still needs — wiping first would delete them from a public
    # repo with no way to recover. Stale leftovers are the lesser evil.
    if assets_dir.exists():
        referenced = referenced_asset_names(body, meta)
        pattern_ignore = shutil.ignore_patterns(
            "*.md",
            "*.mdx",
            "*.mjs",
            "*.js",
            "*.ts",
            "*.html",
            ".gitignore",
            "html-build",
            "package*.json",
        )

        def asset_ignore(dirname: str, names: list[str]) -> set[str]:
            """Skip code/doc files, and any asset the article never references."""
            ignored = set(pattern_ignore(dirname, names))
            for name in names:
                if (Path(dirname) / name).is_file() and name not in referenced:
                    ignored.add(name)
            return ignored

        missing = sorted(n for n in referenced if not (assets_dir / n).exists())
        if missing:
            print(f"[sync] ⚠ 源 assets/ 缺 {len(missing)} 个正文引用的文件，"
                  f"博客侧保留原文件不删: {', '.join(missing[:3])}"
                  f"{' …' if len(missing) > 3 else ''}")

        shutil.copytree(
            assets_dir,
            destination_assets_dir,
            dirs_exist_ok=True,
            ignore=asset_ignore,
        )

    body = rewrite_asset_links(body, slug)
    body = materialize_local_image_refs(body, source_path.parent, destination_assets_dir, slug)
    body = replace_missing_asset_refs(body, source_path.parent, destination_assets_dir, slug)
    body = convert_callouts_to_alerts(body)
    if args.extension == "mdx":
        body = escape_mdx_text(body)
    output = build_blog_frontmatter(meta, body, source_path, args, destination_assets_dir) + body.rstrip() + "\n"
    destination.write_text(output, encoding="utf-8")

    return destination


def iter_origin_articles(origin_dir: Path) -> list[Path]:
    articles: list[Path] = []
    for article_dir in sorted(path for path in origin_dir.iterdir() if path.is_dir()):
        candidate = choose_article_file(article_dir)
        if candidate:
            articles.append(candidate)
        else:
            print(f"Skipping origin directory without a single article file: {article_dir}", file=sys.stderr)
    return articles


def sync_all(args: argparse.Namespace) -> list[Path]:
    origin_dir = Path(args.source).resolve()
    if not origin_dir.is_dir():
        raise SystemExit("--all expects source to be the content/origin directory.")
    destinations: list[Path] = []
    for source_path in iter_origin_articles(origin_dir):
        item_args = argparse.Namespace(**vars(args))
        item_args.source = str(source_path)
        item_args.slug = source_path.parent.name
        destinations.append(sync_article(item_args))
    return destinations


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync content/origin/<slug>/index.md to Erik Lee's Astro blog posts directory.",
    )
    parser.add_argument("source", help="Origin article directory or index.md path.")
    parser.add_argument("--blog-root", help="Astro blog repository root.")
    parser.add_argument("--output-dir", help="Astro blog posts directory, e.g. /blog/src/content/posts.")
    parser.add_argument("--slug", help="Override destination slug. Defaults to source folder name.")
    parser.add_argument("--all", action="store_true", help="Sync every origin article directory under source.")
    parser.add_argument("--extension", choices=["md", "mdx"], default="mdx", help="Destination extension.")
    parser.add_argument("--description", help="Override blog post description.")
    parser.add_argument("--canonical-url", help="Absolute canonical URL for blog frontmatter.")
    parser.add_argument("--draft", dest="draft", action="store_true", default=None, help="Force draft: true.")
    parser.add_argument("--published", dest="draft", action="store_false", help="Force draft: false.")
    parser.add_argument("--keep-title-heading", action="store_true", help="Keep leading H1 that matches title.")
    parser.add_argument("--dry-run", action="store_true", help="Print destination without writing files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    destinations = sync_all(args) if args.all else [sync_article(args)]
    for destination in destinations:
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
