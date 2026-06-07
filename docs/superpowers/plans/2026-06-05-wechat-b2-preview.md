# WeChat B2 Preview Implementation Plan

> Historical note: this was the original implementation plan. The current renderer skill is `wechat-article-renderer`, the current default style preset is `impact-rational`, and the current script is `.agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a full `impact-rational` WeChat HTML preview from the selected Markdown article.

**Architecture:** Create a small Node.js renderer script that reads Markdown, parses common article blocks, and emits standalone WeChat-compatible HTML with inline styles. The script writes output next to the source Markdown so local image paths continue to work.

**Tech Stack:** Node.js ESM using only built-in modules.

---

### Task 1: Build WeChat Renderer

**Files:**
- Current canonical script: `/Users/eriklee/code/my_project/writing-agent/.agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs`

- [ ] **Step 1: Create a Markdown parser and WeChat HTML renderer**

Create a Node script that:

- Accepts a Markdown path as argv[2].
- Extracts the first H1 as the title.
- Extracts the opening quote as the deck.
- Extracts the `一句话总结` paragraph as the summary card.
- Converts headings, paragraphs, blockquotes, lists, tables, images, and horizontal rules.
- Groups content into blue-gray section cards after the opening.
- Writes `<basename>.wechat-preview.html` next to the source Markdown.

- [ ] **Step 2: Run the renderer**

Run:

```bash
node .agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs "微信公众号/0605-Cloudflare收购VoidZero/从Cloudflare收购Vite看AI军备竞赛趋势.md" --style impact-rational
```

Expected: prints the absolute output HTML path and image count.

### Task 2: Add Browser Review Screen

**Files:**
- Create: `/Users/eriklee/code/my_project/writing-agent/.superpowers/brainstorm/6270-1780635402/content/full-preview-004.html`

- [ ] **Step 1: Add a visual companion screen**

Create a browser screen that links to the generated HTML preview and summarizes the review checklist:

- Is the opening strong enough?
- Is the body readable for a long article?
- Are images and captions integrated?
- Does the ending feel like a recurring column?

### Task 3: Verify Output

**Files:**
- Read: generated `.wechat-preview.html`

- [ ] **Step 1: Check generated HTML**

Run:

```bash
test -f "微信公众号/0605-Cloudflare收购VoidZero/从Cloudflare收购Vite看AI军备竞赛趋势.wechat-preview.html"
rg -n "<style|<script|TODO|TBD" "微信公众号/0605-Cloudflare收购VoidZero/从Cloudflare收购Vite看AI军备竞赛趋势.wechat-preview.html" || true
```

Expected: file exists; no `<style>`, `<script>`, `TODO`, or `TBD`.
