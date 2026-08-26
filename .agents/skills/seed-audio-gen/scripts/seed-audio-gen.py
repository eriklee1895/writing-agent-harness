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