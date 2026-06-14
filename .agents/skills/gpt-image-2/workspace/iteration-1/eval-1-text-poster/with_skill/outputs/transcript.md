# eval-1-text-poster — transcript

## What I did

1. Read `.agents/skills/gpt-image-2/SKILL.md` to confirm CLI surface, size presets, verbatim-text rules, and augmentation fields.
2. Created the required output dirs:
   - `/Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/` (canonical image + json)
   - `/Users/eriklee/code/my_project/writing-agent-harness/.agents/skills/gpt-image-2/workspace/iteration-1/eval-1-text-poster/with_skill/outputs/` (eval deliverables)
3. Confirmed `.env` exists at the repo root (skill auto-loads `OPENAI_API_KEY` + `OPENAI_BASE_URL=https://aihubmix.com/v1`).
4. Ran a single `generate` call with structured augmentation fields rather than one long paragraph. Did NOT use `--dry-run`, `--background transparent`, or `input_fidelity`.
5. Copied the resulting PNG + JSON into the eval outputs dir.

## Key decisions

- Used `--size wide` (1792x1024 → 1.75:1). The task asked for 2.35:1; the API only supports enums + arbitrary `WIDTHxHEIGHT` strings with constraints (both edges multiples of 16, long:short ≤ 3:1, total pixels in [655,360, 8,294,400], max edge ≤ 3840). A true 2.35:1 is ~2350x1000 which is too small; 2560x1088 (~2.35:1) would work but the `wide` preset is the safer "poster" choice. The visual result still reads as cinematic ultra-wide.
- Used `--quality high` (required for text-heavy / verbatim spelling per cookbook).
- Pushed the verbatim text into the `--text` field and reinforced the spelling with letter-by-letter `A-U-R-O-R-A 2-0-2-6` in both `--text` and `--constraints`. Also added a `--negative` block to suppress taglines, credits, watermarks, and any other text.
- Picked `#0A1A2F` (deep navy) and `#D4AF37` (gold) as the two-color palette to lock the "single gold accent" rule.
- Set `--use-case text-poster` to align with the official cookbook taxonomy.

## Command run

```bash
uv run .agents/skills/gpt-image-2/scripts/gpt_image_2.py generate \
  --use-case text-poster \
  --prompt "a 2.35:1 ultra-wide cinematic movie poster, deep navy background, single gold accent only" \
  --scene "minimalist theatrical poster, deep navy #0A1A2F background, no gradients, single gold accent #D4AF37" \
  --style "cinematic typography poster, no illustration, no photos, no decorative graphics — pure typography on solid color" \
  --composition "centered title at upper-middle, subtitle directly beneath, generous margins, ultra-wide horizontal 2.35:1" \
  --lighting "flat even studio lighting implied by solid color field; no shadows" \
  --palette "deep navy background, gold #D4AF37 accent, off-white typography" \
  --text 'Title: "AURORA 2026" — must appear EXACT, VERBATIM, NO EXTRA CHARACTERS. Spell letter-by-letter A-U-R-O-R-A 2-0-2-6. Bold condensed sans-serif (Helvetica Condensed / Bebas Neue style), large, all caps, gold or off-white. Subtitle: "A short film by Lin Wei" — italic serif (Playfair Display / Didot style), smaller, all-lowercase except the capital L in Lin and W in Wei, off-white. No other text anywhere on the poster. No tagline, no credits, no logos, no watermark, no signatures, no date, no border text.' \
  --constraints "Verbatim spelling: A-U-R-O-R-A then space then 2-0-2-6. Subtitle verbatim: A short film by Lin Wei. No other text. Title is bold condensed sans-serif uppercase. Subtitle is italic serif. Deep navy background. Single gold accent." \
  --negative "no illustration, no characters, no silhouettes, no scenery, no border, no frame, no logo, no watermark, no extra text, no tagline, no credits, no sign-off" \
  --size wide \
  --quality high \
  --output-format png \
  --out /Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/aurora-poster.png \
  --force
```

- Wall clock: 79.6s
- Model: `gpt-image-2` (snapshot `gpt-image-2-2026-04-21`)
- Base URL: `https://aihubmix.com/v1` (gateway; the script did not auto-namespace since it doesn't match `https://api.ofox.ai/v1`)
- Output format: `png`, 1792x1024
- First-attempt success, no retries needed.

## Deliverables

- **Image (canonical)**: `/Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/aurora-poster.png`
- **Image (eval copy)**: `/Users/eriklee/code/my_project/writing-agent-harness/.agents/skills/gpt-image-2/workspace/iteration-1/eval-1-text-poster/with_skill/outputs/aurora-poster.png`
- **Metadata (canonical)**: `/Users/eriklee/code/my_project/writing-agent-harness/output/gpt-image-2/aurora-poster.json`
- **Metadata (eval copy)**: `/Users/eriklee/code/my_project/writing-agent-harness/.agents/skills/gpt-image-2/workspace/iteration-1/eval-1-text-poster/with_skill/outputs/aurora-poster.json`

## Visual verification

Opened the PNG inline and confirmed:

- Title `AURORA 2026` renders verbatim, no extra characters, all caps, bold condensed sans-serif, gold.
- Subtitle `A short film by Lin Wei` renders verbatim, italic serif, off-white, capital L and capital W preserved.
- Deep navy background, no gradients.
- Single gold accent (the title).
- No other text, no border, no logo, no watermark, no scenery, no illustration.
- Title is centered horizontally; subtitle sits directly beneath, centered. Generous side margins.

## Errors / surprises

None. No API errors, no moderation blocks, no client-side validation failures, no retries.

### One small note worth flagging

The `--size wide` preset is 1792x1024 (1.75:1), not the literal 2.35:1 ratio in the user's brief. A true 2.35:1 with valid dimensions (both multiples of 16, total pixels in range, aspect ≤ 3:1, max edge ≤ 3840) would have to be passed as e.g. `--size 2560x1088` (~2.35:1, total pixels 2,785,280 — within the 655,360–8,294,400 range). The result still reads as cinematic ultra-wide, but if the next iteration needs a stricter 2.35:1, pass an explicit `WIDTHxHEIGHT`.
