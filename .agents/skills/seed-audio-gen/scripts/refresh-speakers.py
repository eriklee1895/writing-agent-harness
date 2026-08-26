#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "volcenginesdkcore>=1.0",
#   "volcenginesdkspeechsaasprod>=1.0",
#   "python-dotenv>=1.0",
# ]
# ///
"""refresh-speakers.py — 从 ListSpeakers API 拉全量音色并更新 speakers.json + speakers.md。

低频手动运行，需 VOLC_ACCESSKEY / VOLC_SECRETKEY（AK/SK 鉴权，非合成接口的 VOLC_SPEECH_API_KEY）。
volcenginesdkcore / volcenginesdkspeechsaasprod 为内部 SDK 包，需预先从内部 registry 安装。

用法:
    python3 scripts/refresh-speakers.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
SPEAKERS_JSON = REFERENCES_DIR / "speakers.json"
SPEAKERS_MD = REFERENCES_DIR / "speakers.md"


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_credentials() -> tuple[str, str]:
    """三級 fallback: env → .env → ~/.volcengine.env"""
    ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
    sk = os.environ.get("VOLC_SECRETKEY", "").strip()
    if ak and sk:
        return ak, sk

    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env)
        ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
        sk = os.environ.get("VOLC_SECRETKEY", "").strip()
        if ak and sk:
            return ak, sk

    user_env = Path.home() / ".volcengine.env"
    if user_env.exists():
        load_dotenv(user_env)
        ak = os.environ.get("VOLC_ACCESSKEY", "").strip()
        sk = os.environ.get("VOLC_SECRETKEY", "").strip()
        if ak and sk:
            return ak, sk

    die(
        "VOLC_ACCESSKEY / VOLC_SECRETKEY not found. "
        "Set via env, .env, or ~/.volcengine.env"
    )


def fetch_all_speakers(ak: str, sk: str) -> list[dict[str, Any]]:
    """分页调 ListSpeakers API 拉全量音色列表。"""
    from volcenginesdkcore import Configuration
    from volcenginesdkspeechsaasprod import (
        SPEECHSAASPRODApi,
        ListSpeakersRequest,
    )

    Configuration.set_default(
        Configuration(ak=ak, sk=sk, region="cn-beijing")
    )
    api = SPEECHSAASPRODApi()

    all_speakers: list[dict[str, Any]] = []
    page = 1
    while True:
        try:
            resp = api.list_speakers(ListSpeakersRequest(page=page))
        except Exception as e:
            die(f"ListSpeakers API call failed on page {page}: {e}")

        result = resp.get("Result") if isinstance(resp, dict) else {}
        if not result:
            # Try attribute access (SDK may return object)
            result = getattr(resp, "Result", None) if hasattr(resp, "Result") else None
            if result is None:
                die(f"Unexpected response shape on page {page}: {type(resp)}")

        if isinstance(result, dict):
            speakers = result.get("Speakers", [])
            total = result.get("Total", 0)
        else:
            speakers = getattr(result, "Speakers", [])
            total = getattr(result, "Total", 0)

        if not speakers:
            break

        # Normalize each speaker to dict
        for s in speakers:
            if isinstance(s, dict):
                all_speakers.append(s)
            else:
                all_speakers.append(_obj_to_dict(s))

        print(f"  Page {page}: fetched {len(speakers)} speakers (total {total}, accumulated {len(all_speakers)})")
        if len(all_speakers) >= total:
            break
        page += 1

    return all_speakers


def _obj_to_dict(obj: Any) -> dict[str, Any]:
    """Convert SDK object to plain dict."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    result: dict[str, Any] = {}
    for key in dir(obj):
        if key.startswith("_"):
            continue
        val = getattr(obj, key)
        if callable(val):
            continue
        result[key] = _obj_to_dict(val) if not isinstance(val, (str, int, float, bool, list, dict, type(None))) else val
    return result


def _first_category(speaker: dict[str, Any]) -> str:
    """Extract first scene category from raw speaker entry."""
    categories = speaker.get("Categories", [])
    if isinstance(categories, list) and categories:
        first = categories[0]
        if isinstance(first, dict):
            sub = first.get("Categories", [])
            if isinstance(sub, list) and sub:
                return str(sub[0])
    return "其他"


def _language_codes(speaker: dict[str, Any]) -> list[str]:
    """Extract language codes from raw speaker Languages list."""
    langs = speaker.get("Languages", [])
    if not isinstance(langs, list):
        return []
    codes: list[str] = []
    for lang in langs:
        if isinstance(lang, dict):
            code = lang.get("Language", "")
            if code:
                codes.append(code)
    return codes


def _voice_type(speaker: dict[str, Any]) -> str:
    """Determine voice type: 'icl' for ICL/tob voices, 'bigtts' otherwise."""
    vt = speaker.get("VoiceType", "")
    if "ICL_" in vt or "_tob" in vt:
        return "icl"
    return "bigtts"


def process_speakers(raw_speakers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert raw ListSpeakers entries to speakers.json structure."""
    processed: list[dict[str, Any]] = []
    for s in raw_speakers:
        entry = {
            "voice_type": s.get("VoiceType", ""),
            "name": s.get("Name", ""),
            "type": _voice_type(s),
            "gender": s.get("Gender", ""),
            "age": s.get("Age", ""),
            "scene": _first_category(s),
            "description": s.get("Description", ""),
            "languages": _language_codes(s),
            "trial_url": s.get("TrialURL", "") or s.get("ShortTrialURL", ""),
            "heat": s.get("Heat", 0),
            "status": s.get("Status", "online"),
            "emoji": s.get("Emoji", ""),
        }
        processed.append(entry)
    return processed


def write_speakers_json(speakers: list[dict[str, Any]], path: Path) -> None:
    """Write speakers.json with 2-space indent, utf-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(speakers, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _scene_sort_key(scene: str) -> tuple[int, str]:
    """Stable scene ordering: 客服 first, then 教学, 通用 last, alphabetical in between."""
    if scene == "客服场景":
        return (0, scene)
    if scene == "教学场景":
        return (1, scene)
    if scene == "通用场景":
        return (99, scene)
    return (2, scene)


def build_speakers_md(speakers: list[dict[str, Any]]) -> str:
    """Build speakers.md markdown content grouped by scene."""
    bigtts_count = sum(1 for s in speakers if s["type"] == "bigtts")
    icl_count = sum(1 for s in speakers if s["type"] == "icl")
    total = len(speakers)

    lines: list[str] = [
        "# seed-audio-1.0 音色速查表",
        "",
        f"> 共 {total} 个音色（{bigtts_count} bigtts + {icl_count} ICL），截至 2026-08-26。",
        "",
        "用 `uv run scripts/seed-audio-gen.py --list-speakers` 查询完整结构化数据。",
        "",
    ]

    # Group by scene
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for s in speakers:
        scene = s.get("scene", "其他")
        by_scene.setdefault(scene, []).append(s)

    # Sort scenes
    sorted_scenes = sorted(by_scene.keys(), key=_scene_sort_key)

    for scene in sorted_scenes:
        items = sorted(by_scene[scene], key=lambda s: -s.get("heat", 0))
        lines.append(f"## {scene}")
        lines.append("")
        lines.append("| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |")
        lines.append("|---|---|---|---|---|---|")
        for item in items:
            emoji = item.get("emoji", "")
            name = f"{emoji} {item['name']}" if emoji else item["name"]
            vt = f"`{item['voice_type']}`"
            gender = item.get("gender", "")
            desc = item.get("description", "")
            trial = item.get("trial_url", "")
            trial_link = f"[试听]({trial})" if trial else ""
            heat = item.get("heat", 0)
            lines.append(f"| {name} | {vt} | {gender} | {desc} | {trial_link} | {heat} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    ak, sk = load_credentials()
    print("Fetching all speakers from ListSpeakers API...")
    raw = fetch_all_speakers(ak, sk)
    print(f"Total raw speakers: {len(raw)}")

    processed = process_speakers(raw)
    print(f"Processed: {len(processed)} speakers")

    # Write speakers.json
    write_speakers_json(processed, SPEAKERS_JSON)
    print(f"Wrote {SPEAKERS_JSON}")

    # Write speakers.md
    md_content = build_speakers_md(processed)
    SPEAKERS_MD.write_text(md_content, encoding="utf-8")
    print(f"Wrote {SPEAKERS_MD}")

    print(f"\nDone. {len(processed)} speakers written to speakers.json + speakers.md")


if __name__ == "__main__":
    main()