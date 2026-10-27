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
