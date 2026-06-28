# Editorial essay illustration styles

For essays, literary nonfiction, cultural commentary, personal narrative, travel writing, and slow-living pieces. The goal is mood, metaphor, and texture — not information density.

This preset provides **scaffolding, not a mold**: it defaults to atmospheric editorial imagery, but the model should keep only the structural guardrails when the user's brief already carries a strong visual concept.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `contemporary editorial illustration`, `painterly illustration`, `mixed-media collage`, `still-life illustration` |
| Background | `generous negative space`, `soft or plain background`, `no diagram elements` |
| Composition | `visual metaphor`, `layered composition`, `central symbolic object or scene` |
| Hard avoids | `text`, `logos`, `diagram elements`, `arrows`, `speech bubbles`, `UI screenshots`, `photorealism unless requested` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Sub-style | Default direction |
|---|---|
| Magazine editorial | `restrained palette`, `muted teal`, `warm amber`, `off-white`, `deep navy`, `atmospheric lighting` |
| Literary watercolor | `soft brushstrokes`, `gentle light`, `quiet mood`, `painterly texture`, `ochre`, `sage green`, `soft gray-blue` |
| Mixed-media collage | `torn paper edges`, `overlapping photos`, `handwritten annotations`, `bold headline`, `textured paper background` |
| Minimal still life | `symbolic objects`, `soft shadows`, `restrained palette`, `contemplative mood` |

> **Override rule:** If the user describes a different palette, medium, or atmosphere, drop the inspirational defaults and keep only the structural template (editorial/metaphor-driven composition, no diagram elements, hard avoids).

---

## 1. Magazine editorial illustration

A polished contemporary editorial image with layered composition and restrained color. Good for opinion pieces, cultural essays, and modern-life topics.

**Core formula:**
```
Contemporary editorial illustration, [visual metaphor], layered composition, restrained palette, atmospheric lighting, no text, no diagram elements
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Contemporary editorial illustration, a paper boat sailing across an ocean of open book pages toward a distant lighthouse, layered composition, muted teal and warm amber palette, soft natural light, metaphor for exploration and knowledge, no text, no diagrams" \
  --use-case illustration-story \
  --style "contemporary editorial illustration, print magazine aesthetic, textured" \
  --composition "wide scene, boat lower left, lighthouse upper right, layered pages as waves" \
  --palette "muted teal, warm amber, off-white, deep navy" \
  --lighting "soft diffused daylight" \
  --constraints "no text, no logos, no diagram elements" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/editorial-paper-boat.png
```

**Best for:** cultural commentary, opinion essays, modern life, solitude/exploration themes

---

## 2. Muted literary watercolor

Soft, painterly washes with visible brushwork. Ideal for nature writing, season essays, memory pieces, and introspective themes.

**Core formula:**
```
Muted watercolor illustration, [scene], soft brushstrokes, gentle light, quiet mood, painterly texture, generous negative space
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Muted watercolor illustration, an empty park bench in late autumn afternoon, golden leaves scattered on the path, two small blurred figures walking in the distance, soft brushstrokes, gentle side light, quiet nostalgic mood, generous negative space" \
  --use-case illustration-story \
  --style "muted watercolor illustration, painterly texture, soft brushwork" \
  --composition "bench off-center, path leading into soft-focus distance, airy background" \
  --palette "ochre, muted orange, sage green, soft gray-blue" \
  --lighting "golden hour, soft diffused" \
  --constraints "no text, no hard edges, no photorealism" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/literary-watercolor-bench.png
```

**Best for:** nature essays, season memory, slow living, introspection

---

## 3. Mixed-media editorial collage

Overlapping photographs, torn paper, handwritten notes, and bold type. Great for brand narratives, cultural essays, and mood-driven articles where you want a tactile, magazine-page feel.

**Core formula:**
```
Editorial mixed-media collage, [theme], overlapping photos with torn edges, handwritten annotations, bold headline, textured paper background, print magazine aesthetic
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Editorial mixed-media collage about 'The Future of Reading'. 4 to 6 overlapping photos with torn-paper edges, handwritten annotations in black ink, one bold centered headline reading EXACT VERBATIM 'The Future of Reading'. Print magazine aesthetic, textured off-white paper background, muted warm palette, no watermark" \
  --use-case illustration-story \
  --style "editorial mixed-media collage, print magazine aesthetic, torn paper, handwritten notes" \
  --composition "asymmetric grid, headline centered, overlapping photo layers" \
  --palette "warm off-white paper, muted terracotta, dusty teal, black ink" \
  --text "The Future of Reading" \
  --size 2k-landscape \
  --quality high \
  --out output/gpt-image-2/editorial-collage-reading.png
```

**Best for:** brand narrative, cultural essays, magazine-style articles

---

## 4. Minimal literary still life

A quiet, object-driven scene with symbolic props. Good when the essay centers on a single idea or object.

**Core formula:**
```
Minimal literary still life, [symbolic objects], soft shadows, restrained palette, contemplative mood, generous negative space
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Minimal literary still life, a single open notebook, a half-empty coffee cup, and a pair of reading glasses on a wooden table, soft morning light from the left, restrained warm palette, contemplative quiet mood, generous negative space, no text" \
  --use-case illustration-story \
  --style "minimal literary still life, soft realistic illustration, quiet mood" \
  --composition "objects grouped lower left, large empty space above" \
  --palette "warm wood tones, cream, soft gray, muted amber" \
  --lighting "soft morning side light, gentle shadows" \
  --constraints "no text, no clutter" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/literary-still-life.png
```

**Best for:** personal essays, writing-about-writing, reflective pieces

---

## General tips

1. **Lead with mood, not facts.** Editorial essay illustrations should feel like the article, not explain it.
2. **Use visual metaphors.** Paper boats, empty chairs, open windows, lighthouses — abstract nouns become concrete images.
3. **Avoid text unless the image is a collage.** Most essay illustrations work better without words.
4. **Prefer `landscape` or `wide` sizes** for article headers; use `square` for inline thumbnails.
5. **For CJK essays,** gpt-image-2 can render Chinese text if needed, but essay illustrations usually benefit from no text.
6. **When the user's brief already specifies a palette, medium, or atmosphere, drop the inspirational defaults and keep only the structural guardrails.**
