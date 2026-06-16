#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27.0",
#   "pillow>=10.0.0",
# ]
# ///
"""Generate, edit, and batch-generate images with Seedream 5.0 via Volcengine Ark API.

Subcommands:
  generate         Create a new image from a text prompt.
  edit             Modify an existing image using reference images.
  generate-batch   Run many generation jobs from a JSONL file.

Defaults to doubao-seedream-5-0-260128. Sibling *.json metadata is written
next to each output image.

API docs: https://www.volcengine.com/docs/82379/1824121?lang=zh
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
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import httpx


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "doubao-seedream-5-0-260128"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_OUTPUT_DIR = "output/seedream-image-gen"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_TIMEOUT = 300
DEFAULT_CONCURRENCY = 3
DEFAULT_MAX_N = 4
MAX_RETRIES = 3
RETRY_BACKOFF = (1.0, 2.0, 4.0)
MAX_REFERENCE_IMAGES = 14
MAX_REFERENCE_BYTES = 30 * 1024 * 1024
MAX_GROUP_IMAGES = 15
SIZE_MIN_PIXELS = 3_686_400  # 2560×1440
SIZE_MAX_PIXELS = 16_777_216  # 4096×4096
MAX_PROMPT_CHARS = 6_000  # generous for mixed Chinese/English

ALLOWED_OUTPUT_FORMATS = {"png", "jpeg", "jpg"}
ALLOWED_SIZE_STRINGS = {"2K", "3K", "4K"}


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


def _slugify(value: str, max_len: int = 60) -> str:
    """Turn a prompt snippet into a safe filename component."""
    value = value.strip().lower()
    # Keep CJK characters; replace whitespace and punctuation with hyphens
    value = re.sub(r"[^\w一-鿿]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:max_len] if value else "image"


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def _get_api_settings() -> tuple[str, str]:
    """Return (api_key, base_url). Reads env, then .env, then prompts (TTY only)."""
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL") or os.getenv("MODEL_IMAGE_API_BASE") or DEFAULT_BASE_URL

    if not api_key:
        if sys.stdin.isatty() and sys.stderr.isatty():
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
# Size validation
# ---------------------------------------------------------------------------


def _validate_size(size: str) -> None:
    """Lightweight client-side size validation. Raises SystemExit on error."""
    size_upper = size.upper()
    if size_upper in ALLOWED_SIZE_STRINGS:
        return

    m = re.fullmatch(r"(\d{3,5})x(\d{3,5})", size)
    if not m:
        _die(
            f"Invalid size '{size}'. Use '2K', '3K', '4K', or 'WIDTHxHEIGHT' "
            "(e.g. '2048x2048', '4096x4096', '2560x1440')."
        )

    w, h = int(m.group(1)), int(m.group(2))
    total = w * h
    aspect = max(w, h) / min(w, h)

    if total < SIZE_MIN_PIXELS:
        _die(
            f"Size {size}: total pixels {total:,} below minimum {SIZE_MIN_PIXELS:,} "
            "(e.g. 2560x1440)."
        )
    if total > SIZE_MAX_PIXELS:
        _die(
            f"Size {size}: total pixels {total:,} exceeds maximum {SIZE_MAX_PIXELS:,} "
            "(e.g. 4096x4096)."
        )
    if aspect > 16:
        _die(
            f"Size {size}: aspect ratio {aspect:.1f}:1 exceeds maximum 16:1."
        )


# ---------------------------------------------------------------------------
# Reference image handling
# ---------------------------------------------------------------------------


def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def _encode_reference_image(path: str) -> str:
    """Convert a local image file to base64 data URL, or pass through a URL."""
    if _is_url(path):
        return path

    p = Path(path).expanduser().resolve()
    if not p.is_file():
        _die(f"Reference image not found: {path}")

    size = p.stat().st_size
    if size > MAX_REFERENCE_BYTES:
        _warn(f"Reference image exceeds 30MB limit: {path} ({size:,} bytes)")

    ext = p.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"

    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/{ext};base64,{b64}"


def _resolve_reference_images(paths: list[str]) -> list[str]:
    """Resolve and encode reference image paths. URLs pass through unchanged."""
    return [_encode_reference_image(p) for p in paths]


# ---------------------------------------------------------------------------
# Prompt
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


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------


def _build_request_body(
    *,
    model: str,
    prompt: str,
    size: str,
    output_format: str,
    watermark: bool,
    web_search: bool,
    reference_images: Optional[list[str]],
    optimize_prompt: Optional[str],
    sequential: bool,
    max_images: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "output_format": output_format,
        "watermark": watermark,
    }

    if web_search:
        body["tools"] = [{"type": "web_search"}]

    if reference_images:
        body["image"] = reference_images if len(reference_images) > 1 else reference_images[0]

    if optimize_prompt:
        body["optimize_prompt_options"] = {"mode": optimize_prompt}

    if sequential:
        body["sequential_image_generation"] = "auto"
        body["sequential_image_generation_options"] = {"max_images": max_images}

    return body


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _make_output_path(
    prompt: str,
    out: Optional[str],
    out_dir: str,
    index: int = 0,
) -> Path:
    """Determine the output file path."""
    if out:
        p = Path(out).expanduser().resolve()
        if p.suffix == "":
            p = p.with_suffix(f".{DEFAULT_OUTPUT_FORMAT}")
        return p

    d = Path(out_dir).expanduser().resolve()
    d.mkdir(parents=True, exist_ok=True)
    ts = _now_slug()
    slug = _slugify(prompt, max_len=40)
    stem = f"{ts}-{slug}" if index == 0 else f"{ts}-{slug}-{index + 1}"
    return d / f"{stem}.png"


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
    revised_prompt: Optional[str] = None,
    usage: Optional[dict] = None,
) -> None:
    meta: dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "size": size,
        "output_format": output_format,
        "watermark": watermark,
        "web_search": web_search,
        "optimize_prompt": optimize_prompt,
        "reference_images": reference_images or [],
        "base_url": base_url,
        "image_path": str(image_path),
        "created_at": _now_iso(),
        "dry_run": dry_run,
    }
    if revised_prompt:
        meta["revised_prompt"] = revised_prompt
    if usage:
        meta["usage"] = usage

    meta_path = image_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Metadata: {meta_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Error classification and retry
# ---------------------------------------------------------------------------


def _is_retryable(status_code: int) -> bool:
    return status_code in (429, 500, 502, 503, 504)


def _classify_and_report(response: httpx.Response) -> str:
    """Return classification: 'transient', 'user_error', 'auth_error', 'success'."""
    if response.is_success:
        return "success"

    status = response.status_code
    if _is_retryable(status):
        return "transient"

    if status == 401:
        return "auth_error"

    return "user_error"


# ---------------------------------------------------------------------------
# Core API call
# ---------------------------------------------------------------------------


async def _call_api(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    """Make a single image generation API call. Returns parsed JSON."""
    # httpx.AsyncClient resolves base_url to a URL object — use it safely
    base = str(client.base_url).rstrip("/")
    url = f"{base}/images/generations"
    response = await client.post(url, json=body, timeout=float(timeout))

    # Log response status for debugging
    print(f"HTTP {response.status_code}", file=sys.stderr)

    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        # Non-JSON response — dump first 500 chars for diagnosis
        text = response.text[:500]
        print(f"Unexpected response (non-JSON): {text}", file=sys.stderr)
        raise _APIError(response.status_code, "NonJSONResponse", text)

    try:
        data = response.json()
    except Exception:
        text = response.text[:500]
        print(f"Failed to parse JSON response: {text}", file=sys.stderr)
        raise _APIError(response.status_code, "JSONParseError", text)

    if not response.is_success:
        error_info = data.get("error", {})
        code = error_info.get("code", f"HTTP {response.status_code}")
        message = error_info.get("message", str(data))
        raise _APIError(response.status_code, code, message)

    return data


class _APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


async def _download_image(client: httpx.AsyncClient, url: str, timeout: int) -> bytes:
    """Download a generated image from a URL."""
    response = await client.get(url, timeout=float(timeout))
    response.raise_for_status()
    return response.content


async def _generate_single(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    timeout: int,
) -> tuple[list[bytes], Optional[str], Optional[dict]]:
    """Make one API call. Returns (image_bytes_list, revised_prompt, usage)."""
    data = await _call_api(client, body, timeout)

    images: list[bytes] = []
    revised_prompt: Optional[str] = None
    usage: Optional[dict] = data.get("usage")

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

    return images, revised_prompt, usage


async def _generate_with_retry(
    api_key: str,
    base_url: str,
    body: dict[str, Any],
    timeout: int,
) -> tuple[list[bytes], Optional[str], Optional[dict]]:
    """Generate with retry for transient errors."""
    last_error: Optional[_APIError] = None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                base_url=base_url,
                headers=headers,
            ) as client:
                return await _generate_single(client, body, timeout)
        except httpx.TimeoutException as e:
            last_error = _APIError(0, "Timeout", str(e))
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"Timeout, retrying in {delay:.0f}s (attempt {attempt+1}/{MAX_RETRIES})...", file=sys.stderr)
                await asyncio.sleep(delay)
        except _APIError as e:
            last_error = e
            if _is_retryable(e.status_code) and attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(
                    f"API error {e.status_code} ({e.code}), retrying in {delay:.0f}s "
                    f"(attempt {attempt+1}/{MAX_RETRIES})...",
                    file=sys.stderr,
                )
                await asyncio.sleep(delay)
            else:
                raise

    raise last_error  # Shouldn't reach, but satisfy type checker


# ---------------------------------------------------------------------------
# Subcommand: generate
# ---------------------------------------------------------------------------


def _add_generate_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate", help="Create a new image from a text prompt.")
    p.add_argument("--prompt", "-p", help="Text description for the image.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file.")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL}).")
    p.add_argument("--size", default="2048x2048", help="Image size: 2K, 3K, 4K, or WIDTHxHEIGHT (default: 2048x2048).")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "jpg"], help="Output image format (default: png).")
    p.add_argument("--out", help="Output file path. Default: output/seedream-image-gen/<timestamp>-<slug>.png")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    p.add_argument("--n", type=int, default=1, help="Number of independent images to generate (1-4, default: 1).")
    p.add_argument("--reference-image", action="append", default=[], help="Reference image path or URL (repeatable, max 14).")
    p.add_argument("--web-search", action="store_true", default=True, help="Enable web search. Enabled by default.")
    p.add_argument("--no-web-search", action="store_false", dest="web_search", help="Disable web search.")
    p.add_argument("--watermark", action="store_true", help="Include Seedream watermark (default: off).")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], help="Enable prompt optimization.")
    p.add_argument("--sequential", action="store_true", help="Enable sequential image generation for group images.")
    p.add_argument("--max-images", type=int, default=4, help="Max images for sequential generation (1-15, default: 4).")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true", help="Print the request body and exit without calling the API.")
    p.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    p.set_defaults(func=_cmd_generate)


def _cmd_generate(args: argparse.Namespace) -> int:
    prompt = _read_prompt(args.prompt, args.prompt_file)
    if len(prompt) > MAX_PROMPT_CHARS:
        _warn(f"Prompt length {len(prompt)} exceeds recommended {MAX_PROMPT_CHARS} chars.")

    _validate_size(args.size)

    if args.n < 1 or args.n > DEFAULT_MAX_N:
        _die(f"--n must be 1-{DEFAULT_MAX_N} (got {args.n}).")

    if len(args.reference_image) > MAX_REFERENCE_IMAGES:
        _die(f"Maximum {MAX_REFERENCE_IMAGES} reference images (got {len(args.reference_image)}).")

    if args.sequential and (args.max_images < 1 or args.max_images > MAX_GROUP_IMAGES):
        _die(f"--max-images must be 1-{MAX_GROUP_IMAGES} (got {args.max_images}).")

    api_key, base_url = _get_api_settings()

    refs = _resolve_reference_images(args.reference_image) if args.reference_image else None

    body = _build_request_body(
        model=args.model,
        prompt=prompt,
        size=args.size,
        output_format=args.output_format if args.output_format != "jpg" else "jpeg",
        watermark=args.watermark,
        web_search=args.web_search,
        reference_images=refs,
        optimize_prompt=args.optimize_prompt,
        sequential=args.sequential,
        max_images=args.max_images,
    )

    # Dry-run
    if args.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        image_path = _make_output_path(prompt, args.out, args.out_dir)
        _write_metadata(
            image_path,
            prompt=prompt, model=args.model, size=args.size,
            output_format=args.output_format, watermark=args.watermark,
            web_search=args.web_search, reference_images=refs,
            optimize_prompt=args.optimize_prompt, base_url=base_url, dry_run=True,
        )
        return 0

    # For --n > 1, generate concurrently
    if args.n > 1:
        return asyncio.run(_generate_concurrent(args, body, api_key, base_url, prompt, refs))

    return asyncio.run(_generate_one(args, body, api_key, base_url, prompt, refs))


async def _generate_one(
    args: argparse.Namespace,
    body: dict[str, Any],
    api_key: str,
    base_url: str,
    prompt: str,
    refs: Optional[list[str]],
) -> int:
    try:
        images, revised_prompt, usage = await _generate_with_retry(
            api_key, base_url, body, args.timeout,
        )
    except _APIError as e:
        _die(f"API error {e.status_code}: {e.code} — {e.message}")

    for idx, img_bytes in enumerate(images):
        image_path = _make_output_path(prompt, args.out, args.out_dir, idx)
        if image_path.exists() and not args.force:
            _die(f"Output already exists: {image_path} (use --force to overwrite)")
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(img_bytes)
        print(f"Image: {image_path}")

        _write_metadata(
            image_path,
            prompt=prompt, model=args.model, size=args.size,
            output_format=args.output_format, watermark=args.watermark,
            web_search=args.web_search, reference_images=refs,
            optimize_prompt=args.optimize_prompt, base_url=base_url,
            dry_run=False, revised_prompt=revised_prompt, usage=usage,
        )

    return 0


async def _generate_concurrent(
    args: argparse.Namespace,
    body: dict[str, Any],
    api_key: str,
    base_url: str,
    prompt: str,
    refs: Optional[list[str]],
) -> int:
    """Run --n independent generations concurrently."""
    async def _run_one(i: int) -> tuple[int, list[bytes], Optional[str], Optional[dict], Optional[str]]:
        try:
            images, revised_prompt, usage = await _generate_with_retry(
                api_key, base_url, body.copy(), args.timeout,
            )
            return i, images, revised_prompt, usage, None
        except _APIError as e:
            return i, [], None, None, str(e)

    tasks = [_run_one(i) for i in range(args.n)]
    results = await asyncio.gather(*tasks)

    errors = 0
    for i, images, revised_prompt, usage, error in results:
        if error:
            print(f"Error (variant {i+1}/{args.n}): {error}", file=sys.stderr)
            errors += 1
            continue
        for j, img_bytes in enumerate(images):
            image_path = _make_output_path(prompt, args.out, args.out_dir, i * len(images) + j)
            if image_path.exists() and not args.force:
                _warn(f"Output exists, skipping: {image_path}")
                continue
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(img_bytes)
            print(f"Image: {image_path}")

            _write_metadata(
                image_path,
                prompt=prompt, model=args.model, size=args.size,
                output_format=args.output_format, watermark=args.watermark,
                web_search=args.web_search, reference_images=refs,
                optimize_prompt=args.optimize_prompt, base_url=base_url,
                dry_run=False, revised_prompt=revised_prompt, usage=usage,
            )

    if errors == args.n:
        _die(f"All {args.n} concurrent generations failed.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: edit (alias for generate with reference image)
# ---------------------------------------------------------------------------


def _add_edit_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("edit", help="Create an image based on reference images (alias for generate --reference-image).")
    p.add_argument("--prompt", "-p", required=True, help="Text description for the edit.")
    p.add_argument("--prompt-file", help="Read prompt from a UTF-8 file (mutually exclusive with --prompt).")
    p.add_argument("--reference-image", action="append", required=True, help="Reference image(s) path or URL (repeatable, max 14).")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL}).")
    p.add_argument("--size", default="2048x2048", help="Image size: 2K, 3K, 4K, or WIDTHxHEIGHT.")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "jpg"], help="Output image format.")
    p.add_argument("--out", help="Output file path.")
    p.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).")
    p.add_argument("--web-search", action="store_true", default=True, help="Enable web search. Enabled by default.")
    p.add_argument("--no-web-search", action="store_false", dest="web_search", help="Disable web search.")
    p.add_argument("--watermark", action="store_true", help="Include Seedream watermark.")
    p.add_argument("--optimize-prompt", choices=["standard", "fast"], help="Enable prompt optimization.")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true", help="Print the request body and exit without calling the API.")
    p.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    p.set_defaults(func=_cmd_edit)


def _cmd_edit(args: argparse.Namespace) -> int:
    # edit is an alias for generate with required reference images
    if not args.reference_image:
        _die("--reference-image is required for edit subcommand.")
    # Ensure generate-only attrs have defaults
    for attr, default in [("n", 1), ("sequential", False), ("max_images", 4)]:
        if not hasattr(args, attr):
            setattr(args, attr, default)
    return _cmd_generate(args)


# ---------------------------------------------------------------------------
# Subcommand: generate-batch
# ---------------------------------------------------------------------------


def _add_batch_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("generate-batch", help="Run many generation jobs from a JSONL file.")
    p.add_argument("--input", required=True, help="Path to JSONL file. Each line: bare string (prompt) or JSON object (prompt + overrides).")
    p.add_argument("--out-dir", default=f"{DEFAULT_OUTPUT_DIR}/batch", help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}/batch).")
    p.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help=f"Max concurrent requests (default: {DEFAULT_CONCURRENCY}).")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL}).")
    p.add_argument("--size", default="2048x2048", help="Default image size.")
    p.add_argument("--output-format", default=DEFAULT_OUTPUT_FORMAT, choices=["png", "jpeg", "jpg"], help="Default output image format.")
    p.add_argument("--web-search", action="store_true", default=True, help="Enable web search. Enabled by default.")
    p.add_argument("--no-web-search", action="store_false", dest="web_search", help="Disable web search.")
    p.add_argument("--watermark", action="store_true", help="Include Seedream watermark.")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT}).")
    p.add_argument("--dry-run", action="store_true", help="Print all request bodies and exit without calling the API.")
    p.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    p.set_defaults(func=_cmd_batch)


def _parse_jsonl(path: str) -> list[dict[str, Any]]:
    """Parse a JSONL file. Each line is a bare string (prompt) or JSON object."""
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
            # Try as bare string
            line = line.strip('"').strip("'").strip()
            data = line

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
    api_key, base_url = _get_api_settings()

    # Build bodies for each job, merging with CLI defaults
    bodies: list[tuple[str, dict[str, Any]]] = []
    for i, job in enumerate(jobs):
        prompt = job["prompt"]
        body = _build_request_body(
            model=job.get("model", args.model),
            prompt=prompt,
            size=job.get("size", args.size),
            output_format=job.get("output_format", args.output_format),
            watermark=job.get("watermark", args.watermark),
            web_search=job.get("web_search", args.web_search),
            reference_images=job.get("reference_image") if job.get("reference_image") else None,
            optimize_prompt=job.get("optimize_prompt"),
            sequential=job.get("sequential_image_generation") == "auto",
            max_images=job.get("max_images", 4),
        )
        bodies.append((prompt, body))

    if args.dry_run:
        for i, (prompt, body) in enumerate(bodies):
            print(f"\n--- Job {i+1} ---")
            print(json.dumps(body, ensure_ascii=False, indent=2))
        return 0

    return asyncio.run(_run_batch(args, bodies, api_key, base_url))


async def _run_batch(
    args: argparse.Namespace,
    bodies: list[tuple[str, dict[str, Any]]],
    api_key: str,
    base_url: str,
) -> int:
    sem = asyncio.Semaphore(args.concurrency)

    async def _run_job(index: int, prompt: str, body: dict[str, Any]) -> bool:
        async with sem:
            try:
                images, revised_prompt, usage = await _generate_with_retry(
                    api_key, base_url, body, args.timeout,
                )
                for j, img_bytes in enumerate(images):
                    stem = _slugify(prompt, max_len=30)
                    out_dir = Path(args.out_dir).expanduser().resolve()
                    out_dir.mkdir(parents=True, exist_ok=True)
                    image_path = out_dir / f"job-{index+1:03d}-{stem}-{j+1}.png"
                    if image_path.exists() and not args.force:
                        _warn(f"Output exists, skipping: {image_path}")
                        continue
                    image_path.write_bytes(img_bytes)
                    print(f"[{index+1}/{len(bodies)}] Image: {image_path}")

                    _write_metadata(
                        image_path,
                        prompt=prompt, model=body["model"], size=body["size"],
                        output_format=body.get("output_format", args.output_format),
                        watermark=body.get("watermark", args.watermark),
                        web_search="tools" in body,
                        reference_images=body.get("image"),
                        optimize_prompt=body.get("optimize_prompt_options", {}).get("mode"),
                        base_url=base_url, dry_run=False,
                        revised_prompt=revised_prompt, usage=usage,
                    )
                return True
            except _APIError as e:
                print(f"[{index+1}/{len(bodies)}] Error: {e.code} — {e.message}", file=sys.stderr)
                return False

    tasks = [_run_job(i, prompt, body) for i, (prompt, body) in enumerate(bodies)]
    results = await asyncio.gather(*tasks)

    successes = sum(1 for r in results if r)
    failures = len(results) - successes
    print(f"\nBatch complete: {successes} success, {failures} failed", file=sys.stderr)
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> int:
    _load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate images with Seedream 5.0 via Volcengine Ark API.\n"
                    "API docs: https://www.volcengine.com/docs/82379/1824121?lang=zh",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands.")
    _add_generate_parser(subparsers)
    _add_edit_parser(subparsers)
    _add_batch_parser(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
