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
DEFAULT_OUTPUT_DIR = "content/inbox/videos"
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
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

# Seedance 2.0 series (the only line this script currently supports).
# - Standard (260128): 1080p OK, all ratios, audio.
# - Fast (260128): 1080p NOT supported, cheaper and quicker.
# - Mini (260615): 1080p NOT supported, trial period 2026-06-15 to 2026-06-22
#   in console only; API access from 2026-06-22.
VALID_MODELS = {
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
}
# Seedance 2.0 variants that cap at 720p.
NO_1080P_MODELS = {
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-2-0-mini-260615",
}
VALID_RATIOS = {"16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"}
VALID_RESOLUTIONS = {"480p", "720p", "1080p"}
SUPPORTED_IMAGE_ROLES = {"first_frame", "last_frame", "reference_image"}
SUPPORTED_VIDEO_ROLES = {"reference_video"}
SUPPORTED_AUDIO_ROLES = {"reference_audio"}


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
    parsed = urlparse(path_or_url)
    return parsed.scheme in {"http", "https"}


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
    }.get(ext, f"image/{ext}")


def _video_mime(ext: str) -> str:
    return {
        "mp4": "video/mp4", "mov": "video/quicktime",
        "avi": "video/x-msvideo", "mkv": "video/x-matroska", "webm": "video/webm",
    }.get(ext, f"video/{ext}")


def _audio_mime(ext: str) -> str:
    return {
        "mp3": "audio/mpeg", "wav": "audio/wav", "aac": "audio/aac",
        "flac": "audio/flac", "m4a": "audio/mp4", "ogg": "audio/ogg",
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
    if args.model not in VALID_MODELS:
        raise SystemExit(f"Error: unsupported model '{args.model}'. Valid: {VALID_MODELS}")
    if args.ratio not in VALID_RATIOS:
        raise SystemExit(f"Error: unsupported ratio '{args.ratio}'. Valid: {VALID_RATIOS}")
    if args.resolution not in VALID_RESOLUTIONS:
        raise SystemExit(f"Error: unsupported resolution '{args.resolution}'. Valid: {VALID_RESOLUTIONS}")
    if args.resolution == "1080p" and args.model in NO_1080P_MODELS:
        raise SystemExit(
            f"Error: model '{args.model}' does not support 1080p (capped at 720p). Use --resolution 720p or 480p."
        )
    if args.duration != -1 and not (4 <= args.duration <= 15):
        raise SystemExit("Error: duration must be between 4 and 15, or -1 for adaptive.")

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).expanduser().resolve().read_text(encoding="utf-8").strip()
    if not prompt:
        raise SystemExit("Error: provide --prompt or --prompt-file.")

    content: list[dict[str, Any]] = [build_content_item("text", prompt)]

    def _add_media(path_or_url: str, item_type: str, role: str, allowed_exts: set[str]) -> None:
        if is_url(path_or_url):
            content.append(build_content_item(item_type, path_or_url, role))
        else:
            local_path = validate_local_media(path_or_url, allowed_exts)
            ext = local_path.suffix.lower().lstrip(".")
            mime_type = _media_mime(ext, item_type)
            file_bytes = local_path.read_bytes()
            b64 = base64.b64encode(file_bytes).decode("ascii")
            data_url = f"data:{mime_type};base64,{b64}"
            content.append(build_content_item(item_type, data_url, role))

    if args.first_frame:
        _add_media(args.first_frame, "image_url", "first_frame", {"png", "jpg", "jpeg", "webp", "gif", "bmp"})
    if args.last_frame:
        _add_media(args.last_frame, "image_url", "last_frame", {"png", "jpg", "jpeg", "webp", "gif", "bmp"})
    for img in args.reference_image or []:
        _add_media(img, "image_url", "reference_image", {"png", "jpg", "jpeg", "webp", "gif", "bmp"})
    for vid in args.reference_video or []:
        _add_media(vid, "video_url", "reference_video", {"mp4", "mov", "avi", "mkv", "webm"})
    for aud in args.reference_audio or []:
        _add_media(aud, "audio_url", "reference_audio", {"mp3", "wav", "aac", "flac", "m4a", "ogg"})

    validate_mode_constraints(content)
    if args.enable_web_search:
        non_text = [c for c in content if c.get("type") != "text"]
        if non_text:
            raise SystemExit(
                "Error: --enable-web-search requires pure text content. "
                f"Found {len(non_text)} non-text item(s); remove --first-frame/--last-frame/--reference-*."
            )

    payload: dict[str, Any] = {
        "model": args.model,
        "content": content,
        "duration": args.duration,
        "ratio": args.ratio,
        "resolution": args.resolution,
        "generate_audio": args.generate_audio,
        "watermark": args.watermark,
    }
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.return_last_frame:
        payload["return_last_frame"] = True
    if args.frames is not None:
        # Frames take precedence over duration per the official spec.
        payload["frames"] = args.frames
        payload.pop("duration", None)
    if args.service_tier:
        payload["service_tier"] = args.service_tier
    if args.priority is not None:
        payload["priority"] = args.priority
    if args.draft:
        payload["draft"] = True
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
      prompt, duration, ratio, resolution, generate_audio, watermark,
      seed, return_last_frame,
      first_frame, last_frame, reference_image, reference_video, reference_audio.
    Values for *_frame and reference_* can be a single path/URL string or a list.
    Missing shot keys fall back to the defaults dict.
    """
    prompt = shot.get("prompt") or shot.get("text")
    if not prompt:
        raise SystemExit(f"Error: shot missing 'prompt': {shot}")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]

    image_exts = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}
    video_exts = {"mp4", "mov", "avi", "mkv", "webm"}
    audio_exts = {"mp3", "wav", "aac", "flac", "m4a", "ogg"}

    def _add_media(opt_key: str, item_type: str, role: str, exts: set[str]) -> None:
        v = shot.get(opt_key)
        if not v:
            return
        items = v if isinstance(v, list) else [v]
        for path_or_url in items:
            if is_url(path_or_url):
                content.append(build_content_item(item_type, path_or_url, role))
            else:
                local_path = validate_local_media(path_or_url, exts)
                ext = local_path.suffix.lower().lstrip(".")
                mime_type = _media_mime(ext, item_type)
                b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
                data_url = f"data:{mime_type};base64,{b64}"
                content.append(build_content_item(item_type, data_url, role))

    _add_media("first_frame", "image_url", "first_frame", image_exts)
    _add_media("last_frame", "image_url", "last_frame", image_exts)
    _add_media("reference_image", "image_url", "reference_image", image_exts)
    _add_media("reference_video", "video_url", "reference_video", video_exts)
    _add_media("reference_audio", "audio_url", "reference_audio", audio_exts)

    validate_mode_constraints(content)

    if shot.get("duration") is not None and not (shot["duration"] == -1 or 4 <= shot["duration"] <= 15):
        raise SystemExit(f"Error: shot duration must be 4-15 or -1, got {shot['duration']}")
    ratio = shot.get("ratio", defaults.get("ratio", "16:9"))
    if ratio not in VALID_RATIOS:
        raise SystemExit(f"Error: shot ratio '{ratio}' not in {VALID_RATIOS}")
    resolution = shot.get("resolution", defaults.get("resolution", "720p"))
    if resolution not in VALID_RESOLUTIONS:
        raise SystemExit(f"Error: shot resolution '{resolution}' not in {VALID_RESOLUTIONS}")

    payload: dict[str, Any] = {
        "model": shot.get("model", defaults.get("model", "doubao-seedance-2-0-260128")),
        "content": content,
        "duration": shot.get("duration", defaults.get("duration", 5)),
        "ratio": ratio,
        "resolution": resolution,
        "generate_audio": shot.get("generate_audio", defaults.get("generate_audio", True)),
        "watermark": shot.get("watermark", defaults.get("watermark", False)),
    }
    seed = shot.get("seed", defaults.get("seed"))
    if seed is not None:
        payload["seed"] = seed
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
    if resp.status_code != 200:
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
        if resp.status_code != 200:
            raise SystemExit(f"Error polling task: HTTP {resp.status_code} {resp.text}")
        data = resp.json()
        status = data.get("status", "unknown")
        if verbose:
            print(f"[{int(time.time() - start)}s] status={status}", file=sys.stderr)
        if status in {"succeeded", "completed", "failed", "expired"}:
            return data
        if time.time() - start > max_wait:
            raise SystemExit(f"Timeout after {max_wait}s. Last status: {status}")
        await asyncio.sleep(interval)


async def _download_video_async(client: httpx.AsyncClient, video_url: str, output_path: Path) -> None:
    resp = await client.get(video_url, timeout=120)
    resp.raise_for_status()
    with output_path.open("wb") as f:
        async for chunk in resp.aiter_bytes(chunk_size=8192):
            if chunk:
                f.write(chunk)


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
    _load_dotenv()
    api_key, base_url = get_auth()
    payload = build_payload(args)

    prompt = payload["content"][0]["text"]
    output_dir = make_output_dir(args.output_dir, prompt)
    write_prompt(output_dir, prompt)

    if args.dry_run:
        dry_path = output_dir / "manifest.json"
        dry_path.write_text(json.dumps({
            "dry_run": True,
            "request_payload": payload,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Dry-run mode: request payload saved.")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"\nOutput dir: {output_dir}")
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
    _load_dotenv()
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
    _load_dotenv()
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
    _load_dotenv()
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
    if resp.status_code != 200:
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
    _load_dotenv()
    api_key, base_url = get_auth()
    url = f"{base_url}/contents/generations/tasks/{args.task_id}"
    async with httpx.AsyncClient() as client:
        resp = await _request_with_retry(
            client, "DELETE", url,
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=30,
        )
    if resp.status_code != 200:
        raise SystemExit(f"Error cancelling task: HTTP {resp.status_code} {resp.text}")
    print(f"Cancelled/deleted: {args.task_id}")
    return 0


def cmd_cancel_task(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_cancel_task_async(args))


async def cmd_batch_submit_async(args: argparse.Namespace) -> int:
    _load_dotenv()
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
        "seed": args.seed,
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
        for r, p in zip(ok_results, polled):
            status = p.get("status")
            if status in {"succeeded", "completed"}:
                video_url = p.get("content", {}).get("video_url")
                if video_url:
                    video_path = out_dir / f"shot-{r['shot_index']:03d}-{r['task_id']}.mp4"
                    print(f"  Downloading shot {r['shot_index']} to {video_path}...", flush=True)
                    async with httpx.AsyncClient() as client:
                        await _download_video_async(client, video_url, video_path)
                else:
                    print(f"  Shot {r['shot_index']}: succeeded but no video_url")
            else:
                print(f"  Shot {r['shot_index']} ({r['task_id']}) status={status}: {p.get('error')}")
    elif n_ok:
        print(f"\nAll {n_ok} tasks submitted. To track progress:")
        print(f"  uv run scripts/generate_seedance_video.py list-tasks --task-ids {' '.join(r['task_id'] for r in results if r['task_id'])}")

    return 0 if n_err == 0 else 1


def cmd_batch_submit(args: argparse.Namespace) -> int:
    return asyncio.run(cmd_batch_submit_async(args))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate videos with Seedance 2.0.")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Default subcommand: generate. Insert it when the first argument is not a known subcommand.
    known_commands = {"generate", "create", "poll", "download", "list-tasks", "cancel-task", "batch-submit"}
    if sys.argv[1:] and sys.argv[1] not in known_commands:
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
        p.add_argument("--seed", type=int)
        p.add_argument("--frames", type=int, help="Frame count (overrides --duration). Use 25+4n format in [29, 289].")
        p.add_argument("--service-tier", choices=["default", "flex"], help="default=online, flex=offline (cheaper).")
        p.add_argument("--priority", type=int, help="Queue priority (higher runs sooner).")
        p.add_argument("--draft", action="store_true", help="Generate a low-cost draft/样片 task.")
        p.add_argument(
            "--enable-web-search",
            action="store_true",
            help="Enable the web_search tool. Pure text input only (no images/videos/audio).",
        )
        p.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
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
    download.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    download.add_argument("--verbose", action="store_true")

    list_tasks = subparsers.add_parser("list-tasks", help="List video generation tasks (filter by status/model/task-ids)")
    list_tasks.add_argument("--status", choices=["queued", "running", "succeeded", "failed", "cancelled", "expired"], help="Filter by task status")
    list_tasks.add_argument("--model", help="Filter by model name (e.g. doubao-seedance-2-0-260128)")
    list_tasks.add_argument("--task-ids", nargs="+", help="Filter by specific task IDs (space-separated)")
    list_tasks.add_argument("--page-num", type=int, default=1)
    list_tasks.add_argument("--page-size", type=int, default=20)
    list_tasks.add_argument("--json-only", action="store_true", help="Print full JSON response instead of a table summary")

    batch = subparsers.add_parser("batch-submit", help="Submit multiple shots in one call (parallel). Reads shot configs from a JSON file.")
    batch.add_argument("--shots-file", required=True, help="Path to JSON file: array of {prompt, [duration], [first_frame], [reference_image], ...}")
    batch.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help=f"Output root (default: {DEFAULT_OUTPUT_DIR})")
    batch.add_argument("--model", default="doubao-seedance-2-0-260128", choices=sorted(VALID_MODELS))
    batch.add_argument("--duration", type=int, default=5)
    batch.add_argument("--ratio", default="16:9", choices=sorted(VALID_RATIOS))
    batch.add_argument("--resolution", default="720p", choices=sorted(VALID_RESOLUTIONS))
    batch.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=True)
    batch.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=False)
    batch.add_argument("--return-last-frame", action="store_true")
    batch.add_argument("--seed", type=int)
    batch.add_argument("--wait", action="store_true", help="After submitting, wait for all tasks to complete and download videos")
    batch.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL)
    batch.add_argument("--max-wait", type=int, default=DEFAULT_MAX_WAIT)

    cancel = subparsers.add_parser("cancel-task", help="Cancel a queued task or delete a completed/failed task record")
    cancel.add_argument("--task-id", required=True)

    return parser.parse_args()


def main() -> int:
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
