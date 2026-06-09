# Style Profiles

## `auto` (default)

- Lets the script choose a style from the brief instead of forcing one house look
- Uses technical profiles for diagrams and engineering notes
- Uses editorial/artistic profiles for essays, cultural observations, and WeChat body illustrations
- Prefer this when the user has not explicitly named a visual style

## `editorial-atmospheric`

- Best for essays, cultural observation, and section-opening body illustrations
- Contemporary editorial illustration with layered composition and subtle texture
- Atmospheric but concrete: avoid vague pretty scenery
- No text, labels, diagrams, or arrows

## `modern-guochao-editorial`

- Best for Chinese culture, cities, historical motifs, cultural tourism, traditional festivals, and 国风/古风 subjects
- Modern editorial composition with restrained guochao influence
- Rich but not gaudy; avoid tourist-poster clichés and cheap costume-drama gloss
- No text, labels, diagrams, or arrows unless explicitly requested

## `cinematic-editorial`

- Best for stage scenes, city scenes, nightlife, live events, and emotionally grounded cultural essays
- Film-still inspired composition with natural lighting and concrete scene detail
- Should feel observed, not fantasy concept art
- No text, labels, diagrams, or arrows

## `flat-tech-infographic`

- Best for technical docs, AI notes, and repo architecture inserts
- Flat shapes, clean grouping, and icon-assisted modules
- Soft but professional colors
- Readable bilingual labels
- Balanced whitespace

## `flat-illustration`

- Best for concept explanation with lighter technical density
- More decorative than the default
- Still keep labels short and structured

## `sketchnote`

- Best for study notes, tutorial summaries, and prompt-engineering cards
- Hand-drawn accents, notebook feel, softer linework

## `soft-tech-diagram`

- Best for architecture, system boundaries, and knowledge graphs
- Gentle technical diagram feel
- Dashed containers and subtle node relationships

## `repo-architecture-clean`

- Best for codebase structure and ownership diagrams
- Minimal decoration
- Crisp block hierarchy
- Strong spacing and labeling discipline

## `watercolor-illustration`

- Best when the user explicitly wants a soft painterly mood
- Watercolor painting texture, soft brushstrokes
- Muted, atmospheric palette with generous negative space
- No diagrams, labels, arrows, or text — pure visual mood
- Do not treat it as the universal default for 散文/随笔/公众号配图

## Style selection rule

- If the user explicitly names a style profile, use it.
- If the user provides a reference image, use the reference image to adapt the selected profile.
- If the user does not specify a style, use `auto`.
- For literary/essay/WeChat illustrations, choose the style that fits the article's subject and voice; do not default blindly to watercolor.
- Artistic profiles (`editorial-atmospheric`, `modern-guochao-editorial`, `cinematic-editorial`, `watercolor-illustration`, `flat-illustration`, `sketchnote`) skip the technical infographic prompt framing and focus on a concrete visual idea with atmosphere and restraint.
