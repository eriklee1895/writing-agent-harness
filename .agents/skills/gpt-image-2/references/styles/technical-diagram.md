# Technical diagram illustration styles

For system architecture posts, SaaS explainers, developer docs, workflow tutorials, and methodology articles. The goal is clarity, hierarchy, and clean structure.

This preset provides **scaffolding, not a mold**: it defaults to clean white backgrounds and modern tech palettes, but the model should keep only the structural guardrails when the user's brief already carries a strong visual concept.

We split this category into two altitude levels so you don't accidentally ask for a simple icon overview when you actually need a labeled architecture diagram.

- **Simple / overview:** [`technical-diagram-simple`](#1-technical-diagram-simple) — clean isometric, product demos, module overviews.
- **Detailed / architecture:** [`technical-diagram-architecture`](#2-technical-diagram-architecture) — layered diagrams with numbered steps, component labels, data flows, and legends.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `clean isometric illustration`, `modern flat illustration`, `technical diagram`, `information design` |
| Background | `crisp white background`, `minimal or no texture`, `no dark vignette` |
| Composition | `layered modules`, `left-to-right data flow`, `numbered steps`, `labeled components`, `legend row` |
| Hard avoids | `photorealism`, `3D render look`, `dark background`, `ornamental decoration`, `paragraphs of body text` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Dimension | Default direction |
|---|---|
| Color | `modern tech palette`, `blue and teal`, `soft gray`, `dark navy accents` |
| Style | `modern SaaS aesthetic`, `clean information design` |

> **Override rule:** If the user describes a different palette, rendering style, or atmosphere, drop the inspirational defaults and keep only the structural template (white background, layered/flow composition, hard avoids).

---

## 1. Technical diagram — simple

A clean, high-level overview. Use this when you want a readable thumbnail or hero image that communicates structure without dense labels.

**Core formula:**
```
Clean isometric illustration, [system name] overview diagram, [N] layered modules, color-coded blocks, arrows showing data flow, modern tech palette, white background, minimal or no text
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Clean isometric illustration of a microservices architecture overview, 4 layers (client apps, API gateway, service layer, data layer), color-coded blocks in blue and teal, arrows showing request flow, modern tech palette, crisp white background, no text" \
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

**Best for:** product overviews, module relationship diagrams, landing-page hero diagrams

---

## 2. Technical diagram — architecture

A detailed architecture diagram with explicit steps, component labels, and data-flow annotations. Use this when the article needs to explain *how* something works, not just what it looks like.

**Core formula:**
```
Detailed technical architecture diagram, [system name], [N] numbered steps or layers, labeled components, arrows showing data flow, legend row, modern flat or isometric style, white background
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Detailed technical architecture diagram explaining Retrieval-Augmented Generation (RAG). 5 numbered steps left-to-right: 1 User Query, 2 Retrieve from Knowledge Base, 3 Augment Prompt, 4 LLM Generate, 5 Generated Answer. Each step shows a labeled component box with a simple icon. Arrows connect the steps. A bottom legend row explains each component. Clean modern flat style, crisp white background, blue and teal palette" \
  --use-case infographic-diagram \
  --style "detailed technical architecture diagram, labeled components, modern flat illustration" \
  --composition "horizontal pipeline, 5 numbered steps top row, legend row below" \
  --palette "white background, blue, teal, soft gray, dark navy text" \
  --text "User Query, Retrieve, Augment, Generate, Generated Answer" \
  --constraints "numbered steps, labeled components, legend row, no paragraphs of body text" \
  --negative "oversimplified icon row, missing labels, dark background" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/rag-architecture-diagram.png
```

**Best for:** architecture deep-dives, methodology explainers, workflow tutorials, developer docs

---

## 3. Clean process infographic

A step-by-step timeline or flow diagram with icons and concise labels. gpt-image-2 handles small text well, so this is a good style to include verbatim labels.

**Core formula:**
```
Clean process infographic, [process name], [N] steps left-to-right, each step with a simple icon and short label, modern flat style, white background
```

**Example (full preset):**
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

## 4. Blueprint / line-art schematic

A technical drawing with cyan or dark lines on a white background. Perfect for developer docs, API design, CI/CD diagrams, and engineering blogs.

**Core formula:**
```
Blueprint style technical schematic, [system/tool] diagram, line-art layout, [cyan/dark] lines on white, clean engineering feel, minimal labels
```

**Example (full preset):**
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

## General tips

1. **Match altitude to intent.** Use `technical-diagram-simple` for overviews and `technical-diagram-architecture` when the reader needs to follow a pipeline.
2. **Prefer `wide` or `2k-landscape` sizes.** Technical diagrams are usually read on desktop.
3. **Use `--quality high` when labels matter.** gpt-image-2 renders small text better than most models, but it still benefits from high quality.
4. **Keep labels short.** One or two words per label. Long sentences become unreadable at small sizes.
5. **Explicitly ask for `white background` and `no dark vignette`.** gpt-image-2 sometimes defaults to dark gradient backdrops for tech imagery.
6. **Avoid mixing 3D render and flat diagram in the same prompt.** Pick one visual language and stay consistent.
7. **For architecture diagrams, explicitly request numbered steps, a legend row, and labeled components.** Without these constraints the model tends to collapse the diagram into a few generic icons.
8. **When the user's brief already specifies a palette or rendering style, drop the inspirational defaults and keep only the structural guardrails.**
