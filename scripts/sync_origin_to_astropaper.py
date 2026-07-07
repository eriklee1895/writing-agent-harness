#!/usr/bin/env python3
"""Sync canonical origin articles into an AstroPaper posts directory.

This is intentionally a one-way adapter: content/origin remains the source of
truth, and the AstroPaper repo receives rendered publishing copies.
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
    text = str(value or "").strip().removeprefix("./")
    if not text.startswith("assets/"):
        return True
    return (source_dir / text).exists()


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


def infer_taxonomy(source_meta: dict[str, object], slug: str) -> tuple[str, str | None, list[str]]:
    title = str(source_meta.get("title") or "")
    raw_tags = source_meta.get("tags") or []
    tags = [str(tag) for tag in raw_tags] if isinstance(raw_tags, list) else [str(raw_tags)]
    haystack = " ".join([slug, title, *tags]).lower()

    category = "AI Engineering"
    series: str | None = None

    if any(token in haystack for token in ("spacex", "ipo", "narrative", "poniai", "openmontage")):
        category = "AI Frontier"
    if any(token in haystack for token in ("banshengxue", "luolebai", "handanxuebu", "左手指月")):
        category = "Culture & Media"
    if any(token in haystack for token in ("writing", "wechat", "公众号", "ai-dialogue", "common-terms")):
        category = "Writing System"
    if any(token in haystack for token in ("cloudflare", "astro", "vite", "tanstack", "copilotkit", "langchain")):
        category = "Web & AI Tooling"

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


def build_astropaper_frontmatter(
    source_meta: dict[str, object],
    body: str,
    source_path: Path,
    args: argparse.Namespace,
) -> str:
    title = source_meta.get("title") or first_heading_title(body) or source_path.parent.name
    description = (
        args.description
        or source_meta.get("description")
        or source_meta.get("subtitle")
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
    cover = (
        source_meta.get("ogImage")
        or source_meta.get("coverImage")
        or source_meta.get("cover")
    )
    if cover and not source_asset_exists(source_path.parent, cover):
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
        f"canonicalURL: {yaml_scalar(args.canonical_url)}" if args.canonical_url else "",
        f"ogImage: {normalize_asset_path(cover, source_path.parent.name)}" if cover else "",
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


def sync_article(args: argparse.Namespace) -> Path:
    source_path = resolve_source_path(args.source)

    source_text = source_path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(source_text)
    if not args.keep_title_heading:
        body = strip_duplicate_title_heading(body, meta.get("title"))

    slug = args.slug or source_path.parent.name
    destination = resolve_destination(args, slug).resolve()
    destination_assets_dir = destination.parent / "assets" / slug

    if args.dry_run:
        print(f"Would write: {destination}")
        print(f"Would copy assets: {source_path.parent / 'assets'} -> {destination_assets_dir}")
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = source_path.parent / "assets"
    if destination_assets_dir.exists():
        shutil.rmtree(destination_assets_dir)
    if assets_dir.exists():
        shutil.copytree(
            assets_dir,
            destination_assets_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                "*.md",
                "*.mdx",
                "*.mjs",
                "*.js",
                "*.ts",
                "*.html",
                ".gitignore",
                "html-build",
                "package*.json",
            ),
        )

    body = rewrite_asset_links(body, slug)
    body = materialize_local_image_refs(body, source_path.parent, destination_assets_dir, slug)
    body = replace_missing_asset_refs(body, source_path.parent, destination_assets_dir, slug)
    if args.extension == "mdx":
        body = escape_mdx_text(body)
    output = build_astropaper_frontmatter(meta, body, source_path, args) + body.rstrip() + "\n"
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
        description="Sync content/origin/<slug>/index.md to an AstroPaper posts directory.",
    )
    parser.add_argument("source", help="Origin article directory or index.md path.")
    parser.add_argument("--blog-root", help="AstroPaper repository root.")
    parser.add_argument("--output-dir", help="AstroPaper posts directory, e.g. /blog/src/content/posts.")
    parser.add_argument("--slug", help="Override destination slug. Defaults to source folder name.")
    parser.add_argument("--all", action="store_true", help="Sync every origin article directory under source.")
    parser.add_argument("--extension", choices=["md", "mdx"], default="mdx", help="Destination extension.")
    parser.add_argument("--description", help="Override AstroPaper description.")
    parser.add_argument("--canonical-url", help="Absolute canonical URL for AstroPaper frontmatter.")
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
