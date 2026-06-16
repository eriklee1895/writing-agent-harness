# Brief 8: TanStack Ecosystem Dependency Graph

A flat-tech infographic showing the TanStack ecosystem as a directed dependency graph, NOT just a catalog. The 13+ libraries are placed in 5 layered swimlanes, with thin arrows showing which library depends on / is built on top of which. English labels only (consistent with the other ecosystem image).

Layout: 5 horizontal swimlanes stacked vertically on a soft off-white background. Each library is a rounded card with its name, version tag, and a tiny icon. Cards within the same lane are evenly spaced. Thin arrows (mint green for "built on" relationships, neutral gray for "integrates with") connect related cards across lanes.

Lane 1 (top, framework layer):
- Two cards: "Start RC" (mint accent) and "Router v1" (mint accent)
- Thick arrow from Start → Router: "Start is built on Router"
- Small sub-label on Router: "type-safe routes / search params / loaders"

Lane 2 (data and state management, mint accent for Query which is the core):
- "Query v5" - largest card in this lane, marked "core server-state"
- "DB beta" - smaller, with arrow Query → DB: "local-first sync on top of Query"
- "Store alpha" - independent, no arrows
- "AI beta" - independent card, small dashed arrow AI → Start and AI → Query: "uses both as base"

Lane 3 (UI and UX):
- "Table v9" - mint accent, with arrow Router → Table and Query → Table
- "Form new" - with arrows Router → Form and Query → Form
- "Hotkeys alpha" - independent

Lane 4 (performance):
- "Virtual v3" - with arrow Table → Virtual: "virtualizes Table rows"
- "Pacer beta" - with arrow Form → Pacer: "rate-limit Form submissions"

Lane 5 (tooling, bottom):
- "Devtools alpha" - spanning card, with arrows from Query, Router, Table, Form all pointing to it: "inspect everything"
- "Config alpha" - small, neutral
- "CLI alpha" - small, neutral, with arrow Start → CLI: "scaffold Start apps"
- "Intent alpha" - small, dashed arrow from CLI → Intent: "ships agent skills"

Right margin: a small legend explaining the arrow types:
- Solid mint arrow: "built on / extends"
- Dashed gray arrow: "integrates with / optional"

Bottom: a single horizontal banner with three stats: "11.3B+ downloads / 391M+ weekly / 124K+ stars" — same as the why-tanstack-wins image for visual consistency.

Color: tanstack mint #32E6E2 as the primary accent (heavier on Framework lane + Query + Router, lighter on bottom tooling lane), soft slate gray neutrals, off-white background, very subtle drop shadows. Rounded corners, consistent stroke weight.

Style: flat-tech-infographic, clean, professional, document-friendly, ample whitespace, no Chinese text.
