---
name: seedream-image-gen
description: ByteDance Seedream 5.0 Pro/Lite image model. Generate and edit images: text-to-image, **marker-based local editing (no mask/Photoshop — draw a colored rectangle on the image and describe the change in natural language to swap titles/objects/materials or add/remove elements, chain multi-region edits)**, outpaint to extend canvas, and batch generation. Production-grade Chinese/English/mixed-language text rendering for graphic design (posters, covers, banners, logos, labels, slogans), strong 国潮/水墨/24节气 Chinese aesthetic fluency, product/e-commerce photography, 3D/icons/isometric illustrations, and editorial infographics (hero photo + frosted-glass data cards in National Geographic / Bloomberg data-journalism style). Use this whenever you need to create or edit visuals with embedded text, Chinese-style art (节气/节日/水墨/新中式/国潮), product shots, editorial or marketing imagery, data explainers / infographic posters, character-consistent series, or modify existing images with title/object swaps and local edits.
---

# seedream-image-gen

ByteDance Seedream 5.0 image generation via Volcengine Ark API. Single-file Python CLI (PEP 723, `uv run` directly). Supports text-to-image, image-to-image / style transfer, **marker-based local editing** (draw a colored box and describe the change in natural language, no mask/bbox/Photoshop), outpaint (extend canvas), and batch JSONL generation.

## Models

| Model | ID | `--model` alias | Use for |
|---|---|---|---|
| **Seedream 5.0 Pro** (default) | `doubao-seedream-5-0-pro-260628` | `pro` | Everything — text, marker edits, Chinese aesthetics, product shots. Released 2026-06-28. |
| Seedream 5.0 Lite | `doubao-seedream-5-0-260128` | `lite` | Fast no-text sketches, >4 MP output, web-search / sequential. Weaker text, no marker edits — see [lite-quickref.md](references/lite-quickref.md). |

This skill targets only the 5.0 family; it does not support Seedream 4.x / 3.x / 2.x (weaker text, no marker editing).

- **Endpoint**: `POST https://ark.cn-beijing.volces.com/api/v3/images/generations` (text-to-image and editing share one endpoint; there is no separate `/edits`)
- **Auth**: `ARK_API_KEY` environment variable or `.env` file in the working directory

## Quick Workflow

### Generate a new image (default: Pro / 2K / PNG / url-based download)

```bash
uv run scripts/seedream_image_gen.py generate \
  --prompt "A minimalist movie poster for a sci-fi film about deep-sea AI, dark teal background, large white sans-serif title 'ABYSS PROTOCOL' at the top centered, one-line orange tagline below, one glowing jellyfish silhouette bottom-left, cinematic"
```

### Edit an image (swap title / object / material, or extend canvas)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image poster.png \
  --marker-rect "5%,6%,90%,25%" \
  --prompt "Replace the title in the red box with '新标题', matching the existing font, size, color, and alignment"
```

The CLI draws a semi-transparent colored rectangle on the reference image with Pillow, appends a "remove the markers" instruction to the prompt, and sends the annotated image — you never need to handle masks yourself.

> Marker editing is Pro-only and is the main thing that differentiates Seedream from gpt-image / Midjourney / Flux. For the full protocol (multi-color multi-region, chain editing, threshold table, failure modes, 8 copy-paste recipes), see **[references/marker-editing.md](references/marker-editing.md)**.

### Batch generation (JSONL)

```bash
uv run scripts/seedream_image_gen.py generate-batch \
  --input jobs.jsonl --concurrency 3
```

Each line of the JSONL is either a bare prompt string or a JSON object like `{"prompt": "...", "size": "2K", ...}`.

## When to use

**Core strengths of Seedream 5.0 Pro** (this is where you will get the most leverage over other image models):

- **Graphics with embedded text** — Chinese/English/mixed-language posters, covers, banners, social graphics, logos, circular badges, package labels, and slogans. Pro renders large headlines, short labels, and circular/arc text reliably at 2K.
- **Local edits to existing graphics** — title swaps, object replacement, material changes, adding or removing elements, using the marker-based colored-box workflow. This works first-try for common swaps without Photoshop-style precision work.
- **Chinese / East-Asian aesthetic imagery** — 国潮 (neo-Chinese), 24 节气 (solar terms), traditional festivals (Spring Festival, Mid-Autumn, Dragon Boat), ink-wash painting (水墨), gongbi fine brushwork, new-Chinese lifestyle editorial, Chinese architecture and food. ByteDance's Chinese-trained model maps these concepts far more accurately than English-native models.
- **Product / e-commerce / food photography** — white-background product shots, lifestyle scenes, flat-lays, food photography, cosmetics/3C/apparel lookbooks, sale-event banners — well-mapped vocabulary from ad-training data, cheap enough to iterate.
- **Character-consistent multi-scene series** — pass one or more reference images of a character and generate them across scenes while retaining facial features (articles, storybooks, social content, comic panels).
- **Cost-sensitive batch work** — ~¥0.30-0.60/image on Pro, ~¥0.22 on Lite; batch concurrency of 3-5 is cheap.

**Commodity capabilities** that work well but aren't unique to this model:
- Style transfer (Van Gogh, Ghibli, cyberpunk, ukiyo-e, etc.) via image-to-image
- Outpaint (extend canvas) on any side
- Concept art, editorial illustration, abstract backgrounds
- Apparel prints, stickers, tattoo designs, album art, desktop wallpapers, presentation slide backgrounds

## When to pick a different approach

- **Dense small text, long body copy, tables, sheet music, math equations, chess diagrams, long-form handwritten text** — Pro's large-text is strong but long-form/symbolic content still fails. Post-add in Figma/HTML/PS, or use a text-layout pipeline rather than image-gen.
- **Engineering multi-view drawings, precise mechanical diagrams** — perspective isn't CAD-accurate; use actual CAD tools.
- **Pixel-perfect UI screenshots** — render in a browser, don't generate.
- **Accurate likeness of named celebrities / public figures** — faces blend and hallucinate; use stock or a shoot.
- **ControlNet-style control** (depth maps, pose skeletons, line-art tracing) — the public API doesn't expose these. Use a local image-generation stack with ControlNet support if required.
- **High-end jewelry / faceted gemstones** — diamond fire and complex refractions come out muddy; photograph or 3D-render.
- **Long-form calligraphy in the style of specific famous calligraphers** (《兰亭序》precise copies, etc.) — the model approximates a style but cannot reproduce a specific work stroke-for-stroke.

## Choosing Pro vs Lite

Pro is the default for a reason: it renders text reliably, supports marker edits, produces the Chinese-aesthetic and product-photography looks, and latency (~95s @ 2K) is nearly identical to Lite — so there is little reason to switch unless you have a specific constraint.

Switch to Lite with `--model lite` only when you need: fast no-text concept sketches, >4 MP resolution, `--web-search`/`--sequential` (Lite-only params), or large cheap batches of non-text visuals. Full decision detail, pixel-range table, Lite-only flags, and the "what Lite doesn't have" list (no marker edit, weaker text, unverified prompt-technique transfer) are in **[references/lite-quickref.md](references/lite-quickref.md)** — read it before reaching for `--model lite`, not after.

Print the full capability matrix (max refs, optimize modes, etc.):
`uv run scripts/seedream_image_gen.py list-models`

## Size Shortcuts

| Flag | Resolution | Aspect | Typical uses |
|---|---|---|---|
| (default) | 2K (model-picked, ~1536×2048) | 3:4-ish | Posters, social posts, general workhorse |
| `--square` | Pro: 1024×1024 / Lite: 2048×2048 | 1:1 | Social posts, product main images, logos |
| `--wide` (alias `--wechat-header`) | 1792×1024 (Pro-only) | 16:9 | Banners, headers, hero images, YouTube/B站/博客/公众号 covers |
| `--portrait` | Pro: 1536×2048 / Lite: 2048×2732 | 3:4 | Posters, magazine covers, 小红书/Instagram stories |
| `--landscape` | Pro: 2048×1152 / Lite: 2732×1536 | 16:9 | Wallpapers, presentation slides, cinematic frames |
| `--size 1K/2K/3K/4K` | preset + prompt aspect | model-judged, per official reference table | Bare preset: describe the aspect ratio in your prompt and the model outputs the reference pixels for that ratio at the chosen tier (1K/2K Pro, 2K/3K/4K Lite; **arbitrary ratios in [1/16,16] supported**, the table only lists common ones) — see the "Size：两种指定方式" table in [api-reference.md](references/api-reference.md) |
| `--size WxH` | custom (e.g. `2560x1440`) | your choice | Exact resolution; validated against model pixel range |

Size and aspect ratio can also be described in natural language inside the prompt (e.g. "竖版 3:4 海报", "手机壁纸 9:16", "16:9 横版", "方形头像") — the model will pick a reasonable size near its default (2K). Prefer the explicit `--size` / shortcut flags when you need deterministic dimensions (platform uploads, print specs, matching an existing layout); use in-prompt sizing when you are describing a feel and the exact pixel count does not matter.

Valid custom-WxH bounds: **Pro** 0.9 MP – 4.6 MP (default 1024×1024) with aspect ratio ∈ [1/16, 16]; **Lite** 3.7 MP – 16 MP (default 2048×2048; see [lite-quickref.md](references/lite-quickref.md) for the full floor/ceiling table — note Lite categorically cannot do 1K/1024²/1792×1024). The bound is on total pixels (W×H), not per-side. The client rejects out-of-range sizes before spending an API call. For common platform/destination sizes (e-commerce mains, social posts, stories, video covers, wallpapers), see the [Common Use-Case Size Reference](references/api-reference.md#common-use-case-size-reference) in the API reference.

## Text rendering (Pro)

Seedream 5.0 Pro renders Chinese and English text well enough for production graphics: large headlines, subheads, slogans, circular-badge logos, and short card labels all work first-try.

**Text prompt formula**

```
[background & layout] + ["text content in quotes, verbatim"] +
[font family / weight / size as fraction of canvas / color / alignment / position] +
[decorative elements] + [style + size]
```

**Text reliability @ 2K Pro**

| Content type | Reliable? | Notes |
|---|---|---|
| Large Chinese headline (≤12 chars) | ✅ Perfect | One-shot, sharp, correct |
| Large English headline (≤4 words) | ✅ Perfect | Specify Title Case or ALL CAPS |
| Chinese+English mixed headline | ✅ Good | Specify "中英字号视觉平衡" |
| Circular / arc logo text | ✅ Good | Say "沿圆环顶部弧形排列" / "arched along top of circle" |
| Card/diagram labels (2-4 chars/words) | ✅ Good | 2K required; specify sans-serif |
| 2-4 line subtitle / slogan | ⚠️ Usually OK | Proofread; retry once if errors |
| Long body text (>8 lines) | ❌ Don't rely on it | Post-add in Figma/HTML/PS |
| Math / equations / sheet music / chess diagrams | ❌ Unreliable | Symbolic reasoning fails |
| Cursive/calligraphy long text | ❌ Strokes blur | Short 1-2 char calligraphy is fine |
| Named signatures / celebrity handwriting | ❌ Hallucinated | Don't try |
| Small body text (< 1/30 of canvas height) | ❌ Pixel limit | Use larger text or post-add |

Specify font families by description, **not** by filename — the model does not know names like "Source Han Serif" or "Helvetica Neue". Use descriptive terms (`粗黑无衬线` / `宋体` / `手写毛笔字`; `bold sans-serif` / `serif` / `script`); the full Chinese/English font-description vocabulary is in [prompt-engineering.md](references/prompt-engineering.md).

Specify size as a fraction of the canvas (e.g. "字号占画面高度 1/6") and position relatively ("顶部居中", "top-left aligned"); don't write "72pt".

**Always default to 2K for text work.** Text is muddy at 1K, and Lite produces frequent character errors. The `--wide` / `--wechat-header` shortcut produces 1792×1024 (≈1.84 MP) which is large enough for Pro-only headline graphics.

**Prompt language** — Seedream is Chinese-native. Write **Chinese** for Chinese subjects/culture/text (节气/水墨/中式建筑/中文大字/中餐/国风), **English** for Latin-script typography and Western brands, and keep photography/lighting/render jargon (bokeh, rim light, impasto, chiaroscuro) as **English loanwords** inside either. The sweet spot is a Chinese narrative peppered with English technical terms; don't force English on Chinese content. Full decision table in [prompt-engineering.md](references/prompt-engineering.md).

For extended guidance see [references/prompt-engineering.md](references/prompt-engineering.md) (formula, language choice, **anti-pattern watchlist** with concrete fix-phrases, and advanced community-validated tricks) and [references/styles/text-poster.md](references/styles/text-poster.md) (6 copy-paste-ready recipes: tech-blog cover, magazine cover, wide banner header, infographic, sale banner, circular-badge logo).

**Four common traps that silently ruin output** (full list in prompt-engineering.md):
1. When generating 9:16/phone/stories content, **always** add `no UI elements, no phone frame, no status bar, pure photo/illustration content` ("无UI界面、无手机边框、无状态栏、纯画面") — the word "手机/phone/9:16" otherwise hallucinates a fake phone chrome around the image. Lock aspect ratio via `--size WxH`, not prose.
2. Vertical English magazine titles need explicit structure **and** position-locking: "one English word per horizontal line, stacked top-to-bottom, in the left 1/3 margin (not overlapping the portrait)" ("每个英文单词独占一行水平书写、从上到下排列在左侧留白区域、不覆盖到人物/产品身上"). Writing "竖排英文" alone produces overlaid/duplicated letters; break words longer than 6 letters (e.g. INTEL-LIGENCE) to avoid overflow.
3. Products with smooth surfaces (bottles, headphones, lipstick tubes, mugs, boxes) almost always get a fake gibberish brand name — explicitly add `no branding text, no labels, no logos, clean unbranded surface` ("瓶身/表面无品牌文字、无标签、无logo、纯净无印刷") unless you want branding.
4. If you want **blank negative space for later text overlay** (e.g. hero banner left 60% empty), say so literally: `left 60% is pure gradient background, NO text, NO logos, NO watermarks, clean empty area for later title overlay` ("左侧留白为纯背景、无任何文字、无logo、无水印，供后期叠加标题"). Writing "留白放标题" makes the model hallucinate fake characters in the blank.

## Marker-based local editing (Pro)

Pro has no mask or bbox parameters. Local edits use a **visual marker convention**: draw a semi-transparent colored rectangle on the reference image, describe the change in natural language, and the model recognizes the marker, performs the edit, and removes the marker in the output. The CLI automates both drawing and marker cleanup — you only pass `--marker-rect`.

**Why this beats mask/bbox APIs**

- 🎯 **No coordinate precision needed** — draw a rough rectangle; the model identifies the object boundary
- 🎨 **Multi-region edits via colors** — "red box: swap title, blue box: add a cat" in a single call
- 🗣️ **Natural language is the interface** — no mask bitmaps, no bbox JSON arrays, no image-editor knowledge required
- 🧹 **Auto cleanup** — markers are removed by the model (the CLI appends the cleanup instruction)
- 🔒 **Pixels outside the marked region are preserved** — tested on sofa→navy+add-cat and title-swap: window, plants, lighting, surrounding graphics all stayed intact

One caveat: rectangles are supported natively; arbitrary scribbles require pre-drawing with Pillow or other tooling.

`--marker-rect X,Y,W,H` can be passed multiple times and supports two formats:
- Pixels: `100,150,800,300` (top-left X,Y + width/height)
- Percent: `10%,15%,60%,20%` (more robust across image sizes, recommended)

Optional parameters:
- `--marker-color #ff0000` marker color (use distinct colors for multiple regions, then say "红框 X，蓝框 Y" in the prompt)
- `--marker-alpha 80` fill transparency (0-255, default 80)
- `--marker-stroke 3` outline stroke width (px, default 3)
- `--no-marker-cleanup-prompt` disable the auto-appended "remove the markers" suffix (advanced)
- `--outpaint <dir:pixels>` canvas extension (left/right/top/bottom, can be passed multiple times)

**Typical edit-prompt structure**

```
[Color] box: replace [original object] with [new object + material + color + lighting],
keeping [perspective / font / size / shadow / position] unchanged,
pixels outside the box remain exactly as-is.
```

Validated scenarios: headline swap on existing posters, sofa material change + adding an animal, metal sculpture → transparent glass, multi-region multi-color simultaneous edits. For detailed protocol, failure thresholds (rect <8% ignored / >70% full-regen), annotated-preview workflow, 8 copy-paste recipes (title swap / product recolor / add element / remove / multi-color / chain edit / outpaint+marker / vertical English), and anti-patterns, see **[references/marker-editing.md](references/marker-editing.md)**. For multi-reference identity/fusion workflows (face+outfit+palette), see Formula 6 in **[references/prompt-engineering.md](references/prompt-engineering.md)**.

## Honest Capability Scorecard (2026-07-10, 200+ test images)

Every row below is empirically tested, not inferred from marketing copy. "✅ Production" = reliable with the documented recipe; "⚠️ Best-effort" = works but has a known failure mode; "❌ Not available" = the public Ark API does not expose this.

| Capability | Verdict | Score | Notes |
|---|---|---|---|
| 风格迁移 (style transfer) | ✅ Production | 9.5/10 top styles | Commitment-language formula is the lever. [style-transfer.md](references/styles/style-transfer.md) |
| 文字渲染 (text rendering) | ✅ Production | 9-10/10 structured, 2/10 per-cell-unique | 30-cell rule for tables/grids. [text-deep.md](references/text-deep.md) |
| 多参考图融合 (multi-ref fusion) | ✅ Production | 8.5-9/10 (2-3 refs) | Sweet spot 2-3 refs; role-assignment required. [prompt-engineering.md 公式6](references/prompt-engineering.md) |
| 复杂信息可视化 (infographic) | ✅ Production | 51-53/60 | Cross-subject transferable recipe. [editorial-infographic.md](references/styles/editorial-infographic.md) |
| 圈选/点选局部修改 (marker color/material/makeup/feature) | ✅ Production | 9-9.5/10 | Hex ±1 shade drift; single-feature precision confirmed (heterochromia test). [marker-editing.md Recipe 9](references/marker-editing.md) |
| 草图渲染 (sketch-to-render) | ✅ Production | 9-9.5/10 | Confirmed across photoreal + flat-illustration targets. [marker-editing.md](references/marker-editing.md) |
| 多图融合抠像 (multi-image extraction compositing) | ✅ Production | 8.5-9/10 (2 people) | Unified lighting genuinely works. [marker-editing.md Recipe 12](references/marker-editing.md) |
| 区域重绘/擦除修复 (inpaint/erase) | ✅ Production (replaceable object) / ❌ (compositional anchor object) | 9-9.5/10 vs 0/10 | **Refined 2026-07-10**: not purely day/night-dependent — within the SAME daytime matte scene, a parked car in a row of similar cars erased at 9.5/10 while a bicycle leaning on a lamppost (compositional focal point) failed at 0/10 with an identically well-formed marker+prompt. The real variable is object salience: replaceable/interchangeable objects erase reliably, visual-anchor objects resist (same underlying mechanism as hero-object/primary-light-source failures). Night+reflective+neon scenes remain a separate, harder failure mode (1-4/10). [marker-editing.md Recipe 10](references/marker-editing.md) |
| 坐标精准定位 + 数学演算续写 | ⚠️ Best-effort | 9.5/10 for style-continuation | Model renders your given answer in matching handwriting; **it does not solve math itself** — you supply the correct derivation. [marker-editing.md Recipe 11](references/marker-editing.md) |
| **智能图层分离 (auto layer separation → transparent PNG layers)** | ❌ **Not available** | n/a | **Not exposed on the public Ark API** — only in ByteDance's internal demo UI. No `mask`/`layers`/`bbox` params exist. Marker edit can approximate "change one region" but never outputs N independent alpha-channel layers. [api-reference.md](references/api-reference.md) |
| 物理光影全真模拟 | ✅ Production | 8.8→9/10 | Rotational wheel-blur solved with explicit anti-detail prompting (was thought to be a hard fail). [photorealism.md](references/styles/photorealism.md) |
| 人像肌理天花板 | ✅ Production (was ⚠️) | 9.5/10 raw skin | **Overturned original ~80% finding.** The beauty-filter default is a prompt gap, not a ceiling — aggressive texture enumeration (pores/vellus/redness/blemishes/oil) + concrete reference analogy ("dermatology reference photo, not a cosmetics ad") + stacked negations gets raw dermatology-grade skin on the hardest cases (young E-Asian woman + young man), reproducible. Recipe in [photorealism.md](references/styles/photorealism.md). |
| 10 人以上大合照不畸形 | ✅ Production (was ❌) | 9/10 at 10 people | **Overturned original finding.** Explicit per-person enumeration (ethnicity+age+hair+clothing spelled out for every person) breaks the face-cloning cliff. Generic "10 diverse people" prompts still fail at 4.5/10. [photorealism.md](references/styles/photorealism.md) |
| 双风格自由切换 (photo ↔ CGI) | ✅ Production | 9-9.5/10 | Pure prompt-keyword toggle, no mode switch needed. [photorealism.md](references/styles/photorealism.md) |
| 原生多语种生成 (10+ languages) | ✅ Production (Latin/CJK/Korean) / ⚠️ (Thai/Arabic) | 9-10/10 vs 5-8.7/10 | Thai tonal diacritics are the softest layer. [multilingual.md](references/multilingual.md) |
| 多语言同屏排版 | ✅ Production | 9-9.5/10 | 3-4 scripts per-panel layout; same-line mixing risks diacritic bleed. [multilingual.md](references/multilingual.md) |
| 文字鬼画符根治 (garbled text elimination) | ✅ Mostly solved | varies by density | Structured/repeated labels 9-10/10; per-cell-unique content collapses past 30 cells. [text-deep.md](references/text-deep.md) |
| 结构纠错 (anatomy/architecture/mechanical perspective) | ✅ Production | 8.5-9.5/10 dedicated tests | Dynamic dance pose (5-finger accuracy, correct joint bends) 9.5/10; two-point architectural perspective (converging grid lines, no warping) 9/10; watch-gear mechanical mesh (correct tooth interlock, plausible ratios) 8.5/10. Hands under complex multi-object interaction (chopsticks, group ≥4) remain the softest sub-case. No pre-Pro baseline exists to quantify the marketed "90% error reduction," but absolute quality on these three dedicated single-image tests is high. |
| 超高分辨率 (2.36 MP) | ✅ Production | verified | Pro max ~4.6MP (总像素 4,624,220); Lite goes to 16MP. See [Size Shortcuts](#size-shortcuts) and [api-reference.md](references/api-reference.md). |

**The one confirmed gap**: 智能图层分离 (auto transparent-PNG layer separation) is a real capability shown in ByteDance's marketing/demo UI but **not present on the public Ark API this skill calls**. Every other originally-requested killer capability has a working recipe, including three (10-person groups, wheel motion blur, defeating the beauty-filter for raw skin) that earlier testing had marked as hard model ceilings — all three turned out to be prompt-engineering gaps, crackable with the same pattern: **aggressive explicit enumeration + a concrete reference analogy + stacked negations**. When a Seedream output looks like a generic/smoothed default, suspect the prompt before concluding it's a model limit.

## Examples

> All examples default to Pro / 2K / PNG, downloaded from the server's returned URL. `--dry-run` prints the request body without calling the API, so you can sanity-check before spending money.

### 1. Sci-fi movie poster (3:4)

```bash
uv run scripts/seedream_image_gen.py generate --portrait \
  --prompt "Minimalist sci-fi movie poster, 3:4 vertical, deep navy-to-black gradient background, one glowing bioluminescent jellyfish floating bottom-left, large white bold sans-serif title 'ABYSS PROTOCOL' centered at top taking 1/6 of the image height, one-line smaller orange sans-serif tagline 'The deep remembers' below the title, tiny white credit block at bottom, cinematic teal-orange palette, clean editorial print quality"
```

### 2. Wide banner / cover header (Pro-only shortcut)

```bash
uv run scripts/seedream_image_gen.py generate --wide \
  --prompt "Wide 16:9 banner, left 60% white-to-light-gray gradient, large bold black sans-serif title 'Claude 5 深度解析' left-aligned taking 1/4 of the image height on the left side, one-line smaller gray subtitle 'Agentic Coding 的下一个十年' below it, right 40% deep-blue abstract particle/light-beam decoration, sharp clean editorial feel"
```

(The `--wechat-header` alias produces the same size and is kept for backward compatibility.)

### 3. Bilingual infographic

```bash
uv run scripts/seedream_image_gen.py generate \
  --size 1792x1024 \
  --prompt "Horizontal tech infographic poster, white background, top-center large deep-blue bold sans-serif Chinese title 'AI 编程三阶段', smaller English subtitle 'Three Eras of AI Coding' directly below, middle section has three horizontally arranged blue rounded-rectangle cards, each card has a centered white short label '补全' '对话' '自主' respectively, thin gray arrows connecting the cards, flat vector style"
```

### 4. Circular badge logo

```bash
uv run scripts/seedream_image_gen.py generate --square \
  --prompt "Circular badge logo, dark-navy fill + double-thin gold outer ring, white bold serif English letters arched along the top of the circle 'SEEDREAM PRO', center has two red seal-script Chinese characters '豆包', gold laurel-wreath decoration, pure white background, flat vector style"
```

### 5. Sale / e-commerce banner (16:9)

```bash
uv run scripts/seedream_image_gen.py generate \
  --size 1792x1024 --no-negative-prompt \
  --prompt "E-commerce mid-year sale banner 16:9, warm-red gradient background with golden particle light effects, centered large gold bold-Song Chinese title '年中大促' taking 1/3 of the image height, smaller white sans-serif subtitle '全场 5 折起' below it, gold ribbons / gift boxes / gold coins as decoration, festive atmosphere"
```

### 6. Text swap (edit + marker — the highest-frequency edit)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image my-poster.png \
  --marker-rect "5%,6%,90%,25%" \
  --prompt "Replace the title in the red box with 'GPT-Image 2 全面解析', keeping the bold sans-serif font, point size, and center alignment; the subtitle and blue graphic below remain unchanged; pixels outside the box stay exactly as-is"
```

### 7. Object / material swap (edit + marker)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image living-room.png \
  --marker-rect "10%,45%,80%,40%" \
  --prompt "Replace the beige fabric three-seater sofa in the red box with a navy-blue velvet three-seater sofa with thin brass legs; the velvet has a soft sheen; perspective and sunlight direction unchanged; candles and books on the coffee table unchanged; pixels outside the box unchanged"
```

### 8. Style transfer (image-to-image)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image portrait.png \
  --prompt "Repaint this portrait in Van Gogh oil-painting style, thick impasto brushwork, swirling background, strong yellow-blue contrast; retain the subject's facial features but repaint everything in visible brushstrokes"
```

### 9. Same character, new scene (reference consistency)

```bash
uv run scripts/seedream_image_gen.py generate \
  --size 1792x1024 \
  --reference-image portrait-front.png \
  --prompt "Using the young East-Asian woman in the reference image (round glasses, short bob with blunt bangs, round face, cream sweater), place her on a rainy night at a Shibuya crossing in Tokyo wearing a black trench coat, neon blue-purple light on her face, wet ground reflecting neon, shallow depth of field, cinematic, 16:9"
```

### 10. Outpaint (1:1 → 16:9)

```bash
uv run scripts/seedream_image_gen.py edit \
  --reference-image square-poster.png \
  --outpaint left:400 --outpaint right:400 \
  --prompt "Extend this 1:1 poster into a 16:9 horizontal image, naturally filling the new canvas while matching the existing style, lighting, and color palette"
```

(The CLI pastes the original image at the center of a larger canvas, fills empty space with an edge-sampled neutral color, and appends a natural-extension instruction to the prompt.)

### 11. Lite fast-sketch mode

See [references/lite-quickref.md](references/lite-quickref.md) for the full example, Lite-only flags (`--web-search`, `--sequential`), and the pixel-floor table.

## CLI Reference

Flags below apply to both models unless noted; Lite-only flags (`--web-search`, `--sequential`) and Lite's pixel-floor constraints are detailed in [references/lite-quickref.md](references/lite-quickref.md).

### generate (create new image)

```
generate
  --prompt/-p <text>          Prompt text (mutually exclusive with --prompt-file)
  --prompt-file <path>        Read prompt from a UTF-8 file
  --reference-image <path|url> Reference image (repeatable; for image-to-image or
                               character-consistency work)
  --model pro|lite|<full-id>  Model (default pro)
  --size <1K|2K|3K|4K|WxH>    Size preset (default 2K; Lite supports 3K/4K) or
                               explicit WxH (e.g. 1792x1024)
  --wide                      Shortcut: 1792x1024 wide banner (16:9, Pro-only)
  --wechat-header             Alias for --wide (backward compatibility)
  --portrait                  Shortcut: 3:4 vertical (Pro: 1536x2048, Lite: 2048x2732)
  --landscape                 Shortcut: 16:9 horizontal (Pro: 2048x1152, Lite: 2732x1536)
  --square                    Shortcut: square (Pro: 1024x1024, Lite: 2048x2048)
  --output-format png|jpeg    Output format (default png)
  --watermark                 Add Seedream watermark (default off)
  --web-search                Enable web search (Lite only)
  --negative-prompt <text>    Negative prompt (Pro ships with a gentle quality-guard
                               default: "模糊, 低质量, 水印, 变形, 多余肢体"; pass an empty
                               string to disable it)
  --no-negative-prompt        Disable the default negative prompt (useful for
                               non-human scenes like product/landscape where
                               "extra limbs" is irrelevant)
  --optimize-prompt standard|fast Prompt optimization (Pro: standard only)
  --n <1-4>                   Generate n independent images (default 1)
  --out <path>                Output file path
  --out-dir <dir>             Output directory (default output/seedream-image-gen/)
  --timeout <sec>             Timeout (default 300)
  --force                     Overwrite existing files
  --dry-run                   Print request body and exit
```

### edit (modify an image: marker edit / style transfer / outpaint / img2img)

Inherits most `generate` parameters, and adds:

```
edit
  --reference-image <path>    Input image (required, repeatable; the first image is the
                               primary target when markers/outpaint are used)
  --marker-rect <spec>        Rectangular edit region (repeatable); pixel X,Y,W,H or
                               X%,Y%,W%,H%
  --marker-color #rrggbb      Marker color (default #ff0000)
  --marker-alpha <0-255>      Fill transparency (default 80)
  --marker-stroke <px>        Outline stroke width (default 3)
  --no-marker-cleanup-prompt  Don't auto-append "remove colored markers" instruction
  --outpaint <dir:pixels>     Extend the canvas (dir=left/right/top/bottom; repeatable)
```

Note: `edit` does not have `--n` / `--sequential` (edits target a single image; generate variants by re-running).

### generate-batch (batch)

```
generate-batch
  --input <jsonl>             JSONL file; each line is a bare prompt string or a
                               {"prompt": ...} JSON object
  --concurrency <n>           Max concurrent requests (default 3)
  --out-dir <dir>             Output directory (default output/seedream-image-gen/batch/)
  --model/size/...            Default parameters (overridable per-job)
  --dry-run                   Print all bodies and exit
  --force                     Overwrite existing files
```

JSONL job-object supported fields: `prompt`, `model`, `size`, `output_format`, `wide`, `wechat_header`, `square`, `portrait`, `landscape`, `watermark`, `web_search`, `optimize_prompt`, `negative_prompt`, `no_negative_prompt`, `reference_image` (list), `marker_rects` (list), `marker_color`, `marker_alpha`, `marker_stroke`, `no_marker_cleanup_prompt`, `outpaint` (list), `timeout`.

### list-models

Prints the known model IDs, capability matrix, and pricing.

## Output

- Images are written to `--out-dir` (default `output/seedream-image-gen/`) with filenames `YYYYMMDD-HHMMSS-<slug>[-n].png`.
- Each image is accompanied by a same-name `.json` metadata file containing: prompt, model, size, negative_prompt, marker_rects, outpaint, reported_size (actual output resolution), elapsed_ms, revised_prompt, usage, etc.
- When markers are used, an annotated copy (with the colored box drawn) is saved as `*-annotated.png` in the output directory so you can verify placement.
- Local reference images are automatically converted to base64 data URLs; remote URLs are passed through directly.

## Style Presets

| Preset | Best for |
|---|---|
| [text-poster](references/styles/text-poster.md) | Posters/covers/banners/badges with text (6 recipes; Pro core) |
| [text-effects](references/styles/text-effects.md) | 16 text effects (metal / neon / ink / glass / flame / bubble / 3D etc.) |
| [chinese-aesthetic](references/styles/chinese-aesthetic.md) | 国潮/水墨/24节气/traditional festivals/Chinese architecture/food (Pro-strength domain) |
| [product-photography](references/styles/product-photography.md) | Product/e-commerce/food (white BG, lifestyle, flat-lay, unboxing, lookbook) |
| [3d-icon-isometric](references/styles/3d-icon-isometric.md) | 3D app icons, frosted glass, claymorphism/盲盒手办, isometric miniature dioramas, chrome/neon 3D text |
| [editorial-infographic](references/styles/editorial-infographic.md) | Editorial infographic — hero photo + frosted-glass data cards (NatGeo / Bloomberg data-journalism style); for explainers, report covers, science/tech articles |
| [hand-drawn-tech-editorial](references/styles/hand-drawn-tech-editorial.md) | Hand-drawn tech editorial look (architecture diagrams + handwritten labels) |
| [technical-diagram](references/styles/technical-diagram.md) | Technical architecture / flow / schematic diagrams (labels ≤4 chars render reliably) |
| [education-science](references/styles/education-science.md) | Education / science / explainers (supports short labels) |
| [editorial-essay](references/styles/editorial-essay.md) | Editorial / cultural-essay accompaniment visuals (optional large overlaid title) |
| [visual-narrative](references/styles/visual-narrative.md) | Visual narrative / storyboard scenes (optional kicker title) |
| [editorial-pencil-sketch](references/styles/editorial-pencil-sketch.md) | Editorial pencil-sketch look (supports handwritten annotations) |
| [style-transfer](references/styles/style-transfer.md) | Style transfer — turn any photo into ink wash / ukiyo-e / Van Gogh / paper-cut / Dutch still life / Pixar / anime (commitment-language formula + 6 recipes; failing styles documented) |
| [photorealism](references/styles/photorealism.md) | Photorealistic photography — portrait / product / landscape / cityscape / candlelight / dual CGI toggle; group-shot success curve + realism-focused negative prompt |
| [multilingual](references/multilingual.md) | Multilingual typography + localization — 10+ languages (CJK/Latin/Hangul/Thai/Arabic), same-screen 4-script banner recipe, per-language scoring table |
| [text-deep](references/text-deep.md) | Text-dense image generation — architecture diagrams, calendars, data tables, menus, math/chemistry formulas, body text + footnotes; the **30-cell rule** for when to overlay values via HTML/PIL instead of asking Seedream |

For visual-generation tasks that don't fit an existing preset, write the prompt directly following the formula in [references/prompt-engineering.md](references/prompt-engineering.md) — presets are scaffolding, not molds; override anything that conflicts with the user brief.

## Error Handling

- **429/5xx auto-retry**: up to 8 attempts with exponential backoff (2/4/8/16/30/30/30/30s); honors the HTTP `retry-after` header.
- **400/401/403 do not retry**: parameter error, key error, or permission error (e.g. model not enabled for the account) — fail immediately with the error.
- Passing web_search/sequential/stream/fast-mode on Pro is filtered by the client (wastes no API call).
- Passing 1K / 1024² / 1792×1024 on Lite is rejected client-side (below the pixel floor).

## Authentication

1. Environment variable `ARK_API_KEY` (preferred)
2. `ARK_API_KEY=...` in a `.env` file in the working directory
3. Interactive prompt at the terminal (last resort; requires a TTY)

Get an API key: <https://console.volcengine.com/ark/region:ark+cn-beijing/apikey>

## References

- [API reference](references/api-reference.md) — parameter matrix, marker protocol, outpaint protocol, pricing, error codes
- [Prompt engineering guide](references/prompt-engineering.md) — six prompt formulas (generic / text / marker / consistency / style / multi-ref fusion), failure-mode checklist
- [Marker editing deep reference](references/marker-editing.md) — 8 copy-paste recipes, rect-size thresholds, annotated.png inspection checklist, failure modes
- [Lite quick reference](references/lite-quickref.md) — when to actually switch models, pixel-floor table, Lite-only flags, what Lite doesn't have
- [Styles directory](references/styles/) — 12 style presets (see table above)
