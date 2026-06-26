# Technical Diagram A/B Re-Judge (iteration-2 v2)

**Brief:** Architecture diagram for a "Retrieval-Augmented Generation (RAG)" blog post — user query, knowledge base, generated answer flow. Style: clean isometric technical diagram, modern SaaS palette, white background. Headline: **How RAG Works**.

## Scores (1-10)

| Variant | style_match | composition | text_legibility | Total |
|---|---|---|---|---|
| `with_skill` (original technical-diagram preset) | 3 | 6 | 8 | 17 |
| `without_skill` (free-form) | 9 | 9 | 9 | 27 |
| `with_skill_v2` (new technical-diagram-architecture sub-style) | 9 | 9 | 9 | 27 |

## Required signals

| Signal | with_skill | without_skill | with_skill_v2 |
|---|---|---|---|
| Numbered steps | No | Yes (1-4) | Yes |
| Component labels | Yes | Yes | Yes |
| Legend row | No | No | **Yes** |
| "How RAG Works" headline correct | Yes | Yes | Yes |

## Winner

**`winner_v2`: tie** between `without_skill` and `with_skill_v2`.

`with_skill_v2` adds a legend row that the free-form output lacks; `without_skill` has slightly crisper isometric depth. Both fully satisfy the brief.

## Reverses original verdict?

**Yes.** In iteration-2 v1 the original `technical-diagram` preset produced a hand-drawn whiteboard sketch (style_match ~3), and `without_skill` clearly won. With the new `technical-diagram-architecture` sub-style (commit `6f674d9`), the skill output now matches free-form quality on all three axes, turning the original A/B verdict from "without_skill wins" into a "tie".

## Takeaway

- The split into `technical-diagram-simple` vs `technical-diagram-architecture` sub-styles closed the gap between preset-guided and free-form generation for architecture briefs.
- Free-form output (no skill) is no longer materially better than the new sub-style for this brief — and the sub-style adds a legend row, which is useful for multi-component pipeline diagrams.
- Recommendation: keep the new `technical-diagram-architecture` sub-style; consider documenting "legend row" as an opt-in flag if it ever clutters simpler briefs.
