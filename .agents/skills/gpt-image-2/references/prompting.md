# Prompting rules for gpt-image-2

These rules are distilled from the official OpenAI cookbook (`image-gen-models-prompting-guide`) and the Image API guide. Follow them for any non-trivial prompt.

## Verbatim text rendering

gpt-image-2's strongest differentiator is in-image text. The cookbook rules:

1. **Wrap literal text in quotes or ALL CAPS.** Declare typography: font style, size, color, placement. Example:
   > Title: "AURORA 2026", bold sans-serif, top-center, white on dark navy.
2. **For tricky words (brand names, uncommon spellings), spell letter-by-letter.** Mention "EXACT, verbatim, no extra characters".
3. **For small text, dense labels, multi-font layouts, infographics** → `quality=high` and a landscape size. Use a `WIDTHxHEIGHT` (e.g. `2048x1152`) instead of `auto` so the model has more pixels for legibility.
4. **For complex multi-section prompts, use short labeled segments or line breaks** instead of one long paragraph. Each labeled segment becomes a coherent region.
5. The model can still struggle with precise placement and clarity. Do not promise pixel-perfect text. If a label is wrong, tighten the prompt and re-run.

CJK-specific typography is not in the official cookbook. Apply the same rules and add font-family hints (e.g. `"Source Han Sans CN"`, `"Noto Sans CJK SC"`, `"LXGW WenKai"`) — these are community-validated, not officially endorsed.

## Structure

Recommended order: `Scene/backdrop → Subject → Details → Constraints`. Use the augmentation flags in the skill to enforce this:

```
--scene "alpine lake at dawn, light mist over water"
--subject "small wooden cabin with a lit window"
--style "photorealistic, 35mm photography, slight film grain"
--composition "wide landscape, cabin off-center right, low horizon"
--lighting "soft golden hour, warm interior glow"
--constraints "no text, no logos, no watermark"
--negative "no people, no birds, no text"
```

Skip empty fields; the augmentation step only emits lines you actually filled.

## Composition hints

Use camera/composition language for photorealism. Examples:

- `wide-angle, low-angle, volumetric light rays through fog`
- `eye-level close-up, shallow depth of field, bokeh background`
- `top-down flat-lay, even soft lighting, no harsh shadows`

For infographics and slides, explicitly name the regions: `left column: legend; center: main chart; right column: callouts`.

## Style transfer (edit mode)

When you pass reference images for style only, write the prompt so the model knows the references are style guidance, not literal subjects. Example:

> Use the provided reference image ONLY for style guidance (palette, line quality, brushwork). Do not copy its literal subject matter. Generate a totally new scene: ...

## Edit invariants

For edits, repeat invariants in every iteration prompt to reduce drift. Example:

> Replace ONLY the background with a warm sunset gradient. Keep the product, the product edges, the lighting on the product, and the camera angle UNCHANGED.

If the model starts changing things you wanted to preserve, copy the invariant list verbatim from a previous successful prompt and add it to the new one.

## Use-case taxonomy

The skill does not bundle domain presets. Pick a slug from this list and pass it via `--use-case`:

- `photorealistic-natural` — candid/editorial lifestyle scenes
- `product-mockup` — catalog, packaging, merch
- `ui-mockup` — app/web wireframes (state the desired fidelity)
- `infographic-diagram` — diagrams, posters, knowledge cards with text
- `logo-brand` — vector-friendly mark exploration
- `illustration-story` — comics, children's book, narrative scenes
- `stylized-concept` — style-driven concept art, 3D renders
- `historical-scene` — period-accurate / world-knowledge scenes

The slug is informational; the actual visual direction comes from `--style`, `--scene`, and `--composition`.

## What NOT to do

- Don't ask for a transparent background — gpt-image-2 rejects it.
- Don't ask for a specific font by name unless you also say it must be EXACT (the model will interpret the name as a style hint, not a hard requirement).
- Don't pack more than ~4 visual ideas into one prompt. Split into multiple generations.
- Don't rely on `input_fidelity` — it's disabled on gpt-image-2.
- Don't promise the user "this will be deterministic" — gpt-image-2 has temperature-based variation by design.
