# Education and science illustration styles

For explainers, how-to guides, textbook-style content, knowledge cards, and science communication. The goal is accurate structure plus approachable visuals.

This preset provides **scaffolding, not a mold**: it defaults to friendly educational layouts and clean academic palettes, but the model should keep only the structural guardrails when the user's brief already carries a strong visual concept.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `hand-drawn tutorial illustration`, `concept framework diagram`, `textbook illustration`, `clean knowledge poster` |
| Background | `white background`, `clean layout`, `minimal decorative clutter` |
| Composition | `step-by-step layout`, `labeled nodes`, `clear hierarchy`, `icons + short labels`, `legend or key row` |
| Hard avoids | `photorealism unless requested`, `dark background`, `paragraphs of body text`, `ornamental decoration`, `unreadable tiny labels` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Sub-style | Default direction |
|---|---|
| Hand-drawn tutorial | `warm sketchbook palette`, `coffee browns`, `cream`, `soft orange`, `graphite gray`, `friendly and approachable` |
| Concept framework | `soft academic palette`, `warm gradient`, `clean flat design`, `educational illustration style` |
| Textbook illustration | `academic palette`, `earthy browns`, `oranges`, `yellows`, `grays`, `accurate visual representation` |
| Knowledge poster | `bold typography`, `limited palette`, `navy blue background with white text`, `mobile-friendly vertical layout` |

> **Override rule:** If the user describes a different palette, rendering style, or layout, drop the inspirational defaults and keep only the structural template (white background, step-by-step/labeled composition, hard avoids).

---

## 1. Hand-drawn tutorial

A friendly step-by-step diagram with sketchy lines and warm colors. Great for recipes, DIY guides, fitness tutorials, and soft-skill explainers.

**Core formula:**
```
Hand-drawn tutorial illustration, [topic] step-by-step, [N] steps in one image, simple icons, warm sketchbook palette, white background
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Hand-drawn tutorial illustration showing how to make pour-over coffee, 4 steps in one wide image, simple icons and short English labels for each step, warm sketchbook palette with coffee browns and cream, white background, friendly and approachable" \
  --use-case infographic-diagram \
  --style "hand-drawn tutorial illustration, sketchbook aesthetic, warm colors" \
  --composition "4 steps left-to-right, each with a small circular icon and label" \
  --palette "white background, coffee brown, cream, soft orange, graphite gray" \
  --text "Bloom, Pour, Steep, Serve" \
  --constraints "short labels, friendly hand-drawn feel, no photorealism" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/coffee-tutorial.png
```

**Best for:** recipes, DIY guides, fitness tutorials, soft-skill how-tos

---

## 2. Concept framework diagram

A structured visual of relationships, hierarchies, or cycles. Useful for academic concepts, mental models, and theory explainers.

**Core formula:**
```
Clean concept framework diagram, [concept] structure, [shape/layout] showing relationships, labeled nodes, soft academic palette, white background
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Clean concept framework diagram of Maslow's hierarchy of needs, 5-level pyramid from physiological at the bottom to self-actualization at the top, each level with a simple icon and short English label, soft warm gradient, white background, educational illustration style" \
  --use-case infographic-diagram \
  --style "clean concept framework diagram, educational illustration, soft flat design" \
  --composition "pyramid centered, labels aligned to each level" \
  --palette "white background, warm gradient from coral to soft yellow" \
  --text "Physiological, Safety, Belonging, Esteem, Self-Actualization" \
  --constraints "labels exact and readable, no extra text" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/maslow-pyramid.png
```

**Best for:** academic concepts, mental models, frameworks, theory explainers

---

## 3. Textbook illustration

A precise, labeled diagram suitable for formal educational content. Good for biology, physics, geography, and other subject-matter posts.

**Core formula:**
```
Textbook illustration style, [topic], accurate visual representation, clear labels, clean layout, academic palette, white background
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Textbook illustration style cross-section of Earth's interior, showing crust, mantle, outer core, and inner core with clear English labels, different colors and textures for each layer, academic palette, white background, suitable for middle-school geography" \
  --use-case infographic-diagram \
  --style "textbook illustration, scientific diagram, clear labels" \
  --composition "central cross-section, labels pointing to each layer" \
  --palette "white background, earthy browns, oranges, yellows, grays" \
  --text "Crust, Mantle, Outer Core, Inner Core" \
  --constraints "labels accurate and readable, no decorative clutter" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/earth-interior.png
```

**Best for:** science communication, textbook content, academic writing

---

## 4. Knowledge poster / social card

A compact, shareable summary with a headline, a few key points, and simple icons. Good for Twitter/X threads, newsletters, and mobile-first explainers.

**Core formula:**
```
Clean knowledge poster, headline '[title]', [N] key points with icons, mobile-friendly layout, bold typography, limited palette
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Clean knowledge poster with headline EXACT VERBATIM '5 Sleep Myths Debunked', 5 numbered cards arranged vertically, each with a simple icon and a short myth label, navy blue background with white text, mobile-friendly vertical layout, modern information design" \
  --use-case infographic-diagram \
  --style "clean knowledge poster, modern information design, bold typography" \
  --composition "headline top, 5 cards stacked below, each with number + icon + label" \
  --palette "navy blue background, white text, soft yellow accents" \
  --text "5 Sleep Myths Debunked" \
  --constraints "headline exact, labels short, vertical mobile layout" \
  --size "1024x1792" \
  --quality high \
  --out output/gpt-image-2/sleep-myths-poster.png
```

**Best for:** social sharing, newsletter graphics, quick explainers

---

## General tips

1. **Limit information density.** 3–6 core concepts per image is ideal. More becomes unreadable.
2. **Use labels sparingly.** gpt-image-2 renders text well, but educational images still work better with icons + short labels than paragraphs.
3. **White background is safest.** Colored backgrounds can distract from the concept.
4. **Match the visual style to the audience.** Hand-drawn for casual learners; textbook style for formal content.
5. **For vertical mobile formats,** use `--size "1024x1792"` or similar. Remember both edges must be multiples of 16.
6. **When the user's brief already specifies a palette, rendering style, or layout, drop the inspirational defaults and keep only the structural guardrails.**
