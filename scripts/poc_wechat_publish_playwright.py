#!/usr/bin/env python3
"""
PoC: WeChat Official Account article publishing via Playwright.

Goal: validate that Playwright can replace the baoyu CDP path for the
article (文章) publish flow — login-state reuse, capture the editor tab,
fill title/author/body, and (optionally) save a draft.

Scope is intentionally minimal: plain-text article only, no images, no
cover, no renderer integration. We are validating the editor-automation
mechanics, not layout fidelity. Full capability lives in a later skill if
this PoC proves Playwright is the better path.

Publish boundary: this script only saves a DRAFT (草稿箱). It never clicks
发布/群发. WeChat QR login requires one-time human participation.

Usage:
    uv run python scripts/poc_wechat_publish_playwright.py \
        --markdown content/source/2026-05-24-wechat-opening/article.md \
        --title "静待鹅鸣" --author "Erik"

    # add --save-draft to actually persist the draft and report appmsgid
"""

from __future__ import annotations

import argparse
import html as html_mod
import os
import re
import sys
import time
from pathlib import Path

try:
    import playwright  # noqa: F401
except ImportError:
    print("ERROR: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from playwright.sync_api import TimeoutError as PWTimeoutError
from playwright.sync_api import sync_playwright

# ── Constants ──────────────────────────────────────────────────────────

CHROME_PATH = os.environ.get(
    "CHROME_EXECUTABLE",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
# Dedicated profile — fully decoupled from baoyu's shared profile.
USER_DATA_DIR = Path.home() / ".config" / "wechat-publish-playwright" / "profile"
ARTIFACTS_DIR = Path(__file__).parent / ".poc-artifacts"

WECHAT_URL = "https://mp.weixin.qq.com/"
HOME_URL_PATTERN = re.compile(r"/cgi-bin/home")
LOGIN_TIMEOUT_MS = 300_000  # 5 min for QR scan + phone confirm

# Article-editor DOM contract (extracted from baoyu wechat-article.ts, proven).
SEL_TITLE = "#title"
SEL_AUTHOR = "#author"
SEL_SUMMARY = "#js_description"
SEL_BODY = ".rich_media_content .ProseMirror"
SEL_SAVE_DRAFT = "#js_submit button"  # 保存为草稿 (NOT 发布/群发)

# ── Minimal Markdown → HTML (plain text + inline images) ─────────────────

IMG_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)$")


def parse_markdown(md: str, base_dir: Path):
    """Convert markdown body into <p> blocks + extract inline images.

    Returns (body_html, images) where body_html contains a unique text
    placeholder for each image, and images is a list of
    {placeholder, path, alt}. Image upload happens later by locating the
    placeholder in the editor and replacing it (mirrors baoyu's approach).
    Handles paragraphs, **bold**, and standalone image refs. Headings are
    rendered as bold paragraphs (minimal — full styling is the renderer's job).
    """
    blocks: list[str] = []
    images: list[dict] = []
    for raw_para in re.split(r"\n\s*\n", md.strip()):
        para = raw_para.strip()
        if not para:
            continue
        img_match = IMG_RE.match(para)
        if img_match:
            idx = len(images)
            placeholder = f"WXIMGPH{idx}WXIMGPH"
            img_path = (base_dir / img_match.group("path")).resolve()
            images.append({
                "placeholder": placeholder,
                "path": img_path,
                "alt": img_match.group("alt"),
            })
            blocks.append(f"<p>{placeholder}</p>")
            continue
        # Collapse intra-paragraph newlines into spaces.
        para = re.sub(r"\s*\n\s*", " ", para)
        # Strip leading markdown heading markers → bold paragraph.
        heading = re.match(r"^#{1,6}\s+(.*)$", para)
        if heading:
            para = f"**{heading.group(1)}**"
        escaped = html_mod.escape(para, quote=False)
        # Apply **bold** after escaping (asterisks survive escaping).
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        blocks.append(f"<p>{escaped}</p>")
    return "".join(blocks), images


def strip_frontmatter(text: str) -> str:
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", text, flags=re.DOTALL)
    return text[m.end():] if m else text

# ── Editor helpers (evaluate-based, mirror baoyu's proven approach) ──────

_JS_SET_INPUT = """
([selector, value]) => {
  const el = document.querySelector(selector);
  if (!el) return false;
  el.focus();
  el.value = value;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.dispatchEvent(new Event('blur', { bubbles: true }));
  return true;
}
"""

_JS_INSERT_BODY = """
(html) => {
  const editor = document.querySelector('.rich_media_content .ProseMirror');
  if (!editor) return JSON.stringify({ ok: false, reason: 'editor-missing' });
  editor.focus();
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.deleteContents();
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
  const inserted = document.execCommand('insertHTML', false, html);
  editor.dispatchEvent(new InputEvent('input', {
    bubbles: true, inputType: 'insertHTML', data: ''
  }));
  return JSON.stringify({
    ok: inserted || (editor.innerText || '').trim().length > 0,
    textLength: (editor.innerText || '').trim().length
  });
}
"""

_JS_DRAFT_STATUS = """
() => {
  const submit = document.querySelector('#js_submit');
  const button = submit ? submit.querySelector('button') : null;
  let appmsgid = '';
  try { appmsgid = new URL(location.href).searchParams.get('appmsgid') || ''; } catch (e) {}
  const messages = Array.from(
    document.querySelectorAll('.weui-desktop-toast, .weui-desktop-toptips, .js_tips')
  ).map((el) => (el.innerText || el.textContent || '').trim()).filter(Boolean);
  const dialogs = Array.from(
    document.querySelectorAll('.weui-desktop-dialog, .weui-desktop-mask, [class*="dialog"]')
  ).filter((el) => el.offsetParent !== null)
   .map((el) => (el.innerText || '').trim().slice(0, 120)).filter(Boolean);
  return JSON.stringify({
    appmsgid,
    isLoading: (submit && submit.classList.contains('btn_loading')) || (button && button.disabled) || false,
    submitText: (submit ? (submit.innerText || '') : '').trim().slice(0, 40),
    messages,
    dialogs
  });
}
"""


def set_input(page, selector: str, value: str) -> bool:
    return page.evaluate(_JS_SET_INPUT, [selector, value])

# ── Inline-image helpers (mirror baoyu: select placeholder → delete → upload) ──

# Body image file input. baoyu uses the first matching input and it works on
# the article editor (type=77); cover uploader differs.
SEL_IMG_INPUT = 'input[type="file"][accept*="image"]'

_JS_SELECT_PLACEHOLDER = """
(placeholder) => {
  const editor = document.querySelector('.rich_media_content .ProseMirror');
  if (!editor) return false;
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null);
  let node;
  while ((node = walker.nextNode())) {
    const idx = node.nodeValue.indexOf(placeholder);
    if (idx !== -1) {
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + placeholder.length);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      editor.focus();
      return true;
    }
  }
  return false;
}
"""

_JS_IMG_COUNT = """
() => {
  const editor = document.querySelector('.rich_media_content .ProseMirror');
  if (!editor) return JSON.stringify({ total: 0, mmbiz: 0, sample: '' });
  const imgs = Array.from(editor.querySelectorAll('img'))
    .filter((i) => !i.classList.contains('ProseMirror-separator'));
  const onCdn = (i) => {
    const cand = [i.src, i.currentSrc, i.getAttribute('data-src'), i.getAttribute('src')];
    return cand.some((u) => (u || '').includes('mmbiz.qpic.cn'));
  };
  const mmbiz = imgs.filter(onCdn).length;
  const sample = imgs.length ? (imgs[0].outerHTML || '').slice(0, 200) : '';
  return JSON.stringify({ total: imgs.length, mmbiz, sample });
}
"""


def img_count(page) -> dict:
    import json as _json
    return _json.loads(page.evaluate(_JS_IMG_COUNT))


def wait_for_cdn(page, expected: int, timeout_s: int = 90) -> dict:
    """Wait until all body images carry an mmbiz.qpic.cn URL (CDN upload done)."""
    deadline = time.monotonic() + timeout_s
    last = img_count(page)
    while time.monotonic() < deadline:
        last = img_count(page)
        if last["mmbiz"] >= expected:
            return last
        page.wait_for_timeout(1_000)
    return last


def upload_body_images(editor, images: list[dict]) -> dict:
    """Replace each placeholder with an uploaded body image.

    Returns a summary dict. For each image: select the placeholder text,
    delete it (Backspace), then set_input_files on the hidden body image
    input; WeChat inserts the image at the cursor and uploads to its CDN.
    """
    n_inputs = editor.locator(SEL_IMG_INPUT).count()
    print(f"[poc] 正文图片输入框数量: {n_inputs}（用 .first，对齐 baoyu）")
    uploaded = 0
    for i, img in enumerate(images):
        if not img["path"].exists():
            print(f"[poc] ⚠ 图片不存在，跳过: {img['path']}", file=sys.stderr)
            continue
        found = editor.evaluate(_JS_SELECT_PLACEHOLDER, img["placeholder"])
        if not found:
            print(f"[poc] ⚠ 编辑器内未找到占位符 {img['placeholder']}", file=sys.stderr)
            continue
        editor.keyboard.press("Backspace")  # delete selected placeholder text
        before = img_count(editor)["total"]
        editor.locator(SEL_IMG_INPUT).first.set_input_files(str(img["path"]))
        # Wait for the editor img count to increase (upload + insert).
        deadline = time.monotonic() + 30
        ok = False
        while time.monotonic() < deadline:
            if img_count(editor)["total"] >= before + 1:
                ok = True
                break
            editor.wait_for_timeout(500)
        if ok:
            uploaded += 1
            print(f"[poc] 图片 {i + 1}/{len(images)} 已插入: {img['path'].name}")
        else:
            print(f"[poc] ⚠ 图片 {i + 1} 上传超时: {img['path'].name}", file=sys.stderr)
    return {"requested": len(images), "uploaded": uploaded}

# ── Main publish flow ────────────────────────────────────────────────────

def publish(md_path: Path, title: str, author: str, summary: str | None,
            save_draft: bool, profile_dir: Path) -> int:
    if not md_path.exists():
        print(f"ERROR: markdown file not found: {md_path}", file=sys.stderr)
        return 1
    if not os.path.exists(CHROME_PATH):
        print(f"ERROR: Chrome not found at {CHROME_PATH}. Set CHROME_EXECUTABLE.", file=sys.stderr)
        return 1

    profile_dir.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    body_md = strip_frontmatter(md_path.read_text(encoding="utf-8"))
    body_html, images = parse_markdown(body_md, md_path.parent)
    line_count = body_md.count("\n") + 1
    print(f"[poc] 文章: {md_path}  ({line_count} 行 → {len(body_html)} chars HTML, {len(images)} 图)")

    timings: dict[str, float] = {}
    t0 = time.monotonic()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=CHROME_PATH,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        timings["browser_launch"] = time.monotonic() - t0
        editor = None
        try:
            page = context.new_page()
            page.goto(WECHAT_URL, wait_until="domcontentloaded", timeout=30_000)

            # ── Login: reuse profile state or wait for QR scan ──
            t_login = time.monotonic()
            if not HOME_URL_PATTERN.search(page.url):
                # Best-effort: click 微信快捷登录 if present (skip QR wait).
                try:
                    quick = page.get_by_text("微信快捷登录", exact=False)
                    if quick.count() > 0:
                        quick.first.click(timeout=3_000)
                except Exception:
                    pass
                print("[poc] 未检测到登录态。请在弹出的 Chrome 窗口中扫码登录"
                      "（或点『微信快捷登录』）。等待进入后台首页…")
                try:
                    page.wait_for_url(HOME_URL_PATTERN, timeout=LOGIN_TIMEOUT_MS)
                except PWTimeoutError:
                    print("ERROR: 登录超时（5 分钟内未进入 /cgi-bin/home）。", file=sys.stderr)
                    return 1
            timings["login_wait"] = time.monotonic() - t_login
            print(f"[poc] 已登录后台: {page.url}")

            # ── Open the article (文章) editor — opens in a new tab ──
            t_editor = time.monotonic()
            page.wait_for_selector(".new-creation__menu-item", timeout=20_000)
            article_title = page.locator(
                ".new-creation__menu-item .new-creation__menu-title"
            ).filter(has_text=re.compile(r"^\s*文章\s*$"))
            if article_title.count() == 0:
                page.screenshot(path=str(ARTIFACTS_DIR / "menu-not-found.png"))
                print("ERROR: 首页未找到『文章』创作入口。截图已存。", file=sys.stderr)
                return 1
            with context.expect_page(timeout=30_000) as new_page_info:
                article_title.first.click()
            editor = new_page_info.value
            editor.wait_for_load_state("domcontentloaded")
            editor.wait_for_selector(SEL_BODY, state="visible", timeout=30_000)
            timings["open_editor"] = time.monotonic() - t_editor
            print(f"[poc] 文章编辑器已打开: {editor.url}")

            # ── Fill title / author / summary / body ──
            t_fill = time.monotonic()
            if not set_input(editor, SEL_TITLE, title):
                print("WARNING: 标题输入框未找到", file=sys.stderr)
            if author:
                set_input(editor, SEL_AUTHOR, author)
            if summary:
                set_input(editor, SEL_SUMMARY, summary)

            import json as _json
            body_result = _json.loads(editor.evaluate(_JS_INSERT_BODY, body_html))
            if not body_result.get("ok"):
                editor.screenshot(path=str(ARTIFACTS_DIR / "body-insert-failed.png"))
                print(f"ERROR: 正文注入失败: {body_result}", file=sys.stderr)
                return 1
            print(f"[poc] 已填充 — 标题/作者/正文 (editor innerText={body_result['textLength']} chars)")

            # ── Upload inline body images (placeholder → upload → CDN) ──
            img_summary = {"requested": 0, "uploaded": 0}
            if images:
                img_summary = upload_body_images(editor, images)
                # Wait for CDN upload to finish before saving (else save stalls).
                stats = wait_for_cdn(editor, img_summary["uploaded"]) if img_summary["uploaded"] else img_count(editor)
                print(f"[poc] 正文图片: 请求 {img_summary['requested']} / "
                      f"已插入 {img_summary['uploaded']} / "
                      f"编辑器内 {stats['total']} 张 (mmbiz CDN: {stats['mmbiz']})")
                print(f"[poc] 首图 DOM 样本: {stats.get('sample', '')}")
            timings["fill"] = time.monotonic() - t_fill

            # ── Save draft (optional) ──
            if save_draft:
                t_save = time.monotonic()
                editor.locator(SEL_SAVE_DRAFT).first.click(timeout=10_000)
                appmsgid = ""
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    status = _json.loads(editor.evaluate(_JS_DRAFT_STATUS))
                    fail = next((m for m in status["messages"]
                                 if re.search(r"保存.*失败|草稿.*失败|save.*fail", m, re.I)), None)
                    if fail:
                        editor.screenshot(path=str(ARTIFACTS_DIR / "draft-save-failed.png"))
                        print(f"ERROR: 保存草稿失败: {fail}", file=sys.stderr)
                        return 1
                    # appmsgid is assigned once WeChat creates the draft record
                    # server-side. Don't gate on !isLoading — with large images
                    # the button can stay in a loading state while the draft is
                    # already persisted (observed false-negative otherwise).
                    if status["appmsgid"]:
                        appmsgid = status["appmsgid"]
                        break
                    editor.wait_for_timeout(1_000)
                timings["save_draft"] = time.monotonic() - t_save
                if appmsgid:
                    print(f"[poc] ✓ 草稿已保存  appmsgid={appmsgid}")
                else:
                    last = _json.loads(editor.evaluate(_JS_DRAFT_STATUS))
                    editor.screenshot(path=str(ARTIFACTS_DIR / "appmsgid-timeout.png"))
                    print("[poc] ⚠ 未在 90s 内捕获 appmsgid。诊断:")
                    print(f"       url={editor.url}")
                    print(f"       submitText={last.get('submitText')!r} isLoading={last.get('isLoading')}")
                    print(f"       dialogs={last.get('dialogs')}")
                    print(f"       messages={last.get('messages')}")
            else:
                print("[poc] dry-run（未保存草稿）。加 --save-draft 实际存草稿。")

        except Exception as exc:  # noqa: BLE001
            try:
                (editor or page).screenshot(path=str(ARTIFACTS_DIR / "error.png"))
            except Exception:
                pass
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        finally:
            timings["total"] = time.monotonic() - t0
            print("\n[poc] ── 耗时计量 (s) ──")
            for k, v in timings.items():
                print(f"  {k:<16} {v:6.2f}")
            print("[poc] 浏览器窗口保留打开，供人工检查。完成后手动关闭。")
            # Note: not closing context so the editor stays open for inspection.

    return 0

# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="PoC: publish WeChat article via Playwright")
    parser.add_argument("--markdown", type=Path, required=True, help="Markdown article path")
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument("--author", default="", help="Author name")
    parser.add_argument("--summary", default="", help="Summary/摘要 (optional)")
    parser.add_argument("--save-draft", action="store_true", help="Actually save draft (default: dry-run)")
    parser.add_argument("--profile", type=Path, default=USER_DATA_DIR, help="Chrome profile dir")
    args = parser.parse_args()

    return publish(
        md_path=args.markdown,
        title=args.title,
        author=args.author,
        summary=args.summary or None,
        save_draft=args.save_draft,
        profile_dir=args.profile,
    )


if __name__ == "__main__":
    sys.exit(main())
