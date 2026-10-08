"""Regression tests for the origin -> blog sync adapter.

The bug these lock down: `heroImage`/`ogImage` were blanked whenever the cover
file was missing from the *origin* working tree. Image binaries are gitignored,
so a clean checkout legitimately has none of them while the blog still serves
its own committed copy — the sync therefore deleted those fields from published
posts, and hand-repairing them only held until the next sync.

`source_asset_exists` and `asset_exists_in_source_or_destination` deliberately
answer different questions. Both properties are asserted here so that a future
"unify the two checks" refactor fails loudly instead of shipping.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_origin_to_blog.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_origin_to_blog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_origin_to_blog"] = module
    spec.loader.exec_module(module)
    return module


sync = _load_module()


def make_args(**overrides) -> argparse.Namespace:
    defaults = dict(
        blog_root=Path("/tmp/blog"),
        canonical_url="",
        description="",
        draft=None,
        extension="mdx",
        output_dir=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def build_scene(tmp_path: Path, *, origin_has_file: bool, destination_has_file: bool):
    """Return (source_path, destination_assets_dir) for a one-cover article."""
    origin = tmp_path / "origin" / "2026-01-01-demo"
    (origin / "assets").mkdir(parents=True)
    source_path = origin / "index.md"
    source_path.write_text("---\ntitle: Demo\n---\n\nbody\n", encoding="utf-8")
    if origin_has_file:
        (origin / "assets" / "cover.png").write_bytes(b"origin")

    destination_assets = tmp_path / "blog" / "assets" / "2026-01-01-demo"
    destination_assets.mkdir(parents=True)
    if destination_has_file:
        (destination_assets / "cover.png").write_bytes(b"destination")

    return source_path, destination_assets


def render(tmp_path, *, origin_has_file, destination_has_file) -> str:
    source_path, destination_assets = build_scene(
        tmp_path,
        origin_has_file=origin_has_file,
        destination_has_file=destination_has_file,
    )
    meta = {"title": "Demo", "cover": "assets/cover.png"}
    return sync.build_blog_frontmatter(
        meta, "body\n", source_path, make_args(), destination_assets
    )


# --- the regression -------------------------------------------------------


def test_hero_image_survives_missing_local_cover_when_blog_has_it(tmp_path):
    """THE BUG: origin lacks the gitignored cover, blog still has its copy."""
    frontmatter = render(
        tmp_path, origin_has_file=False, destination_has_file=True
    )
    assert "heroImage: ./assets/2026-01-01-demo/cover.png" in frontmatter
    assert "ogImage: ./assets/2026-01-01-demo/cover.png" in frontmatter


def test_hero_image_written_when_origin_has_cover(tmp_path):
    frontmatter = render(tmp_path, origin_has_file=True, destination_has_file=False)
    assert "heroImage: ./assets/2026-01-01-demo/cover.png" in frontmatter


def test_hero_image_blanked_when_neither_side_has_cover(tmp_path):
    """Both sides missing means the blog would render a broken image."""
    frontmatter = render(tmp_path, origin_has_file=False, destination_has_file=False)
    assert "heroImage:" not in frontmatter
    assert "ogImage:" not in frontmatter


# --- the safety property that must NOT be unified away --------------------


def test_strip_leading_cover_stays_strict_when_only_destination_has_file(tmp_path):
    """Stripping is destructive, so it must require the file in the origin tree.

    If this ever starts returning a stripped body, the two existence checks have
    been merged and a missing origin asset can now delete the body's only image.
    """
    source_path, destination_assets = build_scene(
        tmp_path, origin_has_file=False, destination_has_file=True
    )
    body = "![cover](assets/cover.png)\n\nrest of the body\n"
    assert sync.strip_leading_cover_image(body, "assets/cover.png", source_path.parent) == body


def test_strip_leading_cover_strips_when_origin_has_file(tmp_path):
    source_path, _ = build_scene(
        tmp_path, origin_has_file=True, destination_has_file=False
    )
    body = "![cover](assets/cover.png)\n\nrest of the body\n"
    assert sync.strip_leading_cover_image(body, "assets/cover.png", source_path.parent) == "rest of the body\n"


# --- the two helpers keep their distinct semantics ------------------------


def test_source_asset_exists_ignores_destination(tmp_path):
    source_dir = tmp_path / "origin"
    (source_dir / "assets").mkdir(parents=True)
    destination = tmp_path / "blog" / "assets" / "slug"
    destination.mkdir(parents=True)
    (destination / "cover.png").write_bytes(b"x")

    assert sync.source_asset_exists(source_dir, "assets/cover.png") is False


def test_asset_exists_in_source_or_destination_checks_both(tmp_path):
    source_dir = tmp_path / "origin"
    (source_dir / "assets").mkdir(parents=True)
    destination = tmp_path / "blog" / "assets" / "slug"
    destination.mkdir(parents=True)

    assert sync.asset_exists_in_source_or_destination(source_dir, "assets/cover.png", destination) is False

    (destination / "cover.png").write_bytes(b"x")
    assert sync.asset_exists_in_source_or_destination(source_dir, "assets/cover.png", destination) is True

    (source_dir / "assets" / "other.png").write_bytes(b"x")
    assert sync.asset_exists_in_source_or_destination(source_dir, "assets/other.png", destination) is True


def test_non_asset_references_are_trusted(tmp_path):
    """External URLs and bare filenames are not the sync's business."""
    source_dir = tmp_path / "origin"
    source_dir.mkdir()
    destination = tmp_path / "blog" / "assets" / "slug"
    destination.mkdir(parents=True)

    for value in ("https://example.com/a.png", "cover.png", "", None):
        assert sync.asset_exists_in_source_or_destination(source_dir, value, destination) is True
