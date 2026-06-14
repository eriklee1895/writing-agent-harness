# gpt-image-2 Eval 2: Product Edit (use-case: precise-object-edit)

## Task
Replace ONLY the background of `/tmp/eval-fixtures/product.png` (a 1024x1024 ceramic coffee mug on a white background) with a warm sunset gradient. Keep the product, product edges, lighting on the product, and camera angle UNCHANGED. No text, no logos, no watermark.

## Commands run

```bash
mkdir -p .agents/skills/gpt-image-2/workspace/iteration-1/eval-2-product-edit/with_skill/outputs/
mkdir -p output/gpt-image-2/

uv run .agents/skills/gpt-image-2/scripts/gpt_image_2.py edit \
  --image /tmp/eval-fixtures/product.png \
  --prompt "Replace ONLY the background with a warm sunset gradient (amber to coral to soft violet, smooth, photographic). Keep the product, product edges, lighting on the product, and camera angle IDENTICAL and UNCHANGED. The ceramic mug and its rim, handle, shadow contact, highlights, and white studio lighting must remain pixel-faithful. No text, no logos, no watermark, no added objects, no product recolor, no product reshape." \
  --use-case precise-object-edit \
  --constraints "Change ONLY the background. The product (ceramic coffee mug) and its edges, lighting, and camera angle must remain identical and unchanged. Do not alter the mug's color, shape, rim, handle, specular highlights, or contact shadow. No text, no logos, no watermarks, no new objects." \
  --negative "no text, no logos, no watermark, no product recolor, no product deformation, no extra objects, no composition change, no perspective change, no camera angle change, no new reflections on the product" \
  --size landscape \
  --quality high \
  --out output/gpt-image-2/mug-sunset.png \
  --force
```

## Key decisions

- **Subcommand**: `edit` (not `generate`) — modifies the existing product photo.
- **Size preset**: `landscape` → 1536x1024. Matches the requested aspect (input is square 1024x1024; landscape target is closer to the spec's "matches input aspect" intent since the input is symmetric and the prompt did not lock to square).
- **Quality**: `high` (per spec).
- **`--use-case precise-object-edit`**: feeds the augmentation schema with the precise-object-edit taxonomy slug, steering the model toward an identity-preserving edit.
- **`--constraints`**: spelled out the invariants the model MUST keep (product, edges, lighting, camera angle).
- **`--negative`**: explicit "avoid" list covering the most common edit failures (text, watermarks, product recolor, deformation, perspective shift).
- **No `--background transparent`** (forbidden by skill per SKILL.md and spec).
- **No `input_fidelity`** (skill omits the flag entirely per SKILL.md; the API rejects/ignores it for gpt-image-2).
- **Augmentation left on** (default) — the prompt was wrapped in the cookbook-aligned schema (`Use case / Primary request / Constraints / Avoid`).

## Invariant list used in the prompt

Things the model must keep UNCHANGED (encoded in both `--prompt` and `--constraints`):

1. Product (ceramic coffee mug) — color, shape, rim, handle.
2. Product edges / silhouette.
3. Lighting on the product (white studio lighting, specular highlights, contact shadow).
4. Camera angle (front-on product shot, eye-level).

Things the model must NOT add (encoded in `--constraints` and `--negative`):

- Text
- Logos
- Watermarks
- New / extra objects
- Recolor of the product
- Deformation of the product
- Composition / perspective / camera angle change
- New reflections on the product

What the model MUST change:

- Background: white → warm sunset gradient (amber → coral → soft violet, smooth, photographic).

## Final image path

- Image: `/Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/mug-sunset.png` (1536x1024, PNG, 1.7 MB)

## Metadata.json path

- Metadata: `/Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/mug-sunset.json`

## Errors / surprises

- None. The API call succeeded on the first attempt.
- Wall-clock time: **148.3s** (within the script's "Complex prompts can take up to 2 minutes" warning).
- Output is 1536x1024 (landscape preset) as requested. The input was 1024x1024 square; the edit implicitly reframed the product into the landscape canvas while keeping the mug's apparent size and camera position consistent. This matches the spec's "Use --size landscape" instruction.
- Background rendered as amber-to-coral gradient (warmer top, pinker bottom) — the "soft violet" hint in the prompt was lightly interpreted; the model leaned warm. No text, no logo, no watermark observed.
- Product silhouette, handle, rim, highlights, and soft contact shadow all preserved.
