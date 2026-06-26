---
name: seedream-image-gen
description: Generate high-quality images with the Seedream image model. Use for text-to-image, image-to-image with reference images, sequential group generation (storyboards/comics), web search-enhanced generation, and batch generation.
---

# Seedream Image Gen

Generate images with ByteDance Seedream 5.0 via the Volcengine Ark API.

## Quick workflow

1. Identify intent: `generate` (new image), `edit` (modify with reference), or `generate-batch` (many prompts).
2. Pick a size: `2K` (default), `3K`, `4K`, or `WIDTHxHEIGHT` (e.g. `2048x2048`, `4096x4096`).
3. If using reference images, prepare local files or URLs.
4. Run `--dry-run` first to inspect the request payload.
5. Run the script with `uv run`.
6. Inspect the output image and sibling `*.json` metadata.

## When to use

- Cost-sensitive image generation (Seedream is significantly cheaper than gpt-image-2).
- Chinese-language prompts and culturally specific styles (ink wash, guochao, water town, etc.).
- Text-heavy infographics and diagrams (Seedream 5.0's Chinese text rendering is a differentiator).
- Sequential group generation for storyboards, comics, or thematic series.
- Web search-enhanced generation for timely or knowledge-intensive topics.

## Script

Use `uv run`:

```bash
# Single generation (text-to-image)
uv run scripts/seedream_image_gen.py generate \
  --prompt "一只橘猫坐在窗台上，阳光洒在毛发上，窗外是秋天的枫叶" --size 2K

# With Chinese cultural style
uv run scripts/seedream_image_gen.py generate \
  --prompt "江南水乡诗意画卷，白墙黑瓦古建筑，石桥横跨清澈河面，乌篷船缓缓划过" \
  --size 4K --no-web-search

# Technical infographic
uv run scripts/seedream_image_gen.py generate \
  --prompt "生成一张信息图，解释啤酒酿造过程，5个步骤每步配插图，温暖色调" \
  --size 2K

# Image-to-image (style following, multi-reference fusion)
uv run scripts/seedream_image_gen.py generate \
  --prompt "参考图片的风格，生成一张秋天的公园场景" \
  --reference-image style-ref.jpg

# Sequential group generation (storyboard / comic)
uv run scripts/seedream_image_gen.py generate \
  --prompt "生成一组共4张连贯分镜：场景1宇航员维修飞船，场景2陨石袭击，场景3紧急躲避，场景4惊险逃回" \
  --size 2K --sequential --max-images 4

# Edit (alias for generate with reference image)
uv run scripts/seedream_image_gen.py edit \
  --prompt "把这只猫变成蓝色" \
  --reference-image cat.jpg

# Batch from a JSONL file
uv run scripts/seedream_image_gen.py generate-batch \
  --input prompts.jsonl --size 2K --out-dir output/seedream-image-gen/batch

# Dry-run: print the resolved request payload, never call the API
uv run scripts/seedream_image_gen.py generate \
  --prompt "..." --dry-run
```

The script writes a sibling `*.json` next to each output image with the prompt, model, size, web_search, reference_images, usage, and timestamp.

## Authentication

Loaded in this order, first non-empty wins:

1. `ARK_API_KEY` from the current shell.
2. `ARK_API_KEY` from `.env` in the current working directory.
3. Interactive prompt (TTY only).

`ARK_BASE_URL` is optional — defaults to `https://ark.cn-beijing.volces.com/api/v3`.

Do not commit credentials. The skill never writes credentials to disk.

**Get your API key**: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey

## Model

Default: `doubao-seedream-5-0-260128` (Seedream 5.0, SOTA as of 2026/02).

Override with `--model <id>` for other versions (e.g., `doubao-seedream-4-5-251128`).

## Size constraints

Seedream supports two size specification methods:

| Method | Format | Examples |
|--------|--------|----------|
| String resolution | `2K` / `3K` / `4K` | Model auto-determines exact dimensions |
| Exact pixels | `WIDTHxHEIGHT` | `2048x2048`, `4096x4096`, `2560x1440` |

Client-side validation:
- Total pixels must be in [3,686,400, 16,777,216] (2560×1440 to 4096×4096).
- Aspect ratio must be ≤ 16:1.

> 可用字符串分辨率因模型而异：默认 5.0 支持 `2K` / `3K` / `4K`；5.0 lite 多一个 `1K`；4.0 不支持 `3K`。完整矩阵见 `references/api-reference.md` 的「可用模型」表。脚本不会按模型校验，传了不支持的字符串会被 API 返回 400。

For WeChat covers, use `article-illustration` which handles the crop. This skill does not auto-crop.

## Output format

Default: `png`. Also supports `jpeg` / `jpg`.

## web_search

Default: **enabled**. Seedream 5.0 can web search to enhance generation quality for knowledge-intensive topics.
Disable with `--no-web-search` for purely abstract/creative prompts.

## Watermark

Default: **off**. Seedream's API watermark is disabled by default.
Enable with `--watermark` if needed.

## Sequential group generation

Trigger with `--sequential --max-images <n>` (1-15). Use for:
- Storyboards and film shots
- Comic strips
- Thematic image series
- Character-driven narrative scenes

## Reference images

- Local files: auto-encoded as base64 data URLs.
- URLs: passed through directly.
- Maximum 14 reference images per request.
- Formats: jpeg, png, webp, bmp, tiff, gif, heic, heif.
- File size ≤ 30MB each.

## Error handling

| Error | Behavior |
|-------|----------|
| 429 / 5xx / network timeout | Auto-retry up to 3 times with exponential backoff (1s, 2s, 4s) |
| 400 / 401 / 403 / 404 | No retry, immediate error with diagnostics |
| Timeout | Default 300s, configurable with `--timeout` |

## Prompt engineering

Seedream uses Chinese-language prompts by preference. The recommended formula:

```
[风格锚点] + [主体 + 行为 + 环境] + [细节元素] + [色彩 + 光影 + 构图] + [分辨率]
```

Key tips:
- Start with a style anchor (e.g., "中国古风写意", "赛博朋克", "扁平等距插图")
- Use concrete nouns: 白墙黑瓦 > 古建筑
- Wrap text content in Chinese quotes ""
- Avoid mixing conflicting styles

Full prompt guides in `references/prompt-engineering.md` and `references/styles/`.

## CLI reference

### `generate` flags

| Flag | Notes |
|------|-------|
| `--prompt` / `--prompt-file` | Required for `generate`. Mutually exclusive. |
| `--model` | Default `doubao-seedream-5-0-260128`. |
| `--size` | Default `2048x2048`. `2K`/`3K`/`4K` or `WIDTHxHEIGHT`. |
| `--output-format` | `png`/`jpeg`/`jpg`. Default `png`. |
| `--out` | Output file path. Default: `output/seedream-image-gen/<ts>-<slug>.png`. |
| `--out-dir` | Output directory. Default: `output/seedream-image-gen/`. |
| `--n` | 1-4, default 1. Independent concurrent generations. |
| `--reference-image` | Repeatable. Local path or URL. Max 14. |
| `--web-search` (default) / `--no-web-search` | Web search toggle. Default ON. |
| `--watermark` | Include Seedream watermark. Default OFF. |
| `--optimize-prompt` | `standard` or `fast`. |
| `--sequential` / `--max-images` | Group generation mode (1-15 images). |
| `--timeout` | Default 300s. |
| `--dry-run` | Print request body, never call API. |
| `--force` | Overwrite existing output files. |

### `edit` flags

Same as `generate`, with `--reference-image` required.

### `generate-batch` flags

| Flag | Notes |
|------|-------|
| `--input` | Required. JSONL file (bare string or object per line). |
| `--out-dir` | Default `output/seedream-image-gen/batch/`. |
| `--concurrency` | Default 3. Max concurrent requests. |
| `--model` / `--size` / `--output-format` / `--web-search` / `--no-web-search` / `--timeout` / `--dry-run` / `--force` | Same as `generate`. |

## JSONL job format (generate-batch)

One job per line:
- Bare string = prompt with CLI defaults.
- JSON object = prompt + per-job overrides.

```jsonl
"一只猫坐在窗台上"
{"prompt": "一条狗在雪地里跑", "size": "2K", "output_format": "jpeg"}
{"prompt": "生成一组4张故事书插图", "sequential_image_generation": "auto", "max_images": 4}
```

Per-job overrides: `prompt` (required), `model`, `size`, `output_format`, `watermark`, `web_search`, `reference_image`, `optimize_prompt`, `sequential_image_generation`, `max_images`.

## Output handling

- Final images: `output/seedream-image-gen/` by default.
- Sibling `*.json` metadata next to each image (prompt, model, size, watermark, web_search, reference_images, usage, timestamp).
- Reruns fail on existing files unless `--force`.

## References

- `references/api-reference.md` — API endpoint, parameters, error codes, official doc links.
- `references/prompt-engineering.md` — Prompt formula, best practices, Chinese/English tips.
- `references/styles/editorial-essay.md` — 散文/随笔/文艺评论风格 prompts.
- `references/styles/technical-diagram.md` — 技术架构/图表风格 prompts.
- `references/styles/education-science.md` — 教育/科普风格 prompts.
- `references/styles/visual-narrative.md` — 视频/叙事/分镜风格 prompts.
- `references/styles/editorial-pencil-sketch.md` — 编辑式铅笔淡彩手绘风格，适合工作流与人机协作场景。
- `references/styles/text-effects.md` — 16种文字特效 + 中文文本渲染技巧.
