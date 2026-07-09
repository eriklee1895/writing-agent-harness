---
name: gpt-image-2
description: "Generate, edit, and batch-generate raster images with OpenAI's gpt-image-2 model via the Image API. Use when the user wants to create or modify a picture file — a photo, poster, product shot, character, infographic, illustration, collage, banner, or slide. Handles background swaps, object removal, text replacement, style transfer, and up to 16 reference images. Batch mode for many prompts or JSONL files. gpt-image-2 is SOTA for in-image text rendering (2026/06) — ideal when the picture needs readable words. Outputs PNG, JPEG, or WebP. Do NOT use for SVG/vector icons, matplotlib charts, Mermaid/Excalidraw diagrams, HTML/CSS mockups, or other code-native output."
---

# gpt-image-2

Generate and edit images with OpenAI's gpt-image-2 model via the Image API.

## Quick workflow

1. Identify intent: `generate` (new image), `edit` (modify existing), or `generate-batch` (many prompts).
2. Pick a size preset or pass a `WIDTHxHEIGHT` string (must satisfy the [Size constraints](#size-constraints) below).
3. If using references, prepare PNG/WebP/JPG files under 50MB each.
4. For complex prompts, run `--dry-run` first to see the final augmented prompt and request payload.
5. Run the bundled script with `uv run`.
6. Inspect the output PNG (or JPEG/WebP) and the sibling `*.json` metadata.

## When to use

- A photo, illustration, sprite, product shot, mockup, infographic, poster, slide, or banner that benefits from AI generation.
- An edit of an existing image: background replacement, object removal, text replacement/localization, style transfer, inpainting with a mask, compositing multiple reference images.
- A batch of variants from many prompts (asynchronous, configurable concurrency).
- Text-heavy images (posters, slides, infographics with verbatim labels): gpt-image-2's strongest differentiator.

## When NOT to use

- SVG/vector icons, code-native diagrams, deterministic layout, ASCII wireframes.
- Anything that needs a clean transparent background straight from the API. gpt-image-2 accepts `background=transparent`, but the official cookbook recommends generating opaque and using a downstream `rembg` step for the cleanest transparent assets.
- Tasks better served by deterministic code or an existing repo-native asset.

## Script

Use `uv run`. Dependencies are self-declared in the script's PEP 723 inline metadata — `uv run` auto-installs them in an isolated environment.

```bash
# Single generation
uv run scripts/gpt_image_2.py generate \
  --prompt "A cozy alpine cabin at dawn, mist over the lake" \
  --size landscape \
  --out output/gpt-image-2/cabin.png

# Edit: replace background while keeping the product
uv run scripts/gpt_image_2.py edit \
  --image input.png \
  --prompt "Replace only the background with a warm sunset gradient. Keep the product and its edges unchanged." \
  --out output/gpt-image-2/sunset-edit.png

# Edit with multiple reference images (up to 16) + mask
uv run scripts/gpt_image_2.py edit \
  --image product.png \
  --image style-ref.png \
  --mask inpaint-mask.png \
  --prompt "Use image 1 as the subject. Use image 2 only for style guidance (palette, line quality). Repaint the masked region as if it were a single coherent scene." \
  --out output/gpt-image-2/merged.png

# Batch from a JSONL file
uv run scripts/gpt_image_2.py generate-batch \
  --input prompts.jsonl \
  --out-dir output/gpt-image-2/batch \
  --concurrency 5

# Dry-run: print the resolved request payload, never call the API
uv run scripts/gpt_image_2.py generate \
  --prompt "..." --dry-run
```

The script writes a sibling `*.json` next to each output image with the resolved prompt, model, size, base URL, and timestamp. Use this for traceability.

## Authentication

Loaded in this order, first non-empty wins:

1. `OPENAI_API_KEY` and `OPENAI_BASE_URL` from the current shell.
2. The same keys from `.env` in the current working directory (lines like `OPENAI_API_KEY=...` and `OPENAI_BASE_URL=...`; comments and blank lines are ignored; values are only set if not already in the environment).
3. Interactive prompt (only when stdin and stderr are both a TTY) — temporary input, never echoed or written to disk.

Do not commit credentials. The skill never writes credentials to disk.

## Model selection

- Default: `gpt-image-2` (snapshot `gpt-image-2-2026-04-21`, SOTA as of 2026/06 per the official cookbook).
- When `OPENAI_BASE_URL` matches a known gateway, the model name is automatically namespaced:
  - `https://api.ofox.io/v1` → `openai/gpt-image-2`
  - everything else → `gpt-image-2`
- Override with `--model <name>` if your gateway expects a different identifier.

## gpt-image-2 capabilities and constraints (read this before invoking)

These are the non-obvious rules that will break your run if you ignore them. They are verified against the official OpenAI Image API docs and cookbook.

### Do not use `input_fidelity`

The Image API disables `input_fidelity` for gpt-image-2 ("the API doesn't allow changing it because the model processes every image input at high fidelity automatically"). Older cookbook code samples still pass it; the API silently ignores or rejects. This skill OMITS the parameter entirely. It is not exposed as a CLI flag.

### `background=transparent`: supported, but not recommended

gpt-image-2 accepts `background=transparent` and the API will attempt it, but the official cookbook explicitly recommends keeping outputs opaque and running a downstream background-removal step (e.g. `rembg`) for the cleanest transparent assets. The script allows `--background transparent` for compatibility, prints a warning, and requires `output-format png` or `webp`. For best results, prefer `--background opaque` + rembg.

### Size constraints

The API accepts `auto` plus a small set of enum sizes, and also accepts arbitrary `WIDTHxHEIGHT` strings with hard constraints:

- Both edges must be multiples of 16.
- Aspect ratio (long:short) must be ≤ 3:1.
- Total pixels must be in [655,360, 8,294,400].
- Maximum edge length ≤ 3840px.
- Outputs > 2560x1440 are flagged experimental by OpenAI.

The script validates these client-side and prints a precise error before sending the request. Size presets map to safe values:

| Preset | Pixels | Use case |
| --- | --- | --- |
| `square` | 1024x1024 | avatars, product shots |
| `landscape` | 1536x1024 | default landscape |
| `portrait` | 1024x1536 | mobile/portrait |
| `wide` | 1792x1024 | banners, headline covers |
| `2k-landscape` | 2048x1152 | high-res landscape |
| `4k-landscape` | 3840x2160 | experimental 4K |
| `auto` | auto | provider chooses (≈1024x1024 unless context suggests otherwise) |

You can also pass any `WIDTHxHEIGHT` string (e.g. `1536x864`) and the script will validate before sending.

### Output format

GPT image models always return base64-encoded PNG. The script does not expose a `response_format` flag. `output_format` (`png|jpeg|webp`) and `output_compression` (0-100, jpeg/webp only) ARE supported and exposed as CLI flags.

### Error handling

Branch on `error.code` from the OpenAI SDK:

- `429` or 5xx → transient; the script auto-retries with exponential backoff (up to 3 attempts).
- `image_generation_user_error` (400) → user-correctable; the script prints `error.message` and does NOT retry.
- `moderation_blocked` → content moderation; the script prints `error.moderation_details.moderation_stage` (`input|output|unknown`) and category hints, and does NOT retry.

Transient network errors (timeouts, connection resets) also retry. User errors never retry.

### Streaming

Not implemented in this skill. The Image API guide documents `stream=true` + `partial_images` (0-3) as supported, but the model overview page marks "Streaming — Not supported". For CLI workflows the wall-clock wait is acceptable; the script prints elapsed seconds on stderr every ~15s for long generations.

## Prompt augmentation

When `--augment` is on (default), the script can reformat your `--prompt` into a structured spec. The augmentation fields mirror the official cookbook's prompt schema:

```
Use case: <taxonomy slug>
Primary request: <your prompt>
Scene/backdrop: <environment>
Subject: <main subject>
Style/medium: <photo/illustration/3D/etc>
Composition/framing: <wide/close/top-down; placement>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Materials/textures: <surface details>
Text (verbatim): "<exact text>"
Constraints: <must keep/must avoid>
Avoid: <negative constraints>
```

Pass any subset via flags (`--scene`, `--style`, `--text`, etc.). Empty fields are dropped. Disable with `--no-augment` if you want to send your prompt verbatim.

The skill does NOT bundle a domain-specific style library (no watercolor, no guochao, no flat-tech-infographic). For domain-specific style presets, compose this skill with `article-illustration` or write the style text directly into `--style`.

## Verbatim text rendering (gpt-image-2's strongest differentiator)

gpt-image-2 renders in-image text more accurately than any prior model. The cookbook's official rules — apply them to every text-heavy image:

1. Wrap literal text in **quotes or ALL CAPS** in the prompt. Declare typography: font style, size, color, placement.
2. For tricky words (brand names, uncommon spellings), **spell them letter-by-letter** (S-P-E-L-L). Mention "EXACT, verbatim, no extra characters".
3. For small text, dense labels, multi-font layouts, and infographics → **`quality=high`** and a landscape size.
4. For complex multi-section prompts, use **short labeled segments or line breaks** instead of one long paragraph.
5. The model can still struggle with precise placement and clarity; do not promise pixel-perfect text.

CJK-specific typography is not documented in the official cookbook — apply the same verbatim rules and add font-family hints empirically.

## CLI reference

### Common flags

| Flag | Notes |
| --- | --- |
| `--model` | Default `gpt-image-2`. Override for other gateways. |
| `--prompt` / `--prompt-file` | Required for `generate` and `edit`. Mutually exclusive. |
| `--size` | Preset name or `WIDTHxHEIGHT`. See size table. |
| `--quality` | `low|medium|high|auto`. Default `auto`. Use `high` for text-heavy images. |
| `--background` | `transparent|opaque|auto`. Default `auto`. `transparent` is supported but the cookbook recommends opaque + a downstream rembg step; `transparent` requires `output-format png` or `webp`. |
| `--n` | 1-10. Default 1. |
| `--output-format` | `png|jpeg|webp`. Default `png`. |
| `--output-compression` | 0-100. jpeg/webp only. |
| `--moderation` | `auto|low`. Default `auto`. |
| `--out` | Output file path. Default `output/gpt-image-2/output.png`. |
| `--out-dir` | Output directory (used by `generate-batch`). |
| `--force` | Overwrite existing output. |
| `--dry-run` | Print request payload, never call the API. |
| `--no-augment` | Skip prompt augmentation. |
| `--use-case / --scene / --subject / --style / --composition / --lighting / --palette / --materials / --text / --constraints / --negative` | Augmentation fields. |
| `--downscale-max-dim` | If set, also write a copy with the long edge ≤ N pixels. |
| `--downscale-suffix` | Suffix for the downscaled copy. Default `-web`. |

### Edit-only flags

| Flag | Notes |
| --- | --- |
| `--image` | Repeatable. Up to 16 images. Order matters; reference by index in the prompt. |
| `--mask` | Single PNG with alpha channel. |

### generate-batch flags

| Flag | Notes |
| --- | --- |
| `--input` | Path to JSONL. One job per line. |
| `--out-dir` | Required. |
| `--concurrency` | 1-25. Default 5. |
| `--max-attempts` | 1-10. Default 3. |
| `--fail-fast` | Stop the batch on first failure. |

## JSONL job format (generate-batch)

One job per line. Plain string = bare prompt. Object = prompt plus per-job overrides:

```json
{"prompt":"Cavernous hangar interior with a compact shuttle","use_case":"stylized-concept","size":"landscape","quality":"high"}
{"prompt":"Gray wolf in profile, snowy forest","size":"square","negative":"no watermark, no logos"}
```

Per-job keys override the CLI defaults for that job. All augmentation fields, `n`, `size`, `quality`, `background`, `output_format`, `output_compression`, `moderation`, `model`, and an explicit `out` filename (treated as a file under `--out-dir`) are supported.

## Output handling

- Final images: `output/gpt-image-2/` by default.
- Intermediate / scratch files: `tmp/gpt-image-2/`.
- Sibling `*.json` metadata next to each image (prompt, model, size, quality, base URL, timestamp, dry-run flag).
- `--downscale-max-dim` writes an additional downscaled copy (e.g. `cover-web.png` next to `cover.png`). The default suffix is `-web`; override with `--downscale-suffix`.
- Reruns fail on existing files unless `--force`.

## Style presets: scaffolding, not molds

Style presets in `references/styles/` are deliberately split into **structural guardrails** and **inspirational defaults**:

- **Structural guardrails** (keep unless the brief overrides): composition/layout patterns, white-background defaults, hard negative constraints, and use-case-appropriate formats (e.g. numbered steps for architecture diagrams, panels for storyboards).
- **Inspirational defaults** (yield when the brief supplies its own style): palette, mood, medium, and props.

When a user brief is topic-only, the preset provides the full scaffold. When the brief already describes a strong visual concept, drop the inspirational layer and keep only the structural guardrails. See the "Override rule" callout in each style file for the exact boundary.

## References

- `references/image-api.md` — endpoint and parameter quick reference.
- `references/prompting.md` — cookbook-aligned prompting rules and the augmentation schema.
- `references/sample-prompts.md` — copy/paste prompt recipes by use case.
- `references/styles/editorial-pencil-sketch.md` — hand-drawn pencil + watercolor, ideal for AI workflows and editorial illustrations.
- `references/styles/editorial-essay.md` — essays, literary nonfiction, cultural commentary.
- `references/styles/technical-diagram.md` — system architecture, SaaS explainers, developer docs. Includes `technical-diagram-simple` and `technical-diagram-architecture` sub-styles.
- `references/styles/education-science.md` — explainers, how-to guides, textbook-style content.
- `references/styles/visual-narrative.md` — storyboards, comics, film concepts, narrative series.
- `references/openai-official-links.md` — canonical OpenAI docs and cookbook links.
