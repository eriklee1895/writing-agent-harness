# Technical diagram illustration styles

For system architecture posts, SaaS explainers, developer docs, workflow tutorials, and methodology articles. The goal is clarity, hierarchy, and clean structure.

## 1. Isometric system diagram

A clean isometric view of layered modules with clear data flow. Ideal for architecture overviews and product demos.

**Core formula:**
```
Clean isometric illustration, [system name] architecture diagram, [N] layered modules, color-coded blocks, arrows showing data flow, modern tech palette, white background, no text
```

**Example:**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Clean isometric illustration of a microservices architecture diagram, 4 layers (client apps, API gateway, service layer, data layer), color-coded blocks in blue and teal, arrows showing request flow, modern tech palette, crisp white background, no text" \
  --use-case infographic-diagram \
  --style "clean isometric illustration, technical diagram, modern SaaS aesthetic" \
  --composition "layered from front-left to back-right, arrows flowing left-to-right" \
  --palette "white background, blue, teal, light gray, dark navy accents" \
  --lighting "soft even lighting, minimal shadows" \
  --constraints "no text, no labels, no logos, white background" \
  --negative "photorealism, 3D render look, dark background" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/isometric-microservices.png
```

**Best for:** system architecture, product overviews, module relationship diagrams

---

## 2. Clean process infographic

A step-by-step timeline or flow diagram with icons and concise labels. gpt-image-2 handles small text well, so this is a good style to include verbatim labels.

**Core formula:**
```
Clean process infographic, [process name], [N] steps left-to-right, each step with a simple icon and short label, modern flat style, white background
```

**Example:**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Clean process infographic explaining the beer brewing process, 5 steps left-to-right (Mashing, Boiling, Fermentation, Conditioning, Bottling), each step with a simple icon and a short English label. Warm brown and amber palette, modern flat style, crisp white background, professional information design" \
  --use-case infographic-diagram \
  --style "clean process infographic, modern flat design, information design" \
  --composition "horizontal timeline, 5 evenly spaced nodes" \
  --palette "white background, warm amber, soft brown, cream, dark text" \
  --text "Mashing, Boiling, Fermentation, Conditioning, Bottling" \
  --constraints "labels must be short and readable, no extra text" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/brewing-process.png
```

**Best for:** workflow tutorials, methodology explainers, step-by-step guides

---

## 3. Blueprint / line-art schematic

A technical drawing with cyan or dark lines on a white background. Perfect for developer docs, API design, CI/CD diagrams, and engineering blogs.

**Core formula:**
```
Blueprint style technical schematic, [system/tool] diagram, line-art layout, [cyan/dark] lines on white, clean engineering feel, minimal labels
```

**Example:**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Blueprint style technical schematic of a Kubernetes cluster, line-art layout showing Master nodes and Worker nodes with connecting lines, cyan lines on white background, clean engineering feel, minimal icons, no paragraphs of text" \
  --use-case infographic-diagram \
  --style "blueprint technical schematic, line-art, engineering diagram" \
  --composition "cluster centered, master nodes top, worker nodes below, lines for connections" \
  --palette "white background, cyan lines, light blue fills, dark blue accents" \
  --lighting "flat technical lighting" \
  --constraints "no text blocks, no logos, line-art only" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/kubernetes-blueprint.png
```

**Best for:** developer documentation, infrastructure diagrams, API design

---

## 4. Technical poster / one-pager

A single-page visual summary with a hero diagram, a few icons, and a bold headline. Good for landing-page-style articles or launch posts.

**Core formula:**
```
Modern technical poster, [topic] explained visually, hero diagram, 3-4 supporting icons, bold headline, clean white background, SaaS aesthetic
```

**Example:**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Modern technical poster explaining 'How Retrieval-Augmented Generation Works'. Central hero diagram showing a user query, a knowledge base, and a combined answer flow. 3 supporting icons below. Bold headline reading EXACT VERBATIM 'How RAG Works'. Clean white background, SaaS aesthetic, blue and teal palette" \
  --use-case infographic-diagram \
  --style "modern technical poster, SaaS information design, clean flat illustration" \
  --composition "headline top center, hero diagram middle, icon row bottom" \
  --palette "white background, blue, teal, soft gray" \
  --text "How RAG Works" \
  --constraints "headline exact, no body text paragraphs" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/rag-technical-poster.png
```

**Best for:** launch posts, feature explainers, one-page technical summaries

---

## General tips

1. **Prefer `wide` or `2k-landscape` sizes.** Technical diagrams are usually read on desktop.
2. **Use `--quality high` when labels matter.** gpt-image-2 renders small text better than most models, but it still benefits from high quality.
3. **Keep labels short.** One or two words per label. Long sentences become unreadable at small sizes.
4. **Explicitly ask for `white background` and `no dark vignette`.** gpt-image-2 sometimes defaults to dark gradient backdrops for tech imagery.
5. **Avoid mixing 3D render and flat diagram in the same prompt.** Pick one visual language and stay consistent.
