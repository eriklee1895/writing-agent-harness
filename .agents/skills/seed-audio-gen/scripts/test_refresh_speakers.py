# .agents/skills/seed-audio-gen/scripts/test_refresh_speakers.py
"""Tests for refresh-speakers.build_speakers_md curated quick reference."""
import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "refresh-speakers.py"
spec = importlib.util.spec_from_file_location("refresh_speakers", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _spk(vt, scene, heat=0, name=None):
    return {
        "voice_type": vt, "name": name or vt, "type": "bigtts",
        "gender": "女", "age": "", "scene": scene, "description": "d",
        "languages": [], "trial_url": "https://example.com/t.wav",
        "heat": heat, "status": "online", "emoji": "",
    }


def test_scene_order_creative_first():
    """通用场景排第一，角色扮演随后，客服/教学靠后，其他垫底"""
    speakers = [
        _spk("a", "客服场景"), _spk("b", "通用场景", heat=5),
        _spk("c", "角色扮演"), _spk("d", "教学场景"),
        _spk("e", "其他"), _spk("f", "视频配音"),
    ]
    md = mod.build_speakers_md(speakers)
    headers = [line for line in md.splitlines() if line.startswith("## ")]
    scene_names = [h.split("（")[0].replace("## ", "") for h in headers]
    assert scene_names[0] == "通用场景"
    assert scene_names[1] == "角色扮演"
    assert scene_names.index("其他") == len(scene_names) - 1
    assert scene_names.index("通用场景") < scene_names.index("视频配音") < scene_names.index("教学场景") < scene_names.index("客服场景")


def test_top_n_truncation_per_scene():
    """每个场景最多列 TOP_VOICES_PER_SCENE 行，但标注总数"""
    speakers = [_spk(f"v{i}", "角色扮演", heat=100 - i) for i in range(12)]
    md = mod.build_speakers_md(speakers)
    # 标注本场景共 12 个
    assert "本场景共 12 个" in md
    # 只列 Top 5
    assert f"列 Top {mod.TOP_VOICES_PER_SCENE}" in md
    rows = [l for l in md.splitlines() if l.startswith("| v")]
    assert len(rows) == mod.TOP_VOICES_PER_SCENE
    # 按 heat 降序，最高热的在前
    assert "v0" in rows[0]


def test_curated_header_does_not_claim_full():
    """头部声明精选速查、全量在 json 且勿读，不再自称全量表格"""
    md = mod.build_speakers_md([_spk("a", "通用场景")])
    assert "精选" in md
    assert "speakers.json" in md
    # 不应再出现旧的「共 N 个音色」全量自称句
    assert "音色速查表\n" not in md  # 旧标题已改为「音色速查（精选）」
    assert "（精选）" in md
