#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pillow>=10",
# ]
# ///
"""Derive channel-ready cover images from one approved visual master."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageOps


def parse_size(value: str) -> tuple[int, int]:
    try:
        width, height = value.lower().split("x", 1)
        size = (int(width), int(height))
    except (ValueError, TypeError) as exc:
        raise ValueError("size must use WIDTHxHEIGHT, for example 1728x736") from exc
    if min(size) <= 0:
        raise ValueError("size dimensions must be positive")
    return size


def validate_focus(value: float, name: str) -> float:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


def output_image(image: Image.Image, output: Path) -> None:
    suffix = output.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".webp"}:
        image.save(output, quality=92)
    elif suffix == ".png":
        image.save(output)
    else:
        raise ValueError("output must be a .png, .jpg, .jpeg or .webp file")


def update_manifest(
    manifest_path: Path,
    *,
    source: Path,
    output: Path,
    result: dict,
    role: str,
    channel: str,
) -> None:
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"images": []}
    images = manifest.setdefault("images", [])
    existing = next((item for item in images if item.get("file") == output.name), {})
    entry = {
        **existing,
        "file": output.name,
        "status": "candidate",
        "role": role,
        "channel": channel,
        "derived_from": source.name,
        "derivation": result["derivation"],
        "dimensions": result["dimensions"],
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "visual_review": "pending",
    }
    images[:] = [item for item in images if item.get("file") != output.name]
    images.append(entry)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def derive_cover(
    source: Path | str,
    output: Path | str,
    size: tuple[int, int],
    *,
    mode: str = "crop",
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    background: str = "#ffffff",
    role: str = "cover",
    channel: str = "blog",
    manifest_path: Path | str | None = None,
    force: bool = False,
) -> dict:
    source = Path(source)
    output = Path(output)
    target_width, target_height = size
    if min(target_width, target_height) <= 0:
        raise ValueError("size dimensions must be positive")
    if source.resolve() == output.resolve():
        raise ValueError("refusing to overwrite the visual master")
    if output.is_symlink():
        raise ValueError("refusing to write through a symlink output")
    if output.exists() and not force:
        raise FileExistsError(f"output exists; pass force=True to replace it: {output}")
    if mode not in {"crop", "pad"}:
        raise ValueError("mode must be crop or pad")
    validate_focus(focus_x, "focus_x")
    validate_focus(focus_y, "focus_y")
    background_rgb = ImageColor.getrgb(background)

    with Image.open(source) as opened:
        source_image = ImageOps.exif_transpose(opened).convert("RGBA")
    source_width, source_height = source_image.size
    if mode == "crop":
        scale = max(target_width / source_width, target_height / source_height)
    else:
        scale = min(target_width / source_width, target_height / source_height)
    if scale > 1:
        raise ValueError("refusing to upscale the source image")

    canvas = Image.new("RGBA", (target_width, target_height), (*background_rgb, 255))
    derivation = {
        "operation": mode,
        "from": [source_width, source_height],
        "to": [target_width, target_height],
        "focus": [focus_x, focus_y],
    }

    if mode == "crop":
        target_ratio = target_width / target_height
        source_ratio = source_width / source_height
        if source_ratio > target_ratio:
            crop_width = round(source_height * target_ratio)
            crop_height = source_height
        else:
            crop_width = source_width
            crop_height = round(source_width / target_ratio)
        left = round(focus_x * (source_width - crop_width))
        top = round(focus_y * (source_height - crop_height))
        crop_box = (left, top, left + crop_width, top + crop_height)
        resized = source_image.crop(crop_box).resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
        canvas.paste(resized, (0, 0), resized)
        derivation["crop"] = list(crop_box)
    else:
        resized_size = (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )
        resized = source_image.resize(resized_size, Image.Resampling.LANCZOS)
        left = (target_width - resized.width) // 2
        top = (target_height - resized.height) // 2
        canvas.paste(resized, (left, top), resized)
        derivation["padding"] = [left, top]

    output.parent.mkdir(parents=True, exist_ok=True)
    output_image(canvas.convert("RGB"), output)
    result = {
        "output": str(output),
        "dimensions": [target_width, target_height],
        "derivation": derivation,
    }
    if manifest_path is not None:
        update_manifest(
            Path(manifest_path),
            source=source,
            output=output,
            result=result,
            role=role,
            channel=channel,
        )
        result["manifest"] = str(manifest_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crop or pad an approved cover master into a channel-ready derivative.",
        epilog="Visual review stays pending until the actual channel preview is checked.",
    )
    parser.add_argument("--input", required=True, help="Approved source image")
    parser.add_argument("--output", required=True, help="New derivative path")
    parser.add_argument("--size", required=True, help="Target size, e.g. 1728x736")
    parser.add_argument("--mode", choices=("crop", "pad"), default="crop")
    parser.add_argument("--focus-x", type=float, default=0.5)
    parser.add_argument("--focus-y", type=float, default=0.5)
    parser.add_argument("--background", default="#ffffff")
    parser.add_argument("--role", default="cover")
    parser.add_argument("--channel", default="blog")
    parser.add_argument("--manifest", help="Optional manifest.json to create or update")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing derivative")
    parser.add_argument("--json", action="store_true", help="Emit structured result JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = derive_cover(
            args.input,
            args.output,
            parse_size(args.size),
            mode=args.mode,
            focus_x=args.focus_x,
            focus_y=args.focus_y,
            background=args.background,
            role=args.role,
            channel=args.channel,
            manifest_path=args.manifest,
            force=args.force,
        )
    except (OSError, ValueError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Created {result['output']} ({'x'.join(map(str, result['dimensions']))}); visual review pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
