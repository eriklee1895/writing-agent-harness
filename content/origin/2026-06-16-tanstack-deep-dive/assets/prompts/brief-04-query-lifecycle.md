# Brief 4: TanStack Query Lifecycle

A flat-tech infographic showing TanStack Query's 4-stage server-state lifecycle as a horizontal pipeline. English labels only.

Four stages connected by arrows on a clean off-white background:

1. "Fetch" - icon: a hand reaching for a glowing node; sub-label "query function"
2. "Share" - icon: three readers sharing a single cache; sub-label "cache key contract"
3. "Revalidate" - icon: a circular refresh with a clock; sub-label "stale-while-revalidate"
4. "Collect" - icon: a recycling bin with a soft timer; sub-label "garbage collection"

Each stage sits inside a rounded module with consistent padding. Arrows between stages are smooth and labeled with tiny tags like "observers" between Share and Revalidate. Above the pipeline floats a single horizontal line labeled "stale data stays useful" with a check mark, suggesting that the system never throws away data unless it has to.

Color: tanstack mint #32E6E2 primary accent, soft slate gray, off-white background, very subtle drop shadows. Rounded modules, consistent stroke weight.

Style: flat-tech-infographic, clean, document-friendly, generous whitespace.
