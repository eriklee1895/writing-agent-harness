#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown>=3.6"]
# ///
"""Convert article.md -> a polished single-page report.html.

Deterministic MD->HTML so verbatim code is never altered by an LLM.
- markdown (extra/tables/fenced_code/toc/sane_lists)
- ```mermaid blocks -> <div class="mermaid"> (unescaped)
- ![img] + *caption* -> <figure><img><figcaption>
- 文件:`path` lines -> filename tab before code blocks
- sidebar nav from h2/h3 toc tokens
- Tailwind-free hand CSS; GSAP+ScrollTrigger reveals; Mermaid 10; highlight.js
"""
from __future__ import annotations
import html
import re
from pathlib import Path

import markdown

DIR = Path(__file__).resolve().parent
SRC = DIR / "article.md"
OUT = DIR / "report.html"


def split_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n")
            body = text[end + 4 :].lstrip("\n")
            cur_key = None
            for line in block.splitlines():
                m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
                if m:
                    cur_key = m.group(1)
                    meta[cur_key] = m.group(2).strip().strip('"')
                elif line.strip().startswith("- ") and cur_key:
                    meta.setdefault(cur_key + "_list", "")
            return meta, body
    return meta, text


def build_toc_nav(toc_tokens: list) -> str:
    items = []
    for t in toc_tokens:
        if t["level"] != 2:
            continue
        children = "".join(
            f'<a class="nav-sub" href="#{c["id"]}">{html.escape(strip_tags(c["name"]))}</a>'
            for c in t.get("children", [])
            if c["level"] == 3
        )
        items.append(
            f'<div class="nav-group">'
            f'<a class="nav-top" href="#{t["id"]}">{html.escape(strip_tags(t["name"]))}</a>'
            f'{children}</div>'
        )
    return "\n".join(items)


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def postprocess(html_body: str) -> str:
    # 1) mermaid fenced blocks -> div.mermaid (unescape entities markdown added)
    def mermaid_sub(m: re.Match) -> str:
        code = html.unescape(m.group(1))
        return f'<div class="mermaid">{code}</div>'

    html_body = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        mermaid_sub,
        html_body,
        flags=re.DOTALL,
    )

    # 2) image + caption -> figure
    html_body = re.sub(
        r'<p>\s*(<img[^>]+>)\s*</p>\s*<p><em>(.*?)</em></p>',
        lambda m: f'<figure class="fig reveal">{m.group(1)}<figcaption>{m.group(2)}</figcaption></figure>',
        html_body,
        flags=re.DOTALL,
    )
    # cover (image alone, no caption) -> figure.cover
    html_body = re.sub(
        r'<p>\s*(<img[^>]+alt="Steer[^>]+>)\s*</p>',
        lambda m: f'<figure class="fig cover reveal">{m.group(1)}</figure>',
        html_body,
    )
    # any remaining lone image -> figure
    html_body = re.sub(
        r'<p>\s*(<img[^>]+>)\s*</p>',
        lambda m: f'<figure class="fig reveal">{m.group(1)}</figure>',
        html_body,
    )

    # 3) 文件:`path` paragraph -> filename tab class
    html_body = re.sub(
        r'<p>文件:(<code>.*?</code>)</p>',
        lambda m: f'<p class="code-file">{m.group(1)}</p>',
        html_body,
    )

    # 4) wrap tables for horizontal scroll + reveal
    html_body = re.sub(
        r'<table>',
        '<div class="table-wrap reveal"><table>',
        html_body,
    )
    html_body = re.sub(r'</table>', '</table></div>', html_body)

    # 5) mark mermaid + pre + h2 for reveal
    html_body = html_body.replace('<div class="mermaid">', '<div class="mermaid reveal">')
    html_body = re.sub(r'<pre>', '<pre class="reveal">', html_body)
    return html_body


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    meta, body = split_frontmatter(raw)

    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists", "admonition"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
    )
    html_body = md.convert(body)
    nav = build_toc_nav(md.toc_tokens)
    html_body = postprocess(html_body)

    # Pull the H1 out of body to use as hero (keep it removed from flow)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_body, flags=re.DOTALL)
    hero_title = strip_tags(h1_match.group(1)) if h1_match else meta.get("title", "")
    # remove the first h1 and the cover figure right after it from body (they go to hero)
    if h1_match:
        html_body = html_body.replace(h1_match.group(0), "", 1)
    cover_match = re.search(r'<figure class="fig cover reveal">.*?</figure>', html_body, flags=re.DOTALL)
    cover_html = cover_match.group(0) if cover_match else ""
    if cover_match:
        html_body = html_body.replace(cover_match.group(0), "", 1)

    title = meta.get("title", hero_title)
    summary = meta.get("summary", "")
    date = meta.get("date", "")
    register = meta.get("register", "")

    page = TEMPLATE
    page = page.replace("{{TITLE}}", html.escape(title))
    page = page.replace("{{HERO_TITLE}}", html.escape(hero_title or title))
    page = page.replace("{{SUMMARY}}", html.escape(summary))
    page = page.replace("{{DATE}}", html.escape(date))
    page = page.replace("{{REGISTER}}", html.escape(register))
    page = page.replace("{{COVER}}", cover_html)
    page = page.replace("{{NAV}}", nav)
    page = page.replace("{{BODY}}", html_body)

    OUT.write_text(page, encoding="utf-8")
    imgs = page.count("<img")
    merm = page.count('class="mermaid')
    print(f"Wrote {OUT} ({len(page)} bytes); images={imgs} mermaid={merm} h2nav={nav.count('nav-top')}")
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<style>
:root{
  --bg:#0a0d14; --bg2:#0d111a; --panel:#11161f; --panel2:#141a25;
  --ink:#cdd6e6; --ink-strong:#eef2f8; --muted:#7c8aa3; --faint:#586074;
  --line:#1d2533; --line2:#28324a;
  --cyan:#33d1e3; --cyan-dim:#1aa3b8; --amber:#f0ad4e; --violet:#9a8cff;
  --maxw:880px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
  font-size:16.5px; line-height:1.85; -webkit-font-smoothing:antialiased;
  background-image:radial-gradient(900px 500px at 80% -8%, rgba(51,209,227,.07), transparent 60%),
                   radial-gradient(700px 400px at -5% 10%, rgba(154,140,255,.06), transparent 55%);
  background-attachment:fixed;
}
::selection{background:rgba(51,209,227,.28); color:#fff}
a{color:var(--cyan); text-decoration:none}
a:hover{color:#7fe3ef}

/* reading progress */
#progress{position:fixed; top:0; left:0; height:3px; width:0%;
  background:linear-gradient(90deg,var(--cyan),var(--violet)); z-index:60; box-shadow:0 0 12px rgba(51,209,227,.6)}

/* layout */
.shell{display:grid; grid-template-columns:288px minmax(0,1fr); gap:0; max-width:1280px; margin:0 auto}
aside{position:sticky; top:0; align-self:start; height:100vh; overflow-y:auto; padding:30px 22px 60px;
  border-right:1px solid var(--line); background:linear-gradient(180deg,rgba(13,17,26,.6),transparent)}
aside .brand{font-family:'Space Grotesk',sans-serif; font-weight:700; letter-spacing:.5px; color:var(--ink-strong); font-size:15px; margin-bottom:4px}
aside .brand b{color:var(--cyan)}
aside .brand-sub{color:var(--muted); font-size:12px; margin-bottom:22px; letter-spacing:.3px}
.nav-group{margin-bottom:6px}
.nav-top{display:block; color:var(--ink); font-weight:600; font-size:13.5px; padding:6px 10px; border-radius:8px; border-left:2px solid transparent}
.nav-top:hover{background:var(--panel); color:var(--ink-strong)}
.nav-sub{display:block; color:var(--muted); font-size:12.5px; padding:4px 10px 4px 20px; border-left:2px solid transparent}
.nav-sub:hover{color:var(--cyan)}
.nav-top.active{color:var(--cyan); border-left-color:var(--cyan); background:rgba(51,209,227,.06)}
.nav-sub.active{color:var(--ink-strong); border-left-color:var(--line2)}

main{min-width:0; padding:0 0 120px}
.wrap{max-width:var(--maxw); margin:0 auto; padding:0 30px}

/* hero */
.hero{padding:78px 0 30px; border-bottom:1px solid var(--line); margin-bottom:14px}
.hero .kicker{font-family:'Space Grotesk',sans-serif; color:var(--cyan); font-weight:600; letter-spacing:3px; font-size:12.5px; text-transform:uppercase; margin-bottom:18px}
.hero h1{font-family:'Space Grotesk',sans-serif; font-weight:700; color:var(--ink-strong);
  font-size:clamp(28px,4.4vw,46px); line-height:1.18; letter-spacing:-.3px; margin:0 0 20px}
.hero .lead{color:var(--muted); font-size:16px; line-height:1.8; max-width:760px; margin:0 0 22px}
.hero .meta{display:flex; flex-wrap:wrap; gap:10px; font-size:12.5px; color:var(--muted)}
.hero .meta span{border:1px solid var(--line2); border-radius:999px; padding:4px 13px; background:rgba(255,255,255,.015)}
.hero .meta b{color:var(--cyan); font-weight:600}
.hero .cover{margin-top:34px}

/* typography */
main h2{font-family:'Space Grotesk',sans-serif; color:var(--ink-strong); font-weight:700;
  font-size:clamp(22px,3vw,30px); line-height:1.3; letter-spacing:-.2px; margin:72px 0 8px; padding-top:14px; scroll-margin-top:20px}
main h2::before{content:""; display:block; width:46px; height:3px; border-radius:3px;
  background:linear-gradient(90deg,var(--cyan),var(--violet)); margin-bottom:18px}
main h3{font-family:'Space Grotesk',sans-serif; color:var(--ink-strong); font-weight:600;
  font-size:19.5px; margin:42px 0 4px; letter-spacing:-.1px; scroll-margin-top:20px}
main h3::before{content:"#"; color:var(--cyan-dim); margin-right:9px; font-weight:600}
main p{margin:16px 0}
main strong{color:var(--ink-strong); font-weight:600}
main em{color:var(--ink)}
main ul,main ol{margin:16px 0; padding-left:22px}
main li{margin:8px 0}
main li::marker{color:var(--cyan-dim)}

/* inline code */
:not(pre)>code{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:.86em; background:var(--panel2); color:#a6e7ef; border:1px solid var(--line);
  padding:1.5px 6px; border-radius:6px; white-space:nowrap}

/* code blocks */
.code-file{font-family:'JetBrains Mono',ui-monospace,monospace; font-size:12.5px; color:var(--muted);
  margin:26px 0 0; padding:7px 14px; background:var(--panel); border:1px solid var(--line);
  border-bottom:none; border-radius:10px 10px 0 0; display:inline-block}
.code-file+pre{margin-top:0; border-top-left-radius:0}
.code-file code{background:none; border:none; color:var(--amber); padding:0; white-space:nowrap}
pre{margin:24px 0; background:#0c1119 !important; border:1px solid var(--line); border-radius:12px;
  padding:18px 20px; overflow-x:auto; box-shadow:0 8px 30px rgba(0,0,0,.28)}
pre code{font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:13px; line-height:1.7; background:none !important; padding:0}
pre::-webkit-scrollbar{height:9px}
pre::-webkit-scrollbar-thumb{background:var(--line2); border-radius:9px}

/* figures */
figure.fig{margin:34px 0; text-align:center}
figure.fig img{max-width:100%; height:auto; border:1px solid var(--line2); border-radius:14px;
  box-shadow:0 18px 50px rgba(0,0,0,.4)}
figure.fig figcaption{color:var(--muted); font-size:13.5px; margin-top:14px; line-height:1.6; max-width:720px; margin-left:auto; margin-right:auto}
.hero .cover img{border-radius:16px; box-shadow:0 30px 80px rgba(0,0,0,.5),0 0 0 1px var(--line2)}

/* mermaid */
.mermaid{margin:28px 0; padding:22px; background:var(--panel); border:1px solid var(--line);
  border-radius:14px; text-align:center; overflow-x:auto}
.mermaid svg{max-width:100%; height:auto}

/* tables */
.table-wrap{margin:26px 0; overflow-x:auto; border:1px solid var(--line); border-radius:12px}
table{border-collapse:collapse; width:100%; font-size:14px; min-width:560px}
th,td{padding:11px 15px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; line-height:1.6}
thead th{background:var(--panel2); color:var(--ink-strong); font-weight:600; font-family:'Space Grotesk',sans-serif;
  border-bottom:1px solid var(--line2); white-space:nowrap}
tbody tr:hover{background:rgba(51,209,227,.035)}
tbody tr:last-child td{border-bottom:none}
td code{white-space:normal}

blockquote{border-left:3px solid var(--cyan-dim); margin:22px 0; padding:6px 18px; color:var(--muted); background:rgba(51,209,227,.04); border-radius:0 8px 8px 0}

/* reveal */
.reveal{opacity:0; transform:translateY(22px)}
.reveal.is-in{opacity:1; transform:none}

footer{border-top:1px solid var(--line); margin-top:80px; padding:34px 0 10px; color:var(--muted); font-size:13px}
footer b{color:var(--ink)}

/* mobile */
.menu-btn{display:none}
@media(max-width:1000px){
  .shell{grid-template-columns:1fr}
  aside{position:fixed; z-index:50; left:0; top:0; width:300px; transform:translateX(-105%);
    transition:transform .28s ease; background:var(--bg2); box-shadow:0 0 60px rgba(0,0,0,.6)}
  aside.open{transform:none}
  .menu-btn{display:flex; position:fixed; top:14px; left:14px; z-index:55; width:44px; height:44px;
    align-items:center; justify-content:center; background:var(--panel); border:1px solid var(--line2);
    border-radius:11px; color:var(--cyan); cursor:pointer; font-size:18px}
  .wrap{padding:0 20px}
  .hero{padding-top:64px}
}
</style>
</head>
<body>
<div id="progress"></div>
<button class="menu-btn" id="menuBtn" aria-label="menu">☰</button>
<div class="shell">
  <aside id="sidebar">
    <div class="brand"><b>STEER</b> · 技术拆解</div>
    <div class="brand-sub">Codex × Hermes · mid-turn steering</div>
    <nav id="toc">
      <a class="nav-top" href="#top">开篇</a>
      {{NAV}}
    </nav>
  </aside>
  <main>
    <div class="wrap">
      <header class="hero" id="top">
        <div class="kicker">Agent Runtime · 前沿技术分析</div>
        <h1>{{HERO_TITLE}}</h1>
        <p class="lead">{{SUMMARY}}</p>
        <div class="meta">
          <span>📅 <b>{{DATE}}</b></span>
          <span>{{REGISTER}}</span>
          <span>一手源码 · Codex (Rust) / Hermes (Python)</span>
        </div>
        <div class="cover">{{COVER}}</div>
      </header>
      <article id="content">
        {{BODY}}
      </article>
      <footer>
        <p><b>关于本报告</b> · 基于 Codex (<code>codex-rs</code>) 与 Hermes 一手源码、官方 changelog / PR、OpenClaw / Copilot SDK / Claude Code 官方文档,经多源对抗式核查写成。所有 <code>file:line</code> 引用对应核查时点的仓库状态;版本、PR、日期均标注 UTC 与来源。</p>
        <p style="margin-top:8px">事实分级:fact / inference / speculation 已在正文区分;社区逆向命名(如 nO / h2A)与未核实项(桌面 Steer 控件)已显式标注。</p>
      </footer>
    </div>
  </main>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/rust.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
<script>
// highlight.js (guarded)
try{ if(window.hljs){ document.querySelectorAll('pre code').forEach(b=>{ if(!b.classList.contains('language-mermaid')) hljs.highlightElement(b); }); } }catch(e){}

// mermaid (guarded)
try{
  if(window.mermaid){
    mermaid.initialize({startOnLoad:true, theme:'base', securityLevel:'loose',
      themeVariables:{
        background:'#11161f', primaryColor:'#141a25', primaryTextColor:'#cdd6e6',
        primaryBorderColor:'#33d1e3', lineColor:'#7c8aa3', secondaryColor:'#19202e',
        tertiaryColor:'#0c1119', fontSize:'14px',
        actorBkg:'#141a25', actorBorder:'#33d1e3', actorTextColor:'#eef2f8',
        signalColor:'#7c8aa3', signalTextColor:'#cdd6e6', labelBoxBkgColor:'#141a25',
        noteBkgColor:'#1b2433', noteTextColor:'#cdd6e6', noteBorderColor:'#9a8cff'
      }});
  }
}catch(e){}

// FAILSAFE: if GSAP/ScrollTrigger missing, force-show all reveals
(function(){
  var ok = (typeof gsap!=='undefined') && (typeof ScrollTrigger!=='undefined');
  if(!ok){ document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('is-in')}); return; }
  gsap.registerPlugin(ScrollTrigger);
  document.querySelectorAll('.reveal').forEach(function(el){
    gsap.to(el,{scrollTrigger:{trigger:el, start:'top 88%'}, opacity:1, y:0, duration:.6, ease:'power2.out',
      onStart:function(){el.classList.add('is-in')}});
  });
})();

// reading progress + active nav
(function(){
  var prog=document.getElementById('progress');
  var links=[].slice.call(document.querySelectorAll('#toc a'));
  var map=links.map(function(a){var id=a.getAttribute('href').slice(1);return {a:a, el:document.getElementById(id)};}).filter(function(x){return x.el;});
  function onScroll(){
    var h=document.documentElement; var st=h.scrollTop||document.body.scrollTop;
    var max=h.scrollHeight-h.clientHeight; prog.style.width=(max>0?(st/max*100):0)+'%';
    var cur=null;
    for(var i=0;i<map.length;i++){ if(map[i].el.getBoundingClientRect().top<=120) cur=map[i]; }
    links.forEach(function(a){a.classList.remove('active')});
    if(cur) cur.a.classList.add('active');
  }
  document.addEventListener('scroll',onScroll,{passive:true}); onScroll();
})();

// mobile menu
(function(){
  var b=document.getElementById('menuBtn'), s=document.getElementById('sidebar');
  if(b){ b.addEventListener('click',function(){s.classList.toggle('open')});
    s.addEventListener('click',function(e){ if(e.target.tagName==='A') s.classList.remove('open'); }); }
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
