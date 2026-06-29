#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.28.0",
# ]
# ///

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_OUTPUT_DIR = os.environ.get("SEEDANCE_OUTPUT_DIR", os.path.join("output", "seedance"))
DEFAULT_POLL_INTERVAL = 20
DEFAULT_MAX_WAIT = 1800

# --- Retry config ---
# Submit/poll/list can hit 429 (rate limit) or 5xx (transient server error).
# Retry with exponential backoff, honoring Retry-After header when present.
# 4xx client errors are NOT retried.
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF_S = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0
RETRY_MAX_BACKOFF_S = 30.0
RETRY_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Input reference media size limits (per 官方 2298881, updated 2026-06-25).
# These are INPUT limits, not output video size limits.
# Output videos have no API size cap; only 24h URL validity matters.
MAX_IMAGE_BYTES = 30 * 1024 * 1024       # 30 MB
MAX_VIDEO_BYTES = 200 * 1024 * 1024      # 200 MB (URL/asset:// only; video does not support base64)
MAX_AUDIO_BYTES = 15 * 1024 * 1024       # 15 MB
# Total request body is 64 MB per the official spec. Base64 inflates ~33%,
# so a 48 MB raw video already becomes ~64 MB after encoding. We hard-fail
# at 60 MB estimated body to leave headroom for JSON wrapper + text prompt.
# Note: video does NOT support base64 transport per official spec, so this
# body-size guard mainly protects image/audio base64 payloads.
MAX_BODY_BYTES = 60 * 1024 * 1024        # 60 MB safety margin

# Seedance 2.0 series (the only line this script currently supports).
# - Standard (260128): 4k/1080p/720p/480p, all ratios incl. adaptive, audio.
# - Fast (260128): 720p/480p only (no 1080p, no 4k), cheaper and quicker.
# - Mini (260615): 720p/480p only; API GA on/after 2026-06-25.
# Resolution tiers that cap at 720p (no 1080p, no 4k):
VALID_MODELS = {
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
}
NO_1080P_MODELS = {
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
}
# Standard-only premium tier (4k):
NO_4K_MODELS = NO_1080P_MODELS  # fast + mini don't do 4k either
VALID_RATIOS = {"16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"}
VALID_RESOLUTIONS = {"480p", "720p", "1080p", "4k"}
SUPPORTED_IMAGE_ROLES = {"first_frame", "last_frame", "reference_image"}
SUPPORTED_VIDEO_ROLES = {"reference_video"}
SUPPORTED_AUDIO_ROLES = {"reference_audio"}
# Image formats accepted by Seedance 2.0 (HEIC/HEIF added 2026 on 2.0 + 1.5 pro):
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "heic", "heif"}
VIDEO_EXTS = {"mp4", "mov"}
AUDIO_EXTS = {"mp3", "wav"}

# --- Validation helpers (shared between build_payload and build_payload_from_shot) ---

def validate_model(model: str) -> None:
    if model not in VALID_MODELS:
        raise SystemExit(f"Error: unsupported model '{model}'. Valid: {sorted(VALID_MODELS)}")

def validate_duration(duration: int) -> None:
    if duration != -1 and not (4 <= duration <= 15):
        raise SystemExit("Error: duration must be between 4 and 15, or -1 for adaptive.")

def validate_ratio(ratio: str) -> None:
    if ratio not in VALID_RATIOS:
        raise SystemExit(f"Error: unsupported ratio '{ratio}'. Valid: {sorted(VALID_RATIOS)}")

def validate_resolution(model: str, resolution: str) -> None:
    if resolution not in VALID_RESOLUTIONS:
        raise SystemExit(f"Error: unsupported resolution '{resolution}'. Valid: {sorted(VALID_RESOLUTIONS)}")
    if resolution in {"1080p", "4k"} and model in NO_1080P_MODELS:
        raise SystemExit(
            f"Error: model '{model}' does not support {resolution} (capped at 720p). "
            f"Use --resolution 720p or 480p."
        )

def validate_web_search_mode(content: list[dict[str, Any]], enable_web_search: bool) -> None:
    if enable_web_search:
        non_text = [c for c in content if c.get("type") != "text"]
        if non_text:
            raise SystemExit(
                "Error: --enable-web-search requires pure text content. "
                f"Found {len(non_text)} non-text item(s); remove --first-frame/--last-frame/--reference-*."
            )


# --- Media handling (shared) ---

class MediaTracker:
    """Track total raw bytes of locally-loaded media for body-size estimation."""
    def __init__(self) -> None:
        self.raw_bytes: int = 0

# Per-type size limits for INPUT reference media (not output video).
# Sizes come from 官方视频生成教程 (doc 2298881, updated 2026-06-25):
#   - image: 30 MB
#   - video: 200 MB (URL/asset ID only — video does NOT support base64 per the
#     same doc, so large videos must be served from a public URL or asset://)
#   - audio: 15 MB
# Total request body ≤ 64 MB after base64; script hard-fails at 60 MB.
_SIZE_LIMITS: dict[str, int] = {
    "image_url": MAX_IMAGE_BYTES,
    "video_url": 200 * 1024 * 1024,
    "audio_url": MAX_AUDIO_BYTES,
}


def add_media_to_content(
    content: list[dict[str, Any]],
    tracker: MediaTracker,
    path_or_url: str,
    item_type: str,
    role: str,
    allowed_exts: set[str],
) -> None:
    """Append a media reference to content. Validates local file size; tracks total raw bytes."""
    if is_url(path_or_url):
        # URL size is server-side; we don't pre-validate. API will 400 if too big.
        content.append(build_content_item(item_type, path_or_url, role))
        return
    # Per 官方视频生成教程 (doc 2298881, updated 2026-06-25):
    #   - 图片支持 URL / Base64 / 素材 ID
    #   - 视频支持 URL / 素材 ID（**不支持 Base64**）
    #   - 音频支持 URL / Base64 / 素材 ID
    if item_type == "video_url":
        raise SystemExit(
            f"Error: local video files are not supported ({path_or_url}). "
            "Seedance 2.0 video inputs only accept public URLs or asset:// IDs (no base64). "
            "Upload the video to a public URL or TOS first."
        )
    local_path = validate_local_media(path_or_url, allowed_exts)
    size = local_path.stat().st_size
    limit = _SIZE_LIMITS.get(item_type)
    if limit and size > limit:
        mb = size / 1024 / 1024
        limit_mb = limit // (1024 * 1024)
        raise SystemExit(
            f"Error: {item_type.split('_')[0]} {local_path.name} is {mb:.1f} MB; "
            f"max {limit_mb} MB per the official input limit."
        )
    ext = local_path.suffix.lower().lstrip(".")
    mime_type = _media_mime(ext, item_type)
    file_bytes = local_path.read_bytes()
    b64 = base64.b64encode(file_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"
    content.append(build_content_item(item_type, data_url, role))
    tracker.raw_bytes += size


def check_total_body_size(content: list[dict[str, Any]], raw_bytes: int) -> None:
    """Hard-fail if estimated request body exceeds the 60 MB safety margin (official 64 MB)."""
    if raw_bytes <= 0:
        return
    # base64 inflates ~33%; +50 bytes per data URL prefix.
    estimated_body = raw_bytes * 4 // 3 + 50 * sum(1 for c in content if c.get("type") != "text")
    if estimated_body > MAX_BODY_BYTES:
        mb = estimated_body / 1024 / 1024
        raise SystemExit(
            f"Error: estimated request body is {mb:.1f} MB; "
            f"max {MAX_BODY_BYTES // (1024 * 1024)} MB (official 64 MB minus safety margin). "
            f"Reduce number of media files or pre-upload to a public URL."
        )



def _load_dotenv() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug or "seedance-video-gen"


def get_auth() -> tuple[str, str]:
    api_key = os.getenv("ARK_API_KEY", "")
    base_url = os.getenv("ARK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not api_key:
        raise SystemExit(
            "Error: ARK_API_KEY not found. Set it in your shell or .env file:\n"
            "  export ARK_API_KEY='sk-...'"
        )
    return api_key, base_url


def make_output_dir(output_dir: str, prompt: str) -> Path:
    today = dt.date.today().isoformat()
    short_slug = slugify(prompt)[:40]
    root = Path(output_dir).expanduser().resolve() / f"{today}-{short_slug}"
    counter = 0
    while True:
        candidate = root if counter == 0 else Path(f"{root}-{counter}")
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        counter += 1


def is_url(path_or_url: str) -> bool:
    """Return True for remote references: http(s):// URLs and asset:// URIs."""
    parsed = urlparse(path_or_url)
    if parsed.scheme in {"http", "https"}:
        return True
    if path_or_url.startswith("asset://"):
        return True
    return False


def validate_local_media(path: str, allowed_exts: set[str]) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SystemExit(f"Error: file not found: {p}")
    ext = p.suffix.lower().lstrip(".")
    if ext not in allowed_exts:
        raise SystemExit(
            f"Error: unsupported file extension '{ext}' for {p}. Allowed: {allowed_exts}"
        )
    return p


def build_content_item(
    item_type: str,
    url: str,
    role: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": item_type}
    if item_type == "text":
        payload["text"] = url
    elif item_type == "image_url":
        payload["image_url"] = {"url": url}
    elif item_type == "video_url":
        payload["video_url"] = {"url": url}
    elif item_type == "audio_url":
        payload["audio_url"] = {"url": url}
    else:
        raise ValueError(f"Unknown content type: {item_type}")
    if role:
        payload["role"] = role
    return payload


def validate_mode_constraints(content: list[dict[str, Any]]) -> None:
    roles = [item.get("role") for item in content if item.get("type") != "text"]
    has_first_last = any(r in {"first_frame", "last_frame"} for r in roles)
    has_reference = any(r and r.startswith("reference_") for r in roles)
    if has_first_last and has_reference:
        raise SystemExit(
            "Error: first/last frame mode and reference mode are mutually exclusive."
        )
    images = [r for r in roles if r in SUPPORTED_IMAGE_ROLES]
    videos = [r for r in roles if r in SUPPORTED_VIDEO_ROLES]
    audios = [r for r in roles if r in SUPPORTED_AUDIO_ROLES]
    if len(images) > 9:
        raise SystemExit("Error: at most 9 reference images allowed.")
    if len(videos) > 3:
        raise SystemExit("Error: at most 3 reference videos allowed.")
    if len(audios) > 3:
        raise SystemExit("Error: at most 3 reference audios allowed.")
    if len(images) + len(videos) + len(audios) > 12:
        raise SystemExit("Error: total reference media must be <= 12.")
    if audios and not (images or videos):
        raise SystemExit(
            "Error: audio reference requires at least one image or video reference."
        )


def _image_mime(ext: str) -> str:
    return {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
        "tiff": "image/tiff", "heic": "image/heic", "heif": "image/heif",
    }.get(ext, f"image/{ext}")


def _video_mime(ext: str) -> str:
    return {
        "mp4": "video/mp4", "mov": "video/quicktime",
    }.get(ext, f"video/{ext}")


def _audio_mime(ext: str) -> str:
    return {
        "mp3": "audio/mpeg", "wav": "audio/wav",
    }.get(ext, f"audio/{ext}")


def _media_mime(ext: str, item_type: str) -> str:
    if item_type == "image_url":
        return _image_mime(ext)
    if item_type == "video_url":
        return _video_mime(ext)
    if item_type == "audio_url":
        return _audio_mime(ext)
    return f"application/octet-stream"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    validate_model(args.model)
    validate_ratio(args.ratio)
    validate_resolution(args.model, args.resolution)
    validate_duration(args.duration)

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).expanduser().resolve().read_text(encoding="utf-8").strip()
    if not prompt:
        raise SystemExit("Error: provide --prompt or --prompt-file.")

    content: list[dict[str, Any]] = [build_content_item("text", prompt)]
    tracker = MediaTracker()

    if args.first_frame:
        add_media_to_content(content, tracker, args.first_frame, "image_url", "first_frame", IMAGE_EXTS)
    if args.last_frame:
        add_media_to_content(content, tracker, args.last_frame, "image_url", "last_frame", IMAGE_EXTS)
    for v in args.reference_image or []:
        add_media_to_content(content, tracker, v, "image_url", "reference_image", IMAGE_EXTS)
    for v in args.reference_video or []:
        add_media_to_content(content, tracker, v, "video_url", "reference_video", VIDEO_EXTS)
    for v in args.reference_audio or []:
        add_media_to_content(content, tracker, v, "audio_url", "reference_audio", AUDIO_EXTS)

    check_total_body_size(content, tracker.raw_bytes)
    validate_mode_constraints(content)
    validate_web_search_mode(content, args.enable_web_search)

    payload: dict[str, Any] = {
        "model": args.model,
        "content": content,
        "duration": args.duration,
        "ratio": args.ratio,
        "resolution": args.resolution,
        "generate_audio": args.generate_audio,
        "watermark": args.watermark,
    }
    if args.return_last_frame:
        payload["return_last_frame"] = True
    if args.priority is not None:
        payload["priority"] = args.priority
    if args.enable_web_search:
        payload["tools"] = [{"type": "web_search"}]
    return payload

async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_backoff_s: float = DEFAULT_RETRY_BACKOFF_S,
    **kwargs,
) -> httpx.Response:
    # Wrap client.request with retry-on-429/5xx and exponential backoff.
    # Honors Retry-After header (seconds) when present; falls back to exp
    # backoff. Returns the last response on permanent failure so the caller
    # can decide what to do. Re-raises httpx.RequestError if all retries
    # fail with a transport error.
    backoff = initial_backoff_s
    last_resp: httpx.Response | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = await client.request(method, url, **kwargs)
        except httpx.RequestError:
            if attempt == max_retries:
                raise
            await asyncio.sleep(backoff)
            backoff = min(backoff * RETRY_BACKOFF_MULTIPLIER, RETRY_MAX_BACKOFF_S)
            continue
        if resp.status_code not in RETRY_STATUS_CODES:
            return resp
        last_resp = resp
        if attempt == max_retries:
            return resp
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                wait = float(retry_after)
            except ValueError:
                wait = backoff
        else:
            wait = backoff
        await asyncio.sleep(wait)
        backoff = min(backoff * RETRY_BACKOFF_MULTIPLIER, RETRY_MAX_BACKOFF_S)
    return last_resp  # unreachable, kept for type checker


def build_payload_from_shot(shot: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    """Build a Seedance payload from one shot config + shared defaults.

    Shot keys (all optional except prompt):
      prompt, model, duration, ratio, resolution, generate_audio, watermark,
      return_last_frame,
      first_frame, last_frame, reference_image, reference_video, reference_audio.
    Values for *_frame and reference_* can be a single path/URL string or a list.
    Missing shot keys fall back to the defaults dict.
    """
    prompt = shot.get("prompt") or shot.get("text")
    if not prompt:
        raise SystemExit(f"Error: shot missing 'prompt': {shot}")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    tracker = MediaTracker()

    def _add_shot_media(opt_key: str, item_type: str, role: str, exts: set[str]) -> None:
        v = shot.get(opt_key)
        if not v:
            return
        items = v if isinstance(v, list) else [v]
        for path_or_url in items:
            add_media_to_content(content, tracker, path_or_url, item_type, role, exts)

    _add_shot_media("first_frame", "image_url", "first_frame", IMAGE_EXTS)
    _add_shot_media("last_frame", "image_url", "last_frame", IMAGE_EXTS)
    _add_shot_media("reference_image", "image_url", "reference_image", IMAGE_EXTS)
    _add_shot_media("reference_video", "video_url", "reference_video", VIDEO_EXTS)
    _add_shot_media("reference_audio", "audio_url", "reference_audio", AUDIO_EXTS)

    check_total_body_size(content, tracker.raw_bytes)
    validate_mode_constraints(content)

    # Validate every per-shot param that defaults would otherwise silently override.
    model = shot.get("model", defaults.get("model", "doubao-seedance-2-0-260128"))
    ratio = shot.get("ratio", defaults.get("ratio", "16:9"))
    resolution = shot.get("resolution", defaults.get("resolution", "720p"))
    duration = shot.get("duration", defaults.get("duration", 5))
    validate_model(model)
    validate_ratio(ratio)
    validate_resolution(model, resolution)
    validate_duration(duration)

    payload: dict[str, Any] = {
        "model": model,
        "content": content,
        "duration": duration,
        "ratio": ratio,
        "resolution": resolution,
        "generate_audio": shot.get("generate_audio", defaults.get("generate_audio", True)),
        "watermark": shot.get("watermark", defaults.get("watermark", False)),
    }
    if shot.get("return_last_frame") or defaults.get("return_last_frame"):
        payload["return_last_frame"] = True
    return payload

async def _create_task_async(
    client: httpx.AsyncClient, api_key: str, base_url: str, payload: dict[str, Any]
) -> dict[str, Any]:
    url = f"{base_url}/contents/generations/tasks"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if os.getenv("SEEDANCE_ACCEPT_ENCODING_IDENTITY"):
        headers["Accept-Encoding"] = "identity"
    resp = await _request_with_retry(
        client, "POST", url, headers=headers, json=payload, timeout=60,
    )
    if resp.status_code >= 400:
        raise SystemExit(f"Error creating task: HTTP {resp.status_code} {resp.text}")
    return resp.json()


async def _poll_task_async(
    client: httpx.AsyncClient, api_key: str, base_url: str,
    task_id: str, interval: int, max_wait: int, verbose: bool,
) -> dict[str, Any]:
    url = f"{base_url}/contents/generations/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    start = time.time()
    while True:
        resp = await _request_with_retry(client, "GET", url, headers=headers, timeout=60)
        if resp.status_code >= 400:
            raise SystemExit(f"Error polling task: HTTP {resp.status_code} {resp.text}")
        data = resp.json()
        status = data.get("status", "unknown")
        if verbose:
            print(f"[{int(time.time() - start)}s] status={status}", file=sys.stderr)
        # Official terminal states per doc 1521309 (2026-06-25):
        # queued / running / succeeded / failed / cancelled / expired.
        # ("completed" is NOT an official synonym; accept defensively.)
        if status in {"succeeded", "completed", "failed", "cancelled", "expired"}:
            return data
        if time.time() - start > max_wait:
            raise SystemExit(f"Timeout after {max_wait}s. Last status: {status}")
        await asyncio.sleep(interval)


async def _download_video_async(client: httpx.AsyncClient, video_url: str, output_path: Path) -> None:
    """Download a video URL to a local file.

    Retries on 408/429/5xx (transient errors). Once headers are received and we
    start streaming the body, we do NOT retry — partial downloads would be wasted.
    """
    backoff = DEFAULT_RETRY_BACKOFF_S
    last_err: Exception | None = None
    for attempt in range(DEFAULT_MAX_RETRIES + 1):
        try:
            resp = await client.get(video_url, timeout=120)
            if resp.status_code in RETRY_STATUS_CODES and attempt < DEFAULT_MAX_RETRIES:
                last_err = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}", request=resp.request, response=resp
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * RETRY_BACKOFF_MULTIPLIER, RETRY_MAX_BACKOFF_S)
                continue
            resp.raise_for_status()
            with output_path.open("wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            return
        except httpx.RequestError as e:
            last_err = e
            if attempt < DEFAULT_MAX_RETRIES:
                await asyncio.sleep(backoff)
                backoff = min(backoff * RETRY_BACKOFF_MULTIPLIER, RETRY_MAX_BACKOFF_S)
                continue
            raise
    raise SystemExit(
        f"Error: failed to download {video_url} after {DEFAULT_MAX_RETRIES + 1} attempts: {last_err}"
    )


def write_manifest(
    output_dir: Path,
    payload: dict[str, Any],
    task_response: dict[str, Any],
    video_path: Path | None,
    last_frame_path: Path | None,
) -> Path:
    manifest = {
        "task_id": task_response.get("id"),
        "status": task_response.get("status"),
        "model": task_response.get("model", payload.get("model")),
        "ratio": task_response.get("ratio", payload.get("ratio")),
        "duration": task_response.get("duration", payload.get("duration")),
        "resolution": task_response.get("resolution", payload.get("resolution")),
        "usage": task_response.get("usage"),
        "error": task_response.get("error"),
        "video_url": task_response.get("content", {}).get("video_url"),
        "last_frame_url": task_response.get("content", {}).get("last_frame_url"),
        "seed": task_response.get("seed"),
        "service_tier": task_response.get("service_tier"),
        "priority": task_response.get("priority"),
        "draft": task_response.get("draft"),
        "framespersecond": task_response.get("framespersecond"),
        "execution_expires_after": task_response.get("execution_expires_after"),
        "task_created_at": task_response.get("created_at"),
        "task_updated_at": task_response.get("updated_at"),
        "request_payload": payload,
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "output_files": {
            "video": str(video_path) if video_path else None,
            "last_frame": str(last_frame_path) if last_frame_path else None,
        },
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_prompt(output_dir: Path, prompt: str) -> Path:
    path = output_dir / "prompt.md"
    path.write_text(f"# Seedance Prompt\n\n{prompt}\n", encoding="utf-8")
    return path


async def cmd_generate_async(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()
    payload = build_payload(args)

    prompt = payload["content"][0]["text"]
    output_dir = make_output_dir(args.output_dir, prompt)
    write_prompt(output_dir, prompt)

    if args.dry_run:
        synthesized = {
            "id": "DRY-RUN",
            "status": "dry_run",
            "model": payload["model"],
            "ratio": payload["ratio"],
            "duration": payload["duration"],
            "resolution": payload["resolution"],
            "content": {},
            "usage": None,
            "error": None,
        }
        manifest_path = write_manifest(output_dir, payload, synthesized, None, None)
        print("Dry-run mode: no API call made.")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"\nOutput dir: {output_dir}")
        print(f"Manifest: {manifest_path}")
        return 0

    async with httpx.AsyncClient() as client:
        print(f"Creating task at {base_url} ...")
        task = await _create_task_async(client, api_key, base_url, payload)
        task_id = task.get("id")
        print(f"Task ID: {task_id}")

        print(f"Polling (interval={args.poll_interval}s, max_wait={args.max_wait}s) ...")
        result = await _poll_task_async(
            client, api_key, base_url, task_id, args.poll_interval, args.max_wait, args.verbose,
        )
        status = result.get("status")
        print(f"Final status: {status}")

        video_path: Path | None = None
        last_frame_path: Path | None = None
        # Canonical success status is "succeeded" per official API.
        # "completed" is NOT a real status but accept it defensively for forward-compat.
        if status in {"succeeded", "completed"}:
            video_url = result.get("content", {}).get("video_url")
            if video_url:
                video_path = output_dir / "video.mp4"
                print(f"Downloading video to {video_path} ...")
                await _download_video_async(client, video_url, video_path)
            last_frame_url = result.get("content", {}).get("last_frame_url")
            if last_frame_url:
                last_frame_path = output_dir / "last-frame.jpg"
                print(f"Downloading last frame to {last_frame_path} ...")
                await _download_video_async(client, last_frame_url, last_frame_path)
        else:
            print(f"Task did not succeed: {result.get('error')}")

        manifest_path = write_manifest(output_dir, payload, result, video_path, last_frame_path)
        print(f"Manifest: {manifest_path}")
        print(f"Output dir: {output_dir}")
        return 0 if status in {"succeeded", "completed"} else 1


def cmd_generate(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_generate_async(args))


def cmd_create(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()
    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    async def _run():
        async with httpx.AsyncClient() as client:
            return await _create_task_async(client, api_key, base_url, payload)
    task = asyncio.run(_run())
    print(json.dumps(task, ensure_ascii=False, indent=2))
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()
    if not args.task_id:
        raise SystemExit("Error: --task-id required for poll.")
    async def _run():
        async with httpx.AsyncClient() as client:
            return await _poll_task_async(
                client, api_key, base_url, args.task_id,
                args.poll_interval, args.max_wait, args.verbose,
            )
    result = asyncio.run(_run())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    if not args.video_url:
        raise SystemExit("Error: --video-url required for download.")
    output_dir = make_output_dir(args.output_dir, Path(args.video_url).name or "seedance-download")
    video_path = output_dir / "video.mp4"
    async def _run():
        async with httpx.AsyncClient() as client:
            await _download_video_async(client, args.video_url, video_path)
    print(f"Downloading {args.video_url} to {video_path} ...")
    asyncio.run(_run())
    print(f"Saved: {video_path}")
    return 0


async def cmd_list_tasks_async(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()
    base_params: dict[str, Any] = {
        "page_num": args.page_num,
        "page_size": args.page_size,
    }
    if args.status:
        base_params["filter.status"] = args.status
    if args.model:
        base_params["filter.model"] = args.model
    if args.task_ids:
        params_list: list[tuple[str, str]] = [
            (k, str(v)) for k, v in base_params.items()
        ]
        for tid in args.task_ids:
            params_list.append(("filter.task_ids", tid))
        params_arg: Any = params_list
    else:
        params_arg = base_params
    url = f"{base_url}/contents/generations/tasks"
    async with httpx.AsyncClient() as client:
        resp = await _request_with_retry(
            client, "GET", url, params=params_arg,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=30,
        )
    if resp.status_code >= 400:
        raise SystemExit(f"Error listing tasks: HTTP {resp.status_code} {resp.text}")
    body = resp.json()
    if args.json_only:
        print(json.dumps(body, ensure_ascii=False, indent=2))
    else:
        items = body.get("items", [])
        total = body.get("total", "?")
        print(f"Total matching: {total}  Returned: {len(items)}")
        for item in items:
            ts = item.get("updated_at") or item.get("created_at") or 0
            when = dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds") if ts else "-"
            print(f"  [{item.get('status','?'):>9}]  {item.get('id','?'):<32}  {item.get('model','?'):<35}  {when}")
        if args.status and isinstance(total, int) and total > len(items):
            print(f"  ... ({total - len(items)} more; use --page-size to see more)")
    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_list_tasks_async(args))


async def cmd_cancel_task_async(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()
    url = f"{base_url}/contents/generations/tasks/{args.task_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        # 1. Look up the task to report its current state.
        prev_state = "?"
        try:
            get_resp = await _request_with_retry(
                client, "GET", url, headers=headers, timeout=30,
            )
            if get_resp.status_code < 400:
                prev_state = get_resp.json().get("status", "?")
        except SystemExit:
            pass  # If GET fails, proceed anyway; the DELETE will reveal the truth.

        # 2. Issue DELETE.
        del_resp = await _request_with_retry(
            client, "DELETE", url, headers=headers, timeout=30,
        )
    if del_resp.status_code >= 400:
        raise SystemExit(
            f"Error cancelling task: HTTP {del_resp.status_code} {del_resp.text}\n"
            f"  (Note: per official API, DELETE on a running task is rejected.)"
        )

    # 3. Tell the user what actually happened based on the previous state.
    transitions = {
        "queued": "was queued -> now cancelled (no longer runs)",
        "succeeded": "had succeeded -> record deleted (history gone)",
        "failed": "had failed -> record deleted (history gone)",
        "expired": "had expired -> record deleted (history gone)",
        "cancelled": "was already cancelled -> no-op",
    }
    msg = transitions.get(prev_state, f"was in state {prev_state} -> DELETE returned 200")
    print(f"Task {args.task_id}: {msg}.")
    return 0


def cmd_cancel_task(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_cancel_task_async(args))


async def cmd_batch_submit_async(args: argparse.Namespace) -> int:
    api_key, base_url = get_auth()

    shots_path = Path(args.shots_file).expanduser().resolve()
    if not shots_path.is_file():
        raise SystemExit(f"Error: --shots-file not found: {shots_path}")
    try:
        shots = json.loads(shots_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Error: invalid JSON in {shots_path}: {e}")
    if not isinstance(shots, list):
        raise SystemExit(f"Error: --shots-file must be a JSON array of shot objects")
    if not shots:
        raise SystemExit(f"Error: --shots-file is empty")

    defaults: dict[str, Any] = {
        "model": args.model,
        "duration": args.duration,
        "ratio": args.ratio,
        "resolution": args.resolution,
        "generate_audio": args.generate_audio,
        "watermark": args.watermark,
        "return_last_frame": args.return_last_frame,
    }

    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M%S")
    out_dir = Path(args.output_dir).expanduser().resolve() / f"batch-submit-{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Snapshot the input file for traceability
    (out_dir / "shots.json").write_text(shots_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Submitting {len(shots)} shots in parallel (each gets its own task_id)...", flush=True)

    async with httpx.AsyncClient() as client:
        async def _submit_one(shot: dict[str, Any], idx: int) -> dict[str, Any]:
            t0 = time.monotonic()
            try:
                payload = build_payload_from_shot(shot, defaults)
                resp = await _create_task_async(client, api_key, base_url, payload)
                latency_ms = round((time.monotonic() - t0) * 1000, 1)
                return {
                    "shot_index": idx,
                    "prompt": payload["content"][0]["text"][:100],
                    "model": payload["model"],
                    "task_id": resp.get("id"),
                    "status": "submitted",
                    "status_code": 200,
                    "latency_ms": latency_ms,
                    "error": None,
                }
            except SystemExit as e:
                return {
                    "shot_index": idx,
                    "prompt": (shot.get("prompt") or "?")[:100],
                    "task_id": None,
                    "status": "error",
                    "status_code": 0,
                    "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                    "error": str(e),
                }
            except Exception as e:
                return {
                    "shot_index": idx,
                    "prompt": (shot.get("prompt") or "?")[:100],
                    "task_id": None,
                    "status": "exception",
                    "status_code": 0,
                    "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                    "error": f"{type(e).__name__}: {e}",
                }

        results = await asyncio.gather(*[_submit_one(s, i) for i, s in enumerate(shots)])

    n_ok = sum(1 for r in results if r["status"] == "submitted")
    n_err = len(results) - n_ok
    print(f"\n{'='*70}")
    print(f"Batch submit summary: {n_ok} submitted, {n_err} errors (of {len(results)})")
    print(f"{'='*70}")
    for r in results:
        marker = "[OK]" if r["status"] == "submitted" else "[ERR]"
        tid = r["task_id"] or "-"
        print(f"  {marker} #{r['shot_index']:>3}  [{r['status_code']:>3}]  {tid:<32}  {r['latency_ms']:>6.0f}ms  {r['prompt']}")
        if r["error"]:
            print(f"          error: {r['error']}")
    print(flush=True)

    manifest = {
        "submitted_at": dt.datetime.now().isoformat(timespec="seconds"),
        "shots_file": str(shots_path),
        "shots_count": len(shots),
        "submitted_ok": n_ok,
        "errors": n_err,
        "results": results,
        "defaults": {k: v for k, v in defaults.items() if v is not None},
    }
    (out_dir / "batch_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {out_dir}/batch_manifest.json")

    if args.wait and n_ok:
        print(f"\nWaiting for {n_ok} tasks to complete (poll {args.poll_interval}s, max {args.max_wait}s)...", flush=True)
        ok_results = [r for r in results if r["task_id"]]
        async with httpx.AsyncClient() as client:
            polled = await asyncio.gather(*[
                _poll_task_async(client, api_key, base_url, r["task_id"], args.poll_interval, args.max_wait, False)
                for r in ok_results
            ])
        n_succeeded = 0
        n_failed_after_wait = 0
        for r, p in zip(ok_results, polled):
            status = p.get("status")
            # Update manifest entry with final state
            r["status"] = status
            r["finished_at"] = dt.datetime.now().isoformat(timespec="seconds")
            usage = p.get("usage") or {}
            if usage:
                r["usage"] = usage
            error = p.get("error")
            if error:
                r["error"] = str(error)
            content = p.get("content") or {}
            video_url = content.get("video_url")
            last_frame_url = content.get("last_frame_url")
            video_file = None
            last_frame_file = None
            if status in {"succeeded", "completed"}:
                if video_url:
                    video_path = out_dir / f"shot-{r['shot_index']:03d}-{r['task_id']}.mp4"
                    print(f"  Downloading shot {r['shot_index']} to {video_path}...", flush=True)
                    async with httpx.AsyncClient() as client:
                        await _download_video_async(client, video_url, video_path)
                    video_file = str(video_path)
                    n_succeeded += 1
                else:
                    print(f"  Shot {r['shot_index']}: succeeded but no video_url")
                    n_failed_after_wait += 1
                if last_frame_url and args.return_last_frame:
                    lf_path = out_dir / f"shot-{r['shot_index']:03d}-{r['task_id']}-last-frame.jpg"
                    async with httpx.AsyncClient() as client:
                        await _download_video_async(client, last_frame_url, lf_path)
                    last_frame_file = str(lf_path)
            else:
                print(f"  Shot {r['shot_index']} ({r['task_id']}) status={status}: {p.get('error')}")
                n_failed_after_wait += 1
            if video_file:
                r["video_file"] = video_file
            if last_frame_file:
                r["last_frame_file"] = last_frame_file
        # Re-write manifest with final per-task status / usage / file paths
        manifest["wait_completed_at"] = dt.datetime.now().isoformat(timespec="seconds")
        manifest["succeeded"] = n_succeeded
        manifest["failed_after_wait"] = n_failed_after_wait
        (out_dir / "batch_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWait complete: {n_succeeded} succeeded, {n_failed_after_wait} failed/abnormal. Manifest updated.")
    elif n_ok:
        print(f"\nAll {n_ok} tasks submitted. To track progress:")
        print(f"  uv run scripts/generate_seedance_video.py list-tasks --task-ids {' '.join(r['task_id'] for r in results if r['task_id'])}")

    return 0 if n_err == 0 else 1


def cmd_batch_submit(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_batch_submit_async(args))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate videos with Seedance 2.0.")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Default subcommand: generate. Insert it when the first argument is not a known
    # subcommand AND not a top-level-only flag (--help/--version/-h reach argparse's
    # top-level help). Flag-first invocations (e.g. `--prompt ...`, `--model ...`)
    # ARE auto-prefixed with `generate`, matching the SKILL.md quick-start examples.
    known_commands = {"generate", "create", "poll", "download", "list-tasks", "cancel-task", "batch-submit"}
    if sys.argv[1:] and sys.argv[1] not in known_commands and sys.argv[1] not in {"-h", "--help", "--version"}:
        sys.argv.insert(1, "generate")

    def _add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--model", default="doubao-seedance-2-0-260128", choices=sorted(VALID_MODELS))
        p.add_argument("--prompt", "-p")
        p.add_argument("--prompt-file")
        p.add_argument("--first-frame")
        p.add_argument("--last-frame")
        p.add_argument("--reference-image", action="append", default=[])
        p.add_argument("--reference-video", action="append", default=[])
        p.add_argument("--reference-audio", action="append", default=[])
        p.add_argument("--duration", type=int, default=5)
        p.add_argument("--ratio", default="16:9", choices=sorted(VALID_RATIOS))
        p.add_argument("--resolution", default="720p", choices=sorted(VALID_RESOLUTIONS))
        p.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=True)
        p.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=False)
        p.add_argument("--return-last-frame", action="store_true")
        p.add_argument("--priority", type=int, help="Queue priority (higher runs sooner).")
        p.add_argument(
            "--enable-web-search",
            action="store_true",
            help="Enable the web_search tool. Pure text input only (no images/videos/audio).",
        )
        p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                       help="Output root directory (default: SEEDANCE_OUTPUT_DIR env var, or 'output/seedance/')")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--verbose", action="store_true")

    gen = subparsers.add_parser("generate", help="Create task, poll, and download video (default)")
    _add_common(gen)
    gen.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    gen.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT)

    create = subparsers.add_parser("create", help="Create task only")
    _add_common(create)

    poll = subparsers.add_parser("poll", help="Poll an existing task")
    poll.add_argument("--task-id", required=True)
    poll.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    poll.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT)
    poll.add_argument("--verbose", action="store_true")

    download = subparsers.add_parser("download", help="Download a video URL")
    download.add_argument("--video-url", required=True)
    download.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                          help="Output root directory (default: SEEDANCE_OUTPUT_DIR env var, or 'output/seedance/')")
    download.add_argument("--verbose", action="store_true")

    list_tasks = subparsers.add_parser("list-tasks", help="List video generation tasks (filter by status/model/task-ids)")
    list_tasks.add_argument("--status", choices=["queued", "running", "succeeded", "failed", "cancelled", "expired"], help="Filter by task status")
    list_tasks.add_argument("--model", help="Filter by model name (e.g. doubao-seedance-2-0-260128)")
    list_tasks.add_argument("--task-ids", nargs="+", help="Filter by specific task IDs (space-separated)")
    list_tasks.add_argument("--page-num", type=int, default=1)
    list_tasks.add_argument("--page-size", type=int, default=20)
    list_tasks.add_argument("--json-only", action="store_true", help="Print full JSON response instead of a table summary")
    list_tasks.add_argument("--verbose", action="store_true")

    batch = subparsers.add_parser("batch-submit", help="Submit multiple shots in one call (parallel). Reads shot configs from a JSON file.")
    batch.add_argument("--shots-file", required=True, help="Path to JSON file: array of {prompt, [duration], [first_frame], [reference_image], ...}")
    batch.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                       help="Output root (default: SEEDANCE_OUTPUT_DIR env var, or 'output/seedance/')")
    batch.add_argument("--model", default="doubao-seedance-2-0-260128", choices=sorted(VALID_MODELS))
    batch.add_argument("--duration", type=int, default=5)
    batch.add_argument("--ratio", default="16:9", choices=sorted(VALID_RATIOS))
    batch.add_argument("--resolution", default="720p", choices=sorted(VALID_RESOLUTIONS))
    batch.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=True)
    batch.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=False)
    batch.add_argument("--return-last-frame", action="store_true")
    batch.add_argument("--wait", action="store_true", help="After submitting, wait for all tasks to complete and download videos")
    batch.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    batch.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT)
    batch.add_argument("--verbose", action="store_true")

    cancel = subparsers.add_parser("cancel-task", help="Cancel a queued task or delete a completed/failed task record")
    cancel.add_argument("--task-id", required=True)
    cancel.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main() -> int:
    _load_dotenv()
    args = parse_args()
    command = args.command or "generate"
    if command == "generate":
        return cmd_generate(args)
    if command == "create":
        return cmd_create(args)
    if command == "poll":
        return cmd_poll(args)
    if command == "download":
        return cmd_download(args)
    if command == "list-tasks":
        return cmd_list_tasks(args)
    if command == "cancel-task":
        return cmd_cancel_task(args)
    if command == "batch-submit":
        return cmd_batch_submit(args)
    raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
