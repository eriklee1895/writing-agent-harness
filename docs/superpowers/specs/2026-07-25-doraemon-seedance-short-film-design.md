# Doraemon Seedance Short Film Design

## Context

The user provided a 12-panel storyboard for a lighthearted Doraemon fan short and asked for the complete production workflow: expand the story, plan the storyboard and shots, generate the shot artwork, turn the shots into video with Seedance, and edit the final film.

The approved direction is a roughly two-minute, vertical short. The original storyboard remains the narrative seed, but the finished film needs a stronger middle act so that the extra running time comes from escalation, character choices, and comic reversals rather than slower pacing.

## Approved Direction

- Working title: 《小道具，大冒险！》
- Format: 9:16 vertical video
- Target duration: 120 seconds, acceptable final range 115–125 seconds
- Visual style: polished 2D Japanese animation, bright colors, expressive faces, cinematic light, family-friendly comedy
- Language: Chinese
- Dialogue strategy: short dialogue and narration added in post; no long lip-sync passages
- Audio strategy: original whimsical score, designed sound effects, and consistent post-produced voices; do not reuse the franchise theme song
- Delivery: 1080 × 1920 MP4, H.264 video with AAC audio
- Publication: local deliverables only; no external publication is part of this task

## Story Premise

Nobita cannot begin an essay titled “The Adventure I Want Most” because he believes nothing adventurous ever happens to him. Doraemon brings out the “Imagination Realizer,” a can-shaped gadget that temporarily turns a thought into reality.

The first experiments are harmless and delightful: a tiny dinosaur, a floating castle, a miniature pirate ship, flowers, and bubbles. When the friends arrive, everyone imagines something different at the same time. The overloaded gadget combines their ideas into a ridiculous mechanical “imagination hound” that absorbs objects from the neighborhood and chases them.

The group escapes on a conjured pirate ship and rides a giant wave through the streets. Nobita finally understands the gadget’s reset rule: a single shared thought is stronger than five competing thoughts. Everyone imagines “going home together.” The chaos collapses back into the small can. That evening, Nobita finishes his essay with a new conclusion: the best adventure is not the strangest place, but the friends who face it with you.

## Narrative Structure

### Act I — No Adventure, Then Too Much Adventure

Nobita struggles with the essay, Doraemon introduces the gadget, and the first bedroom test succeeds. The act establishes the gadget’s red reset button and the rule that thoughts become real for a short time.

### Act II — Everyone Wants Something Different

The experiment moves outdoors. Shizuka, Suneo, and Gian join in. Their simultaneous wishes overload the gadget and create the mechanical imagination hound. The group first runs separately, then learns to cooperate.

### Act III — One Shared Thought

The friends board an imagined pirate ship, ride a giant wave, and finally defeat the chaos by agreeing on one simple wish. The sunset epilogue resolves Nobita’s essay and lands the friendship theme without a moralizing speech.

## Approaches Considered

### Reference-controlled atomic shots — selected

Generate a clean keyframe for every shot, animate it as an independent Seedance task, then assemble the selected takes in post. This provides the strongest control over character appearance, composition, pacing, and retries.

### Multi-beat 12–15 second Seedance scenes

Use fewer but longer generations containing several camera beats. This reduces the number of tasks but makes camera changes, character continuity, and selective retries less predictable.

### Motion-comic treatment

Animate still panels with parallax, pans, zooms, particles, and voice-over. This is economical and faithful to the supplied board, but it does not meet the desired sense of a fully animated short.

## Shot Plan

“Generation duration” is the Seedance source duration. “Edit duration” is the expected portion retained in the final cut. Every generated clip stays within Seedance’s 4–15 second range and includes trim handles for editing.

| ID | Story action | Framing and movement | Generation | Edit |
| --- | --- | --- | ---: | ---: |
| S01 | Nobita stares at the blank adventure essay and sighs | Medium shot, slow push-in across the desk | 8s | 7s |
| S02 | His pencil doodle becomes a pathetic squiggle; he declares that nothing exciting happens to him | Insert to close-up, small comic rack focus | 7s | 6s |
| S03 | Doraemon peeks through the door, listens, and enters | Medium doorway shot, gentle lateral slide | 8s | 7s |
| S04 | Doraemon searches the pocket and produces several wrong gadgets before finding the correct can | Medium two-shot with quick comic timing | 7s | 6s |
| S05 | The “Imagination Realizer” is revealed and its red reset button is explained | Hero close-up, orbit into an extreme insert | 8s | 7s |
| S06 | The button activates; a tiny dinosaur, castle, and pirate ship bloom across the bedroom | Wide shot, upward tilt and controlled orbit | 9s | 8s |
| S07 | Nobita imagines a giant dorayaki; it bounces around the room and nearly flattens Doraemon | Dynamic medium-wide, whip pan and reaction | 8s | 7s |
| S08 | They take the gadget outside and create harmless flowers, bubbles, and a toy-sized cloud | Neighborhood wide shot, forward tracking | 8s | 7s |
| S09 | Shizuka and Suneo discover the experiment and ask for a turn | Four-character medium grouping, restrained movement | 8s | 7s |
| S10 | Gian arrives and demands “something much bigger” | Low-angle entrance followed by Doraemon’s worried reaction | 8s | 7s |
| S11 | Several wishes appear at once; the can shakes, overheats, and spits out mismatched objects | Fast montage within one stable spatial setup | 9s | 8s |
| S12 | The fragments combine into a large, goofy mechanical imagination hound | Reveal from paws to face, rapid dolly out | 8s | 7s |
| S13 | The hound chases Nobita, Doraemon, and Gian while absorbing bins and umbrellas | Low tracking chase, strong foreground parallax | 8s | 7s |
| S14 | Shizuka and Suneo create a decoy while Doraemon searches for the missing reset button | Cross-cut action expressed as one lateral chase composition | 8s | 7s |
| S15 | Nobita imagines the pirate ship; the friends leap aboard as the hound closes in | Crane-up reveal, action matched to the jump | 8s | 7s |
| S16 | The ship surfs a giant blue wave through the neighborhood while the hound follows | Epic dynamic wide, rising camera and sweeping arc | 7s | 6s |
| S17 | The friends shout one shared thought—“一起回家！”—and the chaos contracts into the can | Group tableau, push toward the can, flash transition | 5s | 4s |
| S18 | At sunset, Nobita finishes the essay; he and Doraemon look over the neighborhood | Warm medium shot moving to a wide pullback | 6s | 5s |

The expected Seedance source total is 138 seconds. The planned edit total is 120 seconds.

## Dialogue Draft

Dialogue is intentionally short so that action remains readable in a vertical frame and voice continuity can be controlled in post.

| Shot | Dialogue or narration |
| --- | --- |
| S01 | Nobita: “我最想经历的冒险……” |
| S02 | Nobita: “可我哪有什么冒险啊。” |
| S03 | Doraemon: “你确定？” |
| S04 | Doraemon: “不是这个……也不是这个……” |
| S05 | Doraemon: “脑洞成真罐！想到什么，就会出现什么。” |
| S07 | Doraemon: “不要一下想那么大！” |
| S09 | Shizuka: “我们也可以试试吗？” |
| S10 | Gian: “要玩就来个大的！” |
| S11 | Doraemon: “别一起想——它会超载的！” |
| S13 | Nobita: “为什么我的冒险都在追我啊！” |
| S14 | Shizuka: “别只顾着跑，我们一起想办法！” |
| S15 | Nobita: “那就来一艘海盗船！” |
| S17 | Everyone: “一起回家！” |
| S18 | Narration: “后来我才知道，最好的冒险，不在多远的地方，而在谁陪你一起出发。” |

## Visual System

### Character consistency

- Create one clean character bible containing separate full-body references for Doraemon, Nobita, Shizuka, Suneo, and Gian.
- Create a separate prop sheet for the Imagination Realizer and its red reset button.
- Keep the canonical clothing, body proportions, and signature colors stable across all keyframes.
- Do not use a multi-view turnaround as a single Seedance reference because it can produce duplicate characters.
- High-motion group scenes use a composed first frame rather than asking Seedance to invent all five characters from text.

### Keyframe strategy

- Generate one 9:16 keyframe per shot at the intended opening composition.
- Use the user’s supplied storyboard as narrative and composition reference, not as a literal video first frame because it contains twelve panels and handwritten text.
- Remove captions, speech bubbles, watermarks, and panel borders from all Seedance input frames.
- Use a shared palette: sky blue, warm cream, soft green, red accent, and golden sunset.
- Keep important faces and props inside the central safe region, leaving the lower area available for post-produced subtitles.

### Seedance reference strategy

Seedance does not allow `first_frame` and `reference_image` roles in the same task. The production therefore uses two deliberate modes:

1. Most shots use the generated keyframe as `first_frame`. It already contains the required characters, environment, palette, and composition.
2. Shots that prove unstable in first-frame mode may switch to multimodal `reference_image` mode with a small set of references, but not both modes simultaneously.

Character-heavy shots are kept spatially simple. Shots with more than four visible characters begin from a carefully composed group keyframe and avoid complicated individual choreography in the same generation.

## Seedance Production Strategy

### Preview pass

Use the fast model at 720p for the three highest-risk scenes:

- S06: imagination effects in the bedroom
- S12: mechanical hound reveal
- S16: ship and giant wave

Generate two variants of each high-risk scene. Review character stability, action readability, and visual style before committing to the full render pass.

### Final pass

- Model: `doubao-seedance-2-0-260128` standard
- Resolution: 1080p
- Ratio: 9:16
- Audio generation: disabled; final audio is created in post
- Watermark: disabled
- Return last frame: enabled for continuity checks when useful
- Submission: atomic tasks, tracked by shot ID and manifest

Each prompt specifies one dominant action, one camera movement, the 2D animation style, the character invariants, and a concise negative constraint block. Successful shots are never regenerated merely because another shot failed.

## Audio Design

- Original score: playful woodwinds, pizzicato strings, toy percussion, and a faster adventure rhythm during the chase; no recognizable franchise melody
- Character voices: consistent Chinese voices created separately from the video generations
- Sound effects: pencil scratch, pocket rummaging, gadget beep, electrical overload, magical bloom, rubbery impact, mechanical bark, running steps, ship creak, wave crash, flash contraction, and evening ambience
- Mix shape: quiet opening, rising wonder, dense chase climax, brief silence before the reset, warm musical release
- Dialogue remains centered and intelligible; music ducks beneath speech
- Apply short fades at clip boundaries to avoid model-generated or edit-induced clicks

## Editing Design

- Assemble selected takes in narrative order with hard cuts for comedy and motion-matched cuts for action.
- Use flash cuts for gadget activation and reset, whip-pan cuts during the chase, and an audio bridge from S17 into the sunset epilogue.
- Trim generated handles to remove unstable first or final frames.
- Add subtitles in post rather than asking the video model to render Chinese text.
- Subtitle safe area: centered above the bottom interface region, maximum two lines, high-contrast white text with a restrained dark outline.
- Deliver both a subtitled master and a clean master.

## Project Layout

Production assets will live under:

```text
content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/
├── source/
│   └── supplied-storyboard.png
├── design/
│   ├── storyboard.md
│   ├── shot-list.json
│   └── dialogue.md
├── references/
│   ├── character-bible.png
│   └── prop-sheet.png
├── keyframes/
│   ├── S01.png
│   └── ...
├── seedance/
│   ├── previews/
│   └── finals/
├── audio/
│   ├── voices/
│   ├── music/
│   └── sfx/
├── edit/
│   ├── captions.srt
│   ├── edit-manifest.json
│   └── contact-sheet.jpg
├── final/
│   ├── doraemon-small-gadget-adventure-clean.mp4
│   ├── doraemon-small-gadget-adventure-subtitled.mp4
│   └── poster.jpg
├── manifest.json
└── notes.md
```

Large generated binary assets remain local unless the user explicitly asks to track them in Git. Text manifests, prompts, and design notes remain traceable.

## Failure Handling

- Character drift: regenerate only the affected shot with a cleaner keyframe and fewer simultaneous actions.
- Duplicate characters: simplify the composition, reduce reference count, and avoid multi-view sheets.
- Style drift toward live action or 3D: move “polished 2D Japanese animation” to the start of the prompt and strengthen the first-frame style.
- Broken anatomy or object penetration: shorten the action, separate it into two shots, or hide the transition behind a whip pan or foreground occlusion.
- Unreadable group action: split the group into two spatial layers or two adjacent shots.
- Failed API task: preserve the manifest error, correct the specific parameter or content problem, and resubmit only that shot.
- Poor audio continuity: keep Seedance audio disabled and rebuild the sound in post.

## Quality Checks

Before calling the film complete:

- Confirm every selected shot has the expected characters, clothing, prop state, and direction of movement.
- Inspect representative frames from every clip for duplicate characters, deformed hands, face drift, unwanted text, borders, logos, and watermarks.
- Verify the final master is 1080 × 1920, 9:16, H.264 with AAC audio.
- Verify duration is between 115 and 125 seconds.
- Verify the audio track exists, dialogue is intelligible, and peaks do not clip.
- Verify subtitle timing, line breaks, spelling, and safe-area placement.
- Inspect the opening frame, several action frames, the reset flash, and the final sunset frame visually.
- Create a contact sheet and preserve the final shot selection, prompts, task IDs, and edit manifest.

## Deliverables

- Expanded storyboard and shot list
- Character bible and prop sheet
- Eighteen keyframes
- Selected Seedance source clips and generation manifests
- Chinese dialogue recordings, original score, and sound effects
- Clean 1080 × 1920 master
- Subtitled 1080 × 1920 master
- Poster frame, contact sheet, captions, prompt files, and production manifest

## Cost And Review Boundary

Image generation, Seedance preview/final tasks, speech generation, and music generation may invoke paid APIs. Execution begins only after the user reviews this written design and explicitly approves proceeding with those production calls. No publishing or external distribution is authorized.
