---
name: article-illustration
description: Generate article illustrations in multiple styles — watercolor art, flat illustrations, technical diagrams, infographics, and more. Use when agent needs covers, inset illustrations, atmospheric dividers, blog banners, or technical diagrams for articles. Supports text-only generation, reference-image-plus-text style guidance, and prompt-only dry-run review.
---

# Article Illustration

Use this skill to create illustrations for articles — covers, inset imagery, dividers, banners, and diagrams.

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
6. For live generation, run the bundled script with `uv run`.

## Script

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

- Use `gpt-image-2` for official OpenAI and for `https://aihubmix.com/v1`.
- Use `openai/gpt-image-2` for `https://api.ofox.io/v1`.
- Default back to `gpt-image-2` unless a provider requires a namespaced model name.

## References

- Read `references/style-profiles.md` when selecting or explaining styles.
- Read `references/prompt-patterns.md` when the requested illustration type needs prompt refinement.
- Browse `references/styles/` for ready-to-use style presets (`editorial-pencil-sketch`, `hand-drawn-tech-editorial`, `technical-diagram`, and more). Treat them as creative references, not mandatory templates — adapt or ignore them based on the brief.
- Read `references/openai-image-workflow.md` when debugging auth, request modes, or output behavior.
- Read `references/openai-official-links.md` when you need the official OpenAI docs for GPT Image, Images API, or Python examples.
