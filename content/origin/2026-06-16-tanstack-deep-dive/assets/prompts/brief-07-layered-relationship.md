# Brief 7: TanStack vs Next.js Layered Relationship

A flat-tech infographic showing TanStack's position vs Next.js as a layered stack — TanStack libraries live in the base-capability layer that any framework can pick up. Bilingual labels (English primary, Chinese secondary), since the article is in Chinese.

Layout: three horizontal swimlanes stacked vertically on a soft off-white background.

Top lane (label "应用层 / Application Layer"):
- Two large rounded cards side by side
- Left card: "Data-driven SPA / 数据密集 SPA" with small icons (dashboard gauge, table, chart)
- Right card: "Content / SEO Site / 内容与 SEO 站" with small icons (newspaper, shopping cart)

Middle lane (label "应用框架层 / App Framework Layer"):
- Three medium rounded cards in a row, visually equal weight
- Card 1: "TanStack Start" with mint-green accent (the new choice)
- Card 2: "Next.js" with neutral gray dot
- Card 3: "Remix / React Router 7" with neutral gray dot

Bottom lane (label "基础能力层 / Base Capability Layer"):
- A single full-width card split into 4 sub-modules
- "TanStack Router" (typed routes)
- "TanStack Query" (server state lifecycle)
- "TanStack AI" (AG-UI / agents)
- "TanStack DB" (local-first sync)
- This whole lane has the strongest mint-green accent to signal "TanStack's home turf"

Arrows:
- From each top card, draw thin arrows down to whichever framework(s) it can sit on
  - Data-driven SPA → both TanStack Start AND Next.js
  - Content/SEO → only Next.js (visually thicker arrow)
- From each framework card, draw arrows down to the base layer modules it uses
  - TanStack Start uses Router + Query + DB (solid arrows, mint color)
  - Next.js optionally uses Query + AI (dashed arrows, neutral)
  - Remix uses Router (dashed)
- A special curved dashed arrow from the bottom lane back up to the top, labeled "composable, not monolithic / 可组合而非单体"

Right margin: a small note block with three short callouts:
- "TanStack libraries are framework-agnostic"
- "You can mix-and-match"
- "Start vs Next.js is a framework choice, not a base-library choice"

Color: tanstack mint #32E6E2 primary accent (strong on bottom lane and TanStack Start card), soft slate gray neutrals, off-white background, very subtle drop shadows, rounded corners, consistent stroke weight.

Style: flat-tech-infographic, clean, document-friendly, generous whitespace, bilingual labels.
