# .agents/skills/seed-audio-gen/scripts/test_seed_audio_gen.py
import importlib.util
import struct
import wave
from types import SimpleNamespace
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


def test_is_retryable_transient_only():
    """只有 429/5xx 和服务内部码可重试；400/401 等不重试"""
    assert mod.is_retryable(429, None) is True
    for s in (500, 502, 503, 504):
        assert mod.is_retryable(s, None) is True
    assert mod.is_retryable(200, "55000000") is True   # volcano internal code
    assert mod.is_retryable(400, None) is False
    assert mod.is_retryable(401, None) is False
    assert mod.is_retryable(200, "45001116") is False  # prompt too long = deterministic
    assert mod.is_retryable(None, None) is False


def test_synthesize_retries_then_succeeds(monkeypatch, tmp_path):
    """前两次 503、第三次成功 → 重试后出音频，attempts=3"""
    import base64 as _b64
    calls = {"n": 0}

    def fake_post(client, headers, body):
        calls["n"] += 1
        if calls["n"] < 3:
            return {"ok": False, "status": 503, "code": None,
                    "message": "service unavailable", "log_id": "L%d" % calls["n"]}
        return {"ok": True, "log_id": "Lok",
                "data": {"audio": _b64.b64encode(b"RIFFfake"), "duration": 1.0,
                         "original_duration": 1.0, "url": ""}}

    monkeypatch.setattr(mod, "_post_once", fake_post)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)  # 不真睡
    r = mod.synthesize("测试", api_key="k", output_dir=tmp_path)
    assert calls["n"] == 3
    assert r["error"] is None
    assert r["attempts"] == 3
    assert r["audio_file"]


def test_synthesize_client_error_no_retry(monkeypatch, tmp_path):
    """4xx 确定性错误立即返回，不重试（attempts=1）"""
    calls = {"n": 0}

    def fake_post(client, headers, body):
        calls["n"] += 1
        return {"ok": False, "status": 400, "code": "45001116",
                "message": "prompt too long", "log_id": "L1"}

    monkeypatch.setattr(mod, "_post_once", fake_post)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    r = mod.synthesize("测试", api_key="k", output_dir=tmp_path)
    assert calls["n"] == 1
    assert r["attempts"] == 1
    assert r["error"] is not None
    assert "45001116" in r["error"]


def test_synthesize_network_error_retried(monkeypatch, tmp_path):
    """网络异常（ConnectError）可重试；耗尽后返回错误"""
    calls = {"n": 0}

    def fake_post(client, headers, body):
        calls["n"] += 1
        return {"ok": False, "status": None, "code": None,
                "message": "ConnectError: boom", "retryable": True}

    monkeypatch.setattr(mod, "_post_once", fake_post)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    r = mod.synthesize("测试", api_key="k", output_dir=tmp_path)
    assert calls["n"] == mod.MAX_RETRIES + 1  # 4 = 3 retries + 1 initial
    assert r["error"] is not None
    assert r["attempts"] == mod.MAX_RETRIES + 1


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


def _refs_args(**kw):
    defaults = dict(speaker=None, ref_audios=None, ref_image=None, ref_image_url=None)
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _url(u):
    """a reference tagged as coming from --ref-audio-url"""
    return ("url", u)


def _path(p):
    """a reference tagged as coming from --ref-audio (local)"""
    return ("path", p)


def test_build_references_remote_url():
    """--ref-audio-url 值进 audio_url，不读本地文件"""
    refs = mod._build_references(_refs_args(ref_audios=[_url("https://example.com/a.wav")]))
    assert refs == [{"audio_url": "https://example.com/a.wav"}]


def test_build_references_local_path():
    """--ref-audio 本地路径读成 audio_data (base64)"""
    local = Path(__file__).parent / "seed-audio-gen.py"
    refs = mod._build_references(_refs_args(ref_audios=[_path(str(local))]))
    assert len(refs) == 1 and "audio_data" in refs[0]


def test_build_references_multi_order_preserved():
    """混合 --ref-audio-url 和 --ref-audio，按 CLI 顺序保留（@音频N 顺序）"""
    local = Path(__file__).parent / "seed-audio-gen.py"  # 任意存在的文件即可
    args = _refs_args(ref_audios=[_url("https://example.com/a.wav"), _path(str(local))])
    refs = mod._build_references(args)
    assert len(refs) == 2
    assert refs[0] == {"audio_url": "https://example.com/a.wav"}
    assert "audio_data" in refs[1]
    # 反向顺序也保留
    args2 = _refs_args(ref_audios=[_path(str(local)), _url("https://example.com/b.wav")])
    refs2 = mod._build_references(args2)
    assert "audio_data" in refs2[0]
    assert refs2[1] == {"audio_url": "https://example.com/b.wav"}


def test_build_references_url_flag_rejects_non_url():
    """--ref-audio-url 给了本地路径 → 报错并提示用 --ref-audio"""
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_audios=[_url("/local/path.wav")]))


def test_build_references_path_flag_rejects_url():
    """--ref-audio 给了 URL → 报错并提示用 --ref-audio-url"""
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_audios=[_path("https://example.com/a.wav")]))


def test_build_references_missing_local_file():
    """--ref-audio 本地文件不存在 → 发 HTTP 前报错"""
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_audios=[_path("/nonexistent/audio.wav")]))


def test_build_references_speaker_and_audio_conflict():
    """speaker 与参考音频互斥"""
    args = _refs_args(speaker="zh_female_vv_uranus_bigtts",
                      ref_audios=[_url("https://example.com/a.wav")])
    with pytest.raises(SystemExit):
        mod._build_references(args)


def test_build_references_over_limit():
    """超过 3 条参考音频直接报错，不调 API"""
    args = _refs_args(ref_audios=[_url("https://example.com/%d.wav" % i) for i in range(4)])
    with pytest.raises(SystemExit):
        mod._build_references(args)


def test_build_references_image_conflicts(tmp_path):
    """图片参考不能与音频参考或 speaker 混用（API 45001001 / 官方文档约束）"""
    img = tmp_path / "x.png"
    img.write_bytes(b"fake")
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_image=str(img),
                                         ref_audios=[_url("https://example.com/a.wav")]))
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_image=str(img),
                                         speaker="zh_female_vv_uranus_bigtts"))


def test_build_references_image_alone(tmp_path):
    """单独图片参考正常进 references"""
    img = tmp_path / "x.png"
    img.write_bytes(b"fake")
    refs = mod._build_references(_refs_args(ref_image=str(img)))
    assert len(refs) == 1 and "image_data" in refs[0]


def _make_wav(path: Path, seconds: float, rate: int = 8000) -> Path:
    """生成指定时长的静音 wav（mono 8-bit，体积小，mutagen 可读时长）"""
    n = int(rate * seconds)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(b"\x80" * n)
    return path


def test_ref_audio_too_long_rejected(tmp_path):
    """本地参考音频超过 30s → 发 HTTP 前 die（实测值在错误信息里）"""
    wav = _make_wav(tmp_path / "long.wav", mod.MAX_REF_AUDIO_SECONDS + 1)
    args = _refs_args(ref_audios=[_path(str(wav))])
    with pytest.raises(SystemExit):
        mod._build_references(args)


def test_ref_audio_within_duration_ok(tmp_path):
    """短音频（<30s、小体积）通过预检"""
    wav = _make_wav(tmp_path / "ok.wav", 5)
    refs = mod._build_references(_refs_args(ref_audios=[_path(str(wav))]))
    assert len(refs) == 1 and "audio_data" in refs[0]


def test_ref_audio_too_large_rejected(tmp_path):
    """本地参考音频超过 10MB → die（用 truncate 造假大体积稀疏文件，不实际写 10MB）"""
    big = tmp_path / "big.wav"
    _make_wav(big, 1)
    with open(big, "ab") as f:
        f.truncate(mod.MAX_REF_AUDIO_BYTES + 1024)  # 稀疏撑到 >10MB
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_audios=[_path(str(big))]))


def test_ref_image_too_large_rejected(tmp_path):
    """本地参考图片超过 10MB → die"""
    img = tmp_path / "big.png"
    img.write_bytes(b"\x89PNG")
    with open(img, "ab") as f:
        f.truncate(mod.MAX_REF_IMAGE_BYTES + 1024)  # 稀疏撑到 >10MB
    with pytest.raises(SystemExit):
        mod._build_references(_refs_args(ref_image=str(img)))