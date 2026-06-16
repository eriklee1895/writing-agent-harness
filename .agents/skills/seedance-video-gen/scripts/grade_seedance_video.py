#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def find_videos(outputs_dir: Path) -> list[Path]:
    return sorted(outputs_dir.rglob("video.mp4"))


def find_any_mp4(outputs_dir: Path) -> list[Path]:
    flat = sorted(p for p in outputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4")
    if flat:
        return flat
    return find_videos(outputs_dir)


def find_manifests(outputs_dir: Path) -> list[Path]:
    return sorted(outputs_dir.rglob("manifest.json"))


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": str(exc)}


def _load_metadata_json(outputs_dir: Path) -> dict[str, Any]:
    for name in ("manifest.json", "task_metadata.json", "seedance-final-response.json"):
        path = outputs_dir / name
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return {}


def _has_first_frame_role(manifest: dict[str, Any]) -> bool:
    content = manifest.get("request_payload", {}).get("content", [])
    if any(item.get("role") == "first_frame" for item in content):
        return True
    if manifest.get("output_files", {}).get("first_frame"):
        return True
    return False


def _has_audio_enabled(manifest: dict[str, Any]) -> bool:
    """Check if generate_audio was true in request."""
    if manifest.get("request_payload", {}).get("generate_audio") is True:
        return True
    return False


def _prompt_has_audio_content(prompt_path: Path) -> bool:
    """Check if prompt.md mentions audio/music/sound effects."""
    if not prompt_path.is_file():
        return False
    text = prompt_path.read_text(encoding="utf-8").lower()
    keywords = ["background music", "sound effect", "音频", "音效", "音乐", "bgm",
                "（）", "()", "<>", "{}"]
    return any(kw in text for kw in keywords)


# ---- Graders for existing evals (1-3) ----

def grade_product_ad(outputs_dir: Path) -> list[dict[str, Any]]:
    all_videos = find_any_mp4(outputs_dir)
    prompt_path = outputs_dir / "prompt.md"
    manifest = _load_metadata_json(outputs_dir)

    results = []
    video = all_videos[0] if all_videos else None
    results.append({
        "text": "视频文件 video.mp4 存在且非空",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video} ({video.stat().st_size} bytes)" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 包含正确的 task_id、model、ratio=9:16、duration=5",
        "passed": (
            bool(manifest.get("task_id") or manifest.get("id"))
            and manifest.get("model") in {"doubao-seedance-2-0-260128", "doubao-seedance-2-0-fast-260128"}
            and manifest.get("ratio") == "9:16"
            and manifest.get("duration") == 5
        ),
        "evidence": json.dumps({
            "task_id": manifest.get("task_id") or manifest.get("id"),
            "model": manifest.get("model"),
            "ratio": manifest.get("ratio"),
            "duration": manifest.get("duration"),
        }, ensure_ascii=False),
    })
    results.append({
        "text": "prompt.md 存在",
        "passed": prompt_path.is_file() and prompt_path.stat().st_size > 0,
        "evidence": f"Found {prompt_path}" if prompt_path.is_file() else "No prompt.md found",
    })
    return results


def grade_first_frame(outputs_dir: Path) -> list[dict[str, Any]]:
    videos = find_videos(outputs_dir)
    flat_mp4s = sorted(p for p in outputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4")
    all_videos = videos or flat_mp4s
    manifests = find_manifests(outputs_dir)
    manifest = load_manifest(manifests[0]) if manifests else _load_metadata_json(outputs_dir)
    images = sorted(p for p in outputs_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    video = all_videos[0] if all_videos else None

    results = []
    first_frame_used = _has_first_frame_role(manifest)
    results.append({
        "text": "首帧图存在且被脚本成功引用",
        "passed": bool(images) and (first_frame_used or video is not None),
        "evidence": f"Images: {[str(i) for i in images[:3]]}; first_frame used: {first_frame_used}; video: {video}",
    })
    results.append({
        "text": "生成的 video.mp4 存在",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video}" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 中包含 first_frame 相关记录",
        "passed": first_frame_used,
        "evidence": json.dumps(manifest.get("output_files") or manifest.get("request_payload", {}).get("content", [])[:3], ensure_ascii=False),
    })
    return results


def grade_batch_shots(outputs_dir: Path) -> list[dict[str, Any]]:
    videos = find_videos(outputs_dir)
    manifests = find_manifests(outputs_dir)
    flat_mp4s = sorted(p for p in outputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4")
    all_videos = videos or flat_mp4s

    all_correct = True
    details = []
    for m in manifests:
        data = load_manifest(m)
        req = data.get("request_payload", {})
        ok = (
            data.get("ratio") == "16:9"
            and data.get("duration") == 4
            and req.get("generate_audio") is False
            and req.get("watermark") is False
        )
        if not ok:
            all_correct = False
        details.append({
            "path": str(m),
            "ratio": data.get("ratio"),
            "duration": data.get("duration"),
            "generate_audio": req.get("generate_audio"),
            "watermark": req.get("watermark"),
        })

    results = []
    results.append({
        "text": "生成 3 个独立视频文件",
        "passed": len(all_videos) == 3 and all(v.stat().st_size > 0 for v in all_videos),
        "evidence": f"Found {len(all_videos)} videos: {[str(v) for v in all_videos]}",
    })
    results.append({
        "text": "每个 manifest.json 的 ratio=16:9、duration=4、generate_audio=false、watermark=false",
        "passed": all_correct and len(manifests) == 3,
        "evidence": json.dumps(details, ensure_ascii=False) if details else "No manifests found",
    })
    results.append({
        "text": "生成 3 个带正确参数的 manifest.json",
        "passed": len(manifests) == 3,
        "evidence": f"Found {len(manifests)} manifests",
    })
    return results


# ---- Graders for new evals (4-8) ----


def _generic_basic_check(outputs_dir: Path, expect_audio: bool = False, expect_ratio: str | None = None, expect_duration: int | None = None) -> tuple[dict, list, list, Path]:
    """Return (manifest, all_videos, all_manifests, prompt_path)."""
    manifest = _load_metadata_json(outputs_dir)
    all_videos = find_any_mp4(outputs_dir)
    all_manifests = find_manifests(outputs_dir)
    prompt_path = outputs_dir / "prompt.md" if not all_manifests else all_manifests[0].parent / "prompt.md"
    return manifest, all_videos, all_manifests, prompt_path


def grade_education_animation(outputs_dir: Path) -> list[dict[str, Any]]:
    manifest, all_videos, all_manifests, prompt_path = _generic_basic_check(outputs_dir)
    video = all_videos[0] if all_videos else None
    results = []
    results.append({
        "text": "视频文件 video.mp4 存在且非空",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video} ({video.stat().st_size} bytes)" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 的 generate_audio=true",
        "passed": _has_audio_enabled(manifest) or manifest.get("generate_audio") is True,
        "evidence": f"generate_audio in manifest: {manifest.get('generate_audio') or manifest.get('request_payload', {}).get('generate_audio')}",
    })
    results.append({
        "text": "prompt.md 包含音频提示词（背景音乐或音效符号）",
        "passed": _prompt_has_audio_content(prompt_path),
        "evidence": f"Prompt at {prompt_path}" if prompt_path.is_file() else "No prompt.md found",
    })
    return results


def grade_drama_dialogue(outputs_dir: Path) -> list[dict[str, Any]]:
    manifest, all_videos, all_manifests, prompt_path = _generic_basic_check(outputs_dir)
    video = all_videos[0] if all_videos else None
    results = []
    results.append({
        "text": "视频文件 video.mp4 存在",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video}" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 的 generate_audio=true",
        "passed": _has_audio_enabled(manifest) or manifest.get("generate_audio") is True,
        "evidence": f"generate_audio: {manifest.get('generate_audio') or manifest.get('request_payload', {}).get('generate_audio')}",
    })
    results.append({
        "text": "prompt.md 中包含 {} 格式的台词或对白",
        "passed": _prompt_has_audio_content(prompt_path),
        "evidence": f"Prompt at {prompt_path}" if prompt_path.is_file() else "No prompt.md found",
    })
    return results


def grade_first_last_frame(outputs_dir: Path) -> list[dict[str, Any]]:
    manifest, all_videos, all_manifests, prompt_path = _generic_basic_check(outputs_dir)
    video = all_videos[0] if all_videos else None
    content = manifest.get("request_payload", {}).get("content", [])
    has_first = any(item.get("role") == "first_frame" for item in content)
    has_last = any(item.get("role") == "last_frame" for item in content)
    results = []
    results.append({
        "text": "视频文件 video.mp4 存在",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video}" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 中使用首尾帧模式（content 中有 first_frame 和 last_frame role）",
        "passed": has_first and has_last,
        "evidence": json.dumps({"has_first_frame": has_first, "has_last_frame": has_last}),
    })
    results.append({
        "text": "manifest.json 的 duration=5、generate_audio=false",
        "passed": (
            manifest.get("duration") in (5, None)
            and manifest.get("request_payload", {}).get("generate_audio") is False
        ),
        "evidence": f"duration={manifest.get('duration')}, generate_audio={manifest.get('request_payload', {}).get('generate_audio')}",
    })
    return results


def grade_multimodal_ref(outputs_dir: Path) -> list[dict[str, Any]]:
    manifest, all_videos, all_manifests, prompt_path = _generic_basic_check(outputs_dir)
    video = all_videos[0] if all_videos else None
    content = manifest.get("request_payload", {}).get("content", [])
    has_ref_image = any(item.get("role") == "reference_image" for item in content)
    has_ref_audio = any(item.get("role") == "reference_audio" for item in content)
    results = []
    results.append({
        "text": "视频文件 video.mp4 存在",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video}" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 的 content 中包含 reference_image 和 reference_audio role",
        "passed": has_ref_image and has_ref_audio,
        "evidence": json.dumps({"has_reference_image": has_ref_image, "has_reference_audio": has_ref_audio}),
    })
    results.append({
        "text": "manifest.json 的 duration=8、generate_audio=true",
        "passed": (
            manifest.get("duration") in (8, None)
            and (_has_audio_enabled(manifest) or manifest.get("generate_audio") is True)
        ),
        "evidence": f"duration={manifest.get('duration')}, generate_audio={_has_audio_enabled(manifest)}",
    })
    return results


def grade_social_vertical(outputs_dir: Path) -> list[dict[str, Any]]:
    manifest, all_videos, all_manifests, prompt_path = _generic_basic_check(outputs_dir)
    video = all_videos[0] if all_videos else None
    results = []
    results.append({
        "text": "视频文件 video.mp4 存在且非空",
        "passed": video is not None and video.stat().st_size > 0,
        "evidence": f"Found {video} ({video.stat().st_size} bytes)" if video else "No video file found",
    })
    results.append({
        "text": "manifest.json 的 ratio=9:16、generate_audio=true",
        "passed": (
            manifest.get("ratio") == "9:16"
            and (_has_audio_enabled(manifest) or manifest.get("generate_audio") is True)
        ),
        "evidence": f"ratio={manifest.get('ratio')}, generate_audio={_has_audio_enabled(manifest)}",
    })
    results.append({
        "text": "prompt.md 中包含字幕描述",
        "passed": _prompt_has_audio_content(prompt_path),
        "evidence": f"Prompt at {prompt_path}" if prompt_path.is_file() else "No prompt.md found",
    })
    return results


GRADERS = {
    "eval-product-ad": grade_product_ad,
    "eval-first-frame": grade_first_frame,
    "eval-batch-shots": grade_batch_shots,
    "eval-education-animation": grade_education_animation,
    "eval-drama-dialogue": grade_drama_dialogue,
    "eval-first-last-frame": grade_first_last_frame,
    "eval-multimodal-ref": grade_multimodal_ref,
    "eval-social-vertical": grade_social_vertical,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade seedance-video-gen benchmark outputs.")
    parser.add_argument("--eval-name", required=True, choices=sorted(GRADERS))
    parser.add_argument("--outputs-dir", required=True)
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir).expanduser().resolve()
    expectations = GRADERS[args.eval_name](outputs_dir)
    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    grading = {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": passed / total if total else 0.0,
        },
    }
    out_path = outputs_dir.parent / "grading.json"
    out_path.write_text(json.dumps(grading, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(json.dumps(grading, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
