#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "openai>=1.76.0",
#   "pillow>=10.0.0",
# ]
# ///

from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import json
import os
import re
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from openai import OpenAI


def _load_dotenv() -> None:
    """Load .env from the current working directory if it exists and values are not already set."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    # Only load values that aren't already in the environment
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


STYLE_PROFILES = {
    "editorial-atmospheric": {
        "style_text": (
            "contemporary editorial illustration, layered composition, subtle texture, "
            "restrained color palette, atmospheric but concrete, article-friendly visual metaphor, "
            "no text labels, no diagrams, no arrows"
        ),
        "is_artistic": True,
    },
    "flat-tech-infographic": {
        "style_text": (
            "flat technical infographic illustration, clean grouped modules, clear arrows, "
            "soft professional palette, concise bilingual labels, document-friendly composition"
        ),
        "is_artistic": False,
    },
    "flat-illustration": {
        "style_text": (
            "flat illustration, simple geometric forms, concise annotations, soft editorial look"
        ),
        "is_artistic": True,
    },
    "modern-guochao-editorial": {
        "style_text": (
            "modern Chinese editorial illustration with restrained guochao influence, "
            "historical motifs reinterpreted through clean contemporary composition, "
            "rich but not gaudy colors, subtle paper texture, no text labels, no diagrams"
        ),
        "is_artistic": True,
    },
    "cinematic-editorial": {
        "style_text": (
            "cinematic editorial still, dramatic but natural lighting, grounded scene details, "
            "documentary-like framing with an illustrative finish, no text labels, no diagrams"
        ),
        "is_artistic": True,
    },
    "sketchnote": {
        "style_text": (
            "hand-drawn sketchnote style, notebook feel, soft linework, compact explanatory callouts"
        ),
        "is_artistic": True,
    },
    "soft-tech-diagram": {
        "style_text": (
            "soft technical diagram, subtle dashed containers, layered modules, light academic visual language"
        ),
        "is_artistic": False,
    },
    "repo-architecture-clean": {
        "style_text": (
            "clean repository architecture diagram, crisp blocks, restrained decoration, "
            "clear ownership and dependency labels"
        ),
        "is_artistic": False,
    },
    "watercolor-illustration": {
        "style_text": (
            "watercolor painting illustration, soft brushstrokes, muted palette, "
            "atmospheric and evocative, fine art feel, generous negative space, "
            "no text labels, no diagrams, no arrows — pure visual mood"
        ),
        "is_artistic": True,
    },
}

SIZE_PRESETS = {
    # WeChat & blog presets (primary)
    "wechat-cover-hd": "1792x1024",   # WeChat headline cover; auto-crops to 1080x460 (2.35:1)
    "portrait-hd": "1024x1536",       # portrait orientation for mobile-body insets
    "blog-banner": "2048x1152",       # blog hero / desktop banner
    "9:16": "1024x1792",              # full phone portrait
    # Legacy / generic presets
    "doc-hd": "1536x1024",
    "doc-2k": "2048x1152",
    "doc-4k": "3840x2160",
    "cover-hd": "1792x1024",          # legacy alias for wechat-cover-hd
    "3:2": "1536x1024",
    "1:1": "1024x1024",
    "16:9": "1536x1024",
    "auto": "auto",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate article illustrations.")
    parser.add_argument("--brief", help="Short illustration brief.")
    parser.add_argument("--brief-file", help="Path to a UTF-8 text file containing the brief.")
    parser.add_argument("--title", default="article-illustration")
    parser.add_argument("--mode", choices=["text-only", "reference+text"], default="text-only")
    parser.add_argument("--reference-image", action="append", default=[])
    parser.add_argument(
        "--style-profile",
        default="auto",
        choices=["auto", *sorted(STYLE_PROFILES)],
    )
    parser.add_argument("--size", default="auto")
    parser.add_argument(
        "--quality",
        default="auto",
        choices=["auto", "high", "medium", "low"],
    )
    parser.add_argument("--language", default="zh")
    parser.add_argument("--output-dir", default="output/article-illustration")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_brief(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.brief:
        parts.append(args.brief.strip())
    if args.brief_file:
        parts.append(Path(args.brief_file).read_text(encoding="utf-8").strip())
    brief = "\n\n".join(part for part in parts if part)
    if not brief:
        raise SystemExit("Error: provide --brief or --brief-file.")
    return brief


def normalize_reference_images(paths: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"Error: reference image not found: {path}")
        normalized.append(str(path))
    return normalized


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "article-illustration"


def get_api_settings(require_key: bool) -> tuple[str | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if api_key:
        return api_key, base_url
    if not require_key:
        return None, base_url
    if sys.stdin.isatty() and sys.stderr.isatty():
        api_key = getpass.getpass("OPENAI_API_KEY is missing. Enter a temporary key: ").strip()
        if api_key:
            return api_key, base_url
    raise SystemExit(
        "Error: OPENAI_API_KEY is required. Set it in your shell, for example:\n"
        "  export OPENAI_API_KEY='sk-...'\n"
        "  export OPENAI_BASE_URL='https://your-proxy.example/v1'  # optional"
    )


def resolve_model_name(base_url: str | None) -> str:
    if not base_url:
        return "gpt-image-2"
    normalized = base_url.rstrip("/").lower()
    if normalized.startswith("https://api.ofox.io/v1"):
        return "openai/gpt-image-2"
    return "gpt-image-2"


def detect_content_type(brief: str) -> dict[str, str]:
    """Detect content type and return label + category for prompt enrichment.

    Categories: cover, inset, divider, banner, diagram
    """
    lower = brief.lower()

    # WeChat / article covers
    if any(t in lower for t in ("cover", "封面", "cover image")):
        return {"label": "WeChat article cover", "category": "cover"}

    # Divider / separator
    if any(t in lower for t in ("divider", "separator", "分割", "section break")):
        return {"label": "atmospheric divider", "category": "divider"}

    # Blog banners
    if any(t in lower for t in ("banner", "hero", "首页", "头图")):
        return {"label": "blog banner", "category": "banner"}

    # Inset / body illustrations
    if any(t in lower for t in ("inset", "插图", "body image", "配图")):
        return {"label": "body inset illustration", "category": "inset"}

    # Technical diagrams (legacy)
    repo_terms = (
        "repo", "repository", "codebase", "folder structure",
        "directory structure", "module relationship", "module dependency",
        "package structure", "目录", "仓库",
    )
    if any(t in lower for t in repo_terms):
        return {"label": "repo architecture diagram", "category": "diagram"}
    if any(t in lower for t in ("process", "workflow", "步骤", "流程")):
        return {"label": "process diagram", "category": "diagram"}
    if any(t in lower for t in ("knowledge", "card", "指南", "总结", "笔记")):
        return {"label": "knowledge card", "category": "diagram"}
    if any(t in lower for t in ("architecture", "system", "服务", "架构")):
        return {"label": "architecture diagram", "category": "diagram"}

    return {"label": "article illustration", "category": "inset"}


def is_artistic_style(style_profile: str) -> bool:
    return STYLE_PROFILES.get(style_profile, {}).get("is_artistic", False)


def resolve_style_profile(requested: str, brief: str) -> str:
    """Choose a style when --style-profile=auto.

    Auto should keep agents from treating watercolor as the universal literary default.
    It favors a concrete editorial style for essays, while still selecting technical
    profiles for diagrams and engineering notes.
    """
    if requested != "auto":
        return requested

    content_info = detect_content_type(brief)
    category = content_info["category"]
    lower = brief.lower()

    if category == "diagram":
        if any(t in lower for t in ("repo", "repository", "codebase", "目录", "仓库")):
            return "repo-architecture-clean"
        if any(t in lower for t in ("architecture", "system", "架构", "workflow", "process", "流程")):
            return "soft-tech-diagram"
        return "flat-tech-infographic"

    if any(t in brief for t in ("国潮", "古风", "古城", "战国", "赵国", "邯郸", "成语", "礼宴", "文旅", "传统文化")):
        return "modern-guochao-editorial"

    if any(t in brief for t in ("舞台", "现场", "电影", "光影", "夜色", "城市", "街头")):
        return "cinematic-editorial"

    return "editorial-atmospheric"


def build_prompt(
    *,
    brief: str,
    title: str,
    mode: str,
    style_profile: str,
    language: str,
    size_label: str,
    reference_images: list[str],
) -> str:
    style_text = STYLE_PROFILES[style_profile]["style_text"]
    artistic = is_artistic_style(style_profile)
    ref_clause = ""
    if mode == "reference+text" and reference_images:
        ref_clause = (
            "Use the provided reference image or images only for style guidance such as palette, "
            "line quality, spacing, icon treatment, and annotation tone. "
            "Do not copy their literal subject matter. "
            f"Reference count: {len(reference_images)}. "
        )

    if artistic:
        content_info = detect_content_type(brief)
        category_guidance = {
            "cover": (
                "This is a WeChat Official Account headline cover image (公众号头条封面). "
                "Compose for a 2.35:1 ultra-wide crop (1080x460). "
                "Keep key subjects centered or in the bottom third — top area will be cropped. "
                "Design for readability as a small thumbnail in WeChat's subscription feed. "
                "Title text will be overlaid by the editor, so leave ample negative space."
            ),
            "inset": (
                "This is a body illustration inside a WeChat article read on mobile phones (~390px wide). "
                "Compose for narrow-width readability. Use generous negative space."
            ),
            "divider": (
                "This is a narrow atmospheric divider between article sections. "
                "Keep the composition simple and horizontal. It should feel like a visual breath."
            ),
            "banner": (
                "This is a blog hero banner for desktop reading. "
                "Leave upper area clear for overlaid title and subtitle text."
            ),
        }
        guidance = category_guidance.get(content_info.get("category", ""), "")

        return (
            f"Create an illustration titled '{title}'. "
            f"Style: {style_text}. "
            "This is for an article or essay — not a technical document. "
            "Do NOT add any diagrams, arrows, labels, callouts, or text. "
            "Focus on a concrete visual idea with atmosphere, restraint, and editorial clarity. "
            f"{guidance} "
            f"Language/region: {language}. "
            f"Target aspect ratio: {size_label}. "
            f"Mode: {mode}. "
            f"{ref_clause}"
            f"Brief:\n{brief}"
        ).strip()

    content_info = detect_content_type(brief)
    diagram_type = content_info["label"]
    return (
        f"Create a polished article illustration titled '{title}'. "
        f"Diagram type: {diagram_type}. "
        f"Use a {style_text}. "
        "Make it suitable for insertion into engineering notes or a design document. "
        "Prefer a clear information hierarchy with section titles, concise Chinese/English labels, "
        "short notes, arrows, grouped modules, and strong readability. "
        "Avoid dense paragraph blocks. "
        f"Language mode: {language}. "
        f"Target aspect ratio preset: {size_label}. "
        f"Mode: {mode}. "
        f"{ref_clause}"
        f"Content brief:\n{brief}"
    ).strip()


def make_output_paths(output_dir: str, title: str) -> tuple[Path, Path]:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    stem = f"{ts}-{slugify(title)}"
    output_root = Path(output_dir).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    # Avoid collision when two calls happen within the same second
    counter = 0
    while True:
        suffix = f"-{counter}" if counter else ""
        png_path = output_root / f"{stem}{suffix}.png"
        json_path = output_root / f"{stem}{suffix}.json"
        if not png_path.exists() and not json_path.exists():
            return png_path, json_path
        counter += 1


def metadata_dict(
    *,
    args: argparse.Namespace,
    brief: str,
    prompt: str,
    reference_images: list[str],
    image_path: Path | None,
    model_name: str,
) -> dict[str, Any]:
    content_info = detect_content_type(brief)
    return {
        "title": args.title,
        "brief": brief,
        "content_type": content_info["label"],
        "content_category": content_info["category"],
        "mode": args.mode,
        "style_profile": args.style_profile,
        "resolved_style_profile": args.resolved_style_profile,
        "size": args.size,
        "resolved_size": SIZE_PRESETS.get(args.size, args.size),
        "quality": args.quality,
        "language": args.language,
        "model": model_name,
        "reference_images": reference_images,
        "prompt": prompt,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "output_files": [str(image_path)] if image_path else [],
        "crop_hint": "1080x460 (2.35:1)" if SIZE_PRESETS.get(args.size) == "1792x1024" and args.size in ("wechat-cover-hd", "cover-hd") else None,
        "dry_run": args.dry_run,
    }


def crop_cover_image(image_path: Path, size_label: str) -> Path | None:
    """Post-generate crop for WeChat cover presets (1792x1024 -> 1080x460, 2.35:1)."""
    if size_label not in ("wechat-cover-hd", "cover-hd"):
        return None
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow not available. Run via `uv run` which auto-installs PEP 723 deps.")
        print("Cover image NOT cropped — use at 1792x1024 or crop manually.")
        return None

    img = Image.open(image_path)
    target_w, target_h = 1080, 460

    if img.width < target_w or img.height < target_h:
        print(f"Warning: source image {img.width}x{img.height} too small for {target_w}x{target_h} crop")
        return None

    # Center-crop to 2.35:1, then resize
    crop_h = int(img.width / 2.35)
    top = (img.height - crop_h) // 2
    cropped = img.crop((0, top, img.width, top + crop_h))
    resized = cropped.resize((target_w, target_h), Image.LANCZOS)

    crop_path = image_path.with_stem(image_path.stem + "-cropped")
    resized.save(crop_path, "PNG")
    print(f"Cover cropped to 2.35:1: {image_path.name} -> {crop_path.name} ({target_w}x{target_h})")
    return crop_path


def build_client(api_key: str | None, base_url: str | None) -> OpenAI:
    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def generate_text_only(
    client: OpenAI,
    model_name: str,
    prompt: str,
    size: str,
    quality: str,
) -> bytes:
    response = client.images.generate(
        model=model_name,
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
    )
    data = response.data[0]
    if data.b64_json:
        return base64.b64decode(data.b64_json)
    if data.url:
        import urllib.request
        import tempfile
        return urllib.request.urlopen(data.url).read()
    raise RuntimeError("Image generation returned neither b64_json nor url")


def generate_from_reference(
    client: OpenAI,
    model_name: str,
    prompt: str,
    size: str,
    reference_images: list[str],
    quality: str,
) -> bytes:
    with ExitStack() as stack:
        image_files = [stack.enter_context(open(path, "rb")) for path in reference_images]
        response = client.images.edit(
            model=model_name,
            image=image_files,
            prompt=prompt,
            size=size,
            quality=quality,
        )
    return base64.b64decode(response.data[0].b64_json)


def main() -> int:
    _load_dotenv()
    args = parse_args()
    brief = load_brief(args)
    args.resolved_style_profile = resolve_style_profile(args.style_profile, brief)
    reference_images = normalize_reference_images(args.reference_image)
    if args.mode == "reference+text" and not reference_images:
        raise SystemExit("Error: reference+text mode requires at least one --reference-image.")

    resolved_size = SIZE_PRESETS.get(args.size, args.size)
    _, preview_base_url = get_api_settings(require_key=False)
    model_name = resolve_model_name(preview_base_url)
    prompt = build_prompt(
        brief=brief,
        title=args.title,
        mode=args.mode,
        style_profile=args.resolved_style_profile,
        language=args.language,
        size_label=args.size,
        reference_images=reference_images,
    )
    image_path, meta_path = make_output_paths(args.output_dir, args.title)

    if args.dry_run:
        metadata = metadata_dict(
            args=args,
            brief=brief,
            prompt=prompt,
            reference_images=reference_images,
            image_path=None,
            model_name=model_name,
        )
        meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Mode: dry-run")
        print(f"Style: {args.resolved_style_profile} (requested: {args.style_profile})")
        print(f"Model: {model_name}")
        print(f"Prompt saved to: {meta_path}")
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return 0

    api_key, base_url = get_api_settings(require_key=True)
    model_name = resolve_model_name(base_url)
    client = build_client(api_key, base_url)

    if args.mode == "reference+text":
        image_bytes = generate_from_reference(
            client,
            model_name,
            prompt,
            resolved_size,
            reference_images,
            args.quality,
        )
    else:
        image_bytes = generate_text_only(
            client,
            model_name,
            prompt,
            resolved_size,
            args.quality,
        )

    image_path.write_bytes(image_bytes)

    # Post-generation: auto-crop for WeChat covers
    crop_path = crop_cover_image(image_path, args.size)
    if crop_path:
        image_path = crop_path

    metadata = metadata_dict(
        args=args,
        brief=brief,
        prompt=prompt,
        reference_images=reference_images,
        image_path=image_path,
        model_name=model_name,
    )
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Mode: generate")
    print(f"Style: {args.resolved_style_profile} (requested: {args.style_profile})")
    print(f"Image: {image_path}")
    print(f"Metadata: {meta_path}")
    print(f"Markdown: ![{args.title}]({image_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
