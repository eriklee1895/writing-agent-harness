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

API_BASE = "https://openspeech.bytedance.com"
ENDPOINT = f"{API_BASE}/api/v3/tts/create"
DEFAULT_MODEL = "seed-audio-1.0"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CONCURRENCY = 3
MAX_PROMPT_CHARS = 3000
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


def synthesize(prompt: str, *, api_key: str,
               references: list[dict] | None = None,
               audio_config: dict | None = None,
               watermark: dict | None = None,
               model: str = DEFAULT_MODEL,
               output_dir: Path = Path("./seedaudio-output"),
               enable_subtitle: bool = False) -> dict[str, Any]:
    """Call seed-audio API. Returns dict with audio_file, durations, url, meta fields, error."""
    validate_prompt_length(prompt)
    body = build_body(prompt, references=references, audio_config=audio_config, watermark=watermark, model=model)
    headers = {"X-Api-Key": api_key, "X-Api-Request-Id": str(uuid.uuid4()), "Content-Type": "application/json"}
    log_id = ""
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=httpx.Timeout(300.0, connect=10.0)) as c:
            r = c.post(ENDPOINT, headers=headers, json=body)
            log_id = r.headers.get("X-Tt-Logid", "")
            elapsed = time.perf_counter() - t0
            data = r.json()
            if r.status_code != 200 or "audio" not in data:
                return {"audio_file": None, "error": f"{data.get('code','')}: {data.get('message', r.text[:200])}",
                        "log_id": log_id, "elapsed_s": round(elapsed, 2), "text_prompt": prompt}
            audio_bytes = base64.b64decode(data["audio"])
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
            fname = output_dir / f"seedaudio_{ts}_{uuid.uuid4().hex[:6]}.mp3"
            fname.write_bytes(audio_bytes)
            dur = float(data.get("duration") or 0)
            orig_dur = float(data.get("original_duration") or dur)
            url = data.get("url", "")
            sub = data.get("subtitle")
            fetched = now_iso()
            result = {
                "audio_file": str(fname),
                "duration": round(dur, 2),
                "original_duration": round(orig_dur, 2),
                "url": url,
                "fetched_at": fetched,
                "url_expires_at": _expires_at(fetched, hours=2),
                "subtitle": sub,
                "log_id": log_id,
                "model": model,
                "text_prompt": prompt,
                "estimated_cost_yuan": estimate_cost(orig_dur),
                "elapsed_s": round(elapsed, 2),
                "error": None,
            }
            # write meta sidecar
            meta_path = fname.with_suffix(".meta.json")
            meta_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            return result
    except Exception as e:
        return {"audio_file": None, "error": f"{type(e).__name__}: {e}", "log_id": log_id,
                "elapsed_s": round(time.perf_counter() - t0, 2), "text_prompt": prompt}


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Volcengine seed-audio-1.0 audio generation")
    parser.add_argument("prompt", nargs="?", help="text_prompt (natural language scene description, max 3000 chars)")
    parser.add_argument("-o", "--output-dir", default="./seedaudio-output/", help="output directory")
    parser.add_argument("--speaker", help="speaker ID (reuse seed-tts-2.0 voices or cloned voices)")
    parser.add_argument("--ref-audio", help="local reference audio path (auto base64, <=30s, <=10MB)")
    parser.add_argument("--ref-audio-url", help="remote reference audio URL")
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
                        output_dir=Path(args.output_dir), enable_subtitle=args.subtitle)
    print(json.dumps(result, ensure_ascii=False))


def _build_references(args) -> list[dict] | None:
    refs: list[dict] = []
    if args.speaker:
        refs.append({"speaker": args.speaker})
    elif args.ref_audio:
        p = Path(args.ref_audio)
        if not p.exists():
            die(f"--ref-audio file not found: {args.ref_audio}")
        refs.append({"audio_data": base64.b64encode(p.read_bytes()).decode()})
    elif args.ref_audio_url:
        refs.append({"audio_url": args.ref_audio_url})
    if args.ref_image:
        p = Path(args.ref_image)
        if not p.exists():
            die(f"--ref-image file not found: {args.ref_image}")
        refs.append({"image_data": base64.b64encode(p.read_bytes()).decode()})
    elif args.ref_image_url:
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
        prompt = item.pop("prompt") or item.pop("text_prompt") or ""
        if not prompt:
            return {"error": f"item {i}: missing prompt"}
        # item 里可 override speaker/format 等
        refs = list(item.get("references") or [])
        if not refs and item.get("speaker"):
            refs = [{"speaker": item["speaker"]}]
        cfg = {"format": item.get("format", args.format), "sample_rate": item.get("sample_rate", args.sample_rate)}
        if item.get("speech_rate", 0) != 0: cfg["speech_rate"] = item["speech_rate"]
        result = synthesize(prompt, api_key=api_key, references=refs or None, audio_config=cfg,
                            model=args.model, output_dir=Path(args.output_dir),
                            enable_subtitle=item.get("subtitle", args.subtitle))
        return result

    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(task, i, dict(item)): i for i, item in enumerate(items)}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    print(json.dumps(build_batch_summary(results), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()