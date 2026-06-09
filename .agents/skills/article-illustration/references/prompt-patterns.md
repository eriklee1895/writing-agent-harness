# Prompt Patterns

## Shared prompt template

Always build prompts in this order:

1. Subject and goal
2. Content type (cover / inset / divider / banner / diagram)
3. Layout structure
4. Style profile
5. Visual constraints
6. Output constraints

## Style-specific frames

The script auto-selects the prompt frame based on whether the chosen style has `is_artistic: True`. Do NOT manually override this — the script handles it correctly.

### Artistic styles (editorial-atmospheric, modern-guochao-editorial, cinematic-editorial, watercolor-illustration, flat-illustration, sketchnote)

Frame: "article or essay — not a technical document. Do NOT add any diagrams, arrows, labels, callouts, or text. Focus on a concrete visual idea with atmosphere, restraint, and editorial clarity." The script also injects content-type-specific guidance (cover safe zones, mobile readability, etc.) based on keyword detection.

### Technical styles (flat-tech-infographic, soft-tech-diagram, repo-architecture-clean)

Frame: "polished article illustration suitable for insertion into engineering notes or a design document. Prefer a clear information hierarchy with section titles, concise Chinese/English labels, short notes, arrows, grouped modules, and strong readability."

## Article illustration patterns

### Cover image (微信封面)

Focus on:
- 2.35:1 ultra-wide composition (cropped from 1792x1024)
- Key subjects centered or in lower portion
- Generous negative space for title overlay
- Readable at small thumbnail size in WeChat's subscription feed

### Body inset illustration

Focus on:
- Mobile-first composition (~390px reading width)
- Emotional resonance
- Generous negative space between text
- No text labels

### Atmospheric section divider

Focus on:
- Simple, horizontal composition
- Evocative but not distracting
- Visual breathing space

### Blog banner

Focus on:
- Desktop reading at ~1200px wide
- Upper area clear for overlaid title text

## Technical diagram patterns

### Architecture diagram

Focus on:
- system boundaries
- layered components
- data flow arrows
- integration labels

### Process diagram

Focus on:
- ordered steps
- directional arrows
- stage containers
- decision points

### Knowledge card

Focus on:
- one main title
- 3-6 compact concept blocks
- highlight chips
- supportive mini-icons

### Repo or module relationship diagram

Focus on:
- folder or service blocks
- responsibility labels
- dependency arrows
- clean spacing

## Text density rule

- Default to medium annotation density.
- Use title + section title + short labels + one-line notes.
- Avoid multi-sentence blocks unless the user explicitly asks for dense infographic output.
