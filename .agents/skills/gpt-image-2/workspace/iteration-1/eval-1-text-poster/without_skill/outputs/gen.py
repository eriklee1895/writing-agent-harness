"""Generate an AURORA 2026 movie poster with gpt-image-2 via the OpenAI SDK.

Loads OPENAI_API_KEY and OPENAI_BASE_URL from the project's .env file (no dotenv
dependency — we just parse it ourselves). Saves the resulting PNG to:
  /Users/eriklee/code/my_project/writing-agent-harness/output/baseline/aurora-poster.png
"""

from __future__ import annotations

import base64
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

REPO_ROOT = Path("/Users/eriklee/code/my_project/writing-agent-harness")
ENV_PATH = REPO_ROOT / ".env"
OUTPUT_PATH = REPO_ROOT / "output" / "baseline" / "aurora-poster.png"

PROMPT = (
    "A 2.35:1 ultra-wide cinematic movie poster. "
    "Centered title typography reads EXACTLY, VERBATIM, with NO EXTRA CHARACTERS: "
    "'AURORA 2026'. The title must spell A-U-R-O-R-A, letter by letter, "
    "in bold condensed sans-serif type (Helvetica Condensed / Bebas style), "
    "all caps, very large, centered horizontally. "
    "Directly below the title, in smaller italic serif type, the subtitle reads "
    "EXACTLY: 'A short film by Lin Wei'. "
    "No other text anywhere on the poster. No tagline, no credits, no logos, no borders. "
    "Background is a deep navy color (a single solid deep-navy field). "
    "A single gold accent color used sparingly on one small element (e.g. a thin "
    "gold underline beneath the title, or one small gold star). "
    "Minimalist, modern, elegant film poster. High contrast, sharp typography. "
    "Photorealistic print-quality poster. 1792x1024, 2.35:1 aspect ratio."
)


def load_env(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE per line, ignores blanks and # comments."""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        # Strip surrounding quotes if present
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


def main() -> int:
    load_env(ENV_PATH)

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        print("ERROR: OPENAI_API_KEY missing from .env", file=sys.stderr)
        return 1

    print(f"Using base_url={base_url}")
    print(f"Model: gpt-image-2, size: 1792x1024, quality: high")

    client = OpenAI(api_key=api_key, base_url=base_url)

    try:
        resp = client.images.generate(
            model="gpt-image-2",
            prompt=PROMPT,
            size="1792x1024",
            quality="high",
            n=1,
        )
    except Exception as e:
        # Surface error code + message clearly
        print(f"ERROR from API: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    if not resp.data:
        print("ERROR: empty response data", file=sys.stderr)
        return 3

    item = resp.data[0]
    b64 = item.b64_json
    if not b64:
        # Some proxies return URL instead of base64; fall back to download.
        url = getattr(item, "url", None)
        if url:
            import urllib.request
            print(f"Downloading from URL: {url}")
            with urllib.request.urlopen(url) as f:
                png_bytes = f.read()
        else:
            print("ERROR: no b64_json and no url in response", file=sys.stderr)
            return 4
    else:
        png_bytes = base64.b64decode(b64)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(png_bytes)
    print(f"Wrote {len(png_bytes):,} bytes -> {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
