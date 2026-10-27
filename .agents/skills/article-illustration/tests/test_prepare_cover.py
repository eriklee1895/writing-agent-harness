from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_cover.py"


def load_module():
    spec = importlib.util.spec_from_file_location("prepare_cover", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["prepare_cover"] = module
    spec.loader.exec_module(module)
    return module


prepare = load_module()


def write_image(path: Path, size=(400, 200), mode="RGB"):
    image = Image.new(mode, size, (255, 0, 0, 255) if mode == "RGBA" else "red")
    if size[0] >= 200:
        image.paste("blue", (size[0] // 2, 0, size[0], size[1]))
    image.save(path)


def test_crop_uses_focal_point_and_exact_dimensions(tmp_path):
    source = tmp_path / "source.png"
    write_image(source)
    output = tmp_path / "left.png"

    result = prepare.derive_cover(source, output, (100, 100), mode="crop", focus_x=0.0)

    assert result["dimensions"] == [100, 100]
    assert result["derivation"]["crop"] == [0, 0, 200, 200]
    assert Image.open(output).getpixel((50, 50)) == (255, 0, 0)


def test_crop_can_preserve_right_side(tmp_path):
    source = tmp_path / "source.png"
    write_image(source)
    output = tmp_path / "right.png"

    prepare.derive_cover(source, output, (100, 100), mode="crop", focus_x=1.0)

    assert Image.open(output).getpixel((50, 50)) == (0, 0, 255)


def test_pad_preserves_whole_image_and_background(tmp_path):
    source = tmp_path / "source.png"
    write_image(source)
    output = tmp_path / "padded.png"

    result = prepare.derive_cover(source, output, (200, 200), mode="pad", background="#ffffff")

    image = Image.open(output)
    assert image.size == (200, 200)
    assert image.getpixel((100, 10)) == (255, 255, 255)
    assert result["derivation"]["operation"] == "pad"


def test_rgba_is_composited_on_requested_background(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGBA", (100, 50), (0, 0, 0, 0)).save(source)
    output = tmp_path / "alpha.png"

    prepare.derive_cover(source, output, (100, 100), mode="pad", background="#ffffff")

    assert Image.open(output).getpixel((10, 10)) == (255, 255, 255)


def test_rejects_upscaling_and_master_overwrite(tmp_path):
    source = tmp_path / "source.png"
    write_image(source, size=(100, 100))

    with pytest.raises(ValueError, match="upscale"):
        prepare.derive_cover(source, tmp_path / "large.png", (200, 100), mode="crop")
    with pytest.raises(ValueError, match="master"):
        prepare.derive_cover(source, source, (100, 100), mode="crop", force=True)


def test_existing_output_requires_force(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    write_image(source)
    output.write_bytes(b"do not overwrite")

    with pytest.raises(FileExistsError):
        prepare.derive_cover(source, output, (100, 100), mode="crop")


def test_refuses_symlink_output_even_with_force(tmp_path):
    source = tmp_path / "source.png"
    target = tmp_path / "archived-master.png"
    output = tmp_path / "cover.png"
    write_image(source)
    target.write_bytes(b"archived master")
    output.symlink_to(target)

    with pytest.raises(ValueError, match="symlink"):
        prepare.derive_cover(source, output, (100, 100), mode="crop", force=True)

    assert target.read_bytes() == b"archived master"


def test_manifest_records_derivation_and_pending_review(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover-wechat.png"
    manifest = tmp_path / "manifest.json"
    write_image(source)

    prepare.derive_cover(
        source,
        output,
        (200, 100),
        mode="crop",
        role="wechat_cover",
        channel="wechat",
        manifest_path=manifest,
    )

    entry = json.loads(manifest.read_text())["images"][0]
    assert entry["file"] == output.name
    assert entry["derived_from"] == source.name
    assert entry["role"] == "wechat_cover"
    assert entry["channel"] == "wechat"
    assert entry["dimensions"] == [200, 100]
    assert entry["status"] == "candidate"
    assert entry["visual_review"] == "pending"
    assert len(entry["sha256"]) == 64


def test_rederiving_resets_review_and_preserves_other_entries(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    manifest = tmp_path / "manifest.json"
    write_image(source)
    manifest.write_text(json.dumps({"images": [
        {"file": output.name, "status": "used", "visual_review": "approved", "note": "keep me"},
        {"file": "unrelated.png", "status": "used"},
    ]}))

    prepare.derive_cover(source, output, (200, 100), mode="crop", manifest_path=manifest, force=True)

    entries = json.loads(manifest.read_text())["images"]
    assert entries[0]["file"] == "unrelated.png"
    assert entries[1]["status"] == "candidate"
    assert entries[1]["visual_review"] == "pending"
    assert entries[1]["note"] == "keep me"


def test_cli_emits_structured_json(tmp_path, capsys):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    write_image(source)

    exit_code = prepare.main([
        "--input", str(source),
        "--output", str(output),
        "--size", "200x100",
        "--mode", "crop",
        "--json",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["output"] == str(output)
    assert payload["dimensions"] == [200, 100]


def test_rederiving_clears_old_approval_and_regeneration_fields(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    manifest = tmp_path / "manifest.json"
    write_image(source)
    manifest.write_text(json.dumps({"images": [{
        "file": output.name,
        "status": "used",
        "visual_review": "approved",
        "approved_by": "user",
        "approval_date": "2026-01-01",
        "review": {"sizes": ["old"]},
        "home_review": "approved",
        "regeneration": {"reason": "old"},
        "home_published": True,
        "wechat_published": True,
        "archive": "old/archive.png",
        "note": "keep me",
    }]}))

    prepare.derive_cover(source, output, (200, 100), mode="crop", manifest_path=manifest, force=True)

    entry = json.loads(manifest.read_text())["images"][0]
    for field in ["approved_by", "approval_date", "review", "home_review", "regeneration", "home_published", "wechat_published", "archive"]:
        assert field not in entry, field
    assert entry["status"] == "candidate"
    assert entry["visual_review"] == "pending"
    assert entry["note"] == "keep me"


def test_invalid_manifest_does_not_replace_existing_image(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    manifest = tmp_path / "manifest.json"
    write_image(source)
    output.write_bytes(b"approved-image")
    manifest.write_text("{not-json")

    with pytest.raises(json.JSONDecodeError):
        prepare.derive_cover(source, output, (100, 100), mode="crop", manifest_path=manifest, force=True)

    assert output.read_bytes() == b"approved-image"


def test_rgba_background_is_preserved(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "alpha.png"
    write_image(source, size=(100, 50), mode="RGBA")

    prepare.derive_cover(source, output, (100, 100), mode="pad", background="#11223380")

    image = Image.open(output)
    assert image.mode == "RGBA"
    assert image.getpixel((1, 1)) == (17, 34, 51, 128)


def test_manifest_symlink_is_rejected_without_touching_target(tmp_path):
    source = tmp_path / "source.png"
    output = tmp_path / "cover.png"
    target = tmp_path / "archived-manifest.json"
    link = tmp_path / "manifest.json"
    write_image(source)
    target.write_text('{"images": []}')
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symlink manifest"):
        prepare.derive_cover(source, output, (100, 100), mode="crop", manifest_path=link)

    assert target.read_text() == '{"images": []}'
    assert not output.exists()


def test_same_named_assets_keep_distinct_lineage(tmp_path):
    manifest = tmp_path / "manifest.json"
    for directory in ["blog", "wechat"]:
        (tmp_path / directory).mkdir()
        write_image(tmp_path / directory / "master.png")

    prepare.derive_cover(tmp_path / "blog" / "master.png", tmp_path / "blog" / "cover.png", (100, 100), mode="crop", role="blog_cover", channel="blog", manifest_path=manifest)
    prepare.derive_cover(tmp_path / "wechat" / "master.png", tmp_path / "wechat" / "cover.png", (100, 100), mode="crop", role="wechat_cover", channel="wechat", manifest_path=manifest)

    entries = json.loads(manifest.read_text())["images"]
    assert [entry["file"] for entry in entries] == ["blog/cover.png", "wechat/cover.png"]
    assert [entry["derived_from"] for entry in entries] == ["blog/master.png", "wechat/master.png"]
