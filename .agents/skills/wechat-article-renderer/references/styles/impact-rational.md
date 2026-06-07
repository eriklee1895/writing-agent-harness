# Impact Rational Style

中文名：冲击开场，理性正文

## Intent

`impact-rational` is the current default house style for long-form AI infrastructure and developer-tooling commentary. It should feel more deliberate than a plain Markdown conversion, but calm enough for dense technical reading.

## Visual System

- Accent red: use for the hero border, small labels, diamond markers, and strongest thesis phrases.
- Blue-gray: use for headings, quote blocks, image frames, borders, and calm body emphasis.
- White cards: use as reading containers for hero, summary, map, and body sections.
- Dark closing panel: use for the recurring final CTA.

## Structure

1. Hero: red left border, `趋势观察` or similar label, H1, deck, thin red divider.
2. Summary: `一句话总结` label plus the core thesis.
3. Outline: `文章大纲` with up to six H2-derived entries. Keep the outline denser than body text, around `line-height:1.55` with modest row gaps. If H2 headings already start with numbers, render those numbers as separate badges instead of adding another ordered-list counter. Internal anchor links are allowed in local previews, but the outline must still read well if WeChat strips link attributes.
4. Body cards: one card per major H2 section.
5. Quote blocks: blue-gray background with left border.
6. Image blocks: use a single lightweight figure, full content width, rounded image, and small caption. Avoid nested image cards or double frames inside body cards. Consecutive evidence screenshots may be replaced by one compact collage image when screenshots are only supporting proof.
7. Closing CTA: dark panel with short follow-up promise.

## Mobile Safety

- Use inline styles only.
- Add `box-sizing:border-box` and `max-width:100%` to containers.
- Avoid fixed `min-width` on tables; use `table-layout:fixed` and break long tokens.
- Use `overflow-wrap:break-word` and `word-break:break-word` on headings, paragraphs, lists, code blocks, and table cells.
- Keep section padding conservative enough for 390-430px mobile widths.

## Tone

Use a serious analytical tone. The layout can be high-impact at the opening, but the body should feel rational, credible, and durable as a recurring column.
