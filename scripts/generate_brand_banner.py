#!/usr/bin/env -S /Users/eriklee/.local/bin/uv run --python 3.14
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "openai>=1.76.0",
# ]
# ///
"""Generate three brand banner variants for writing-agent-harness README.

Uses gpt-image-2 with fully custom prompts. Reads OPENAI_API_KEY and
OPENAI_BASE_URL from environment or .env file.
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from openai import OpenAI

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "assets"
SIZE = "1200x624"
MODEL = "gpt-image-2"

TAGLINE = "Words with weight, agents with taste."
PROJECT_NAME = "writing-agent-harness"

FOX_CHARACTER = (
    "a small geometric fox mascot character constructed from clean, simple shapes "
    "(circles, triangles, smooth arcs) — cute but not childish, intelligent and warm, "
    "with a subtle glowing presence, sitting alertly beside a small glowing lamp or an open notebook, "
    "one paw resting on the desk, the other holding a pen or stylus"
)

LAYOUT = (
    f"Left side of the banner: the project name '{PROJECT_NAME}' in a refined modern "
    f"sans-serif typeface, prominent. Below it, the tagline '{TAGLINE}' in a smaller "
    f"elegant sans-serif size. Right side: {FOX_CHARACTER}. "
    f"The composition is a polished brand banner — editorial magazine-level typography, "
    f"balanced whitespace, no diagrams, no UI elements, no icons, no arrows."
)

VARIANTS = {
    "dark-warm": {
        "filename": "brand-banner-dark-warm.png",
        "atmosphere": (
            "Deep dark blue-black background (#0a0e17 to #141c2b). Warm amber and golden "
            "geometric light accents — the fox glows with a soft warm amber/golden light, "
            "as if lit by a single desk lamp in a late-night writing session. "
            "The project name in warm off-white (#f5f0e8), the tagline in muted warm gold (#c9a96e). "
            "Subtle golden dust motes or geometric light particles suspended in the dark."
        ),
    },
    "light-paper": {
        "filename": "brand-banner-light-paper.png",
        "atmosphere": (
            "Creamy warm off-white background with subtle paper texture (#faf7f0 to #f0ebe0). "
            "The fox character in warm ochre (#c17a3e) and soft muted blue (#5b7fa5) geometric shapes "
            "with a gentle ink-wash accent. The project name in deep charcoal (#1e1e1e), "
            "the tagline in warm medium gray (#6b5e4f). "
            "Light, airy, like the title page of a well-designed literary journal."
        ),
    },
    "rich-restrained": {
        "filename": "brand-banner-rich-restrained.png",
        "atmosphere": (
            "Deep teal-blue-green background (#0d2b2b to #143838). The fox character in warm "
            "burnished gold (#d4a853), rust-red (#b55a3a), and soft dusty pink (#c4a0a0) "
            "geometric accents. The project name in soft warm white (#f2ede0), "
            "the tagline in muted warm gold (#c9a96e). "
            "Rich, restrained, like the cover of a beautifully typeset hardcover book. "
            "Subtle geometric decorative elements in the corners."
        ),
    },
}


def _read_env_file() -> dict[str, str]:
    """Read key-value pairs from .env in repo root, without logging secrets."""
    env = {}
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return env
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip().strip('"').strip("'")
        env[key.strip()] = val
    return env


def get_config() -> tuple[str, str | None]:
    """Return (api_key, base_url_or_none) from environment or .env."""
    dotenv = _read_env_file()
    api_key = os.getenv("OPENAI_API_KEY") or dotenv.get("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL") or dotenv.get("OPENAI_BASE_URL") or None
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is required. Set it via environment variable or .env file."
        )
    return api_key, base_url


def resolve_model(base_url: str | None) -> str:
    if not base_url:
        return MODEL
    if "api.ofox.ai" in base_url:
        return "openai/gpt-image-2"
    return MODEL


def generate(
    client: OpenAI, model: str, variant_name: str, config: dict
) -> Path:
    prompt = (
        f"A brand banner illustration for the open-source project '{PROJECT_NAME}'. "
        f"{LAYOUT} "
        f"Color atmosphere: {config['atmosphere']} "
        f"Overall feel: {variant_name.replace('-', ' ')} — polished, editorial, "
        f"the bridge between technology and the humanities. "
        f"All text must be rendered clearly and accurately in the image itself. "
        f"Size: {SIZE}."
    )

    print(f"\n🎨 Generating variant: {variant_name}")
    print(f"   Prompt length: {len(prompt)} chars")

    resp = client.images.generate(
        model=model,
        prompt=prompt,
        n=1,
        size=SIZE,
        quality="auto",
    )

    data = resp.data[0]
    if data.b64_json:
        image_bytes = base64.b64decode(data.b64_json)
    elif data.url:
        import urllib.request
        image_bytes = urllib.request.urlopen(data.url).read()
    else:
        raise RuntimeError("No image data in response")

    output_path = OUTPUT_DIR / config["filename"]
    output_path.write_bytes(image_bytes)
    print(f"   ✅ Saved: {output_path}")
    return output_path


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    api_key, base_url = get_config()
    model = resolve_model(base_url)

    print(f"🔑 Base URL: {base_url or '(default OpenAI)'}")
    print(f"🧠 Model:   {model}")

    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    results: dict[str, str] = {}
    for variant_name, config in VARIANTS.items():
        try:
            path = generate(client, model, variant_name, config)
            results[variant_name] = str(path)
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results[variant_name] = f"ERROR: {e}"

    ok = sum(1 for v in results.values() if not v.startswith("ERROR"))
    print(f"\n✅ Done. Generated {ok}/3 variants.")
    return 0 if ok == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
