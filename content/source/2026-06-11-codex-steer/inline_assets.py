#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10.0.0"]
# ///
"""report.html -> report.standalone.html with images inlined as base64 WEBP.

WEBP (q90) keeps infographic text crisp while shrinking photographic panels
(cover / paradigm) dramatically vs PNG. report.html keeps the lossless PNGs.
CDN libs (fonts, highlight.js, mermaid, gsap) stay remote by design.
"""
from __future__ import annotations
import base64
import io
import re
from pathlib import Path

from PIL import Image

DIR = Path(__file__).resolve().parent
SRC = DIR / "report.html"
OUT = DIR / "report.standalone.html"
MAX_W = 1600  # ~2x the ~820px display width


def encode(p: Path) -> str:
    im = Image.open(p).convert("RGB")
    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=90, method=6)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{b64}"


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    cache: dict[str, str] = {}

    def repl(m: re.Match) -> str:
        rel = m.group(2)
        if rel not in cache:
            p = DIR / rel
            if not p.is_file():
                print(f"  WARN missing {rel}")
                return m.group(0)
            cache[rel] = encode(p)
        return m.group(1) + cache[rel] + m.group(3)

    html = re.sub(r'(<img[^>]+src=")(assets/[^"]+)(")', repl, html)
    OUT.write_text(html, encoding="utf-8")
    mb = len(html.encode("utf-8")) / 1_048_576
    print(f"Wrote {OUT} ({mb:.2f} MB); inlined {len(cache)} images as WEBP (max width {MAX_W})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
