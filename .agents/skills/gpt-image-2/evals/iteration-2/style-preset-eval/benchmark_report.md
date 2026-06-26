# Style Preset Skill Evaluation Benchmark Report

**Eval Date:** 2026-06-26
**Judge:** LLM-as-judge (Claude Opus 4.8)
**Models Evaluated:** gpt-image-2, seedream-image-gen (Doubao Seedream 5.0)
**Methodology:** A/B comparison of style-preset-augmented prompts (`with_skill`) vs. free-form prompts derived from general SKILL.md guidance (`without_skill`). Each image was scored on style match (1-10), composition/task fit (1-10), and text legibility (1-10 or null).

---

## Per-Style Results

| Model | Style | Winner | Style (w/s) | Style (w/o) | Comp (w/s) | Comp (w/o) | Text (w/s) | Text (w/o) |
|---|---|---|---|---|---|---|---|---|
| gpt-image-2 | editorial-pencil-sketch | **with_skill** | 9 | 7 | 9 | 8 | 8 | 7 |
| gpt-image-2 | editorial-essay | **with_skill** | 9 | 8 | 9 | 8 | — | — |
| gpt-image-2 | technical-diagram | **without_skill** | 6 | 8 | 6 | 9 | 9 | 9 |
| gpt-image-2 | education-science | **with_skill** | 9 | 7 | 9 | 7 | 9 | 8 |
| gpt-image-2 | visual-narrative | **with_skill** | 9 | 8 | 9 | 7 | — | — |
| seedream | editorial-pencil-sketch | **tie** | 8 | 8 | 7 | 7 | 6 | 5 |
| seedream | editorial-essay | **with_skill** | 9 | 7 | 9 | 7 | — | — |
| seedream | technical-diagram | **without_skill** | 5 | 6 | 5 | 7 | 7 | 8 |
| seedream | education-science | **without_skill** | 6 | 7 | 6 | 8 | 7 | 8 |
| seedream | visual-narrative | **with_skill** | 9 | 7 | 9 | 6 | — | — |

---

## Summary Stats

| Metric | Value |
|---|---|
| **Overall Winner** | with_skill |
| **Wins (with_skill)** | 6 |
| **Wins (without_skill)** | 3 |
| **Ties** | 1 |
| **Aggregate Score (with_skill)** | 241 |
| **Aggregate Score (without_skill)** | 230 |
| **Margin** | +11 (with_skill) |

---

## Detailed Rationales

### gpt-image-2 / editorial-pencil-sketch — with_skill wins
The with_skill image nails the pencil-sketch aesthetic with genuine graphite line work, watercolor washes, and a clean white background. It also includes a creative 5-step process flow at the bottom that adds editorial value. The without_skill version leans more toward a colored illustration with heavier pigment; the robot is more detailed/mechanical and the overall feel is less sketchbook-like.

### gpt-image-2 / editorial-essay — with_skill wins
Both images are excellent. The with_skill version has stronger layered composition with a human figure sitting on the boat, creating narrative depth. The without_skill version is beautiful but slightly more static and abstract. The with_skill palette (muted teal, warm amber) is more distinctive and magazine-like.

### gpt-image-2 / technical-diagram — without_skill wins (biggest surprise)
The without_skill image is a far superior technical diagram. It shows a complete 5-step RAG pipeline with numbered steps, labeled components, a Knowledge Base section with file icons, and a bottom legend row. The with_skill version is simplified to 4 generic icons with arrows, missing the actual architecture depth. Both render "How RAG Works" perfectly, but the without_skill composition satisfies the brief far better.

### gpt-image-2 / education-science — with_skill wins
The with_skill image is a textbook knowledge poster: navy background, clean white cards, large numbered circles, simple icons, and perfectly readable myth labels. The without_skill version uses a slightly different blue, has more cluttered card layouts with extra body text, and the icons are more detailed/photographic rather than simple line icons.

### gpt-image-2 / visual-narrative — with_skill wins
The with_skill storyboard uses true cinematic horizontal panels with clear camera progression (medium shot → wide shot → dynamic close-up → over-the-shoulder). The without_skill version uses vertical panel dividers which disrupt the cinematic flow, and the meteor shower panel shows the astronaut already fleeing rather than the shower appearing in the distance.

### seedream / editorial-pencil-sketch — tie
Both images are quite similar. The with_skill version has slightly more saturated color washes and a more complete scene. The without_skill version is more muted and monochrome, with somewhat garbled Chinese text. Both capture the hand-drawn aesthetic well.

### seedream / editorial-essay — with_skill wins
The with_skill image is a stunning editorial illustration with soft watercolor-like washes, warm golden light, and a dreamy atmosphere. The without_skill version is flatter, more vector-like, with less texture and depth. The with_skill version clearly benefits from the "contemporary editorial illustration" style anchor.

### seedream / technical-diagram — without_skill wins
Both Seedream technical diagrams are underwhelming. The with_skill version uses a 3-layer vertical stack that doesn't match the requested isometric style at all — it's a basic flowchart. The without_skill version at least shows a horizontal left-to-right flow with three distinct columns and a robot character, which is more engaging.

### seedream / education-science — without_skill wins
The without_skill version is a stronger knowledge poster. It uses a true navy background, has clear red X icons for each myth, includes explanatory subtext, and the layout is more balanced. The with_skill version uses a lighter blue background, inconsistent card shapes, and the content deviates from the brief (different myths than expected).

### seedream / visual-narrative — with_skill wins
The with_skill version is a proper 2x2 grid with clear panel separation, excellent character consistency (same white suit with blue patches), and dramatic cinematic lighting. The without_skill version has inconsistent panel sizing, the astronaut's suit changes between panels, and panel 2 shows only the meteor shower without the astronaut — breaking narrative continuity.

---

## Key Observations

1. **Style presets provide the biggest advantage for narrative and editorial styles.** Visual-narrative and editorial-essay both showed clear wins for with_skill across both models, suggesting that structured per-panel or metaphor-driven prompts benefit enormously from preset guidance.

2. **Technical diagrams are the weakest category for presets.** Both gpt-image-2 and seedream without_skill outperformed their with_skill counterparts. The preset's emphasis on "clean isometric" and "SaaS aesthetic" may oversimplify complex architecture diagrams, while free-form prompting allows the model to build richer, more informative diagrams.

3. **Seedream struggles with isometric technical styles.** Both Seedream technical-diagram outputs were basic flowcharts rather than true isometric architecture diagrams. The Chinese style preset's "扁平等距插图" formula doesn't translate well to actual isometric rendering in Seedream 5.0.

4. **Text legibility is strong across the board for both models, but gpt-image-2 consistently outperforms Seedream in English text rendering.** Seedream excels at Chinese text, which aligns with its training bias.

5. **The education-science style showed mixed results.** gpt-image-2 with_skill won decisively, but Seedream with_skill lost. This suggests the knowledge poster formula in the English preset transfers better to gpt-image-2's training, while the Chinese preset's "知识卡片" formula may need refinement for strict content adherence.

---

## Recommendations

### Keep and refine
- **editorial-pencil-sketch** — Consistently delivers superior results across both models. The graphite-line-dominant, sketchbook aesthetic is well-captured.
- **editorial-essay** — Strong wins on both models. The "contemporary editorial illustration" anchor and specific palette guidance produce magazine-quality output.
- **visual-narrative** — The per-panel shot description template is clearly effective. Both models produced cinematic storyboards with good character consistency.

### Revise
- **technical-diagram (both models)** — Reduce emphasis on "isometric" and "SaaS aesthetic" which can oversimplify. Add guidance for multi-layer diagrams with numbered steps, labeled components, and legend rows. Consider splitting into "simple diagram" and "detailed architecture" variants.
- **education-science (Seedream)** — The Chinese "知识卡片" preset needs content adherence guardrails. The with_skill version generated different myth content than the brief specified. Add explicit content-locking guidance.

### Add
- **data-visualization / chart-graph** — Neither current preset set covers this common need well. A dedicated style for bar charts, line graphs, and dashboards would fill a gap.
- **technical-diagram-advanced** — A variant that explicitly allows body text, explanatory subtext, and detailed component labels, since the without_skill versions that included more text were sometimes judged better.

### Seedream-specific
- The Chinese technical-diagram preset should either drop the isometric claim and embrace flat infographic, or add much stronger 3D/isometric keywords (等距3D, 立体模块, 透视图).
- Consider adding more explicit negative constraints to the pencil-sketch preset (避免厚涂上色, 避免照片写实) as Seedream tends to add more color than intended.

---

*Report generated by LLM-as-judge evaluator. All images were reviewed visually against their briefs and intended style definitions from the respective skill preset files.*
