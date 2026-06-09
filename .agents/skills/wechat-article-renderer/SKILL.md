---
name: wechat-article-renderer
description: "Render Markdown into polished WeChat Official Account (微信公众号) HTML preview using this repo's style presets. Use when the user asks to 排版/美化/生成/预览微信公众号文章, wants a free md2wechat alternative, or needs a Markdown article converted into WeChat-ready inline HTML before 草稿箱/publish workflow."
---

# WeChat Article Renderer

## Overview

Use this skill to turn a Markdown article into a polished WeChat Official Account HTML preview.

Markdown remains the source of truth. Generate HTML for review first; publishing is a separate step handled by `wechat-publish-workflow`.

Current default style preset: `impact-rational`（中文名：冲击开场，理性正文），适合技术长文、AI infrastructure、developer tooling commentary。未来新增风格时，继续保留这个 skill 作为统一 renderer，通过 `--style <name>` 和 `references/styles/<name>.md` 扩展，不要为每个 style 新建一个 skill。

## Quick Start

Run the bundled renderer:

```bash
node {baseDir}/scripts/render-wechat-article.mjs /absolute/path/to/article.md
```

指定 style preset：

```bash
node {baseDir}/scripts/render-wechat-article.mjs /absolute/path/to/article.md --style impact-rational
```

The output defaults to:

```text
/same/folder/article-name.wechat-preview.html
```

To choose an explicit output path:

```bash
node {baseDir}/scripts/render-wechat-article.mjs /absolute/path/to/article.md /absolute/path/to/output.html
```

`{baseDir}` is the directory containing this `SKILL.md`.

## Workflow

1. Read the Markdown source and keep it unchanged unless the user explicitly asks for article edits.
2. Generate a WeChat HTML preview with `scripts/render-wechat-article.mjs`.
3. Open or refresh the preview in a browser, preferably with a mobile-width check around 390-430px.
4. Verify no horizontal overflow, cropped cards, missing images, raw Markdown syntax, TODO/TBD text, or unreadable long links/code.
5. Iterate on the renderer or Markdown only if the visual result needs improvement.
6. When the user approves, publish or sync using `baoyu-post-to-wechat` if requested.

## Style Presets

Use `references/styles/impact-rational.md` for the current default style decisions. Load only the selected style reference when style-specific visual decisions are needed.

Current style presets:

- `impact-rational`: 技术评论/观点文，默认。
- `literary-essay`: 个人散文/随笔。
- `cultural-essay`: 文化现象、城市、音乐、文旅观察类随笔。
- `tech-blog`: 通用技术博客。

Style extension convention:

- Add a new style guide at `references/styles/<style-name>.md`.
- Add a matching renderer branch or theme token set in `scripts/render-wechat-article.mjs`.
- Keep style names semantic, not brainstorm labels. Good examples: `impact-rational`, `compact-briefing`, `minimal-reference`.
- Keep WeChat platform constraints shared across all styles: inline styles, no external `href`, mobile-safe width, and local image `data-local-path`.

Shared renderer rules:

- Keep all layout styling inline; avoid external CSS and JavaScript.
- Do not output external link `href` attributes in WeChat HTML. Render links and references as readable text because the WeChat editor rejects non-`mp.weixin.qq.com` links when saving drafts.
- Do not inline image binaries as base64. WeChat preview HTML should stay lightweight and reviewable.
- Preserve local image references with `data-local-path`; paths may point to article `assets/`, `.local-archive/YYYY-MM-DD-slug/images/`, or another local archive hint.
- CDP publishing resolves `data-local-path` at draft creation time, uploads images to WeChat, and replaces `src` with WeChat CDN URLs.
- Make small-screen safety non-negotiable: `box-sizing:border-box`, width constraints, and long-token wrapping.
- Keep `一句话总结` and `文章大纲` available when the selected style supports long-form reading aids.

## Cover Images

When a WeChat article needs a new cover image, prefer the system `$imagegen` skill first. If the built-in image tool is unavailable and CLI fallback is needed, load credentials from the project `.env` without printing secret values. Do not recreate the removed duplicate project-local `gpt-image-gen` skill unless the user explicitly requests a project-specific fork.

## Publishing Boundary

This skill creates reviewable HTML. Do not assume the article is published.

For WeChat draft publishing, use `baoyu-post-to-wechat` after the user confirms the preview. If the user wants to paste manually, provide the generated HTML path and the preview URL/file path.

## Validation Checklist

Before saying the preview is ready, confirm:

- Renderer exits successfully and reports the expected title/image count.
- HTML file exists and contains no `<script>`, external stylesheet dependency, `TODO`, or `TBD`.
- HTML contains no external link `href`; reference items should show title/source as text.
- Mobile-width browser check has `documentElement.scrollWidth <= documentElement.clientWidth`.
- Hero, summary card, reader map, section headings, quotes, images, and closing CTA render cleanly.
- Source Markdown remains the canonical article.
