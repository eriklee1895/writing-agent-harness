# AURORA 2026 Poster — Baseline (no skill)

## What I did

1. Wrote a self-contained Python script `gen.py` that:
   - Parses `OPENAI_API_KEY` and `OPENAI_BASE_URL` out of the repo's `.env` directly (no `dotenv` / `python-dotenv` dependency — just a tiny regex loader).
   - Calls the OpenAI Python SDK with `OpenAI(api_key=..., base_url=...)`.
   - Invokes `client.images.generate(model="gpt-image-2", prompt=..., size="1792x1024", quality="high", n=1)`.
   - Decodes `b64_json` from the response and writes the bytes to disk.
   - Has a fallback path for the rare case the proxy returns a URL instead of base64.
2. Ran the script via `uv run --with openai python3 gen.py` (no venv, no `pip`).
3. Verified the output is a valid 1792x1024 PNG (≈2.35:1, exactly the requested `gpt-image-2` size).
4. Visually confirmed the text with vision:
   - Title: `AURORA 2026` (bold condensed sans-serif, all caps, centered)
   - Subtitle: `A short film by Lin Wei` (italic serif, smaller, centered below)
   - Background: solid deep navy
   - Gold accent: a single thin gold horizontal rule with a small gold star at center
   - No extra text anywhere — no tagline, no credits, no borders

## Final image path

- `/Users/eriklee/code/my_project/writing-agent-harness/output/baseline/aurora-poster.png` (276,196 bytes, 1792x1024 PNG)

## Errors / surprises

- None. The call succeeded on the first try. No retries, no parameter issues.
- Did not use `input_fidelity` (per instructions — gpt-image-2 disables it).
- Did not use `background="transparent"` (per instructions — gpt-image-2 rejects it).
- The letter-by-letter hint (`A-U-R-O-R-A`) in the prompt, combined with `quality="high"`, gave clean spelling on the first generation.

## Files in this output dir

- `gen.py` — the generation script (the boilerplate I would have otherwise copy-pasted from a skill)
- `transcript.md` — this file
