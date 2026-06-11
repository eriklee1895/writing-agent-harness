#!/usr/bin/env python3
"""
Publish a WeChat Official Account article (文章) draft via Playwright.

Production successor to baoyu-post-to-wechat's CDP article flow. Reuses the
editor-automation mechanics validated in the PoC: dedicated-profile login
reuse, declarative editor-tab capture, ProseMirror body injection, inline
body-image upload with CDN-completion wait, and draft-save with appmsgid
confirmation.

Pipeline position:
    article.md (frontmatter = metadata authority)
        → wechat-article-renderer → *.wechat-preview.html (styled body)
        → THIS → 草稿箱 → human final review

Metadata authority is the SOURCE .md frontmatter (title/author/description/
cover), NOT the rendered HTML (whose <title>/<meta> are body-derived). The
rendered HTML supplies the styled BODY only.

Resolution:
    title   : --title → frontmatter title → body first H1 (hero text)
    author  : --author → frontmatter author → config.toml default_author → ask once & save
    summary : --summary → frontmatter description/summary → first body paragraph (≤120)
    cover   : --cover → frontmatter cover  (best-effort upload; never blocks save)

Publish boundary: saves a DRAFT only. Never clicks 发布/群发.

Usage:
    uv run python .agents/skills/wechat-article-publisher/scripts/publish.py \
        --article content/source/<slug>/article.md \
        --html    content/wechat/<slug>/article.wechat-preview.html \
        --save-draft
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import sys
import time
import tomllib
from pathlib import Path

try:
    import playwright  # noqa: F401
except ImportError:
    print("ERROR: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from playwright.sync_api import TimeoutError as PWTimeoutError
from playwright.sync_api import sync_playwright

# ── Constants ──────────────────────────────────────────────────────────

CHROME_PATH = os.environ.get(
    "CHROME_EXECUTABLE",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
# Dedicated profile, decoupled from baoyu. Override with --profile or env.
DEFAULT_PROFILE = Path(
    os.environ.get(
        "WECHAT_PUBLISH_PROFILE_DIR",
        str(Path.home() / ".config" / "wechat-article-publisher" / "profile"),
    )
)
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config.toml"
ARTIFACTS_DIR = Path(__file__).resolve().parent / ".artifacts"

WECHAT_URL = "https://mp.weixin.qq.com/"
HOME_URL_PATTERN = re.compile(r"/cgi-bin/home")
LOGIN_TIMEOUT_MS = 300_000  # 5 min for QR scan + phone confirm

# Article-editor DOM contract (extracted from baoyu wechat-article.ts, proven).
SEL_TITLE = "#title"
SEL_AUTHOR = "#author"
SEL_SUMMARY = "#js_description"
SEL_BODY = ".rich_media_content .ProseMirror"
# Visible title is its OWN ProseMirror (syncs to the hidden #title textarea).
# Setting #title.value does NOT render — must type into this editor.
SEL_TITLE_EDITOR = "#js_title_main .ProseMirror"
TITLE_MOD = "Meta" if sys.platform == "darwin" else "Control"
SEL_SAVE_DRAFT = "#js_submit button"        # 保存为草稿 (NOT 发布/群发)
SEL_IMG_INPUT = 'input[type="file"][accept*="image"]'

# Rendered-HTML body containers, most-specific first.
BODY_CONTAINERS = ("article.dark-text", ".dark-card", "article", "body")

# ── Config (TOML, stdlib read-only; simple flat write) ───────────────────

def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}


def save_default_author(author: str) -> None:
    """Persist default_author back to config.toml (flat string keys only)."""
    cfg = load_config()
    cfg["default_author"] = author
    header = ("# wechat-article-publisher 配置（skill 只读，用户手编）\n"
              "# 解析优先级：CLI → frontmatter → 本配置 → 首次询问写回\n\n")
    body = "".join(f'{k} = "{v}"\n' for k, v in cfg.items())
    CONFIG_PATH.write_text(header + body, encoding="utf-8")

# ── Frontmatter / metadata ───────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Extract a minimal YAML-ish frontmatter block into a dict."""
    meta: dict[str, str] = {}
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, flags=re.DOTALL)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.+)$", line.strip())
        if kv:
            meta[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return meta


def strip_frontmatter(text: str) -> str:
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", text, flags=re.DOTALL)
    return text[m.end():] if m else text


def first_paragraph(body_html: str, limit: int = 120) -> str:
    """First substantial body paragraph as a summary fallback (≤limit chars)."""
    soup = BeautifulSoup(body_html, "html.parser")
    for p in soup.find_all("p"):
        t = p.get_text(strip=True)
        if len(t) >= 8 and "WXIMGPH" not in t:
            return t[:limit]
    t = soup.get_text(" ", strip=True)
    return t[:limit]

# ── Body extraction: rendered HTML (preferred) ───────────────────────────

def extract_body_from_html(html_text: str):
    """Extract styled body + images from rendered HTML; strip the hero.

    Returns (body_html, images, hero_title). The renderer's hero section
    carries the article H1 — we capture its text as a title fallback and
    remove the section so the title isn't duplicated inside the body (the
    title goes into the #title field separately). Each <img> becomes a text
    placeholder for later upload. External links are unwrapped to plain text.
    """
    soup = BeautifulSoup(html_text, "html.parser")

    container = None
    for sel in BODY_CONTAINERS:
        container = soup.select_one(sel)
        if container:
            break
    if container is None:
        container = soup

    # Strip hero, capture its heading as the title fallback.
    hero_title = ""
    hero = container.select_one(".dark-hero")
    if hero is not None:
        h = hero.find(["h1", "h2", "h3"])
        if h:
            hero_title = h.get_text(strip=True)
        hero.decompose()
    else:
        h1 = container.find("h1")
        if h1:
            hero_title = h1.get_text(strip=True)

    # Safety net: unwrap external links to plain text (WeChat rejects them).
    for a in container.find_all("a"):
        href = a.get("href", "")
        if href.startswith("http") and "mp.weixin.qq.com" not in href:
            a.replace_with(a.get_text())

    images: list[dict] = []
    for img in list(container.find_all("img")):
        local = img.get("data-local-path") or img.get("src") or ""
        placeholder = f"WXIMGPH{len(images)}WXIMGPH"
        alt = img.get("alt", "")
        # Renderer wraps images as <figure><img><figcaption>…</figcaption></figure>.
        # Keeping the figure leaves an empty leaf where the <img> was (a gap above
        # the caption, nested in the figure → invisible to "empty paragraph"
        # cleanup). So unwrap the figure into a placeholder paragraph + a clean
        # caption paragraph; the post-upload leftover then becomes a top-level
        # empty <p> that trim_empty_blocks() can remove.
        fig = img.find_parent("figure")
        if fig is not None:
            cap = fig.find("figcaption")
            cap_text = cap.get_text(strip=True) if cap else alt
            ph_p = soup.new_tag("p")
            ph_p.string = placeholder
            fig.insert_before(ph_p)
            if cap_text:
                cap_p = soup.new_tag("p")
                cap_p["style"] = "text-align:center;font-size:13px;color:#888;margin:8px 0 16px;"
                cap_p.string = cap_text
                fig.insert_before(cap_p)
            fig.decompose()
        else:
            img.replace_with(soup.new_string(placeholder))
        images.append({"placeholder": placeholder, "path": Path(local), "alt": alt})

    return container.decode_contents(), images, hero_title

# ── Body extraction: markdown fallback ───────────────────────────────────

IMG_RE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)$")


def parse_markdown(md: str, base_dir: Path):
    """Minimal markdown body → <p> blocks + images + first-H1 title.

    The first H1 is treated as the title (captured, not emitted into the body)
    to mirror hero-stripping in the HTML path. Other headings render as bold.
    """
    blocks: list[str] = []
    images: list[dict] = []
    first_h1 = ""
    for raw_para in re.split(r"\n\s*\n", md.strip()):
        para = raw_para.strip()
        if not para:
            continue
        img_match = IMG_RE.match(para)
        if img_match:
            placeholder = f"WXIMGPH{len(images)}WXIMGPH"
            images.append({
                "placeholder": placeholder,
                "path": (base_dir / img_match.group("path")).resolve(),
                "alt": img_match.group("alt"),
            })
            blocks.append(f"<p>{placeholder}</p>")
            continue
        para = re.sub(r"\s*\n\s*", " ", para)
        heading = re.match(r"^(#{1,6})\s+(.*)$", para)
        if heading:
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1 and not first_h1:
                first_h1 = text  # title — do not emit into body
                continue
            para = f"**{text}**"
        escaped = html_mod.escape(para, quote=False)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        blocks.append(f"<p>{escaped}</p>")
    return "".join(blocks), images, first_h1

# ── Editor JS helpers (validated in PoC) ─────────────────────────────────

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

_JS_GET_INPUT = "(selector) => { const el = document.querySelector(selector); return el ? (el.value || '') : null; }"

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
  const sample = imgs.length ? (imgs[0].outerHTML || '').slice(0, 160) : '';
  return JSON.stringify({ total: imgs.length, mmbiz, sample });
}
"""

_JS_DRAFT_STATUS = """
() => {
  const submit = document.querySelector('#js_submit');
  const button = submit ? submit.querySelector('button') : null;
  let appmsgid = '';
  try { appmsgid = new URL(location.href).searchParams.get('appmsgid') || ''; } catch (e) {}
  const messages = Array.from(
    document.querySelectorAll('.weui-desktop-toast, .weui-desktop-toptips, .js_tips, .weui-desktop-toast__content')
  ).map((el) => (el.innerText || el.textContent || '').trim()).filter(Boolean);
  return JSON.stringify({
    appmsgid,
    isLoading: (submit && submit.classList.contains('btn_loading')) || (button && button.disabled) || false,
    messages
  });
}
"""

SAVE_OK_RE = re.compile(r"保存成功|已保存|草稿.*成功|save.*success", re.I)
SAVE_FAIL_RE = re.compile(r"保存.*失败|草稿.*失败|save.*fail", re.I)

_JS_CLEAN_PLACEHOLDERS = r"""
() => {
  const editor = document.querySelector('.rich_media_content .ProseMirror');
  if (!editor) return 0;
  let n = 0, node;
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT, null);
  const hits = [];
  while ((node = walker.nextNode())) {
    if (/WXIMGPH\d+WXIMGPH/.test(node.nodeValue)) hits.push(node);
  }
  for (const t of hits) { t.nodeValue = t.nodeValue.replace(/WXIMGPH\d+WXIMGPH/g, ''); n++; }
  return n;
}
"""

_JS_TRIM_EMPTY = r"""
() => {
  const editor = document.querySelector('.rich_media_content .ProseMirror');
  if (!editor) return 0;
  const hasRealImg = (el) => Array.from(el.querySelectorAll('img'))
    .some((i) => !i.classList.contains('ProseMirror-separator'));
  let removed = 0;
  // Remove empty <p>/<figure> blocks left over from image-placeholder deletion.
  // Image blocks (real <img>) and blocks with text are preserved. The renderer
  // never emits intentionally-empty paragraphs, so this is safe for our content.
  for (const el of Array.from(editor.querySelectorAll('p, figure'))) {
    if (hasRealImg(el)) continue;
    const txt = (el.textContent || '').replace(/[​ \s]/g, '');
    if (txt === '') { el.remove(); removed++; }
  }
  return removed;
}
"""


def set_input(page, selector: str, value: str) -> bool:
    return page.evaluate(_JS_SET_INPUT, [selector, value])


def get_input(page, selector: str):
    return page.evaluate(_JS_GET_INPUT, selector)


def ensure_title(editor, title: str) -> bool:
    """Type the title into the visible title ProseMirror; verify via #title sync.

    The visible title is its own ProseMirror editor (#js_title_main .ProseMirror)
    that syncs to a hidden <textarea id=title>. Setting #title.value renders
    nothing (it's display:hidden), so we click the title editor and type real
    keystrokes ProseMirror captures, then read back the synced #title value.
    """
    try:
        loc = editor.locator(SEL_TITLE_EDITOR).first
        loc.click(timeout=5_000)
        editor.keyboard.press(f"{TITLE_MOD}+a")
        editor.keyboard.press("Delete")
        editor.keyboard.type(title)
        editor.wait_for_timeout(300)
    except Exception as exc:  # noqa: BLE001
        print(f"[publish] ⚠ 标题输入异常: {type(exc).__name__}", file=sys.stderr)
        return False
    return get_input(editor, SEL_TITLE) == title


def img_count(page) -> dict:
    return json.loads(page.evaluate(_JS_IMG_COUNT))


def wait_for_cdn(page, expected: int, timeout_s: int = 120) -> dict:
    """Wait until `expected` body images carry an mmbiz.qpic.cn URL."""
    deadline = time.monotonic() + timeout_s
    last = img_count(page)
    while time.monotonic() < deadline:
        last = img_count(page)
        if last["mmbiz"] >= expected:
            return last
        page.wait_for_timeout(1_000)
    return last


def upload_body_images(editor, images: list[dict]) -> dict:
    """Replace each placeholder with an uploaded body image (validated flow).

    WeChat appears to serialize body-image uploads, so we wait for each image
    to reach the CDN before starting the next — otherwise the 2nd+ upload's
    DOM insert stalls behind the 1st and times out.
    """
    uploaded = 0
    for i, img in enumerate(images):
        if not img["path"].exists():
            print(f"[publish] ⚠ 图片不存在，跳过: {img['path']}", file=sys.stderr)
            continue
        if not editor.evaluate(_JS_SELECT_PLACEHOLDER, img["placeholder"]):
            print(f"[publish] ⚠ 编辑器内未找到占位符 {img['placeholder']}", file=sys.stderr)
            continue
        editor.keyboard.press("Backspace")  # delete selected placeholder text
        before = img_count(editor)["total"]
        editor.locator(SEL_IMG_INPUT).first.set_input_files(str(img["path"]))
        # Wait for the editor img count to increase (upload + insert). Large
        # images on a slow link can take a while; 60s avoids dropping an image.
        deadline = time.monotonic() + 60
        ok = False
        while time.monotonic() < deadline:
            if img_count(editor)["total"] >= before + 1:
                ok = True
                break
            editor.wait_for_timeout(500)
        if ok:
            uploaded += 1
            print(f"[publish] 图片 {i + 1}/{len(images)} 已插入: {img['path'].name}")
            # Serialize: wait for THIS image to reach the CDN before the next.
            wait_for_cdn(editor, uploaded, timeout_s=60)
        else:
            print(f"[publish] ⚠ 图片 {i + 1} 上传超时: {img['path'].name}", file=sys.stderr)
    return {"requested": len(images), "uploaded": uploaded}


def _cover_modal_open(editor) -> bool:
    return editor.evaluate("""() => Array.from(document.querySelectorAll(
        '.weui-desktop-dialog, .weui-desktop-mask, [class*=cover_pop], [class*=cover_dialog], [class*=js_cover_null_pop]'
      )).some((el) => el.offsetParent !== null)""")


def try_set_cover(editor, cover_path: Path) -> str:
    """Best-effort cover upload. NEVER blocks save: any failure → dismiss + manual.

    Flow (from the dumped cover dialog structure): click cover area → dialog →
    『本地上传』(triggers a native file chooser) → set file → 裁剪 → 完成. If any
    step fails, dump the cover UI and Escape any leftover modal so draft-save is
    never blocked. Returns a short status string.
    """
    try:
        # 1. Open the cover dialog.
        trigger = None
        for loc in (editor.locator("#js_cover_area"),
                    editor.locator(".js_cover_btn_area"),
                    editor.get_by_text(re.compile(r"(选择|添加|上传).*封面|封面.*(选择|上传)"))):
            if loc.count() > 0:
                trigger = loc.first
                break
        if trigger is None:
            return "no-trigger"
        trigger.scroll_into_view_if_needed(timeout=3_000)
        trigger.click(timeout=5_000)
        editor.wait_for_timeout(1_500)

        # 2. Click 本地上传 → capture native file chooser (or a revealed DOM input).
        local_btn = editor.get_by_text("本地上传", exact=False)
        if local_btn.count() == 0:
            try:
                (ARTIFACTS_DIR / "cover-ui.html").write_text(editor.content(), encoding="utf-8")
            except Exception:
                pass
            if _cover_modal_open(editor):
                editor.keyboard.press("Escape")
            return "no-local-upload-btn"
        uploaded = False
        try:
            with editor.expect_file_chooser(timeout=6_000) as fc_info:
                local_btn.first.click(timeout=5_000)
            fc_info.value.set_files(str(cover_path))
            uploaded = True
        except PWTimeoutError:
            inp = editor.locator('input[type="file"][accept*="image"]')
            if inp.count() > 0:
                inp.last.set_input_files(str(cover_path))
                uploaded = True
        if not uploaded:
            if _cover_modal_open(editor):
                editor.keyboard.press("Escape")
            return "upload-not-triggered"

        # 3. Wait for the uploaded image to load into the cropper BEFORE 完成 —
        #    clicking 完成 too early yields "必须插入一张图片".
        ready_deadline = time.monotonic() + 20
        while time.monotonic() < ready_deadline:
            ready = editor.evaluate("""() => {
              const loading = document.querySelector('[class*=js_cover_loading], [class*=cover_loading]');
              const loadingVisible = loading && loading.offsetParent !== null;
              const cropImg = Array.from(document.querySelectorAll(
                '[class*=cover] img, [class*=crop] img, .select-cover__preview img'))
                .find((i) => (i.getAttribute('src') || '').length > 20);
              return !loadingVisible && !!cropImg;
            }""")
            if ready:
                break
            editor.wait_for_timeout(500)

        # 4. Confirm. 完成 may appear for the crop step then the dialog.
        for _ in range(3):
            done = editor.get_by_role("button", name=re.compile("完成"))
            if done.count() == 0:
                done = editor.get_by_text("完成", exact=True)
            if done.count() == 0:
                break
            try:
                done.first.click(timeout=3_000)
                editor.wait_for_timeout(1_500)
            except Exception:
                break

        # 5. Verify a cover preview now exists.
        has_cover = editor.evaluate("""() => {
            const p = document.querySelector(
              '.js_cover_preview_new img, .js_cover_preview_square img, #js_cover_area img');
            return !!(p && (p.getAttribute('src') || '').length > 0);
        }""")

        # 5. Safety: if a modal is still open, Escape so save is never blocked.
        if _cover_modal_open(editor):
            editor.keyboard.press("Escape")
            editor.wait_for_timeout(500)
        return "cover-set" if has_cover else "uploaded-unconfirmed"
    except Exception as exc:  # noqa: BLE001
        try:
            (ARTIFACTS_DIR / "cover-ui.html").write_text(editor.content(), encoding="utf-8")
        except Exception:
            pass
        try:
            if _cover_modal_open(editor):
                editor.keyboard.press("Escape")
        except Exception:
            pass
        return f"error:{type(exc).__name__}"


def save_draft_and_confirm(editor, timeout_s: int = 120) -> str | None:
    """Click 保存为草稿 robustly and confirm via appmsgid OR success toast.

    Returns the appmsgid (may be "" if confirmed only via toast) on success,
    or None on timeout/failure. Draft-save confirmation is flaky on WeChat's
    side (observed 1s vs >90s for identical content), so we use multiple
    signals and a generous timeout instead of gating on appmsgid + !isLoading.
    """
    clicked = False
    for loc in (editor.get_by_role("button", name=re.compile("保存为草稿")),
                editor.locator(SEL_SAVE_DRAFT)):
        try:
            if loc.count() > 0:
                loc.first.scroll_into_view_if_needed(timeout=3_000)
                loc.first.click(timeout=10_000)
                clicked = True
                break
        except Exception:
            continue
    if not clicked:
        print("[publish] ⚠ 未找到『保存为草稿』按钮", file=sys.stderr)
        return None

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = json.loads(editor.evaluate(_JS_DRAFT_STATUS))
        if any(SAVE_FAIL_RE.search(m) for m in status["messages"]):
            editor.screenshot(path=str(ARTIFACTS_DIR / "draft-save-failed.png"))
            fail = next(m for m in status["messages"] if SAVE_FAIL_RE.search(m))
            print(f"ERROR: 保存草稿失败: {fail}", file=sys.stderr)
            return None
        if status["appmsgid"]:
            return status["appmsgid"]
        if any(SAVE_OK_RE.search(m) for m in status["messages"]):
            return status["appmsgid"]  # may be "" — toast-confirmed
        editor.wait_for_timeout(1_000)
    return None

# ── Metadata resolution ──────────────────────────────────────────────────

def resolve_author(cli_author: str, fm: dict) -> str:
    """CLI → frontmatter → config.toml → ask once & save."""
    if cli_author:
        return cli_author
    if fm.get("author"):
        return fm["author"]
    cfg = load_config()
    if cfg.get("default_author"):
        return cfg["default_author"]
    try:
        entered = input("[publish] 配置无默认作者，请输入公众号署名（将写入 config.toml）: ").strip()
    except EOFError:
        return ""
    if entered:
        save_default_author(entered)
    return entered


def load_article(article_path: Path | None, html_path: Path | None):
    """Resolve (frontmatter, body_html, images, h1_title) from the inputs.

    Metadata frontmatter comes from the source .md (article_path). The body
    comes from the rendered HTML if given, else from the .md (minimal render).
    """
    fm: dict = {}
    md_body, md_base = "", Path.cwd()
    if article_path is not None:
        text = article_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        md_body = strip_frontmatter(text)
        md_base = article_path.parent

    if html_path is not None:
        body_html, images, h1_title = extract_body_from_html(
            html_path.read_text(encoding="utf-8"))
    else:
        body_html, images, h1_title = parse_markdown(md_body, md_base)

    return fm, body_html, images, h1_title

# ── Main publish flow ────────────────────────────────────────────────────

def publish(article_path: Path | None, html_path: Path | None,
            title: str | None, author: str, summary: str | None,
            cover: str | None, save_draft: bool, profile_dir: Path,
            try_cover: bool = False) -> int:
    for p in (article_path, html_path):
        if p is not None and not p.exists():
            print(f"ERROR: 输入不存在: {p}", file=sys.stderr)
            return 1
    if not os.path.exists(CHROME_PATH):
        print(f"ERROR: Chrome not found at {CHROME_PATH}. Set CHROME_EXECUTABLE.", file=sys.stderr)
        return 1

    profile_dir.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    fm, body_html, images, h1_title = load_article(article_path, html_path)

    # Resolve metadata (frontmatter is authority for per-article fields).
    title = title or fm.get("title") or h1_title
    author = resolve_author(author, fm)
    summary = summary or fm.get("description") or fm.get("summary") or first_paragraph(body_html)
    # Cover: --cover resolves relative to CWD; frontmatter cover relative to .md dir.
    cover_path = None
    if cover:
        cover_path = Path(cover) if Path(cover).is_absolute() else (Path.cwd() / cover).resolve()
    else:
        cover_ref = fm.get("cover") or fm.get("coverImage") or fm.get("image")
        if cover_ref:
            base = article_path.parent if article_path else Path.cwd()
            cover_path = (Path(cover_ref) if Path(cover_ref).is_absolute()
                          else (base / cover_ref).resolve())

    if not title:
        print("ERROR: 缺少标题（--title / frontmatter title / 正文 H1 均无）", file=sys.stderr)
        return 1

    print(f"[publish] 正文: {len(body_html)} chars, {len(images)} 图")
    print(f"[publish] 标题: {title}")
    print(f"[publish] 作者: {author or '(空)'}")
    print(f"[publish] 摘要: {(summary[:40] + '…') if summary else '(空)'}")
    print(f"[publish] 封面: {cover_path if cover_path else '(无, 手动设置)'}")

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
        page = None
        try:
            page = context.new_page()
            page.goto(WECHAT_URL, wait_until="domcontentloaded", timeout=30_000)

            # ── Login: reuse profile or wait for QR scan ──
            t_login = time.monotonic()
            if not HOME_URL_PATTERN.search(page.url):
                try:
                    quick = page.get_by_text("微信快捷登录", exact=False)
                    if quick.count() > 0:
                        quick.first.click(timeout=3_000)
                except Exception:
                    pass
                print("[publish] 未检测到登录态。请在弹出的 Chrome 窗口扫码登录"
                      "（或点『微信快捷登录』）。等待进入后台…")
                try:
                    page.wait_for_url(HOME_URL_PATTERN, timeout=LOGIN_TIMEOUT_MS)
                except PWTimeoutError:
                    print("ERROR: 登录超时（5 分钟内未进入 /cgi-bin/home）。", file=sys.stderr)
                    return 1
            timings["login_wait"] = time.monotonic() - t_login
            print("[publish] 已登录后台。")

            # ── Open the article (文章) editor — new tab ──
            t_editor = time.monotonic()
            page.wait_for_selector(".new-creation__menu-item", timeout=20_000)
            article_menu = page.locator(
                ".new-creation__menu-item .new-creation__menu-title"
            ).filter(has_text=re.compile(r"^\s*文章\s*$"))
            if article_menu.count() == 0:
                page.screenshot(path=str(ARTIFACTS_DIR / "menu-not-found.png"))
                print("ERROR: 首页未找到『文章』创作入口。截图已存。", file=sys.stderr)
                return 1
            with context.expect_page(timeout=30_000) as new_page_info:
                article_menu.first.click()
            editor = new_page_info.value
            editor.wait_for_load_state("domcontentloaded")
            editor.wait_for_selector(SEL_BODY, state="visible", timeout=30_000)
            timings["open_editor"] = time.monotonic() - t_editor
            print("[publish] 文章编辑器已打开。")

            # ── Inject body, then upload images ──
            t_fill = time.monotonic()
            body_result = json.loads(editor.evaluate(_JS_INSERT_BODY, body_html))
            if not body_result.get("ok"):
                editor.screenshot(path=str(ARTIFACTS_DIR / "body-insert-failed.png"))
                print(f"ERROR: 正文注入失败: {body_result}", file=sys.stderr)
                return 1
            print(f"[publish] 正文已注入 (innerText={body_result['textLength']} chars)")

            img_summary = {"requested": 0, "uploaded": 0}
            if images:
                img_summary = upload_body_images(editor, images)
                stats = (wait_for_cdn(editor, img_summary["uploaded"])
                         if img_summary["uploaded"] else img_count(editor))
                # Remove leftover placeholders from failed uploads, then trim
                # empty paragraphs left where images were extracted (the gap
                # between an image and its caption).
                leftover = editor.evaluate(_JS_CLEAN_PLACEHOLDERS)
                trimmed = editor.evaluate(_JS_TRIM_EMPTY)
                print(f"[publish] 正文图片: 请求 {img_summary['requested']} / "
                      f"已插入 {img_summary['uploaded']} / CDN {stats['mmbiz']}/{stats['total']}"
                      f"（清理空行 {trimmed}）")
                if leftover:
                    print(f"[publish] ⚠ 清理了 {leftover} 个未上传成功的图片占位符，"
                          f"对应图片缺失，请人工补图。", file=sys.stderr)
                if img_summary["uploaded"] and stats["mmbiz"] < img_summary["uploaded"]:
                    print("[publish] ⚠ 部分图片未确认上 CDN；保存可能不稳，请人工检查。", file=sys.stderr)

            # ── Set metadata AFTER body/images (so they aren't clobbered) ──
            if ensure_title(editor, title):
                print("[publish] 标题已写入 #title 并回读校验通过。")
            else:
                print(f"[publish] ⚠ 标题回读不一致（期望: {title}）", file=sys.stderr)
            if author:
                set_input(editor, SEL_AUTHOR, author)
            if summary:
                set_input(editor, SEL_SUMMARY, summary)
            timings["fill"] = time.monotonic() - t_fill

            # ── Cover (opt-in, experimental, never blocks save) ──
            # WeChat's cover dialog is a custom drag-drop + crop widget whose
            # local-upload path doesn't complete reliably via automation. Cover
            # is therefore MANUAL by default; --try-cover attempts it anyway.
            if try_cover and cover_path and cover_path.exists():
                status = try_set_cover(editor, cover_path)
                ok = status == "cover-set"
                print(f"[publish] 封面尝试: {status}"
                      f"{'（已设置）' if ok else '（未确认，请在草稿箱手动设置）'}")
            elif cover_path and cover_path.exists():
                print(f"[publish] 封面: {cover_path.name}（默认手动设置；加 --try-cover 实验性自动上传）")
            elif cover_path:
                print(f"[publish] ⚠ 封面文件不存在: {cover_path}（手动设置）", file=sys.stderr)

            # Visual-verification screenshot (title/author/summary/cover/body state).
            try:
                editor.screenshot(path=str(ARTIFACTS_DIR / "verify.png"), full_page=True)
            except Exception:
                pass

            # ── Save draft (optional) ──
            if save_draft:
                # Re-confirm title right before save (clobber guard).
                if get_input(editor, SEL_TITLE) != title:
                    print("[publish] ⚠ 保存前标题被清空，重新写入…", file=sys.stderr)
                    ensure_title(editor, title)
                t_save = time.monotonic()
                appmsgid = save_draft_and_confirm(editor)
                timings["save_draft"] = time.monotonic() - t_save
                if appmsgid is not None:
                    label = f"appmsgid={appmsgid}" if appmsgid else "（toast 确认，URL 暂无 appmsgid）"
                    print(f"[publish] ✓ 草稿已保存  {label}")
                    print("[publish] → 去微信后台「草稿箱」做最终 human review：核对标题/正文/图片，"
                          "（必要时）设置封面，再决定是否发布。")
                else:
                    editor.screenshot(path=str(ARTIFACTS_DIR / "appmsgid-timeout.png"))
                    print(f"[publish] ⚠ 保存未确认（{int(timings['save_draft'])}s）。url={editor.url}",
                          file=sys.stderr)
                    print("[publish] 草稿可能已自动保存，请去「草稿箱」人工确认。截图已存。", file=sys.stderr)
                    return 1
            else:
                print("[publish] dry-run（未保存草稿）。加 --save-draft 实际存草稿。")

        except Exception as exc:  # noqa: BLE001
            try:
                (editor or page).screenshot(path=str(ARTIFACTS_DIR / "error.png"))
            except Exception:
                pass
            print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        finally:
            timings["total"] = time.monotonic() - t0
            print("\n[publish] ── 耗时计量 (s) ──")
            for k, v in timings.items():
                print(f"  {k:<16} {v:6.2f}")
            print("[publish] 浏览器窗口保留打开，供人工检查。")

    return 0

# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Publish WeChat article draft via Playwright")
    parser.add_argument("--article", type=Path, help="Source article.md (frontmatter = metadata authority)")
    parser.add_argument("--html", type=Path, help="Rendered .wechat-preview.html (styled body; preferred)")
    parser.add_argument("--title", help="Override title (else frontmatter title → body H1)")
    parser.add_argument("--author", default="", help="Override author (else frontmatter → config.toml)")
    parser.add_argument("--summary", default="", help="Override summary (else frontmatter → first paragraph)")
    parser.add_argument("--cover", help="Override cover image path (else frontmatter cover)")
    parser.add_argument("--try-cover", action="store_true",
                        help="实验性：尝试自动上传封面（默认手动，自动化不稳定）")
    parser.add_argument("--save-draft", action="store_true", help="Save draft (default: dry-run)")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE, help="Chrome profile dir")
    args = parser.parse_args()

    if args.article is None and args.html is None:
        parser.error("需要 --article 和/或 --html 至少一个")

    return publish(
        article_path=args.article,
        html_path=args.html,
        title=args.title,
        author=args.author,
        summary=args.summary or None,
        cover=args.cover,
        save_draft=args.save_draft,
        profile_dir=args.profile,
        try_cover=args.try_cover,
    )


if __name__ == "__main__":
    sys.exit(main())
