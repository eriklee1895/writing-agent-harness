// Build a self-contained, single-file report.html from article.md.
//  - article.md  -> HTML (marked + highlight.js, build-time)
//  - ```mermaid blocks -> inline themed SVG (assets/diagrams/*.svg)
//  - 3 concept illustrations inlined as base64 at section anchors; hero in the header
//  - TOC + scroll-spy nav, reading-progress bar, GSAP reveal animations (inlined)
// Re-runnable: picks the newest matching PNG per slug, so regenerated art is auto-used.
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import hljs from 'highlight.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..', '..');                 // 2026-06-11-hermes-steer-deep-dive/
const ARTICLE = join(ROOT, 'article.md');
const ASSETS = join(ROOT, 'assets');
const DIAGRAMS = join(ASSETS, 'diagrams');
const OUT = join(ROOT, 'report.html');

// ---------- helpers ----------
function cleanSvg(s) {
  return s.replace(/<\?xml[^>]*\?>\s*/i, '').replace(/<!DOCTYPE[^>]*>\s*/i, '');
}
function slugify(s) {
  return (s || '').trim().toLowerCase()
    .replace(/[^\w一-鿿]+/g, '-')
    .replace(/^-+|-+$/g, '') || 's';
}
function escapeReg(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
function escapeHtml(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

function findImage(slug) {
  if (!existsSync(ASSETS)) return null;
  const files = readdirSync(ASSETS).filter(f => f.toLowerCase().endsWith('.png') && f.includes(slug));
  if (!files.length) return null;
  files.sort((a, b) => statSync(join(ASSETS, b)).mtimeMs - statSync(join(ASSETS, a)).mtimeMs);
  return join(ASSETS, files[0]);
}
function imgDataUri(slug) {
  const p = findImage(slug);
  if (!p) { console.error('MISSING IMAGE for slug:', slug); return null; }
  return 'data:image/png;base64,' + readFileSync(p).toString('base64');
}
function insetFigure(slug, alt, cap) {
  const uri = imgDataUri(slug);
  if (!uri) return '<!-- missing image: ' + slug + ' -->';
  return '<figure class="illustration reveal"><img alt="' + escapeHtml(alt) + '" src="' + uri + '"><figcaption>' + cap + '</figcaption></figure>';
}

// ---------- markdown -> html ----------
const md = readFileSync(ARTICLE, 'utf8').replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');
const svgs = ['01-semantics', '02-dataflow', '03-decision', '04-loop']
  .map(n => cleanSvg(readFileSync(join(DIAGRAMS, n + '.svg'), 'utf8')));

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    if (lang === 'mermaid') return code;                 // replaced below
    if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value;
    return hljs.highlightAuto(code).value;
  },
}));
marked.setOptions({ gfm: true });

let html = marked.parse(md);

// mermaid code blocks -> inline SVG figures (in document order)
let mi = 0;
html = html.replace(/<pre><code class="[^"]*language-mermaid[^"]*">[\s\S]*?<\/code><\/pre>/g, () => {
  const svg = svgs[mi++] || '';
  return '<figure class="diagram reveal">' + svg + '</figure>';
});
if (mi !== svgs.length) console.error('WARN replaced ' + mi + ' mermaid blocks, have ' + svgs.length + ' svgs');

// heading ids + TOC (h2 only) + reveal class on h2
const toc = [];
html = html.replace(/<h([23])>([\s\S]*?)<\/h\1>/g, (m, lvl, inner) => {
  const text = inner.replace(/<[^>]+>/g, '').trim();
  const id = slugify(text);
  if (lvl === '2') { toc.push({ id, text }); return '<h2 id="' + id + '" class="anchor reveal">' + inner + '</h2>'; }
  return '<h3 id="' + id + '" class="anchor">' + inner + '</h3>';
});

// extract title (first h1) + dek (first paragraph after it), strip both from body
let title = 'Hermes steer 深度报告';
const h1m = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
if (h1m) title = h1m[1].replace(/<[^>]+>/g, '').trim();
html = html.replace(/<h1[^>]*>[\s\S]*?<\/h1>\s*/, '');
let dek = '';
const pm = html.match(/^\s*<p>([\s\S]*?)<\/p>\s*/);
if (pm) { dek = pm[1]; html = html.replace(/^\s*<p>[\s\S]*?<\/p>\s*/, ''); }

// reveal class on heavy blocks; wrap tables for horizontal scroll on mobile
html = html.replace(/<pre><code/g, '<pre class="reveal"><code');
html = html.replace(/<blockquote>/g, '<blockquote class="reveal">');
html = html.replace(/<table>/g, '<div class="tablewrap reveal"><table>').replace(/<\/table>/g, '</table></div>');

// external links open in a new tab
html = html.replace(/<a href=/g, '<a target="_blank" rel="noopener" href=');

// insert concept illustrations after the relevant section headings
function insertAfterH2(containing, figureHtml) {
  const re = new RegExp('(<h2 id="[^"]*"[^>]*>[^<]*' + escapeReg(containing) + '[^<]*</h2>)');
  if (!re.test(html)) { console.error('anchor h2 not found for:', containing); return; }
  html = html.replace(re, '$1\n' + figureHtml);
}
insertAfterH2('turn-based trap', insetFigure('hermes-steer-batch-vs-interrupt',
  '人类的中断驱动 vs agent 的批处理驱动,以及三种处理语义',
  '图 1 · 人类认知是中断驱动、agent 执行是批处理驱动;一条中途到达的输入,可以被 interrupt 推倒重来、queue 排到下一轮,或被 steer 在回合内引导。'));
insertAfterH2('核心机制', insetFigure('hermes-steer-masquerading',
  'steer 文本被包进 marker 追加到 tool result 尾部,系统提示作为信任锚',
  '图 2 · steer 被追加到最后一个 tool result 的尾部,套上自描述 marker;系统提示作为信任锚,要求模型只信这一个 marker——而这正是注入防御最该怀疑的通道。'));
insertAfterH2('安全插入点', insetFigure('hermes-steer-two-drains',
  '一轮 loop 内的两个 drain 点守在工具执行两侧',
  '图 3 · pre-API 与 post-tool 两个 drain 点守在工具执行两侧;steer 只在安全边界注入,工具执行本身从不被打断。'));

// ---------- assemble ----------
const navItems = toc.map((t, i) =>
  '<a href="#' + t.id + '" data-id="' + t.id + '"><span class="n">' + String(i + 1).padStart(2, '0') + '</span><span class="t">' + escapeHtml(t.text) + '</span></a>'
).join('\n');

const heroUri = imgDataUri('hermes-steer-hero');
const heroFigure = heroUri
  ? '<figure class="hero-illustration"><img alt="MID-TURN STEER — 把一句话塞进正在跑的 agent" src="' + heroUri + '"></figure>'
  : '';

const plain = md.replace(/```[\s\S]*?```/g, '').replace(/\s+/g, '');
const minutes = Math.max(1, Math.round(plain.length / 450));
const metaLine = '2026 · 06 · 11　·　' + toc.length + ' 节 · 4 流程图 · 4 概念图　·　约 ' + minutes + ' 分钟';

const gsapJs = readFileSync(join(HERE, 'node_modules', 'gsap', 'dist', 'gsap.min.js'), 'utf8');
const stJs = readFileSync(join(HERE, 'node_modules', 'gsap', 'dist', 'ScrollTrigger.min.js'), 'utf8');

const interDir = join(HERE, 'node_modules', '@fontsource', 'inter', 'files');
const jbmDir = join(HERE, 'node_modules', '@fontsource', 'jetbrains-mono', 'files');
function fontFace(family, weight, dir, file) {
  const b64 = readFileSync(join(dir, file)).toString('base64');
  return "@font-face{font-family:'" + family + "';font-style:normal;font-weight:" + weight +
    ";font-display:swap;src:url(data:font/woff2;base64," + b64 + ") format('woff2')}";
}
const FONTS = [
  fontFace('Inter', 400, interDir, 'inter-latin-400-normal.woff2'),
  fontFace('Inter', 500, interDir, 'inter-latin-500-normal.woff2'),
  fontFace('Inter', 700, interDir, 'inter-latin-700-normal.woff2'),
  fontFace('Inter', 800, interDir, 'inter-latin-800-normal.woff2'),
  fontFace('JetBrains Mono', 400, jbmDir, 'jetbrains-mono-latin-400-normal.woff2'),
].join('\n') + '\n';

const CSS = FONTS + `
*,*::before,*::after{box-sizing:border-box}
:root{
  --paper:#faf6ee; --paper-2:#f3ecdd; --panel:#fffdf8;
  --ink:#221f18; --ink-soft:#4b463c; --muted:#8d8676; --faint:#b8b0a0;
  --rule:#e6ddcc; --rule-2:#d8ceb9;
  --accent:#c0801a; --accent-ink:#9a6510; --accent-soft:#f1dca8;
  --slate:#46606f; --danger:#b4503c;
  --code-bg:#211e1a; --code-ink:#e9e1d2;
  --maxw:760px; --nav:288px;
  --sans:'Inter',-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:'JetBrains Mono',"SF Mono",ui-monospace,Menlo,Consolas,monospace;
}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:17px;line-height:1.82;font-feature-settings:"cv11" 1;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:linear-gradient(90deg,var(--accent),var(--accent-ink));transition:width .08s linear}

.topbar{position:fixed;top:0;left:0;right:0;height:52px;z-index:50;display:none;
  align-items:center;gap:12px;padding:0 16px;background:rgba(250,246,238,.86);
  backdrop-filter:saturate(140%) blur(10px);border-bottom:1px solid var(--rule)}
.topbar .tt{font-weight:600;font-size:14px;color:var(--ink-soft);overflow:hidden;
  white-space:nowrap;text-overflow:ellipsis}
#tocToggle{appearance:none;border:1px solid var(--rule-2);background:var(--panel);color:var(--ink);
  border-radius:8px;height:34px;padding:0 12px;font-size:13px;font-family:var(--sans);cursor:pointer;flex:0 0 auto}

.layout{display:grid;grid-template-columns:var(--nav) minmax(0,1fr);gap:0;max-width:1240px;margin:0 auto}
.sidebar{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
  padding:40px 22px 40px 28px;border-right:1px solid var(--rule)}
.sidebar .brand{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-ink);font-weight:700;margin-bottom:6px}
.sidebar .brand-sub{font-size:12.5px;color:var(--muted);margin-bottom:26px;line-height:1.5}
.toc{display:flex;flex-direction:column;gap:1px}
.toc a{display:flex;gap:10px;align-items:baseline;padding:7px 10px;border-radius:8px;
  color:var(--ink-soft);text-decoration:none;font-size:13.5px;line-height:1.45;transition:background .15s,color .15s}
.toc a .n{color:var(--faint);font-family:var(--mono);font-size:11px;flex:0 0 auto;font-variant-numeric:tabular-nums}
.toc a:hover{background:var(--paper-2);color:var(--ink)}
.toc a.active{background:var(--accent-soft);color:var(--accent-ink)}
.toc a.active .n{color:var(--accent-ink)}

main{min-width:0;padding:0 0 96px}
.hero{max-width:var(--maxw);margin:0 auto;padding:84px 24px 26px}
.hero .kicker{font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-ink);font-weight:700;margin-bottom:18px}
.hero h1{font-family:var(--sans);font-weight:800;font-size:clamp(31px,5.2vw,48px);line-height:1.2;
  letter-spacing:-.022em;margin:0 0 22px;text-wrap:balance}
.hero .dek{font-size:18.5px;line-height:1.8;color:var(--ink-soft);margin:0 0 26px}
.hero .meta{font-size:12.5px;color:var(--muted);font-family:var(--mono);letter-spacing:.02em;
  padding-top:18px;border-top:1px solid var(--rule)}
.hero-illustration{margin:34px 0 0}
.hero-illustration img{width:100%;height:auto;border:1px solid var(--rule);border-radius:14px;
  box-shadow:0 20px 50px -28px rgba(40,30,10,.4)}

.prose{max-width:var(--maxw);margin:0 auto;padding:0 24px}
.prose h2{font-family:var(--sans);font-weight:700;font-size:26px;line-height:1.32;letter-spacing:-.014em;
  margin:64px 0 18px;padding-top:30px;border-top:1px solid var(--rule);scroll-margin-top:70px;text-wrap:balance}
.prose h2::before{content:"";display:block;width:34px;height:3px;border-radius:2px;background:var(--accent);margin-bottom:18px}
.prose h3{font-weight:700;font-size:18.5px;margin:38px 0 12px;color:var(--ink);scroll-margin-top:70px}
.prose p{margin:0 0 19px}
.prose strong{font-weight:700;color:var(--ink)}
.prose a{color:var(--accent-ink);text-decoration:none;border-bottom:1px solid var(--accent-soft)}
.prose a:hover{border-bottom-color:var(--accent)}
.prose ul,.prose ol{margin:0 0 19px;padding-left:1.3em}
.prose li{margin:6px 0}
.prose li::marker{color:var(--accent)}
.prose :not(pre)>code{font-family:var(--mono);font-size:.86em;background:var(--paper-2);
  border:1px solid var(--rule);border-radius:5px;padding:.08em .4em;color:var(--accent-ink);word-break:break-word}
.prose hr{border:0;border-top:1px solid var(--rule);margin:40px 0}

pre.code,pre{background:var(--code-bg);color:var(--code-ink);border-radius:12px;
  padding:18px 20px;overflow-x:auto;margin:22px 0;font-size:13.5px;line-height:1.66;
  border:1px solid #000;box-shadow:0 14px 34px -22px rgba(0,0,0,.6)}
pre code{font-family:var(--mono);background:none;border:0;padding:0;color:inherit;font-size:inherit}
pre::-webkit-scrollbar{height:9px}
pre::-webkit-scrollbar-thumb{background:#4a443b;border-radius:6px}

figure.diagram{margin:30px 0;padding:22px 18px;background:var(--panel);border:1px solid var(--rule);
  border-radius:14px;text-align:center;overflow-x:auto;box-shadow:0 12px 32px -26px rgba(40,30,10,.4)}
figure.diagram svg{max-width:100%!important;height:auto!important}
figure.illustration{margin:30px 0;text-align:center}
figure.illustration img{width:100%;height:auto;border:1px solid var(--rule);border-radius:14px;
  box-shadow:0 16px 40px -28px rgba(40,30,10,.42)}
figure.illustration figcaption,figure.diagram figcaption{font-size:13px;color:var(--muted);
  line-height:1.6;margin-top:12px;text-align:left;padding:0 4px}

.tablewrap{overflow-x:auto;margin:24px 0;border:1px solid var(--rule);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:14.5px}
thead th{background:var(--paper-2);text-align:left;font-weight:700;color:var(--ink)}
th,td{padding:11px 14px;border-bottom:1px solid var(--rule);vertical-align:top;line-height:1.6}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:rgba(243,236,221,.45)}

blockquote{margin:22px 0;padding:14px 20px;background:var(--panel);border-left:3px solid var(--accent);
  border-radius:0 10px 10px 0;color:var(--ink-soft);font-size:15.5px}
blockquote p{margin:0 0 8px}
blockquote p:last-child{margin:0}

.foot{max-width:var(--maxw);margin:60px auto 0;padding:26px 24px 0;border-top:1px solid var(--rule);
  font-size:13px;color:var(--muted);line-height:1.7}

.reveal{will-change:transform,opacity}

@media (max-width:1024px){
  :root{--nav:0px}
  .topbar{display:flex}
  .layout{grid-template-columns:1fr}
  .sidebar{position:fixed;top:0;left:0;width:300px;max-width:84vw;z-index:55;background:var(--panel);
    border-right:1px solid var(--rule);transform:translateX(-104%);transition:transform .28s ease;
    box-shadow:0 0 50px -10px rgba(0,0,0,.25)}
  .sidebar.open{transform:none}
  main{padding-top:52px}
  .hero{padding-top:48px}
}
@media (max-width:560px){
  body{font-size:16px}
  .hero{padding-left:18px;padding-right:18px}
  .prose{padding-left:18px;padding-right:18px}
}
.scrim{position:fixed;inset:0;background:rgba(20,16,8,.32);z-index:54;opacity:0;pointer-events:none;transition:opacity .28s}
.scrim.show{opacity:1;pointer-events:auto}
@media (min-width:1025px){.scrim{display:none}}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .reveal{opacity:1!important;transform:none!important}
}

/* highlight.js — warm dark theme */
.hljs{color:#e9e1d2;background:transparent}
.hljs-comment,.hljs-quote{color:#9a917d;font-style:italic}
.hljs-keyword,.hljs-selector-tag,.hljs-literal,.hljs-section,.hljs-link{color:#e0a04a}
.hljs-built_in,.hljs-name{color:#7fb0c4}
.hljs-string,.hljs-attr,.hljs-template-tag,.hljs-addition,.hljs-bullet,.hljs-symbol{color:#a7c388}
.hljs-number,.hljs-meta{color:#d8916a}
.hljs-title,.hljs-class .hljs-title,.hljs-type{color:#ecc66a}
.hljs-params{color:#e9e1d2}
.hljs-variable,.hljs-template-variable{color:#d8916a}
.hljs-deletion{color:#d8916a}
.hljs-emphasis{font-style:italic}.hljs-strong{font-weight:700}
`;

const INIT = `
(function(){
  var rm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var bar = document.getElementById('progress');
  function onScroll(){
    var h=document.documentElement, sc=h.scrollTop||document.body.scrollTop, max=(h.scrollHeight-h.clientHeight)||1;
    bar.style.width=(sc/max*100)+'%';
  }
  addEventListener('scroll', onScroll, {passive:true}); onScroll();

  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var map={}; links.forEach(function(a){map[a.getAttribute('data-id')]=a;});
  var secs=links.map(function(a){return document.getElementById(a.getAttribute('data-id'));}).filter(Boolean);
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){
        links.forEach(function(l){l.classList.remove('active');});
        var a=map[e.target.id]; if(a){a.classList.add('active');
          a.scrollIntoView({block:'nearest'});}
      }});
    }, {rootMargin:'-12% 0px -78% 0px'});
    secs.forEach(function(s){io.observe(s);});
  }

  var sidebar=document.getElementById('sidebar'), toggle=document.getElementById('tocToggle'), scrim=document.getElementById('scrim');
  function close(){sidebar.classList.remove('open');scrim.classList.remove('show');}
  if(toggle){toggle.addEventListener('click',function(){sidebar.classList.toggle('open');scrim.classList.toggle('show');});}
  if(scrim){scrim.addEventListener('click',close);}
  links.forEach(function(a){a.addEventListener('click',close);});

  if(!rm && window.gsap && window.ScrollTrigger){
    gsap.registerPlugin(ScrollTrigger);
    var tl=gsap.timeline({defaults:{ease:'power3.out'}});
    tl.from('.hero .kicker',{y:18,opacity:0,duration:.6})
      .from('.hero h1',{y:30,opacity:0,duration:.85},'-=.35')
      .from('.hero .dek',{y:22,opacity:0,duration:.7},'-=.55')
      .from('.hero .meta',{opacity:0,duration:.6},'-=.45')
      .from('.hero-illustration',{y:34,opacity:0,duration:.9},'-=.45');
    gsap.utils.toArray('.reveal').forEach(function(el){
      gsap.from(el,{y:30,opacity:0,duration:.7,ease:'power2.out',
        scrollTrigger:{trigger:el,start:'top 90%',once:true}});
    });
    ScrollTrigger.refresh();
  }
})();
`;

const out =
  '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width, initial-scale=1">' +
  '<meta name="color-scheme" content="light">' +
  '<title>' + escapeHtml(title) + '</title>' +
  '<style>' + CSS + '</style></head><body>' +
  '<div class="progress" id="progress"></div>' +
  '<div class="topbar"><button id="tocToggle" aria-label="目录">☰ 目录</button><span class="tt">' + escapeHtml(title) + '</span></div>' +
  '<div class="scrim" id="scrim"></div>' +
  '<div class="layout">' +
    '<aside class="sidebar" id="sidebar">' +
      '<div class="brand">Hermes · steer</div>' +
      '<div class="brand-sub">中途干预机制 · 代码级深拆</div>' +
      '<nav class="toc">' + navItems + '</nav>' +
    '</aside>' +
    '<main>' +
      '<section class="hero">' +
        '<div class="kicker">Agent 前沿技术分析</div>' +
        '<h1>' + escapeHtml(title) + '</h1>' +
        '<p class="dek">' + dek + '</p>' +
        '<div class="meta">' + metaLine + '</div>' +
        heroFigure +
      '</section>' +
      '<article class="prose">' + html + '</article>' +
      '<footer class="foot">本报告由 <code>article.md</code> 派生构建为单文件 HTML。机制部分逐字核证自 hermes-agent 仓库源码;对其他 agent 的对比与通用技术事实截至 2026-06,已在正文标注来源与置信度。</footer>' +
    '</main>' +
  '</div>' +
  '<script>' + gsapJs + '</script>' +
  '<script>' + stJs + '</script>' +
  '<script>' + INIT + '</script>' +
  '</body></html>';

writeFileSync(OUT, out, 'utf8');
console.log('built ' + OUT);
console.log('  sections: ' + toc.length + ' | mermaid inlined: ' + mi + ' | size: ' + (Buffer.byteLength(out) / 1024 / 1024).toFixed(2) + ' MB');
