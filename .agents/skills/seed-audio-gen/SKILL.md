---
name: seed-audio-gen
description: >
  从一条自然语言场景描述，一次生成「人声 + 音效 + 背景音乐」混合的成品音频（最长 120 秒）。Use this skill whenever the user wants to generate a complete audio scene — voice combined with sound effects, ambient sound, and/or background music — in a single call. 触发场景包括且不限于：有声书/广播剧/播客的场景化音频、影视配音、游戏 NPC 台词 + 战斗氛围、广告配音 + 音乐床、视频片头音频、多角色对话 + 环境音、用参考音频克隆音色生成多段语音、需要时间戳精准控制台词进出时机的配音。关键信号：用户提到「场景音」「环境音」「音效 + 配音」「BGM + 人声」「一次生成成品音频」「多角色对话」「有声书/广播剧升级到剧感」时，必须使用本 skill。本 skill 是 seed-audio-1.0（火山引擎豆包音频生成模型），不是传统 TTS——它把 TTS + 配乐 + 拟音 + 混音的多步流程压成一次调用。不适用场景（用更优工具）：纯旁白/批量朗读用 volcengine-tts（快 11 倍、便宜 14 倍、流式）；纯背景音乐用 volcengine-bigmusic-bgm（时长精确）；实时对话用双向流式 TTS；SSML/拼音注解用 volcengine-tts。
---

# seed-audio-gen

Generate complete audio scenes from natural language prompts using Volcano Engine's Doubao Audio Generation 1.0 (`seed-audio-1.0`). One API call produces voice + sound effects + BGM — a mixed, mastered audio clip up to 120 seconds.

This is a **generative audio model**, not a traditional TTS. Think of it as "prompt an audio scene" rather than "read this text aloud."

**Project homepage**: https://seed.bytedance.com/seedaudio1_0

## Quick Start

```bash
# Single scene — outputs MP3 + .meta.json to seedaudio-output/
uv run scripts/seed-audio-gen.py "一位温柔女声朗读：你好，欢迎使用豆包音频生成模型"

# BGM + voice + sound effects scene
uv run scripts/seed-audio-gen.py "轻柔的钢琴BGM背景下，一位温柔女声缓缓说道：今晚的月色真美。句尾伴随一声微风拂过的音效。"

# With speaker selection (reuses seed-tts-2.0 voice catalog)
uv run scripts/seed-audio-gen.py "用深沉的语气朗读：夜幕降临，城市亮起了万家灯火。" --speaker zh_male_dongfanghaoran_uranus_bigtts

# Voice cloning from local reference audio
uv run scripts/seed-audio-gen.py "用参考音频的音色说：这是克隆后的声音。" --ref-audio ~/reference-speaker.wav

# Remote reference audio URL
uv run scripts/seed-audio-gen.py "用参考音色说：远程克隆也可以。" --ref-audio-url https://example.com/ref.wav

# Multi-character cloning: up to 3 reference audios, bound in CLI order
# (mix --ref-audio local paths and --ref-audio-url URLs; @音频N follows the flags left to right)
uv run scripts/seed-audio-gen.py '@音频1的声音（中年男性，低沉）用沉稳的语气说："大家好，我是一号男主播。"@音频2的声音（年轻女性，甜美）笑着回应："大家好，我是二号女主播。"' \
  --ref-audio ~/voice-male.wav --ref-audio-url https://example.com/voice-female.wav

# Batch mode — concurrent scene generation with cost estimate
uv run scripts/seed-audio-gen.py --batch '[{"prompt":"女声朗读：这是第一段。"},{"prompt":"男声朗读：这是第二段。"}]'

# List available speakers (local table, no API call)
uv run scripts/seed-audio-gen.py --list-speakers
```

## Script

The core implementation is `scripts/seed-audio-gen.py` — a PEP 723 inline-dependency Python script.

**Always run with `uv run`** — it auto-creates an isolated environment from the inline metadata. Never use bare `python` or `pip`.

## Environment Setup

The script reads `VOLC_SPEECH_API_KEY` with three-level fallback:

1. `VOLC_SPEECH_API_KEY` environment variable
2. `.env` file in the current working directory
3. `~/.volcengine.env` (user-level config)

To set up permanently:

```bash
echo 'VOLC_SPEECH_API_KEY=your-key-here' >> ~/.volcengine.env
```

Note: Unlike `volcengine-tts`, this skill does **not** require `X-Api-Resource-Id` or AK/SK. Only `VOLC_SPEECH_API_KEY` (X-Api-Key) is needed for everyday use. The `--list-speakers` command reads from a local table and does not call the API.

## CLI Reference

### Single Scene Mode (default)

```
uv run scripts/seed-audio-gen.py <prompt> [options]
```

Output: JSON to stdout with `audio_file`, `duration`, `original_duration`, `url`, `subtitle`, `log_id`, `model`, `text_prompt`, `estimated_cost_yuan`, and `error` (on failure). Each audio file also gets a `.meta.json` sidecar.

### Batch Mode

```
uv run scripts/seed-audio-gen.py --batch '<json-array>' [options]
```

Each item is an object with `prompt` (or `text_prompt`) plus optional per-item overrides: `speaker`, `references`, `format`, `sample_rate`, `speech_rate`, `subtitle`. To clone voices in batch, pass the full API `references` array per item — the `--ref-audio` / `--ref-audio-url` CLI flags are **not** read from batch items and are **not** shared into items:

```json
[
  {"prompt": "@音频1的声音说：第一段。", "references": [{"audio_url": "https://example.com/a.wav"}]},
  {"prompt": "用这个音色说：第二段。", "references": [{"audio_data": "<base64>"}]}
]
```

Items without `references` use no voice cloning unless `speaker` is set. A failed item reports its own `error`; other items continue.

Output: JSON with `results` array, `total_duration_seconds`, `estimated_cost_yuan`, `success_count`, `fail_count`.

### Prompt Input

| Parameter | Required | Description |
|---|---|---|
| `<prompt>` (positional) | Yes | Natural language scene description, max 3000 chars |

If prompt exceeds 3000 characters, the CLI rejects with an error including the exact length, the limit, and a hint to split into multiple calls.

### Reference (voice / image source)

| Flag | Description |
|---|---|
| `--speaker <id>` | Speaker ID, reuses the seed-tts-2.0 `_bigtts`/`_tob` voice catalog |
| `--ref-audio <path>` | Local reference audio file (auto base64-encoded). Each clip ≤30s, ≤10MB, wav/mp3/pcm/ogg_opus. **Repeat up to 3 times** for multi-character cloning |
| `--ref-audio-url <url>` | Remote reference audio URL (`http(s)`). Same repeat/ordering rules as `--ref-audio` |

`--speaker` is mutually exclusive with the reference-audio flags (pick one voice source). Up to 3 reference audios total; `--ref-audio` and `--ref-audio-url` may be mixed, and the `@音频1`..`@音频3` numbering follows the flags left-to-right in CLI order. Putting a URL in `--ref-audio` or a local path in `--ref-audio-url` is rejected with a hint before any API call.

**Local media is validated pre-flight** (before base64/encode/upload): a local `--ref-audio` must be ≤10MB and ≤30s (duration read via `mutagen`; raw `.pcm` skips the duration check since it has no header), a local `--ref-image` ≤10MB — over-limit files fail fast with the measured size/duration and a fix hint. Remote URLs cannot be validated locally (the server downloads them), so those limits are enforced by the API.

| Flag | Description |
|---|---|
| `--ref-image <path>` | Local reference image path (auto base64-encoded, max 10MB, jpeg/png/webp, max 1 image) — generates audio matching the picture's atmosphere/character setup; with an image, `text_prompt` can be just the lines to speak. API support verified 2026-08-27 |
| `--ref-image-url <url>` | Remote reference image URL |

Image references **cannot be mixed with audio references or `--speaker`** (API error `45001001: image reference cannot be mixed with audio or video references`; official doc: image_data/image_url 不能与 audio_data、audio_url 或 speaker 同时传入；the CLI pre-validates this).

### Audio Config

| Flag | Default | Description |
|---|---|---|
| `--model` | `seed-audio-1.0` | Model version; open string, reserved for future 2.0 |
| `--format` | `mp3` | Audio format: wav, mp3, pcm, ogg_opus |
| `--sample-rate` | `48000` | Sample rate: 8000, 16000, 24000, 32000, 44100, 48000 |
| `--speech-rate` | `0` | Speed [-50, 100], 100=2x, -50=0.5x |
| `--loudness-rate` | `0` | Volume [-50, 100] |
| `--pitch-rate` | `0` | Pitch [-12, 12] semitones |
| `--subtitle` | off | Enable sentence + word-level millisecond timestamps |

### Watermark

| Flag | Description |
|---|---|
| `--watermark` | AIGC explicit watermark (rhythmic identifier at audio end) |
| `--watermark-meta` | Implicit metadata watermark (header metadata) |

### General

| Flag | Default | Description |
|---|---|---|
| `-o, --output-dir` | `./seedaudio-output/` | Output directory |
| `--batch <json>` | — | Batch mode, JSON array of scene objects |
| `--concurrency` | `3` | Max parallel requests in batch mode |
| `--list-speakers` | — | List speakers from local table (no API call) |
| `--filter <k=v>` | — | Filter speakers: `scene=视频配音`, `type=bigtts`, `lang=ja` |
| `--sort heat` | — | Sort speakers by heat (popularity) |

### Deliberately Omitted Flags

The following flags from `volcengine-tts` are intentionally **not** exposed in `seed-audio-gen`, because seed-audio handles everything through the natural language `text_prompt`:

- `--context` / `--ssml` / `--latex` — these are seed-tts-2.0 features. In seed-audio, express tone, pacing, and emotion directly in the prompt.
- `--no-subtitle` — seed-audio subtitle is off by default (unlike seed-tts-2.0 where it's on by default).

## Output Format

### Success (single)

```json
{
  "audio_file": "seedaudio-output/seedaudio_20260826_210000_a1b2c3.mp3",
  "duration": 9.3,
  "original_duration": 9.3,
  "url": "https://lf3-speech-sign.bytednsdoc.com/...",
  "fetched_at": "2026-08-26T21:00:00+08:00",
  "url_expires_at": "2026-08-26T23:00:00+08:00",
  "subtitle": null,
  "log_id": "202608262100000FACFE6D19421815D605",
  "model": "seed-audio-1.0",
  "text_prompt": "一位温柔女声朗读：你好世界",
  "estimated_cost_yuan": 0.16,
  "elapsed_s": 12.45,
  "error": null
}
```

### Error (single)

```json
{
  "audio_file": null,
  "error": "45001116: text_prompt length 3600 exceeds maximum of 3000 chars...",
  "log_id": "",
  "elapsed_s": 0.01,
  "text_prompt": "..."
}
```

### Batch

```json
{
  "results": [
    {"audio_file": "seedaudio-output/seedaudio_20260826_210000_a1b2c3.mp3", "duration": 9.3, "estimated_cost_yuan": 0.16, ...},
    {"audio_file": null, "error": "429: quota exceeded", ...}
  ],
  "total_duration_seconds": 120.5,
  "estimated_cost_yuan": 2.01,
  "success_count": 8,
  "fail_count": 2
}
```

## Metadata Sidecar

Each audio file gets a `.meta.json` sibling with the same base name:

```
seedaudio-output/
  seedaudio_20260826_210000_a1b2c3.mp3
  seedaudio_20260826_210000_a1b2c3.meta.json
```

The meta file includes all result fields: `audio_file`, `duration`, `original_duration`, `url`, `fetched_at`, `url_expires_at`, `subtitle`, `log_id`, `model`, `text_prompt`, `estimated_cost_yuan`, `elapsed_s`, and `error`.

### CDN URL Expiry

The API returns a temporary CDN URL valid for **2 hours**. The `fetched_at` and `url_expires_at` fields track the validity window. The local `audio_file` is the permanent primary storage; the URL is a convenience copy. Downstream tools should check `url_expires_at` and fall back to the local file when the URL expires.

### Subtitle Timestamps

When `--subtitle` is enabled, the `subtitle` field contains sentence-level and word-level timestamps in milliseconds. Use for: subtitle generation, B-roll alignment, lip-sync hinting, karaoke-style highlighting.

## Voice Selection

**Query the catalog with `--list-speakers`** (reads a local table, no API call). Do **not** read `references/speakers.json` into context — it is ~220KB / 444 voices. `references/speakers.md` is a short curated shortlist (Top 5 per scene, with trial links), not the full list.

### Common-scene quick picks

For the usual scenes, reach for these defaults first; otherwise browse `references/speakers.md` or `--list-speakers`:

| Scenario | Voice | voice_type |
|---|---|---|
| General narration / podcast intro (default female) | Vivi 2.0 · warm, calm (heat 100) | `zh_female_vv_uranus_bigtts` |
| Ad / brand read (warm female) | 咪仔 2.0 · steady, elegant | `zh_female_mizai_uranus_bigtts` |
| Suspense / dramatic narration (male) | 悬疑解说 2.0 · dramatic | `zh_male_xuanyijieshuo_uranus_bigtts` |
| Authoritative narrative / drama male lead | 东方浩然 2.0 · deep, heroic | `zh_male_dongfanghaoran_uranus_bigtts` |
| Audiobook / late-night emotional (male) | 深夜播客 · soft, atmospheric | `zh_male_shenyeboke_uranus_bigtts` |
| Children / picture book | 小雪 2.0 · sweet, patient | `zh_female_xiaoxue_uranus_bigtts` |
| English content | Michael (m) / Dacey (f) | `ICL_uranus_en_male_michael_tob` / `en_female_dacey_uranus_bigtts` |
| Multi-character / niche roles | describe the character, or clone with `--ref-audio` | `--list-speakers --filter scene=角色扮演` (156 voices) |

Browse by scene/heat:

```bash
# Full catalog
uv run scripts/seed-audio-gen.py --list-speakers

# Filter by scene type
uv run scripts/seed-audio-gen.py --list-speakers --filter scene=视频配音

# Filter by language, sorted by heat
uv run scripts/seed-audio-gen.py --list-speakers --filter lang=ja --sort heat
```

To refresh the speaker table when new voices are released, run:

```bash
uv run scripts/refresh-speakers.py
```

This requires AK/SK (`VOLC_ACCESSKEY`/`VOLC_SECRETKEY`) and the internal Volcano SDK preinstalled; the ListSpeakers API uses a different auth system than everyday synthesis.

## Prompt Guide

For the full prompt-writing guide — timestamp syntax, total-duration declaration, scene element structure, `@音频N` multi-voice binding, directing vocabulary, voice selection, and complete worked examples — read `references/seedaudio-prompt-guide.md`.

### Scenario quick reference

seed-audio-gen handles **mixed audio scenes** (voice + SFX + BGM together) — not single-element generation. Match your scenario to a worked example in the prompt guide:

| Scenario | Key elements | Example in prompt-guide |
|---|---|---|
| 广告/视频片头配音 | 台词 + 产品音效 + BGM + 时间戳 | Example 1: Skincare Ad |
| 影视/剧情对白 | 多角色对话 + 环境音 + 情绪节奏 | Example 2: Rainy Night Farewell |
| 游戏 NPC 台词 | 角色音色 + 动作音效 + 氛围 BGM | Example 3: Game Character Voice |
| 有声书/广播剧 | 旁白 + 多角色 + 场景氛围 | Example 4: Audiobook Scene |
| 多角色音色克隆 | 2-3 条参考音频 + `@音频N` 绑定 | Multi-Reference section |
| 超过 120s 长内容 | 分段生成 + 末段音频回灌做参考延长 | Long-form section below |
| 纯音效场景 | 无台词，只有 SFX/环境音 | 无独立示例；prompt 里只写音效描述、不写台词 |
| 纯 BGM 场景 | 无台词无人声，只有音乐 | 能出粗氛围底垫，但时长不精确、非专用音乐模型；**要精确秒数/干净配乐用 `volcengine-bigmusic-bgm` 更优** |

The pattern across all examples: describe BGM, define characters (gender/age/timbre/tone), write timestamped dialogue, describe SFX — all in one `text_prompt`. The model orchestrates them onto a single timeline.

## Long-form Content (>120s): Audio Extension

Each call generates at most 120s. For longer scenes (audiobook chapters, multi-scene podcasts), chain calls while keeping voices consistent:

1. Generate segment 1 (≤120s).
2. Generate segment 2 with `--ref-audio segment1.mp3` (or the tail few seconds of it) — the model treats the previous output as a voice reference and extends with the same timbre. For multi-character scenes, pass each character's reference audio again in the same order, keeping the `@音频N` bindings identical.
3. Repeat, always referencing the most recent segment.

This is the official "音频延长" workflow — chaining references keeps multi-character voices consistent across extensions ("在多次音频延长中保持音色的高度一致").

For a recurring long-running series (fixed cast across many episodes), prefer registering a fixed speaker ID (`_tob` ICL voice) over ad-hoc cloning — see the Voice Selection section.

## Error Handling

- **Prompt too long**: `PromptTooLongError` — text_prompt exceeds 3000 chars. Rejected with length, limit, and hint to split into multiple calls.
- **Retries on transient failures**: HTTP 429/500/502/503/504, service-internal code `55000000`, and network/timeout errors retry up to 3 times with exponential backoff (1s → 2s → 4s). Deterministic 4xx client errors (bad auth, bad params, prompt too long) fail fast with no retry. The result includes `attempts` (the try count).
- **API errors**: HTTP non-200 or missing `audio` field — returned with error code + message + `log_id`.
- **Network/exception**: Exception type and message returned in the `error` field.
- **Batch mode**: Each item retries independently; a failed item reports its error in its result object while other items continue.
- Always include the `log_id` in error output for support escalation.

## Billing

- **1 yuan per minute**, billed by `original_duration` (the model's raw output duration).
- **Speed (`--speech-rate`) does not affect billing** — the cost is always based on the unadjusted `original_duration`. A 2x speed-up still costs the same as 1x.
- **Voice cloning is free** — passing `--ref-audio` or `--ref-audio-url` incurs no additional charge.
- Registered custom voices (`_tob` ICL speakers) are billed by **voice slot**, not per call.
- Each call generates up to 120s. Batch `estimated_cost_yuan` is the sum of all items.

## When to Use This Skill

- User wants to generate a complete audio scene with voice + BGM + sound effects in one call
- User mentions 生成式音频, seed-audio, 豆包音频, 有声书, 广播剧, 影视配音, 游戏音效, 广告配音, 视频片头
- User needs multi-character dialogue, emotional voice acting, or timestamped scene orchestration
- User needs voice cloning for consistent character voices across scenes
- User wants to create audio content for audiobooks, radio dramas, video dubbing, game audio, or podcast intros
- User has a scene description in natural language (not a verbatim script to be read word-for-word)

## When NOT to Use

- **Pure narration / reading text verbatim** — use `volcengine-tts`. seed-audio is ~11x slower and ~14x more expensive for simple TTS. It may also rewrite or embellish the input text (it's a generative model, not a deterministic reader).
- **Precise, clean BGM tracks** — use `volcengine-bigmusic-bgm`. seed-audio *can* emit a rough music-only / ambient bed when you omit dialogue (verified), but it is not a dedicated music model: track duration is not precisely controllable and music quality trails BigMusic. Reach for BigMusic when you need an exact-length, standalone music track; seed-audio's BGM is best as part of a mixed voice+SFX+music scene.
- **Real-time / streaming conversation** — use a bidirectional streaming TTS. seed-audio is non-streaming and takes 10+ seconds per call.
- **SSML-precise control** — use `volcengine-tts`. seed-audio does not support SSML; all timing and emotion is expressed in natural language, which is expressive but not deterministic.
- **Verbatim word-for-word accuracy required** — seed-audio is a generative model and may paraphrase. If you need every character read exactly as written, use `volcengine-tts`.
- **Long-form content beyond 120s** — the model maxes out at 120s per call. Use the audio-extension chaining workflow above for scene content longer than 120s; for plain long-form narration, `volcengine-tts` is also faster and cheaper.