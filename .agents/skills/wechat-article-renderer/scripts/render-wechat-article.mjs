#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

// ── Style tokens ────────────────────────────────────────────────
const STYLE_TOKENS = {
  "impact-rational": {
    accent: "#d84b37",
    blue: "#3d6a8a",
    text: "#303b46",
    muted: "#596673",
    panelBorder: "rgba(67,105,128,.14)",
    shadow: "0 8px 24px rgba(43,70,88,.08)",
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif",
    headingFontFamily: undefined,
    bodyBg: "#f4f7f8",
    cardBg: "#ffffff",
    quoteBg: "#edf4f8",
    quoteBorder: "#4a7c9b",
    useCards: true,
    showOutline: true,
    showSummary: true,
    heroStyle: "border-left",
    headingPrefix: "◆",
    closingPanel: true,
    lineHeight: "1.9",
  },
  "literary-essay": {
    accent: "#8b5e3c",
    blue: "#5a7d6a",
    text: "#3a3a3a",
    muted: "#7a7a7a",
    panelBorder: "transparent",
    shadow: "none",
    fontFamily: "'Noto Serif SC','STSong','SimSun','PingFang SC','Hiragino Sans GB',serif",
    headingFontFamily: "'Noto Serif SC','STSong','Georgia',serif",
    bodyBg: "#fafaf7",
    cardBg: "transparent",
    quoteBg: "#f7f4f0",
    quoteBorder: "#8b5e3c",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "centered",
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "2.0",
  },
  "cultural-essay": {
    accent: "#9a5b2f",
    blue: "#345f5a",
    text: "#332f2a",
    muted: "#74685c",
    panelBorder: "rgba(154,91,47,.14)",
    shadow: "none",
    fontFamily: "'Noto Serif SC','STSong','SimSun','PingFang SC','Hiragino Sans GB',serif",
    headingFontFamily: "'Noto Serif SC','STSong','Georgia',serif",
    bodyBg: "#ffffff",
    cardBg: "transparent",
    quoteBg: "#f5efe5",
    quoteBorder: "#9a5b2f",
    highlightBg: "#f8f1e8",
    highlightColor: "#2f2a24",
    highlightBorder: "rgba(154,91,47,.22)",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "cultural",
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "2.0",
  },
  "tech-blog": {
    accent: "#0066cc",
    blue: "#2c5f8a",
    text: "#24292e",
    muted: "#586069",
    panelBorder: "rgba(0,102,204,.12)",
    shadow: "0 4px 16px rgba(0,0,0,.06)",
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif",
    headingFontFamily: undefined,
    bodyBg: "#f6f8fa",
    cardBg: "#ffffff",
    quoteBg: "#f0f7ff",
    quoteBorder: "#0066cc",
    useCards: true,
    showOutline: true,
    showSummary: true,
    heroStyle: "border-left",
    headingPrefix: "#",
    closingPanel: true,
    lineHeight: "1.9",
  },
  "warm-editorial": {
    // 复刻 index.html 的温暖纸质感风格：暖灰底、H2 焦糖色、深色表头、圆角表格
    accent: "#d97757",
    blue: "#d97757",
    text: "#141413",
    muted: "#b0aea5",
    panelBorder: "#e8e6dc",
    shadow: "0 1px 3px rgba(0,0,0,.06)",
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Serif SC',Arial,sans-serif",
    headingFontFamily: undefined,
    bodyBg: "#faf9f5",
    cardBg: "#ffffff",
    quoteBg: "#f3f1ea",
    quoteBorder: "#d97757",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "warm",
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "1.9",
    codeBg: "#f3f1ea",
    codeBorder: "rgba(0,0,0,.08)",
    tableHeaderBg: "#141413",
    tableHeaderColor: "#faf9f5",
    darkBg: "#1a1a18",
    darkCardBg: "#2a2a28",
    darkText: "#e8e6dc",
    darkMuted: "#8b8a84",
    darkAccent: "#e8966f",
    darkQuoteBg: "#2a2a25",
    darkCodeBg: "#2a2a28",
    darkHeadingColor: "#e8966f",
  },
  "agent-flow": {
    accent: "#ff6b35",
    blue: "#2d8cff",
    text: "#1a1a2e",
    muted: "#6b7280",
    panelBorder: "transparent",
    shadow: "none",
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif",
    headingFontFamily: undefined,
    bodyBg: "#ffffff",
    cardBg: "transparent",
    quoteBg: "#f8f9ff",
    quoteBorder: "#2d8cff",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "centered",
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "1.9",
    codeBg: "#f3f4f6",
    codeBorder: "rgba(0,0,0,.08)",
    darkBg: "#111827",
    darkCardBg: "#1f2937",
    darkText: "#e5e7eb",
    darkMuted: "#9ca3af",
    darkAccent: "#fb923c",
    darkQuoteBg: "#1e293b",
    darkCodeBg: "#374151",
    darkHeadingColor: "#fbbf24",
  },
  "editorial-magazine": {
    // 杂志编辑风：纯白底、深靛蓝+朱红双色、大标题大留白、杂志章节感
    accent: "#c0392b",          // 朱红，用于强调、链接、编号
    blue: "#1e3a5f",            // 深靛蓝，主标题色
    text: "#1c1c1e",            // 近黑正文，阅读舒适
    muted: "#8a8f98",           // 中灰辅助文字
    panelBorder: "#e8e8ed",
    shadow: "none",
    fontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei','Noto Serif SC',Arial,sans-serif",
    headingFontFamily: "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif",
    bodyBg: "#ffffff",
    cardBg: "#ffffff",
    quoteBg: "#fafbfc",
    quoteBorder: "#1e3a5f",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "magazine",      // 新 hero 风格：大标题 + 副标题 + 分割线 + 元信息
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "1.95",
    codeBg: "#f6f8fa",
    codeBorder: "rgba(0,0,0,.06)",
    tableHeaderBg: "#1e3a5f",
    tableHeaderColor: "#ffffff",
    darkBg: "#0f172a",
    darkCardBg: "#1e293b",
    darkText: "#e2e8f0",
    darkMuted: "#94a3b8",
    darkAccent: "#f87171",
    darkQuoteBg: "#1e293b",
    darkCodeBg: "#1e293b",
    darkHeadingColor: "#93c5fd",
  },
  "neo-futurism": {
    // 新国风编辑风：深墨黑底 + 陶土朱红accent，匹配封面唐朝国风水墨质感，高级杂志感
    accent: "#c45a3a",           // 陶土朱红（暖调，匹配封面国风配色）
    blue: "#1a1a1a",
    text: "#1a1a1a",
    muted: "#7a736c",
    panelBorder: "#1a1a1a",
    shadow: "0 1px 3px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.04)",
    fontFamily: "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif",
    headingFontFamily: "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif",
    bodyBg: "#ffffff",
    cardBg: "#ffffff",
    quoteBg: "transparent",
    quoteBorder: "#c45a3a",
    useCards: false,
    showOutline: false,
    showSummary: false,
    heroStyle: "neo-title",      // 简洁标题区：仅标题+副标题，无冗余信息
    headingPrefix: "",
    closingPanel: false,
    lineHeight: "1.85",
    codeBg: "#1a1a1a",
    codeBorder: "#c45a3a",
    tableHeaderBg: "#1a1a1a",
    tableHeaderColor: "#ffffff",
    darkBg: "#000000",
    darkCardBg: "#111111",
    darkText: "#f5f5f5",
    darkMuted: "#7a736c",
    darkAccent: "#e07a5a",
    darkQuoteBg: "#1a1a1a",
    darkCodeBg: "#000000",
    darkHeadingColor: "#ffffff",
    sectionNumber: true,
  },
};

const STYLE_LABELS = {
  "impact-rational": {
    heroLabel: "趋势观察",
    authorNoteLabel: "作者想说",
    outlineLabel: "阅读地图",
    questionLabel: "三个关键问题",
    thesisLabel: "核心判断",
    galleryLabel: "公告截图速览",
    closingCTA: "下一篇正在路上...",
  },
  "literary-essay": {
    heroLabel: "散文随笔",
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "文中配图",
    closingCTA: undefined,
  },
  "cultural-essay": {
    heroLabel: "文化随笔",
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "文中配图",
    closingCTA: undefined,
  },
  "tech-blog": {
    heroLabel: "技术观察",
    authorNoteLabel: "作者想说",
    outlineLabel: "内容导航",
    questionLabel: "关键问题",
    thesisLabel: "核心判断",
    galleryLabel: "截图速览",
    closingCTA: "下一篇在路上 →",
  },
  "agent-flow": {
    heroLabel: undefined,
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "配图",
    closingCTA: undefined,
  },
  "warm-editorial": {
    heroLabel: undefined,
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "配图",
    closingCTA: undefined,
  },
  "editorial-magazine": {
    heroLabel: undefined,
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "配图",
    closingCTA: undefined,
  },
  "neo-futurism": {
    heroLabel: undefined,
    authorNoteLabel: undefined,
    outlineLabel: undefined,
    questionLabel: undefined,
    thesisLabel: undefined,
    galleryLabel: "配图",
    closingCTA: undefined,
  },
};

// ── Shared constants ─────────────────────────────────────────────
const SAFE_WRAP = "box-sizing:border-box; max-width:100%; overflow-wrap:break-word; word-break:break-word;";
const DEFAULT_STYLE = "warm-editorial";
const SUPPORTED_STYLES = new Set(Object.keys(STYLE_TOKENS));
let IMAGE_BASE_DIR = process.cwd();
let ACTIVE_STYLE = DEFAULT_STYLE;

function getTokens() {
  return STYLE_TOKENS[ACTIVE_STYLE] || STYLE_TOKENS[DEFAULT_STYLE];
}

function getLabels() {
  return STYLE_LABELS[ACTIVE_STYLE] || STYLE_LABELS[DEFAULT_STYLE];
}

// ── HTML utilities ───────────────────────────────────────────────
function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

// ── Markdown parsing ─────────────────────────────────────────────
function stripFrontmatter(markdown) {
  if (!markdown.startsWith("---\n")) return markdown;
  const end = markdown.indexOf("\n---\n", 4);
  return end === -1 ? markdown : markdown.slice(end + 5);
}

function stripHtmlComments(markdown) {
  return markdown.replace(/<!--[\s\S]*?-->/g, "");
}

function attrValue(markup, name) {
  const match = markup.match(new RegExp(`${name}=["']([^"']+)["']`, "i"));
  return match ? match[1] : "";
}

function videoPlaceholderLine(markup) {
  const sourceMatch = markup.match(/<source\b[^>]*src=["']([^"']+)["'][^>]*>/i);
  const src = sourceMatch ? sourceMatch[1] : attrValue(markup, "src");
  const poster = attrValue(markup, "poster");
  const attrs = [
    src ? `src="${src}"` : "",
    poster ? `poster="${poster}"` : "",
  ].filter(Boolean).join(" ");
  return `\n::video-placeholder ${attrs}::\n`;
}

function replaceRawVideoBlocks(markdown) {
  return markdown.replace(/<video\b[\s\S]*?<\/video>/gi, (match) => videoPlaceholderLine(match));
}

function plainInline(value) {
  return value
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .trim();
}

function inline(markdown) {
  const tokens = getTokens();
  let html = escapeHtml(markdown);

  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风行内样式：code 用深靛蓝底白字 + bold 用朱红加粗 + link 用深靛蓝下划线
    html = html.replace(/`([^`]+)`/g, (_match, code) => (
      `<code class="dark-code" style="font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono',monospace; font-size:.88em; color:${tokens.blue}; background:${tokens.codeBg || "#f6f8fa"}; border:1px solid rgba(30,58,95,.12); border-radius:3px; padding:2px 6px;">${code}</code>`
    ));
    html = html.replace(/\*\*([^*]+)\*\*/g, `<strong style="color:${tokens.text}; font-weight:700;">$1</strong>`);
    html = html.replace(/\*([^*]+)\*/g, `<em style="font-style:italic; color:${tokens.text};">$1</em>`);
    html = html.replace(/==([^=]+)==/g, (_match, text) => (
      `<span style="color:${tokens.text}; background:${tokens.highlightBg || "rgba(192,57,43,.12)"}; padding:2px 4px; border-radius:2px; border-bottom:2px solid ${tokens.accent};">${text}</span>`
    ));
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label) => (
      `<span style="color:${tokens.accent}; border-bottom:1px solid ${tokens.accent}; font-weight:500;">${label}</span>`
    ));
  } else if (ACTIVE_STYLE === "neo-futurism") {
    // 国风编辑风行内样式：code 深墨底陶土朱红字 + bold 黑色加粗 + link 陶土朱红
    html = html.replace(/`([^`]+)`/g, (_match, code) => (
      `<code class="dark-code" style="font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono',monospace; font-size:.88em; color:${tokens.accent}; background:#faf8f5; border:1px solid rgba(196,90,58,.18); border-radius:3px; padding:2px 6px;">${code}</code>`
    ));
    html = html.replace(/\*\*([^*]+)\*\*/g, `<strong style="color:${tokens.text}; font-weight:800;">$1</strong>`);
    html = html.replace(/\*([^*]+)\*/g, `<em style="font-style:italic; color:${tokens.text};">$1</em>`);
    html = html.replace(/==([^=]+)==/g, (_match, text) => (
      `<span style="color:${tokens.text}; background:rgba(196,90,58,.10); padding:2px 4px; border-radius:2px; border-bottom:2px solid ${tokens.accent};">${text}</span>`
    ));
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label) => (
      `<span style="color:${tokens.accent}; border-bottom:1px solid ${tokens.accent}; font-weight:600;">${label}</span>`
    ));
  } else {
    html = html.replace(/`([^`]+)`/g, (_match, code) => (
      `<code class="dark-code" style="font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,'Liberation Mono',monospace; font-size:.92em; color:${tokens.accent}; background:#fff3ee; border:1px solid rgba(216,75,55,.16); border-radius:4px; padding:1px 5px;">${code}</code>`
    ));
    html = html.replace(/\*\*([^*]+)\*\*/g, `<strong style="color:${tokens.accent}; font-weight:700;">$1</strong>`);
    html = html.replace(/\*([^*]+)\*/g, `<em style="font-style:normal; color:${tokens.blue};">$1</em>`);
    html = html.replace(/==([^=]+)==/g, (_match, text) => (
      `<span style="color:${tokens.highlightColor || tokens.text}; background:${tokens.highlightBg || "rgba(216,75,55,.10)"}; padding:1px 4px; border-radius:4px;">${text}</span>`
    ));
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label) => (
      `<span style="color:${tokens.blue}; border-bottom:1px solid rgba(61,106,138,.28);">${label}</span>`
    ));
  }

  return html;
}

function isImageLine(line) {
  return /^!\[[^\]]*]\([^)]+\)\s*$/.test(line.trim());
}

function parseImage(line) {
  const match = line.trim().match(/^!\[([^\]]*)]\(([^)]+)\)\s*$/);
  if (!match) return null;
  return { alt: match[1] || "文章配图", src: match[2] };
}

function imageAttrs(src, alt) {
  const escapedSrc = escapeAttr(src);
  const escapedAlt = escapeAttr(alt);
  if (/^(https?:|data:|\/\/)/i.test(src)) {
    return `src="${escapedSrc}" alt="${escapedAlt}"`;
  }
  const localPath = path.isAbsolute(src) ? src : path.resolve(IMAGE_BASE_DIR, src);
  return `src="${escapedSrc}" data-local-path="${escapeAttr(localPath)}" alt="${escapedAlt}"`;
}

function parseTable(lines, start) {
  const rows = [];
  let i = start;
  while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
    const cells = lines[i]
      .trim()
      .slice(1, -1)
      .split("|")
      .map((cell) => cell.trim());
    rows.push(cells);
    i += 1;
  }
  if (rows.length < 2 || !rows[1].every((cell) => /^:?-+:?$/.test(cell))) {
    return null;
  }
  return { block: { type: "table", header: rows[0], rows: rows.slice(2) }, next: i };
}

function parseBlocks(markdown) {
  const lines = replaceRawVideoBlocks(stripHtmlComments(stripFrontmatter(markdown))).replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    const fenceOpen = trimmed.match(/^(`{3,})/);
    if (fenceOpen) {
      // Closing fence is a run of backticks at least as long as the opener,
      // with no trailing content (info string only allowed on the opener).
      const closeRe = new RegExp(`^\`{${fenceOpen[1].length},}\\s*$`);
      const lang = trimmed.slice(fenceOpen[1].length).trim().split(/\s+/)[0] || "";
      const code = [];
      i += 1;
      while (i < lines.length && !closeRe.test(lines[i].trim())) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push({ type: "code", lang, text: code.join("\n") });
      continue;
    }

    const videoPlaceholder = trimmed.match(/^::video-placeholder(?:\s+src="([^"]+)")?(?:\s+poster="([^"]+)")?\s*::$/);
    if (videoPlaceholder) {
      blocks.push({
        type: "videoPlaceholder",
        src: videoPlaceholder[1] || "",
        poster: videoPlaceholder[2] || "",
      });
      i += 1;
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: "heading", level: heading[1].length, text: heading[2].trim() });
      i += 1;
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i += 1;
      continue;
    }

    const table = parseTable(lines, i);
    if (table) {
      blocks.push(table.block);
      i = table.next;
      continue;
    }

    const highlight = trimmed.match(/^==(.+)==$/);
    if (highlight) {
      blocks.push({ type: "highlight", text: highlight[1].trim() });
      i += 1;
      continue;
    }

    if (trimmed.startsWith(">")) {
      const quoteLines = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].replace(/^\s*>\s?/, ""));
        i += 1;
      }
      blocks.push({ type: "quote", lines: quoteLines });
      continue;
    }

    if (isImageLine(trimmed)) {
      blocks.push({ type: "image", ...parseImage(trimmed) });
      i += 1;
      continue;
    }

    if (/^[-*]\s+/.test(trimmed) || /^\d+[.)]\s+/.test(trimmed)) {
      const ordered = /^\d+[.)]\s+/.test(trimmed);
      const items = [];
      while (i < lines.length) {
        const itemLine = lines[i].trim();
        const itemMatch = ordered
          ? itemLine.match(/^\d+[.)]\s+(.+)$/)
          : itemLine.match(/^[-*]\s+(.+)$/);
        if (!itemMatch) break;
        items.push(itemMatch[1].trim());
        i += 1;
      }
      blocks.push({ type: "list", ordered, items });
      continue;
    }

    const paragraph = [trimmed];
    i += 1;
    while (i < lines.length) {
      const next = lines[i].trim();
      if (!next) break;
      if (/^(#{1,6})\s+/.test(next) || next.startsWith(">") || /^---+$/.test(next) || isImageLine(next)) break;
      if (/^[-*]\s+/.test(next) || /^\d+[.)]\s+/.test(next) || /^\s*\|.*\|\s*$/.test(next) || /^```/.test(next)) break;
      paragraph.push(next);
      i += 1;
    }
    blocks.push({ type: "paragraph", text: paragraph.join(" ") });
  }

  return blocks;
}

function groupConsecutiveImages(blocks) {
  const grouped = [];
  for (let index = 0; index < blocks.length;) {
    if (blocks[index].type !== "image") {
      grouped.push(blocks[index]);
      index += 1;
      continue;
    }

    const images = [];
    while (blocks[index]?.type === "image") {
      images.push(blocks[index]);
      index += 1;
    }
    grouped.push(images.length === 1 ? images[0] : { type: "imageGroup", images });
  }
  return grouped;
}

function takeOpening(blocks) {
  const remaining = [...blocks];
  const titleIndex = remaining.findIndex((block) => block.type === "heading" && block.level === 1);
  const title = titleIndex >= 0 ? plainInline(remaining[titleIndex].text) : "未命名文章";
  if (titleIndex >= 0) remaining.splice(titleIndex, 1);

  const deckIndex = remaining.findIndex((block) => block.type === "quote");
  const deck = deckIndex >= 0
    ? plainInline(remaining[deckIndex].lines.join(" "))
    : "";
  if (deckIndex >= 0) remaining.splice(deckIndex, 1);

  const summaryIndex = remaining.findIndex((block) => (
    block.type === "paragraph" && /一句话总结/.test(block.text)
  ));
  const summary = summaryIndex >= 0
    ? plainInline(remaining[summaryIndex].text.replace(/^(\*\*)?一句话总结[:：](\*\*)?\s*/, ""))
    : deck;
  if (summaryIndex >= 0) remaining.splice(summaryIndex, 1);

  while (remaining[0]?.type === "hr") remaining.shift();

  return { title, deck, summary, blocks: groupConsecutiveImages(remaining) };
}

// ── HTML generation ──────────────────────────────────────────────
let _sectionNum = 0;
function headingHtml(block) {
  const tokens = getTokens();
  const ff = tokens.headingFontFamily || tokens.fontFamily;
  const prefix = tokens.headingPrefix ? `<span style="color:${tokens.accent};">${tokens.headingPrefix}</span> ` : "";
  if (block.level === 2) {
    if (ACTIVE_STYLE === "cultural-essay") {
      return `<h2 style="${SAFE_WRAP} font-size:21px; color:${tokens.blue}; margin:4px 0 18px; padding:12px 14px 12px 13px; background:#f3f8f6; border-left:4px solid ${tokens.accent}; border-radius:0 10px 10px 0; letter-spacing:0; line-height:1.45; font-family:'Songti SC','Noto Serif SC','STSong','SimSun','PingFang SC','Hiragino Sans GB',serif; font-weight:700;">${inline(block.text)}</h2>`;
    }
    if (ACTIVE_STYLE === "editorial-magazine") {
      // 杂志风 H2：超大上下留白 + 左侧 accent 短线 + 粗体大字号 + 近黑色
      return `<h2 class="dark-heading" style="${SAFE_WRAP} font-size:26px; color:${tokens.text}; margin:52px 0 22px; letter-spacing:-.01em; line-height:1.35; font-family:${ff}; font-weight:800; padding-left:16px; border-left:4px solid ${tokens.accent};">${inline(block.text)}</h2>`;
    }
    if (ACTIVE_STYLE === "neo-futurism") {
      // 国风编辑风 H2：深墨色渐变背景 + 陶土朱红编号块 + 白字，低调高级不刺眼
      const num = typeof _sectionNum !== "undefined" ? String(_sectionNum).padStart(2, "0") : "";
      const numHtml = num
        ? `<div style="${SAFE_WRAP} display:inline-flex; align-items:center; justify-content:center; min-width:38px; padding:0 12px; height:100%; background:linear-gradient(180deg,rgba(255,230,180,.25),rgba(212,166,78,.18)); color:#ffe6b4; font-size:13px; font-weight:800; letter-spacing:.04em; font-family:'SF Mono',ui-monospace,Menlo,monospace; margin-right:0; flex-shrink:0; border-right:1px solid rgba(255,230,180,.22); text-shadow:0 1px 4px rgba(0,0,0,.2);">${num}</div>`
        : "";
      return `<h2 class="dark-heading" style="${SAFE_WRAP} position:relative; display:flex; align-items:stretch; font-size:18px; color:#fff; margin:32px 0 20px; letter-spacing:.01em; line-height:1.3; font-family:${ff}; font-weight:700; background:linear-gradient(120deg,#7a1f0f 0%,#b53d1f 38%,#c45a3a 68%,#d4873e 100%); padding:0; border-radius:3px; overflow:hidden; box-shadow:0 2px 10px rgba(122,31,15,.15),inset 0 1px 0 rgba(255,255,255,.12);">
        ${numHtml}
        <span style="${SAFE_WRAP} position:relative; z-index:1; padding:13px 20px 13px 0;">${inline(block.text)}</span>
      </h2>`;
    }
    return `<h2 class="dark-heading" style="${SAFE_WRAP} font-size:21px; color:${tokens.blue}; margin:0 0 16px; padding-bottom:11px; border-bottom:1px dashed rgba(74,124,155,.34); letter-spacing:0; line-height:1.45; font-family:${ff};">${prefix}${inline(block.text)}</h2>`;
  }
  if (block.level === 3) {
    if (ACTIVE_STYLE === "editorial-magazine") {
      // 杂志风 H3：深靛蓝 + 半粗体 + 较大字号 + 无装饰线，干净利落
      return `<h3 style="${SAFE_WRAP} font-size:20px; color:${tokens.blue}; margin:32px 0 14px; line-height:1.45; font-weight:700; font-family:${ff}; letter-spacing:-.005em;">${inline(block.text)}</h3>`;
    }
    if (ACTIVE_STYLE === "neo-futurism") {
      // 国风编辑风 H3：陶土朱红短竖线 + 粗体黑字，紧凑有力
      return `<h3 style="${SAFE_WRAP} font-size:18px; color:${tokens.text}; margin:32px 0 14px; line-height:1.4; font-weight:700; font-family:${ff}; letter-spacing:-.005em; border-left:4px solid ${tokens.accent}; padding-left:12px;">${inline(block.text)}</h3>`;
    }
    return `<h3 style="${SAFE_WRAP} font-size:18px; color:${tokens.blue}; margin:22px 0 12px; line-height:1.5; border-left:4px solid ${tokens.accent}; padding-left:10px; font-family:${ff};">${inline(block.text)}</h3>`;
  }
  return `<h4 style="${SAFE_WRAP} font-size:16px; color:${tokens.muted}; margin:18px 0 10px; line-height:1.5; font-family:${ff};">${inline(block.text)}</h4>`;
}

function paragraphHtml(text) {
  const tokens = getTokens();
  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风段落：首行缩进 2em、行高更松、段间距更大
    return `<p style="${SAFE_WRAP} font-size:16px; line-height:${tokens.lineHeight}; color:${tokens.text}; margin:0 0 20px; letter-spacing:.02em; text-indent:2em;">${inline(text)}</p>`;
  }
  if (ACTIVE_STYLE === "neo-futurism") {
    // 国风编辑风段落：不缩进、行高 1.8、段间距 16px，节奏更紧凑
    return `<p style="${SAFE_WRAP} font-size:16px; line-height:1.8; color:${tokens.text}; margin:0 0 16px; letter-spacing:.01em;">${inline(text)}</p>`;
  }
  return `<p style="${SAFE_WRAP} font-size:16px; line-height:${tokens.lineHeight}; color:${tokens.text}; margin:0 0 16px; letter-spacing:0;">${inline(text)}</p>`;
}

function highlightHtml(block) {
  const tokens = getTokens();
  return `<div style="${SAFE_WRAP} margin:8px 0 20px; padding:14px 15px; background:${tokens.highlightBg || "#fff8f5"}; border:1px solid ${tokens.highlightBorder || "rgba(216,75,55,.18)"}; border-left:4px solid ${tokens.accent}; border-radius:10px;">
  <div style="${SAFE_WRAP} color:${tokens.highlightColor || tokens.text}; font-size:15px; line-height:1.85; font-weight:600; margin:0;">${inline(block.text)}</div>
</div>`;
}

function questionStackHtml(block) {
  const tokens = getTokens();
  const labels = getLabels();
  const questions = block.lines
    .map((line) => {
      const text = plainInline(line).trim();
      return text.startsWith("💡") ? text.slice("💡".length).trim() : text;
    })
    .filter(Boolean);
  const rows = questions.map((question, index) => `<div style="${SAFE_WRAP} margin:${index === 0 ? "0" : "9px"} 0 0; padding:9px 11px; background:#ffffff; border:1px solid rgba(74,124,155,.14); border-radius:8px;">
    <span style="display:inline-block; width:28px; color:${tokens.accent}; font-size:13px; font-weight:700; vertical-align:top;">${String(index + 1).padStart(2, "0")}</span>
    <span style="color:#344657; font-size:15px; line-height:1.55; font-weight:700; vertical-align:top;">${escapeHtml(question)}</span>
  </div>`).join("");
  return `<div style="${SAFE_WRAP} margin:0 0 16px; padding:13px; background:#f7fafb; border:1px solid rgba(74,124,155,.16); border-radius:10px;">
  <div style="${SAFE_WRAP} color:${tokens.blue}; font-size:13px; font-weight:700; margin:0 0 10px;">${escapeHtml(labels.questionLabel || "关键问题")}</div>
  ${rows}
</div>`;
}

function thesisCalloutHtml(block) {
  const tokens = getTokens();
  const labels = getLabels();
  const text = block.lines.join(" ").trim().replace(/^💡\s*\*\*核心判断\*\*[:：]\s*/, "");
  return `<div style="${SAFE_WRAP} margin:0 0 18px; padding:14px 15px; background:#fff8f5; border:1px solid rgba(216,75,55,.18); border-left:4px solid ${tokens.accent}; border-radius:0 10px 10px 0;">
  <div style="${SAFE_WRAP} color:${tokens.accent}; font-size:13px; line-height:1.4; font-weight:700; margin:0 0 7px;">${escapeHtml(labels.thesisLabel || "核心判断")}</div>
  <div style="${SAFE_WRAP} color:${tokens.text}; font-size:15px; line-height:1.8; margin:0;">${inline(text)}</div>
</div>`;
}

function quoteHtml(block) {
  const tokens = getTokens();
  const plainLines = block.lines.map((line) => plainInline(line));
  const normalizedLines = plainLines.map((line) => {
    const text = line.trim();
    return text.startsWith("💡") ? text.slice("💡".length).trim() : text;
  });
  if (normalizedLines.length === 3 && normalizedLines.every((line) => line.startsWith("为什么是"))) {
    return questionStackHtml(block);
  }
  if (normalizedLines.some((line) => line.startsWith("核心判断：") || line.startsWith("核心判断:"))) {
    return thesisCalloutHtml(block);
  }

  const content = block.lines
    .filter((line) => line.trim())
    .map((line) => {
      if (/^[-*]\s+/.test(line.trim())) {
        return `<div style="margin-top:6px;">• ${inline(line.trim().replace(/^[-*]\s+/, ""))}</div>`;
      }
      return `<div>${inline(line)}</div>`;
    })
    .join("");
  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风引用：大字号衬线 + 大引号装饰 + 宽左右边距 + 无背景色
    return `<blockquote class="dark-quote" style="${SAFE_WRAP} margin:28px 24px 28px; padding:0; background:transparent; border-left:none; color:${tokens.text}; font-size:17px; line-height:1.85; font-family:'Noto Serif SC','Songti SC','STSong','SimSun',serif; font-weight:500; font-style:italic;">
  <div style="${SAFE_WRAP} font-size:48px; line-height:0.8; color:${tokens.accent}; margin:0 0 12px; font-family:Georgia,serif; font-style:normal;">&ldquo;</div>
  ${content}
  <div style="${SAFE_WRAP} font-size:48px; line-height:0.8; color:${tokens.accent}; margin:12px 0 0; text-align:right; font-family:Georgia,serif; font-style:normal;">&rdquo;</div>
</blockquote>`;
  }
  if (ACTIVE_STYLE === "neo-futurism") {
    // 国风编辑风引用：衬线大字号 + 居中 + 陶土朱红上下线 + 雅致感
    return `<blockquote class="dark-quote" style="${SAFE_WRAP} margin:32px 0; padding:24px 16px; border-top:1px solid ${tokens.accent}; border-bottom:1px solid ${tokens.accent}; background:transparent; color:${tokens.text}; font-size:18px; line-height:1.8; font-weight:600; letter-spacing:.02em; text-align:center; font-family:'Noto Serif SC','Songti SC','STSong',serif; font-style:italic;">${content}</blockquote>`;
  }
  return `<blockquote class="dark-quote" style="${SAFE_WRAP} margin:0 0 18px; padding:15px 16px; background:${tokens.quoteBg}; border-left:4px solid ${tokens.quoteBorder}; border-radius:0 10px 10px 0; color:${tokens.muted}; font-size:15px; line-height:${tokens.lineHeight};">${content}</blockquote>`;
}

function listHtml(block) {
  const tokens = getTokens();
  const tag = block.ordered ? "ol" : "ul";
  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风列表：更大间距 + 自定义 accent 色小圆点 + 稍大字号
    const items = block.items
      .map((item, idx) => {
        const bullet = block.ordered
          ? `<span style="display:inline-block; min-width:22px; color:${tokens.accent}; font-weight:700; font-family:Georgia,serif;">${idx + 1}.</span>`
          : `<span style="display:inline-block; width:6px; height:6px; background:${tokens.accent}; border-radius:50%; margin-right:12px; vertical-align:middle; transform:translateY(-2px);"></span>`;
        return `<li style="${SAFE_WRAP} margin:0 0 12px; list-style:none; padding-left:0;">${bullet}${inline(item)}</li>`;
      })
      .join("");
    return `<${tag} style="${SAFE_WRAP} padding-left:0; margin:0 0 22px; color:${tokens.text}; font-size:16px; line-height:${tokens.lineHeight}; list-style:none;">${items}</${tag}>`;
  }
  if (ACTIVE_STYLE === "neo-futurism") {
    // 国风编辑风列表：用原生ul/ol + list-style-type，微信100%稳定渲染（和默认分支一致的成熟方案）
    const items = block.items
      .map((item) => `<li style="${SAFE_WRAP} margin:0 0 10px; padding-left:4px; color:${tokens.accent};"><span style="color:${tokens.text};">${inline(item)}</span></li>`)
      .join("");
    const listStyle = block.ordered
      ? `padding-left:26px; margin:0 0 22px; color:${tokens.text}; font-size:16px; line-height:${tokens.lineHeight}; list-style-type:decimal;`
      : `padding-left:24px; margin:0 0 22px; color:${tokens.accent}; font-size:16px; line-height:${tokens.lineHeight}; list-style-type:disc;`;
    return `<${tag} style="${SAFE_WRAP} ${listStyle}">${items}</${tag}>`;
  }
  // 默认分支：统一使用自定义 bullet，避免微信编辑器对原生 list-style-type 的异常渲染
  // （常见表现为数字后带冒号/空白占位）。
  const items = block.items
    .map((item, idx) => {
      const bullet = block.ordered
        ? `<span style="display:inline-block; min-width:22px; color:${tokens.accent}; font-weight:700; font-family:Georgia,serif; flex-shrink:0;">${idx + 1}.</span>`
        : `<span style="display:inline-block; width:6px; height:6px; background:${tokens.accent}; border-radius:50%; margin-right:10px; vertical-align:middle; transform:translateY(-2px); flex-shrink:0;"></span>`;
      return `<li style="${SAFE_WRAP} margin:0 0 8px; list-style:none; padding-left:0; display:flex; align-items:flex-start; gap:4px;">${bullet}<span style="color:${tokens.text};">${inline(item)}</span></li>`;
    })
    .join("");
  return `<${tag} style="${SAFE_WRAP} padding-left:0; margin:0 0 16px; font-size:15px; line-height:${tokens.lineHeight}; list-style:none;">${items}</${tag}>`;
}

function referenceListHtml(block) {
  const tokens = getTokens();
  const items = block.items.map((item, index) => {
    const match = item.match(/^\[([^\]]+)]\(([^)]+)\)\s*[-—]\s*(.+)$/);
    if (!match) {
      return `<div style="${SAFE_WRAP} margin:0; padding:8px 0; border-bottom:1px solid rgba(74,124,155,.12); color:${tokens.text}; font-size:13px; line-height:1.55;">${inline(item)}</div>`;
    }
    const [, title, _href, rawSource] = match;
    const source = plainInline(rawSource);
    return `<div style="${SAFE_WRAP} margin:0; padding:8px 0; border-bottom:1px solid rgba(74,124,155,.12);">
  <div style="${SAFE_WRAP} color:#8b97a3; font-size:11px; line-height:1.35; font-weight:600; margin:0 0 3px;">${String(index + 1).padStart(2, "0")} · ${escapeHtml(source)}</div>
  <div style="${SAFE_WRAP} color:${tokens.blue}; font-size:13px; line-height:1.5; font-weight:500;">${escapeHtml(title)}</div>
</div>`;
  }).join("");
  return `<div style="${SAFE_WRAP} margin:-2px 0 0;">${items}</div>`;
}

function imageHtml(block) {
  const tokens = getTokens();
  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风图片：更大上下间距 + 斜体图说 + 左侧短 accent 线 + 更小圆角
    return `<figure style="${SAFE_WRAP} width:100%; margin:28px 0 32px; text-align:center;">
  <img ${imageAttrs(block.src, block.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:4px; display:block; margin:0 auto; box-shadow:0 4px 20px rgba(0,0,0,.08);">
  <figcaption style="${SAFE_WRAP} font-size:13px; line-height:1.6; color:${tokens.muted}; margin:14px 0 0; padding-left:12px; border-left:2px solid ${tokens.accent}; text-align:left; font-style:italic;">${escapeHtml(block.alt)}</figcaption>
</figure>`;
  }
  if (ACTIVE_STYLE === "neo-futurism") {
    // 新未来主义图片：全出血 + 顶部 accent 细线 + 下方小字图说；封面图简化（无 accent 线、无 caption）
    const isCover = block.alt === "封面" || block.alt === "cover" || /(^|[\/\\])cover\.(png|jpg|jpeg|webp)$/i.test(block.src);
    if (isCover) {
      return `<figure style="${SAFE_WRAP} width:100%; margin:0 0 32px; text-align:center;">
  <img ${imageAttrs(block.src, block.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:0; display:block; margin:0;">
</figure>`;
    }
    return `<figure style="${SAFE_WRAP} width:100%; margin:28px 0 32px; text-align:center;">
  <img ${imageAttrs(block.src, block.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:4px; display:block; margin:0; box-shadow:0 2px 12px rgba(0,0,0,.06);">
  ${block.alt && !isCover ? `<figcaption style="${SAFE_WRAP} font-size:12px; line-height:1.6; color:${tokens.muted}; margin:10px 0 0; letter-spacing:.02em;">${escapeHtml(block.alt)}</figcaption>` : ""}
</figure>`;
  }
  return `<figure style="${SAFE_WRAP} width:100%; margin:20px 0; text-align:center;">
  <img ${imageAttrs(block.src, block.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:10px; display:block; margin:0 auto;">
  <figcaption style="${SAFE_WRAP} font-size:13px; line-height:1.65; color:#6a727a; margin:10px 0 0;">${escapeHtml(block.alt)}</figcaption>
</figure>`;
}

function videoPlaceholderHtml(block) {
  const tokens = getTokens();
  const srcLabel = block.src ? path.basename(block.src) : "待替换视频素材";
  const posterHtml = block.poster
    ? `<div style="${SAFE_WRAP} margin:0 0 10px; text-align:center;">
      <img ${imageAttrs(block.poster, "视频封面")} style="box-sizing:border-box; width:100%; max-width:420px; height:auto; border-radius:8px; display:block; margin:0 auto;">
    </div>`
    : "";
  return `<div style="${SAFE_WRAP} margin:20px 0; padding:14px 15px; background:#f8faf9; border:1px dashed ${tokens.panelBorder === "transparent" ? "rgba(52,95,90,.28)" : tokens.panelBorder}; border-radius:10px;">
  ${posterHtml}
  <div style="${SAFE_WRAP} color:${tokens.accent}; font-size:13px; line-height:1.5; font-weight:700; margin:0 0 5px;">视频素材位</div>
  <div style="${SAFE_WRAP} color:${tokens.text}; font-size:14px; line-height:1.7; margin:0;">${escapeHtml(srcLabel)}</div>
  <div style="${SAFE_WRAP} color:${tokens.muted}; font-size:12px; line-height:1.6; margin:7px 0 0;">发布时替换为视频号、腾讯视频或微信素材库视频。</div>
</div>`;
}

function imageGroupHtml(block) {
  const tokens = getTokens();
  const labels = getLabels();
  const [lead, ...rest] = block.images;
  const leadHtml = lead ? `<div style="${SAFE_WRAP} margin:0 0 12px; text-align:center;">
    <img ${imageAttrs(lead.src, lead.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:8px; display:block; margin:0 auto;">
    <p style="${SAFE_WRAP} font-size:13px; line-height:1.65; color:#6a727a; margin:9px 0 0;">${escapeHtml(lead.alt)}</p>
  </div>` : "";
  const secondaryHtml = rest.length > 0 ? `<div style="${SAFE_WRAP} font-size:0; margin:0;">
    ${rest.map((image, index) => `<div style="${SAFE_WRAP} display:inline-block; width:${rest.length === 1 ? "100%" : "49%"}; margin:${index % 2 === 0 ? "0 2% 0 0" : "0"}; vertical-align:top; text-align:center;">
      <img ${imageAttrs(image.src, image.alt)} style="box-sizing:border-box; width:100%; max-width:100%; height:auto; border-radius:8px; display:block; margin:0 auto;">
      <p style="${SAFE_WRAP} font-size:12px; line-height:1.55; color:#6a727a; margin:8px 0 0;">${escapeHtml(image.alt)}</p>
    </div>`).join("")}
  </div>` : "";
  return `<div style="${SAFE_WRAP} width:100%; background:linear-gradient(135deg,#f7f9fb,#edf4f8); border:1px solid rgba(74,124,155,.16); border-radius:12px; padding:14px; margin:20px 0; text-align:left;">
  <div style="${SAFE_WRAP} font-size:13px; color:${tokens.accent}; font-weight:700; margin:0 0 10px;">${escapeHtml(labels.galleryLabel || "公告截图速览")}</div>
  ${leadHtml}
  ${secondaryHtml}
</div>`;
}

function tableHtml(block) {
  const tokens = getTokens();
  const columnCount = Math.max(block.header.length, ...block.rows.map((row) => row.length));
  let columnWidths = [];
  if (columnCount === 2) {
    columnWidths = ["22%", "78%"];
  } else if (columnCount === 3) {
    columnWidths = ["30%", "35%", "35%"];
  } else {
    columnWidths = Array.from({ length: columnCount }, () => `${(100 / columnCount).toFixed(4)}%`);
  }
  // IMPORTANT: do NOT use a real <table>/<th>/<td>. WeChat's editor recognises
  // table tags and automatically wraps them in a dashed "table editing" box
  // (with a blank toolbar strip above). That box can't be removed via inline
  // styles. We instead draw the table with flex rows of <div>s, which WeChat
  // leaves alone — no dashed box, and column widths are fully respected.
  const headerBg = tokens.tableHeaderBg || "#f8fafc";
  const headerColor = tokens.tableHeaderColor || "#6b7d8e";

  const headerCells = block.header.map((cell, i) => {
    const w = columnWidths[i] || "auto";
    return `<div style="${SAFE_WRAP} box-sizing:border-box; width:${w}; flex:0 0 ${w}; padding:10px 10px; color:${headerColor}; font-size:12px; line-height:1.4; font-weight:600; text-align:left; letter-spacing:.02em;">${inline(cell)}</div>`;
  }).join("");
  const headerRow = `<div style="${SAFE_WRAP} display:flex; width:100%; background:${headerBg}; border-radius:6px 6px 0 0;">${headerCells}</div>`;

  const bodyRows = block.rows.map((row, index) => {
    const last = index === block.rows.length - 1;
    const bb = last ? "border-bottom:1.5px solid rgba(0,0,0,.10);" : "border-bottom:1px solid rgba(0,0,0,.07);";
    const cells = row.map((cell, cellIndex) => {
      const w = columnWidths[cellIndex] || "auto";
      const isFirst = cellIndex === 0;
      return `<div style="${SAFE_WRAP} box-sizing:border-box; width:${w}; flex:0 0 ${w}; padding:10px 10px; font-size:14px; line-height:1.7; color:${isFirst ? tokens.blue : tokens.text}; font-weight:${isFirst ? "600" : "400"};">${inline(cell)}</div>`;
    }).join("");
    return `<div style="${SAFE_WRAP} display:flex; width:100%; ${bb}">${cells}</div>`;
  }).join("");

  return `<section style="${SAFE_WRAP} width:100%; margin:4px 0 20px; border-top:1.5px solid rgba(0,0,0,.10);">${headerRow}${bodyRows}</section>`;
}

// Syntax highlight palette (inline styles — WeChat strips classes & <style> blocks).
const CODE_COLORS = {
  base: "#e6edf3",
  comment: "#8b949e",
  muted: "#8b949e",
  string: "#a5d6ff",
  number: "#79c0ff",
  keyword: "#ff7b72",
  literal: "#79c0ff",
  type: "#ffa657",
  func: "#d2a8ff",
};
const CODE_KEYWORDS = new Set([
  // rust
  "fn","let","mut","pub","async","await","match","return","struct","enum","impl","use","mod","crate","as","ref","move","where","trait","dyn","unsafe","loop",
  // python
  "def","class","elif","with","import","from","try","except","finally","raise","lambda","yield","pass","global","nonlocal","and","or","not","is","del","assert","in",
  // shared control / js / ts
  "if","else","for","while","break","continue","function","var","const","static","new","this","export","default","typeof","instanceof","case","switch","throw","catch","do","void","extends","super","public","private","protected","interface","type",
]);
const CODE_LITERALS = new Set(["true","false","null","undefined","None","True","False","self","Self","Some","Ok","Err"]);

function codeCommentLeaders(lang) {
  const l = (lang || "").toLowerCase();
  if (["python","py","bash","sh","shell","zsh","yaml","yml","ruby","rb","toml","ini","makefile","dockerfile","conf","r"].includes(l)) return ["#"];
  if (["rust","rs","js","javascript","jsx","ts","typescript","tsx","go","c","cpp","h","java","json","jsonc","swift","kotlin","kt","scala","php"].includes(l)) return ["//"];
  return ["//", "#"]; // unknown / plain fences (ASCII flows, daemon examples)
}

function highlightCodeLine(line, leaders) {
  let out = "";
  let i = 0;
  const n = line.length;
  while (i < n) {
    const ch = line[i];
    const leader = leaders.find((cl) => line.startsWith(cl, i));
    if (leader) { // line comment → end of line
      out += `<span style="color:${CODE_COLORS.comment};">${escapeHtml(line.slice(i))}</span>`;
      break;
    }
    if (ch === '"' || ch === "'" || ch === "`") { // string literal
      let j = i + 1;
      while (j < n) { if (line[j] === "\\") { j += 2; continue; } if (line[j] === ch) { j += 1; break; } j += 1; }
      out += `<span style="color:${CODE_COLORS.string};">${escapeHtml(line.slice(i, j))}</span>`;
      i = j; continue;
    }
    if (/\d/.test(ch) && !/[A-Za-z_]/.test(line[i - 1] || "")) { // number
      const m = /^\d[\d_]*(?:\.[\d_]+)?/.exec(line.slice(i));
      out += `<span style="color:${CODE_COLORS.number};">${escapeHtml(m[0])}</span>`;
      i += m[0].length; continue;
    }
    if (/[A-Za-z_$]/.test(ch)) { // identifier / keyword / type / call
      const w = /^[A-Za-z_$][A-Za-z0-9_$]*/.exec(line.slice(i))[0];
      let color = null;
      if (CODE_KEYWORDS.has(w)) color = CODE_COLORS.keyword;
      else if (CODE_LITERALS.has(w)) color = CODE_COLORS.literal;
      else if (/^[A-Z]/.test(w)) color = CODE_COLORS.type;
      else { let k = i + w.length; while (k < n && line[k] === " ") k += 1; if (line[k] === "(") color = CODE_COLORS.func; }
      out += color ? `<span style="color:${color};">${escapeHtml(w)}</span>` : escapeHtml(w);
      i += w.length; continue;
    }
    out += escapeHtml(ch); // punctuation / spaces
    i += 1;
  }
  return out;
}

function codeHtml(block) {
  // WeChat collapses \n and leading whitespace, and strips `white-space:pre`.
  // Robust horizontal-scroll recipe that survives WeChat's sanitizer:
  //   • <br> for line breaks, &nbsp; for indentation (literal whitespace is lost)
  //   • OUTER element: overflow-x:auto  → the scroll viewport
  //   • INNER element: white-space:nowrap + display:inline-block → lines never wrap,
  //     the block grows to the widest line, the viewport scrolls horizontally.
  // `nowrap` is preserved by WeChat far more reliably than `pre`.
  const leaders = codeCommentLeaders(block.lang);
  const body = block.text.split("\n").map((line) => {
    const lead = (line.match(/^[ \t]*/) || [""])[0];
    const indent = "&nbsp;".repeat(lead.replace(/\t/g, "    ").length);
    return indent + highlightCodeLine(line.slice(lead.length), leaders);
  }).join("<br>");
  const langLabel = block.lang
    ? `<div style="box-sizing:border-box; font-size:11px; color:${CODE_COLORS.muted}; margin:0 0 10px; letter-spacing:.06em; font-weight:600; text-transform:uppercase; font-family:'SF Mono',SFMono-Regular,ui-monospace,Menlo,Monaco,Consolas,monospace;">${escapeHtml(block.lang)}</div>`
    : "";
  const inner = `<div style="display:inline-block; min-width:100%; white-space:nowrap; font-size:14px; line-height:1.7; font-family:'SF Mono',SFMono-Regular,ui-monospace,Menlo,Monaco,Consolas,'Liberation Mono','Courier New',monospace;">${body}</div>`;
  const tokens = getTokens();
  if (ACTIVE_STYLE === "editorial-magazine") {
    // 杂志风代码块：更紧凑的圆角 + 更暗的深靛蓝底色 + 小字号
    return `<section class="dark-code" style="box-sizing:border-box; max-width:100%; overflow-x:auto; background:#162032; color:${CODE_COLORS.base}; border-radius:4px; padding:12px 14px; margin:0 0 22px; border-left:3px solid ${tokens.accent};">${langLabel}${inner}</section>`;
  }
  if (ACTIVE_STYLE === "neo-futurism") {
    // 新未来主义代码块：纯黑底 + 电光青左边框 + 无圆角（或极小）
    return `<section class="dark-code" style="box-sizing:border-box; max-width:100%; overflow-x:auto; background:#000000; color:#e6edf3; border-radius:2px; padding:16px 18px; margin:0 0 24px; border-left:3px solid ${tokens.accent};">${langLabel}${inner}</section>`;
  }
  return `<section class="dark-code" style="box-sizing:border-box; max-width:100%; overflow-x:auto; background:#1f252c; color:${CODE_COLORS.base}; border-radius:10px; padding:14px 16px; margin:0 0 18px;">${langLabel}${inner}</section>`;
}

function blockHtml(block) {
  switch (block.type) {
    case "heading":
      return headingHtml(block);
    case "paragraph":
      return paragraphHtml(block.text);
    case "highlight":
      return highlightHtml(block);
    case "quote":
      return quoteHtml(block);
    case "list":
      return listHtml(block);
    case "image":
      return imageHtml(block);
    case "videoPlaceholder":
      return videoPlaceholderHtml(block);
    case "imageGroup":
      return imageGroupHtml(block);
    case "table":
      return tableHtml(block);
    case "code":
      return codeHtml(block);
    case "hr":
      if (ACTIVE_STYLE === "editorial-magazine") {
        // 杂志风分割线：居中短细线 + 上下大留白
        return `<div style="text-align:center; margin:40px 0;"><span style="display:inline-block; width:40px; height:1px; background:${getTokens().accent};"></span></div>`;
      }
      if (ACTIVE_STYLE === "neo-futurism") {
        // 国风编辑风：H2深色块已天然分隔章节，不需要额外分割线
        return ``;
      }
      return `<div style="height:1px; background:linear-gradient(90deg,transparent,rgba(74,124,155,.28),transparent); margin:22px 0;"></div>`;
    default:
      return "";
  }
}

function outlineItems(blocks) {
  return blocks
    .filter((block) => block.type === "heading" && block.level === 2)
    .slice(0, 6)
    .map((block, index) => {
      const raw = plainInline(block.text);
      const match = raw.match(/^(\d{1,2})\s+(.+)$/);
      return {
        id: `section-${index + 1}`,
        number: match ? match[1].padStart(2, "0") : String(index + 1).padStart(2, "0"),
        text: match ? match[2] : raw,
      };
    });
}

function renderBody(blocks) {
  const tokens = getTokens();
  const chunks = [];
  let current = [];

  for (const block of blocks) {
    if (block.type === "heading" && block.level === 2 && current.length > 0) {
      chunks.push(current);
      current = [block];
    } else {
      current.push(block);
    }
  }
  if (current.length > 0) chunks.push(current);

  let sectionIndex = 0;
  _sectionNum = 0;
  return chunks.map((chunk) => {
    const standaloneImages = chunk.length === 1 && chunk[0].type === "image";
    if (standaloneImages) return imageHtml(chunk[0]);
    const firstBlock = chunk[0];
    const isReferenceSection = firstBlock?.type === "heading" && firstBlock.level === 2 && plainInline(firstBlock.text) === "参考资料";
    const isH2Section = firstBlock?.type === "heading" && firstBlock.level === 2;
    if (isH2Section) _sectionNum += 1;
    const anchor = isH2Section
      ? ` id="section-${++sectionIndex}"`
      : "";
    const sectionStyle = tokens.useCards
      ? `background:${tokens.cardBg}; border:1px solid ${tokens.panelBorder}; border-radius:14px; padding:22px 18px; box-shadow:${tokens.shadow}; margin-bottom:22px;`
      : `background:transparent; padding:0 0 32px; margin-bottom:0;`;
    const sectionClass = tokens.useCards ? "dark-card dark-border" : "";
    return `<section${anchor}${sectionClass ? ` class="${sectionClass}"` : ""} style="${SAFE_WRAP} width:100%; ${sectionStyle}">
${chunk.map((block) => (isReferenceSection && block.type === "list" ? referenceListHtml(block) : blockHtml(block))).join("\n")}
</section>`;
  }).join("\n");
}

function closingPanelHtml() {
  const tokens = getTokens();
  const labels = getLabels();
  if (!tokens.closingPanel || !labels.closingCTA) return "";
  return `<section style="${SAFE_WRAP} width:100%; background:#1f252c; color:#d4d9df; border-radius:14px; padding:24px 20px; margin-top:28px; text-align:center; box-shadow:${tokens.shadow};">
    <p style="${SAFE_WRAP} font-size:16px; line-height:1.8; color:#e8ebef; margin:0; font-family:${tokens.fontFamily};">${escapeHtml(labels.closingCTA)}</p>
  </section>`;
}

function renderDocument({ title, deck, summary, blocks }) {
  const tokens = getTokens();
  const labels = getLabels();

  // ── Hero section ──
  let heroHtml;
  const ff = tokens.headingFontFamily || tokens.fontFamily;
  if (tokens.heroStyle === "none") {
    // 不渲染 hero 区块
    heroHtml = "";
  } else if (tokens.heroStyle === "neo-title") {
    // 简洁标题区：标题 + 一句话副标题，无冗余装饰
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:transparent; padding:16px 0 24px; margin-bottom:8px;">
        <h1 style="${SAFE_WRAP} font-size:26px; line-height:1.4; color:${tokens.text}; margin:0 0 14px; font-weight:800; letter-spacing:-.01em; font-family:${ff};">${escapeHtml(title)}</h1>
        ${deck ? `<p style="${SAFE_WRAP} font-size:15px; line-height:1.75; color:${tokens.muted}; margin:0;">${escapeHtml(deck)}</p>` : ""}
      </section>`;
  } else if (tokens.heroStyle === "cultural") {
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:#fff; padding:18px 2px 24px; text-align:left; margin-bottom:26px; border-bottom:1px solid rgba(154,91,47,.16);">
        <div style="${SAFE_WRAP} color:${tokens.accent}; font-size:12px; line-height:1; margin:0 0 14px; letter-spacing:0; font-family:${tokens.fontFamily};">
          <span style="display:inline-block; width:28px; height:1px; background:${tokens.accent}; vertical-align:middle; margin-right:9px;"></span>${escapeHtml(labels.heroLabel)}
        </div>
        <h1 style="${SAFE_WRAP} font-size:25px; line-height:1.46; color:${tokens.text}; margin:0; font-weight:800; letter-spacing:0; font-family:${ff};">${escapeHtml(title)}</h1>
        ${deck ? `<p style="${SAFE_WRAP} font-size:15px; line-height:1.85; color:${tokens.muted}; margin:15px 0 0;">${escapeHtml(deck)}</p>` : ""}
      </section>`;
  } else if (tokens.heroStyle === "centered") {
    heroHtml = `<section class="dark-hero" style="${SAFE_WRAP} width:100%; background:${tokens.cardBg === "transparent" ? tokens.bodyBg : tokens.cardBg}; border-radius:14px; padding:32px 20px 28px; text-align:center; margin-bottom:24px;">
        ${labels.heroLabel ? `<div style="display:inline-block; color:${tokens.accent}; font-size:13px; line-height:1; padding:6px 10px; border:1px solid ${tokens.accent}; border-radius:4px; margin-bottom:18px; opacity:0.8;">${escapeHtml(labels.heroLabel)}</div>` : ""}
        <h1 style="${SAFE_WRAP} font-size:26px; line-height:1.4; color:#1f252c; margin:0 auto; font-weight:700; letter-spacing:0; font-family:${ff}; max-width:90%;">${escapeHtml(title)}</h1>
        ${deck ? `<p style="${SAFE_WRAP} font-size:15px; line-height:1.8; color:${tokens.muted}; margin:14px auto 0; max-width:86%;">${escapeHtml(deck)}</p>` : ""}
      </section>`;
  } else if (tokens.heroStyle === "warm") {
    // warm-editorial: minimal centered hero matching index.html vibe
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:transparent; padding:0 2px 18px; margin-bottom:28px;">
        <h1 style="${SAFE_WRAP} font-size:24px; line-height:1.45; color:${tokens.text}; margin:0 0 12px; font-weight:600; letter-spacing:0; font-family:${ff};">${escapeHtml(title)}</h1>
        ${deck ? `<p style="${SAFE_WRAP} font-size:14px; line-height:1.8; color:${tokens.muted}; margin:0;">${escapeHtml(deck)}</p>` : ""}
      </section>`;
  } else if (tokens.heroStyle === "magazine") {
    // editorial-magazine: 杂志封面式 hero，大标题 + 短分割线 + 副标题 + 日期标签
    const today = new Date();
    const dateStr = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}`;
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:transparent; padding:8px 2px 36px; margin-bottom:12px; border-bottom:1px solid rgba(0,0,0,.08);">
        <div style="${SAFE_WRAP} color:${tokens.accent}; font-size:11px; line-height:1; margin:0 0 18px; letter-spacing:.18em; font-weight:600; text-transform:uppercase; font-family:${tokens.fontFamily};">
          ${escapeHtml(labels.heroLabel || "深度特稿")}
        </div>
        <h1 style="${SAFE_WRAP} font-size:30px; line-height:1.35; color:${tokens.text}; margin:0 0 20px; font-weight:800; letter-spacing:-.01em; font-family:${ff};">${escapeHtml(title)}</h1>
        <div style="width:40px; height:3px; background:${tokens.accent}; margin:0 0 20px;"></div>
        ${deck ? `<p style="${SAFE_WRAP} font-size:16px; line-height:1.85; color:${tokens.muted}; margin:0 0 22px; font-weight:400;">${escapeHtml(deck)}</p>` : ""}
        <div style="${SAFE_WRAP} font-size:12px; line-height:1; color:${tokens.muted}; letter-spacing:.05em;">
          <span style="color:${tokens.blue}; font-weight:600;">OpenMontage</span>
          <span style="margin:0 8px; opacity:.4;">·</span>
          <span>${dateStr}</span>
          <span style="margin:0 8px; opacity:.4;">·</span>
          <span>约 8 分钟阅读</span>
        </div>
      </section>`;
  } else if (tokens.heroStyle === "neo-hero") {
    // neo-futurism 2.0 hero：全出血深色渐变背景 + 白字大标题 + 辉光 + 统计条 + 底部渐变过渡
    const today = new Date();
    const dateStr = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}`;
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:radial-gradient(circle at 85% 15%, rgba(0,229,199,.35) 0%, rgba(0,229,199,0) 45%), linear-gradient(135deg,#0a0a1f 0%,#1a1047 28%,#241b5c 52%,#0f4c5c 78%,${tokens.accent} 100%); padding:56px 20px 44px; margin:-40px -16px 36px; color:#fff;">
        <div style="${SAFE_WRAP} max-width:760px; margin:0 auto;">
          <div style="${SAFE_WRAP} display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border:1px solid rgba(255,255,255,.25); border-radius:100px; font-size:11px; letter-spacing:.22em; color:rgba(255,255,255,.85); font-family:'SF Mono',ui-monospace,Menlo,monospace; font-weight:600; margin:0 0 24px;">
            <span style="display:inline-block; width:6px; height:6px; background:${tokens.accent}; border-radius:50%; box-shadow:0 0 8px ${tokens.accent};"></span>
            OPEN SOURCE · AI VIDEO
          </div>
          <h1 style="${SAFE_WRAP} font-size:34px; line-height:1.22; color:#ffffff; margin:0 0 20px; font-weight:900; letter-spacing:-.02em; font-family:${ff}; text-shadow:0 2px 20px rgba(0,0,0,.3);">${escapeHtml(title)}</h1>
          ${deck ? `<p style="${SAFE_WRAP} font-size:16px; line-height:1.75; color:rgba(255,255,255,.82); margin:0 0 32px; font-weight:400; letter-spacing:.01em;">${escapeHtml(deck)}</p>` : ""}
          <div style="${SAFE_WRAP} display:flex; flex-wrap:wrap; gap:0; padding:20px 0 0; border-top:1px solid rgba(255,255,255,.18);">
            <div style="${SAFE_WRAP} flex:1; min-width:70px; padding-right:12px; border-right:1px solid rgba(255,255,255,.12);"><div style="font-size:26px; font-weight:900; color:#fff; line-height:1.1; font-family:${ff}; letter-spacing:-.02em;">12</div><div style="font-size:10px; color:rgba(255,255,255,.6); margin-top:6px; letter-spacing:.15em; font-weight:600;">PIPELINES</div></div>
            <div style="${SAFE_WRAP} flex:1; min-width:70px; padding:0 12px; border-right:1px solid rgba(255,255,255,.12);"><div style="font-size:26px; font-weight:900; color:#fff; line-height:1.1; font-family:${ff}; letter-spacing:-.02em;">57+</div><div style="font-size:10px; color:rgba(255,255,255,.6); margin-top:6px; letter-spacing:.15em; font-weight:600;">TOOLS</div></div>
            <div style="${SAFE_WRAP} flex:1; min-width:70px; padding:0 12px; border-right:1px solid rgba(255,255,255,.12);"><div style="font-size:26px; font-weight:900; color:#fff; line-height:1.1; font-family:${ff}; letter-spacing:-.02em;">500+</div><div style="font-size:10px; color:rgba(255,255,255,.6); margin-top:6px; letter-spacing:.15em; font-weight:600;">SKILLS</div></div>
            <div style="${SAFE_WRAP} flex:1; min-width:70px; padding-left:12px;"><div style="font-size:26px; font-weight:900; color:${tokens.accent}; line-height:1.1; font-family:${ff}; letter-spacing:-.02em; text-shadow:0 0 16px rgba(0,229,199,.5);">14</div><div style="font-size:10px; color:rgba(255,255,255,.6); margin-top:6px; letter-spacing:.15em; font-weight:600;">VIDEO AI</div></div>
          </div>
          <div style="${SAFE_WRAP} font-size:11px; color:rgba(255,255,255,.5); margin-top:18px; letter-spacing:.08em; font-weight:500;">
            <span style="color:rgba(255,255,255,.75); font-weight:600;">OpenMontage</span>
            <span style="margin:0 8px; opacity:.5;">·</span>
            <span>${dateStr}</span>
            <span style="margin:0 8px; opacity:.5;">·</span>
            <span>约 8 分钟阅读</span>
          </div>
        </div>
      </section>`;
  } else {
    // border-left hero (default for impact-rational and tech-blog)
    heroHtml = `<section style="${SAFE_WRAP} width:100%; background:${tokens.cardBg}; border-left:8px solid ${tokens.accent}; border-radius:0 14px 14px 0; padding:28px 20px; box-shadow:0 14px 38px rgba(54,72,89,.13); margin-bottom:24px;">
        <div style="display:inline-block; background:${tokens.accent}; color:#fff; font-size:13px; line-height:1; padding:7px 11px; border-radius:4px; margin-bottom:16px;">${escapeHtml(labels.heroLabel)}</div>
        <h1 style="${SAFE_WRAP} font-size:28px; line-height:1.28; color:#1f252c; margin:0 0 16px; font-weight:750; letter-spacing:0; font-family:${ff};">${escapeHtml(title)}</h1>
        ${deck ? `<p style="${SAFE_WRAP} font-size:16px; line-height:1.9; color:${tokens.muted}; margin:0;">${escapeHtml(deck)}</p>` : ""}
        ${deck ? `<div style="height:1px; background:linear-gradient(90deg,${tokens.accent},rgba(216,75,55,0)); margin:22px 0 0;"></div>` : ""}
      </section>`;
  }

  // ── Summary card ──
  const summaryHtml = (tokens.showSummary && summary)
    ? `<section style="${SAFE_WRAP} width:100%; background:${tokens.cardBg}; border:1px solid ${tokens.panelBorder}; border-radius:14px; padding:22px 18px 20px; box-shadow:${tokens.shadow}; margin-bottom:22px;">
        <div style="font-size:13px; color:${tokens.accent}; font-weight:700; margin-bottom:10px;">${escapeHtml(labels.authorNoteLabel || "作者想说")}</div>
        <p style="${SAFE_WRAP} font-size:16px; line-height:1.95; color:${tokens.text}; margin:0;">${escapeHtml(summary)}</p>
      </section>`
    : "";

  // ── Outline / reading map ──
  const mapItems = outlineItems(blocks);
  const mapHtml = (tokens.showOutline && mapItems.length > 0)
    ? `<section style="${SAFE_WRAP} width:100%; background:${tokens.cardBg}; border:1px solid ${tokens.panelBorder}; border-radius:14px; padding:22px 18px; box-shadow:${tokens.shadow}; margin-bottom:22px;">
  <h2 style="${SAFE_WRAP} font-size:20px; color:${tokens.blue}; margin:0 0 12px; padding-bottom:11px; border-bottom:1px dashed rgba(74,124,155,.34); letter-spacing:0;"><span style="color:${tokens.accent};">${tokens.headingPrefix}</span> ${escapeHtml(labels.outlineLabel || "阅读地图")}</h2>
  <div style="${SAFE_WRAP} margin:0;">
    ${mapItems.map((item) => `<div style="${SAFE_WRAP} display:block; color:#3a4652; margin:0 0 6px; line-height:1.55;">
      <span style="display:inline-block; min-width:32px; color:${tokens.accent}; font-size:13px; font-weight:700; letter-spacing:0;">${escapeHtml(item.number)}</span>
      <span style="font-size:15px;">${escapeHtml(item.text)}</span>
    </div>`).join("\n")}
  </div>
</section>` : "";

  return `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeAttr(summary || deck || title)}">
  ${tokens.darkBg ? `<style>@media(prefers-color-scheme:dark){body.dark-aware{background:${tokens.darkBg}!important}body.dark-aware .dark-card{background:${tokens.darkCardBg}!important;border-color:rgba(255,255,255,.08)!important}body.dark-aware .dark-text{color:${tokens.darkText}!important}body.dark-aware .dark-muted{color:${tokens.darkMuted}!important}body.dark-aware .dark-accent{color:${tokens.darkAccent}!important}body.dark-aware .dark-heading{color:${tokens.darkHeadingColor}!important}body.dark-aware .dark-code{background:${tokens.darkCodeBg}!important;border-color:rgba(255,255,255,.06)!important}body.dark-aware .dark-quote{background:${tokens.darkQuoteBg}!important}body.dark-aware .dark-hero{background:${tokens.darkCardBg}!important}body.dark-aware img{opacity:.9}}</style>`:''}
</head>
<body class="dark-aware" style="box-sizing:border-box; max-width:100%; margin:0; padding:0; background:${tokens.bodyBg}; overflow-x:hidden;">
  <div class="dark-card" style="${SAFE_WRAP} width:100%; background:${tokens.bodyBg}; padding:${ACTIVE_STYLE === "neo-futurism" ? "0 16px 48px" : "24px 12px"};">

    <article class="dark-text" style="${SAFE_WRAP} width:100%; max-width:760px; margin:0 auto; font-family:${tokens.fontFamily}; color:${tokens.text};">
      ${heroHtml}

      ${summaryHtml}
      ${mapHtml}
      ${renderBody(blocks)}
      ${closingPanelHtml()}
    </article>
  </div>
</body>
</html>
`;
}

// ── Main ──────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  if (args.includes("--list-styles")) {
    console.log(JSON.stringify({ styles: [...SUPPORTED_STYLES], defaultStyle: DEFAULT_STYLE }, null, 2));
    return;
  }

  let input = "";
  let output = "";
  let serve = false;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--style") {
      const style = args[index + 1];
      if (!style) {
        console.error("Missing value for --style");
        process.exit(1);
      }
      ACTIVE_STYLE = style;
      index += 1;
      continue;
    }
    if (arg?.startsWith("--style=")) {
      ACTIVE_STYLE = arg.slice("--style=".length);
      continue;
    }
    if (arg === "--serve") {
      serve = true;
      continue;
    }
    if (arg?.startsWith("--")) {
      console.error(`Unknown option: ${arg}`);
      process.exit(1);
    }
    if (!input) {
      input = arg || "";
    } else if (!output) {
      output = arg || "";
    } else {
      console.error(`Unexpected argument: ${arg}`);
      process.exit(1);
    }
  }

  if (!input) {
    console.error(`Usage: node scripts/render-wechat-article.mjs <article.md> [output.html] [--style ${[...SUPPORTED_STYLES].join("|")}] [--serve]`);
    console.error("List styles: node scripts/render-wechat-article.mjs --list-styles");
    process.exit(1);
  }

  if (!SUPPORTED_STYLES.has(ACTIVE_STYLE)) {
    console.error(`Unsupported style: ${ACTIVE_STYLE}`);
    console.error(`Supported styles: ${[...SUPPORTED_STYLES].join(", ")}`);
    process.exit(1);
  }

  const inputPath = path.resolve(input);
  const outputPath = output
    ? path.resolve(output)
    : path.join(path.dirname(inputPath), `${path.basename(inputPath, path.extname(inputPath))}.wechat-preview.html`);

  const markdown = fs.readFileSync(inputPath, "utf8");
  IMAGE_BASE_DIR = path.dirname(inputPath);
  const blocks = parseBlocks(markdown);
  const opening = takeOpening(blocks);
  const html = renderDocument(opening);
  fs.writeFileSync(outputPath, html, "utf8");

  const imageCount = opening.blocks.reduce((count, block) => (
    count + (block.type === "imageGroup" ? block.images.length : block.type === "image" ? 1 : 0)
  ), 0);
  console.log(JSON.stringify({ outputPath, title: opening.title, imageCount, style: ACTIVE_STYLE }, null, 2));

  if (serve) {
    const scriptDir = path.dirname(path.resolve(process.argv[1]));
    const serverScript = path.join(scriptDir, "preview-server.mjs");
    const serveDir = path.dirname(outputPath);
    console.log(`\nStarting preview at http://localhost:49255/`);
    console.log(`Serving: ${serveDir}`);
    console.log(`Press Ctrl+C to stop.\n`);
    const { spawn } = await import("node:child_process");
    const child = spawn("node", [serverScript, serveDir], { stdio: "inherit" });
    child.on("exit", () => process.exit(0));
  }
}

main();
