#!/usr/bin/env python3
"""Edit product photo: replace background with warm sunset gradient.

Uses the OpenAI Python SDK's client.images.edit() method with gpt-image-2.
Input: /tmp/eval-fixtures/product.png (1024x1024 ceramic mug on white)
Output: a sunset-gradient version, product/edges/lighting/camera unchanged.
"""
import os
import sys
from pathlib import Path

# Load .env manually (no dotenv dep)
env_path = Path("/Users/eriklee/code/my_project/writing-agent-harness/.env")
for line in env_path.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, val = line.split("=", 1)
    os.environ.setdefault(key.strip(), val.strip())

from openai import OpenAI

INPUT = "/tmp/eval-fixtures/product.png"
FINAL_OUT = "/Users/eriklee/code/my_project/writing-agent-harness/output/baseline/mug-sunset.png"
HERE_OUT = "/Users/eriklee/code/my_project/writing-agent-harness/.agents/skills/gpt-image-2/workspace/iteration-1/eval-2-product-edit/without_skill/outputs/mug-sunset.png"

# Prompt: replace ONLY the background. Preserve the product, edges, lighting, camera angle.
# Explicit anti-instructions: no text, no logos, no watermark.
PROMPT = (
    "Replace ONLY the background of this product photo with a warm sunset "
    "gradient sky (deep orange near the horizon fading to soft pink and "
    "lavender above). The ceramic mug product, its shape, edges, surface "
    "details, original lighting, reflections, shadows on the mug, and the "
    "camera angle must remain completely unchanged. Keep the same product "
    "framing and proportions. Do not add any text, logos, watermarks, or "
    "extra objects."
)

client = OpenAI()  # picks up OPENAI_API_KEY and OPENAI_BASE_URL from env

with open(INPUT, "rb") as f:
    result = client.images.edit(
        model="gpt-image-2",
        image=f,
        prompt=PROMPT,
        size="1536x1024",
        quality="high",
        n=1,
    )

# New SDK returns b64_json (or url). Save bytes to both destinations.
image_bytes = result.data[0].b64_json
import base64
png_bytes = base64.b64decode(image_bytes) if image_bytes else None
if png_bytes is None and hasattr(result.data[0], "url") and result.data[0].url:
    import urllib.request
    png_bytes = urllib.request.urlopen(result.data[0].url).read()

if png_bytes is None:
    print("ERROR: no image bytes returned", file=sys.stderr)
    print("result:", result, file=sys.stderr)
    sys.exit(1)

for path in (FINAL_OUT, HERE_OUT):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png_bytes)
    print(f"wrote {path} ({len(png_bytes)} bytes)")
