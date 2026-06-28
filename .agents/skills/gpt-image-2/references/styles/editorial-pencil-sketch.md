# Editorial pencil-sketch workflow

A warm, hand-drawn illustration style: graphite/ink line work on white paper, lightly tinted with muted watercolor washes. It feels like a designer's sketchbook — rational but human, airy but structured. Great for visualizing AI workflows, creative processes, editorial explainers, and human-machine collaboration.

This preset provides **scaffolding, not a mold**: it defaults to a left-to-right workflow layout and a light sketchbook palette, but the model should keep only the structural guardrails when the user's brief already carries a strong visual concept.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `hand-drawn pencil sketch`, `ink line art`, `light watercolor washes`, `sketchbook aesthetic`, `illustration on white paper` |
| Background | `clean white background`, `generous negative space`, `no dark vignette` |
| Composition | `left-to-right process flow`, `isometric-ish layout`, `storyboard panels`, `thumbnail grid`, `concept map` |
| Subject | `human and friendly robot collaborating`, `designer at desk`, `small rounded robot assistant`, `creative workspace` |
| Hard avoids | `photorealism`, `dark background`, `neon colors`, `heavy shadows`, `3D render look`, `vector flat illustration` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Dimension | Default direction |
|---|---|
| Color | `muted pastel palette`, `soft blue`, `sage green`, `terracotta orange`, `lavender accents`, `graphite gray line work` |
| Mood | `warm editorial illustration`, `intellectual but cozy`, `maker-space mood`, `creative process visualization` |
| Props | `magnifying glass`, `scissors`, `sticky notes`, `timeline`, `storyboard panels`, `mood board`, `clapperboard` |

> **Override rule:** If the user describes a different palette, medium, or atmosphere, drop the inspirational defaults and keep only the structural template (white background, workflow composition, hard avoids).

## Reusable prompt template

```text
A hand-drawn editorial illustration in pencil sketch style with light watercolor washes on a clean white background.

Scene: [what is happening — e.g. an AI-human writing workflow, a video editing pipeline, a research process].
Composition: [how the scene is laid out — e.g. left-to-right flow, isometric storyboard, central workspace surrounded by thumbnails].
Details: [list key props and actors — e.g. writer, small friendly robot, sticky notes, timeline, storyboard panels, magnifying glass].
Colors (default; override if brief specifies): muted pastel accents — soft blue, sage green, terracotta orange, lavender; line work remains graphite gray.
Mood (default; override if brief specifies): thoughtful, creative, human-AI teamwork, airy and uncluttered.
Avoid: photorealism, dark background, neon colors, heavy shadows, 3D render look.
```

## Example: AI writing workflow (full preset)

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A hand-drawn editorial illustration in pencil sketch style with light watercolor washes on a clean white background. A writer and a small friendly robot sit side by side at a wooden desk covered with sticky notes, a timeline, and storyboard panels. Left-to-right creative workflow. Muted pastel accents: soft blue, sage green, terracotta orange, lavender. Graphite line work. Thoughtful, airy, human-AI collaboration mood." \
  --use-case illustration-story \
  --style "hand-drawn pencil sketch, ink line art, light watercolor washes, sketchbook aesthetic" \
  --composition "isometric-ish layout, left-to-right workflow, desk as central stage" \
  --palette "white paper, graphite gray lines, soft blue, sage green, terracotta orange, lavender" \
  --lighting "soft even daylight, no harsh shadows" \
  --constraints "clean white background, no photorealism, no 3D render look" \
  --negative "dark background, neon colors, heavy shadows, photorealism, 3D render" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/sketch-workflow.png
```

## Example: user already gave a strong style (structure only)

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "An AI writing workflow shown as a dark charcoal sketch on cream kraft paper, bold ink strokes, single warm amber highlight. Left-to-right process flow, writer and robot at a desk, sticky notes and timeline. No photorealism, no 3D render, no neon colors." \
  --use-case illustration-story \
  --composition "left-to-right workflow, desk as central stage" \
  --constraints "clean background, no photorealism, no 3D render look" \
  --negative "photorealism, 3D render, neon colors" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/sketch-workflow-override.png
```

## Variations

- **Cooler / more technical**: replace `sage green, terracotta orange` with `slate blue, pale cyan, silver gray`; keep the line work dominant.
- **Warmer / more personal**: add `warm off-white paper`, `sepia ink`, `honey yellow highlights`.
- **More diagram, less scene**: emphasize `concept map`, `labeled nodes`, `dashed arrows`, `small icons`.
- **Simpler / hero image**: reduce props to one figure + one large object, keep 60%+ white space.

## Tips

1. Start with the medium (`hand-drawn pencil sketch with watercolor washes`) before describing the scene — it anchors the model early.
2. Explicitly request `clean white background` and `no dark vignette`; gpt-image-2 sometimes defaults to textured gray backdrops for sketches.
3. Use `--quality high` when the image includes small labels, icons, or dense process details.
4. For text labels inside the illustration, wrap them in quotes and use `--text` plus `--quality high`. See [prompting.md](../prompting.md#verbatim-text-rendering) for the verbatim-text rules.
5. When the user's brief already contains a strong palette or atmosphere, drop the inspirational defaults; keep only the structural guardrails.
