---
name: volcengine-tts
description: >
  Generate speech audio from text using Volcano Engine's (火山引擎) Doubao Speech Synthesis Model 2.0 (豆包语音合成大模型2.0, seed-tts-2.0).
  Use this skill whenever the user needs text-to-speech, voiceover, narration, dubbing, 配音, 旁白, 朗读, TTS, speech synthesis, or audio generation from text.
  Also use when the user mentions 火山引擎 TTS, 豆包语音, volcengine speech, or needs AI-generated voice audio for videos, podcasts, or presentations.
  Supports single-sentence and batch synthesis with Chinese, English, Japanese, Spanish, Indonesian, Portuguese, Korean, and dialects.
  This skill should ALWAYS be used for any TTS/语音合成 task — never attempt to call the Volcano Engine TTS API directly without it.
---

# Volcengine TTS

Generate speech audio using Volcano Engine's Doubao Speech Synthesis Model 2.0 (`seed-tts-2.0`).

## Quick Start

```bash
# Single sentence — outputs MP3 + .meta.json to tts-output/
uv run scripts/volcengine-tts.py "你好，欢迎使用豆包语音合成"

# With speaker selection
uv run scripts/volcengine-tts.py "Hello world" --speaker en_female_dacey_uranus_bigtts

# Batch mode — concurrent synthesis
uv run scripts/volcengine-tts.py --batch '[{"text":"第一句","speaker":"zh_female_vv_uranus_bigtts"},{"text":"第二句"}]'

# List available speakers
uv run scripts/volcengine-tts.py --list-speakers
```

## Script

The core implementation is `scripts/volcengine-tts.py` — a PEP 723 inline-dependency Python script.

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

## CLI Reference

### Single Sentence Mode (default)

```
uv run scripts/volcengine-tts.py <text> [options]
```

Output: JSON to stdout with `audio_file`, `duration_ms`, `text`, `speaker`, `format`, `sample_rate`, `text_words`, `log_id`, and `error` (on failure).

### Batch Mode

```
uv run scripts/volcengine-tts.py --batch '<json-array>' [options]
```

Each item: `{"text": "...", "speaker": "...", ...}`. Extra keys override per-item options (speaker, speech_rate, volume, etc.).

Output: JSON array of results, each with the same fields as single mode. Failed items have `error` set; successful items continue independently.

### Key Options

| Flag | Default | Description |
|------|---------|-------------|
| `--speaker`, `-s` | `zh_female_vv_uranus_bigtts` | Voice/speaker ID |
| `--output-dir`, `-o` | `./tts-output/` | Output directory |
| `--batch`, `-b` | — | Batch JSON input (disables positional text) |
| `--concurrency`, `-c` | `3` | Max parallel requests in batch mode |
| `--format` | `mp3` | Audio format: mp3, pcm, ogg_opus, wav |
| `--sample-rate` | `24000` | Sample rate: 8000, 16000, 22050, 24000, 32000, 44100, 48000 |
| `--speech-rate` | `0` | Speed [-50, 100], 100=2x, -50=0.5x |
| `--volume` | `0` | Volume [-50, 100], 100=2x |
| `--pitch` | `0` | Pitch [-12, 12] semitones |
| `--model` | `seed-tts-2.0-standard` | `seed-tts-2.0-standard` (fast/stable) or `seed-tts-2.0-expressive` (emotional range, supports `--context`) |
| `--context` | — | Natural language prompt for HOW to speak — tone, emotion, pacing, persona. E.g. "用痛心的语气说话", "像深夜电台主持人一样温柔地读", "用激动兴奋的语气". Only works with `--model expressive`. |
| `--ssml` | — | Parse input text as SSML |
| `--language` | — | Explicit language: zh-cn, en, ja, es-mx, id, pt-br, ko |
| `--latex` | — | Enable LaTeX formula reading for math/physics content |
| `--latex-parser v2` | — | Stronger LaTeX parsing (auto-enables `--strip-markdown`, higher latency) |
| `--silence-duration` | `0` | Trailing silence in ms [0, 30000] |
| `--watermark` | — | Add AIGC audio watermark |
| `--strip-markdown` | — | Remove Markdown syntax (e.g. `**bold**` → "bold") |
| `--strip-emoji` | — | Remove emoji characters before TTS |
| `--list-speakers` | — | Fetch and display available voices, then exit |

### Model Selection

| Model | Latency | `--context` | Best for |
|-------|---------|:---:|----------|
| `seed-tts-2.0-standard` (default) | Low | ❌ | General voiceover, narration, dubbing — fast and stable |
| `seed-tts-2.0-expressive` | Higher | ✅ | Emotional delivery, nuanced tone — use with `--context` |

`--context` (API: `context_texts`) lets you give natural language voice instructions — "用痛心的语气说话", "像新闻主播一样播报". This is the key reason to choose expressive over standard.

## Output Format

### Success (single)
```json
{
  "audio_file": "tts-output/tts_20260616_113000_001.mp3",
  "duration_ms": 1240,
  "text": "你好世界",
  "speaker": "zh_female_vv_uranus_bigtts",
  "format": "mp3",
  "sample_rate": 24000,
  "text_words": 4,
  "log_id": "202606161130000FACFE6D19421815D605"
}
```

### Error (single)
```json
{
  "audio_file": null,
  "duration_ms": null,
  "text": "你好世界",
  "error": "45002001: No readable text!",
  "log_id": "202606161130000FACFE6D19421815D605"
}
```

### Batch
```json
{
  "results": [
    {"audio_file": "tts-output/tts_20260616_113000_001.mp3", "duration_ms": 1240, ...},
    {"audio_file": null, "error": "429: quota exceeded for types: concurrency", ...}
  ],
  "total_duration_ms": 1240,
  "success_count": 1,
  "fail_count": 1
}
```

## Metadata Sidecar

Each audio file gets a `.meta.json` sibling with the same base name:
```
tts-output/
  tts_20260616_113000_001.mp3
  tts_20260616_113000_001.meta.json
```

Downstream tools (video compositors, subtitle generators) should read the `.meta.json` files — they survive process restarts and don't require re-reading the audio.

## Voice Selection

For the complete voice catalog, read `references/volcengine-speakers.md`. Quick picks:

| Scenario | Speaker ID | Description |
|----------|-----------|-------------|
| 通用旁白 (General narration) | `zh_female_vv_uranus_bigtts` | Vivi 2.0 — warm, versatile female |
| 技术解说 (Tech explainer) | `zh_male_m191_uranus_bigtts` | 云舟 2.0 — clear, professional male |
| 故事讲述 (Storytelling) | `zh_female_wenroumama_uranus_bigtts` | 温柔妈妈 2.0 — warm, gentle |
| 悬疑解说 (Suspense) | `zh_male_xuanyijieshuo_uranus_bigtts` | 悬疑解说 2.0 — dramatic male |
| 英语旁白 (English) | `en_female_dacey_uranus_bigtts` | Dacey — natural American female |
| 英语男声 (English male) | `en_male_tim_uranus_bigtts` | Tim — natural American male |

Use `--list-speakers` to fetch the current full list from the API.

## Error Handling

- **Retryable errors**: HTTP 429, 5xx, and Volcano codes 55000000 — auto-retried with exponential backoff (1s → 2s → 4s, max 3 attempts)
- **Non-retryable errors**: HTTP 4xx (except 429), Volcano codes 45000000–45002001 — returned immediately with error message
- **Batch mode**: Failed items report error in their result object; other items continue independently
- Always include the `log_id` in error output for support escalation
- For full error code reference and official docs, read `references/volcengine-api-docs.md`

## When to Use This Skill

- User asks to generate voice audio, TTS, speech synthesis
- User needs voiceover/narration/dubbing for video, podcast, or presentation
- User mentions 火山引擎, 豆包语音, volcengine TTS, or seed-tts
- User wants to convert text to spoken audio in Chinese, English, Japanese, etc.
- User needs batch voice generation from a script or article

## When NOT to Use

- Voice cloning / 声音复刻 — needs a separate skill (uses `seed-icl-2.0`)
- Real-time speech recognition / ASR — different API
- Music/audio editing — not TTS
