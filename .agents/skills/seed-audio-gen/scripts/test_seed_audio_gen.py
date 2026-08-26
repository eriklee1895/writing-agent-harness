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