#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.34.2",
# ]
# ///

from __future__ import annotations

import argparse
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

import requests


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_OUTPUT_DIR = "content/inbox/videos"
DEFAULT_POLL_INTERVAL = 20
DEFAULT_MAX_WAIT = 1800

VALID_MODELS = {
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
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
    return slug or "seedance-video"


def get_auth() -> tuple[str, str]:
    api_key = os.getenv("ARK_API_KEY")
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
        raise SystemExit(f"Error: unsupported file extension '{ext}' for {p}. Allowed: {allowed_exts}")
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
        raise SystemExit("Error: first/last frame mode and reference mode are mutually exclusive.")
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
        raise SystemExit("Error: audio reference requires at least one image or video reference.")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.model not in VALID_MODELS:
        raise SystemExit(f"Error: unsupported model '{args.model}'. Valid: {VALID_MODELS}")
    if args.ratio not in VALID_RATIOS:
        raise SystemExit(f"Error: unsupported ratio '{args.ratio}'. Valid: {VALID_RATIOS}")
    if args.resolution not in VALID_RESOLUTIONS:
        raise SystemExit(f"Error: unsupported resolution '{args.resolution}'. Valid: {VALID_RESOLUTIONS}")
    if args.model == "doubao-seedance-2-0-fast-260128" and args.resolution == "1080p":
        raise SystemExit("Error: fast model does not support 1080p.")
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
            # Convert local file to base64 data URL
            ext = local_path.suffix.lower().lstrip(".")
            mime_type = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
                "gif": "image/gif",
                "bmp": "image/bmp",
            }.get(ext, f"image/{ext}")
            if item_type == "video_url":
                mime_type = {
                    "mp4": "video/mp4",
                    "mov": "video/quicktime",
                    "avi": "video/x-msvideo",
                    "mkv": "video/x-matroska",
                    "webm": "video/webm",
                }.get(ext, f"video/{ext}")
            elif item_type == "audio_url":
                mime_type = {
                    "mp3": "audio/mpeg",
                    "wav": "audio/wav",
                    "aac": "audio/aac",
                    "flac": "audio/flac",
                    "m4a": "audio/mp4",
                    "ogg": "audio/ogg",
                }.get(ext, f"audio/{ext}")
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
    return payload


def create_task(api_key: str, base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url}/contents/generations/tasks"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if os.getenv("SEEDANCE_ACCEPT_ENCODING_IDENTITY"):
        headers["Accept-Encoding"] = "identity"
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise SystemExit(f"Error creating task: HTTP {resp.status_code} {resp.text}")
    return resp.json()


def poll_task(api_key: str, base_url: str, task_id: str, interval: int, max_wait: int, verbose: bool) -> dict[str, Any]:
    url = f"{base_url}/contents/generations/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    start = time.time()
    while True:
        resp = requests.get(url, headers=headers, timeout=60)
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
        time.sleep(interval)


def download_video(video_url: str, output_path: Path) -> None:
    # Video URL download should NOT include Authorization header
    resp = requests.get(video_url, stream=True, timeout=120)
    resp.raise_for_status()
    with output_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
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


def cmd_generate(args: argparse.Namespace) -> int:
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

    print(f"Creating task at {base_url} ...")
    task = create_task(api_key, base_url, payload)
    task_id = task.get("id")
    print(f"Task ID: {task_id}")

    print(f"Polling (interval={args.poll_interval}s, max_wait={args.max_wait}s) ...")
    result = poll_task(api_key, base_url, task_id, args.poll_interval, args.max_wait, args.verbose)
    status = result.get("status")
    print(f"Final status: {status}")

    video_path: Path | None = None
    last_frame_path: Path | None = None
    if status in {"succeeded", "completed"}:
        video_url = result.get("content", {}).get("video_url")
        if video_url:
            video_path = output_dir / "video.mp4"
            print(f"Downloading video to {video_path} ...")
            download_video(video_url, video_path)
        last_frame_url = result.get("content", {}).get("last_frame_url")
        if last_frame_url:
            last_frame_path = output_dir / "last-frame.jpg"
            print(f"Downloading last frame to {last_frame_path} ...")
            download_video(last_frame_url, last_frame_path)
    else:
        print(f"Task did not succeed: {result.get('error')}")

    manifest_path = write_manifest(output_dir, payload, result, video_path, last_frame_path)
    print(f"Manifest: {manifest_path}")
    print(f"Output dir: {output_dir}")
    return 0 if status in {"succeeded", "completed"} else 1


def cmd_create(args: argparse.Namespace) -> int:
    _load_dotenv()
    api_key, base_url = get_auth()
    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    task = create_task(api_key, base_url, payload)
    print(json.dumps(task, ensure_ascii=False, indent=2))
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    _load_dotenv()
    api_key, base_url = get_auth()
    if not args.task_id:
        raise SystemExit("Error: --task-id required for poll.")
    result = poll_task(api_key, base_url, args.task_id, args.poll_interval, args.max_wait, args.verbose)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    if not args.video_url:
        raise SystemExit("Error: --video-url required for download.")
    output_dir = make_output_dir(args.output_dir, Path(args.video_url).name or "seedance-download")
    video_path = output_dir / "video.mp4"
    print(f"Downloading {args.video_url} to {video_path} ...")
    download_video(args.video_url, video_path)
    print(f"Saved: {video_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate videos with Seedance 2.0.")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Default subcommand: generate. Insert it when the first argument is not a known subcommand.
    known_commands = {"generate", "create", "poll", "download"}
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
    raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
