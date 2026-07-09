#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "openai>=1.76.0",
#   "pillow>=10.0.0",
# ]
# ///
"""Generate, edit, and batch-generate images with OpenAI's gpt-image-2.

Subcommands:
  generate         Create a new image from a prompt.
  edit             Modify one or more existing images.
  generate-batch   Run many generation jobs from a JSONL file.

Defaults to gpt-image-2. Sibling *.json metadata is written next to each output.
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
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gpt-image-2"
DEFAULT_OUTPUT_PATH = "output/gpt-image-2/output.png"
DEFAULT_OUTPUT_DIR = "output/gpt-image-2"
DEFAULT_TMP_DIR = "tmp/gpt-image-2"
DEFAULT_QUALITY = "auto"
DEFAULT_OUTPUT_FORMAT = "png"
DEFAULT_CONCURRENCY = 5
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_DOWNSCALE_SUFFIX = "-web"
DEFAULT_DRY_RUN_OUTPUT_DIR = "tmp/gpt-image-2/dry-run"

ALLOWED_QUALITIES = {"low", "medium", "high", "auto"}
ALLOWED_OUTPUT_FORMATS = {"png", "jpeg", "jpg", "webp"}
ALLOWED_MODERATION = {"auto", "low"}

# OpenAI supports `transparent` on the API, but the gpt-image-2 cookbook recommends
# generating opaque outputs and using a downstream background-removal step for best
# results. We allow `transparent` but warn so users know the recommendation.
SUPPORTED_BACKGROUNDS = {"transparent", "opaque", "auto", None}

# size preset table (validated against gpt-image-2 hard constraints)
SIZE_PRESETS: dict[str, Optional[str]] = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "wide": "1792x1024",
    "2k-landscape": "2048x1152",
    "4k-landscape": "3840x2160",
    "auto": "auto",
}

# OpenAI cookbook's standard enum values plus auto.
STANDARD_SIZE_ENUMS = {
    "auto",
    "1024x1024",
    "1024x1536",
    "1024x1792",
    "1536x1024",
    "1536x864",
    "1792x1024",
    "2048x2048",
    "2048x1152",
    "3840x2160",
    "2160x3840",
}

SIZE_HARD_MAX_EDGE = 3840
SIZE_EXPERIMENTAL_MAX_EDGE = 2560
SIZE_MIN_PIXELS = 655_360
SIZE_MAX_PIXELS = 8_294_400

MAX_IMAGE_BYTES = 50 * 1024 * 1024
MAX_MASK_BYTES = 4 * 1024 * 1024
MAX_PROMPT_CHARS = 32_000
MAX_BATCH_JOBS = 500
MAX_N = 10
MAX_CONCURRENCY = 25
MAX_ATTEMPTS_LIMIT = 10

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _load_dotenv() -> None:
    """Load .env from the current working directory if it exists.

    Only sets values not already in the environment. Comments and blank lines
    are ignored. Quoted values are stripped of matching outer quotes.
    """
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


def _dependency_hint(package: str) -> str:
    return (
        "Install it in this skill's environment with: "
        "`uv run` auto-installs PEP 723 dependencies."
    )


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:60] if value else "job"


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Auth & model resolution
# ---------------------------------------------------------------------------


def get_api_settings(require_key: bool) -> tuple[Optional[str], Optional[str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    if api_key:
        return api_key, base_url
    if not require_key:
        return None, base_url
    if sys.stdin.isatty() and sys.stderr.isatty():
        try:
            api_key = getpass.getpass("OPENAI_API_KEY is missing. Enter a temporary key: ").strip()
        except (EOFError, KeyboardInterrupt):
            api_key = None
        if api_key:
            return api_key, base_url
    _die(
        "OPENAI_API_KEY is required. Set it in your shell or .env, for example:\n"
        "  export OPENAI_API_KEY='sk-...'\n"
        "  export OPENAI_BASE_URL='https://your-proxy.example/v1'  # optional"
    )
    return None, None  # unreachable


def resolve_model_name(base_url: Optional[str], override: Optional[str] = None) -> str:
    """Resolve the gpt-image-2 model identifier for the current base URL.

    Default: gpt-image-2. Some OpenAI-compatible gateways expect a vendor prefix.
    """
    if override:
        return override
    if not base_url:
        return DEFAULT_MODEL
    normalized = base_url.rstrip("/").lower()
    if normalized.startswith("https://api.ofox.io/v1"):
        return "openai/gpt-image-2"
    return DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Size validation
# ---------------------------------------------------------------------------


def _resolve_size(size: str) -> str:
    if size in SIZE_PRESETS:
        resolved = SIZE_PRESETS[size]
        if resolved is None:
            _die(f"size preset {size!r} has no value.")
        return resolved
    return size


def _validate_size(size: str) -> None:
    resolved = _resolve_size(size)
    if resolved == "auto":
        return
    if resolved in STANDARD_SIZE_ENUMS:
        # Standard enums still need to be sanity-checked against the constraint grid.
        w, h = (int(v) for v in resolved.split("x"))
    else:
        m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", resolved)
        if not m:
            _die(
                f"size {resolved!r} is not a valid WIDTHxHEIGHT string or a known preset. "
                "Use 'auto', a preset name, or 'WIDTHxHEIGHT' (e.g. '1536x864')."
            )
        w, h = int(m.group(1)), int(m.group(2))
        if w % 16 != 0 or h % 16 != 0:
            _die(
                f"size {resolved!r}: both edges must be multiples of 16. "
                f"({w} and {h} are not; try {w - w % 16}x{h - h % 16} or nearest multiple of 16.)"
            )
        if min(w, h) <= 0:
            _die(f"size {resolved!r}: edges must be positive.")
    if max(w, h) > SIZE_HARD_MAX_EDGE:
        _die(f"size {resolved!r}: exceeds the {SIZE_HARD_MAX_EDGE}px max edge.")
    if max(w, h) > SIZE_EXPERIMENTAL_MAX_EDGE:
        _warn(
            f"size {resolved!r}: outputs above {SIZE_EXPERIMENTAL_MAX_EDGE}px on the long edge "
            "are flagged experimental by OpenAI."
        )
    aspect = max(w, h) / min(w, h)
    if aspect > 3.0:
        _die(
            f"size {resolved!r}: aspect ratio (long:short) is {aspect:.2f}:1, must be ≤ 3:1."
        )
    total = w * h
    if total < SIZE_MIN_PIXELS:
        _die(
            f"size {resolved!r}: total pixels {total} is below the minimum {SIZE_MIN_PIXELS}."
        )
    if total > SIZE_MAX_PIXELS:
        _die(
            f"size {resolved!r}: total pixels {total} exceeds the maximum {SIZE_MAX_PIXELS}."
        )


# ---------------------------------------------------------------------------
# Prompt / payload
# ---------------------------------------------------------------------------


def _read_prompt(prompt: Optional[str], prompt_file: Optional[str]) -> str:
    if prompt and prompt_file:
        _die("Use --prompt or --prompt-file, not both.")
    if prompt_file:
        path = Path(prompt_file)
        if not path.exists():
            _die(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    _die("Missing prompt. Use --prompt or --prompt-file.")
    return ""  # unreachable


def _validate_prompt_length(prompt: str) -> None:
    if len(prompt) > MAX_PROMPT_CHARS:
        _die(
            f"prompt length {len(prompt)} exceeds the {MAX_PROMPT_CHARS} character limit "
            "for GPT image models."
        )


def _fields_from_args(args: argparse.Namespace) -> dict[str, Optional[str]]:
    return {
        "use_case": getattr(args, "use_case", None),
        "scene": getattr(args, "scene", None),
        "subject": getattr(args, "subject", None),
        "style": getattr(args, "style", None),
        "composition": getattr(args, "composition", None),
        "lighting": getattr(args, "lighting", None),
        "palette": getattr(args, "palette", None),
        "materials": getattr(args, "materials", None),
        "text": getattr(args, "text", None),
        "constraints": getattr(args, "constraints", None),
        "negative": getattr(args, "negative", None),
    }


def _augment_prompt_fields(augment: bool, prompt: str, fields: dict[str, Optional[str]]) -> str:
    if not augment:
        return prompt
    sections: list[str] = []
    if fields.get("use_case"):
        sections.append(f"Use case: {fields['use_case']}")
    sections.append(f"Primary request: {prompt}")
    if fields.get("scene"):
        sections.append(f"Scene/backdrop: {fields['scene']}")
    if fields.get("subject"):
        sections.append(f"Subject: {fields['subject']}")
    if fields.get("style"):
        sections.append(f"Style/medium: {fields['style']}")
    if fields.get("composition"):
        sections.append(f"Composition/framing: {fields['composition']}")
    if fields.get("lighting"):
        sections.append(f"Lighting/mood: {fields['lighting']}")
    if fields.get("palette"):
        sections.append(f"Color palette: {fields['palette']}")
    if fields.get("materials"):
        sections.append(f"Materials/textures: {fields['materials']}")
    if fields.get("text"):
        sections.append(f"Text (verbatim): \"{fields['text']}\"")
    if fields.get("constraints"):
        sections.append(f"Constraints: {fields['constraints']}")
    if fields.get("negative"):
        sections.append(f"Avoid: {fields['negative']}")
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _check_image_paths(paths: Iterable[str], role: str) -> list[Path]:
    resolved: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            _die(f"{role} not found: {path}")
        size = path.stat().st_size
        if size > MAX_IMAGE_BYTES:
            _warn(f"{role} exceeds 50MB limit: {path} ({size} bytes)")
        if path.suffix.lower() not in {".png", ".webp", ".jpg", ".jpeg"}:
            _warn(f"{role} is not png/webp/jpg; the API may reject it: {path}")
        resolved.append(path)
    return resolved


def _check_mask_path(mask: Optional[str]) -> Optional[Path]:
    if not mask:
        return None
    path = Path(mask)
    if not path.exists():
        _die(f"Mask not found: {path}")
    if path.suffix.lower() != ".png":
        _warn(f"Mask should be a PNG with an alpha channel: {path}")
    if path.stat().st_size > MAX_MASK_BYTES:
        _warn(f"Mask exceeds 4MB soft limit: {path}")
    return path


def _normalize_output_format(fmt: Optional[str]) -> str:
    if not fmt:
        return DEFAULT_OUTPUT_FORMAT
    fmt = fmt.lower()
    if fmt not in ALLOWED_OUTPUT_FORMATS:
        _die("output-format must be png, jpeg, jpg, or webp.")
    return "jpeg" if fmt == "jpg" else fmt


def _validate_background(background: Optional[str]) -> None:
    if background not in SUPPORTED_BACKGROUNDS:
        _die("background must be one of transparent, opaque, auto, or unset.")
    if background == "transparent":
        _warn(
            "background=transparent is supported, but the gpt-image-2 cookbook recommends "
            "using background=opaque and a downstream `rembg` step for cleaner transparent assets."
        )


def _validate_transparency(background: Optional[str], output_format: str) -> None:
    if background == "transparent" and output_format not in {"png", "webp"}:
        _die("transparent background requires output-format png or webp.")


def _validate_quality(quality: str) -> None:
    if quality not in ALLOWED_QUALITIES:
        _die("quality must be one of low, medium, high, or auto.")


def _validate_moderation(moderation: Optional[str]) -> None:
    if moderation is None:
        return
    if moderation not in ALLOWED_MODERATION:
        _die("moderation must be one of auto or low.")


def _build_output_paths(
    out: str,
    output_format: str,
    count: int,
    out_dir: Optional[str],
) -> list[Path]:
    ext = "." + output_format

    if out_dir:
        out_base = Path(out_dir)
        out_base.mkdir(parents=True, exist_ok=True)
        return [out_base / f"image_{i}{ext}" for i in range(1, count + 1)]

    out_path = Path(out)
    if out_path.exists() and out_path.is_dir():
        out_path.mkdir(parents=True, exist_ok=True)
        return [out_path / f"image_{i}{ext}" for i in range(1, count + 1)]

    if out_path.suffix == "":
        out_path = out_path.with_suffix(ext)
    elif output_format and out_path.suffix.lstrip(".").lower() != output_format:
        _warn(
            f"Output extension {out_path.suffix} does not match output-format {output_format}."
        )

    if count == 1:
        return [out_path]

    return [
        out_path.with_name(f"{out_path.stem}-{i}{out_path.suffix}")
        for i in range(1, count + 1)
    ]


def _derive_downscale_path(path: Path, suffix: str) -> Path:
    if suffix and not suffix.startswith("-") and not suffix.startswith("_"):
        suffix = "-" + suffix
    return path.with_name(f"{path.stem}{suffix}{path.suffix}")


def _downscale_image_bytes(
    image_bytes: bytes, *, max_dim: int, output_format: str
) -> bytes:
    try:
        from PIL import Image
    except Exception:
        _die(f"Downscaling requires Pillow. {_dependency_hint('pillow')}")

    if max_dim < 1:
        _die("--downscale-max-dim must be >= 1")

    with Image.open(BytesIO(image_bytes)) as img:
        img.load()
        w, h = img.size
        scale = min(1.0, float(max_dim) / float(max(w, h)))
        target = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
        resized = img if target == (w, h) else img.resize(target, Image.Resampling.LANCZOS)

        fmt = output_format.lower()
        if fmt == "jpg":
            fmt = "jpeg"

        if fmt == "jpeg":
            if resized.mode in ("RGBA", "LA") or (
                "transparency" in getattr(resized, "info", {})
            ):
                bg = Image.new("RGB", resized.size, (255, 255, 255))
                bg.paste(
                    resized.convert("RGBA"),
                    mask=resized.convert("RGBA").split()[-1],
                )
                resized = bg
            else:
                resized = resized.convert("RGB")

        out = BytesIO()
        resized.save(out, format=fmt.upper())
        return out.getvalue()


def _decode_and_write(
    images: list[str],
    outputs: list[Path],
    *,
    force: bool,
    downscale_max_dim: Optional[int],
    downscale_suffix: str,
    output_format: str,
    write_metadata: bool = True,
    metadata_factory: Optional[Any] = None,
) -> None:
    for idx, image_b64 in enumerate(images):
        if idx >= len(outputs):
            break
        out_path = outputs[idx]
        if out_path.exists() and not force:
            _die(f"Output already exists: {out_path} (use --force to overwrite)")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw = base64.b64decode(image_b64)
        out_path.write_bytes(raw)
        print(f"Wrote {out_path}", file=sys.stderr)

        if downscale_max_dim is not None:
            derived = _derive_downscale_path(out_path, downscale_suffix)
            if derived.exists() and not force:
                _die(
                    f"Output already exists: {derived} (use --force to overwrite)"
                )
            derived.parent.mkdir(parents=True, exist_ok=True)
            resized = _downscale_image_bytes(
                raw, max_dim=downscale_max_dim, output_format=output_format
            )
            derived.write_bytes(resized)
            print(f"Wrote {derived}", file=sys.stderr)

        if write_metadata and metadata_factory is not None:
            meta = metadata_factory(idx, out_path)
            meta_path = out_path.with_suffix(".json")
            if meta_path.exists() and not force:
                _die(
                    f"Metadata already exists: {meta_path} (use --force to overwrite)"
                )
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"Wrote {meta_path}", file=sys.stderr)


def _print_request(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# Error classification and retry
# ---------------------------------------------------------------------------


def _extract_error_code(exc: Exception) -> Optional[str]:
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and isinstance(err.get("code"), str):
            return err["code"]
    return None


def _extract_moderation_details(exc: Exception) -> Optional[dict]:
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and isinstance(err.get("moderation_details"), dict):
            return err["moderation_details"]
    return None


def _classify_error(exc: Exception) -> str:
    """Return one of: 'transient', 'user_error', 'moderation', 'unknown'."""
    code = _extract_error_code(exc)
    if code is None:
        return "unknown"
    code_lower = code.lower()
    if code_lower in {
        "rate_limit_exceeded",
        "internal_server_error",
        "service_unavailable",
    }:
        return "transient"
    if code_lower in {"moderation_blocked", "content_policy_violation"}:
        return "moderation"
    if code_lower in {
        "image_generation_user_error",
        "invalid_request_error",
        "bad_request",
    }:
        return "user_error"
    if "429" in str(exc) or "5" in code_lower[:1] and code_lower[1:].isdigit():
        return "transient"
    return "unknown"


def _is_retryable_error(exc: Exception) -> bool:
    name = exc.__class__.__name__.lower()
    if "ratelimit" in name or "rate_limit" in name:
        return True
    if "timeout" in name or "timedout" in name:
        return True
    classification = _classify_error(exc)
    if classification == "transient":
        return True
    if classification in {"user_error", "moderation"}:
        return False
    # unknown: do not retry by default
    return False


def _print_error_diagnostics(exc: Exception) -> None:
    code = _extract_error_code(exc)
    classification = _classify_error(exc)
    print(f"Error code: {code or '<unknown>'}", file=sys.stderr)
    print(f"Error classification: {classification}", file=sys.stderr)
    print(f"Error message: {exc}", file=sys.stderr)
    if classification == "moderation":
        details = _extract_moderation_details(exc)
        if details:
            print(
                f"Moderation stage: {details.get('moderation_stage', 'unknown')}",
                file=sys.stderr,
            )
            categories = details.get("categories")
            if categories:
                print(f"Moderation categories: {categories}", file=sys.stderr)
        else:
            print(
                "No moderation_details returned. Treat the request body as the source of truth.",
                file=sys.stderr,
            )


def _extract_retry_after_seconds(exc: Exception) -> Optional[float]:
    for attr in ("retry_after", "retry_after_seconds"):
        val = getattr(exc, attr, None)
        if isinstance(val, (int, float)) and val >= 0:
            return float(val)
    msg = str(exc)
    m = re.search(r"retry[- ]after[:= ]+([0-9]+(?:\.[0-9]+)?)", msg, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------


def _create_client(api_key: Optional[str], base_url: Optional[str]) -> Any:
    try:
        from openai import OpenAI
    except ImportError:
        _die(
            "openai SDK is not installed. " + _dependency_hint("openai")
        )
    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def _create_async_client(api_key: Optional[str], base_url: Optional[str]) -> Any:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        _die(
            "openai SDK is not installed. " + _dependency_hint("openai")
        )
    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _progress_every_seconds() -> float:
    return 15.0


async def _call_with_progress(
    coro_factory: Any, label: str, started_at: float
) -> Any:
    """Run a coroutine while emitting elapsed-time progress on stderr."""
    task = asyncio.create_task(coro_factory())
    next_emit = started_at + _progress_every_seconds()
    while not task.done():
        await asyncio.sleep(0.5)
        now = time.time()
        if now >= next_emit:
            elapsed = now - started_at
            print(f"{label} still running ({elapsed:.0f}s elapsed)", file=sys.stderr)
            next_emit = now + _progress_every_seconds()
    return await task


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------


def _build_generate_payload(
    args: argparse.Namespace, prompt: str, model_name: str
) -> dict[str, Any]:
    fields = _fields_from_args(args)
    augmented = _augment_prompt_fields(args.augment, prompt, fields)
    _validate_prompt_length(augmented)

    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": augmented,
        "n": args.n,
        "size": _resolve_size(args.size),
        "quality": args.quality,
    }
    if args.background is not None:
        payload["background"] = args.background
    if args.output_format is not None:
        payload["output_format"] = _normalize_output_format(args.output_format)
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    if args.moderation is not None:
        payload["moderation"] = args.moderation
    return payload


def _generate(args: argparse.Namespace) -> int:
    prompt = _read_prompt(args.prompt, args.prompt_file)
    _validate_size(args.size)
    _validate_quality(args.quality)
    _validate_background(args.background)
    _validate_moderation(args.moderation)

    api_key, base_url = get_api_settings(require_key=not args.dry_run)
    model_name = resolve_model_name(base_url, args.model)
    payload = _build_generate_payload(args, prompt, model_name)
    output_format = _normalize_output_format(args.output_format)
    _validate_transparency(args.background, output_format)
    payload["output_format"] = output_format
    output_paths = _build_output_paths(args.out, output_format, args.n, args.out_dir)
    downscaled = (
        [str(_derive_downscale_path(p, args.downscale_suffix)) for p in output_paths]
        if args.downscale_max_dim is not None
        else None
    )

    if args.dry_run:
        _print_request(
            {
                "endpoint": "/v1/images/generations",
                "model_resolved": model_name,
                "base_url": base_url,
                "outputs": [str(p) for p in output_paths],
                "outputs_downscaled": downscaled,
                **payload,
            }
        )
        return 0

    print("Calling Image API (generate). Complex prompts can take up to 2 minutes.", file=sys.stderr)
    client = _create_client(api_key, base_url)
    started = time.time()
    try:
        result = client.images.generate(**payload)
    except Exception as exc:
        _print_error_diagnostics(exc)
        if not _is_retryable_error(exc):
            return 1
        raise
    elapsed = time.time() - started
    print(f"Generation completed in {elapsed:.1f}s.", file=sys.stderr)

    images = [item.b64_json for item in result.data]
    if not images:
        _die("API returned no images.")

    def _meta(idx: int, path: Path) -> dict:
        return {
            "title": args.title,
            "prompt": payload["prompt"],
            "model": model_name,
            "base_url": base_url,
            "size": payload["size"],
            "quality": payload["quality"],
            "background": payload.get("background"),
            "output_format": output_format,
            "n": args.n,
            "image_path": str(path),
            "downscale_path": (
                str(_derive_downscale_path(path, args.downscale_suffix))
                if args.downscale_max_dim is not None
                else None
            ),
            "downscale_max_dim": args.downscale_max_dim,
            "reference_images": [],
            "created_at": _now_iso(),
            "dry_run": False,
        }

    _decode_and_write(
        images,
        output_paths,
        force=args.force,
        downscale_max_dim=args.downscale_max_dim,
        downscale_suffix=args.downscale_suffix,
        output_format=output_format,
        write_metadata=True,
        metadata_factory=_meta,
    )
    return 0


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------


def _open_files(paths: list[Path]) -> Any:
    """Return a context manager that opens all paths and yields a list of file handles."""
    return _FileBundle(paths)


def _open_mask(mask_path: Optional[Path]) -> Any:
    if mask_path is None:
        return _NullContext()
    return _SingleFile(mask_path)


class _NullContext:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


class _SingleFile:
    def __init__(self, path: Path):
        self._path = path
        self._handle: Any = None

    def __enter__(self):
        self._handle = self._path.open("rb")
        return self._handle

    def __exit__(self, exc_type, exc, tb):
        if self._handle:
            try:
                self._handle.close()
            except Exception:
                pass
        return False


class _FileBundle:
    def __init__(self, paths: list[Path]):
        self._paths = paths
        self._handles: list[Any] = []

    def __enter__(self):
        self._handles = [p.open("rb") for p in self._paths]
        return self._handles

    def __exit__(self, exc_type, exc, tb):
        for h in self._handles:
            try:
                h.close()
            except Exception:
                pass
        return False


def _build_edit_payload(
    args: argparse.Namespace, prompt: str, model_name: str
) -> dict[str, Any]:
    fields = _fields_from_args(args)
    augmented = _augment_prompt_fields(args.augment, prompt, fields)
    _validate_prompt_length(augmented)

    payload: dict[str, Any] = {
        "model": model_name,
        "prompt": augmented,
        "n": args.n,
        "size": _resolve_size(args.size),
        "quality": args.quality,
    }
    if args.background is not None:
        payload["background"] = args.background
    if args.output_format is not None:
        payload["output_format"] = _normalize_output_format(args.output_format)
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    if args.moderation is not None:
        payload["moderation"] = args.moderation
    return payload


def _edit(args: argparse.Namespace) -> int:
    prompt = _read_prompt(args.prompt, args.prompt_file)
    if not args.image:
        _die("edit requires at least one --image.")
    if len(args.image) > 16:
        _die(
            f"edit accepts up to 16 reference images; got {len(args.image)}. "
            "Drop some or split into multiple edits."
        )
    image_paths = _check_image_paths(args.image, role="image")
    mask_path = _check_mask_path(args.mask)
    _validate_size(args.size)
    _validate_quality(args.quality)
    _validate_background(args.background)
    _validate_moderation(args.moderation)

    api_key, base_url = get_api_settings(require_key=not args.dry_run)
    model_name = resolve_model_name(base_url, args.model)
    payload = _build_edit_payload(args, prompt, model_name)
    output_format = _normalize_output_format(args.output_format)
    _validate_transparency(args.background, output_format)
    payload["output_format"] = output_format
    output_paths = _build_output_paths(args.out, output_format, args.n, args.out_dir)
    downscaled = (
        [str(_derive_downscale_path(p, args.downscale_suffix)) for p in output_paths]
        if args.downscale_max_dim is not None
        else None
    )

    if args.dry_run:
        preview = dict(payload)
        preview["image"] = [str(p) for p in image_paths]
        if mask_path:
            preview["mask"] = str(mask_path)
        _print_request(
            {
                "endpoint": "/v1/images/edits",
                "model_resolved": model_name,
                "base_url": base_url,
                "outputs": [str(p) for p in output_paths],
                "outputs_downscaled": downscaled,
                **preview,
            }
        )
        return 0

    print(
        f"Calling Image API (edit) with {len(image_paths)} image(s). "
        "Complex prompts can take up to 2 minutes.",
        file=sys.stderr,
    )
    client = _create_client(api_key, base_url)
    started = time.time()
    try:
        with _open_files(image_paths) as image_files, _open_mask(mask_path) as mask_file:
            request = dict(payload)
            request["image"] = image_files if len(image_files) > 1 else image_files[0]
            if mask_file is not None:
                request["mask"] = mask_file
            result = client.images.edit(**request)
    except Exception as exc:
        _print_error_diagnostics(exc)
        if not _is_retryable_error(exc):
            return 1
        raise
    elapsed = time.time() - started
    print(f"Edit completed in {elapsed:.1f}s.", file=sys.stderr)

    images = [item.b64_json for item in result.data]
    if not images:
        _die("API returned no images.")

    def _meta(idx: int, path: Path) -> dict:
        return {
            "title": args.title,
            "prompt": payload["prompt"],
            "model": model_name,
            "base_url": base_url,
            "size": payload["size"],
            "quality": payload["quality"],
            "background": payload.get("background"),
            "output_format": output_format,
            "n": args.n,
            "image_path": str(path),
            "downscale_path": (
                str(_derive_downscale_path(path, args.downscale_suffix))
                if args.downscale_max_dim is not None
                else None
            ),
            "downscale_max_dim": args.downscale_max_dim,
            "reference_images": [str(p) for p in image_paths],
            "mask": str(mask_path) if mask_path else None,
            "created_at": _now_iso(),
            "dry_run": False,
        }

    _decode_and_write(
        images,
        output_paths,
        force=args.force,
        downscale_max_dim=args.downscale_max_dim,
        downscale_suffix=args.downscale_suffix,
        output_format=output_format,
        write_metadata=True,
        metadata_factory=_meta,
    )
    return 0


# ---------------------------------------------------------------------------
# generate-batch
# ---------------------------------------------------------------------------


def _normalize_job(job: Any, idx: int) -> dict[str, Any]:
    if isinstance(job, str):
        prompt = job.strip()
        if not prompt:
            _die(f"Empty prompt at job {idx}")
        return {"prompt": prompt}
    if isinstance(job, dict):
        if "prompt" not in job or not str(job["prompt"]).strip():
            _die(f"Missing prompt for job {idx}")
        return job
    _die(f"Invalid job at index {idx}: expected string or object.")
    return {}


def _read_jobs_jsonl(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        _die(f"Input file not found: {p}")
    jobs: list[dict[str, Any]] = []
    for line_no, raw in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            item: Any
            if line.startswith("{"):
                item = json.loads(line)
            else:
                item = line
            jobs.append(_normalize_job(item, idx=line_no))
        except json.JSONDecodeError as exc:
            _die(f"Invalid JSON on line {line_no}: {exc}")
    if not jobs:
        _die("No jobs found in input file.")
    if len(jobs) > MAX_BATCH_JOBS:
        _die(f"Too many jobs ({len(jobs)}). Max is {MAX_BATCH_JOBS}.")
    return jobs


def _merge_non_null(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    merged = dict(dst)
    for k, v in src.items():
        if v is not None:
            merged[k] = v
    return merged


def _job_output_paths(
    *,
    out_dir: Path,
    output_format: str,
    idx: int,
    prompt: str,
    n: int,
    explicit_out: Optional[str],
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "." + output_format

    if explicit_out:
        base = Path(explicit_out)
        if base.suffix == "":
            base = base.with_suffix(ext)
        elif base.suffix.lstrip(".").lower() != output_format:
            _warn(
                f"Job {idx}: output extension {base.suffix} does not match output-format {output_format}."
            )
        base = out_dir / base.name
    else:
        slug = _slugify(prompt[:80])
        base = out_dir / f"{idx:03d}-{slug}{ext}"

    if n == 1:
        return [base]
    return [
        base.with_name(f"{base.stem}-{i}{base.suffix}")
        for i in range(1, n + 1)
    ]


async def _generate_one_with_retries(
    client: Any,
    payload: dict[str, Any],
    *,
    attempts: int,
    job_label: str,
) -> Any:
    last_exc: Optional[Exception] = None
    for attempt in range(1, attempts + 1):
        try:
            return await _call_with_progress(
                lambda: client.images.generate(**payload),
                job_label,
                started_at=time.time(),
            )
        except Exception as exc:
            last_exc = exc
            if not _is_retryable_error(exc):
                _print_error_diagnostics(exc)
                raise
            if attempt == attempts:
                _print_error_diagnostics(exc)
                raise
            sleep_s = _extract_retry_after_seconds(exc)
            if sleep_s is None:
                sleep_s = min(60.0, 2.0**attempt)
            print(
                f"{job_label} attempt {attempt}/{attempts} failed "
                f"({exc.__class__.__name__}); retrying in {sleep_s:.1f}s",
                file=sys.stderr,
            )
            await asyncio.sleep(sleep_s)
    raise last_exc or RuntimeError("unknown error")


async def _run_generate_batch(args: argparse.Namespace) -> int:
    jobs = _read_jobs_jsonl(args.input)
    out_dir = Path(args.out_dir)

    base_fields = _fields_from_args(args)
    base_payload: dict[str, Any] = {
        "model": args.model,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
    }
    if args.background is not None:
        base_payload["background"] = args.background
    if args.output_format is not None:
        base_payload["output_format"] = args.output_format
    if args.output_compression is not None:
        base_payload["output_compression"] = args.output_compression
    if args.moderation is not None:
        base_payload["moderation"] = args.moderation

    if args.dry_run:
        for i, job in enumerate(jobs, start=1):
            prompt = str(job["prompt"]).strip()
            fields = _merge_non_null(base_fields, job.get("fields", {}))
            fields = _merge_non_null(fields, {k: job.get(k) for k in base_fields.keys()})
            augmented = _augment_prompt_fields(args.augment, prompt, fields)
            _validate_prompt_length(augmented)
            _validate_size(str(job.get("size", args.size)))

            job_payload = dict(base_payload)
            job_payload["prompt"] = augmented
            job_payload = _merge_non_null(
                job_payload,
                {k: job.get(k) for k in base_payload.keys()},
            )
            job_payload = {k: v for k, v in job_payload.items() if v is not None}
            job_payload["size"] = _resolve_size(str(job_payload["size"]))
            effective_output_format = _normalize_output_format(
                job_payload.get("output_format")
            )
            job_payload["output_format"] = effective_output_format
            _validate_background(job_payload.get("background"))
            _validate_transparency(job_payload.get("background"), effective_output_format)
            _validate_quality(str(job_payload.get("quality", DEFAULT_QUALITY)))
            _validate_moderation(job_payload.get("moderation"))

            n = int(job_payload.get("n", 1))
            outputs = _job_output_paths(
                out_dir=out_dir,
                output_format=effective_output_format,
                idx=i,
                prompt=prompt,
                n=n,
                explicit_out=job.get("out"),
            )
            downscaled = (
                [str(_derive_downscale_path(p, args.downscale_suffix)) for p in outputs]
                if args.downscale_max_dim is not None
                else None
            )
            _print_request(
                {
                    "endpoint": "/v1/images/generations",
                    "job": i,
                    "outputs": [str(p) for p in outputs],
                    "outputs_downscaled": downscaled,
                    **job_payload,
                }
            )
        return 0

    api_key, base_url = get_api_settings(require_key=True)
    model_name = resolve_model_name(base_url, args.model)
    client = _create_async_client(api_key, base_url)
    sem = asyncio.Semaphore(args.concurrency)
    any_failed = False

    async def run_job(i: int, job: dict[str, Any]) -> tuple[int, Optional[str]]:
        nonlocal any_failed
        prompt = str(job["prompt"]).strip()
        job_label = f"[job {i}/{len(jobs)}]"

        fields = _merge_non_null(base_fields, job.get("fields", {}))
        fields = _merge_non_null(fields, {k: job.get(k) for k in base_fields.keys()})
        augmented = _augment_prompt_fields(args.augment, prompt, fields)
        _validate_prompt_length(augmented)
        _validate_size(str(job.get("size", args.size)))

        payload = dict(base_payload)
        payload["prompt"] = augmented
        payload = _merge_non_null(
            payload, {k: job.get(k) for k in base_payload.keys()}
        )
        payload = {k: v for k, v in payload.items() if v is not None}
        payload["size"] = _resolve_size(str(payload["size"]))
        effective_output_format = _normalize_output_format(
            payload.get("output_format")
        )
        payload["output_format"] = effective_output_format
        _validate_background(payload.get("background"))
        _validate_transparency(payload.get("background"), effective_output_format)
        _validate_quality(str(payload.get("quality", DEFAULT_QUALITY)))
        _validate_moderation(payload.get("moderation"))
        payload["model"] = model_name

        n = int(payload.get("n", 1))
        outputs = _job_output_paths(
            out_dir=out_dir,
            output_format=effective_output_format,
            idx=i,
            prompt=prompt,
            n=n,
            explicit_out=job.get("out"),
        )
        try:
            async with sem:
                print(f"{job_label} starting", file=sys.stderr)
                started = time.time()
                result = await _generate_one_with_retries(
                    client,
                    payload,
                    attempts=args.max_attempts,
                    job_label=job_label,
                )
                elapsed = time.time() - started
                print(f"{job_label} completed in {elapsed:.1f}s", file=sys.stderr)
            images = [item.b64_json for item in result.data]
            if not images:
                raise RuntimeError("API returned no images.")

            def _meta(idx: int, path: Path, _payload=payload) -> dict:
                return {
                    "title": job.get("title", f"job-{i}"),
                    "prompt": _payload["prompt"],
                    "model": model_name,
                    "base_url": base_url,
                    "size": _payload["size"],
                    "quality": _payload.get("quality"),
                    "background": _payload.get("background"),
                    "output_format": effective_output_format,
                    "n": n,
                    "image_path": str(path),
                    "downscale_path": (
                        str(_derive_downscale_path(path, args.downscale_suffix))
                        if args.downscale_max_dim is not None
                        else None
                    ),
                    "downscale_max_dim": args.downscale_max_dim,
                    "reference_images": [],
                    "created_at": _now_iso(),
                    "dry_run": False,
                }

            _decode_and_write(
                images,
                outputs,
                force=args.force,
                downscale_max_dim=args.downscale_max_dim,
                downscale_suffix=args.downscale_suffix,
                output_format=effective_output_format,
                write_metadata=True,
                metadata_factory=_meta,
            )
            return i, None
        except Exception as exc:
            any_failed = True
            print(f"{job_label} failed: {exc}", file=sys.stderr)
            if args.fail_fast:
                raise
            return i, str(exc)

    tasks = [asyncio.create_task(run_job(i, job)) for i, job in enumerate(jobs, start=1)]
    try:
        await asyncio.gather(*tasks)
    except Exception:
        for t in tasks:
            if not t.done():
                t.cancel()
        raise
    return 1 if any_failed else 0


def _generate_batch(args: argparse.Namespace) -> int:
    exit_code = asyncio.run(_run_generate_batch(args))
    if exit_code:
        raise SystemExit(exit_code)
    return 0


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def _add_shared_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", default=None,
                        help=f"Override the model name. Default: {DEFAULT_MODEL} (or namespaced by BASE_URL).")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--title", default="gpt-image-2",
                        help="Used as a label in the metadata JSON.")
    parser.add_argument("--n", type=int, default=1, help=f"Number of images. 1-{MAX_N}.")
    parser.add_argument("--size", default="landscape",
                        help="Preset name or WIDTHxHEIGHT (e.g. 1536x864). Default: landscape.")
    parser.add_argument("--quality", default=DEFAULT_QUALITY,
                        help="low, medium, high, or auto. Use high for text-heavy images.")
    parser.add_argument(
        "--background",
        choices=["transparent", "opaque", "auto"],
        help=(
            "Output background. transparent is supported but the gpt-image-2 cookbook "
            "recommends opaque + a downstream rembg step for best results. "
            "transparent requires output-format png or webp."
        ),
    )
    parser.add_argument("--output-format", choices=["png", "jpeg", "jpg", "webp"],
                        help=f"Output container. Default: {DEFAULT_OUTPUT_FORMAT}.")
    parser.add_argument("--output-compression", type=int,
                        help="0-100. JPEG/WebP only.")
    parser.add_argument("--moderation", choices=["auto", "low"],
                        help="Moderation strictness. Default: auto.")
    parser.add_argument("--out", default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--out-dir")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the resolved request payload, never call the API.")
    parser.add_argument("--no-augment", dest="augment", action="store_false",
                        help="Skip prompt augmentation and send the prompt verbatim.")
    parser.set_defaults(augment=True)

    # Augmentation hints
    parser.add_argument("--use-case")
    parser.add_argument("--scene")
    parser.add_argument("--subject")
    parser.add_argument("--style")
    parser.add_argument("--composition")
    parser.add_argument("--lighting")
    parser.add_argument("--palette")
    parser.add_argument("--materials")
    parser.add_argument("--text")
    parser.add_argument("--constraints")
    parser.add_argument("--negative")

    # Optional downscaled copy
    parser.add_argument("--downscale-max-dim", type=int,
                        help="If set, also write a copy with the long edge ≤ N pixels.")
    parser.add_argument("--downscale-suffix", default=DEFAULT_DOWNSCALE_SUFFIX,
                        help=f"Suffix for the downscaled copy. Default: {DEFAULT_DOWNSCALE_SUFFIX}.")


def main() -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(
        description=(
            "Generate, edit, and batch-generate images with OpenAI's gpt-image-2 via the Image API. "
            "Use only the Image API; the /responses API is not used."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("generate", help="Create a new image")
    _add_shared_args(gen_parser)
    gen_parser.set_defaults(func=_generate)

    edit_parser = subparsers.add_parser("edit", help="Edit an existing image")
    _add_shared_args(edit_parser)
    edit_parser.add_argument("--image", action="append", required=True,
                             help="Repeatable. Up to 16 images. Order matters; reference by index in the prompt.")
    edit_parser.add_argument("--mask", help="Optional PNG with alpha channel.")
    edit_parser.set_defaults(func=_edit)

    batch_parser = subparsers.add_parser(
        "generate-batch", help="Run many generation jobs from a JSONL file"
    )
    _add_shared_args(batch_parser)
    batch_parser.add_argument("--input", required=True,
                              help="Path to JSONL. One job per line.")
    batch_parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    batch_parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    batch_parser.add_argument("--fail-fast", action="store_true")
    batch_parser.set_defaults(func=_generate_batch)

    args = parser.parse_args()

    # Global guards
    if args.n < 1 or args.n > MAX_N:
        _die(f"--n must be between 1 and {MAX_N}.")
    if args.output_compression is not None and not (0 <= args.output_compression <= 100):
        _die("--output-compression must be between 0 and 100.")
    if getattr(args, "concurrency", 1) < 1 or getattr(args, "concurrency", 1) > MAX_CONCURRENCY:
        _die(f"--concurrency must be between 1 and {MAX_CONCURRENCY}.")
    if getattr(args, "max_attempts", DEFAULT_MAX_ATTEMPTS) < 1 or getattr(
        args, "max_attempts", DEFAULT_MAX_ATTEMPTS
    ) > MAX_ATTEMPTS_LIMIT:
        _die(f"--max-attempts must be between 1 and {MAX_ATTEMPTS_LIMIT}.")
    if getattr(args, "downscale_max_dim", None) is not None and args.downscale_max_dim < 1:
        _die("--downscale-max-dim must be >= 1.")
    if args.command == "generate-batch" and not args.out_dir:
        _die("generate-batch requires --out-dir.")

    # In live mode, require auth before any deeper validation
    if not args.dry_run:
        get_api_settings(require_key=True)

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
