# Editorial pencil-sketch workflow

A warm, hand-drawn illustration style: graphite/ink line work on white paper, lightly tinted with muted watercolor washes. It feels like a designer's sketchbook — rational but human, airy but structured. Great for visualizing AI workflows, creative processes, editorial explainers, and human-machine collaboration.

## Style signature

| Dimension | Prompt vocabulary |
|---|---|
| Medium | `hand-drawn pencil sketch`, `ink line art`, `light watercolor washes`, `sketchbook aesthetic`, `illustration on white paper` |
| Color | `muted pastel palette`, `soft blue`, `sage green`, `terracotta orange`, `lavender accents`, `graphite gray line work` |
| Background | `clean white background`, `generous negative space`, `no dark vignette` |
| Composition | `isometric-ish layout`, `left-to-right process flow`, `storyboard panels`, `thumbnail grid`, `concept map` |
| Subject | `human and friendly robot collaborating`, `designer at desk`, `small rounded robot assistant`, `creative workspace` |
| Props | `magnifying glass`, `scissors`, `sticky notes`, `timeline`, `storyboard panels`, `mood board`, `clapperboard` |
| Mood | `warm editorial illustration`, `intellectual but cozy`, `maker-space mood`, `creative process visualization` |
| Avoid | `photorealism`, `dark background`, `neon colors`, `heavy shadows`, `3D render look`, `vector flat illustration` |

## Reusable prompt template

```text
A warm editorial illustration in hand-drawn pencil sketch style with light watercolor washes on a clean white background.

Scene: [what is happening — e.g. an AI-human writing workflow, a video editing pipeline, a research process].
Composition: [how the scene is laid out — e.g. isometric storyboard, left-to-right flow, central workspace surrounded by thumbnails].
Details: [list key props and actors — e.g. writer, small friendly robot, sticky notes, timeline, storyboard panels, magnifying glass].
Colors: muted pastel accents only — soft blue, sage green, terracotta orange, lavender; line work remains graphite gray.
Mood: thoughtful, creative, human-AI teamwork, airy and uncluttered.
Avoid: photorealism, dark background, neon colors, heavy shadows, 3D render look.
```

## Example: AI writing workflow

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "A warm editorial illustration in hand-drawn pencil sketch style with light watercolor washes on a clean white background. A writer and a small friendly robot sit side by side at a wooden desk covered with sticky notes, a timeline, and storyboard panels. Isometric-ish layout, left-to-right creative workflow. Muted pastel accents: soft blue, sage green, terracotta orange, lavender. Graphite line work. Thoughtful, airy, human-AI collaboration mood." \
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

## Example: video editing pipeline

```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Hand-drawn pencil sketch editorial illustration, light watercolor washes, clean white background. A video editor and a small rounded robot review a timeline on a large monitor. Surrounding the monitor: storyboard thumbnails, a clapperboard, a magnifying glass over a clip, and curved arrows showing the editing flow. Muted pastel accents on a graphite line drawing." \
  --use-case illustration-story \
  --style "hand-drawn pencil sketch, light watercolor washes, sketchbook aesthetic" \
  --composition "central monitor with orbiting thumbnails and arrows" \
  --palette "white paper, graphite gray, soft blue, sage green, terracotta orange" \
  --lighting "soft diffused light" \
  --negative "photorealism, 3D render, dark background, neon" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/sketch-video-pipeline.png
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
