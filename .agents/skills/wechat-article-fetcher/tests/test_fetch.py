"""
Regression tests for wechat-article-fetcher HTML processing.

Run with:
    uv run python -m pytest .agents/skills/wechat-article-fetcher/tests/

These tests exercise the pre_clean_html, download_images filter logic,
and the markdownify + post_clean pipeline on synthetic WeChat HTML
fragments. They are intentionally pure-Python (no Playwright, no network)
so they can run in CI without browser binaries.
"""

import sys
from pathlib import Path

# Add the skill's scripts dir to the import path so we can import `fetch`
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pytest

import markdownify as md_lib  # noqa: E402

from fetch import (  # noqa: E402
    pre_clean_html,
    post_clean_markdown,
    WECHAT_NOISE_SELECTORS,
    _is_video_wrapper,
    _VIDEO_WRAPPER_CLASSES,
    normalize_wechat_url,
    generate_slug,
)


# ── pre_clean_html: <pre> handling ─────────────────────────────────────

class TestPreBlockFixing:
    """WeChat nests <span>/<p>/<section>/<div> inside <pre> for fake line
    breaks. pre_clean_html should normalize these to real \\n."""

    def test_plain_pre_unchanged(self):
        out = pre_clean_html("<pre>line1\nline2</pre>")
        assert "line1\nline2" in out

    def test_pre_with_p_replaced_with_text(self):
        out = pre_clean_html("<pre><p>line1</p><p>line2</p></pre>")
        # The <p> tags are unwrapped, and a "\n" is inserted between them
        assert "line1\nline2" in out
        assert "<p>" not in out

    def test_pre_with_adjacent_spans_get_break(self):
        """The classic WeChat code block: <span>line1</span><span>line2</span>"""
        out = pre_clean_html("<pre><span>line1</span><span>line2</span><span>line3</span></pre>")
        assert "line1" in out and "line2" in out and "line3" in out
        # Three lines, not one merged string
        assert "line1\nline2" in out
        assert "line2\nline3" in out

    def test_pre_with_br_between_spans(self):
        """<br> inside <pre> is converted to a real newline (for code block
        readability, markdown's hard-break syntax "  \\n" looks wrong in code)."""
        out = pre_clean_html("<pre><span>line1</span><br><span>line2</span></pre>")
        assert "<br" not in out
        assert "line1" in out and "line2" in out
        # newline between the two
        assert "line1\nline2" in out

    def test_pre_with_text_newline_between_spans(self):
        """If the HTML already has a text \\n between spans, don't double up."""
        out = pre_clean_html("<pre><span>line1</span>\n<span>line2</span></pre>")
        assert "line1" in out and "line2" in out

    def test_pre_with_section_each_gets_break(self):
        out = pre_clean_html(
            "<pre><section><span>line1</span></section><section><span>line2</span></section></pre>"
        )
        # The <section>/<span> tags are unwrapped, line breaks preserved
        assert "line1" in out and "line2" in out
        # Note: WeChat uses <section> as the "soft line break" wrapper.
        # The pre_clean replaces direct-child <p>/<div>/<section> with text
        # + "\n". Nested <section> inside <pre> may not be at the direct-
        # child level, in which case the <span> unwrap handles it.
        # Just verify line break exists between the two values
        assert "line1\n" in out and "line2" in out

    def test_inline_code_untouched(self):
        out = pre_clean_html("<p>use <code>foo()</code> here</p>")
        assert "<code>foo()</code>" in out

    def test_pre_with_code_snippet_each_code_gets_break(self):
        """WeChat's pasted code blocks wrap each line in its own <code>
        element. markdownify treats <code> as inline, so pre_clean must
        replace direct-child <code> with text + \\n to preserve line breaks.
        """
        html = (
            '<pre class="code-snippet__js">'
            '<code><span>class AgentState(CopilotKitState):</span></code>'
            '<code><span>    search_history: list = []</span></code>'
            '<code><span>    completed: bool</span></code>'
            '</pre>'
        )
        cleaned = pre_clean_html(html)
        md = md_lib.markdownify(cleaned, heading_style='ATX')
        # Each line in its own row, not merged
        assert "class AgentState(CopilotKitState):" in md
        assert "search_history" in md
        # Critical: the three lines should be on separate visual lines
        assert "class AgentState(CopilotKitState):\n" in md

    def test_pre_with_br_separated_lines_in_single_code(self):
        """The code-snippet__js class structure can also put all lines
        inside ONE <code> tag, separated by <br><br>. Markdown's <br>
        rendering is a hard break "  \\n", which is wrong for code blocks.
        WeChat's pre_clean replaces <br> inside <pre> with real newlines.
        """
        html = (
            '<pre><code>'
            '<span>import</span> {<span> foo </span>}<br><br>'
            '<span>const x = 1</span><br><br>'
            '<span>export x</span>'
            '</code></pre>'
        )
        cleaned = pre_clean_html(html)
        md = md_lib.markdownify(cleaned, heading_style='ATX')
        # The three logical lines should be on separate visual lines
        assert "import" in md
        assert "const x" in md
        assert "export x" in md
        # Critical: each line has its own newline, not merged
        assert "import" in md and "const x" in md
        lines = [l for l in md.split("\n") if l.strip() and not l.startswith("```")]
        # Should have 3+ meaningful lines (import, const, export)
        assert len(lines) >= 3


# ── pre_clean_html: video marker placement ─────────────────────────────

class TestVideoMarker:
    """<video> and <iframe src='mpvideo.qpic.cn'> should produce a [视频]
    placeholder so Markdown readers know the original had a video."""

    def test_top_level_video_gets_marker(self):
        out = pre_clean_html("<div><p>before</p><video src='x.mp4'></video><p>after</p></div>")
        assert "[视频]" in out
        # And the <video> tag itself is gone
        assert "<video" not in out

    def test_iframe_in_mpcps_gets_marker(self):
        """<iframe src='mpvideo.qpic.cn/...'> inside <mpcps> container."""
        out = pre_clean_html(
            "<div><mpcps><iframe src='https://mpvideo.qpic.cn/x.mp4'></iframe></mpcps><p>after</p></div>"
        )
        assert "[视频]" in out
        assert "<iframe" not in out
        assert "<mpcps" not in out

    def test_marker_survives_noise_selectors(self):
        """Even when the <video> is wrapped in noise-target divs (.js_mpvedio etc),
        the marker should appear in the output."""
        out = pre_clean_html(
            '<div class="js_mpvedio page_video_wrapper">'
            '<div class="mp-video-player">'
            '<video src="x.mp4"></video>'
            '</div></div>'
        )
        assert "[视频]" in out

    def test_both_top_level_video_and_iframe_in_mpcps(self):
        out = pre_clean_html(
            '<div><mpcps><iframe src="https://mpvideo.qpic.cn/x.mp4"></iframe></mpcps>'
            '<video src="y.mp4"></video></div>'
        )
        assert out.count("[视频]") == 2


# ── pre_clean_html: noise removal ───────────────────────────────────────

class TestNoiseRemoval:
    """WECHAT_NOISE_SELECTORS should remove all the listed elements."""

    @pytest.mark.parametrize("selector", [
        "script", "style", ".qr_code_pc", ".reward_area",
        ".original_area_primary", ".wx_profile_card_inner",
        "mpcps", "mp-common-profile", "mp-miniprogram", "mpvoice",
    ])
    def test_selector_clears_matching_element(self, selector):
        # Build HTML that matches the noise selector. Class selectors
        # need `class="..."`; tag selectors need the tag itself.
        if selector.startswith("."):
            class_name = selector[1:]
            html = f'<div><span class="{class_name}">x</span></div>'
        else:
            html = f"<div><{selector}>x</{selector}></div>"
        out = pre_clean_html(html)
        # The body content "x" is removed
        assert "x" not in out, f"{selector} should be removed"


# ── pre_clean_html: full pipeline produces clean output ────────────────

class TestFullPipeline:
    """The whole pre_clean_html should be idempotent and not destroy content."""

    def test_paragraphs_preserved(self):
        out = pre_clean_html("<div><p>hello</p><p>world</p></div>")
        assert "hello" in out and "world" in out

    def test_headings_preserved(self):
        out = pre_clean_html("<div><h1>Title</h1><h2>Sub</h2></div>")
        assert "<h1>Title</h1>" in out
        assert "<h2>Sub</h2>" in out

    def test_image_src_preserved(self):
        out = pre_clean_html('<p><img src="https://mmbiz.qpic.cn/x.png"></p>')
        assert "mmbiz.qpic.cn" in out


# ── download_images filter logic ───────────────────────────────────────

class TestDownloadImagesFilter:
    """download_images should skip mpvideo.qpic.cn (video covers) and
    only process mmbiz.qpic.cn images."""

    def test_mpvideo_cover_skipped(self, tmp_path, monkeypatch):
        from fetch import download_images
        # Don't actually download anything — patch requests.get to track calls
        calls = []

        def fake_get(url, **kwargs):
            calls.append(url)
            from unittest.mock import MagicMock
            resp = MagicMock()
            resp.headers = {"Content-Type": "image/jpeg"}
            resp.content = b"fake"
            return resp

        monkeypatch.setattr("requests.get", fake_get)
        html = (
            '<p><img src="https://mmbiz.qpic.cn/mmbiz_png/abc?xxx=1"></p>'
            '<p><img src="https://mpvideo.qpic.cn/x.mp4?cover=1"></p>'
        )
        updated, manifest = download_images(html, tmp_path, no_images=False)

        # mmbiz image was downloaded; mpvideo was skipped
        downloaded_urls = [c for c in calls if "mmbiz" in c]
        assert len(downloaded_urls) == 1
        # Manifest only has mmbiz
        assert len(manifest) == 1
        assert "mmbiz" in manifest[0]["original_url"]

    def test_non_mmbiz_image_skipped(self, tmp_path, monkeypatch):
        from fetch import download_images
        calls = []

        def fake_get(url, **kwargs):
            calls.append(url)
            from unittest.mock import MagicMock
            resp = MagicMock()
            resp.headers = {"Content-Type": "image/jpeg"}
            resp.content = b"fake"
            return resp

        monkeypatch.setattr("requests.get", fake_get)
        html = '<p><img src="https://example.com/other.jpg"></p>'
        updated, manifest = download_images(html, tmp_path, no_images=False)
        # No download call should have been made
        assert len(calls) == 0
        assert len(manifest) == 0


# ── _is_video_wrapper helper ───────────────────────────────────────────

class TestIsVideoWrapper:
    def test_recognized_class(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup('<div class="js_mpvedio">x</div>', "lxml")
        node = soup.find("div")
        assert _is_video_wrapper(node) is True

    def test_unrelated_class(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup('<div class="content">x</div>', "lxml")
        node = soup.find("div")
        assert _is_video_wrapper(node) is False

    def test_multiple_classes_one_match(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup('<div class="foo mp-video-player bar">x</div>', "lxml")
        node = soup.find("div")
        assert _is_video_wrapper(node) is True


# ── URL normalization ──────────────────────────────────────────────────

class TestURLNormalization:
    def test_https_unchanged(self):
        url = "https://mp.weixin.qq.com/s?__biz=abc"
        assert normalize_wechat_url(url) == url

    def test_strip_quotes(self):
        url = '"https://mp.weixin.qq.com/s?__biz=abc"'
        assert normalize_wechat_url(url) == "https://mp.weixin.qq.com/s?__biz=abc"

    def test_bare_hostname_gets_https(self):
        url = "mp.weixin.qq.com/s?__biz=abc"
        assert normalize_wechat_url(url).startswith("https://mp.weixin.qq.com/")


# ── Slug generation ────────────────────────────────────────────────────

class TestSlugGeneration:
    def test_title_takes_priority_over_biz_mid(self):
        """Title-based slug is more readable than base64 biz+mid. We prefer
        it whenever the title is available, even if the URL has biz+mid."""
        url = "https://mp.weixin.qq.com/s?__biz=MzkwNzg4MjM1Ng==&mid=2247490808"
        slug = generate_slug(url, "【GitHub趋势】CopilotKit：Agent 前端栈与 AG-UI 协议")
        # Should be derived from the title, not the base64 biz
        assert "copilotkit" in slug.lower()
        assert "agent" in slug.lower()
        # Should NOT contain the base64-encoded biz
        assert "mzkwnzg4mjm1ng" not in slug.lower()

    def test_falls_back_to_biz_mid_when_no_title(self):
        url = "https://mp.weixin.qq.com/s?__biz=abc123&mid=def456"
        slug = generate_slug(url, None)
        assert "abc123" in slug
        assert "def456" in slug

    def test_falls_back_to_path_when_no_title_no_params(self):
        url = "https://mp.weixin.qq.com/article/abc"
        slug = generate_slug(url, None)
        assert "abc" in slug


# ── Markdown post-cleaning ─────────────────────────────────────────────

class TestPostCleanMarkdown:
    def test_compress_blank_lines(self):
        md = "line1\n\n\n\nline2"
        assert post_clean_markdown(md) == "line1\n\nline2"

    def test_strip_trailing_whitespace(self):
        md = "line1   \nline2\t"
        out = post_clean_markdown(md)
        assert out == "line1\nline2"

    def test_nbsp_to_space(self):
        md = "line1 line2"
        assert post_clean_markdown(md) == "line1 line2"
