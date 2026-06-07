# WeChat B2 Style Design

> Historical note: this was the original brainstorm/spec. The production style preset is now named `impact-rational`（中文名：冲击开场，理性正文） under the `wechat-article-renderer` skill.

## Goal

Create a reusable WeChat Official Account article style for long-form AI infrastructure and developer-tooling commentary. The style should be more distinctive than a plain Markdown conversion, but still calm enough for long technical essays.

The selected direction was **B2: impact header + rational body**. It has since been renamed to `impact-rational`.

## Source Workflow

Markdown remains the source of truth. We do not hand-edit the article into HTML.

The workflow is:

1. Read the article Markdown and local image references.
2. Generate a WeChat-compatible HTML preview with inline styles.
3. Verify the visual result in a browser.
4. Iterate on style rules.
5. Later, package the stable rules into a project skill.

`md2wechat` paid API is not required. Its free AI-mode prompts may be used as inspiration only. `baoyu-post-to-wechat` remains the likely publishing path because it already handles Markdown-to-WeChat conversion and browser/API draft workflows.

## Visual Principles

The style should combine:

- **B-style opening impact**: red accent, strong label, clear title hierarchy, immediate “worth reading” signal.
- **A-style body credibility**: blue-gray palette, restrained cards, readable line height, professional analytical tone.
- **C-style long-term restraint**: enough whitespace and simplicity that the style can become a recognizable recurring column.

Avoid turning the whole article into a high-saturation red layout. Red is an accent, not the default reading environment.

## Article Components

### Opening Hero

Use a white panel with a strong red left border. Include:

- Small red label, such as `趋势观察` or `AI 军备竞赛`
- H1 title
- One-sentence deck/subtitle
- Thin red gradient divider

Purpose: create the click-and-read impulse.

### Summary Card

Use a compact white card with red label text and normal body text.

Purpose: give readers the thesis before the long argument begins.

### Reader Map

Use a card titled `读这篇文章，你会看到` with a short ordered list.

Purpose: lower the cognitive cost of a long article.

### Body Section

Use blue-gray cards with:

- Rounded corners
- Subtle border
- Soft shadow
- H2 title with red diamond marker and blue-gray heading text
- Paragraphs at around 16px, line-height around 1.9-2

Purpose: keep the body credible, calm, and readable.

### Quote / Judgment Blocks

Use blue-gray quote blocks for analytical statements. Use red sparingly for the strongest thesis or key phrase.

Purpose: make memorable claims scannable without making the article feel overdesigned.

### Image Blocks

Wrap images in a quiet blue-gray frame with optional caption text. Images should support the article, not dominate the layout.

Purpose: integrate screenshots, diagrams, and generated visuals into the reading flow.

### Judgment Cards

Use a small set of stacked cards for major conclusions, such as:

- 开发者的第一现场
- 本地与边缘的环境同构
- AI 软件生产线的默认编排权

Purpose: create shareable, memorable structure inside long analysis.

### Closing CTA

Use a dark closing panel with muted red label text.

Purpose: create a recognizable ending for the column and invite readers to follow future analysis.

## Constraints

- Output must be WeChat-compatible HTML with inline styles.
- Do not rely on external CSS files.
- Avoid JavaScript.
- Keep source Markdown unchanged unless the user explicitly requests a formatted copy.
- Use local images from the article directory when available.
- Avoid nested card-heavy clutter. Use cards as reading containers, not decorative noise.
- Preserve article meaning and section order unless explicitly editing the article.

## First Implementation Target

Generate a full HTML preview for:

`/Users/eriklee/code/my_project/writing-agent/微信公众号/0605-Cloudflare收购VoidZero/从Cloudflare收购Vite看AI军备竞赛趋势.md`

The first pass should cover the whole article, not only the first screen. It should include all inline images and a consistent ending CTA.

## Future Skill Shape

If the full preview works, create a project skill for this house style. The skill should:

- Accept a Markdown article path.
- Extract title, summary, headings, links, and images.
- Generate WeChat-compatible HTML using the B2 style.
- Optionally add a summary card, reader map, judgment cards, and closing CTA.
- Keep publishing separate: either hand off to `baoyu-post-to-wechat` or produce a standalone HTML file for manual review.
