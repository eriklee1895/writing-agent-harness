# Visual narrative illustration styles

For storyboards, comics, film concepts, thematic image series, and narrative-driven articles about video, animation, or storytelling.

This preset provides **scaffolding, not a mold**: it defaults to sequential panel layouts and cinematic framing, but the model should keep only the structural guardrails when the user's brief already carries a strong visual concept.

## Structural template (use unless the brief overrides)

| Guardrail | Default prompt vocabulary |
|---|---|
| Medium | `film storyboard`, `picture-book illustration`, `comic strip`, `cinematic concept art` |
| Background | `scene-appropriate background`, `consistent environment across panels` |
| Composition | `[N] panels`, `left-to-right sequence`, `consistent character`, `narrative progression`, `varied camera angles` |
| Hard avoids | `inconsistent character design`, `missing panels`, `extra panels`, `illegible tiny text`, `photorealism unless requested` |

## Inspirational defaults (override when the brief supplies style/mood/color)

| Sub-style | Default direction |
|---|---|
| Film storyboard | `deep space black`, `cold blue`, `warm amber interior highlights`, `cinematic lighting` |
| Picture-book | `soft whites`, `warm orange`, `gentle greens`, `pale blue`, `gentle storybook aesthetic` |
| Comic strip | `white background`, `soft colors`, `black ink outlines`, `expressive characters` |
| Cinematic concept | `cold blue`, `silver`, `deep black`, `faint warm tones`, `subtle lens flare` |

> **Override rule:** If the user describes a different palette, atmosphere, or rendering style, drop the inspirational defaults and keep only the structural template (panel count/sequence, consistency, hard avoids).

---

## 1. Film storyboard sequence

A sequence of film-style frames showing the same scene from different angles or moments. Useful for planning video content or illustrating a narrative arc in an article.

**Core formula:**
```
Film storyboard sequence, [N] panels, [scene progression], consistent character and environment, varied camera angles, cinematic lighting
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Film storyboard sequence in 4 panels. Panel 1: an astronaut repairs a spacecraft in orbit, medium shot, calm. Panel 2: a meteor shower appears in the distance, wide shot, tension rising. Panel 3: the astronaut dodges debris, dynamic close-up, motion blur. Panel 4: the astronaut reaches the airlock, over-the-shoulder shot, warm interior light. Consistent astronaut suit and spacecraft design across all panels, cinematic lighting" \
  --use-case illustration-story \
  --style "film storyboard, cinematic illustration, sequential narrative" \
  --composition "4 horizontal panels showing progression" \
  --palette "deep space black, cold blue, warm amber interior highlights" \
  --lighting "cinematic, shifting from cold exterior to warm interior" \
  --constraints "consistent character and spacecraft, no text, no speech bubbles" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/storyboard-astronaut.png
```

**Best for:** video planning, narrative articles, game concept pitches

---

## 2. Picture-book illustration

Warm, continuous story illustrations with consistent characters across scenes. Good for brand storytelling, children's content, and gentle narrative essays.

**Core formula:**
```
Picture-book illustration style, [N] scenes about [theme], consistent [character description], gentle narrative progression, warm palette
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Picture-book illustration style, 4 scenes about a small fox searching for spring. Scene 1: the fox wakes in a snowy forest. Scene 2: the fox walks through bare trees and sees the first flower. Scene 3: the fox meets a rabbit by a stream. Scene 4: the fox and rabbit sit on a hill watching a valley of blossoms. Consistent small orange fox and gray rabbit, warm gentle palette, no text" \
  --use-case illustration-story \
  --style "picture-book illustration, gentle storybook aesthetic, warm colors" \
  --composition "4 horizontal scenes showing narrative progression" \
  --palette "soft whites, warm orange, gentle greens, pale blue" \
  --lighting "soft natural light, shifting from winter to spring" \
  --constraints "consistent characters, no text, gentle mood" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/picture-book-fox.png
```

**Best for:** brand storytelling, children's content, narrative essays

---

## 3. Comic strip layout

A short comic with panels, characters, and speech bubbles. Good for light tutorials, humor pieces, and social content.

**Core formula:**
```
Comic strip style, [N]-panel layout about [topic], clear character consistency, expressive poses, English speech bubbles
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Comic strip style, 4-panel layout about a programmer debugging. Panel 1: confident smile with speech bubble 'Everything works'. Panel 2: confused look, 'Wait, this error?'. Panel 3: despair, 'No answers online'. Panel 4: relieved, 'Missing semicolon'. Consistent young programmer character, expressive poses, clean comic art style, white background, English speech bubbles" \
  --use-case illustration-story \
  --style "comic strip, clean comic art, expressive characters" \
  --composition "4-panel grid, left-to-right reading order" \
  --palette "white background, soft colors, black ink outlines" \
  --text "Everything works, Wait this error, No answers online, Missing semicolon" \
  --constraints "consistent character, readable speech bubbles, no extra panels" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/debug-comic.png
```

**Best for:** tutorials with humor, social media comics, team inside jokes

---

## 4. Cinematic concept frame

A single ultra-wide frame with strong atmosphere. Good for hero images in articles about film, games, or visual storytelling.

**Core formula:**
```
Cinematic concept art, [scene], [lens/framing description], [lighting/mood], ultra-wide composition
```

**Example (full preset):**
```bash
uv run scripts/gpt_image_2.py generate \
  --prompt "Cinematic concept art, a lone astronaut standing on the edge of a crater on a distant moon, Earth rising on the horizon, ultra-wide composition, cold blue and silver palette, subtle lens flare, epic but quiet mood, no text" \
  --use-case illustration-story \
  --style "cinematic concept art, film atmosphere, ultra-wide" \
  --composition "ultra-wide, astronaut small in lower third, Earth large on horizon" \
  --palette "cold blue, silver, deep black, faint warm Earth tones" \
  --lighting "rim light from Earth, dark shadows, subtle lens flare" \
  --constraints "no text, no logos, cinematic only" \
  --size wide \
  --quality high \
  --out output/gpt-image-2/cinematic-moon.png
```

**Best for:** hero images, film/game articles, atmospheric storytelling

---

## General tips

1. **Consistency is the hardest part.** For multi-panel sequences, repeat key character traits in every prompt (clothing, color, size, accessories).
2. **Plan the camera progression.** Wide → medium → close-up creates rhythm. All wide or all close-up feels flat.
3. **Use `--quality high` for multi-panel images.** Small panels need the extra resolution.
4. **Avoid dense dialogue.** gpt-image-2 can render text, but comic speech bubbles work best with 3–6 words.
5. **For true sequential generation,** consider using Seedream's `--sequential --max-images` or gpt-image-2 batch mode with tightly controlled prompts.
6. **When the user's brief already specifies a palette, atmosphere, or rendering style, drop the inspirational defaults and keep only the structural guardrails.**
