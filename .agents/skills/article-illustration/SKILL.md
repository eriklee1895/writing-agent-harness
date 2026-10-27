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

**生成器选择优先于旧脚本入口**：本 skill 可用于规划图片角色、信息结构与提示词；实际生图遵循任务中用户指定的 user-level media skill。用户选定内置 `imagegen` 时使用内置工具，不因下方历史脚本示例改走 API。未指定生成器时先询问；同一篇文章已确认的选型可继续沿用。不要把脚本中的模型或尺寸默认值作为当前模型能力的事实来源。

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
   - `prepare_cover.py`：Blog 母版派生微信 1080×460、首页或其他渠道尺寸；先验收 crop/pad 候选。
   - `portrait-hd` for mobile-first inset illustrations
   - `blog-banner` for blog hero images
   - `doc-hd` / `doc-2k` / `doc-4k` for landscape document illustrations
   - `auto` for provider-chosen default
4. If the user supplied reference images, treat them as style guidance only.
5. If the user wants to inspect the prompt first, use `--dry-run`.
6. For live generation, follow the selected media skill. Use the bundled legacy script only when that CLI path is explicitly requested and its provider/model compatibility has been checked.

## Required cover family and derive-first workflow

每篇进入 Blog / 微信等渠道 handoff 的文章都必须有经实际尺寸验收的 Cover。通用模板、系列母版、授权图片与定制生成图都可以满足；不得把“每篇必须独立 AI 生图”当成规则。正文插图仍按需制作。

默认保留一个已批准的视觉母版，再按渠道派生：

1. 先用 focal crop、contain/pad 或一个原生比例候选建立快速基线，并在真实 Blog 卡片、微信小图等目标尺寸比较。**基线只用于对照，不因它成本更低就自动中选。**
2. 如果主要是文字层级或标签布局不合适，可共享背景与结构化内容重新排版；如果原生再生能获得更好的主体、层级和小图效果，就直接走再生，不设置“必须先接受派生”的成本门槛。
3. 再生时沿用原 Prompt、目标比例和本次失败的具体修正，保持同一视觉体系。允许围绕实际对比做多轮优化，直到目标尺寸下效果最佳；每轮都重新验收，不把更换尺寸当作质量保证。
4. `cover` 是 Blog hero / OG 的批准母版；微信使用实际效果最佳的批准版本；`homeCover` 只处理 Blog 首页例外，不能替代 Blog `cover` 或微信 Cover。

使用 `scripts/prepare_cover.py` 做确定性 raster 派生。它只创建候选并把 `visual_review` 记为 `pending`，不会自动宣称构图合格。以下命令从仓库根目录运行，输入、输出和 manifest 都以文章目录为基准：

```bash
uv run .agents/skills/article-illustration/scripts/prepare_cover.py \
  --input content/origin/YYYY-MM-DD-<slug>/assets/cover-master.png \
  --output content/origin/YYYY-MM-DD-<slug>/assets/cover-wechat.png \
  --size 1080x460 \
  --mode crop \
  --focus-x 0.5 --focus-y 0.5 \
  --role wechat_cover --channel wechat \
  --manifest content/origin/YYYY-MM-DD-<slug>/assets/manifest.json \
  --json
```

- `--mode crop` 保持比例裁剪；`--mode pad` 保留完整画面并补边。
- 输出已存在时需显式 `--force`；任何输出或 manifest 软链接都会被拒绝，避免覆盖 closeout 归档。强制重新派生会清除旧审批、发布和 regeneration 元数据，只保留安全备注；同名但不同目录的资产按 manifest 相对路径分别记录 lineage。
- 裁剪派生在 manifest 记录 `derived_from` 与 `derivation`。重新生成的版本记录原/修正 Prompt、参考图与再生原因，不能伪装成像素裁剪。
- 预览后把候选标为 used / rejected，并记录实际检查尺寸与理由；被拒绝的候选不要进入渠道或最终归档。
- 旧的 `wechat-cover-hd` 自动 center-crop 只保留为 legacy fallback，不再是默认渠道适配路径。

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
