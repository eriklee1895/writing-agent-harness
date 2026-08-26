# seed-audio-gen skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个独立的 `seed-audio-gen` project skill，封装火山引擎 seed-audio-1.0 生成式音频 API，支持单句/batch 合成、音色克隆、音色表本地查询、成本预估。

**Architecture:** 单 CLI 脚本（PEP 723）+ 本地音色表 reference + prompt-guide。CLI 调 `openspeech.bytedance.com/api/v3/tts/create`（非流式 HTTP，`X-Api-Key` 鉴权）。和 `volcengine-tts` skill 完全解耦，不互指。靠 SKILL.md 的 "When NOT to use" 单向提示更优选择。

**Tech Stack:** Python 3.12+、PEP 723 inline deps（httpx、mutagen）、uv run、argparse、JSON stdout。

**Spec:** [docs/superpowers/specs/2026-08-26-seed-audio-gen-design.md](../specs/2026-08-26-seed-audio-gen-design.md)

## Global Constraints

- Python 脚本走 PEP 723 inline metadata，shebang `#!/usr/bin/env -S uv run`，`requires-python = ">=3.12"`，调用 `uv run scripts/xxx.py`（见 [docs/skills/skills-guide.md](../../skills/skills-guide.md)）
- 测试文件 `test_*.py` 不走 PEP 723，用项目 `pyproject.toml` dev dependency
- SKILL.md 引用脚本/文档必须用相对 SKILL.md 的路径
- 鉴权只读 `VOLC_SPEECH_API_KEY`（三级 fallback：env → `.env` → `~/.volcengine.env`），不引入 AK/SK
- API 端点固定 `https://openspeech.bytedance.com/api/v3/tts/create`，body 用 `{model, text_prompt, references, audio_config, watermark}`（wiki 方舟命名 `doubao-seed-audio-1-0`/`text`/`audio_setting` 在此端点不可用，实测确认）
- stdout 输出 JSON，错误输出 stderr（exit code 1）
- 不暴露 `--context`/`--latex`/`--ssml`（这些是 seed-tts-2.0 能力，seed-audio 用 text_prompt 自然语言表达）
- skill 路径：`.agents/skills/seed-audio-gen/`（`.claude/skills/` 是软链接指向 `.agents/skills/`）
- 音色表数据源：`~/Downloads/seed-tts-2.0-音色列表.json`（ListSpeakers API 返回，444 条）

---

## File Structure

```
.agents/skills/seed-audio-gen/
  SKILL.md                          # 触发描述 + 能力边界 + When NOT to use
  scripts/
    seed-audio-gen.py               # 主 CLI（PEP 723，单句 + batch + list-speakers）
    refresh-speakers.py             # 音色表更新脚本（PEP 723，用 AK/SK 调 ListSpeakers）
    test_seed_audio_gen.py          # pytest 测试（不走 PEP 723，用项目 pyproject.toml）
  references/
    seedaudio-prompt-guide.md       # 场景语法、时间戳、@音频N、音色选择
    speakers.json                   # 444 条完整音色数据
    speakers.md                     # 人类可读音色速查表
```

---

### Task 1: 音色表数据生成（speakers.json + speakers.md）

这是 reference 数据，先于脚本产出，因为 `--list-speakers` 依赖它。从用户提供的 ListSpeakers JSON 加工成本地 reference。

**Files:**
- Create: `.agents/skills/seed-audio-gen/references/speakers.json`
- Create: `.agents/skills/seed-audio-gen/references/speakers.md`

**Interfaces:**
- Consumes: `~/Downloads/seed-tts-2.0-音色列表.json`（ListSpeakers API 返回，444 条，结构 `{Result: {Speakers: [...], Total}}`）
- Produces: `speakers.json`（数组，每条含 `type` 字段区分 `bigtts`/`icl`）、`speakers.md`（按场景分组速查表）

- [ ] **Step 1: 写数据加工脚本**（一次性，不入 skill）

```python
# /tmp/build_speakers.py — 一次性加工，产出 speakers.json + speakers.md
import json, re
from pathlib import Path
from collections import defaultdict

src = Path.home() / "Downloads/seed-tts-2.0-音色列表.json"
d = json.loads(src.read_text())
speakers = d["Result"]["Speakers"]

out = []
for s in speakers:
    vt = s.get("VoiceType", "")
    kind = "icl" if "_tob" in vt else "bigtts"
    cats = s.get("Categories", [])
    scene = cats[0]["Categories"][0] if cats and cats[0].get("Categories") else "其他"
    out.append({
        "voice_type": vt,
        "name": s.get("Name", ""),
        "type": kind,
        "gender": s.get("Gender", ""),
        "age": s.get("Age", ""),
        "scene": scene,
        "description": s.get("Description", ""),
        "languages": [l.get("Language","") for l in s.get("Languages", [])],
        "trial_url": s.get("TrialURL", ""),
        "heat": s.get("Heat", 0),
        "status": s.get("Status", ""),
        "emoji": s.get("Emoji", ""),
    })

# speakers.json
json_out = Path(".agents/skills/seed-audio-gen/references/speakers.json")
json_out.parent.mkdir(parents=True, exist_ok=True)
json_out.write_text(json.dumps(out, ensure_ascii=False, indent=2))

# speakers.md — 按场景分组，突出 description + trial_url + heat
by_scene = defaultdict(list)
for s in out:
    if s["status"] == "online":
        by_scene[s["scene"]].append(s)

lines = ["# seed-audio-1.0 音色速查表", "",
         f"> 共 {len(out)} 个音色（{sum(1 for x in out if x['type']=='bigtts')} bigtts + {sum(1 for x in out if x['type']=='icl')} ICL），截至 2026-08-26。", "",
         "用 `uv run scripts/seed-audio-gen.py --list-speakers` 查询完整结构化数据。", ""]
for scene in sorted(by_scene.keys()):
    lines.append(f"## {scene}")
    lines.append("")
    lines.append("| 名称 | voice_type | 性别 | 描述 | 试听 | 热度 |")
    lines.append("|---|---|---|---|---|---|")
    for s in sorted(by_scene[scene], key=lambda x: -x["heat"])[:15]:
        trial = f"[试听]({s['trial_url']})" if s["trial_url"] else ""
        lines.append(f"| {s['emoji']} {s['name']} | `{s['voice_type']}` | {s['gender']} | {s['description'][:40]} | {trial} | {s['heat']} |")
    lines.append("")
Path(".agents/skills/seed-audio-gen/references/speakers.md").write_text("\n".join(lines))
print(f"speakers.json: {len(out)} 条; speakers.md: {len(by_scene)} 场景")
```

- [ ] **Step 2: 运行加工脚本**

Run: `cd /Users/eriklee/code/my_project/writing-agent-harness && python3 /tmp/build_speakers.py`
Expected: 输出 `speakers.json: 444 条; speakers.md: N 场景`

- [ ] **Step 3: 验证 JSON 结构**

Run: `python3 -c "import json; d=json.load(open('.agents/skills/seed-audio-gen/references/speakers.json')); print(len(d), d[0]['voice_type'], d[0]['type'])"`
Expected: `444 zh_female_vv_uranus_bigtts bigtts`

- [ ] **Step 4: 验证 md 可读**

Run: `head -20 .agents/skills/seed-audio-gen/references/speakers.md`
Expected: 标题 + 场景分组表格

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/seed-audio-gen/references/speakers.json .agents/skills/seed-audio-gen/references/speakers.md
git commit -m "feat(seed-audio-gen): 444 条音色表 reference（bigtts+icl）"
```

---

### Task 2: 主 CLI 脚本骨架 + API 调用 + 单句模式

实现 `seed-audio-gen.py` 的核心：env 加载、API 调用、单句模式、meta sidecar。先不碰 batch / list-speakers / 参考音频。

**Files:**
- Create: `.agents/skills/seed-audio-gen/scripts/seed-audio-gen.py`
- Test: `.agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py`

**Interfaces:**
- Consumes: `speakers.json`（Task 1 产出，list-speakers 用，本任务暂不读）
- Produces: `synthesize(prompt, **opts) -> dict`（核心函数，单句/batch 共用）；CLI 单句模式输出 JSON 到 stdout

- [ ] **Step 1: 写 prompt 超长校验的失败测试**

```python
# .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import seed_audio_gen as mod

def test_prompt_too_long_raises():
    """text_prompt > 3000 字符时报错，带可执行 hint"""
    long_prompt = "啊" * 3001
    with pytest.raises(mod.PromptTooLongError) as exc_info:
        mod.validate_prompt_length(long_prompt)
    msg = str(exc_info.value)
    assert "3000" in msg
    assert "split your prompt" in msg
    assert "120s" in msg

def test_prompt_at_limit_ok():
    """正好 3000 字符不报错"""
    mod.validate_prompt_length("啊" * 3000)  # 不抛异常即通过
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /Users/eriklee/code/my_project/writing-agent-harness && uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'seed_audio_gen'`

- [ ] **Step 3: 写脚本骨架 + validate_prompt_length**

```python
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: PASS（2 个测试）

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
git commit -m "feat(seed-audio-gen): CLI 骨架 + prompt 超长校验"
```

---

### Task 3: synthesize 核心函数 + 单句模式 + meta sidecar

实现 API 调用、audio_file 保存、meta sidecar（含 CDN URL 时效）、stdout JSON 输出。

**Files:**
- Modify: `.agents/skills/seed-audio-gen/scripts/seed-audio-gen.py`
- Test: `.agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py`

**Interfaces:**
- Produces: `synthesize(prompt, *, api_key, references, audio_config, watermark, output_dir) -> dict`；返回 `{audio_file, duration, original_duration, url, fetched_at, url_expires_at, subtitle, log_id, model, text_prompt, estimated_cost_yuan, error}`

- [ ] **Step 1: 写 build_body 失败测试**

```python
# 追加到 test_seed_audio_gen.py
def test_build_body_minimal():
    """最小 body 结构正确"""
    body = mod.build_body("一位女声朗读：你好", references=None, audio_config=None, watermark=None, model="seed-audio-1.0")
    assert body["model"] == "seed-audio-1.0"
    assert body["text_prompt"] == "一位女声朗读：你好"
    assert "references" not in body or body["references"] is None

def test_build_body_with_speaker():
    """speaker 进 references 列表"""
    body = mod.build_body("test", references=[{"speaker": "zh_female_vv_uranus_bigtts"}], audio_config={"format":"mp3"}, watermark=None, model="seed-audio-1.0")
    assert body["references"] == [{"speaker": "zh_female_vv_uranus_bigtts"}]
    assert body["audio_config"]["format"] == "mp3"

def test_build_body_watermark():
    """watermark flag 展开为 object"""
    body = mod.build_body("test", references=None, audio_config=None, watermark={"aigc": True, "meta": False}, model="seed-audio-1.0")
    assert body["watermark"]["aigc_watermark"] is True
    assert body["watermark"]["aigc_metadata"]["enable"] is False
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: 3 个新测试 FAIL（`build_body` 未定义）

- [ ] **Step 3: 实现 build_body + synthesize + 单句模式 main**

在 `seed-audio-gen.py` 追加：

```python
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
        if watermark.get("meta"):
            w["aigc_metadata"] = {"enable": True}
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: PASS（5 个测试）

- [ ] **Step 5: 写单句模式 main + argparse 骨架**

在 `seed-audio-gen.py` 追加：

```python
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


def _list_speakers(args):
    # Task 4 实现
    die("--list-speakers not implemented yet", code=2)


def _run_batch(args):
    # Task 5 实现
    die("--batch not implemented yet", code=2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 实测单句模式（真实 API 调用）**

Run:
```bash
uv run .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py "一位女声朗读：你好世界" --speaker zh_female_vv_uranus_bigtts
```
Expected: JSON 输出含 `audio_file`、`original_duration`、`url`、`url_expires_at`、`estimated_cost_yuan`，且 `.meta.json` sidecar 生成

- [ ] **Step 7: Commit**

```bash
git add .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
git commit -m "feat(seed-audio-gen): synthesize 核心 + 单句模式 + meta sidecar"
```

---

### Task 4: --list-speakers 本地查询

实现 `--list-speakers`：读 `speakers.json`，支持 `--filter scene=X`、`--filter lang=Y`、`--sort heat`。

**Files:**
- Modify: `.agents/skills/seed-audio-gen/scripts/seed-audio-gen.py`（`_list_speakers` 函数）
- Modify: `.agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py`

**Interfaces:**
- Consumes: `references/speakers.json`（Task 1 产出）
- Produces: `_list_speakers(args)` 实现；`query_speakers(filters, sort_by)` 可测函数

- [ ] **Step 1: 写 query_speakers 失败测试**

```python
# 追加到 test_seed_audio_gen.py
def test_query_speakers_filter_scene():
    speakers = [
        {"voice_type":"a","name":"A","type":"bigtts","scene":"视频配音","heat":50},
        {"voice_type":"b","name":"B","type":"bigtts","scene":"通用场景","heat":100},
        {"voice_type":"c","name":"C","type":"icl","scene":"视频配音","heat":80},
    ]
    result = mod.query_speakers(speakers, filters={"scene":"视频配音"}, sort_by="heat")
    assert len(result) == 2
    assert result[0]["name"] == "C"  # heat 80 > 50

def test_query_speakers_filter_type():
    speakers = [
        {"voice_type":"a","name":"A","type":"bigtts","scene":"通用场景","heat":50},
        {"voice_type":"b","name":"B","type":"icl","scene":"通用场景","heat":100},
    ]
    result = mod.query_speakers(speakers, filters={"type":"icl"}, sort_by=None)
    assert len(result) == 1
    assert result[0]["type"] == "icl"

def test_query_speakers_no_filter():
    speakers = [{"voice_type":"a","name":"A","type":"bigtts","scene":"s","heat":1}]
    result = mod.query_speakers(speakers, filters=None, sort_by=None)
    assert len(result) == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py::test_query_speakers_filter_scene -v`
Expected: FAIL — `query_speakers` 未定义

- [ ] **Step 3: 实现 query_speakers + _list_speakers**

```python
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
    # 输出精简表格
    out = [{"name": s["name"], "voice_type": s["voice_type"], "type": s["type"],
            "gender": s.get("gender",""), "scene": s.get("scene",""),
            "description": s.get("description","")[:40], "heat": s.get("heat",0)} for s in result]
    print(json.dumps({"total": len(out), "speakers": out}, ensure_ascii=False, indent=2))
```

同时在 main() 的 argparse 里加 `--filter`（action append）和 `--sort`：

```python
    parser.add_argument("--filter", action="append", help="filter: scene=视频配音 / type=bigtts / lang=ja")
    parser.add_argument("--sort", choices=["heat"], help="sort by field")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: PASS（8 个测试）

- [ ] **Step 5: 实测 list-speakers**

Run: `uv run .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py --list-speakers --filter scene=视频配音 --sort heat`
Expected: JSON 输出 `{"total": N, "speakers": [...]}`，按热度排序

- [ ] **Step 6: Commit**

```bash
git add .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
git commit -m "feat(seed-audio-gen): --list-speakers 本地查询（filter/sort）"
```

---

### Task 5: batch 模式 + 成本预估

实现 `--batch`：并发合成、每项独立、总结带 `total_duration_seconds` + `estimated_cost_yuan`。

**Files:**
- Modify: `.agents/skills/seed-audio-gen/scripts/seed-audio-gen.py`（`_run_batch` 函数）
- Modify: `.agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py`

**Interfaces:**
- Consumes: `synthesize()`（Task 3 产出）
- Produces: `_run_batch(args)`；`batch_synthesize(items, **opts) -> dict` 可测函数

- [ ] **Step 1: 写 batch 总结计算测试**

```python
# 追加到 test_seed_audio_gen.py
def test_batch_summary():
    results = [
        {"original_duration": 60.0, "error": None},
        {"original_duration": 30.0, "error": None},
        {"original_duration": None, "error": "failed"},
    ]
    summary = mod.build_batch_summary(results)
    assert summary["total_duration_seconds"] == 90.0
    assert summary["estimated_cost_yuan"] == 1.5  # 90s/60 * 1.0
    assert summary["success_count"] == 2
    assert summary["fail_count"] == 1
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py::test_batch_summary -v`
Expected: FAIL — `build_batch_summary` 未定义

- [ ] **Step 3: 实现 build_batch_summary + _run_batch**

```python
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

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(task, i, dict(item)): i for i, item in enumerate(items)}
        for f in as_completed(futures):
            results.append(f.result())
    results.sort(key=lambda r: items.index({}))  # 保持顺序的近似处理
    print(json.dumps(build_batch_summary(results), ensure_ascii=False, indent=2))
```

注意：`results.sort` 那行有 bug（`items.index({})` 找不到），正确做法是按提交顺序收集。修正为：

```python
    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(task, i, dict(item)): i for i, item in enumerate(items)}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    print(json.dumps(build_batch_summary(results), ensure_ascii=False, indent=2))
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py -v`
Expected: PASS（9 个测试）

- [ ] **Step 5: 实测 batch 模式**

Run:
```bash
uv run .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py --batch '[{"prompt":"一位女声朗读：第一段","speaker":"zh_female_vv_uranus_bigtts"},{"prompt":"一位男声朗读：第二段","speaker":"zh_male_m191_uranus_bigtts"}]' --concurrency 2
```
Expected: JSON 含 `results`、`total_duration_seconds`、`estimated_cost_yuan`、`success_count: 2`

- [ ] **Step 6: Commit**

```bash
git add .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
git commit -m "feat(seed-audio-gen): batch 模式 + 成本预估"
```

---

### Task 6: 参考音频克隆实测验证

Task 3 的 `--ref-audio` 已实现 base64 编码，但需真实 API 验证克隆链路通。

**Files:**
- 无新文件，纯验证 Task 3 的实现

- [ ] **Step 1: 用 seed-tts-2.0 生成参考音频**

Run:
```bash
uv run .agents/skills/volcengine-tts/scripts/volcengine-tts.py "在深夜的城市里，每一盏灯背后都有一个不为人知的故事。" --speaker zh_male_xuanyijieshuo_uranus_bigtts -o /tmp/clone-verify
```
Expected: 生成 `tts_*.mp3`

- [ ] **Step 2: 用参考音频跑 seed-audio 克隆**

Run:
```bash
uv run .agents/skills/seed-audio-gen/scripts/seed-audio-gen.py "用参考音频里的音色朗读：今天我们要讲的故事，发生在一九八九年的冬天。" --ref-audio /tmp/clone-verify/tts_*.mp3
```
Expected: JSON 含 `audio_file`，无 error

- [ ] **Step 3: 确认 meta sidecar 含克隆相关字段**

Run: `cat seedaudio-output/*.meta.json | python3 -m json.tool | grep -E "text_prompt|original_duration|url"`
Expected: meta 含 prompt、duration、url

- [ ] **Step 4: Commit（无代码改动则跳过，记录验证通过）**

无代码改动，仅验证。在 SKILL.md 文档里记录验证结果（Task 7）。

---

### Task 7: SKILL.md + prompt-guide.md

写 SKILL.md（触发描述 + Quick Start + When NOT to use）和 `references/seedaudio-prompt-guide.md`（时间戳语法、场景元素、音色选择）。

**Files:**
- Create: `.agents/skills/seed-audio-gen/SKILL.md`
- Create: `.agents/skills/seed-audio-gen/references/seedaudio-prompt-guide.md`

**Interfaces:**
- Consumes: spec 的 SKILL.md 触发描述、prompt-guide 语法（实测 V1 确认的时间戳）

- [ ] **Step 1: 写 SKILL.md**

参考 `.agents/skills/volcengine-tts/SKILL.md` 的结构（frontmatter description + Quick Start + CLI Reference + When to Use / NOT to Use）。核心内容：

frontmatter `description`（从 spec 搬）：
```
生成式音频创作：从自然语言场景描述一次生成「人声+音效+BGM」成品音频（最长120s），支持时间戳精准控制（100ms粒度）、音色克隆、多角色对话、20语种。适合有声书/广播剧/影视配音/游戏音效/广告/视频片头——把 TTS+BGM+音效+混音的多步流程压成一次调用。不适用纯旁白（用 volcengine-tts，快11倍便宜14倍）或纯BGM（用 volcengine-bigmusic-bgm，时长精确）或实时对话（用双向流式TTS）。
```

正文包含：
- Quick Start（单句、batch、list-speakers、克隆示例）
- CLI Reference（参数表，从 spec 决策 4 搬）
- Environment Setup（`VOLC_SPEECH_API_KEY` 三级 fallback）
- Output Format（meta sidecar 结构，含 CDN URL 时效）
- When to Use / When NOT to Use（单向提示，不互指）
- 计费说明（1 元/分钟，按 original_duration，倍速不影响，克隆免费）

- [ ] **Step 2: 写 prompt-guide.md**

核心内容（从 spec + 实测）：
- **时间戳控制语法**：`[2.7s:5.7s]"台词"`，100ms 粒度，实测 V1 确认
- **场景元素结构**：BGM 描述 + 角色定义（性别/年龄/嗓音/语速/语气）+ 时间戳台词 + 音效描述
- **@音频N 引用**：references 里多条音频按顺序引用
- **音色选择**：指向 `speakers.md` 速查表
- **prompt 长度建议**：硬上限 3000 字符，人声中文建议 ≤400 字
- 完整 prompt 示例（从飞书 wiki 搬护肤广告 / 雨夜告别示例）

- [ ] **Step 3: 验证 SKILL.md 引用路径正确**

Run: `grep -oE '\[[^]]+\]\([^)]+\)' .agents/skills/seed-audio-gen/SKILL.md | grep -v 'http' | head`
Expected: 相对路径引用 `scripts/seed-audio-gen.py`、`references/seedaudio-prompt-guide.md` 等

- [ ] **Step 4: Commit**

```bash
git add .agents/skills/seed-audio-gen/SKILL.md .agents/skills/seed-audio-gen/references/seedaudio-prompt-guide.md
git commit -m "feat(seed-audio-gen): SKILL.md + prompt-guide.md"
```

---

### Task 8: refresh-speakers.py 音色表更新脚本

低频手动跑的脚本，用 AK/SK 调 ListSpeakers API 刷新 `speakers.json`。

**Files:**
- Create: `.agents/skills/seed-audio-gen/scripts/refresh-speakers.py`

**Interfaces:**
- Consumes: `VOLC_ACCESSKEY`/`VOLC_SECRETKEY`（env，不同于合成的 `VOLC_SPEECH_API_KEY`）
- Produces: 更新 `references/speakers.json` + `references/speakers.md`

- [ ] **Step 1: 写 refresh-speakers.py**

PEP 723 脚本，依赖 `volcenginesdkcore` + `volcenginesdkspeechsaasprod`（官方 SDK）。调用 ListSpeakers 分页拉全量，加工成 `speakers.json` 结构（复用 Task 1 的加工逻辑）。

参考用户提供的官方示例代码（AK/SK 鉴权，`volcenginesdkspeechsaasprod.SPEECHSAASPRODApi().list_speakers`）。

SKILL.md 标注：「音色表截至 2026-08-26，444 个，需更新时跑 `uv run scripts/refresh-speakers.py`，需 `VOLC_ACCESSKEY`/`VOLC_SECRETKEY`」。

- [ ] **Step 2: 实测 refresh-speakers**

Run: `uv run .agents/skills/seed-audio-gen/scripts/refresh-speakers.py`
Expected: 刷新 `speakers.json`，输出新条数

- [ ] **Step 3: Commit**

```bash
git add .agents/skills/seed-audio-gen/scripts/refresh-speakers.py
git commit -m "feat(seed-audio-gen): refresh-speakers.py 音色表更新脚本"
```

---

### Task 9: 端到端验证 + SKILL.md 收尾

全部功能实测一遍，确认 SKILL.md 的 Quick Start 示例逐字可跑。

**Files:**
- 无新文件，验证 + 微调

- [ ] **Step 1: 逐字跑 SKILL.md Quick Start 示例**

对照 [[skill-edits-verify-documented-examples]]：测试别用规范化子命令形式，逐字跑 SKILL.md 示例。每个 Quick Start 代码块都实跑一遍，确认输出符合 SKILL.md 描述。

- [ ] **Step 2: 验证 skill 软链接生效**

Run: `ls -la .claude/skills/seed-audio-gen 2>/dev/null || echo "需确认软链接"`
Expected: `.claude/skills/seed-audio-gen` 指向 `.agents/skills/seed-audio-gen`（若未自动创建需手动 `ln -s ../../.agents/skills/seed-audio-gen`）

- [ ] **Step 3: 修复发现的任何问题**

跑 Quick Start 时若发现示例不可用、参数名错、输出不符，修 SKILL.md 和脚本，重新验证。

- [ ] **Step 4: 最终 commit**

```bash
git add -A .agents/skills/seed-audio-gen/
git commit -m "feat(seed-audio-gen): 端到端验证通过 + SKILL.md 收尾"
```

- [ ] **Step 5: 更新 docs/skills/skills-list.md**

在 Current Core Skills 列表加 `seed-audio-gen` 条目，描述能力边界。

```bash
git add docs/skills/skills-list.md
git commit -m "docs: skills-list 加 seed-audio-gen 条目"
```

---

## Self-Review

**1. Spec 覆盖检查**：
- 决策 1（单 skill）→ 整个计划是一个 skill ✓
- 决策 2（单向提示不互指）→ Task 7 SKILL.md 的 When NOT to use ✓
- 决策 3（命名 seed-audio-gen）→ 全程使用 ✓
- 决策 4（CLI 参数）→ Task 3 argparse 全覆盖 ✓
- 决策 5（prompt 超长报错）→ Task 2 validate_prompt_length ✓
- 决策 5b（计费细节）→ Task 3 estimate_cost + meta + Task 5 batch ✓
- 决策 6（音色表本地化）→ Task 1 + Task 4 + Task 8 ✓
- 决策 7（meta sidecar + CDN URL）→ Task 3 synthesize ✓
- 决策 8（batch 成本预估）→ Task 5 ✓

**2. Placeholder 扫描**：Task 8 refresh-speakers.py 的实现描述较粗（"参考用户提供的官方示例"）——但这是低频辅助脚本，核心 CLI（Task 1-7）无 placeholder。Task 8 可在实现时对照用户已提供的官方示例代码细化。

**3. 类型一致性**：`synthesize()` 返回的 dict 在 Task 3 定义，Task 5 batch 复用一致。`query_speakers` / `build_batch_summary` / `build_body` 函数签名跨任务一致。

**4. 已核实项落地**：时间戳语法（Task 7 prompt-guide）、openspeech 端点命名（Task 3 build_body）、采样率默认 48000（Task 3 argparse）全部在计划中体现。
