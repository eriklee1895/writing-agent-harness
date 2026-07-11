# Seedream 5.0 Lite — Quick Reference

Lite (`doubao-seedream-5-0-260128`, aliases `lite` / `seedream-lite` / `5-lite`) is **not a parallel product to Pro** — it is a smaller/faster/cheaper sibling in the same 5.0 family, with a strictly narrower capability envelope. Treat it as a fallback mode you opt into for a specific constraint, not a default choice.

This doc exists so `SKILL.md` can stay Pro-focused (where ~95% of this skill's tested capability and documentation lives) without scattering "except on Lite..." caveats through every section. Read this file only when you've decided `--model lite` is the right call per the decision rule below.

## When to actually switch to Lite

Pro is the default because it renders text reliably, supports marker edits, and nails the Chinese-aesthetic/product-photography look that Lite can't match. Lite is faster (~30-60s vs Pro ~95s @ 2K for simple prompts) and cheaper, but the text/marker quality gap is real. Switch only when one of the four constraints below applies:

1. **Fast concept sketches with no text** — Lite ~30–60s vs Pro ~95s. Use for early-stage composition/layout iteration before committing to a Pro final render (a genuinely useful two-tier workflow: Lite for cheap exploration, Pro for the finished asset).
2. **You need >4 MP resolution** — Pro caps at 4 MP (2048×2048-class); Lite goes up to 16 MP. This is the only case where Lite produces something Pro categorically cannot.
3. **You need `--web-search` grounding or `--sequential` storyboard generation** — both are Lite-only API parameters; Pro's API rejects them outright (`tools`, `sequential_image_generation` return 400 on Pro).
4. **Large cheap batches of non-text visuals** — Lite ¥0.22/image vs Pro ¥0.30–0.60/image, and you can tolerate weaker texture/material fidelity.

If none of these four apply, stay on Pro.

## Pixel range & size shortcuts

Lite pixel range: **3.7 MP – 16 MP**, aspect ratio ≤16:1. This is a **floor**, not just a ceiling — Lite categorically cannot produce `1K` / `1024²` / `1792×1024` (all below 3.69 MP). If a task needs one of those exact small sizes, Pro is not just preferred, it's the only option.

| Flag | Lite resolution | Pro resolution (for comparison) |
|---|---|---|
| `--square` | 2048×2048 | 1024×1024 |
| `--portrait` | 2048×2732 | 1536×2048 |
| `--landscape` | 2732×1536 | 2048×1152 |
| `--wide` / `--wechat-header` | **not available** (1792×1024 is below Lite's floor) | 1792×1024 |
| `--size 2K/3K/4K` | all supported | 1K/2K only |

## Lite-only CLI flags

```
--web-search      Enable web-search grounding for the prompt (Lite only; Pro's API 400s on this)
--sequential       Generate a coherent multi-image storyboard/sequence in one call (Lite only)
```

## What Lite does NOT have

- **Marker-based local editing is untested on Lite.** Marker editing is fundamentally a client convention (Pillow draws colored rectangles, model reads them visually), not an API-gated Pro feature — Lite will accept the annotated image and attempt the edit, but text-in-box rendering is weaker, cleanup may leave color artifacts, and the 8%/70% size thresholds in marker-editing.md were measured on Pro only. The CLI warns when you pass `--marker-rect` on Lite. For any serious marker edit (title swap, material change, multi-region), use Pro.
- **Weaker text rendering.** Pro's text-reliability table (SKILL.md → "Text rendering") does not transfer to Lite. Expect frequent character errors even on short headlines. If text matters at all, use Pro regardless of resolution needs.
- **Untested prompt-engineering transfer.** Every commitment-language formula, per-person group-photo enumeration trick, anti-detail motion-blur phrasing, and multilingual same-screen recipe in this skill's reference docs (`style-transfer.md`, `photorealism.md`, `multilingual.md`, `text-deep.md`) was empirically validated **on Pro only** (300+ test images). These techniques are plausible-but-unverified on Lite — don't assume they carry over with the same reliability. If you need one of these capabilities and are on Lite for a resolution/cost reason, expect to re-validate empirically rather than trusting the Pro-derived scores.

## Example

```bash
uv run scripts/seedream_image_gen.py generate \
  --model lite --web-search \
  --prompt "Concept sketch: a futuristic urban air-mobility hub with multiple eVTOLs taking off and landing"
```

## Full capability matrix

`uv run scripts/seedream_image_gen.py list-models` prints the live matrix (max reference images, optimize modes, pricing) for both models — the authoritative source when this doc and the script disagree.