#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "beautifulsoup4>=4.15",
#   "playwright>=1.60",
# ]
# ///
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
    author  : --author → frontmatter author → .config/wechat.toml default_author → ask once & save
    summary : --summary → frontmatter description/summary → first body paragraph (≤120);
              always auto-filled via real keyboard typing into #js_description
    cover   : --cover → frontmatter cover; auto-uploaded when --try-cover is set
              (flow: 封面+ → 从图片库选择 → 上传文件 → 下一步 → 完成)
    original: --declare-original toggles 原创声明 automation (best-effort; checks
              agreement checkbox, confirms modal)

Publish boundary: saves a DRAFT only. Never clicks 发布/群发.

Usage:
    uv run .agents/skills/wechat-article-publisher/scripts/publish.py \
        --article content/origin/YYYY-MM-DD-<slug>/index.md \
        --html    content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html \
        --try-cover --declare-original \
        --save-draft
"""

from __future__ import annotations

import argparse
import html as html_mod
import json
import os
import re
import shutil
import sys
import time
import tomllib
from datetime import datetime
from pathlib import Path

try:
    import playwright  # noqa: F401
except ImportError:
    print("ERROR: playwright not installed. Run: uv run script.py (PEP 723 handles deps)", file=sys.stderr)
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: uv run script.py (PEP 723 handles deps)", file=sys.stderr)
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
ARTIFACTS_DIR = Path(__file__).resolve().parent / ".artifacts"

# ── Config path resolution ──────────────────────────────────────────────
# Canonical location: <repo-root>/.config/wechat.toml (gitignored, per-user).
# Legacy location (pre-2026-06): <skill-dir>/config.toml. Auto-migrated on first
# run so users who already set a default_author don't lose it.
def _resolve_repo_root() -> Path:
    """Walk up from this script until we find a repo marker (AGENTS.md / .git)."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "AGENTS.md").exists() or (parent / ".git").exists():
            return parent
    # Fallback: cwd
    return Path.cwd()

REPO_ROOT = _resolve_repo_root()
CONFIG_DIR = REPO_ROOT / ".config"
CONFIG_PATH = CONFIG_DIR / "wechat.toml"
_LEGACY_CONFIG_PATH = SKILL_DIR / "config.toml"


def _maybe_migrate_legacy_config() -> None:
    """One-shot move of <skill>/config.toml → .config/wechat.toml if needed."""
    if CONFIG_PATH.exists() or not _LEGACY_CONFIG_PATH.exists():
        return
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _LEGACY_CONFIG_PATH.replace(CONFIG_PATH)
        print(f"[publish] 配置已迁移: {_LEGACY_CONFIG_PATH} → {CONFIG_PATH}",
              file=sys.stderr)
    except OSError as exc:
        print(f"[publish] ⚠ 配置迁移失败 ({exc})，继续使用旧路径。",
              file=sys.stderr)

WECHAT_URL = "https://mp.weixin.qq.com/"
HOME_URL_PATTERN = re.compile(r"/cgi-bin/home")
LOGIN_TIMEOUT_MS = 300_000  # 5 min for QR scan + phone confirm

# Article-editor DOM contract (verified against 2026-06 公众号 editor refresh).
SEL_TITLE = "#title"
SEL_AUTHOR = "#author"
SEL_SUMMARY = "#js_description"
SEL_BODY = ".rich_media_content .ProseMirror"
# Visible title ProseMirror. The 2026 editor refresh moved it to `.title-editor__input .ProseMirror`;
# the legacy #js_title_main selector is kept as a fallback for older cached rollouts.
SEL_TITLE_EDITOR = ".title-editor__input .ProseMirror"
SEL_TITLE_EDITOR_LEGACY = "#js_title_main .ProseMirror"
TITLE_MOD = "Meta" if sys.platform == "darwin" else "Control"
SEL_SAVE_DRAFT = "#js_submit button"        # 保存为草稿 (NOT 发布/群发)
SEL_IMG_INPUT = 'input[type="file"][accept*="image"]'

# Rendered-HTML body containers, most-specific first.
BODY_CONTAINERS = ("article.dark-text", ".dark-card", "article", "body")

# ── Config (TOML, stdlib read-only; simple flat write) ───────────────────

def load_config() -> dict:
    _maybe_migrate_legacy_config()
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return {}


def save_default_author(author: str) -> None:
    """Persist default_author back to .config/wechat.toml (flat string keys only)."""
    _maybe_migrate_legacy_config()
    cfg = load_config()
    cfg["default_author"] = author
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    header = ("# wechat-article-publisher 配置（脚本读写，用户可手编）\n"
              "# 解析优先级：CLI → 文章 frontmatter → 本配置 → 首次询问写回\n"
              "# 路径：<repo>/.config/wechat.toml（已 .gitignore）\n\n")
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
        # No dedicated hero wrapper (e.g. warm-editorial style emits a bare
        # <h1> at the top wrapped in a <section>). Capture the first H1 as
        # title fallback AND remove it (and any now-empty wrappers) from the
        # body so the title does not appear twice and doesn't leave blank
        # lines at the top.
        h1 = container.find("h1")
        if h1:
            hero_title = h1.get_text(strip=True)
            # Walk up and remove ancestors that become empty after removing h1,
            # stopping at the container itself. This catches warm-editorial's
            # `<section><h1>...</h1>\n\n</section>` empty-shell pattern.
            ancestors_to_check = []
            p = h1.parent
            while p is not None and p is not container:
                ancestors_to_check.append(p)
                p = p.parent
            h1.decompose()
            for anc in ancestors_to_check:
                if anc not in container.descendants:
                    continue  # already removed by a child decompose
                # If the element has no text and no non-empty child elements,
                # drop it (covers inline-styled empty sections / divs / spans).
                if not anc.get_text(strip=True) and not anc.find(
                    ["img", "video", "iframe", "hr"]
                ):
                    anc.decompose()
                else:
                    break
            # Also drop any leading empty paragraph/section that follows
            while True:
                first_child = container.find(True)
                if not first_child:
                    break
                if first_child.name not in ("p", "section", "div", "br"):
                    break
                txt = first_child.get_text(strip=True)
                if txt or first_child.find(["img", "video", "iframe", "hr"]):
                    break
                first_child.decompose()

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
  // 自动保存时间戳区域：底部状态条，形如 "14:32 已保存"
  const saveIndicator = (() => {
    const el = document.querySelector('#js_edui_editor_status, .editor_status, [class*=editor-status], [class*=save_status]');
    return el ? (el.innerText || '').trim() : '';
  })();
  const buttonText = button ? (button.innerText || '').trim() : '';
  const buttonDisabled = button ? (button.disabled || button.classList.contains('weui-desktop-btn_disabled') || button.classList.contains('btn_loading')) : false;
  return JSON.stringify({
    appmsgid,
    isLoading: (submit && submit.classList.contains('btn_loading')) || buttonDisabled || false,
    buttonText,
    messages,
    saveIndicator,
    // post-save DOM also flashes a "保存成功" label in some variants; capture title value too
    title: (document.querySelector('#title')?.value || '').trim().slice(0,40),
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


def _first_visible_locator(page, selectors: list[str]):
    """Return the first visible locator matching any of the selectors (with count>0)."""
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            if loc.count() > 0 and loc.is_visible(timeout=1_000):
                return loc
        except Exception:
            continue
    return None


def set_input(page, selector: str, value: str, *, use_keyboard: bool = True) -> bool:
    """Set an <input>/<textarea> value.

    WeChat's editor uses Vue-style controlled inputs; just assigning el.value and
    dispatching events doesn't reliably propagate. We type real keystrokes into
    the visible element (click → select-all → delete → type) so the framework
    observes the change.
    """
    loc = page.locator(selector).first
    try:
        if loc.count() == 0:
            return False
        loc.scroll_into_view_if_needed(timeout=3_000)
        loc.click(timeout=3_000)
    except Exception:
        return False
    if use_keyboard:
        page.keyboard.press(f"{TITLE_MOD}+a")
        page.keyboard.press("Delete")
        page.keyboard.type(value, delay=8)
        page.wait_for_timeout(200)
    else:
        page.evaluate(
            "([sel, v]) => { const el = document.querySelector(sel); if (!el) return false; el.focus(); el.value = v; el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); return true; }",
            [selector, value],
        )
    return True


def get_input(page, selector: str):
    return page.evaluate(
        "(sel) => { const els = document.querySelectorAll(sel); for (const el of els) { if (el.offsetParent !== null) return el.value || ''; } return null; }",
        selector,
    )


def ensure_title(editor, title: str) -> bool:
    """Type the title into the visible title ProseMirror; verify via #title sync.

    The visible title is its own ProseMirror editor that syncs to a hidden
    <textarea id=title>. Setting #title.value renders nothing (the textarea
    is visibility:hidden / height:0), so we must type real keystrokes into
    the visible ProseMirror, then read back the synced #title value.
    """
    try:
        loc = _first_visible_locator(editor, [SEL_TITLE_EDITOR, SEL_TITLE_EDITOR_LEGACY])
        if loc is None:
            print(f"[publish] ⚠ 未找到标题 ProseMirror", file=sys.stderr)
            return False
        loc.click(timeout=5_000)
        editor.keyboard.press(f"{TITLE_MOD}+a")
        editor.keyboard.press("Delete")
        editor.keyboard.type(title, delay=10)
        editor.wait_for_timeout(500)
    except Exception as exc:  # noqa: BLE001
        print(f"[publish] ⚠ 标题输入异常: {type(exc).__name__}: {exc}", file=sys.stderr)
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


def _any_modal_open(editor) -> bool:
    """Return True if any visible dialog/modal is on screen (cover/original/crop)."""
    return editor.evaluate("""() => Array.from(document.querySelectorAll(
        '.weui-desktop-dialog:not([style*="display: none"]), .weui-desktop-mask, [role="dialog"]'
      )).some((el) => { const r = el.getBoundingClientRect(); return r.width > 100 && r.height > 100; })""")


def _dismiss_modals(editor) -> None:
    """Best-effort Escape to close any leftover modal (cover/original/crop)."""
    for _ in range(3):
        if not _any_modal_open(editor):
            return
        editor.keyboard.press("Escape")
        editor.wait_for_timeout(600)


def _click_visible(editor, selector: str, *, within: str | None = None, timeout_ms: int = 4_000) -> bool:
    """Click the first element matching `selector` that has a non-zero bounding rect.

    WeChat's DOM often has duplicate hidden elements for the same logical button
    (e.g. 3 `.js_imagedialog` nodes, 2 `.weui-desktop-btn_primary`), so naïve
    .first.click() hits a hidden node. This helper iterates matches (optionally
    scoped by `within` — a CSS selector for a container) and clicks the first
    visible one via JS dispatch.
    """
    if within:
        return bool(editor.evaluate("""(args) => {
          const { within: rootSel, sel } = args;
          const root = document.querySelector(rootSel);
          if (!root) return false;
          const nodes = root.querySelectorAll(sel);
          for (const el of nodes) {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) { el.click(); return true; }
          }
          return false;
        }""", {"within": within, "sel": selector}))
    return bool(editor.evaluate("""(sel) => {
      const nodes = document.querySelectorAll(sel);
      for (const el of nodes) {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) { el.click(); return true; }
      }
      return false;
    }""", selector))


def try_set_cover(editor, cover_path: Path) -> str:
    """Best-effort cover upload. NEVER blocks save: any failure → dismiss modals.

    2026 editor flow (verified via probe_cover_final.py):
      1. Click `.js_cover_btn_area` (the "+ 拖拽或选择封面" placeholder).
      2. JS-click the visible `.js_imagedialog` ("从图片库选择") in the popover.
      3. Wait for `.weui-desktop-dialog_img-picker` image picker modal.
      4. Click `.single_upload_btn_container` (the visible 上传文件 button)
         while listening for a native file chooser → set files.
      5. Wait for the upload to finish (green "上传成功" toast, new image in
         the recent grid auto-selected).
      6. Click the 下一步 primary button in the picker → crop dialog.
      7. Click 完成 in the crop dialog → cover is set.
      8. Verify `.js_cover_preview_new` has a visible <img> with src.

    Returns a short status string (cover-set / uploaded-unconfirmed / error:*).
    """
    try:
        # 1. Open the cover popover.
        cover_area = editor.locator("#js_cover_area .js_cover_btn_area").first
        if cover_area.count() == 0:
            return "no-trigger"
        cover_area.scroll_into_view_if_needed(timeout=3_000)
        cover_area.click(timeout=5_000)
        editor.wait_for_timeout(800)

        # 2. Click 从图片库选择 — must use JS-click because the popover has
        #    duplicate hidden .js_imagedialog nodes.
        if not _click_visible(editor, ".js_imagedialog", within="#js_cover_area", timeout_ms=3_000):
            _dismiss_modals(editor)
            return "no-image-library-btn"
        editor.wait_for_timeout(1_500)
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-01-picker-open.png"))

        # 3. Wait for image picker dialog to appear.
        try:
            editor.wait_for_selector(".weui-desktop-dialog_img-picker",
                                     state="visible", timeout=6_000)
        except PWTimeoutError:
            _dismiss_modals(editor)
            return "picker-not-shown"

        # 4. Click 上传文件 and set cover file via native file chooser.
        #    The widget uses WebUploader which renders a transparent <label>
        #    overlay (id="rt_rt_<random>") that intercepts pointer events over
        #    the visible <a class="single_upload_btn_container"> button. The
        #    hidden <input type=file multiple> lives INSIDE that overlay div.
        #    Dispatching a JS click on the overlay's label (or just calling
        #    set_input_files directly on the file input) bypasses the interception.
        uploaded = False
        # Strategy 1: set_input_files directly on the WebUploader-managed file
        # input inside the image-picker dialog. WebUploader's input is injected
        # at runtime inside .webuploader-container → rt_rt_* → <input type=file>.
        # Playwright can dispatch set_input_files even on display:none inputs.
        try:
            fi_loc = editor.locator(
                ".weui-desktop-dialog_img-picker .webuploader-container input[type='file']"
            ).first
            fi_loc.set_input_files(str(cover_path), timeout=8_000)
            uploaded = True
        except Exception:
            uploaded = False
        # Strategy 2: JS-click the transparent <label> inside the rt_rt_*
        # overlay, listen for file chooser event.
        if not uploaded:
            try:
                with editor.expect_file_chooser(timeout=6_000) as fc_info:
                    editor.evaluate("""() => {
                      const dlg = document.querySelector('.weui-desktop-dialog_img-picker');
                      if (!dlg) return;
                      const label = dlg.querySelector('.webuploader-container label');
                      if (label) { label.click(); return; }
                      // Fallback: any visible element whose click would open chooser
                      const a = dlg.querySelector('a.single_upload_btn_container');
                      if (a) a.click();
                    }""")
                fc_info.value.set_files(str(cover_path))
                uploaded = True
            except PWTimeoutError:
                uploaded = False
        if not uploaded:
            _dismiss_modals(editor)
            return "upload-not-triggered"
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-02-file-set.png"))

        # 5. Wait for upload to finish: a VISIBLE 下一步/确定 primary button in the
        #    picker footer becomes non-disabled (probe showed wechat renders
        #    nested hidden "确定" primaries for sub-controls like "新建分组";
        #    we MUST filter by bounding-rect visibility, not just querySelector).
        #    Also look for "上传成功" toast as a secondary signal, but the
        #    reliable signal is the footer primary becoming clickable.
        deadline = time.monotonic() + 40
        next_ready = False
        while time.monotonic() < deadline:
            state = editor.evaluate("""() => {
              const dlg = document.querySelector('.weui-desktop-dialog_img-picker');
              if (!dlg) return {open:false};
              const prims = Array.from(dlg.querySelectorAll('.weui-desktop-btn_primary'));
              // pick visible primaries (non-zero bounding rect, not display:none)
              const visible = prims.filter(b => {
                if (b.classList.contains('weui-desktop-btn_disabled') || b.disabled) return false;
                const r = b.getBoundingClientRect();
                return r.width > 40 && r.height > 20;
              });
              const texts = visible.map(b => (b.innerText||'').trim());
              const toasts = Array.from(document.querySelectorAll(
                '.weui-desktop-toast, .weui-desktop-toptips, [class*=toast], [class*=toptips]'
              )).map(t => (t.innerText||'').trim()).filter(x => x).slice(0,3);
              return {open:true, texts, toasts};
            }""")
            if state.get("open"):
                texts = state.get("texts", [])
                # Wait until a visible primary with 下一步 OR (确定 + 上传成功 toast)
                if any("下一步" in t for t in texts):
                    next_ready = True
                    break
                if any("上传成功" in t for t in state.get("toasts", [])) and any(t in ("确定","完成") for t in texts):
                    next_ready = True
                    break
            editor.wait_for_timeout(700)
        if not next_ready:
            editor.screenshot(path=str(ARTIFACTS_DIR / "cover-03-upload-timeout.png"))
            _dismiss_modals(editor)
            return "upload-timeout"
        editor.wait_for_timeout(1_200)  # let thumbnail render settle after selection
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-04-next-ready.png"))

        # 6. Click 下一步 in the picker → opens crop dialog. Prefer a visible
        #    primary whose text is 下一步 to avoid clicking inner sub-dialog
        #    "确定" buttons (e.g. the 新建分组 rename control lives inside the
        #    picker DOM with its own primary).
        next_clicked = False
        for _ in range(5):
            next_clicked = bool(editor.evaluate("""() => {
              const dlg = document.querySelector('.weui-desktop-dialog_img-picker');
              if (!dlg) return false;
              const prims = dlg.querySelectorAll('.weui-desktop-btn_primary');
              // first try text==下一步
              for (const b of prims) {
                if (b.disabled || b.classList.contains('weui-desktop-btn_disabled')) continue;
                const r = b.getBoundingClientRect();
                if (r.width<40 || r.height<20) continue;
                if ((b.innerText||'').trim() === '下一步') { b.click(); return true; }
              }
              // fallback: any visible primary
              for (const b of prims) {
                if (b.disabled || b.classList.contains('weui-desktop-btn_disabled')) continue;
                const r = b.getBoundingClientRect();
                if (r.width<40 || r.height<20) continue;
                b.click(); return true;
              }
              return false;
            }"""))
            if next_clicked:
                break
            editor.wait_for_timeout(500)
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-after-next-click.png"))
        if not next_clicked:
            _dismiss_modals(editor)
            return "next-btn-not-found"
        editor.wait_for_timeout(2_000)
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-05-crop-dialog.png"))

        # 7. Crop step: click 完成 primary in the crop/confirm dialog. The crop
        #    dialog is a fresh .weui-desktop-dialog layered on top; we look for
        #    a VISIBLE primary button (non-zero rect) and prefer 完成/确定 text,
        #    scoped to the visible topmost dialog to avoid clicking anything
        #    in the now-background picker.
        crop_deadline = time.monotonic() + 12
        crop_clicked = False
        while time.monotonic() < crop_deadline:
            clicked = editor.evaluate("""() => {
              const dlgs = Array.from(document.querySelectorAll(
                '.weui-desktop-dialog, [role="dialog"]'
              )).filter(d => { const r = d.getBoundingClientRect(); return r.width>200 && r.height>200; });
              // iterate topmost (last in DOM order = on top)
              for (let i = dlgs.length - 1; i >= 0; i--) {
                const d = dlgs[i];
                const prims = d.querySelectorAll('.weui-desktop-btn_primary');
                // prefer 完成/确定/确认
                for (const pref of ['完成','确定','确认','下一步']) {
                  for (const b of prims) {
                    if (b.disabled || b.classList.contains('weui-desktop-btn_disabled')) continue;
                    const r = b.getBoundingClientRect();
                    if (r.width < 40 || r.height < 20) continue;
                    if ((b.innerText||'').trim() === pref) { b.click(); return pref; }
                  }
                }
                // fallback: any visible primary
                for (const b of prims) {
                  if (b.disabled || b.classList.contains('weui-desktop-btn_disabled')) continue;
                  const r = b.getBoundingClientRect();
                  if (r.width < 40 || r.height < 20) continue;
                  b.click(); return 'fallback';
                }
              }
              return '';
            }""")
            if clicked:
                crop_clicked = True
                break
            editor.wait_for_timeout(500)
        if crop_clicked:
            editor.wait_for_timeout(2_500)
        editor.screenshot(path=str(ARTIFACTS_DIR / "cover-06-after-crop.png"))

        # Sometimes there is a second confirmation ("确定" in a "封面已选择"
        # style follow-up); click any remaining non-disabled primary button
        # whose text is 完成/确定/确认 within a visible modal.
        for _ in range(2):
            if not _any_modal_open(editor):
                break
            clicked = editor.evaluate("""() => {
              const candidates = Array.from(document.querySelectorAll(
                '.weui-desktop-dialog .weui-desktop-btn_primary, [role="dialog"] .weui-desktop-btn_primary'
              )).filter(b => {
                if (b.classList.contains('weui-desktop-btn_disabled') || b.disabled) return false;
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
              });
              for (const b of candidates) {
                const t = (b.innerText || '').trim();
                if (t === '完成' || t === '确定' || t === '确认' || t === '下一步') {
                  b.click(); return t;
                }
              }
              // Nothing found — dismiss
              return '';
            }""")
            if clicked:
                editor.wait_for_timeout(1_500)
            else:
                break
        _dismiss_modals(editor)

        # 8. Verify cover preview is visible with a src. WeChat uses several
        #    preview selectors across editor versions; check them all and also
        #    look for an <img> with mmbiz CDN src inside the cover area.
        has_cover = editor.evaluate("""() => {
            const ca = document.querySelector('#js_cover_area');
            if (!ca) return false;
            // Try known preview wrappers
            const previewSels = [
              '.js_cover_preview_new', '.select-cover__preview',
              '.js_cover_preview', '.cover-area__preview',
              '.appmsg_cover', '.js_cover',
            ];
            for (const s of previewSels) {
              const el = ca.querySelector(s);
              if (!el) continue;
              if (getComputedStyle(el).display === 'none') continue;
              const r = el.getBoundingClientRect();
              if (r.width < 10) continue;
              const img = el.querySelector('img');
              if (img && /mmbiz|blob:/.test(img.src || '')) return true;
              if (el.style.backgroundImage && /mmbiz|blob:/.test(el.style.backgroundImage)) return true;
            }
            // Fallback: any mmbiz <img> sized like a cover thumbnail in #js_cover_area
            const imgs = ca.querySelectorAll('img');
            for (const im of imgs) {
              const r = im.getBoundingClientRect();
              if (r.width > 60 && r.height > 60 && /mmbiz/.test(im.src || '')) return true;
            }
            return false;
        }""")
        return "cover-set" if has_cover else "uploaded-unconfirmed"
    except Exception as exc:  # noqa: BLE001
        try:
            (ARTIFACTS_DIR / "cover-ui.html").write_text(editor.content(), encoding="utf-8")
        except Exception:
            pass
        _dismiss_modals(editor)
        return f"error:{type(exc).__name__}"


def try_declare_original(editor) -> str:
    """Best-effort 原创声明 (original declaration).

    Flow (verified via probe earlier in this session):
      1. Click `.js_original_apply` in #js_original → modal opens with
         "声明原创" / 文字原创 pre-selected, author auto-filled.
      2. The modal requires checking an agreement checkbox (if present & not
         already checked).
      3. Click 确定 primary button.
    Returns a status string (original-set / not-needed / error:*). Never blocks
    save; dismisses modal on failure.
    """
    try:
        # Check whether 原创 is already declared (text shows "已声明" or the
        # switch has the "on" class).
        already = editor.evaluate("""() => {
          const area = document.querySelector('#js_original');
          if (!area) return false;
          const t = (area.innerText || '').trim();
          if (t.includes('已声明')) return true;
          if (t.includes('文字原创')) return true;
          if (area.classList.contains('js_original_applied')) return true;
          const sw = area.querySelector('.weui-desktop-switch');
          if (sw && sw.classList.contains('weui-desktop-switch_on')) return true;
          if (t.includes('作者:') && !t.includes('未声明')) return true;
          return false;
        }""")
        if already:
            return "already-set"

        # 1. Click the 原创声明 trigger (".js_original_apply" is the "未声明 >"
        #    text/button in the sidebar; clicking opens the declaration modal).
        trig = editor.locator("#js_original .js_original_apply").first
        if trig.count() == 0:
            return "no-trigger"
        trig.scroll_into_view_if_needed(timeout=3_000)
        trig.click(timeout=5_000)
        editor.wait_for_timeout(1_500)

        # Wait for original-declaration modal to appear (detect via text).
        deadline = time.monotonic() + 8
        modal_ready = False
        while time.monotonic() < deadline:
            visible = editor.evaluate("""() => {
              const dlgs = Array.from(document.querySelectorAll(
                '.weui-desktop-dialog, [role="dialog"]'
              )).filter(d => {
                const r = d.getBoundingClientRect();
                return r.width > 200 && r.height > 200;
              });
              for (const d of dlgs) {
                if ((d.innerText || '').includes('声明原创')
                    || (d.innerText || '').includes('原创声明')) {
                  return d;
                }
              }
              return null;
            }""")
            if visible:
                modal_ready = True
                break
            editor.wait_for_timeout(500)
        if not modal_ready:
            _dismiss_modals(editor)
            return "modal-not-shown"
        editor.screenshot(path=str(ARTIFACTS_DIR / "original-01-modal-open.png"))

        # 2. Check the agreement checkbox if present and unchecked.
        #    The modal contains multiple switches (reward 打赏, white-list 转载,
        #    agreement 协议); ONLY the "我已阅读并同意…" checkbox needs to be
        #    checked for 确定 to enable. We avoid clicking already-checked
        #    switches (which would toggle them off).
        editor.evaluate("""() => {
          const dlgs = Array.from(document.querySelectorAll(
            '.weui-desktop-dialog, [role="dialog"]'
          )).filter(d => {
            const r = d.getBoundingClientRect();
            return r.width > 200 && r.height > 200
              && ((d.innerText||'').includes('声明原创') || (d.innerText||'').includes('原创声明'));
          });
          if (!dlgs.length) return;
          const dlg = dlgs[0];
          // The agreement checkbox is typically the one whose label mentions 同意/协议
          const agreeLabel = Array.from(dlg.querySelectorAll('label, .weui-desktop-form__check, .weui-desktop-check')).find(
            el => /同意|协议|条款/.test((el.innerText||'').trim())
          );
          let cb = null;
          if (agreeLabel) {
            cb = agreeLabel.querySelector('input[type=checkbox]')
              || (agreeLabel.classList.contains('weui-desktop-form__check') ? agreeLabel : null);
          }
          if (!cb) {
            // Fallback: first unchecked checkbox in the modal
            cb = dlg.querySelector('input[type=checkbox]:not(:checked)');
          }
          if (!cb) return;
          if (cb.tagName === 'INPUT' && cb.type === 'checkbox') {
            if (!cb.checked) cb.click();
          } else {
            // custom-styled wrapper
            if (!cb.classList.contains('weui-desktop-form__check_checked')
                && !cb.classList.contains('checked')) {
              cb.click();
            }
          }
        }""")
        editor.wait_for_timeout(500)

        # 3. Wait for the 确定 primary to become enabled (Vue may take a beat
        #    after the agreement checkbox is toggled / content is ready), then
        #    click it. Scope to the original modal AND require visibility (non-
        #    zero bounding rect) to avoid clicking hidden nested buttons.
        confirm_ready_deadline = time.monotonic() + 6
        confirm_clicked = False
        while time.monotonic() < confirm_ready_deadline:
            confirm_clicked = bool(editor.evaluate("""() => {
              const dlgs = Array.from(document.querySelectorAll(
                '.weui-desktop-dialog, [role="dialog"]'
              )).filter(d => {
                const r = d.getBoundingClientRect();
                return r.width > 200 && r.height > 200
                  && ((d.innerText||'').includes('声明原创') || (d.innerText||'').includes('原创声明'));
              });
              if (!dlgs.length) return false;
              const dlg = dlgs[0];
              const prims = dlg.querySelectorAll('.weui-desktop-btn_primary');
              for (const b of prims) {
                if (b.disabled || b.classList.contains('weui-desktop-btn_disabled')) continue;
                const r = b.getBoundingClientRect();
                if (r.width < 40 || r.height < 20) continue;  // skip hidden
                const t = (b.innerText||'').trim();
                if (t === '确定' || t === '确认' || t === '完成') {
                  b.click(); return true;
                }
              }
              return false;
            }"""))
            if confirm_clicked:
                break
            editor.wait_for_timeout(500)
        editor.wait_for_timeout(3_000)
        _dismiss_modals(editor)
        editor.screenshot(path=str(ARTIFACTS_DIR / "original-02-after-confirm.png"))

        # Verify — the post-declare UI shows "文字原创 · 作者: <name> · 已开启快捷转载 >"
        # rather than the literal "已声明" string; treat either as success.
        confirmed = False
        for _ in range(8):
            confirmed = editor.evaluate("""() => {
              const area = document.querySelector('#js_original');
              if (!area) return false;
              const t = (area.innerText || '').trim();
              if (t.includes('已声明')) return true;
              if (t.includes('文字原创')) return true;
              if (area.classList.contains('js_original_applied')) return true;
              if (area.querySelector('.weui-desktop-switch_on')) return true;
              // The "未声明 >" text disappears after successful declaration;
              // if we see an author row (e.g. "作者: Erik") it's declared.
              if (t.includes('作者:') && !t.includes('未声明')) return true;
              return false;
            }""")
            if confirmed:
                break
            editor.wait_for_timeout(500)
        return "original-set" if confirmed else "clicked-unconfirmed"
    except Exception as exc:  # noqa: BLE001
        _dismiss_modals(editor)
        return f"error:{type(exc).__name__}"


def save_draft_and_confirm(editor, *, initial_appmsgid: str = "",
                           expected_title: str = "", timeout_s: int = 30) -> str | None:
    """Click 保存为草稿 and confirm the save actually committed.

    Key invariants:
      - `appmsgid` is ALREADY present in the URL when a fresh editor tab opens
        (WeChat pre-allocates a draft slot), so its presence alone is NOT a
        save signal. We treat it as success only if it CHANGED after our click.
      - WeChat auto-saves constantly as the user types, so an explicit click on
        "保存为草稿" can be a no-op if auto-save just ran. The reliable signal
        is therefore POST-state verification: wait up to timeout_s for either
        (a) an explicit "保存成功" toast, (b) a NEW appmsgid in the URL, or
        (c) the #title value matching expected_title AND the button returning
        to non-loading state for ≥2s.
      - After the wait loop we always read back #title / #author / cover card;
        if title mismatches, we do ONE remediation cycle: re-ensure title →
        re-click save → wait 5s.

    Returns the appmsgid (may be "" on first-save edge case) on success,
    or None on hard failure.
    """
    # Pre-click state snapshot
    pre = json.loads(editor.evaluate(_JS_DRAFT_STATUS))
    pre_appmsgid = pre.get("appmsgid", "") or initial_appmsgid
    pre_title = pre.get("title", "")
    seen_ok_toast = False
    stable_since: float | None = None

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
    print(f"[publish] 已点击『保存为草稿』（pre_appmsgid={pre_appmsgid!r} pre_title_matches={pre_title==expected_title}）",
          file=sys.stderr)

    deadline = time.monotonic() + timeout_s
    last_status = pre
    while time.monotonic() < deadline:
        status = json.loads(editor.evaluate(_JS_DRAFT_STATUS))
        last_status = status
        # Failure toast
        if any(SAVE_FAIL_RE.search(m) for m in status["messages"]):
            editor.screenshot(path=str(ARTIFACTS_DIR / "draft-save-failed.png"))
            fail = next(m for m in status["messages"] if SAVE_FAIL_RE.search(m))
            print(f"ERROR: 保存草稿失败: {fail}", file=sys.stderr)
            return None
        if any(SAVE_OK_RE.search(m) for m in status["messages"]):
            seen_ok_toast = True
        new_appmsgid = status.get("appmsgid", "")
        appmsgid_changed = bool(new_appmsgid) and new_appmsgid != pre_appmsgid
        title_ok = (not expected_title) or status.get("title", "") == expected_title
        loading_done = not status.get("isLoading")
        # Signal (a): explicit OK toast AND loading done
        if seen_ok_toast and loading_done:
            break
        # Signal (b): new appmsgid assigned (first save) AND loading done
        if appmsgid_changed and loading_done:
            break
        # Signal (c): title matches expected AND button done loading AND
        # stayed done for 2s (gives Vue time to flush; auto-save usually
        # has committed everything by this point).
        if title_ok and loading_done:
            if stable_since is None:
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= 2.0:
                break
        else:
            stable_since = None
        editor.wait_for_timeout(500)

    editor.wait_for_timeout(1_500)
    final = json.loads(editor.evaluate(_JS_DRAFT_STATUS))
    final_appmsgid = final.get("appmsgid", "") or pre_appmsgid
    final_title = final.get("title", "")

    # Verify title committed; one remediation cycle if not
    if expected_title and final_title != expected_title:
        print(f"[publish] ⚠ 保存后标题不匹配（期望 {expected_title!r}，实际 {final_title!r}）。"
              f"补填后再保存一次。", file=sys.stderr)
        editor.screenshot(path=str(ARTIFACTS_DIR / "title-not-committed.png"))
        if ensure_title(editor, expected_title):
            editor.wait_for_timeout(500)
            editor.keyboard.press("Tab")
            editor.wait_for_timeout(300)
            for loc in (editor.get_by_role("button", name=re.compile("保存为草稿")),
                        editor.locator(SEL_SAVE_DRAFT)):
                try:
                    if loc.count() > 0:
                        loc.first.scroll_into_view_if_needed(timeout=3_000)
                        loc.first.click(timeout=5_000)
                        break
                except Exception:
                    continue
            editor.wait_for_timeout(5_000)
            final = json.loads(editor.evaluate(_JS_DRAFT_STATUS))
            final_appmsgid = final.get("appmsgid", "") or final_appmsgid
            final_title = final.get("title", "")
            print(f"[publish] 二次保存后: title={final_title!r}", file=sys.stderr)

    final_title_ok = (not expected_title) or final_title == expected_title
    ok = seen_ok_toast or final_title_ok
    print(f"[publish] 保存轮询结束: appmsgid={final_appmsgid!r} title={final_title!r} "
          f"title_ok={final_title_ok} toast_seen={seen_ok_toast}", file=sys.stderr)
    if not ok:
        editor.screenshot(path=str(ARTIFACTS_DIR / "draft-save-unconfirmed.png"))
        return None
    return final_appmsgid

# ── Metadata resolution ──────────────────────────────────────────────────

def resolve_author(cli_author: str, fm: dict) -> str:
    """CLI → frontmatter → .config/wechat.toml → ask once & save."""
    if cli_author:
        return cli_author
    if fm.get("author"):
        return fm["author"]
    cfg = load_config()
    if cfg.get("default_author"):
        return cfg["default_author"]
    try:
        entered = input("[publish] 配置无默认作者，请输入公众号署名（将写入 .config/wechat.toml）: ").strip()
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


# ── Channel archive (content/wechat/) ────────────────────────────────────

# Match path segments content/origin/YYYY-MM-DD-<slug>/<file>
_ORIGIN_RE = re.compile(
    r"(?:^|[\\/])content[\\/]origin[\\/](\d{4}-\d{2}-\d{2}-[^\\/]+)[\\/]"
)

# Read appmsgid from an existing publish-status.md (tolerant to frontmatter
# variations; pulls the first appmsgid: "..." or appmsgid: 100000410 value).
_APPMSGID_RE = re.compile(r'^appmsgid:\s*"?([^"\s]+)"?', re.MULTILINE)


def _read_appmsgid(status_path: Path) -> str | None:
    try:
        text = status_path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = _APPMSGID_RE.search(text)
    return m.group(1) if m else None


def _find_project_root(start: Path) -> Path | None:
    """Walk up looking for a directory that contains BOTH content/origin/ and content/wechat/."""
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "content" / "origin").is_dir() and (candidate / "content" / "wechat").is_dir():
            return candidate
    return None


def ensure_wechat_archive(html_path: Path, article_path: Path | None) -> Path:
    """Ensure a channel-archive copy of the rendered HTML exists under content/wechat/.

    Channel-artifact contract (see AGENTS.md / wechat-publish-workflow):
        content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html
    is the canonical artifact that maps 1:1 to a WeChat draft (and later publish).

    Behavior:
      - If html_path already lives under content/wechat/, use it as-is.
      - If html_path lives under content/origin/YYYY-MM-DD-<slug>/, copy it
        to content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html (creating
        the directory if needed), and return the archived path. The file is
        only copied if the archive is missing or older than the source.
      - Otherwise (exotic path), return html_path unchanged and print a hint.
    """
    html_resolved = html_path.resolve()
    html_str = str(html_resolved)

    # Case 1: already in content/wechat/ → use as-is
    m_wechat = re.search(r"(?:^|[\\/])content[\\/]wechat[\\/](\d{4}-\d{2}-\d{2}-[^\\/]+)[\\/]", html_str)
    if m_wechat:
        return html_path

    # Case 2: in content/origin/YYYY-MM-DD-<slug>/ → copy to content/wechat/
    m_origin = _ORIGIN_RE.search(html_str)
    if m_origin:
        slug = m_origin.group(1)
        project_root = _find_project_root(html_path.parent)
        if project_root is None:
            # fall back: content/wechat/ sibling to content/origin/
            origin_dir = html_resolved.parents[
                next(i for i, p in enumerate(html_resolved.parents)
                     if p.name == "origin")
            ]
            project_root = origin_dir.parent.parent
        wechat_dir = project_root / "content" / "wechat" / slug
        wechat_dir.mkdir(parents=True, exist_ok=True)
        archive_html = wechat_dir / "index.wechat-preview.html"
        # Overwrite guard: if a previous successful publish exists
        # (publish-status.md with a filled appmsgid), don't silently clobber
        # the HTML that corresponds to that WeChat draft. Old drafts remain
        # in WeChat's 草稿箱; overwriting would lose the traceable artifact.
        existing_status = wechat_dir / "publish-status.md"
        existing_appmsgid = None
        if existing_status.exists():
            existing_appmsgid = _read_appmsgid(existing_status)
        if (not archive_html.exists()
                or html_resolved.stat().st_mtime > archive_html.stat().st_mtime):
            if existing_appmsgid:
                # Preserve the previously-published HTML as a historical
                # snapshot before overwriting. Git is the ultimate history,
                # but an explicit local file is friendlier when iterating.
                snapshot = wechat_dir / f"index.wechat-preview.appmsgid-{existing_appmsgid}.html"
                if not snapshot.exists():
                    shutil.copy2(archive_html, snapshot)
                    print(f"[publish] ⚠ 检测到已有草稿 appmsgid={existing_appmsgid}，"
                          f"旧 HTML 已快照到 {snapshot.name}")
            shutil.copy2(html_resolved, archive_html)
            print(f"[publish] 渠道归档: {archive_html}")
        else:
            print(f"[publish] 渠道归档已存在且最新: {archive_html}")
        return archive_html

    # Case 3: exotic path — leave alone, but tell the user
    if article_path is not None:
        m_art = _ORIGIN_RE.search(str(article_path.resolve()))
        if m_art:
            slug = m_art.group(1)
            project_root = _find_project_root(article_path.parent)
            if project_root is not None:
                wechat_dir = project_root / "content" / "wechat" / slug
                wechat_dir.mkdir(parents=True, exist_ok=True)
                archive_html = wechat_dir / "index.wechat-preview.html"
                if (not archive_html.exists()
                        or html_resolved.stat().st_mtime > archive_html.stat().st_mtime):
                    shutil.copy2(html_resolved, archive_html)
                    print(f"[publish] 渠道归档（article-derived slug）: {archive_html}")
                return archive_html
    print(f"[publish] ⚠ 未能识别 --html 路径为 content/origin/ 或 content/wechat/，"
          f"跳过 content/wechat/ 自动归档: {html_path}", file=sys.stderr)
    return html_path


def write_publish_status(archive_html: Path, *, appmsgid: str | None,
                         title: str, author: str, summary: str | None,
                         body_html_len: int, image_count: int,
                         cover_path: Path | None, status: str) -> Path | None:
    """Write content/wechat/YYYY-MM-DD-<slug>/publish-status.md after save.

    Returns the path written, or None if we can't locate the wechat dir.
    The directory name is the full date+slug (matching AGENTS.md convention),
    while the ``slug`` frontmatter field is the bare slug without the date prefix.
    """
    wechat_dir = archive_html.parent
    dir_name = wechat_dir.name
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", dir_name)
    if not m:
        return None
    date_str = m.group(1)
    bare_slug = m.group(2)
    status_path = wechat_dir / "publish-status.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_line = (summary[:60] + "…") if summary and len(summary) > 60 else (summary or "")
    cover_rel = cover_path.name if cover_path else ""

    entry = (
        f"- {now}  status={status}  appmsgid={appmsgid or '(待确认)'}\n"
        f"  - 标题：{title}\n"
        f"  - 作者：{author or '(空)'}\n"
        f"  - 摘要：{summary_line}\n"
        f"  - 正文：{body_html_len} chars，{image_count} 张正文图\n"
        f"  - 封面：{cover_rel or '(无, final review 设置)'}\n"
    )

    if status_path.exists():
        existing = status_path.read_text(encoding="utf-8")
        # Update the frontmatter to reflect the LATEST save, then append the
        # new entry under a ## Draft History section (create if needed).
        existing = _upsert_status_frontmatter(
            existing, date_str=date_str, bare_slug=bare_slug, dir_name=dir_name,
            status=status, appmsgid=appmsgid or "", title=title, author=author,
            image_count=image_count, now=now,
        )
        NEXT_STEP_PROMPT = "下一步：去微信后台「草稿箱」做 final human review"
        head, _, history_sec = existing.partition("\n## Draft History\n")
        # Strip any previously appended "下一步：..." guidance from head AND
        # history so we don't pile up copies on every re-save.
        head_trimmed = re.split(r"\n\s*下一步：[^\n]*\s*$", head.rstrip())[0].rstrip()
        # Refresh the "最新一次保存" intro line so it reflects the CURRENT save.
        head_trimmed = re.sub(
            r"最新一次保存（[^）]+）对应 appmsgid=[^。]+。",
            f"最新一次保存（{now}）对应 appmsgid={appmsgid or '(待确认)'}。",
            head_trimmed,
        )
        history_clean = history_sec
        if "\n下一步：" in history_clean:
            history_clean = history_clean.split("\n下一步：", 1)[0]
        history_clean = history_clean.strip("\n")
        if history_clean:
            new_history = "## Draft History\n\n" + history_clean.rstrip("\n") + "\n" + entry.rstrip("\n")
        else:
            new_history = "## Draft History\n\n" + entry.rstrip("\n")
        new_text = (
            head_trimmed + "\n\n"
            + new_history.rstrip("\n") + "\n\n"
            + NEXT_STEP_PROMPT + "（核对标题/正文/图片、设置封面），再决定是否群发。\n"
        )
    else:
        frontmatter = (
            f"---\n"
            f"date: {date_str}\n"
            f"slug: {bare_slug}\n"
            f"dir: {dir_name}\n"
            f"status: {status}\n"
            f"appmsgid: \"{appmsgid or ''}\"\n"
            f"channel: wechat\n"
            f"title: {title}\n"
            f"author: {author or ''}\n"
            f"image_count: {image_count}\n"
            f"saved_at: {now}\n"
            f"---\n\n"
        )
        new_text = (
            frontmatter
            + f"# 发布状态\n\n"
            + f"最新一次保存（{now}）对应 appmsgid={appmsgid or '(待确认)'}。"
            + "完整草稿/发布历史见下方 Draft History。\n\n"
            + "## Draft History\n\n"
            + entry.rstrip("\n") + "\n\n"
            + "下一步：去微信后台「草稿箱」做 final human review（核对标题/正文/图片、设置封面），再决定是否群发。\n"
        )
    status_path.write_text(new_text, encoding="utf-8")
    return status_path


_FM_ONE_RE = re.compile(rf"^({re.escape('appmsgid')}|{re.escape('status')}|{re.escape('title')}|{re.escape('author')}|{re.escape('image_count')}|{re.escape('saved_at')}):\s*(.*)$", re.MULTILINE)


def _upsert_status_frontmatter(existing: str, *, date_str: str, bare_slug: str,
                               dir_name: str, status: str, appmsgid: str,
                               title: str, author: str, image_count: int,
                               now: str) -> str:
    """Rewrite frontmatter fields (status, appmsgid, title, author, image_count,
    saved_at) to the latest save, leaving date/slug/dir/channel intact.
    Falls back to rewriting the whole frontmatter if structure is unexpected."""
    if not existing.startswith("---"):
        return existing  # unexpected; leave alone
    end = existing.find("\n---", 3)
    if end == -1:
        # No closing --- found (frontmatter delimiter got dropped somehow on a
        # prior write). Rebuild frontmatter from scratch and treat the rest as
        # body, using `\n## Draft History\n` as the body-start landmark when
        # possible; otherwise fall back to first "# 发布状态" heading.
        body_start = existing.find("\n## Draft History\n")
        if body_start == -1:
            body_start = existing.find("\n# 发布状态")
        if body_start == -1:
            # Give up rather than clobber content.
            return existing
        body = existing[body_start:]
        fm_text = ""
    else:
        fm_text = existing[3:end + 1]
        body = existing[end + len("\n---"):]

    updates = {
        "status": status,
        "appmsgid": f'"{appmsgid}"' if appmsgid else '""',
        "title": title.replace(":", " -"),  # naive YAML safety
        "author": author or "",
        "image_count": str(image_count),
        "saved_at": now,
    }

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        if key in updates:
            return f"{key}: {updates[key]}"
        return m.group(0)

    if fm_text:
        new_fm = _FM_ONE_RE.sub(_sub, fm_text)
    else:
        # Rebuild minimal frontmatter, preserving date/slug/dir/channel if possible
        new_fm = (
            f"\ndate: {date_str}\n"
            f"slug: {bare_slug}\n"
            f"dir: {dir_name}\n"
            f"channel: wechat\n"
        )
    # Ensure all expected keys exist
    for k, v in updates.items():
        if f"\n{k}:" not in new_fm:
            new_fm = new_fm.rstrip() + f"\n{k}: {v}\n"
    return "---" + new_fm + body


# ── Main publish flow ────────────────────────────────────────────────────

def publish(article_path: Path | None, html_path: Path | None,
            title: str | None, author: str, summary: str | None,
            cover: str | None, save_draft: bool, profile_dir: Path,
            try_cover: bool = False, declare_original: bool = False) -> int:
    for p in (article_path, html_path):
        if p is not None and not p.exists():
            print(f"ERROR: 输入不存在: {p}", file=sys.stderr)
            return 1
    if not os.path.exists(CHROME_PATH):
        print(f"ERROR: Chrome not found at {CHROME_PATH}. Set CHROME_EXECUTABLE.", file=sys.stderr)
        return 1

    profile_dir.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Channel archive: content/wechat/YYYY-MM-DD-<slug>/index.wechat-preview.html
    # If the rendered HTML is still under content/origin/, auto-copy it to the
    # channel dir and use THAT copy as the payload sent to WeChat. This keeps
    # the channel artifact in lock-step with the saved draft (appmsgid).
    archive_html: Path | None = None
    if html_path is not None:
        html_path = ensure_wechat_archive(html_path, article_path)
        archive_html = html_path

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
            # Snapshot pre-allocated appmsgid (WeChat assigns a draft slot on open;
            # we must NOT treat that as a successful save signal later).
            try:
                initial_appmsgid = (
                    editor.evaluate("() => new URL(location.href).searchParams.get('appmsgid') || ''")
                    or ""
                )
            except Exception:
                initial_appmsgid = ""
            print(f"[publish] 初始 appmsgid（预分配槽位）: {initial_appmsgid or '(none)'}")

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
                # Re-confirm title after each image (baoyu pattern:
                # image insertion can clear the title field).
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
            # WeChat's cover dialog is a custom drag-drop + crop widget. Default
            # is manual (human sets cover in final review); --try-cover automates
            # via: + → 从图片库选择 → 上传文件 → 下一步 → 完成.
            if try_cover and cover_path and cover_path.exists():
                status = try_set_cover(editor, cover_path)
                ok = status == "cover-set"
                print(f"[publish] 封面尝试: {status}"
                      f"{'（已设置）' if ok else '（未确认，请在草稿箱手动设置）'}")
            elif cover_path and cover_path.exists():
                print(f"[publish] 封面: {cover_path.name}（默认手动设置；加 --try-cover 实验性自动上传）")
            elif cover_path:
                print(f"[publish] ⚠ 封面文件不存在: {cover_path}（手动设置）", file=sys.stderr)

            # ── 原创声明 (opt-in; best-effort, never blocks save) ──
            if declare_original:
                orig_status = try_declare_original(editor)
                orig_ok = orig_status in ("original-set", "already-set")
                print(f"[publish] 原创声明: {orig_status}"
                      f"{'（已声明）' if orig_ok else '（请人工确认）'}")

            # Visual-verification screenshot (title/author/summary/cover/body state).
            try:
                editor.screenshot(path=str(ARTIFACTS_DIR / "verify.png"), full_page=True)
            except Exception:
                pass

            # ── Save draft (optional) ──
            if save_draft:
                # Re-confirm title + author + summary right before save (clobber guard).
                # Cover/original flows interact with modals and DOM that can
                # sometimes wipe Vue-controlled inputs; re-set anything missing.
                def _read_all_meta():
                    return editor.evaluate("""() => ({
                      title: (document.querySelector('#title')?.value || '').trim(),
                      author: (document.querySelector('#author')?.value || '').trim(),
                      summary: (document.querySelector('#js_description')?.value || '').trim(),
                    })""")
                pre = _read_all_meta()
                print(f"[publish] 保存前校验: title={len(pre['title'])}ch author={pre['author']!r} summary={len(pre['summary'])}ch", file=sys.stderr)
                if pre["title"] != title:
                    print("[publish] ⚠ 保存前标题被清空，重新写入…", file=sys.stderr)
                    ensure_title(editor, title)
                if author and pre["author"] != author:
                    print(f"[publish] ⚠ 保存前作者被清空（当前 {pre['author']!r}），重新写入…", file=sys.stderr)
                    set_input(editor, SEL_AUTHOR, author)
                if summary and pre["summary"] != summary:
                    print(f"[publish] ⚠ 保存前摘要被清空（当前 {len(pre['summary'])}ch），重新写入…", file=sys.stderr)
                    set_input(editor, SEL_SUMMARY, summary)
                editor.wait_for_timeout(600)
                # Blur active input (Tab out) so Vue commits any pending keystrokes
                # before the save click; otherwise save can race Vue's reactive flush.
                editor.keyboard.press("Tab")
                editor.wait_for_timeout(200)
                # Final readback to confirm commit made it to the model
                pre2 = _read_all_meta()
                print(f"[publish] Tab/blur 后: title={len(pre2['title'])}ch author={pre2['author']!r} summary={len(pre2['summary'])}ch", file=sys.stderr)
                # Scroll to top and capture viewport screenshot of metadata area
                editor.evaluate("window.scrollTo(0,0)")
                editor.wait_for_timeout(400)
                editor.screenshot(path=str(ARTIFACTS_DIR / "pre-save-meta.png"))
                t_save = time.monotonic()
                appmsgid = save_draft_and_confirm(
                    editor,
                    initial_appmsgid=initial_appmsgid,
                    expected_title=title,
                )
                timings["save_draft"] = time.monotonic() - t_save
                if appmsgid is not None:
                    label = f"appmsgid={appmsgid}" if appmsgid else "（toast 确认，URL 暂无 appmsgid）"
                    print(f"[publish] ✓ 草稿已保存  {label}")
                    print("[publish] → 去微信后台「草稿箱」做最终 human review：核对标题/正文/图片，"
                          "（必要时）设置封面，再决定是否发布。")
                    # Write channel publish-status.md next to the archive HTML
                    if archive_html is not None:
                        try:
                            sp = write_publish_status(
                                archive_html,
                                appmsgid=appmsgid or None,
                                title=title, author=author, summary=summary,
                                body_html_len=len(body_html),
                                image_count=len(images),
                                cover_path=cover_path,
                                status="draft-created",
                            )
                            if sp is not None:
                                print(f"[publish] 发布状态已写入: {sp}")
                        except Exception as exc:  # noqa: BLE001
                            print(f"[publish] ⚠ 写入 publish-status.md 失败: {exc}", file=sys.stderr)
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
    parser.add_argument("--author", default="", help="Override author (else frontmatter → .config/wechat.toml)")
    parser.add_argument("--summary", default="", help="Override summary (else frontmatter → first paragraph)")
    parser.add_argument("--cover", help="Override cover image path (else frontmatter cover)")
    parser.add_argument("--try-cover", action="store_true",
                        help="实验性：尝试自动上传封面（默认手动，自动化不稳定）")
    parser.add_argument("--declare-original", action="store_true",
                        help="尝试自动勾选「声明原创」（默认不声明；人工 final review 时可调整）")
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
        declare_original=args.declare_original,
    )


if __name__ == "__main__":
    sys.exit(main())
