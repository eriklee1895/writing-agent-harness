# hand-drawn-tech-editorial（手绘科技随笔）

A warm hand-drawn tech illustration style: colored pencil and crayon texture on off-white or cream paper, loose organic linework, slight paper grain. The scene is usually a cozy desk or workspace with anthropomorphic computers, robots, terminal windows, coffee mugs, notebooks, potted plants, sticky notes, and small flowchart doodles. It feels like an editorial sketch for a tech essay: rational but human, structured but handcrafted.

Good for AI tool comparisons, agent workflows, tech essays, coding companions, and productivity notes.

> This preset provides **scaffolding, not a mold**: it defaults to a split-screen or facing composition, warm-orange vs cool-blue palette, and friendly device characters, but the model should keep only the structural guardrails (hand-drawn paper texture, avoid corporate flat/glossy) when the user's brief already carries a strong visual concept.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `colored pencil and crayon texture on paper`, `hand-drawn editorial illustration`, `loose organic linework`, `slight paper grain` |
| Background | `warm off-white or cream paper`, `cozy desk scene`, `generous negative space` |
| Composition | `split-screen or facing composition`, `two friendly computer characters across a desk`, `left warm / right cool` |
| Subject | `anthropomorphic monitor or device with a friendly face`, `small robot assistant`, `laptop with chat bubbles or code` |
| Details | `coffee mug`, `notebook`, `potted plant`, `floating sticky notes`, `small flowchart doodles`, `binary code snippets as paper notes` |
| Hard avoids | `photorealism`, `glossy digital rendering`, `corporate flat vector illustration`, `heavy shadows`, `neon colors` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Dimension | Default direction |
|---|---|
| Color | Warm orange/cream/terracotta on the left, cool blue/slate on the right; graphite or dark brown line work |
| Mood | Warm editorial illustration, friendly collaboration, tech essay, handmade warmth |
| Props | Coffee mug, notebook, potted plant, sticky notes, small robot, flowchart doodles |

> **Override rule:** If the user describes a different palette, medium, or atmosphere, drop the inspirational defaults and keep only the structural template (hand-drawn paper texture, optional split-screen layout, avoid corporate flat/glossy).

## Reusable prompt template

```text
A warm hand-drawn tech editorial illustration in colored pencil and crayon on cream paper, loose organic linework, slight paper grain.

Scene: [what is happening — e.g., Claude and Codex collaborating at a desk, an agent and a human writing together].
Composition: [how the scene is laid out — e.g., split-screen facing composition, central workspace, two anthropomorphic computers across from each other].
Details: [key props and characters — e.g., warm-orange monitor holding a coffee mug, cool-blue monitor showing code, small robot assistant, floating binary sticky notes, small flowcharts on the wall].
Colors (default; override if brief specifies): warm orange/cream/terracotta on the left, cool blue/slate on the right, graphite line work.
Mood (default; override if brief specifies): warm, friendly, editorial tech essay, handmade warmth.
Avoid: photorealism, glossy digital rendering, corporate flat vector, heavy shadows, neon colors.
```

## Example: Claude vs Codex (full preset)

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A warm hand-drawn tech editorial illustration in colored pencil and crayon on cream paper. Two friendly anthropomorphic computer monitors face each other across a split-screen desk. Left: warm orange monitor with a Claude asterisk logo, holding a coffee mug, notebook and potted plant nearby. Right: cool blue monitor with a Codex cloud logo, screen showing code, small robot assistant, dark coffee mug. Binary-code sticky notes float between them like messages. Small flowcharts hang on each wall. Loose organic linework, slight paper grain, generous negative space." \
  --use-case illustration-story \
  --style "colored pencil and crayon texture on paper, hand-drawn editorial illustration, loose organic linework, slight paper grain" \
  --composition "split-screen facing composition, two anthropomorphic computers across a desk, left warm / right cool" \
  --palette "warm off-white paper, orange/cream/terracotta left, cool blue/slate right, graphite line work" \
  --lighting "soft even daylight, no harsh shadows" \
  --constraints "cozy desk scene, generous negative space" \
  --negative "photorealism, glossy digital rendering, corporate flat vector, heavy shadows, neon colors" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/hand-drawn-tech-claude-codex.png
```

## Variations

- **More diagram / less scene**: keep the hand-drawn texture but emphasize `labeled nodes`, `dashed arrows`, `short labels on sticky notes`.
- **Warmer / more personal**: add `warm off-white paper`, `sepia ink`, `honey yellow highlights`, reduce tech props.
- **Cooler / more technical**: replace warm orange with `slate blue / silver gray`, let line work dominate, good for developer-tool themes.
- **Single character / hero image**: reduce to one large anthropomorphic device + one small robot + 60%+ negative space.

## Tips

1. Anchor the medium first (`colored pencil and crayon texture on paper`) before describing the scene — it locks the style early.
2. Explicitly request `loose organic linework` and `slight paper grain`; otherwise the model may drift toward polished digital illustration.
3. For text inside the image, wrap it in quotes and use `--text` plus `--quality high`. See [prompting.md](../prompting.md#verbatim-text-rendering). But this style prefers short words, icons, or binary numbers over long paragraphs.
4. When using `--image` as style reference, tell the model to use it only for palette, line quality, and spacing, not to copy the literal subject.
