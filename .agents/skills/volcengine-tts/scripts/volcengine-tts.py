#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests>=2.32",
#   "mutagen>=1.47",
#   "python-dotenv>=1.0",
# ]
# ///

"""
Volcengine TTS — Doubao Speech Synthesis Model 2.0 (seed-tts-2.0).

Single sentence:
    uv run volcengine-tts.py "你好世界"

Batch mode:
    uv run volcengine-tts.py --batch '[{"text":"第一句"},{"text":"第二句"}]'

List speakers:
    uv run volcengine-tts.py --list-speakers

API docs: https://www.volcengine.com/docs/6561/2528925?lang=zh
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from mutagen.mp3 import MP3

# ── API constants ──────────────────────────────────────────────────────────

API_BASE = "https://openspeech.bytedance.com"
TTS_ENDPOINT = f"{API_BASE}/api/v3/tts/unidirectional"
LIST_SPEAKERS_ENDPOINT = "https://open.volcengineapi.com"
LIST_SPEAKERS_ACTION = "ListSpeakers"
LIST_SPEAKERS_VERSION = "2024-01-01"

RESOURCE_ID = "seed-tts-2.0"
DEFAULT_SPEAKER = "zh_female_vv_uranus_bigtts"
DEFAULT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CONCURRENCY = 3
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # seconds, exponential: base * 2^attempt

# Error codes that warrant a retry
RETRYABLE_VOLCANO_CODES = {"55000000"}  # service internal errors
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}

# API success codes (volcano v3 uses 20000000 for success, 0 is also valid)
API_SUCCESS_CODES = {0, 20000000}


# ── Environment ────────────────────────────────────────────────────────────

def load_api_key() -> str:
    """Load VOLC_SPEECH_API_KEY with three-level fallback."""
    # Level 1: already in environment
    key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
    if key:
        return key

    # Level 2: .env in current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key

    # Level 3: user-level config
    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        key = os.environ.get("VOLC_SPEECH_API_KEY", "").strip()
        if key:
            return key

    die("VOLC_SPEECH_API_KEY not found. Set it via environment, .env file, or ~/.volcengine.env")


# ── Helpers ────────────────────────────────────────────────────────────────

def die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def get_mp3_duration_ms(path: Path) -> int:
    """Read MP3 duration in milliseconds from file header."""
    try:
        audio = MP3(str(path))
        if audio.info.length is not None:
            return int(audio.info.length * 1000)
    except Exception:
        pass
    return 0


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# ── Retry ──────────────────────────────────────────────────────────────────

def is_retryable(status_code: int, volcano_code: Optional[str]) -> bool:
    if status_code in RETRYABLE_HTTP_STATUS:
        return True
    if volcano_code and volcano_code in RETRYABLE_VOLCANO_CODES:
        return True
    return False


# ── TTS API call ───────────────────────────────────────────────────────────

def synthesize(
    text: str,
    *,
    api_key: str,
    speaker: str = DEFAULT_SPEAKER,
    fmt: str = DEFAULT_FORMAT,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    pitch: int = 0,
    model: Optional[str] = None,
    ssml: bool = False,
    context_texts: Optional[list[str]] = None,
    language: Optional[str] = None,
    dialect: Optional[str] = None,
    enable_latex: bool = False,
    latex_parser: Optional[str] = None,
    silence_duration: int = 0,
    watermark: bool = False,
    disable_markdown_filter: bool = False,
    disable_emoji_filter: bool = False,
    enable_subtitle: bool = True,
) -> dict[str, Any]:
    """Call the Volcengine TTS HTTP unidirectional streaming API.

    Returns a dict with keys: audio_data (bytes), text_words, log_id,
    words (list of word-level timestamps, empty unless enable_subtitle=True),
    sentence_text (str), error.
    On success, error is None. On failure, audio_data is empty.
    """
    request_id = str(uuid.uuid4())
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-Request-Id": request_id,
        "X-Control-Require-Usage-Tokens-Return": "*",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    }

    audio_params: dict[str, Any] = {
        "format": fmt,
        "sample_rate": sample_rate,
    }
    if speech_rate != 0:
        audio_params["speech_rate"] = speech_rate
    if loudness_rate != 0:
        audio_params["loudness_rate"] = loudness_rate
    if enable_subtitle:
        audio_params["enable_subtitle"] = True

    body: dict[str, Any] = {
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": audio_params,
        }
    }
    additions: dict[str, Any] = {}

    if model:
        body["req_params"]["model"] = model
    if ssml:
        body["req_params"]["ssml"] = "1"
    if context_texts:
        body["req_params"]["context_texts"] = context_texts
    if language:
        body["req_params"]["explicit_language"] = language
    if dialect:
        body["req_params"]["explicit_dialect"] = dialect
    if enable_latex or latex_parser:
        additions["enable_latex_tn"] = True
        additions["disable_markdown_filter"] = True
    if latex_parser:
        additions["latex_parser"] = latex_parser
    if silence_duration > 0:
        additions["silence_duration"] = silence_duration
    if watermark:
        additions["aigc_watermark"] = True
    if disable_markdown_filter:
        additions["disable_markdown_filter"] = True
    if disable_emoji_filter:
        additions["disable_emoji_filter"] = True
    if pitch != 0:
        additions["post_process"] = {"pitch": pitch}
    if additions:
        body["req_params"]["additions"] = additions

    last_error: Optional[str] = None
    log_id: str = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                TTS_ENDPOINT,
                headers=headers,
                json=body,
                stream=True,
                timeout=60,
            )
            log_id = resp.headers.get("X-Tt-Logid", "")

            if not resp.ok:
                volcano_code = None
                try:
                    error_data = resp.json()
                    volcano_code = str(error_data.get("code", ""))
                    last_error = f"{volcano_code}: {error_data.get('message', resp.text)}"
                except Exception:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

                if is_retryable(resp.status_code, volcano_code) and attempt < MAX_RETRIES:
                    delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                    time.sleep(delay)
                    continue
                return {
                    "audio_data": b"",
                    "text_words": 0,
                    "log_id": log_id,
                    "error": last_error,
                }

            # Read chunked response
            audio_chunks: list[bytes] = []
            text_words = 0
            words: list[dict[str, Any]] = []
            sentence_text: str = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue

                code = chunk.get("code", -1)
                if code not in API_SUCCESS_CODES:
                    volcano_code = str(code)
                    msg = chunk.get("message", "unknown error")
                    last_error = f"{volcano_code}: {msg}"

                    if is_retryable(resp.status_code, volcano_code) and attempt < MAX_RETRIES:
                        delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                        time.sleep(delay)
                        break  # break inner loop, retry outer
                    return {
                        "audio_data": b"",
                        "text_words": 0,
                        "words": [],
                        "sentence_text": "",
                        "log_id": log_id,
                        "error": last_error,
                    }

                data_b64 = chunk.get("data", "")
                if data_b64:
                    try:
                        audio_chunks.append(base64.b64decode(data_b64))
                    except Exception:
                        pass

                sentence = chunk.get("sentence")
                if isinstance(sentence, dict):
                    sentence_text = sentence.get("text", sentence_text) or sentence_text
                    sw = sentence.get("words")
                    if isinstance(sw, list) and sw:
                        # Server may send words split across chunks; dedupe by (word, startTime, endTime)
                        seen: set[tuple[str, float, float]] = set()
                        merged: list[dict[str, Any]] = []
                        for w in words + sw:
                            key = (str(w.get("word", "")), float(w.get("startTime", 0.0)), float(w.get("endTime", 0.0)))
                            if key in seen:
                                continue
                            seen.add(key)
                            merged.append(w)
                        words = merged

                usage = chunk.get("usage", {})
                if isinstance(usage, dict):
                    text_words = usage.get("text_words", text_words)

            if last_error and attempt < MAX_RETRIES:
                continue

            return {
                "audio_data": b"".join(audio_chunks),
                "text_words": text_words,
                "words": words,
                "sentence_text": sentence_text,
                "log_id": log_id,
                "error": last_error if last_error else None,
            }

        except requests.RequestException as e:
            last_error = f"Request error: {e}"
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF_BASE * (2 ** attempt)
                time.sleep(delay)
                continue
            return {
                "audio_data": b"",
                "text_words": 0,
                "words": [],
                "sentence_text": "",
                "log_id": log_id,
                "error": last_error,
            }

    return {
        "audio_data": b"",
        "text_words": 0,
        "words": [],
        "sentence_text": "",
        "log_id": log_id,
        "error": last_error or "Max retries exceeded",
    }


# ── Single synthesis ───────────────────────────────────────────────────────

def synthesize_one(
    text: str,
    output_dir: Path,
    *,
    api_key: str,
    speaker: str = DEFAULT_SPEAKER,
    **kwargs: Any,
) -> dict[str, Any]:
    """Synthesize one sentence, save audio + metadata, return result dict."""
    result = synthesize(text, api_key=api_key, speaker=speaker, **kwargs)

    timestamp = now_iso()
    # Use a simple counter embedded in the function's closure-like state
    seq = synthesize_one._seq if hasattr(synthesize_one, "_seq") else 0
    synthesize_one._seq = seq + 1  # type: ignore[attr-defined]

    filename = f"tts_{timestamp}_{seq:03d}"
    audio_path = output_dir / f"{filename}.{kwargs.get('fmt', DEFAULT_FORMAT)}"
    meta_path = output_dir / f"{filename}.meta.json"

    error = result.get("error")
    duration_ms = 0

    if not error and result["audio_data"]:
        ensure_dir(output_dir)
        audio_path.write_bytes(result["audio_data"])
        duration_ms = get_mp3_duration_ms(audio_path)

    meta: dict[str, Any] = {
        "text": text,
        "speaker": speaker,
        "format": kwargs.get("fmt", DEFAULT_FORMAT),
        "sample_rate": kwargs.get("sample_rate", DEFAULT_SAMPLE_RATE),
        "text_words": result["text_words"],
        "log_id": result["log_id"],
        "duration_ms": duration_ms,
        "error": error,
    }
    if result.get("words"):
        meta["words"] = result["words"]
    if result.get("sentence_text"):
        meta["sentence_text"] = result["sentence_text"]

    if not error and result["audio_data"]:
        ensure_dir(output_dir)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "audio_file": str(audio_path) if not error else None,
        "duration_ms": duration_ms,
        "text": text,
        "speaker": speaker,
        "format": kwargs.get("fmt", DEFAULT_FORMAT),
        "sample_rate": kwargs.get("sample_rate", DEFAULT_SAMPLE_RATE),
        "text_words": result["text_words"],
        "log_id": result["log_id"],
        "words": result.get("words", []),
        "sentence_text": result.get("sentence_text", ""),
        "error": error,
    }


# ── Batch synthesis ────────────────────────────────────────────────────────

def synthesize_batch(
    items: list[dict[str, Any]],
    output_dir: Path,
    *,
    api_key: str,
    concurrency: int = DEFAULT_CONCURRENCY,
    base_kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Synthesize multiple sentences concurrently."""
    results: list[Optional[dict[str, Any]]] = [None] * len(items)

    def task(idx: int, item: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        text = item.get("text", "")
        if not text:
            return idx, {"audio_file": None, "duration_ms": 0, "text": "", "error": "Empty text"}

        kwargs = {**base_kwargs}
        kwargs["speaker"] = item.get("speaker", base_kwargs.get("speaker", DEFAULT_SPEAKER))
        # Simple scalar overrides (key in item → kwarg name passed to synthesize())
        scalar_map = {
            "speech_rate": "speech_rate",
            "volume": "loudness_rate",
            "pitch": "pitch",
            "model": "model",
            "language": "language",
            "format": "fmt",
            "sample_rate": "sample_rate",
            "ssml": "ssml",
            "silence_duration": "silence_duration",
            "watermark": "watermark",
            "subtitle": "enable_subtitle",
            "strip_markdown": "disable_markdown_filter",
            "strip_emoji": "disable_emoji_filter",
            "latex": "enable_latex",
            "latex_parser": "latex_parser",
        }
        for item_key, kwarg_key in scalar_map.items():
            if item_key in item:
                kwargs[kwarg_key] = item[item_key]
        # context can come either as a string (single instruction) or list of strings
        if "context" in item:
            ctx = item["context"]
            kwargs["context_texts"] = [ctx] if isinstance(ctx, str) else list(ctx)
        elif "context_texts" in item:
            ctx = item["context_texts"]
            kwargs["context_texts"] = [ctx] if isinstance(ctx, str) else list(ctx)

        return idx, synthesize_one(text, output_dir, api_key=api_key, **kwargs)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(task, i, item): i for i, item in enumerate(items)}
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    valid = [r for r in results if r is not None]
    return {
        "results": valid,
        "total_duration_ms": sum(r.get("duration_ms", 0) for r in valid),
        "success_count": sum(1 for r in valid if not r.get("error")),
        "fail_count": sum(1 for r in valid if r.get("error")),
    }


# ── List speakers ──────────────────────────────────────────────────────────

def list_speakers(api_key: str) -> list[dict[str, Any]]:
    """Fetch available speakers via Volcengine OpenAPI."""
    # Try the ListSpeakers API (volcengine OpenAPI format)
    try:
        resp = requests.post(
            LIST_SPEAKERS_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={
                "Action": LIST_SPEAKERS_ACTION,
                "Version": LIST_SPEAKERS_VERSION,
            },
            params={
                "Action": LIST_SPEAKERS_ACTION,
                "Version": LIST_SPEAKERS_VERSION,
            },
            timeout=30,
        )
        if resp.ok:
            data = resp.json()
            speakers = data.get("Response", {}).get("Speakers", [])
            if speakers:
                return speakers
    except Exception:
        pass

    # Fallback: return the built-in reference list
    return _builtin_speakers()


def _builtin_speakers() -> list[dict[str, Any]]:
    """Built-in speaker catalog for seed-tts-2.0."""
    return [
        {"name": "Vivi 2.0", "voice_type": "zh_female_vv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "小何 2.0", "voice_type": "zh_female_xiaohe_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "云舟 2.0", "voice_type": "zh_male_m191_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "小天 2.0", "voice_type": "zh_male_taocheng_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "刘飞 2.0", "voice_type": "zh_male_liufei_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "魅力苏菲 2.0", "voice_type": "zh_female_sophie_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "清新女声 2.0", "voice_type": "zh_female_qingxinnvsheng_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "知性灿灿 2.0", "voice_type": "zh_female_cancan_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "撒娇学妹 2.0", "voice_type": "zh_female_sajiaoxuemei_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "甜美小源 2.0", "voice_type": "zh_female_tianmeixiaoyuan_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "甜美桃子 2.0", "voice_type": "zh_female_tianmeitaozi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "爽快思思 2.0", "voice_type": "zh_female_shuangkuaisisi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "佩奇猪 2.0", "voice_type": "zh_female_peiqi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "视频配音"},
        {"name": "邻家女孩 2.0", "voice_type": "zh_female_linjianvhai_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "少年梓辛/Brayan 2.0", "voice_type": "zh_male_shaonianzixin_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "猴哥 2.0", "voice_type": "zh_male_sunwukong_uranus_bigtts", "language": "zh", "gender": "male", "scene": "视频配音"},
        {"name": "Tina老师 2.0", "voice_type": "zh_female_yingyujiaoxue_uranus_bigtts", "language": "zh,en-GB", "gender": "female", "scene": "教育场景"},
        {"name": "暖阳女声 2.0", "voice_type": "zh_female_kefunvsheng_uranus_bigtts", "language": "zh", "gender": "female", "scene": "客服场景"},
        {"name": "儿童绘本 2.0", "voice_type": "zh_female_xiaoxue_uranus_bigtts", "language": "zh", "gender": "female", "scene": "有声阅读"},
        {"name": "大壹 2.0", "voice_type": "zh_male_dayi_uranus_bigtts", "language": "zh", "gender": "male", "scene": "视频配音"},
        {"name": "黑猫侦探社咪仔 2.0", "voice_type": "zh_female_mizai_uranus_bigtts", "language": "zh", "gender": "female", "scene": "视频配音"},
        {"name": "鸡汤女 2.0", "voice_type": "zh_female_jitangnv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "视频配音"},
        {"name": "魅力女友 2.0", "voice_type": "zh_female_meilinvyou_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "流畅女声 2.0", "voice_type": "zh_female_liuchangnv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "视频配音"},
        {"name": "儒雅逸辰 2.0", "voice_type": "zh_male_ruyayichen_uranus_bigtts", "language": "zh", "gender": "male", "scene": "视频配音"},
        {"name": "Tim", "voice_type": "en_male_tim_uranus_bigtts", "language": "en-US", "gender": "male", "scene": "多语种"},
        {"name": "Dacey", "voice_type": "en_female_dacey_uranus_bigtts", "language": "en-US", "gender": "female", "scene": "多语种"},
        {"name": "Stokie", "voice_type": "en_female_stokie_uranus_bigtts", "language": "en-US", "gender": "female", "scene": "多语种"},
        {"name": "温柔妈妈 2.0", "voice_type": "zh_female_wenroumama_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "解说小明 2.0", "voice_type": "zh_male_jieshuoxiaoming_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "TVB女声 2.0", "voice_type": "zh_female_tvbnv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "译制片男 2.0", "voice_type": "zh_male_yizhipiannan_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "俏皮女声 2.0", "voice_type": "zh_female_qiaopinv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "直率英子 2.0", "voice_type": "zh_female_zhishuaiyingzi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "邻家男孩 2.0", "voice_type": "zh_male_linjiananhai_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "四郎 2.0", "voice_type": "zh_male_silang_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "儒雅青年 2.0", "voice_type": "zh_male_ruyaqingnian_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "擎苍 2.0", "voice_type": "zh_male_qingcang_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "熊二 2.0", "voice_type": "zh_male_xionger_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "樱桃丸子 2.0", "voice_type": "zh_female_yingtaowanzi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "温暖阿虎/Alvin 2.0", "voice_type": "zh_male_wennuanahu_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "奶气萌娃 2.0", "voice_type": "zh_male_naiqimengwa_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "婆婆 2.0", "voice_type": "zh_female_popo_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "高冷御姐 2.0", "voice_type": "zh_female_gaolengyujie_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "傲娇霸总 2.0", "voice_type": "zh_male_aojiaobazong_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "懒音绵宝 2.0", "voice_type": "zh_male_lanyinmianbao_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "反卷青年 2.0", "voice_type": "zh_male_fanjuanqingnian_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "温柔淑女 2.0", "voice_type": "zh_female_wenroushunv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "古风少御 2.0", "voice_type": "zh_female_gufengshaoyu_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "活力小哥 2.0", "voice_type": "zh_male_huolixiaoge_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "霸气青叔 2.0", "voice_type": "zh_male_baqiqingshu_uranus_bigtts", "language": "zh", "gender": "male", "scene": "有声阅读"},
        {"name": "悬疑解说 2.0", "voice_type": "zh_male_xuanyijieshuo_uranus_bigtts", "language": "zh", "gender": "male", "scene": "有声阅读"},
        {"name": "萌丫头/Cutey 2.0", "voice_type": "zh_female_mengyatou_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "贴心女声/Candy 2.0", "voice_type": "zh_female_tiexinnvsheng_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "鸡汤妹妹/Hope 2.0", "voice_type": "zh_female_jitangmei_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "磁性解说男声/Morgan 2.0", "voice_type": "zh_male_cixingjieshuonan_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "亮嗓萌仔 2.0", "voice_type": "zh_male_liangsangmengzai_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "开朗姐姐 2.0", "voice_type": "zh_female_kailangjiejie_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "高冷沉稳 2.0", "voice_type": "zh_male_gaolengchenwen_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "深夜播客 2.0", "voice_type": "zh_male_shenyeboke_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "鲁班七号 2.0", "voice_type": "zh_male_lubanqihao_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "娇喘女声 2.0", "voice_type": "zh_female_jiaochuannv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "林潇 2.0", "voice_type": "zh_female_linxiao_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "玲玲姐姐 2.0", "voice_type": "zh_female_lingling_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "春日部姐姐 2.0", "voice_type": "zh_female_chunribu_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "唐僧 2.0", "voice_type": "zh_male_tangseng_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "庄周 2.0", "voice_type": "zh_male_zhuangzhou_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "开朗弟弟 2.0", "voice_type": "zh_male_kailangdidi_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "猪八戒 2.0", "voice_type": "zh_male_zhubajie_uranus_bigtts", "language": "zh", "gender": "male", "scene": "角色扮演"},
        {"name": "感冒电音姐姐 2.0", "voice_type": "zh_female_ganmaodianyin_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "谄媚女声 2.0", "voice_type": "zh_female_chanmeinv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "女雷神 2.0", "voice_type": "zh_female_nvleishen_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "亲切女声 2.0", "voice_type": "zh_female_qinqienv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "快乐小东 2.0", "voice_type": "zh_male_kuailexiaodong_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "开朗学长 2.0", "voice_type": "zh_male_kailangxuezhang_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "悠悠君子 2.0", "voice_type": "zh_male_youyoujunzi_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "文静毛毛 2.0", "voice_type": "zh_female_wenjingmaomao_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "知性女声 2.0", "voice_type": "zh_female_zhixingnv_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "清爽男大 2.0", "voice_type": "zh_male_qingshuangnanda_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "渊博小叔 2.0", "voice_type": "zh_male_yuanboxiaoshu_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "阳光青年 2.0", "voice_type": "zh_male_yangguangqingnian_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "清澈梓梓 2.0", "voice_type": "zh_female_qingchezizi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "甜美悦悦 2.0", "voice_type": "zh_female_tianmeiyueyue_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "心灵鸡汤 2.0", "voice_type": "zh_female_xinlingjitang_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "温柔小哥 2.0", "voice_type": "zh_male_wenrouxiaoge_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "柔美女友 2.0", "voice_type": "zh_female_roumeinvyou_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "东方浩然 2.0", "voice_type": "zh_male_dongfanghaoran_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "温柔小雅 2.0", "voice_type": "zh_female_wenrouxiaoya_uranus_bigtts", "language": "zh", "gender": "female", "scene": "通用场景"},
        {"name": "天才童声 2.0", "voice_type": "zh_male_tiancaitongsheng_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "武则天 2.0", "voice_type": "zh_female_wuzetian_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "顾姐 2.0", "voice_type": "zh_female_gujie_uranus_bigtts", "language": "zh", "gender": "female", "scene": "角色扮演"},
        {"name": "广告解说 2.0", "voice_type": "zh_male_guanggaojieshuo_uranus_bigtts", "language": "zh", "gender": "male", "scene": "通用场景"},
        {"name": "少儿故事 2.0", "voice_type": "zh_female_shaoergushi_uranus_bigtts", "language": "zh", "gender": "female", "scene": "有声阅读"},
    ]


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="volcengine-tts",
        description="Volcengine Doubao TTS (seed-tts-2.0) — text to speech",
    )

    # Mode: single text or batch
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to synthesize (single mode)",
    )
    parser.add_argument(
        "--batch", "-b",
        help="Batch mode: JSON array of {\"text\": \"...\", \"speaker\": \"...\", ...}",
    )

    # Output
    parser.add_argument(
        "--output-dir", "-o",
        default="./tts-output/",
        help="Output directory (default: ./tts-output/)",
    )
    parser.add_argument(
        "--speaker", "-s",
        default=DEFAULT_SPEAKER,
        help=f"Speaker/voice ID (default: {DEFAULT_SPEAKER})",
    )

    # Audio params
    parser.add_argument("--format", default=DEFAULT_FORMAT, choices=["mp3", "pcm", "ogg_opus", "wav"])
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--speech-rate", type=int, default=0, help="Speed [-50, 100], 100=2x")
    parser.add_argument("--volume", type=int, default=0, help="Volume [-50, 100], 100=2x")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch [-12, 12] semitones")
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model variant to pass to the API. Omit by default (server picks). "
            "Mainly useful for cloned (ICL) voices, e.g. 'seed-tts-2.0-standard'. "
            "Official seed-tts-2.0 voices support --context without setting this."
        ),
    )
    parser.add_argument("--ssml", action="store_true", help="Parse text as SSML")
    parser.add_argument("--context", help="Voice instruction, e.g. '用温柔的语气说话'")
    parser.add_argument("--language", help="Explicit language: zh-cn, en, ja, es-mx, id, pt-br, ko")
    parser.add_argument("--silence-duration", type=int, default=0, help="Trailing silence ms [0, 30000]")
    parser.add_argument("--watermark", action="store_true", help="Add AIGC audio watermark")
    parser.add_argument("--no-subtitle", dest="subtitle", action="store_false", help="Disable word-level timestamps (saves ~600ms tail latency for latency-sensitive / realtime use cases)")
    parser.add_argument("--strip-markdown", action="store_true", help="Remove markdown syntax before TTS")
    parser.add_argument("--strip-emoji", action="store_true", help="Remove emoji characters before TTS")
    parser.add_argument("--latex", action="store_true", help="Enable LaTeX formula reading; auto-enables markdown filtering")
    parser.add_argument("--latex-parser", choices=["v2"], help="Stronger LaTeX parser for math/education narration; auto-enables --latex and --strip-markdown")

    # Batch
    parser.add_argument("--concurrency", "-c", type=int, default=DEFAULT_CONCURRENCY, help=f"Max parallel requests (default: {DEFAULT_CONCURRENCY})")

    # Info
    parser.add_argument("--list-speakers", action="store_true", help="List available speakers and exit")

    args = parser.parse_args()

    # --list-speakers mode
    if args.list_speakers:
        api_key = load_api_key()
        speakers = list_speakers(api_key)
        print(json.dumps(speakers, ensure_ascii=False, indent=2))
        return

    # Validate mode
    if args.batch:
        try:
            items = json.loads(args.batch)
        except json.JSONDecodeError as e:
            die(f"Invalid --batch JSON: {e}")
        if not isinstance(items, list) or len(items) == 0:
            die("--batch must be a non-empty JSON array")
    elif args.text:
        items = [{"text": args.text}]
    else:
        die("Either provide text as positional argument or use --batch '[...]'")

    api_key = load_api_key()
    output_dir = Path(args.output_dir)

    base_kwargs: dict[str, Any] = {
        "speaker": args.speaker,
        "fmt": args.format,
        "sample_rate": args.sample_rate,
        "speech_rate": args.speech_rate,
        "loudness_rate": args.volume,
        "pitch": args.pitch,
        "model": args.model,
        "ssml": args.ssml,
        "context_texts": [args.context] if args.context else None,
        "language": args.language,
        "silence_duration": args.silence_duration,
        "watermark": args.watermark,
        "enable_subtitle": args.subtitle,
        "disable_markdown_filter": args.strip_markdown,
        "disable_emoji_filter": args.strip_emoji,
        "enable_latex": args.latex,
        "latex_parser": args.latex_parser,
    }

    if args.batch:
        result = synthesize_batch(
            items,
            output_dir,
            api_key=api_key,
            concurrency=args.concurrency,
            base_kwargs=base_kwargs,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Single mode: items has exactly one entry
        item = items[0]
        kwargs = {**base_kwargs}
        kwargs["speaker"] = item.get("speaker", base_kwargs["speaker"])
        result = synthesize_one(item["text"], output_dir, api_key=api_key, **kwargs)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if result.get("error"):
            sys.exit(1)


if __name__ == "__main__":
    main()
