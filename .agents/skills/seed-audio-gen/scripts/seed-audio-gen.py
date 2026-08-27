#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx>=0.27",
#   "mutagen>=1.47",
#   "python-dotenv>=1.0",
# ]
# ///
"""seed-audio-gen — Volcengine Doubao Audio Generation 1.0 (seed-audio-1.0).

Single sentence:
    uv run seed-audio-gen.py "一位女声朗读：你好世界"

Batch:
    uv run seed-audio-gen.py --batch '[{"prompt":"..."},{"prompt":"..."}]'

List speakers:
    uv run seed-audio-gen.py --list-speakers

API: POST https://openspeech.bytedance.com/api/v3/tts/create (non-streaming)
Auth: X-Api-Key only (no X-Api-Resource-Id, unlike seed-tts-2.0)
"""
from __future__ import annotations
import argparse, base64, json, os, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from mutagen import File as _mutagen_File

API_BASE = "https://openspeech.bytedance.com"
ENDPOINT = f"{API_BASE}/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CONCURRENCY = 3
MAX_PROMPT_CHARS = 3000
MAX_AUDIO_REFS = 3  # API accepts 1-3 reference audios per call (official API doc limit)
MAX_RETRIES = 3  # exponential backoff for transient failures: 1s, 2s, 4s
RETRY_BACKOFF_BASE = 1.0  # seconds, delay = base * 2^attempt
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}  # rate-limited / gateway / service
RETRYABLE_VOLCANO_CODES = {"55000000"}  # service internal errors (shared with seed-tts-2.0)
# Reference media limits (official API doc 2550782). Enforced locally, before any
# base64 encode / upload, so an oversized reference fails fast with an actionable
# error instead of a remote API rejection after uploading.
MAX_REF_AUDIO_SECONDS = 30
MAX_REF_AUDIO_BYTES = 10 * 1024 * 1024   # 10MB per reference audio
MAX_REF_IMAGE_BYTES = 10 * 1024 * 1024   # 10MB per reference image
COST_PER_MINUTE_YUAN = 1.0  # 后付费 1 元/分钟

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SPEAKERS_JSON = SKILL_DIR / "references" / "speakers.json"


class PromptTooLongError(Exception):
    """text_prompt 超过 3000 字符"""


def validate_prompt_length(prompt: str) -> None:
    if len(prompt) > MAX_PROMPT_CHARS:
        raise PromptTooLongError(
            f"ERROR 45001116: text_prompt length {len(prompt)} exceeds maximum of {MAX_PROMPT_CHARS} chars.\n"
            f"Hint: split your prompt into multiple calls, or shorten the scene description.\n"
            f"Each call generates up to 120s of audio. 人声播报字数建议中文控制在 400 字以内."
        )


def load_api_key() -> str:
    key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
    if key:
        return key
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key
    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key
    die("VOLC_SPEECH_API_KEY not found. Set via env, .env, or ~/.volcengine.env")


def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def _check_local_ref_audio(path: Path) -> None:
    """Pre-flight a local reference audio file before base64/encode/upload:
    size <= 10MB and (when mutagen can read the header) duration <= 30s.
    Raises SystemExit via die() with measured values so the agent can fix it."""
    size = path.stat().st_size
    if size > MAX_REF_AUDIO_BYTES:
        die(f"--ref-audio too large: {path.name} is {size/1024/1024:.1f}MB, "
            f"limit {MAX_REF_AUDIO_BYTES/1024/1024:.0f}MB. Trim the clip or host it remotely "
            f"and use --ref-audio-url.")
    audio = _mutagen_File(path)
    if audio is not None and getattr(getattr(audio, "info", None), "length", None) is not None:
        dur = float(audio.info.length)
        if dur > MAX_REF_AUDIO_SECONDS:
            die(f"--ref-audio too long: {path.name} is {dur:.1f}s, limit {MAX_REF_AUDIO_SECONDS}s. "
                f"Trim to a <= {MAX_REF_AUDIO_SECONDS}s clip (a clean sample of the voice is enough), "
                f"or host remotely and use --ref-audio-url.")


def _check_local_ref_image(path: Path) -> None:
    """Pre-flight a local reference image: size <= 10MB."""
    size = path.stat().st_size
    if size > MAX_REF_IMAGE_BYTES:
        die(f"--ref-image too large: {path.name} is {size/1024/1024:.1f}MB, "
            f"limit {MAX_REF_IMAGE_BYTES/1024/1024:.0f}MB. Shrink/compress the image "
            f"(jpeg/png/webp) or host it and use --ref-image-url.")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def estimate_cost(original_duration_s: float) -> float:
    return round(original_duration_s / 60.0 * COST_PER_MINUTE_YUAN, 2)


def build_body(prompt: str, *, references: list[dict] | None, audio_config: dict | None,
               watermark: dict | None, model: str = DEFAULT_MODEL) -> dict:
    body: dict[str, Any] = {"model": model, "text_prompt": prompt}
    if references:
        body["references"] = references
    if audio_config:
        body["audio_config"] = audio_config
    if watermark:
        w: dict[str, Any] = {}
        if watermark.get("aigc"):
            w["aigc_watermark"] = True
        if "meta" in watermark:
            w["aigc_metadata"] = {"enable": bool(watermark["meta"])}
        body["watermark"] = w
    return body


def is_retryable(status_code: Optional[int], volcano_code: Any) -> bool:
    """A failure is worth retrying only if it is transient: rate-limiting,
    gateway/service errors, or a Volcano service-internal code. Client errors
    (4xx other than 429 — bad auth, bad prompt, unsupported params) are
    deterministic and fail fast with no retry."""
    if status_code in RETRYABLE_HTTP_STATUS:
        return True
    if volcano_code is not None and str(volcano_code) in RETRYABLE_VOLCANO_CODES:
        return True
    return False


def _post_once(client: httpx.Client, headers: dict, body: dict) -> dict:
    """One create-API POST. Returns a status dict without raising:
    {"ok": True, "data": <json>} or {"ok": False, "status", "code", "message",
    "log_id"} / {"ok": False, "exc": <Exception>, ...}."""
    try:
        r = client.post(ENDPOINT, headers=headers, json=body)
        log_id = r.headers.get("X-Tt-Logid", "")
        try:
            data = r.json()
        except Exception:
            data = {}
        if r.status_code == 200 and "audio" in data:
            return {"ok": True, "data": data, "log_id": log_id}
        return {"ok": False, "status": r.status_code, "log_id": log_id,
                "code": data.get("code"), "message": data.get("message") or r.text[:200]}
    except Exception as e:
        # network-level transient errors (connect/timeout/reset) are retryable
        return {"ok": False, "status": None, "code": None, "message": f"{type(e).__name__}: {e}",
                "exc": e, "retryable": True}


def synthesize(prompt: str, *, api_key: str,
               references: list[dict] | None = None,
               audio_config: dict | None = None,
               watermark: dict | None = None,
               model: str = DEFAULT_MODEL,
               output_dir: Path = Path("./seedaudio-output")) -> dict[str, Any]:
    """Call seed-audio API with exponential backoff on transient failures.
    Returns dict with audio_file, durations, url, meta fields, error."""
    validate_prompt_length(prompt)
    body = build_body(prompt, references=references, audio_config=audio_config, watermark=watermark, model=model)
    t0 = time.perf_counter()
    last = {"code": None, "message": "no response", "log_id": "", "retryable": True}
    attempts = 0
    try:
        with httpx.Client(timeout=httpx.Timeout(300.0, connect=10.0)) as c:
            for attempt in range(MAX_RETRIES + 1):
                attempts = attempt + 1
                # fresh request id per try; keep a stable body
                headers = {"X-Api-Key": api_key, "X-Api-Request-Id": str(uuid.uuid4()),
                           "Content-Type": "application/json"}
                out = _post_once(c, headers, body)
                elapsed = time.perf_counter() - t0
                if out.get("ok"):
                    data = out["data"]
                    log_id = out.get("log_id", "")
                    audio_bytes = base64.b64decode(data["audio"])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    ts = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
                    ext = audio_config.get("format", "mp3") if audio_config else "mp3"
                    fname = output_dir / f"seedaudio_{ts}_{uuid.uuid4().hex[:6]}.{ext}"
                    fname.write_bytes(audio_bytes)
                    dur = float(data.get("duration") or 0)
                    orig_dur = float(data.get("original_duration") or dur)
                    fetched = now_iso()
                    result = {
                        "audio_file": str(fname),
                        "duration": round(dur, 2),
                        "original_duration": round(orig_dur, 2),
                        "url": data.get("url", ""),
                        "fetched_at": fetched,
                        "url_expires_at": _expires_at(fetched, hours=2),
                        "subtitle": data.get("subtitle"),
                        "log_id": log_id,
                        "model": model,
                        "text_prompt": prompt,
                        "estimated_cost_yuan": estimate_cost(orig_dur),
                        "elapsed_s": round(elapsed, 2),
                        "attempts": attempts,
                        "error": None,
                    }
                    meta_path = fname.with_suffix(".meta.json")
                    meta_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                # failure: decide retry
                last = out
                last.setdefault("retryable", False)
                if not is_retryable(out.get("status"), out.get("code")) and not out.get("retryable"):
                    break  # deterministic client error — fail fast, no retry
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))
            # exhausted retries (or deterministic failure)
            elapsed = time.perf_counter() - t0
            code = last.get("code")
            msg = last.get("message") or last.get("exc") or "request failed"
            return {"audio_file": None,
                    "error": f"{f'{code}: ' if code is not None else ''}{msg}",
                    "log_id": last.get("log_id", ""),
                    "elapsed_s": round(elapsed, 2),
                    "attempts": attempts,
                    "text_prompt": prompt}
    except Exception as e:
        return {"audio_file": None, "error": f"{type(e).__name__}: {e}",
                "log_id": last.get("log_id", ""),
                "elapsed_s": round(time.perf_counter() - t0, 2),
                "attempts": attempts, "text_prompt": prompt}


def _expires_at(fetched_iso: str, *, hours: int = 2) -> str:
    """CDN URL 2h 有效，计算过期时间"""
    try:
        dt = datetime.fromisoformat(fetched_iso)
        return (dt + _timedelta(hours=hours)).isoformat()
    except Exception:
        return ""


def _timedelta(*, hours: int = 0):
    from datetime import timedelta
    return timedelta(hours=hours)


class _AppendRef(argparse.Action):
    """Append a (kind, value) tuple to a shared dest, preserving CLI order
    across --ref-audio (local path) and --ref-audio-url (remote URL). The
    kind is decided by which flag was used — not by sniffing the value — so
    mixed calls like `--ref-audio a.wav --ref-audio-url https://.../b.wav`
    keep their @音频N order."""

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        kind = "url" if option_string and option_string.endswith("-url") else "path"
        items.append((kind, values))
        setattr(namespace, self.dest, items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Volcengine seed-audio-1.0 audio generation")
    parser.add_argument("prompt", nargs="?", help="text_prompt (natural language scene description, max 3000 chars)")
    parser.add_argument("-o", "--output-dir", default="./seedaudio-output/", help="output directory")
    parser.add_argument("--speaker", help="speaker ID (reuse seed-tts-2.0 voices or cloned voices)")
    parser.add_argument("--ref-audio", action=_AppendRef, dest="ref_audios", metavar="PATH",
                        help="local reference audio path (auto base64, each <=30s, <=10MB). "
                             "Repeat up to 3 times for multi-character voice cloning; bind in "
                             "prompt with @音频1..@音频3 in CLI order")
    parser.add_argument("--ref-audio-url", action=_AppendRef, dest="ref_audios", metavar="URL",
                        help="remote reference audio URL. Same repeat/@音频N ordering as --ref-audio; "
                             "the two flags can be mixed and order is preserved")
    parser.add_argument("--ref-image", help="local reference image path (auto base64, <=10MB)")
    parser.add_argument("--ref-image-url", help="remote reference image URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="model version (default: seed-audio-1.0)")
    parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["wav","mp3","pcm","ogg_opus"])
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--speech-rate", type=int, default=0)
    parser.add_argument("--loudness-rate", type=int, default=0)
    parser.add_argument("--pitch-rate", type=int, default=0)
    parser.add_argument("--subtitle", action="store_true", help="enable subtitle (sentence+word timestamps)")
    parser.add_argument("--watermark", action="store_true", help="AIGC explicit watermark")
    parser.add_argument("--watermark-meta", action="store_true", help="implicit meta watermark")
    parser.add_argument("--batch", help="batch JSON array")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--list-speakers", action="store_true", help="list speakers from local table")
    parser.add_argument("--filter", action="append", help="filter: scene=视频配音 / type=bigtts / lang=ja")
    parser.add_argument("--sort", choices=["heat"], help="sort by field")
    args = parser.parse_args()

    if args.list_speakers:
        _list_speakers(args)
        return
    if args.batch:
        _run_batch(args)
        return
    if not args.prompt:
        parser.error("prompt is required (or use --batch / --list-speakers)")

    api_key = load_api_key()
    references = _build_references(args)
    audio_config = _build_audio_config(args)
    watermark = {"aigc": args.watermark, "meta": args.watermark_meta} if (args.watermark or args.watermark_meta) else None
    result = synthesize(args.prompt, api_key=api_key, references=references,
                        audio_config=audio_config, watermark=watermark, model=args.model,
                        output_dir=Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False))


def _build_references(args) -> list[dict] | None:
    refs: list[dict] = []
    ref_audios: list[tuple[str, str]] = getattr(args, "ref_audios", None) or []
    if args.speaker and ref_audios:
        die("--speaker and --ref-audio are mutually exclusive (pick one voice source)")
    if len(ref_audios) > MAX_AUDIO_REFS:
        die(f"too many reference audios: {len(ref_audios)} (max {MAX_AUDIO_REFS}). "
            f"Bind them in the prompt with @音频1..@音频{MAX_AUDIO_REFS} in CLI order.")
    if args.speaker:
        refs.append({"speaker": args.speaker})
    for kind, ref in ref_audios:
        if kind == "url":
            if not ref.startswith(("http://", "https://")):
                die(f"--ref-audio-url expects an http(s) URL, got: {ref} "
                    f"(for a local file use --ref-audio)")
            refs.append({"audio_url": ref})
        else:
            if ref.startswith(("http://", "https://")):
                die(f"--ref-audio expects a local file path, got a URL: {ref} "
                    f"(use --ref-audio-url for remote audio)")
            p = Path(ref)
            if not p.exists():
                die(f"--ref-audio file not found: {ref}")
            _check_local_ref_audio(p)
            refs.append({"audio_data": base64.b64encode(p.read_bytes()).decode()})
    if args.ref_image:
        p = Path(args.ref_image)
        if not p.exists():
            die(f"--ref-image file not found: {args.ref_image}")
        if ref_audios or args.speaker:
            # API 45001001: image reference cannot be mixed with audio or video references;
            # doc: image_data/image_url 不能与 audio_data、audio_url 或 speaker 同时传入
            die("image reference cannot be mixed with audio references or --speaker (API 45001001)")
        _check_local_ref_image(p)
        refs.append({"image_data": base64.b64encode(p.read_bytes()).decode()})
    elif args.ref_image_url:
        if ref_audios or args.speaker:
            die("image reference cannot be mixed with audio references or --speaker (API 45001001)")
        refs.append({"image_url": args.ref_image_url})
    return refs if refs else None


def _build_audio_config(args) -> dict:
    cfg: dict[str, Any] = {"format": args.format, "sample_rate": args.sample_rate}
    if args.speech_rate != 0: cfg["speech_rate"] = args.speech_rate
    if args.loudness_rate != 0: cfg["loudness_rate"] = args.loudness_rate
    if args.pitch_rate != 0: cfg["pitch_rate"] = args.pitch_rate
    if args.subtitle: cfg["enable_subtitle"] = True
    return cfg


def query_speakers(speakers: list[dict], *, filters: dict | None = None, sort_by: str | None = None) -> list[dict]:
    result = list(speakers)
    if filters:
        for k, v in filters.items():
            if k == "lang":
                result = [s for s in result if v in s.get("languages", [])]
            else:
                result = [s for s in result if s.get(k) == v]
    if sort_by == "heat":
        result = sorted(result, key=lambda s: -s.get("heat", 0))
    return result


def _list_speakers(args):
    if not SPEAKERS_JSON.exists():
        die(f"speakers.json not found: {SPEAKERS_JSON}")
    speakers = json.loads(SPEAKERS_JSON.read_text())
    filters = {}
    if args.filter:
        for f in args.filter:
            k, _, v = f.partition("=")
            filters[k] = v
    result = query_speakers(speakers, filters=filters or None, sort_by=args.sort)
    out = [{"name": s["name"], "voice_type": s["voice_type"], "type": s["type"],
            "gender": s.get("gender",""), "scene": s.get("scene",""),
            "description": s.get("description","")[:40], "heat": s.get("heat",0)} for s in result]
    print(json.dumps({"total": len(out), "speakers": out}, ensure_ascii=False, indent=2))


def build_batch_summary(results: list[dict]) -> dict:
    total_dur = sum(r.get("original_duration") or 0 for r in results)
    success = sum(1 for r in results if not r.get("error"))
    fail = sum(1 for r in results if r.get("error"))
    return {
        "results": results,
        "total_duration_seconds": round(total_dur, 2),
        "estimated_cost_yuan": estimate_cost(total_dur),
        "success_count": success,
        "fail_count": fail,
    }


def _run_batch(args):
    api_key = load_api_key()
    try:
        items = json.loads(args.batch)
    except json.JSONDecodeError as e:
        die(f"--batch invalid JSON: {e}")
    if not isinstance(items, list):
        die("--batch must be a JSON array")

    def task(i: int, item: dict) -> dict:
        prompt = item.pop("prompt", None) or item.pop("text_prompt", None) or ""
        if not prompt:
            return {"error": f"item {i}: missing prompt"}
        # item 里可 override speaker/format 等
        refs = list(item.get("references") or [])
        if not refs and item.get("speaker"):
            refs = [{"speaker": item["speaker"]}]
        cfg = {"format": item.get("format", args.format), "sample_rate": item.get("sample_rate", args.sample_rate)}
        if item.get("speech_rate", 0) != 0: cfg["speech_rate"] = item["speech_rate"]
        if item.get("subtitle", args.subtitle): cfg["enable_subtitle"] = True
        result = synthesize(prompt, api_key=api_key, references=refs or None, audio_config=cfg,
                            model=args.model, output_dir=Path(args.output_dir))
        return result

    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(task, i, dict(item)): i for i, item in enumerate(items)}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    print(json.dumps(build_batch_summary(results), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()