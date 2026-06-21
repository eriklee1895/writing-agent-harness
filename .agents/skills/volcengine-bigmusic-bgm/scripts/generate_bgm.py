#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
#   "python-dotenv>=1.0",
# ]
# ///

"""
火山引擎 BigMusic (Seed-Music) — instrumental BGM generation.

Generates instrumental background music from a Chinese style description via the
Volcengine OpenAPI (Action=GenBGMForTime, duration-billed). Submits asynchronously;
results are polled via Action=QuerySong.

Auth: Volc Signature V4 (HMAC-SHA256) using VOLC_ACCESSKEY / VOLC_SECRETKEY.

Usage:
    uv run generate_bgm.py "轻柔的钢琴背景纯音乐，温暖治愈" --duration 60 --out bgm.wav
    uv run generate_bgm.py "电子氛围" --duration 60 --format mp3 --out bgm.mp3

Output (JSON on stdout):
    {"audio_file": "...", "duration": 60, "log_id": "...", "error": null, ...}

Docs:
  - 生成纯音乐:        https://www.volcengine.com/docs/84992/2100970
  - 查询任务(QuerySong): https://www.volcengine.com/docs/84992/2100960
  - 鉴权:              https://www.volcengine.com/docs/84992/1967910
  - 常见错误码:         https://www.volcengine.com/docs/84992/1404675
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# ── API constants ──────────────────────────────────────────────────────────

API_HOST = "open.volcengineapi.com"
API_URL = f"https://{API_HOST}/"
SERVICE = "imagination"
REGION = "cn-beijing"
API_VERSION = "2024-08-12"  # OpenAPI Version (query string)
MODEL_VERSION = "v5.0"  # Music model Version (request body)

# We only use the duration-billed (postpaid) action. The package-billed
# GenBGM action is intentionally not exposed; calling it on a postpaid
# account yields 200028 "没有可用资源包".
SUBMIT_ACTION = "GenBGMForTime"

# Polling action: a single shared `QuerySong` action is used to fetch the result
# of any of the submit actions above.
ACTION_QUERY = "QuerySong"

# Duration bounds documented by the API (v5.0): [30, 120] seconds.
MIN_DURATION = 30
MAX_DURATION = 120

# Async polling
POLL_INTERVAL_SECONDS = 5
DEFAULT_POLL_TIMEOUT_SECONDS = 300  # 60s tasks empirically return in ~20s

# ── Error-code hints (官方常见错误码 doc) ────────────────────────────────────

ERROR_CODE_HINTS: dict[int, str] = {
    100001: "InternalError — 服务端内部错误（参数类型/枚举非法，或误用已废弃接口）。",
    100010: (
        "InvalidRequestParams — 请求参数不合法"
        "（检查 Duration ∈ [30,120]、Version、Genre/Mood 枚举值）。"
    ),
    100011: "ServerIpLimit — 海外 IP 限制使用。",
    100013: "AuthFailed — 鉴权失败（检查 VOLC_ACCESSKEY / VOLC_SECRETKEY）。",
    200020: "InvalidSign — 签名无效（注意区分主账号 / 子账号 AK/SK）。",
    200021: "AuthExpired — 用户授权过期。",
    200022: "APIOutOfLimit — 资源包消耗完毕。",
    200023: "APIOutOfQps — 超过 QPS 限制。",
    200024: "AuthDisable — 账号的音乐功能被禁用。",
    200027: "APIOutOfTime — 资源包过期。",
    200028: (
        "APINoSource — 没有可用资源包。"
        "常见原因：Action 与计费方式不匹配（套餐包账号调了 GenBGMForTime，或反之）。"
    ),
    300030: (
        "AlgorithmError — 算法错误。子类型 50000001 MusicSimilarityDetectionNotPassed "
        "是版权/相似度校验失败，建议丰富 prompt 或开启 --rewrite。"
    ),
    300052: "TaskNotFound — 任务未找到（可能 TaskID 错误或已过期清理）。",
    400040: "QueueFull — 队列已满，请稍后重试。",
    429: "RateLimited — 触发限流，请降并发/退避重试。",
    50000001: (
        "MusicSimilarityDetectionNotPassed — 音乐相似度/版权校验未通过。"
        "通过丰富 Text、增加参数、延长 Duration（建议 ≥ 60s）或加 --rewrite 规避。"
    ),
}


# ── Credentials ─────────────────────────────────────────────────────────────


def load_credentials() -> tuple[str, str]:
    """Load VOLC_ACCESSKEY / VOLC_SECRETKEY with a three-level fallback."""

    def _get() -> tuple[str, str]:
        return (
            os.environ.get("VOLC_ACCESSKEY", "").strip(),
            os.environ.get("VOLC_SECRETKEY", "").strip(),
        )

    ak, sk = _get()
    if ak and sk:
        return ak, sk

    for env_path in (Path.cwd() / ".env", Path.home() / ".volcengine.env"):
        if env_path.exists():
            load_dotenv(env_path)
            ak, sk = _get()
            if ak and sk:
                return ak, sk

    die(
        "VOLC_ACCESSKEY / VOLC_SECRETKEY not found. Set them via environment, "
        ".env in CWD, or ~/.volcengine.env"
    )
    raise SystemExit(1)


# ── HTTP / signing ──────────────────────────────────────────────────────────


def sign_and_post(ak: str, sk: str, action: str, body: dict[str, Any]) -> tuple[int, str, str]:
    """Sign and POST a Volcengine OpenAPI request. Returns (status, text, log_id)."""
    now = datetime.now(UTC)
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    body_str = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    payload_hash = hashlib.sha256(body_str.encode("utf-8")).hexdigest()

    canonical_request = "\n".join([
        "POST",
        "/",
        f"Action={action}&Version={API_VERSION}",
        f"host:{API_HOST}\nx-content-sha256:{payload_hash}\nx-date:{x_date}\n",
        "host;x-content-sha256;x-date",
        payload_hash,
    ])

    credential_scope = f"{now.strftime('%Y%m%d')}/{REGION}/{SERVICE}/request"
    string_to_sign = "\n".join([
        "HMAC-SHA256",
        x_date,
        credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    def _hmac(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = _hmac(sk.encode("utf-8"), now.strftime("%Y%m%d"))
    k_region = _hmac(k_date, REGION)
    k_service = _hmac(k_region, SERVICE)
    k_signing = _hmac(k_service, "request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"HMAC-SHA256 Credential={ak}/{credential_scope}, "
        f"SignedHeaders=host;x-content-sha256;x-date, Signature={signature}"
    )

    headers = {
        "Host": API_HOST,
        "X-Date": x_date,
        "X-Content-Sha256": payload_hash,
        "Authorization": authorization,
        "Content-Type": "application/json",
    }
    params = {"Action": action, "Version": API_VERSION}

    try:
        resp = requests.post(API_URL, params=params, headers=headers, data=body_str, timeout=60)
    except requests.RequestException as e:
        return 0, str(e), ""
    return resp.status_code, resp.text, resp.headers.get("x-tt-logid", "")


# ── Response parsing ────────────────────────────────────────────────────────


def explain_error(code: Any, message: str) -> str:
    """Map a Volcengine error code to a human-readable hint."""
    try:
        key = int(code)
    except (TypeError, ValueError):
        return f"[code={code}] {message}"
    hint = ERROR_CODE_HINTS.get(key, "")
    if hint:
        return f"[{key}] {hint} (server: {message})"
    return f"[{key}] {message}"


def parse_envelope(text: str) -> tuple[dict[str, Any] | None, str | None, str]:
    """Parse the Volcengine OpenAPI envelope. Returns (result, error, log_id)."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, f"Non-JSON response: {text[:300]}", ""

    meta = payload.get("ResponseMetadata") or {}
    log_id = meta.get("RequestId", "")
    err_block = meta.get("Error") or {}
    code = payload.get("Code")
    message = payload.get("Message", "")

    if err_block:
        return None, explain_error(err_block.get("CodeN", code), err_block.get("Message", message)), log_id
    if code not in (None, 0) and payload.get("Result") is None:
        return None, explain_error(code, message), log_id

    return payload.get("Result") or {}, None, log_id


# ── Audio download / format sniff ───────────────────────────────────────────


_SNIFF_BYTES = {
    b"RIFF": ".wav",
    b"OggS": ".ogg",
    b"fLaC": ".flac",
    b"ID3": ".mp3",
}


def sniff_ext(url: str, body: bytes) -> str | None:
    """Best-effort audio extension inference from URL query and file magic."""
    m = re.search(r"mime_type=audio_([a-z0-9]+)", url, flags=re.IGNORECASE)
    if m:
        kind = m.group(1).lower()
        return {".wav": ".wav", ".mp3": ".mp3", ".mpeg": ".mp3", ".ogg": ".ogg", ".flac": ".flac"}.get(
            "." + kind, "." + kind
        )
    head = body[:4]
    for sig, ext in _SNIFF_BYTES.items():
        if head.startswith(sig):
            return ext
    # MP3 frame sync (11 bits set)
    if head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") and (head[2] & 0xE0) == 0xE0:
        return ".mp3"
    return None


def download_audio(url: str, out_path: Path) -> Path:
    """Download audio bytes and rename the output to match the real format."""
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    body = resp.content
    sniffed = sniff_ext(url, body)
    target = out_path
    if sniffed and target.suffix.lower() != sniffed:
        target = target.with_suffix(sniffed)
    target.write_bytes(body)
    return target


def transcode_to_mp3(src: Path, dst: Path, bitrate: str = "192k") -> Path:
    """Transcode a downloaded audio file to MP3 using ffmpeg. Returns dst."""
    if shutil.which("ffmpeg") is None:
        die("ffmpeg not found on PATH; install it or drop --format mp3")
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-codec:a", "libmp3lame", "-b:a", bitrate,
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        die(f"ffmpeg transcode failed: {proc.stderr.strip()}")
    return dst


# ── Async task poll ─────────────────────────────────────────────────────────


@dataclass
class TaskResult:
    audio_url: str | None
    failure_code: int | None
    failure_msg: str | None
    log_id: str


def submit_action(ak: str, sk: str, action: str, body: dict[str, Any]) -> tuple[dict | None, str | None, str]:
    """Submit a GenBGM/GenBGMForTime task. Returns (result_dict, error, log_id)."""
    status, text, _ = sign_and_post(ak, sk, action, body)
    if status and status >= 400:
        return None, f"HTTP {status}: {text[:300]}", ""
    return parse_envelope(text)


def poll_task(ak: str, sk: str, task_id: str, timeout_seconds: int) -> TaskResult:
    """Poll QuerySong until the task is success / failure / timeout.

    Per the official docs, the response carries a top-level `Status` integer:
      0 = waiting, 1 = processing, 2 = success, 3 = failed
    Audio URL is at `Result.SongDetail.AudioUrl` on success.
    """
    deadline = time.time() + timeout_seconds
    last_log_id = ""
    while time.time() < deadline:
        _, text, log_id = sign_and_post(ak, sk, ACTION_QUERY, {"TaskID": task_id})
        last_log_id = log_id or last_log_id
        result, err, log_id2 = parse_envelope(text)
        last_log_id = log_id2 or last_log_id
        if err:
            # Treat parse errors as transient only if it's clearly "still running";
            # otherwise return the error verbatim.
            return TaskResult(None, None, err, last_log_id)
        if result:
            status_code = result.get("Status")
            song_detail = result.get("SongDetail") or {}
            audio_url = song_detail.get("AudioUrl") or song_detail.get("AudioURL")
            if status_code == 2 and audio_url:
                return TaskResult(audio_url, None, None, last_log_id)
            if status_code == 3:
                failure = result.get("FailureReason") or {}
                code = failure.get("Code")
                msg = failure.get("Msg")
                return TaskResult(
                    None,
                    int(code) if isinstance(code, (int, float)) else None,
                    msg,
                    last_log_id,
                )
            # 0/1 → still running
        time.sleep(POLL_INTERVAL_SECONDS)

    return TaskResult(None, None, f"Timed out after {timeout_seconds}s polling {task_id}", last_log_id)


# ── High-level generation ───────────────────────────────────────────────────


def build_request_body(
    text: str,
    duration: int,
    *,
    rewrite: bool = False,
    tos_bucket: str | None = None,
) -> dict[str, Any]:
    """Build the request body for GenBGM / GenBGMForTime.

    v5.0 no longer accepts Genre/Mood/Instrument/Theme; everything goes in Text.
    """
    body: dict[str, Any] = {
        "Text": text,
        "Duration": duration,
        "Version": MODEL_VERSION,
        "EnableInputRewrite": rewrite,
    }
    if tos_bucket:
        body["TosBucket"] = tos_bucket
    return body


def generate(
    text: str,
    duration: int,
    out_path: Path,
    *,
    rewrite: bool,
    format: str,  # "wav" (default) or "mp3"
    timeout_seconds: int,
    dry_run: bool,
) -> dict[str, Any]:
    ak, sk = load_credentials()
    body = build_request_body(text, duration, rewrite=rewrite)
    log_id = ""

    if dry_run:
        return {
            "audio_file": None,
            "duration": duration,
            "log_id": "",
            "action": SUBMIT_ACTION,
            "request_body": body,
            "dry_run": True,
            "error": None,
        }

    result, err, log_id = submit_action(ak, sk, SUBMIT_ACTION, body)
    if err:
        return {"audio_file": None, "duration": duration, "log_id": log_id,
                "action": SUBMIT_ACTION, "request_body": body, "error": err}

    # GenBGM always returns a TaskId; some responses may also include a
    # synchronous AudioUrl. Handle both.
    audio_url: str | None = None
    task_id: str | None = None
    for k in ("TaskId", "TaskID", "AudioUrl", "AudioURL"):
        v = result.get(k)
        if isinstance(v, str) and v.startswith("http"):
            audio_url = v
        elif isinstance(v, (str, int)) and str(v):
            task_id = str(v)

    if not audio_url and task_id:
        polled = poll_task(ak, sk, task_id, timeout_seconds)
        log_id = polled.log_id or log_id
        if polled.failure_code is not None or (polled.audio_url is None and polled.failure_msg):
            return {
                "audio_file": None,
                "duration": duration,
                "log_id": log_id,
                "action": SUBMIT_ACTION,
                "task_id": task_id,
                "request_body": body,
                "error": explain_error(
                    polled.failure_code if polled.failure_code is not None else 300030,
                    polled.failure_msg or "task failed",
                ),
            }
        audio_url = polled.audio_url

    if not audio_url:
        return {
            "audio_file": None,
            "duration": duration,
            "log_id": log_id,
            "action": SUBMIT_ACTION,
            "request_body": body,
            "raw_result": result,
            "error": "Submit succeeded but no AudioUrl returned and no TaskId to poll.",
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        final_path = download_audio(audio_url, out_path)
    except requests.RequestException as e:
        return {
            "audio_file": None, "duration": duration, "log_id": log_id,
            "action": SUBMIT_ACTION, "request_body": body,
            "error": f"Audio download failed: {e}",
        }

    if format == "mp3":
        mp3_path = final_path.with_suffix(".mp3")
        try:
            final_path = transcode_to_mp3(final_path, mp3_path)
        except SystemExit as exc:
            return {
                "audio_file": str(final_path),  # keep the wav; user can retry
                "duration": duration, "log_id": log_id,
                "action": SUBMIT_ACTION, "request_body": body,
                "wav_file": str(final_path),
                "error": str(exc),
            }

    return {
        "audio_file": str(final_path),
        "duration": duration,
        "log_id": log_id,
        "action": SUBMIT_ACTION,
        "request_body": body,
        "source": "url",
        "audio_url": audio_url,
        "error": None,
    }


# ── CLI ─────────────────────────────────────────────────────────────────────


def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"audio_file": None, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="volcengine-bigmusic-bgm",
        description="火山引擎 BigMusic (Seed-Music) — instrumental BGM generation",
    )
    parser.add_argument("text", help="Chinese style description, e.g. '关于星空的背景纯音乐，钢琴加吉他'")
    parser.add_argument("--duration", "-d", type=int, default=60,
                        help=f"Duration in seconds [{MIN_DURATION},{MAX_DURATION}] (default: 60)")
    parser.add_argument("--out", "-o", default="./bgm.wav",
                        help="Output audio file path (default: ./bgm.wav; suffix is rewritten to match the real format)")
    parser.add_argument("--rewrite", action="store_true",
                        help="EnableInputRewrite — let the model rewrite/expand the prompt (helps dodge 50000001 similarity checks).")
    parser.add_argument("--format", choices=["wav", "mp3"], default="wav",
                        help="Output container. wav = original (lossless, 10MB/min). mp3 = ffmpeg-transcoded (smaller).")
    parser.add_argument("--timeout", type=int, default=DEFAULT_POLL_TIMEOUT_SECONDS,
                        help=f"Async poll timeout in seconds (default: {DEFAULT_POLL_TIMEOUT_SECONDS}).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request body without calling the API.")
    parser.add_argument("--meta", action="store_true",
                        help="Also write a <out>.meta.json sidecar with the full result.")

    args = parser.parse_args()

    if not (MIN_DURATION <= args.duration <= MAX_DURATION):
        die(f"Duration {args.duration}s out of range; v5.0 supports [{MIN_DURATION},{MAX_DURATION}] seconds.")

    if not args.text.strip():
        die("Empty Text prompt; supply a Chinese style description.")

    out_path = Path(args.out)
    result = generate(
        args.text,
        args.duration,
        out_path,
        rewrite=args.rewrite,
        format=args.format,
        timeout_seconds=args.timeout,
        dry_run=args.dry_run,
    )

    if args.meta and result.get("audio_file"):
        meta_path = Path(result["audio_file"]).with_suffix(Path(result["audio_file"]).suffix + ".meta.json")
        meta_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
