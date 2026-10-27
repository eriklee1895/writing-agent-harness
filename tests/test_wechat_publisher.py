from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".agents/skills/wechat-article-publisher/scripts/publish.py"


def load_module():
    spec = importlib.util.spec_from_file_location("wechat_publisher", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["wechat_publisher"] = module
    spec.loader.exec_module(module)
    return module


publisher = load_module()


def test_repo_relative_image_path_ignores_cwd(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    image = tmp_path / "content/origin/demo/assets/cover.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    other = tmp_path / "somewhere-else"
    other.mkdir()
    monkeypatch.chdir(other)

    resolved = publisher.resolve_local_image_path(
        "content/origin/demo/assets/cover.png",
        html_path=tmp_path / "content/wechat/demo/index.wechat-preview.html",
    )

    assert resolved == image.resolve()


def test_html_relative_path_wins_before_article_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    html_path = tmp_path / "content/wechat/demo/index.wechat-preview.html"
    article_path = tmp_path / "content/origin/demo/index.md"
    html_image = html_path.parent / "assets/pic.png"
    article_image = article_path.parent / "assets/pic.png"
    html_image.parent.mkdir(parents=True)
    article_image.parent.mkdir(parents=True)
    html_image.write_bytes(b"html")
    article_image.write_bytes(b"article")

    resolved = publisher.resolve_local_image_path(
        "assets/pic.png", html_path=html_path, article_path=article_path
    )

    assert resolved == html_image.resolve()


def test_article_relative_path_is_used_when_html_has_no_asset(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    html_path = tmp_path / "content/wechat/demo/index.wechat-preview.html"
    article_path = tmp_path / "content/origin/demo/index.md"
    article_image = article_path.parent / "assets/pic.png"
    article_image.parent.mkdir(parents=True)
    article_image.write_bytes(b"article")

    resolved = publisher.resolve_local_image_path(
        "assets/pic.png", html_path=html_path, article_path=article_path
    )

    assert resolved == article_image.resolve()


def test_absolute_image_path_is_preserved(tmp_path):
    image = tmp_path / "cover.png"
    image.write_bytes(b"image")
    assert publisher.resolve_local_image_path(str(image)) == image


def test_extracted_images_use_the_same_path_resolution(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, "REPO_ROOT", tmp_path)
    image = tmp_path / "content/origin/demo/assets/pic.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    html_path = tmp_path / "content/wechat/demo/index.wechat-preview.html"
    html_path.parent.mkdir(parents=True)
    html_path.write_text("", encoding="utf-8")

    _, images, _ = publisher.extract_body_from_html(
        '<article class="dark-text"><p>Body</p>'
        '<img data-local-path="content/origin/demo/assets/pic.png" src="pic.png">'
        "</article>",
        html_path=html_path,
    )

    assert images[0]["path"] == image.resolve()


def test_missing_author_fails_instead_of_returning_empty(monkeypatch):
    monkeypatch.setattr(publisher, "load_config", lambda: {})
    monkeypatch.setattr("builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError()))

    with pytest.raises(ValueError, match="缺少作者"):
        publisher.resolve_author("", {})


def test_explicit_author_does_not_need_config():
    assert publisher.resolve_author("Erik Lee", {}) == "Erik Lee"
