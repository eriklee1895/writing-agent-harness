---
name: article-illustration
description: Generate article illustrations in multiple styles — watercolor art, flat illustrations, technical diagrams, infographics, and more. Use when agent needs covers, inset illustrations, atmospheric dividers, blog banners, or technical diagrams for articles. Supports text-only generation, reference-image-plus-text style guidance, and prompt-only dry-run review.
---

# Article Illustration

Use this skill to create illustrations for articles — covers, inset imagery, dividers, banners, and diagrams.

## Provider routing and brief priority

This skill coordinates the visual brief, layout and provenance. For live raster generation, use the user's selected media skill: `imagegen`, `gpt-image-api`, `seedream-image-gen` or `openrouter-image`. If no provider has been selected for the current task, ask once, following AGENTS.md. An explicit selection persists within the task; do not ask again or override it with the legacy script below.

For product or Agent engineering articles, establish the product identifiers, key components and relationships before the first cover prompt. Include recognizable logos when requested and meaningful English labels when they help explain the subject. Match the visual medium to the article's technical content and the author's brief; atmosphere alone does not establish a technical topic. Keep a cover's conceptual connections consistent with the article, especially task handoff versus credential delivery.

Channel ratios are constraints, not provider defaults. Prefer native target-ratio generation or background extension that preserves the approved content. The legacy `wechat-cover-hd` crop below can cut off logos and labels; it is not the default adaptation strategy.

## Quick workflow

1. Identify what you need:
   - WeChat cover (公众号头条封面, 2.35:1)
   - Body inset illustration (for literary essays or tech articles)
   - Atmospheric section divider
   - Blog banner / hero
   - Technical diagram (architecture, process, knowledge card)
2. Pick a style profile:
   - `auto` (default): choose from the brief instead of forcing a house style
   - `editorial-atmospheric`: textured contemporary editorial illustration, good for essays and cultural observation
   - `modern-guochao-editorial`: restrained modern guochao / Chinese cultural editorial style
   - `cinematic-editorial`: film-still inspired editorial image with grounded light and scene detail
   - `watercolor-illustration`: fine-art watercolor, use only when the article truly wants a soft painterly mood
   - `flat-illustration`: editorial flat illustration, soft look
   - `sketchnote`: hand-drawn notebook feel
   - `flat-tech-infographic`: technical infographic with clean modules, arrows, bilingual labels
   - `soft-tech-diagram`: subtle dashed containers, light academic style
   - `repo-architecture-clean`: crisp codebase and ownership diagrams
3. Pick a size:
   - `wechat-cover-hd` for WeChat headline covers (auto-crops to 1080x460, 2.35:1)
   - `portrait-hd` for mobile-first inset illustrations
   - `blog-banner` for blog hero images
   - `doc-hd` / `doc-2k` / `doc-4k` for landscape document illustrations
   - `auto` for provider-chosen default
4. If the user supplied reference images, treat them as style guidance only.
5. If the user wants to inspect the prompt first, use `--dry-run`.
6. For live generation, follow the selected media skill. Use the bundled legacy script only when that CLI path is explicitly requested and its provider/model compatibility has been checked.

## Legacy CLI script (explicit fallback only)

Use `uv run` for Python scripts:

```bash
# Literary essay illustration, auto style selection
uv run scripts/generate_article_illustration.py \
  --title "Snowy Window Scene" \
  --brief "A body inset illustration of snow falling outside a warm-lit classroom window..." \
  --size wechat-cover-hd

# Technical diagram
uv run scripts/generate_article_illustration.py \
  --title "RAG Pipeline Overview" \
  --brief "A technical infographic showing ingestion, chunking, embedding, retrieval..." \
  --style-profile flat-tech-infographic \
  --language zh-en \
  --size doc-hd
```

Use `--mode reference+text --reference-image <path>` when the new image should follow the style of one or more reference images.

Use `--dry-run` when you want the exact prompt and parameters without calling the API.

Default output settings:
- `--style-profile auto` (default; resolves from the brief)
- `--language zh` (default; use `zh-en` for bilingual labels)
- `--size auto` for best compatibility with GPT image providers
- `--quality auto` for high-fidelity default behavior

Size presets:
- `wechat-cover-hd` (1792x1024, auto-crops to 1080x460 2.35:1) — WeChat headline cover
- `portrait-hd` (1024x1536) — mobile-body inset
- `blog-banner` (2048x1152) — blog hero / desktop banner
- `9:16` (1024x1792) — full phone portrait
- `doc-hd` (1536x1024) — landscape document
- `doc-2k` (2048x1152) — high-res landscape
- `doc-4k` (3840x2160) — 4K landscape
- `auto` — provider-chosen default

## Authentication

- Read `OPENAI_API_KEY` from the current shell first.
- Read `OPENAI_BASE_URL` from the current shell second.
- If `OPENAI_API_KEY` is missing for a live generation run, prompt temporarily in an interactive shell or tell the user to export the environment variable.
- Do not write credentials to disk.

## Model selection

Use the selected media skill's current model contract. Do not infer the model identity of built-in `imagegen` from the image quality or a user-mentioned model version. The legacy script's historical model names and size presets require compatibility checks before use; this documentation update does not validate that CLI against current providers.

## References

- Read `references/style-profiles.md` when selecting or explaining styles.
- Read `references/prompt-patterns.md` when the requested illustration type needs prompt refinement.
- Browse `references/styles/` for ready-to-use style presets (`editorial-pencil-sketch`, `hand-drawn-tech-editorial`, `technical-diagram`, and more). Treat them as creative references, not mandatory templates — adapt or ignore them based on the brief.
- Read `references/openai-image-workflow.md` when debugging auth, request modes, or output behavior.
- Read `references/openai-official-links.md` when you need the official OpenAI docs for GPT Image, Images API, or Python examples.
