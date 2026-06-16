# Brief 3: TanStack + Agent Architecture

A flat-tech infographic diagram showing how a modern AI agent application is built on top of TanStack libraries. English labels only.

Layout: top-to-bottom data flow.

Top zone: "AI / LLM" - represented as a glowing brain icon in a rounded panel, with sub-labels "OpenAI", "Anthropic", "Ollama" as small chips.

Layer 2: "TanStack AI" - single rounded module, with sub-modules "AG-UI Protocol", "Tool Adapters", "Streaming Primitives". Arrow from LLM down to TanStack AI.

Layer 3: "Server Logic" - module labeled "TanStack Start createServerFn", "RPC endpoints", "Middleware". Arrow down.

Layer 4: "Data Layer" - two side-by-side modules: "TanStack Query (cache + lifecycle)" and "TanStack DB (local-first sync)". Arrow down.

Layer 5: "Client Routing" - module "TanStack Router" with sub-callouts "typed routes", "loader", "search params", "code splitting". Arrow down.

Layer 6 (bottom): "UI Runtime" - three small icons representing "React", "Vue", "Solid" as interchangeable panels.

A horizontal "TanStack Devtools" bar at the very bottom spanning the whole stack.

Right margin: a vertical dashed line connecting every layer labeled "observable boundary".

Color: tanstack mint #32E6E2 accent, soft slate gray neutrals, white background, subtle shadows, clean sans-serif feel through icon design.

Style: flat-tech-infographic, document-friendly, generous whitespace, no Chinese text in the image.
