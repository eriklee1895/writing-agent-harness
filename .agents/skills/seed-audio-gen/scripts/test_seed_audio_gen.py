# .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
import importlib.util
import pytest
from pathlib import Path

_MODULE_PATH = Path(__file__).parent / "seed-audio-gen.py"
spec = importlib.util.spec_from_file_location("seed_audio_gen", str(_MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_prompt_too_long_raises():
    """text_prompt > 3000 字符时报错，带可执行 hint"""
    long_prompt = "啊" * 3001
    with pytest.raises(mod.PromptTooLongError) as exc_info:
        mod.validate_prompt_length(long_prompt)
    msg = str(exc_info.value)
    assert "3000" in msg
    assert "split your prompt" in msg
    assert "120s" in msg

def test_prompt_at_limit_ok():
    """正好 3000 字符不报错"""
    mod.validate_prompt_length("啊" * 3000)  # 不抛异常即通过


def test_build_body_minimal():
    """最小 body 结构正确"""
    body = mod.build_body("一位女声朗读：你好", references=None, audio_config=None, watermark=None, model="seed-audio-1.0")
    assert body["model"] == "seed-audio-1.0"
    assert body["text_prompt"] == "一位女声朗读：你好"
    assert "references" not in body or body["references"] is None


def test_build_body_with_speaker():
    """speaker 进 references 列表"""
    body = mod.build_body("test", references=[{"speaker": "zh_female_vv_uranus_bigtts"}], audio_config={"format":"mp3"}, watermark=None, model="seed-audio-1.0")
    assert body["references"] == [{"speaker": "zh_female_vv_uranus_bigtts"}]
    assert body["audio_config"]["format"] == "mp3"


def test_build_body_watermark():
    """watermark flag 展开为 object"""
    body = mod.build_body("test", references=None, audio_config=None, watermark={"aigc": True, "meta": False}, model="seed-audio-1.0")
    assert body["watermark"]["aigc_watermark"] is True
    assert body["watermark"]["aigc_metadata"]["enable"] is False


def test_query_speakers_filter_scene():
    """按 scene 过滤并按 heat 降序排序"""
    speakers = [
        {"voice_type":"a","name":"A","type":"bigtts","scene":"视频配音","heat":50},
        {"voice_type":"b","name":"B","type":"bigtts","scene":"通用场景","heat":100},
        {"voice_type":"c","name":"C","type":"icl","scene":"视频配音","heat":80},
    ]
    result = mod.query_speakers(speakers, filters={"scene":"视频配音"}, sort_by="heat")
    assert len(result) == 2
    assert result[0]["name"] == "C"  # heat 80 > 50


def test_query_speakers_filter_type():
    """按 type 过滤，不排序"""
    speakers = [
        {"voice_type":"a","name":"A","type":"bigtts","scene":"通用场景","heat":50},
        {"voice_type":"b","name":"B","type":"icl","scene":"通用场景","heat":100},
    ]
    result = mod.query_speakers(speakers, filters={"type":"icl"}, sort_by=None)
    assert len(result) == 1
    assert result[0]["type"] == "icl"


def test_query_speakers_no_filter():
    """无过滤无排序，原样返回"""
    speakers = [{"voice_type":"a","name":"A","type":"bigtts","scene":"s","heat":1}]
    result = mod.query_speakers(speakers, filters=None, sort_by=None)
    assert len(result) == 1


def test_batch_summary():
    results = [
        {"original_duration": 60.0, "error": None},
        {"original_duration": 30.0, "error": None},
        {"original_duration": None, "error": "failed"},
    ]
    summary = mod.build_batch_summary(results)
    assert summary["total_duration_seconds"] == 90.0
    assert summary["estimated_cost_yuan"] == 1.5  # 90s/60 * 1.0
    assert summary["success_count"] == 2
    assert summary["fail_count"] == 1