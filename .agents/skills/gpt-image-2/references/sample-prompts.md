# Sample prompts for gpt-image-2

Quick copy-paste recipes organized by visual style. These are starting points — tune the augmentation fields to your brief.

For detailed style presets, see the [styles/](styles/) directory:

- [Editorial pencil-sketch workflow](styles/editorial-pencil-sketch.md) — hand-drawn line work + watercolor washes, ideal for AI workflows and creative processes.

> **How to add a new preset style:** Add a standalone file under [styles/](styles/) and link it here. Keep existing sections below as quick recipes; move detailed formulas to their own style file.

---

## Photorealistic & product

### Alpine cabin landscape

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A cozy alpine cabin at dawn, mist rising off a still lake, distant snow-dusted peaks" \
  --use-case photorealistic-natural \
  --style "photorealistic, 35mm film photography, slight grain" \
  --composition "wide landscape, cabin off-center right, low horizon, eye-level" \
  --lighting "soft golden hour, warm interior glow from the cabin window" \
  --palette "muted greens, deep teals, warm amber highlights" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/cabin.png
```

### Product mockup with style reference

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Ceramic pour-over coffee dripper on a slate countertop, soft morning side light, slight steam. Use the reference image ONLY for palette and material treatment; do not copy its subject." \
  --use-case product-mockup \
  --style "clean product photography, soft gradient backdrop" \
  --composition "45-degree angle, generous negative space on the right for copy" \
  --lighting "single softbox upper-left, no harsh shadows" \
  --constraints "no logos, no text, no watermark" \
  --size square \
  --out output/gpt-image-2/dripper.png
```

---

## Text-heavy images

### Minimalist movie poster

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Minimalist movie poster, 2.35:1, centered title typography reading EXACT, VERBATIM, NO EXTRA CHARACTERS 'AURORA 2026' in bold condensed sans-serif (Helvetica Condensed style), subtitle in italic serif 'A short film by Lin Wei'. Single line of fine print at the bottom: 'In select theaters December 21'. No other text anywhere." \
  --use-case infographic-diagram \
  --style "minimalist editorial poster, high contrast, single hero subject" \
  --composition "centered, generous negative space, top 30% reserved for safe area" \
  --palette "deep navy background, white type, single gold accent" \
  --text 'AURORA 2026' \
  --size wide \
  --quality high \
  --out output/gpt-image-2/aurora-poster.png
```

---

## Editorial & collage

### Magazine editorial collage

A mixed-media editorial layout: overlapping photos, torn paper edges, handwritten annotations, and one bold headline. Great for cultural essays, brand narratives, and mood-driven articles.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A magazine editorial collage page with the theme 'The Future of Reading'. Mixed-media layout: 4 to 6 photos of varying sizes with torn-paper edges, handwritten annotations in black ink, one bold centered headline reading EXACT VERBATIM 'The Future of Reading'. Print magazine aesthetic, slightly textured paper background, muted warm palette, no watermark." \
  --use-case illustration-story \
  --style "editorial mixed-media collage, print magazine aesthetic, torn paper, handwritten notes" \
  --composition "asymmetric grid, headline centered, overlapping photo layers" \
  --palette "warm off-white paper, muted terracotta, dusty teal, black ink" \
  --text "The Future of Reading" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/magazine-collage.png
```

Tips for this style:
- Specify the number of photos/elements and the headline verbatim.
- Ask for **"torn-paper edges"** and **"slightly textured paper background"** to get the analog feel.
- Keep the color palette muted; too many bright colors look digital.

### Torn-paper mood board

A soft, tactile mood board made of torn paper scraps, fabric swatches, tape, and handwritten labels. Useful for creative proposals, brand direction, and inspiration collages.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A torn-paper mood board for a calm coastal brand. White and warm beige paper background. Scattered pieces: a torn photo of ocean waves, a fabric swatch in oatmeal linen, a hand-painted color strip in seafoam and sand, a small handwritten label reading EXACT VERBATIM 'Coastal Calm', a pressed seaweed specimen, and a piece of washi tape. Soft natural shadows, no harsh digital edges, no watermark." \
  --use-case illustration-story \
  --style "torn-paper mood board, tactile analog collage, natural materials, soft shadows" \
  --composition "flat lay, scattered but balanced, label near center" \
  --palette "warm beige, oatmeal, seafoam, sand, soft gray" \
  --text "Coastal Calm" \
  --size square \
  --quality high \
  --out output/gpt-image-2/mood-board.png
```

Tips for this style:
- List 5-7 specific physical items so the collage feels curated.
- Add **"soft natural shadows"** and **"flat lay"** for depth without 3D render.
- Ask for **"no harsh digital edges"** to keep the analog look.

---

## Posters & illustration

### Vintage travel poster

Bold, retro travel-poster style with flat color blocks and large typography. Good for cities, events, destinations, and seasonal themes.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Vintage travel poster for Kyoto in spring. Bold flat color blocks in coral, teal, and cream. A branch of cherry blossoms frames the top. Centered large typography reading EXACT VERBATIM 'KYOTO SPRING' in a retro sans-serif. Subtitle below: EXACT VERBATIM 'Japan, 2026'. Minimal illustration of a pagoda silhouette at the bottom. No gradients, no photorealism, no watermark." \
  --use-case illustration-story \
  --style "vintage travel poster, bold flat color blocks, retro typography, screen-print aesthetic" \
  --composition "vertical poster layout, title centered, decorative elements top and bottom" \
  --palette "coral, teal, cream, black" \
  --text "KYOTO SPRING, Japan, 2026" \
  --size portrait \
  --quality high \
  --out output/gpt-image-2/kyoto-poster.png
```

Tips for this style:
- Use a limited palette of 3-4 flat colors.
- Quote the title letter-by-letter if it must be exact (e.g. "K-Y-O-T-O S-P-R-I-N-G").
- Specify **"no gradients, no photorealism"** to keep the poster look.

### Cinematic concept art

Cinematic ultra-wide scene with volumetric light, atmospheric haze, and photorealistic texture. Good for mood boards, film pre-visualization, game concept art, and immersive scene illustrations.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Ultra-wide 21:9 cinematic concept art: a massive waterfall cascading into a dark abyss, silhouetted pine trees on the cliff edges, moonlight breaking through storm clouds above, mist and spray illuminated by faint bioluminescent blue glow from the depths. Volumetric light rays, atmospheric haze, photorealistic texture, cinematic color grading with deep teal shadows and cool silver highlights. Epic scale, matte-painting quality. No text, no watermark." \
  --use-case stylized-concept \
  --style "cinematic concept art, ultra-wide matte painting, volumetric light, atmospheric haze, photorealistic" \
  --composition "ultra-wide landscape, low angle looking up, waterfall centered, vast negative space above" \
  --lighting "moonlight from above breaking through clouds, bioluminescent blue glow from below, volumetric god rays" \
  --palette "deep teal, cool silver, moonlight blue, dark pine green, subtle bioluminescent cyan" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/cinematic-waterfall.png
```

Tips for this style:
- Use **"ultra-wide 21:9"** for cinematic framing; `2k-landscape` (2048x1152) is a good match.
- **"Volumetric light rays"** and **"atmospheric haze"** are the two most reliable keywords for cinematic depth.
- Specify a **light source direction** and a **secondary glow source** for dramatic contrast.
- Keep the palette limited (3-5 colors) and name a **color grading** style.
- Add **"matte-painting quality"** or **"photorealistic texture"** to push detail level.
- For brighter daytime cinematic scenes, swap "moonlight" for "golden hour" or "storm light."
```

---

## Diagrams & flowcharts

### Dark-mode tech flowchart

A clean, text-readable process diagram with a modern dark UI aesthetic. gpt-image-2 renders the labels well if you quote the verbatim text and declare the typography.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A dark-mode tech flowchart explaining an Agent workflow. Wide 16:9 layout, deep navy (#0a0f1c) background, neon cyan (#00e5ff) accent lines and glow. Three rounded rectangular nodes arranged left-to-right, connected by cyan arrows. Top title: EXACT VERBATIM 'Claude Code Agent Workflow'. Node 1 label: EXACT VERBATIM 'SENSE' with a radar/scan icon. Node 2 label: EXACT VERBATIM 'PLAN' with a compass icon. Node 3 label: EXACT VERBATIM 'ACT' with a lightning icon. Clean sans-serif type, bold white labels, subtle tech-grid texture. No human figures, no watermark." \
  --use-case infographic-diagram \
  --style "dark-mode tech infographic, neon cyan on deep navy, clean vector-style iconography" \
  --composition "horizontal flow, left-to-right, generous padding, title centered at top" \
  --palette "deep navy background, white text, neon cyan accents" \
  --text "Claude Code Agent Workflow, SENSE, PLAN, ACT" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/agent-flowchart.png
```

Tips for this style:
- Keep node labels short (one or two words) and wrap them in EXACT VERBATIM.
- Declare the arrow direction explicitly (`left-to-right`, `top-to-bottom`, `circular`).
- Use `--quality high` and a landscape size so small text stays sharp.
- If the diagram has more than 5 nodes, prefer `generate-batch` with one node-style reference plus text, or split into two connected diagrams.

### Hand-painted watercolor flowchart

A warm, sketchbook-style diagram with soft watercolor washes, hand-drawn ink outlines, and visible paper texture. Good for presentations, blog posts, and explainers that should feel human and approachable rather than corporate-tech.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A hand-painted watercolor flowchart on white textured paper. Show a 3-step Agent workflow as a horizontal spine. Each step is a soft, rounded rectangular watercolor blob with a hand-drawn ink outline. Step 1: pastel lavender blob, label EXACT VERBATIM 'Sense' (感知), small radar icon. Step 2: pale yellow blob, label EXACT VERBATIM 'Plan' (规划), small compass icon. Step 3: mint green blob, label EXACT VERBATIM 'Act' (执行), small lightning icon. Curved ink arrows between steps with tiny watercolor splash accents. Top title: EXACT VERBATIM 'Agent Workflow'. Soft pastel palette, visible paper grain, confident slightly imperfect linework, airy negative space, no heavy shadows, no photorealism, no watermark." \
  --use-case infographic-diagram \
  --style "hand-painted watercolor infographic, ink outlines first then loose translucent washes, sketchbook aesthetic" \
  --composition "horizontal flow, three rounded blobs left-to-right, title centered above, generous white space" \
  --palette "soft lavender, pale yellow, mint green, black ink outlines, white paper" \
  --text "Agent Workflow, Sense, 感知, Plan, 规划, Act, 执行" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/watercolor-agent-flowchart.png
```

Tips for this style:
- Always mention **"white textured watercolor paper"** and **"visible paper grain"**.
- Use **"ink outlines first, then loose watercolor washes"** to get sketch + color separation.
- Request **"confident slightly imperfect linework"** — too clean kills the hand-drawn feel.
- Keep the color palette small (3-5 pastels) and ask for **"airy negative space"**.
- Quote both English and Chinese text as EXACT VERBATIM if you need bilingual labels.
- For a more editorial look, add: **"no hard digital edges, no airbrush effects"**.

### Flat isometric illustration

A clean, 3D-ish flat illustration with 30° isometric projection. Perfect for SaaS architecture diagrams, onboarding hero images, and product explainers that need a friendly but structured look.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A flat isometric illustration of a modern software development environment. 30-degree isometric projection, clean vector linework. A developer's desk with a large monitor showing code, a laptop open to the side, a coffee mug, a small potted plant, and a bookshelf in the background. Connected floating panels around the desk: CI/CD pipeline status, deployment dashboard, monitoring graphs. Limited palette of 5 colors: deep blue, mint green, warm gray, off-white, soft coral. Subtle drop shadows, no gradients, solid background. Friendly professional mood. No text in the illustration. No watermark." \
  --use-case infographic-diagram \
  --style "flat-color isometric illustration, 30-degree projection, clean linework, 5-color palette" \
  --composition "centered desk scene, floating panels orbiting, isometric perspective" \
  --palette "deep blue, mint green, warm gray, off-white, soft coral" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/isometric-desk.png
```

Tips for this style:
- Always specify **"30-degree isometric projection"** — not just "isometric".
- Limit the palette to **5 colors maximum**; fewer colors = cleaner result.
- Use **"no gradients, no text"** if you only want pure illustration.
- For labeled panels or callouts, add exact verbatim text and set `--quality high`.

### Fact-grounded social infographic

A vertical 9:16 infographic optimized for social sharing, with real factual content structured as a step-by-step explainer. Title at the top, numbered sections with icons, clean pastel palette.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A vertical 9:16 social media infographic explaining how large language models work. Title at the top: EXACT VERBATIM 'How LLMs Work'. Five numbered steps: 1. Tokenize (text broken into pieces), 2. Embed (each piece gets a vector), 3. Attend (model finds relationships), 4. Predict (next token sampled), 5. Decode (tokens back to text). Each step has a minimal icon and a short label. Clean flat vector style, soft pastel palette (lavender, mint, peach, sky blue), generous spacing, numbered circles for each step. No heavy shadows, no watermark, no extra text." \
  --use-case infographic-diagram \
  --style "vertical social infographic, clean flat vector, pastel palette, numbered steps with icons" \
  --composition "vertical flow, title top-center, 5 stacked steps, numbered circles, generous spacing" \
  --palette "lavender, mint, peach, sky blue, white background" \
  --text "How LLMs Work" \
  --size portrait \
  --quality high \
  --out output/gpt-image-2/llm-infographic.png
```

Tips for this style:
- Use **9:16 portrait** (`--size portrait` or `1024x1536`) for Stories/TikTok/Reels format.
- Keep each step label to 1-2 words max for clean text rendering.
- Add **"no extra text"** in constraints — the model sometimes adds unrequested labels.
- For bilingual versions, add Chinese subtitles in parentheses after each label.
- For data-heavy topics, consider `--size 2k-landscape` and split into a carousel series.

### Scientific textbook diagram

A clean, educational diagram in the style of a science textbook or encyclopedia. Large central illustration with numbered callout boxes connected by thin leader lines. Good for biology, physics, engineering, and any topic that benefits from labeled visual explanation.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A scientific textbook diagram explaining photosynthesis. Large central illustration of a leaf cross-section showing chloroplasts, stomata, and veins. 5 numbered callout boxes with short labels: 1. 'Light Absorption' (chlorophyll captures photons), 2. 'Water Splitting' (H2O → O2), 3. 'Electron Transport' (thylakoid membrane), 4. 'Carbon Fixation' (Calvin cycle), 5. 'Glucose Output' (C6H12O6). Thin leader lines connecting each box to its location. Clean vector illustration, flat color, educational textbook style, white background, professional sans-serif typography. No watermark, no decorative elements." \
  --use-case infographic-diagram \
  --style "scientific textbook diagram, clean vector, flat color, numbered callout boxes, leader lines" \
  --composition "large central illustration, 5 callout boxes arranged around it, leader lines" \
  --palette "white background, deep green, sky blue, warm yellow, dark gray labels" \
  --text "Light Absorption, Water Splitting, Electron Transport, Carbon Fixation, Glucose Output" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/photosynthesis-diagram.png
```

Tips for this style:
- Keep callout labels to 1-3 words; long paragraphs degrade rendering.
- Use **"thin leader lines"** to connect labels to diagram locations.
- Specify **"white background"** and **"educational textbook style"** for a clean academic look.
- Verify all facts independently — generated diagrams are design drafts, not authoritative.
- For Chinese (双语), add labels like `'光吸收 (Light Absorption)'`.

### Knowledge card / infographic

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A clean horizontal infographic explaining the RAG pipeline. Sections left-to-right: '1. INGEST' (documents icon), '2. CHUNK' (split blocks icon), '3. EMBED' (vector dots icon), '4. RETRIEVE' (magnifier icon), '5. GENERATE' (chat bubble icon). Arrows between sections. Title at top: 'How RAG Works'. Bilingual labels: English primary, Chinese subtitles (摄取, 分块, 嵌入, 检索, 生成). Modern flat-illustration style, soft palette." \
  --use-case infographic-diagram \
  --style "flat technical infographic, clean grouped modules, soft professional palette" \
  --composition "horizontal flow, clear left-to-right arrows, generous spacing" \
  --palette "cool grays with a single warm accent" \
  --text "How RAG Works" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/rag-pipeline.png
```

---

## Characters & 3D

### Pixar 3D character

A friendly, stylized 3D character with soft lighting and expressive features. Good for IP avatars, story illustrations, and children's content.

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A 3D Pixar-style character of a small curious fox, 3/4 front view, sitting. Large expressive amber eyes, soft round cheeks, gentle smile, fluffy orange-white fur with a few stray strands. Soft cinematic key light from above, warm rim light from behind. Clean pastel gradient background, shallow depth of field with creamy bokeh. No text, no watermark." \
  --use-case stylized-concept \
  --style "3D Pixar-style character, smooth subsurface scattering skin/fur, stylized proportions" \
  --composition "3/4 front view, centered, ample headroom" \
  --lighting "soft cinematic key light from above, warm rim light from behind" \
  --palette "warm orange, white, soft pastel background" \
  --size square \
  --quality high \
  --out output/gpt-image-2/pixar-fox.png
```

Tips for this style:
- Describe facial features in detail (eye size, cheek shape, expression) — Pixar-style is defined by its expressive faces.
- Use **"subsurface scattering"** and **"creamy bokeh"** for material authenticity.
- **"3/4 front view"** is the most readable angle; avoid full profile unless the character design calls for it.
- For consistency across multiple frames/poses, save the first generation as a reference image and pass it to subsequent edits.

---

## Image editing workflows

### Background-replace edit

```bash
uv run scripts/gpt_image_2.py edit \
  --image product.png \
  --prompt "Replace ONLY the background with a warm sunset gradient. Keep the product, the product edges, the lighting on the product, and the camera angle UNCHANGED. No new text, no logos, no watermark." \
  --use-case precise-object-edit \
  --constraints "change only the background; keep the product and its edges unchanged" \
  --size landscape \
  --out output/gpt-image-2/product-sunset.png
```

### Multi-reference compositing (inpaint)

```bash
uv run scripts/gpt_image_2.py edit \
  --image subject.png \
  --image backdrop.png \
  --mask paint-the-subject.png \
  --prompt "Image 1 is the subject. Image 2 is the backdrop. Inpaint the masked region of image 1 with the subject from image 1, placed naturally into the lighting and perspective of image 2. Keep the subject's identity, clothing, and edges intact. No text, no watermark." \
  --size landscape \
  --out output/gpt-image-2/composite.png
```

---

## Batch generation

### From a JSONL file

`prompts.jsonl`:

```json
{"prompt":"Vintage travel poster, EXACT verbatim text 'KYOTO SPRING', letter-by-letter K-Y-O-T-O S-P-R-I-N-G, no extra characters, sakura branches framing the title","size":"square","quality":"high"}
{"prompt":"Studio shot of a matte black fountain pen on warm gray paper","size":"portrait","quality":"medium"}
{"prompt":"A 3D render of a low-poly arctic fox, white and pale blue, soft top-down lighting, gentle shadow","size":"square"}
```

Run:

```bash
uv run scripts/gpt_image_2.py generate-batch \
  --input prompts.jsonl \
  --out-dir output/gpt-image-2/batch \
  --concurrency 5
```

---

## Sources & further reading

- [OpenAI Cookbook — GPT Image prompting guide](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide)
- [awesome-gpt-image-2 — 470+ cases, 20+ industrial templates](https://github.com/freestylefly/awesome-gpt-image-2)
- [garden-skills — 79+ gpt-image-2 templates](https://github.com/ConardLi/garden-skills)
- [Felo.ai — 8-Element Framework + 50 templates](https://felo.ai/blog/gpt-image-2-prompt-guide-50-templates/)
- [lihuanyu.com — gpt-image-2 technical diagram prompts](https://www.lihuanyu.com/en/posts/2026/gpt-image-2-technical-diagram-prompts/)
- [Pixo — GPT-Image-2 prompt guide](https://pixo.video/blog/gpt-image-2-prompt-guide)
- [Fal.ai — GPT Image 2 prompting guide](https://fal.ai/learn/tools/prompting-gpt-image-2)
- [Atlabs — Ultimate GPT Image 2 prompting guide](https://www.atlabs.ai/blog/the-ultimate-gpt-image-2-prompting-guide-how-to-use-openai%E2%80%99s-best-image-model-2026)
- [OIMI — 20 GPT Image 2 examples](https://oimi.ai/en/blog/top-20-gpt-image-2-prompts)
- [Apiyi — GPT-Image-2 prompt collection](https://help.apiyi.com/en/gpt-image-2-prompts-collection-april-2026-en.html)
- [Picsart — How to prompt GPT Image 2](https://picsart.com/blog/gpt-image-2-prompts/)
