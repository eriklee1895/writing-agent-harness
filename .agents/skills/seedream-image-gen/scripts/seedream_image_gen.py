#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27.0",
#   "pillow>=10.0.0",
# ]
# ///
"""Generate, edit, outpaint, and batch-generate images with Seedream 5.0 Pro (default) / 5.0 Lite
via the Volcengine Ark API.

Subcommands:
  generate         Create a new image from a text prompt (default: Pro / 2K / b64_json).
  edit             Modify an image — supports marker-based region edits (red-rect protocol),
                   reference-based style transfer, character consistency, and outpainting.
  generate-batch   Run many generation jobs from a JSONL file.
  list-models      Print the known model table and exit.

Pro is the default model because it ships SOTA Chinese/English text rendering and a
powerful marker-based region-editing workflow (draw a colored rectangle on the reference,
describe the change in natural language, the model replaces that region and removes the
marker). Text-in-image and pixel-localised edits are the headline features.

API docs:
  Seedream 5.0 Pro: https://www.volcengine.com/docs/82379/1824121
  API reference:   https://www.volcengine.com/docs/82379/1541523

Examples live in SKILL.md.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import getpass
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

import httpx
from PIL import Image, ImageDraw


# ---------------------------------------------------------------------------
# Model registry — add models here; everything else (validation, body shaping)
# derives from the capability dict.
# ---------------------------------------------------------------------------

MODEL_PRO = "doubao-seedream-5-0-pro-260628"
MODEL_LITE = "doubao-seedream-5-0-260128"
MODEL_PRO_ALIASES = {"pro", "seedream-pro", "5-pro", "seedream-5-pro", "doubao-seedream-5-0-pro"}
MODEL_LITE_ALIASES = {"lite", "seedream-lite", "5-lite", "seedream-5-lite", "doubao-seedream-5-0",
                     "doubao-seedream-5-0-lite"}

# Capability shape:
#   aliases            set of shorthand names accepted on --model
#   label              human-readable label for list-models
#   size_strings       set of allowed preset sizes (e.g. "2K")
#   pixel_min/max      inclusive total-pixel bounds for WxH sizes
#   aspect_max         max long:short ratio (16 = both landscape and portrait up to 16:1)
#   default_size       default --size when user doesn't pass one
#   max_refs           max reference images in the `image` field
#   supports_web_search  does the model accept tools:[{type:web_search}]?
#   supports_sequential does it accept sequential_image_generation?
#   supports_negative_prompt does it accept negative_prompt? (undocumented but accepted by Pro)
#   optimize_modes     allowed values for optimize_prompt_options.mode
#   response_format_default "url" or "b64_json" — Pro defaults to b64_json to skip a second hop
#   price_per_image    rough ¥/image for the default size bucket; printed by list-models
#   notes              human notes (limitations)

MODELS: dict[str, dict[str, Any]] = {
    MODEL_PRO: {
        "aliases": MODEL_PRO_ALIASES,
        "label": "Seedream 5.0 Pro (2026-06-28 build)",
        "size_strings": {"1K", "2K"},
        "pixel_min": 921_600,          # 960×960 = 0.9MP; doc says ~0.9MP floor; 1024² OK
        "pixel_max": 4_194_304,        # 2048×2048 = 4MP
        "aspect_max": 16,
        "default_size": "2K",
        "max_refs": 10,
        "supports_web_search": False,
        "supports_sequential": False,
        "supports_negative_prompt": True,
        "optimize_modes": {"standard"},
        "response_format_default": "b64_json",
        "price_per_image": "≤2.36MP ¥0.30 / >2.36MP ¥0.60 (extra input image ¥0.02)",
        "notes": "Headline features: strong Chinese+English text rendering; marker-based region editing. "
                 "No web_search, no sequential gen, no stream. Size preset stops at 2K (no 3K/4K). "
                 "RPM ≈ 500.",
    },
    MODEL_LITE: {
        "aliases": MODEL_LITE_ALIASES,
        "label": "Seedream 5.0 Lite (2026-01-28 build)",
        "size_strings": {"2K", "3K", "4K"},
        "pixel_min": 3_686_400,        # 2560×1440 ≈ 3.69MP — hard floor enforced server-side
        "pixel_max": 16_777_216,       # 4096×4096 = 16MP
        "aspect_max": 16,
        "default_size": "2K",
        "max_refs": 14,
        "supports_web_search": True,
        "supports_sequential": True,
        "supports_negative_prompt": False,
        "optimize_modes": {"standard", "fast"},
        "response_format_default": "url",
        "price_per_image": "¥0.22/张 (2K tier)",
        "notes": "Fast sketch/iteration workhorse. Text rendering weaker than Pro (avoid text-heavy "
                 "prompts). Supports web_search and sequential group generation. Pixel floor blocks "
                 "1024² / 1792×1024 WeChat headers (use Pro for those).",
    },
}

DEFAULT_MODEL = MODEL_PRO
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_OUTPUT_DIR = "output/seedream-image-gen"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_TIMEOUT = 300
DEFAULT_CONCURRENCY = 3
DEFAULT_MAX_N = 4
MAX_RETRIES = 8
RETRY_BACKOFF = (2.0, 4.0, 8.0, 16.0, 30.0, 30.0, 30.0, 30.0)
MAX_REFERENCE_BYTES = 30 * 1024 * 1024
MAX_PROMPT_CHARS = 6_000
ALLOWED_OUTPUT_FORMATS = ("png", "jpeg", "jpg")

# Pro default negative prompt — gentle quality guard. User can override with
# --negative-prompt "" (disable) or --negative-prompt "..." (replace).
PRO_DEFAULT_NEGATIVE = "模糊, 低质量, 水印, 变形, 多余肢体"

# Automatic marker-cleanup suffix appended after the user's edit prompt (unless
# --no-marker-cleanup-prompt is passed). Selected by prompt language heuristic.
MARKER_CLEANUP_ZH = "图中彩色方框/圆圈/涂写是我手工标出的编辑区域标记，请严格按上面的描述修改标记区域内的内容，标记区域之外的像素尽量保持不变，完成后清除所有彩色标记线条与填充。"
MARKER_CLEANUP_EN = "The colored rectangles/circles/scribbles in the image are edit markers I drew by hand. Apply the change described above strictly inside the marked regions, keep pixels outside the markers unchanged, and remove all colored marks once done."

# Outpaint auto-prompt suffix (Chinese-first, since Pro prefers Chinese prompts).
OUTPAINT_FILL_ZH = "画布中央是原图片，请自然延伸填充四周的空白区域，使整张图变成一张完整的{aspect_word}图片，延续原有的风格、光照、色调与材质，不要让中心与新填充区域有可见接缝。"
OUTPAINT_FILL_EN = "The center of this canvas is the original image. Naturally extend and fill the surrounding blank areas to make one complete {aspect_word} image, matching the original style, lighting, palette and materials. No visible seam between center and extended regions."


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _load_dotenv() -> None:
    """Load .env from cwd, only setting keys not already in the environment."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
            val = val[1:-1]
        if key and key not in os.environ and val:
            os.environ[key] = val


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _info(message: str) -> None:
    print(message, file=sys.stderr)


def _slugify(value: str, max_len: int = 60) -> str:
    """Turn a prompt snippet into a safe filename component."""
    value = value.strip().lower()
    value = re.sub(r"[^\w一-鿿]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:max_len] if value else "image"


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _looks_chinese(text: str) -> bool:
    """Rough CJK-detection for choosing between zh/en cleanup prompts."""
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return cjk >= 2


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------


def _resolve_model(model_arg: str) -> tuple[str, dict[str, Any]]:
    """Map user-supplied --model (alias or full id) to (canonical_id, capabilities)."""
    if not model_arg:
        return DEFAULT_MODEL, MODELS[DEFAULT_MODEL]

    # Exact id match
    if model_arg in MODELS:
        return model_arg, MODELS[model_arg]

    # Alias match
    needle = model_arg.lower().strip()
    for mid, caps in MODELS.items():
        if needle in caps["aliases"] or needle == mid.lower():
            return mid, caps

    # Pass through unknown model id (user might be using a fresh dated version we
    # haven't registered) — apply Pro defaults but warn.
    _warn(
        f"Unknown model id '{model_arg}'. Using Pro-capability defaults; "
        f"if this is a newer dated Pro build, things should work. Pass the full id "
        f"silently if you know what you're doing."
    )
    return model_arg, MODELS[DEFAULT_MODEL]


def _model_is_pro(model_id: str) -> bool:
    return model_id == MODEL_PRO or model_id in MODELS.get(MODEL_PRO, {}).get("aliases", set())


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _get_api_settings() -> tuple[str, str]:
    """Return (api_key, base_url)."""
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL") or os.getenv("MODEL_IMAGE_API_BASE") or DEFAULT_BASE_URL

    if not api_key:
        if sys.stdin.isatty() and sys.stdout.isatty():
            try:
                api_key = getpass.getpass(
                    "ARK_API_KEY is missing. Enter your Volcengine Ark API key: "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                api_key = None
        if not api_key:
            _die(
                "ARK_API_KEY is required. Set it in your shell or .env, for example:\n"
                "  export ARK_API_KEY='your-key-here'\n"
                "  Get your key at: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey"
            )

    return api_key, base_url.rstrip("/")


# ---------------------------------------------------------------------------
# Size parsing & model-aware validation
# ---------------------------------------------------------------------------


_SIZE_STRING_PIXELS: dict[str, int] = {
    # Resolutions here are nominal buckets — the server picks the exact pixel
    # dimensions. We only need total pixels for client-side range validation.
    "1K": 1_048_576,   # ~1MP, 1024²
    "2K": 4_194_304,   # ~4MP, 2048²
    "3K": 9_437_184,   # ~9MP, 3072²
    "4K": 16_777_216,  # 16MP, 4096²
}


def _apply_size_shortcuts(
    size: Optional[str],
    wechat_header: bool,
    square: bool,
    wide: bool,
    portrait: bool,
    landscape: bool,
    caps: dict[str, Any],
) -> str:
    """Translate convenience flags into size strings; last explicit wins.
    Model-aware so --square and --wide produce valid sizes for both models.
    """
    # Wide/header shortcuts (1792x1024, Pro only due to pixel floor on Lite)
    if wechat_header or wide:
        return "1792x1024"
    if square:
        # Pro allows 1024² (under its 4MP cap); Lite has 3.69MP floor → 2048²
        return "1024x1024" if "1K" in caps["size_strings"] else "2048x2048"
    if portrait:
        # 3:4 vertical — model-aware pixel sizing
        # Pro: 1536x2048 = 3.15MP (fits 0.9-4MP); Lite: 2048x2732 = 5.59MP (over 3.69MP floor)
        return "1536x2048" if "1K" in caps["size_strings"] else "2048x2732"
    if landscape:
        # 16:9 horizontal — model-aware pixel sizing
        # Pro: 2048x1152 = 2.36MP (fits 0.9-4MP); Lite: 2732x1536 = 4.20MP (over 3.69MP floor)
        return "2048x1152" if "1K" in caps["size_strings"] else "2732x1536"
    return size or caps.get("default_size", "2K")


def _validate_size(size: str, caps: dict[str, Any], model_id: str) -> tuple[int, int]:
    """Validate --size against model capabilities. Returns (width, height) for WxH sizes,
    or (0, 0) for preset strings (the server resolves those)."""
    size_upper = size.upper()
    if size_upper in caps["size_strings"]:
        return (0, 0)  # preset, server resolves

    # Common shortcuts
    if size_upper == "1K" and size_upper not in caps["size_strings"]:
        _die(
            f"Size '1K' is not supported by model {model_id}. "
            f"Allowed presets: {sorted(caps['size_strings'])}. "
            f"Use an explicit WxH (e.g. 2560x1440) or pick a larger preset."
        )
    if size_upper in {"3K", "4K"} and size_upper not in caps["size_strings"]:
        _die(
            f"Size '{size_upper}' is not supported by model {model_id}. "
            f"Pro tops out at 2K (~4MP pixel cap). Allowed presets: {sorted(caps['size_strings'])}."
        )

    m = re.fullmatch(r"(\d{3,5})x(\d{3,5})", size)
    if not m:
        _die(
            f"Invalid size '{size}'. Use '1K'/'2K'/'3K'/'4K' (subject to model), or WIDTHxHEIGHT "
            f"(e.g. '1024x1024', '1792x1024', '2560x1440')."
        )

    w, h = int(m.group(1)), int(m.group(2))
    total = w * h
    aspect = max(w, h) / min(w, h)

    if total < caps["pixel_min"]:
        _die(
            f"Size {size}: {total:,} pixels is below the {caps['pixel_min']:,} pixel floor "
            f"for {model_id}. {caps.get('size_floor_hint', '')}"
        )
    if total > caps["pixel_max"]:
        _die(
            f"Size {size}: {total:,} pixels exceeds the {caps['pixel_max']:,} pixel cap "
            f"for {model_id}."
        )
    if aspect > caps["aspect_max"]:
        _die(f"Size {size}: aspect ratio {aspect:.1f}:1 exceeds maximum {caps['aspect_max']}:1.")

    return (w, h)


# ---------------------------------------------------------------------------
# Reference image handling (encoding + marker annotation + outpaint padding)
# ---------------------------------------------------------------------------


def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def _encode_local_image(path: Path) -> str:
    """Base64-encode a local image file as data URL."""
    if not path.is_file():
        _die(f"Reference image not found: {path}")

    size = path.stat().st_size
    if size > MAX_REFERENCE_BYTES:
        _warn(f"Reference image exceeds 30MB limit: {path} ({size:,} bytes)")

    ext = path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


def _encode_reference(path_or_url: str) -> str:
    if _is_url(path_or_url):
        return path_or_url
    p = Path(path_or_url).expanduser().resolve()
    return _encode_local_image(p)


def _resolve_reference_images(paths: list[str]) -> list[str]:
    return [_encode_reference(p) for p in paths]


# ---- Parsing marker rect strings ------------------------------------------------

_RECT_PERCENT = re.compile(r"^\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*,\s*(\d+(?:\.\d+)?)%\s*$")
_RECT_PIXEL = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*$")


def _parse_marker_rect(spec: str) -> tuple[float, float, float, float, bool]:
    """Parse an --marker-rect spec. Returns (x, y, w, h, is_percent).
    Coordinates are left/top offsets + width/height, consistent with Pillow and
    most graphics tools. Percent values are relative to image dimensions.
    """
    spec = spec.strip()
    mp = _RECT_PERCENT.match(spec)
    if mp:
        return (float(mp.group(1)), float(mp.group(2)), float(mp.group(3)), float(mp.group(4)), True)
    mpx = _RECT_PIXEL.match(spec)
    if mpx:
        return (float(mpx.group(1)), float(mpx.group(2)), float(mpx.group(3)), float(mpx.group(4)), False)
    _die(
        f"Invalid marker rect '{spec}'. Use X,Y,W,H in pixels (e.g. 100,200,800,300) "
        f"or percent (e.g. 10%,20%,60%,15%)."
    )
    return (0, 0, 0, 0, False)  # unreachable


def _parse_color(spec: str) -> tuple[int, int, int]:
    """Parse #RRGGBB (with or without leading #) into (r,g,b)."""
    s = spec.strip().lstrip("#")
    if len(s) != 6:
        _die(f"Invalid marker color '{spec}'. Use #RRGGBB (e.g. #ff0000).")
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        _die(f"Invalid marker color '{spec}'. Use #RRGGBB (e.g. #ff0000).")
        return (0, 0, 0)


def _apply_markers(src_path: Path, rects: list[tuple[float, float, float, float, bool]],
                   color: tuple[int, int, int], fill_alpha: int, stroke_width: int) -> bytes:
    """Draw semi-transparent rectangles on a copy of the source image and return
    the annotated image as PNG bytes.
    """
    img = Image.open(src_path).convert("RGBA")
    W, H = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    fill_rgba = (*color, fill_alpha)
    outline_rgb = color

    for (x, y, w, h, is_percent) in rects:
        if is_percent:
            x_px = int(round(x / 100.0 * W))
            y_px = int(round(y / 100.0 * H))
            w_px = int(round(w / 100.0 * W))
            h_px = int(round(h / 100.0 * H))
        else:
            x_px, y_px, w_px, h_px = int(x), int(y), int(w), int(h)

        box = [x_px, y_px, x_px + w_px, y_px + h_px]
        draw.rectangle(box, fill=fill_rgba, outline=outline_rgb, width=stroke_width)

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    buf = _BytesIO()
    combined.save(buf, format="PNG")
    return buf.getvalue()


# Outpaint directions → (left, top, right, bottom) pixel paddings.
_OUTPAINT_DIRS = {"left", "right", "top", "bottom", "up", "down", "l", "r", "t", "b"}


def _parse_outpaint(spec: str) -> tuple[str, int]:
    if ":" not in spec:
        _die(f"Invalid --outpaint '{spec}'. Use direction:pixels (e.g. left:400, right:400).")
    d, px = spec.split(":", 1)
    d = d.strip().lower()
    if d not in _OUTPAINT_DIRS:
        _die(f"Invalid outpaint direction '{d}'. Use left/right/top/bottom (or l/r/t/b).")
    try:
        n = int(px)
    except ValueError:
        _die(f"Invalid pixel count '{px}' in --outpaint {spec}.")
    if n <= 0 or n > 8192:
        _die(f"Outpaint pixel count out of range (1-8192): {n}")
    # canonicalize
    if d == "up": d = "top"
    if d == "down": d = "bottom"
    if d == "l": d = "left"
    if d == "r": d = "right"
    if d == "t": d = "top"
    if d == "b": d = "bottom"
    return (d, n)


def _apply_outpaint(src_path: Path, paddings: dict[str, int]) -> tuple[bytes, str, tuple[int, int]]:
    """Create a larger canvas, paste the source in the center (offset per paddings),
    fill the new area with a neutral color sampled from the image edge average,
    return PNG bytes + an aspect-word hint for the auto-prompt.
    """
    img = Image.open(src_path).convert("RGB")
    W, H = img.size
    pl = paddings.get("left", 0)
    pr = paddings.get("right", 0)
    pt = paddings.get("top", 0)
    pb = paddings.get("bottom", 0)

    new_W = W + pl + pr
    new_H = H + pt + pb

    # Sample a neutral background color from a 20px edge strip — good enough as
    # a seam-masking base; the model will repaint the padded area anyway.
    import statistics
    edge_pixels: list[tuple[int, int, int]] = []
    # top edge
    edge_pixels.extend([img.getpixel((x, 0)) for x in range(0, W, max(1, W // 50))])
    edge_pixels.extend([img.getpixel((x, H - 1)) for x in range(0, W, max(1, W // 50))])
    edge_pixels.extend([img.getpixel((0, y)) for y in range(0, H, max(1, H // 50))])
    edge_pixels.extend([img.getpixel((W - 1, y)) for y in range(0, H, max(1, H // 50))])
    avgr = int(statistics.mean(p[0] for p in edge_pixels))
    avgg = int(statistics.mean(p[1] for p in edge_pixels))
    avgb = int(statistics.mean(p[2] for p in edge_pixels))

    canvas = Image.new("RGB", (new_W, new_H), (avgr, avgg, avgb))
    canvas.paste(img, (pl, pt))

    buf = _BytesIO()
    canvas.save(buf, format="PNG")

    aspect = new_W / new_H
    if aspect > 1.5:
        word = "横版 16:9"
    elif aspect < 0.75:
        word = "竖版 9:16"
    else:
        word = f"{new_W}×{new_H}"

    return (buf.getvalue(), word, (new_W, new_H))


# Lazy import alias so we can construct BytesIO at module level without an extra
# import line in each helper.
from io import BytesIO as _BytesIO  # noqa: E402


def _encode_png_bytes(png_bytes: bytes, ext: str = "png") -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------


def _read_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if prompt and prompt_file:
        _die("Use --prompt or --prompt-file, not both.")
    if prompt_file:
        p = Path(prompt_file)
        if not p.is_file():
            _die(f"Prompt file not found: {p}")
        return p.read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    _die("Missing prompt. Use --prompt or --prompt-file.")
    return ""  # unreachable


def _append_suffix(prompt: str, suffix: str) -> str:
    sep = "\n\n" if prompt and not prompt.endswith(("\n", "。", ".", "!", "?", "！", "？")) else ""
    return f"{prompt}{sep}{suffix}".strip()


# ---------------------------------------------------------------------------
# Request body shaping
# ---------------------------------------------------------------------------


def _build_request_body(
    *,
    model: str,
    caps: dict[str, Any],
    prompt: str,
    size: str,
    output_format: str,
    watermark: bool,
    web_search: bool,
    reference_images: Optional[list[str]],
    optimize_prompt: Optional[str],
    sequential: bool,
    max_images: int,
    negative_prompt: Optional[str],
    response_format: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "output_format": output_format,
        "watermark": watermark,
        "response_format": response_format,
    }

    # Optimize prompt mode — Pro only accepts "standard"; Lite accepts both.
    opt_mode = optimize_prompt or ("standard" if "standard" in caps["optimize_modes"] else None)
    if opt_mode and opt_mode in caps["optimize_modes"]:
        body["optimize_prompt_options"] = {"mode": opt_mode}
    elif optimize_prompt:
        _warn(f"optimize_prompt mode '{optimize_prompt}' not supported on {model}; ignoring.")

    # Web search: only on Lite (and only if user explicitly passes --web-search).
    if web_search:
        if caps["supports_web_search"]:
            body["tools"] = [{"type": "web_search"}]
        else:
            _warn(f"Web search (tools:web_search) is not supported on {model}; ignoring --web-search.")

    # Reference images
    if reference_images:
        if len(reference_images) > caps["max_refs"]:
            _die(
                f"{model} accepts at most {caps['max_refs']} reference images "
                f"(got {len(reference_images)})."
            )
        body["image"] = reference_images if len(reference_images) > 1 else reference_images[0]

    # Sequential group generation (Lite only)
    if sequential:
        if caps["supports_sequential"]:
            body["sequential_image_generation"] = "auto"
            body["sequential_image_generation_options"] = {"max_images": max_images}
        else:
            _die(
                f"--sequential (group/storyboard generation) is only supported on Seedream Lite. "
                f"On Pro, use multiple --reference-image passes with natural-language scene "
                f"descriptions, or run separate calls. Pass --model lite if you need sequential."
            )

    # Negative prompt (Pro only — undocumented but accepted)
    if negative_prompt:
        if caps["supports_negative_prompt"]:
            body["negative_prompt"] = negative_prompt
        else:
            _warn(f"negative_prompt is not supported on {model}; ignoring.")

    return body


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _make_output_path(
    prompt: str,
    out: Optional[str],
    out_dir: str,
    output_format: str,
    index: int = 0,
) -> Path:
    ext = "jpg" if output_format == "jpeg" else output_format
    if out:
        p = Path(out).expanduser().resolve()
        if p.suffix == "":
            p = p.with_suffix(f".{ext}")
        return p

    d = Path(out_dir).expanduser().resolve()
    d.mkdir(parents=True, exist_ok=True)
    ts = _now_slug()
    slug = _slugify(prompt, max_len=40)
    stem = f"{ts}-{slug}" if index == 0 else f"{ts}-{slug}-{index + 1}"
    return d / f"{stem}.{ext}"


def _write_metadata(
    image_path: Path,
    *,
    prompt: str,
    model: str,
    size: str,
    output_format: str,
    watermark: bool,
    web_search: bool,
    reference_images: Optional[list[str]],
    optimize_prompt: Optional[str],
    base_url: str,
    dry_run: bool,
    negative_prompt: Optional[str] = None,
    response_format: Optional[str] = None,
    marker_rects: Optional[list[str]] = None,
    outpaint_specs: Optional[list[str]] = None,
    reported_size: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    revised_prompt: Optional[str] = None,
    usage: Optional[dict] = None,
) -> None:
    # Resolve model label for friendlier metadata
    caps = MODELS.get(model, {}).get("label", model)
    meta: dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "model_label": caps,
        "size": size,
        "output_format": output_format,
        "watermark": watermark,
        "web_search": web_search,
        "optimize_prompt": optimize_prompt,
        "reference_images_count": len(reference_images) if reference_images else 0,
        # Don't persist data URLs — they're huge and can contain secrets-adjacent material
        "reference_images_are_data_urls": bool(reference_images) and all(
            r.startswith("data:") for r in reference_images
        ),
        "negative_prompt": negative_prompt,
        "response_format": response_format,
        "marker_rects": marker_rects or [],
        "outpaint": outpaint_specs or [],
        "base_url": base_url,
        "image_path": str(image_path),
        "created_at": _now_iso(),
        "dry_run": dry_run,
    }
    if reported_size:
        meta["reported_size"] = reported_size
    if elapsed_ms is not None:
        meta["elapsed_ms"] = elapsed_ms
    if revised_prompt:
        meta["revised_prompt"] = revised_prompt
    if usage:
        meta["usage"] = usage

    meta_path = image_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Metadata: {meta_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Error classification + retry
# ---------------------------------------------------------------------------


def _is_retryable(status_code: int) -> bool:
    return status_code in (429, 500, 502, 503, 504)


class _APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str,
                 retry_after: Optional[float] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retry_after = retry_after


async def _call_api(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    base = str(client.base_url).rstrip("/")
    url = f"{base}/images/generations"
    t0 = time.monotonic()
    response = await client.post(url, json=body, timeout=float(timeout))
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    print(f"HTTP {response.status_code} ({elapsed_ms} ms)", file=sys.stderr)

    # Retry-after header
    retry_after: Optional[float] = None
    ra = response.headers.get("retry-after")
    if ra is not None:
        try:
            retry_after = float(ra)
        except ValueError:
            retry_after = None

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        text = response.text[:500]
        print(f"Unexpected response (non-JSON): {text}", file=sys.stderr)
        raise _APIError(response.status_code, "NonJSONResponse", text, retry_after)

    try:
        data = response.json()
    except Exception:
        text = response.text[:500]
        print(f"Failed to parse JSON response: {text}", file=sys.stderr)
        raise _APIError(response.status_code, "JSONParseError", text, retry_after)

    if not response.is_success:
        error_info = data.get("error", {})
        code = error_info.get("code", f"HTTP {response.status_code}")
        message = error_info.get("message", str(data))
        raise _APIError(response.status_code, code, message, retry_after)

    # Attach elapsed time for metadata
    data["_elapsed_ms"] = elapsed_ms
    return data


async def _download_image(client: httpx.AsyncClient, url: str, timeout: int) -> bytes:
    response = await client.get(url, timeout=float(timeout))
    response.raise_for_status()
    return response.content


async def _generate_single(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    timeout: int,
) -> tuple[list[bytes], Optional[str], Optional[dict], Optional[str], Optional[int]]:
    """Returns (image_bytes_list, revised_prompt, usage, reported_size, elapsed_ms)."""
    data = await _call_api(client, body, timeout)
    elapsed_ms = data.get("_elapsed_ms")

    images: list[bytes] = []
    revised_prompt: Optional[str] = None
    usage: Optional[dict] = data.get("usage")
    reported_size: Optional[str] = None

    results = data.get("data") or []
    for item in results:
        url = item.get("url")
        if url:
            img_bytes = await _download_image(client, url, timeout)
            images.append(img_bytes)
        elif item.get("b64_json"):
            images.append(base64.b64decode(item["b64_json"]))
        if item.get("revised_prompt"):
            revised_prompt = item["revised_prompt"]
        if item.get("size"):
            reported_size = item["size"]

    return images, revised_prompt, usage, reported_size, elapsed_ms


async def _generate_with_retry(
    api_key: str,
    base_url: str,
    body: dict[str, Any],
    timeout: int,
) -> tuple[list[bytes], Optional[str], Optional[dict], Optional[str], Optional[int]]:
    last_error: Optional[_APIError] = None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(base_url=base_url, headers=headers) as client:
                return await _generate_single(client, body, timeout)
        except httpx.TimeoutException as e:
            last_error = _APIError(0, "Timeout", str(e))
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(
                    f"Timeout, retrying in {delay:.0f}s (attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
        except _APIError as e:
            last_error = e
            if _is_retryable(e.status_code) and attempt < MAX_RETRIES:
                if e.retry_after and e.retry_after > 0:
                    delay = min(e.retry_after, 60.0)
                else:
                    delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(
                    f"API error {e.status_code} ({e.code}), retrying in {delay:.0f}s "
                    f"(attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
            else:
                raise

    raise last_error  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Subcommand: list-models
# ---------------------------------------------------------------------------


def _cmd_list_models(_args: argparse.Namespace) -> int:
    print("Seedream models known to this skill:\n")
    for mid, caps in MODELS.items():
        print(f"  {mid}")
        print(f"    Label:        {caps['label']}")
        print(f"    Aliases:      {', '.join(sorted(caps['aliases']))}")
        print(f"    Default size: {caps['default_size']}")
        print(f"    Preset sizes: {', '.join(sorted(caps['size_strings']))}")
        print(f"    Pixel range:  {caps['pixel_min']:,} – {caps['pixel_max']:,}")
        print(f"    Max refs:     {caps['max_refs']}")
        print(f"    web_search:   {'yes' if caps['supports_web_search'] else 'no'}")
        print(f"    sequential:   {'yes' if caps['supports_sequential'] else 'no'}")
        print(f"    neg prompt:   {'yes (beta/undocumented)' if caps['supports_negative_prompt'] else 'no'}")
        print(f"    Opt modes:    {', '.join(sorted(caps['optimize_modes']))}")
        print(f"    resp format:  {caps['response_format_default']}")
        print(f"    Price:        {caps['price_per_image']}")
        print(f"    Notes:        {caps['notes']}")
        print()
    print("Default model: " + DEFAULT_MODEL)
    print()
    print("Use --model <id> (or pro/lite alias) to override. Any other model id is passed through")
    print("verbatim with Pro-capability defaults (useful for fresh dated Pro builds).")
    return 0


# ---------------------------------------------------------------------------
# Common setup used by generate/edit/batch
# ---------------------------------------------------------------------------


def _add_common_gen_args(p: argparse.ArgumentParser, *, include_lite_only: bool) -> None:
    """Args shared by generate, edit, and batch (latter uses a subset)."""
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"Model id or alias (pro|lite). Default: {DEFAULT_MODEL}.")
    p.add_argument("--size", default=None,
                   help="Image size preset (1K/2K/3K/4K subject to model) or WIDTHxHEIGHT "
                        "(e.g. 1792x1024). Default follows model (Pro: 2K, Lite: 2K).")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=list(ALLOWED_OUTPUT_FORMATS),
                   help=f"Output image format (default: {DEFAULT_OUTPUT_FORMAT}).")
    p.add_argument("--wechat-header", action="store_true",
                   help="Shorthand for --size 1792x1024 (16:9 wide cover, Pro only). "
                        "Alias: --wide.")
    p.add_argument("--wide", action="store_true",
                   help="Shorthand for --size 1792x1024 (16:9 wide cover/banner, Pro only). "
                        "Alias of --wechat-header.")
    p.add_argument("--square", action="store_true",
                   help="Shorthand for square output (Pro: 1024x1024, Lite: 2048x2048).")
    p.add_argument("--portrait", action="store_true",
                   help="Shorthand for 3:4 vertical output (Pro: 1536x2048, Lite: 2048x2732).")
    p.add_argument("--landscape", action="store_true",
                   help="Shorthand for 16:9 horizontal output (Pro: 2048x1152, Lite: 2732x1536).")
    p.add_argument("--web-search", action="store_true", default=False,
                   help="Enable web search (Lite only; Pro ignores this with a warning). "
                        "Default OFF.")
    p.add_argument("--no-web-search", action="store_false", dest="web_search",
                   help="Explicitly disable web search (default).")
    p.add_argument("--watermark", action="store_true",
                   help="Include Seedream watermark (default: off).")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], default=None,
                   help="Prompt optimization mode. Pro only supports 'standard'.")
    p.add_argument("--negative-prompt", default=None,
                   help=f"Negative prompt. On Pro defaults to a gentle quality guard "
                        f"({PRO_DEFAULT_NEGATIVE!r}); pass --negative-prompt '' to disable. "
                        f"Not supported on Lite.")
    p.add_argument("--no-negative-prompt", action="store_true",
                   help="Disable the default negative prompt (Pro only).")
    p.add_argument("--response-format", choices=["b64_json", "url"], default=None,
                   help="Response format. Default follows model (Pro: b64_json, Lite: url).")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the request body and exit without calling the API.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing output files.")
    if include_lite_only:
        p.add_argument("--n", type=int, default=1,
                       help=f"Number of independent images to generate (1-{DEFAULT_MAX_N}, default: 1).")
        p.add_argument("--sequential", action="store_true",
                       help="Enable sequential storyboard/group generation (Lite only).")
        p.add_argument("--max-images", type=int, default=4,
                       help="Max images for sequential generation (1-15, default: 4).")


def _resolve_common(args: argparse.Namespace, *, require_prompt: bool = True) -> dict[str, Any]:
    """Resolve model, size, prompt, negatives, and edit-preprocess (markers/outpaint)
    from argparse args. Returns a dict with everything needed to build the body.
    """
    model_id, caps = _resolve_model(args.model)

    # Resolve size (convenience flags → explicit string; model-aware)
    size = _apply_size_shortcuts(
        args.size, args.wechat_header, args.square, args.wide, args.portrait, args.landscape, caps,
    )
    _validate_size(size, caps, model_id)

    # Prompt
    prompt = _read_prompt(getattr(args, "prompt", None), getattr(args, "prompt_file", None)) \
        if require_prompt else ""
    if len(prompt) > MAX_PROMPT_CHARS:
        _warn(f"Prompt length {len(prompt)} exceeds recommended {MAX_PROMPT_CHARS} chars.")

    # Negative prompt
    if getattr(args, "no_negative_prompt", False):
        negative_prompt = ""
    elif getattr(args, "negative_prompt", None) is not None:
        negative_prompt = args.negative_prompt
    else:
        # default on Pro, none on Lite
        negative_prompt = PRO_DEFAULT_NEGATIVE if caps["supports_negative_prompt"] else None
    # Normalize empty string to None (so it doesn't get sent)
    if negative_prompt == "":
        negative_prompt = None

    # Response format
    response_format = getattr(args, "response_format", None) or caps["response_format_default"]

    # Reference images (used by both generate (optional) and edit (required))
    ref_paths = list(getattr(args, "reference_image", []) or [])
    marker_specs = list(getattr(args, "marker_rect", []) or [])
    outpaint_specs = list(getattr(args, "outpaint", []) or [])

    annotated_path: Optional[Path] = None
    outpaint_canvas_png: Optional[bytes] = None
    outpaint_aspect_word: Optional[str] = None

    # Outpaint first (it extends the canvas before markers are drawn), then markers.
    if outpaint_specs:
        if not ref_paths:
            _die("--outpaint requires a --reference-image to extend.")
        if len(ref_paths) != 1:
            _die("--outpaint works with exactly one reference image.")
        paddings: dict[str, int] = {}
        for spec in outpaint_specs:
            d, n = _parse_outpaint(spec)
            paddings[d] = paddings.get(d, 0) + n
        src = Path(ref_paths[0]).expanduser().resolve()
        png_bytes, aspect_word, new_dims = _apply_outpaint(src, paddings)
        outpaint_canvas_png = png_bytes
        outpaint_aspect_word = aspect_word
        prompt = _append_suffix(
            prompt,
            (OUTPAINT_FILL_ZH if _looks_chinese(prompt) else OUTPAINT_FILL_EN).format(aspect_word=aspect_word),
        )

    # Marker rectangles — draw on the reference image and append cleanup suffix.
    if marker_specs:
        if not ref_paths:
            _die("--marker-rect requires at least one --reference-image to annotate.")
        # Markers always annotate the first reference; additional refs are passed as-is.
        src_primary = ref_paths[0]
        if outpaint_canvas_png is not None:
            # We already padded; write that to a temp file so we can draw markers on it.
            tmp_path = Path(args.out_dir if hasattr(args, "out_dir") else DEFAULT_OUTPUT_DIR) / ".marker-tmp.png"
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_bytes(outpaint_canvas_png)
            src_for_markers = tmp_path
            # Replace the first reference bytes (no longer outpaint canvas separately)
            outpaint_canvas_png = None
        elif _is_url(src_primary):
            _die("--marker-rect needs a local reference image (URLs cannot be annotated client-side).")
        else:
            src_for_markers = Path(src_primary).expanduser().resolve()

        rects = [_parse_marker_rect(s) for s in marker_specs]
        color = _parse_color(getattr(args, "marker_color", "#ff0000"))
        fill_alpha = int(getattr(args, "marker_alpha", 80))
        stroke_width = int(getattr(args, "marker_stroke", 3))
        annotated_png = _apply_markers(src_for_markers, rects, color, fill_alpha, stroke_width)

        # Save annotated image next to output for inspection
        out_dir = Path(getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        annotated_path = out_dir / f"{_now_slug()}-annotated.png"
        annotated_path.write_bytes(annotated_png)
        _info(f"Marker-annotated image saved for inspection: {annotated_path}")

        # Replace the primary reference with the annotated PNG
        if ref_paths[0] == src_primary:
            ref_paths = [str(annotated_path)] + ref_paths[1:]
        else:
            ref_paths[0] = str(annotated_path)

        # Append cleanup prompt unless disabled
        if not getattr(args, "no_marker_cleanup_prompt", False):
            cleanup = MARKER_CLEANUP_ZH if _looks_chinese(prompt) else MARKER_CLEANUP_EN
            prompt = _append_suffix(prompt, cleanup)

    # Encode reference images (or the outpaint canvas if outpaint was applied without markers)
    refs: Optional[list[str]] = None
    if ref_paths:
        refs = _resolve_reference_images(ref_paths)
    elif outpaint_canvas_png is not None:
        # Outpaint without markers: send padded canvas directly
        refs = [_encode_png_bytes(outpaint_canvas_png)]
        if not prompt.endswith(OUTPAINT_FILL_ZH[-20:]) and not prompt.endswith(OUTPAINT_FILL_EN[-20:]):
            prompt = _append_suffix(
                prompt,
                (OUTPAINT_FILL_ZH if _looks_chinese(prompt) else OUTPAINT_FILL_EN).format(
                    aspect_word=outpaint_aspect_word or "扩展"
                ),
            )

    # N
    n = getattr(args, "n", 1)
    if n < 1 or n > DEFAULT_MAX_N:
        _die(f"--n must be 1-{DEFAULT_MAX_N} (got {n}).")

    # Sequential (Lite only)
    sequential = getattr(args, "sequential", False)
    max_images = getattr(args, "max_images", 4)
    if sequential and (max_images < 1 or max_images > 15):
        _die(f"--max-images must be 1-15 (got {max_images}).")

    # Web-search: if flag is on but model doesn't support it, _build_request_body warns
    web_search = bool(getattr(args, "web_search", False))

    output_format = args.output_format
    if output_format == "jpg":
        output_format = "jpeg"

    return {
        "model_id": model_id,
        "caps": caps,
        "prompt": prompt,
        "size": size,
        "output_format": output_format,
        "watermark": bool(args.watermark),
        "web_search": web_search,
        "optimize_prompt": args.optimize_prompt,
        "negative_prompt": negative_prompt,
        "response_format": response_format,
        "reference_images": refs,
        "reference_image_paths": list(getattr(args, "reference_image", []) or []),
        "marker_specs": marker_specs,
        "outpaint_specs": outpaint_specs,
        "annotated_path": str(annotated_path) if annotated_path else None,
        "n": n,
        "sequential": sequential,
        "max_images": max_images,
        "timeout": int(args.timeout),
        "dry_run": bool(args.dry_run),
        "force": bool(args.force),
    }


# ---------------------------------------------------------------------------
# Subcommand: generate
# ---------------------------------------------------------------------------


def _add_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate", help="Create a new image from a text prompt.")
    p.add_argument("--prompt", "-p", help="Text description for the image.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file.")
    p.add_argument("--reference-image", action="append", default=[],
                   help="Reference image path or URL (repeatable; max 10 on Pro, 14 on Lite).")
    p.add_argument("--out", help="Output file path (default: <out-dir>/<ts>-<slug>.<ext>).")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    _add_common_gen_args(p, include_lite_only=True)
    p.set_defaults(func=_cmd_generate)


def _cmd_generate(args: argparse.Namespace) -> int:
    r = _resolve_common(args, require_prompt=True)
    body = _build_request_body(
        model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
        output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
        reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
        sequential=r["sequential"], max_images=r["max_images"],
        negative_prompt=r["negative_prompt"], response_format=r["response_format"],
    )

    out = getattr(args, "out", None)
    out_dir = getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)

    if r["dry_run"]:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        # Best-effort dry-run metadata path
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"])
        _write_metadata(
            image_path, prompt=r["prompt"], model=r["model_id"], size=r["size"],
            output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
            reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
            base_url=DEFAULT_BASE_URL, dry_run=True, negative_prompt=r["negative_prompt"],
            response_format=r["response_format"], marker_rects=r["marker_specs"],
            outpaint_specs=r["outpaint_specs"],
        )
        return 0

    if r["n"] > 1:
        return asyncio.run(_generate_concurrent(args, body, r, out, out_dir))
    return asyncio.run(_generate_one(args, body, r, out, out_dir))


async def _generate_one(
    args: argparse.Namespace,
    body: dict[str, Any],
    r: dict[str, Any],
    out: Optional[str],
    out_dir: str,
) -> int:
    api_key, base_url = _get_api_settings()
    t0 = time.monotonic()
    try:
        images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
            api_key, base_url, body, r["timeout"],
        )
    except _APIError as e:
        _die(f"API error {e.status_code}: {e.code} — {e.message}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    for idx, img_bytes in enumerate(images):
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"], idx)
        if image_path.exists() and not r["force"]:
            _die(f"Output already exists: {image_path} (use --force to overwrite)")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(img_bytes)
        print(f"Image: {image_path}")

        _write_metadata(
            image_path,
            prompt=r["prompt"], model=r["model_id"], size=r["size"],
            output_format=r["output_format"], watermark=r["watermark"],
            web_search=r["web_search"], reference_images=r["reference_images"],
            optimize_prompt=r["optimize_prompt"], base_url=base_url, dry_run=False,
            negative_prompt=r["negative_prompt"], response_format=r["response_format"],
            marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
            reported_size=reported_size, elapsed_ms=elapsed_ms,
            revised_prompt=revised_prompt, usage=usage,
        )

    return 0


async def _generate_concurrent(
    args: argparse.Namespace,
    body: dict[str, Any],
    r: dict[str, Any],
    out: Optional[str],
    out_dir: str,
) -> int:
    api_key, base_url = _get_api_settings()

    async def _run_one(i: int) -> tuple[int, list[bytes], Optional[str], Optional[dict], Optional[str], Optional[int], Optional[str]]:
        t0 = time.monotonic()
        try:
            images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
                api_key, base_url, body.copy(), r["timeout"],
            )
            return i, images, revised_prompt, usage, reported_size, int((time.monotonic() - t0) * 1000), None
        except _APIError as e:
            return i, [], None, None, None, None, str(e)

    tasks = [_run_one(i) for i in range(r["n"])]
    results = await asyncio.gather(*tasks)

    errors = 0
    for i, images, revised_prompt, usage, reported_size, elapsed_ms, error in results:
        if error:
            print(f"Error (variant {i+1}/{r['n']}): {error}", file=sys.stderr)
            errors += 1
            continue
        for j, img_bytes in enumerate(images):
            image_path = _make_output_path(
                r["prompt"], out, out_dir, r["output_format"], i * len(images) + j,
            )
            if image_path.exists() and not r["force"]:
                _warn(f"Output exists, skipping: {image_path}")
                continue
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(img_bytes)
            print(f"Image: {image_path}")
            _write_metadata(
                image_path,
                prompt=r["prompt"], model=r["model_id"], size=r["size"],
                output_format=r["output_format"], watermark=r["watermark"],
                web_search=r["web_search"], reference_images=r["reference_images"],
                optimize_prompt=r["optimize_prompt"], base_url=base_url, dry_run=False,
                negative_prompt=r["negative_prompt"], response_format=r["response_format"],
                marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
                reported_size=reported_size, elapsed_ms=elapsed_ms,
                revised_prompt=revised_prompt, usage=usage,
            )

    if errors == r["n"]:
        _die(f"All {r['n']} concurrent generations failed.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: edit
# ---------------------------------------------------------------------------


def _add_edit_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "edit",
        help="Modify an image: marker-based region edit (draw a colored box and describe the "
             "change), style transfer, reference-based character consistency, or outpaint."
    )
    p.add_argument("--prompt", "-p", required=True, help="Description of what to change.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file.")
    p.add_argument("--reference-image", action="append", required=True,
                   help="Reference/input image (repeatable; first image is the one being edited "
                        "when markers/outpaint are used).")
    p.add_argument("--marker-rect", action="append", default=[],
                   help="Mark a rectangular region to edit. Spec as X,Y,W,H in pixels "
                        "(e.g. 100,150,800,300) or percent (e.g. 10%%,15%%,60%%,20%%). "
                        "Repeat for multiple regions. Use with a natural-language prompt "
                        "like 'Red box: replace the title with \"新标题\"' and add --marker-color "
                        "for multi-color regions.")
    p.add_argument("--marker-color", default="#ff0000",
                   help="Marker rectangle color (#RRGGBB, default #ff0000 red).")
    p.add_argument("--marker-alpha", type=int, default=80,
                   help="Marker fill alpha 0-255 (default 80).")
    p.add_argument("--marker-stroke", type=int, default=3,
                   help="Marker outline stroke width in px (default 3).")
    p.add_argument("--no-marker-cleanup-prompt", action="store_true",
                   help="Don't auto-append the 'remove the colored markers' suffix.")
    p.add_argument("--outpaint", action="append", default=[],
                   help="Outpaint (extend canvas). Format direction:pixels (e.g. left:400). "
                        "Direction: left/right/top/bottom. Repeat for multiple sides.")
    p.add_argument("--out", help="Output file path.")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR,
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    _add_common_gen_args(p, include_lite_only=False)
    p.set_defaults(func=_cmd_edit, n=1, sequential=False, max_images=4)


def _cmd_edit(args: argparse.Namespace) -> int:
    r = _resolve_common(args, require_prompt=True)
    body = _build_request_body(
        model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
        output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
        reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
        sequential=False, max_images=4,
        negative_prompt=r["negative_prompt"], response_format=r["response_format"],
    )

    out = getattr(args, "out", None)
    out_dir = getattr(args, "out_dir", DEFAULT_OUTPUT_DIR)

    if r["dry_run"]:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        image_path = _make_output_path(r["prompt"], out, out_dir, r["output_format"])
        _write_metadata(
            image_path, prompt=r["prompt"], model=r["model_id"], size=r["size"],
            output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
            reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
            base_url=DEFAULT_BASE_URL, dry_run=True, negative_prompt=r["negative_prompt"],
            response_format=r["response_format"], marker_rects=r["marker_specs"],
            outpaint_specs=r["outpaint_specs"],
        )
        return 0

    return asyncio.run(_generate_one(args, body, r, out, out_dir))


# ---------------------------------------------------------------------------
# Subcommand: generate-batch
# ---------------------------------------------------------------------------


def _add_batch_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate-batch", help="Run many generation jobs from a JSONL file.")
    p.add_argument("--input", required=True, help="Path to JSONL file. Each line: bare string (prompt) "
                                                  "or JSON object (prompt + per-job overrides).")
    p.add_argument("--out-dir", default=f"{DEFAULT_OUTPUT_DIR}/batch",
                   help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}/batch).")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                   help=f"Max concurrent requests (default: {DEFAULT_CONCURRENCY}).")
    # Batch uses a subset of common args (no --n/--sequential/--out per-job)
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Default model (default: {DEFAULT_MODEL}).")
    p.add_argument("--size", default=None, help="Default image size.")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=list(ALLOWED_OUTPUT_FORMATS),
                   help=f"Default output format (default: {DEFAULT_OUTPUT_FORMAT}).")
    p.add_argument("--wechat-header", action="store_true", help="Default size 1792x1024. Alias: --wide.")
    p.add_argument("--wide", action="store_true", help="Default size 1792x1024 (alias of --wechat-header).")
    p.add_argument("--square", action="store_true", help="Default to square output.")
    p.add_argument("--portrait", action="store_true", help="Default to 3:4 vertical output.")
    p.add_argument("--landscape", action="store_true", help="Default to 16:9 horizontal output.")
    p.add_argument("--web-search", action="store_true", default=False, help="Default web-search on (Lite only).")
    p.add_argument("--no-web-search", action="store_false", dest="web_search", help="Default web-search off.")
    p.add_argument("--watermark", action="store_true", help="Default watermark on.")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], default=None,
                   help="Default prompt optimization mode.")
    p.add_argument("--negative-prompt", default=None, help="Default negative prompt.")
    p.add_argument("--no-negative-prompt", action="store_true", help="Default negative-prompt off.")
    p.add_argument("--response-format", choices=["b64_json", "url"], default=None,
                   help="Default response format.")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true", help="Print bodies and exit.")
    p.add_argument("--force", action="store_true", help="Overwrite existing outputs.")
    p.set_defaults(func=_cmd_batch)


def _parse_jsonl(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.is_file():
        _die(f"JSONL file not found: {p}")

    jobs: list[dict[str, Any]] = []
    for lineno, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            data = line.strip('"').strip("'").strip()

        if isinstance(data, str):
            jobs.append({"prompt": data})
        elif isinstance(data, dict):
            if "prompt" not in data:
                _warn(f"Line {lineno}: missing 'prompt' key, skipping.")
                continue
            jobs.append(data)
        else:
            _warn(f"Line {lineno}: unexpected type {type(data).__name__}, skipping.")

    if not jobs:
        _die(f"No valid jobs found in {path}.")
    print(f"Parsed {len(jobs)} job(s) from {path}", file=sys.stderr)
    return jobs


def _cmd_batch(args: argparse.Namespace) -> int:
    jobs = _parse_jsonl(args.input)
    # API key used by async workers — load eagerly so we fail fast on missing key
    _get_api_settings()

    bodies: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for i, job in enumerate(jobs):
        # Merge job onto a pseudo-argparse namespace so _resolve_common handles per-model logic
        class _NS:
            pass
        ns = _NS()
        ns.model = job.get("model", args.model)
        ns.size = job.get("size", args.size)
        ns.output_format = job.get("output_format", args.output_format)
        ns.wechat_header = bool(job.get("wechat_header", args.wechat_header))
        ns.wide = bool(job.get("wide", args.wide)) or ns.wechat_header
        ns.square = bool(job.get("square", args.square))
        ns.portrait = bool(job.get("portrait", args.portrait))
        ns.landscape = bool(job.get("landscape", args.landscape))
        ns.web_search = bool(job.get("web_search", args.web_search))
        ns.watermark = bool(job.get("watermark", args.watermark))
        ns.optimize_prompt = job.get("optimize_prompt", args.optimize_prompt)
        ns.negative_prompt = job.get("negative_prompt", args.negative_prompt)
        ns.no_negative_prompt = bool(job.get("no_negative_prompt", False))
        ns.response_format = job.get("response_format", args.response_format)
        ns.reference_image = list(job.get("reference_image", []) or [])
        ns.marker_rect = list(job.get("marker_rects", []) or [])
        ns.marker_color = job.get("marker_color", "#ff0000")
        ns.marker_alpha = int(job.get("marker_alpha", 80))
        ns.marker_stroke = int(job.get("marker_stroke", 3))
        ns.no_marker_cleanup_prompt = bool(job.get("no_marker_cleanup_prompt", False))
        ns.outpaint = list(job.get("outpaint", []) or [])
        ns.prompt = job["prompt"]
        ns.prompt_file = None
        ns.out_dir = args.out_dir
        ns.n = 1
        ns.sequential = False
        ns.max_images = 4
        ns.timeout = int(job.get("timeout", args.timeout))
        ns.dry_run = bool(args.dry_run)
        ns.force = bool(args.force)
        ns.out = None

        r = _resolve_common(ns, require_prompt=True)
        body = _build_request_body(
            model=r["model_id"], caps=r["caps"], prompt=r["prompt"], size=r["size"],
            output_format=r["output_format"], watermark=r["watermark"], web_search=r["web_search"],
            reference_images=r["reference_images"], optimize_prompt=r["optimize_prompt"],
            sequential=False, max_images=4,
            negative_prompt=r["negative_prompt"], response_format=r["response_format"],
        )
        bodies.append((job["prompt"], body, r))

    if args.dry_run:
        for i, (prompt, body, _r) in enumerate(bodies):
            print(f"\n--- Job {i+1} ---")
            print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0

    return asyncio.run(_run_batch(args, bodies))


async def _run_batch(
    args: argparse.Namespace,
    bodies: list[tuple[str, dict[str, Any], dict[str, Any]]],
) -> int:
    sem = asyncio.Semaphore(args.concurrency)
    api_key, base_url = _get_api_settings()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    async def _run_job(index: int, prompt: str, body: dict[str, Any], r: dict[str, Any]) -> bool:
        async with sem:
            try:
                t0 = time.monotonic()
                images, revised_prompt, usage, reported_size, _call_ms = await _generate_with_retry(
                    api_key, base_url, body, r["timeout"],
                )
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                for j, img_bytes in enumerate(images):
                    stem = _slugify(prompt, max_len=30)
                    ext = "jpg" if r["output_format"] == "jpeg" else r["output_format"]
                    image_path = out_dir / f"job-{index+1:03d}-{stem}-{j+1}.{ext}"
                    if image_path.exists() and not args.force:
                        _warn(f"Output exists, skipping: {image_path}")
                        continue
                    image_path.write_bytes(img_bytes)
                    print(f"[{index+1}/{len(bodies)}] Image: {image_path}")
                    _write_metadata(
                        image_path,
                        prompt=prompt, model=body["model"], size=body["size"],
                        output_format=r["output_format"], watermark=body.get("watermark", False),
                        web_search="tools" in body, reference_images=body.get("image"),
                        optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"),
                        base_url=base_url, dry_run=False,
                        negative_prompt=body.get("negative_prompt"),
                        response_format=body.get("response_format"),
                        marker_rects=r["marker_specs"], outpaint_specs=r["outpaint_specs"],
                        reported_size=reported_size, elapsed_ms=elapsed_ms,
                        revised_prompt=revised_prompt, usage=usage,
                    )
                return True
            except _APIError as e:
                print(f"[{index+1}/{len(bodies)}] Error: {e.code} — {e.message}", file=sys.stderr)
                return False

    tasks = [_run_job(i, prompt, body, r) for i, (prompt, body, r) in enumerate(bodies)]
    results = await asyncio.gather(*tasks)

    successes = sum(1 for r in results if r)
    failures = len(results) - successes
    print(f"\nBatch complete: {successes} success, {failures} failed", file=sys.stderr)
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    _load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate and edit images with Seedream 5.0 Pro (default) via Volcengine Ark API.\n"
                    "Pro ships SOTA Chinese+English text rendering and marker-based region editing.\n"
                    "Docs: https://www.volcengine.com/docs/82379/1824121",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands.")
    _add_generate_parser(subparsers)
    _add_edit_parser(subparsers)
    _add_batch_parser(subparsers)

    # list-models is simple enough to not need a full common-arg parser
    p_list = subparsers.add_parser("list-models", help="Print known model ids, capabilities, and pricing.")
    p_list.set_defaults(func=_cmd_list_models)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
