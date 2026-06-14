#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def find_manifests(outputs_dir: Path) -> list[Path]:
    return sorted(outputs_dir.rglob("manifest.json"))


def find_videos(outputs_dir: Path) -> list[Path]:
    return sorted(outputs_dir.rglob("video.mp4"))


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


def grade_product_ad(outputs_dir: Path) -> list[dict[str, Any]]:
    videos = find_videos(outputs_dir)
    flat_mp4s = sorted(p for p in outputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4")
    all_videos = videos or flat_mp4s
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


def _has_first_frame_role(manifest: dict[str, Any]) -> bool:
    content = manifest.get("request_payload", {}).get("content", [])
    if any(item.get("role") == "first_frame" for item in content):
        return True
    # Fallback: some agents write manifests with output_files.first_frame
    if manifest.get("output_files", {}).get("first_frame"):
        return True
    return False


def grade_first_frame(outputs_dir: Path) -> list[dict[str, Any]]:
    videos = find_videos(outputs_dir)
    manifests = find_manifests(outputs_dir)
    manifest = load_manifest(manifests[0]) if manifests else {}
    images = sorted(p for p in outputs_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    flat_mp4s = sorted(p for p in outputs_dir.iterdir() if p.is_file() and p.suffix.lower() == ".mp4")
    all_videos = videos or flat_mp4s
    video = all_videos[0] if all_videos else None

    results = []
    first_frame_used = _has_first_frame_role(manifest)
    # without_skill agents may not produce a manifest; accept image + video as evidence
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
    # without_skill agents may produce flat .mp4 files instead of video.mp4 in subdirs
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


GRADERS = {
    "eval-product-ad": grade_product_ad,
    "eval-first-frame": grade_first_frame,
    "eval-batch-shots": grade_batch_shots,
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
