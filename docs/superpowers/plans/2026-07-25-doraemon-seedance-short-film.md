# Doraemon Seedance Short Film Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an approximately two-minute, 9:16 Doraemon fan short from eighteen image-controlled Seedance shots and assemble reproducible clean and subtitled masters in Remotion.

**Architecture:** A local production package stores the supplied storyboard, structured shot data, generated keyframes, Seedance prompts/tasks, selected clips, and final outputs. Each shot is generated independently with a 9:16 first frame and Seedance-native Chinese dialogue, music, ambience, and effects. A small Remotion project consumes a deterministic edit manifest, trims and sequences the selected clips, smooths audio boundaries, renders captions from `Caption[]` JSON, and exports both masters.

**Tech Stack:** System `imagegen`; `uv`; project `seedance-video-gen`; Seedance 2.0 standard/fast; Remotion with React/TypeScript, `@remotion/media`, `@remotion/captions`, and Node’s test runner through `tsx`; FFmpeg/FFprobe through the Remotion CLI.

## Global Constraints

- Output duration is 120 seconds, with an acceptable final range of 115–125 seconds.
- Output format is 1080 × 1920, 9:16, 30 fps, H.264 video with AAC audio.
- Use polished 2D Japanese animation, bright colors, expressive faces, cinematic light, and family-friendly comedy.
- Generate all final dialogue, original music, ambience, and effects natively in Seedance; do not use the franchise theme song.
- Use Remotion for the final edit; HyperFrames is not part of this implementation.
- Keep all readable content at least 80 px from the sides and 100 px from the top and bottom of the 1080 × 1920 frame.
- Add Chinese subtitles in Remotion, not in the generated frames or Seedance video.
- Never combine Seedance `first_frame` and `reference_image` roles in one request.
- Each Seedance task duration must be between 4 and 15 seconds.
- Final Seedance renders use `doubao-seedance-2-0-260128`, 1080p, 9:16, native audio enabled, and watermark disabled.
- Public distribution is outside scope.
- Preserve existing user changes and never print API keys or `.env` contents.
- Generated media and the production package remain local under ignored `content/inbox/`; only durable design and plan documents are committed.

---

## File Map

### Durable project documentation

- `docs/superpowers/specs/2026-07-25-doraemon-seedance-short-film-design.md` — approved creative and technical design.
- `docs/superpowers/plans/2026-07-25-doraemon-seedance-short-film.md` — this execution plan.

### Local production package

- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/source/supplied-storyboard.png` — immutable copy of the user’s input.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/storyboard.md` — expanded three-act story and shot descriptions.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/shot-list.json` — canonical eighteen-shot data.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/dialogue.md` — approved dialogue, voice notes, and music identity.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/references/character-bible.png` — character visual anchor.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/references/prop-sheet.png` — gadget visual anchor.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S01.png` through `S18.png` — Seedance first frames.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/prompts/S01.md` through `S18.md` — final prompts.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/preview-shots.json` — six fast-model high-risk variants.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/final-shots.json` — eighteen final standard-model jobs.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/previews/` — preview task manifests and clips.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/finals/` — final task manifests and clips.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/edit/edit-manifest.json` — selected takes, trims, gain, fades, and timing.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/edit/captions.json` — Chinese `Caption[]`.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/edit/remotion/` — editable Remotion source.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/` — clean master, subtitled master, poster, and contact sheet.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/manifest.json` — production provenance and deliverable paths.
- `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/notes.md` — human-readable completion notes.

---

### Task 1: Build the canonical local production package

**Files:**
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/source/supplied-storyboard.png`
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/storyboard.md`
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/dialogue.md`
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/shot-list.json`
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/manifest.json`
- Create: `content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/notes.md`

**Interfaces:**
- Consumes: the approved design spec and `/var/folders/bd/stx12mg16dd8hsrj72kswfl40000gn/T/codex-clipboard-e75d9f26-6d81-4e96-b0c6-595192a6f0ad.png`.
- Produces: `shot-list.json` with `{id, storyAction, generationSeconds, editSeconds, promptFile, keyframeFile, dialogue, musicPhase}` for S01–S18.

- [ ] **Step 1: Create the production directory tree**

Run:

```bash
mkdir -p content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/{source,design,references,keyframes,seedance/prompts,seedance/previews,seedance/finals,edit,final}
```

Expected: all directories exist and no existing file is replaced.

- [ ] **Step 2: Preserve the supplied storyboard**

Run:

```bash
cp /var/folders/bd/stx12mg16dd8hsrj72kswfl40000gn/T/codex-clipboard-e75d9f26-6d81-4e96-b0c6-595192a6f0ad.png content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/source/supplied-storyboard.png
```

Expected: `file` identifies the destination as a PNG and its checksum is recorded in `manifest.json`.

- [ ] **Step 3: Write the expanded story and dialogue**

Copy the three-act premise, S01–S18 shot descriptions, dialogue table, shared music identity, and voice descriptors from the approved spec into `storyboard.md` and `dialogue.md`. Use these repeating voice descriptions:

```text
大雄：少年男声，偏软、略慌张、语速自然
哆啦A梦：明亮温暖的卡通声线，语气可靠又带一点无奈
静香：清晰温柔的少女声线，遇事冷静
小夫：略尖、反应快、带一点夸张
胖虎：洪亮的少年男声，直接但不凶狠
```

Use this repeating music identity:

```text
原创轻快卡通冒险配乐，木管、拨弦、玩具打击乐；追逐段节奏加快，结尾转为温暖柔和；不得出现任何可识别的现有动画主题旋律。
```

- [ ] **Step 4: Write `shot-list.json`**

Use the exact generation/edit durations:

```json
[
  {"id":"S01","generationSeconds":8,"editSeconds":7},
  {"id":"S02","generationSeconds":7,"editSeconds":6},
  {"id":"S03","generationSeconds":8,"editSeconds":7},
  {"id":"S04","generationSeconds":7,"editSeconds":6},
  {"id":"S05","generationSeconds":8,"editSeconds":7},
  {"id":"S06","generationSeconds":9,"editSeconds":8},
  {"id":"S07","generationSeconds":8,"editSeconds":7},
  {"id":"S08","generationSeconds":8,"editSeconds":7},
  {"id":"S09","generationSeconds":8,"editSeconds":7},
  {"id":"S10","generationSeconds":8,"editSeconds":7},
  {"id":"S11","generationSeconds":9,"editSeconds":8},
  {"id":"S12","generationSeconds":8,"editSeconds":7},
  {"id":"S13","generationSeconds":8,"editSeconds":7},
  {"id":"S14","generationSeconds":8,"editSeconds":7},
  {"id":"S15","generationSeconds":8,"editSeconds":7},
  {"id":"S16","generationSeconds":7,"editSeconds":6},
  {"id":"S17","generationSeconds":5,"editSeconds":4},
  {"id":"S18","generationSeconds":6,"editSeconds":5}
]
```

Augment every object with its exact story action, framing, dialogue, prompt path, keyframe path, and `musicPhase` value of `opening`, `wonder`, `chase`, `reset`, or `ending`.

- [ ] **Step 5: Validate the package**

Run:

```bash
node -e "const s=require('./content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/design/shot-list.json'); const g=s.reduce((n,x)=>n+x.generationSeconds,0); const e=s.reduce((n,x)=>n+x.editSeconds,0); if(s.length!==18||g!==138||e!==120) process.exit(1); console.log({shots:s.length,generationSeconds:g,editSeconds:e})"
```

Expected:

```text
{ shots: 18, generationSeconds: 138, editSeconds: 120 }
```

- [ ] **Step 6: Record the local checkpoint**

Update `manifest.json` with the input checksum, design spec commit `638bf83`, package creation timestamp, `status: "design-ready"`, and the six expected deliverable paths. Do not force-add ignored `content/inbox/` files to Git.

---

### Task 2: Generate the visual bible and eighteen keyframes

**Files:**
- Create: `references/character-bible.png`
- Create: `references/prop-sheet.png`
- Create: `keyframes/S01.png` through `keyframes/S18.png`
- Create: `seedance/prompts/S01.md` through `seedance/prompts/S18.md`

**Interfaces:**
- Consumes: `shot-list.json`, the supplied storyboard, and the system `imagegen` skill.
- Produces: twenty 9:16-compatible visual assets and eighteen Seedance prompt files.

- [ ] **Step 1: Generate the character bible**

Use the system image generator in `illustration-story` mode. The supplied storyboard is a narrative/style reference. Generate a clean, text-free reference sheet with Doraemon, Nobita, Shizuka, Suneo, and Gian separated by generous whitespace, canonical clothing and proportions, polished 2D Japanese animation, sky-blue/warm-cream palette, no panel borders, no captions, no logos, and no watermark.

Save the selected output as `references/character-bible.png`.

- [ ] **Step 2: Generate the prop sheet**

Generate the can-shaped “脑洞成真罐” on a clean warm-cream background: cylindrical silver-blue body, circular front lens, short antenna, large red reset button on top, readable from medium and close range, no text, no logo, no watermark.

Save as `references/prop-sheet.png`.

- [ ] **Step 3: Generate S01–S18 keyframes individually**

For each shot, issue one built-in image-generation call using the character bible and prop sheet as local references. Normalize every prompt with:

```text
Use case: illustration-story
Asset type: 9:16 Seedance first frame
Style: polished 2D Japanese animation, bright family-friendly comedy, clean line art, cinematic light
Composition: 1080x1920-safe vertical staging; primary faces and gadget inside the central safe area
Continuity: preserve canonical clothing, body proportions, signature colors, and the exact gadget design
Constraints: one readable story beat; no captions, no speech bubbles, no panel border, no text, no logo, no watermark
Avoid: photorealism, 3D render, duplicate characters, extra limbs, cropped faces, distorted hands
```

Add the exact shot action and framing from `shot-list.json`. Save outputs as `keyframes/S01.png` through `keyframes/S18.png`.

- [ ] **Step 4: Visually validate every keyframe**

Inspect the twenty outputs and reject any frame containing duplicate characters, wrong clothing, deformed faces/hands, unreadable gadget state, unwanted text, or unsafe vertical cropping. Regenerate only the failed asset with one targeted correction.

- [ ] **Step 5: Validate file count and dimensions**

Run:

```bash
find content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes -name 'S??.png' | wc -l
```

Expected: `18`.

Run `sips -g pixelWidth -g pixelHeight` for every image and confirm `pixelHeight > pixelWidth` and `pixelHeight >= 1024`. Expected: zero failures.

- [ ] **Step 6: Write the final per-shot Seedance prompts**

Each `seedance/prompts/Sxx.md` must follow:

```text
2D日系动画风格。以图片1为首帧并保持人物、服装、道具和场景风格稳定。
[主体与单一主动作]
[运镜与构图]
（原创轻快卡通冒险配乐……）
<与动作同步的环境声或拟音>
[角色声线]说{短对白}
竖屏构图，主体位于安全区域；无字幕，无Logo，无水印，无闪烁；人物面部稳定，身体比例稳定，无同款分身，无穿模。
```

Keep the visual/control portion concise and place the exact Chinese dialogue in `{}`.

- [ ] **Step 7: Update provenance**

Add each asset path, final image prompt, input reference paths, generation mode `built-in imagegen`, and review status to `manifest.json`.

---

### Task 3: Run high-risk Seedance preview generations

**Files:**
- Create: `seedance/preview-shots.json`
- Create: `seedance/previews/batch-submit-*/batch_manifest.json`
- Create: six preview MP4 files for two variants each of S06, S12, and S16

**Interfaces:**
- Consumes: S06, S12, and S16 keyframes and prompts.
- Produces: approved prompt/camera variants for the standard final pass.

- [ ] **Step 1: Verify the Seedance credential without printing it**

Run:

```bash
rg -q '^ARK_API_KEY=' .env
```

Expected: exit code `0`. If it fails, stop before any paid call and report that `ARK_API_KEY` is unavailable.

- [ ] **Step 2: Build `preview-shots.json`**

Create six objects:

```json
[
  {
    "shotId":"S06-A",
    "prompt":"2D日系动画风格。以图片1为首帧并保持哆啦A梦、大雄、服装、房间和脑洞成真罐稳定。红色按钮发光，迷你恐龙、漂浮城堡和小海盗船从蓝色魔法光中依次出现，镜头缓慢上仰并小幅环绕，表演惊喜而非恐惧。（原创轻快卡通冒险配乐，木管、拨弦和玩具打击乐，不得出现任何现有动画旋律）<清脆按钮声、魔法粒子展开声、大雄惊叹> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，面部和身体比例稳定，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S06.png",
    "duration":9,"ratio":"9:16","generate_audio":true,"watermark":false
  },
  {
    "shotId":"S06-B",
    "prompt":"2D日系动画风格。以图片1为首帧并保持哆啦A梦、大雄、服装、房间和脑洞成真罐稳定。镜头先贴近发光红按钮，随后快速拉远揭示迷你恐龙、漂浮城堡和小海盗船充满卧室，大雄兴奋后退一步，哆啦A梦抬手提醒。（原创轻快卡通冒险配乐，木管、拨弦和玩具打击乐，不得出现任何现有动画旋律）<按钮哔声、魔法绽放声、轻快惊叹> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，面部和身体比例稳定，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S06.png",
    "duration":9,"ratio":"9:16","generate_audio":true,"watermark":false
  },
  {
    "shotId":"S12-A",
    "prompt":"2D日系动画风格。以图片1为首帧并保持人物、街道、脑洞成真罐和所有道具稳定。散落的恐龙尾巴、海盗船木片、玩具齿轮和雨伞被蓝色能量吸到一起，组合成巨大但滑稽的机械脑洞犬；镜头从机械爪向上揭示脸部，再快速后拉表现体型。（原创卡通冒险配乐开始加速，不得出现任何现有动画旋律）<金属咔哒声、电流声、滑稽机械狗叫> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S12.png",
    "duration":8,"ratio":"9:16","generate_audio":true,"watermark":false
  },
  {
    "shotId":"S12-B",
    "prompt":"2D日系动画风格。以图片1为首帧并保持人物、街道、脑洞成真罐和所有道具稳定。蓝色能量旋涡把恐龙、海盗船、齿轮和雨伞的碎片吸入中心，机械脑洞犬从烟雾中弹出并摇晃天线耳朵，先可爱停顿半秒再突然大叫；镜头绕半圈后迅速拉远。（原创卡通冒险配乐开始加速，不得出现任何现有动画旋律）<旋涡声、弹簧声、机械狗叫> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S12.png",
    "duration":8,"ratio":"9:16","generate_audio":true,"watermark":false
  },
  {
    "shotId":"S16-A",
    "prompt":"2D日系动画风格。以图片1为首帧并保持五位朋友、海盗船、机械脑洞犬和街区稳定。海盗船沿巨大的蓝色浪头冲过街道，朋友们抓紧船舷又兴奋欢呼，机械脑洞犬在浪后追赶；镜头从船侧低位跟拍，随后升高形成壮阔弧线。（原创快节奏卡通冒险配乐，木管、拨弦和玩具打击乐，不得出现任何现有动画旋律）<海浪、船体吱呀、欢呼、远处机械狗叫> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，五人身份独立，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S16.png",
    "duration":7,"ratio":"9:16","generate_audio":true,"watermark":false
  },
  {
    "shotId":"S16-B",
    "prompt":"2D日系动画风格。以图片1为首帧并保持五位朋友、海盗船、机械脑洞犬和街区稳定。镜头位于船头略低位置随海盗船攀上蓝色巨浪，越过浪顶时短暂失重，再俯冲向街道；机械脑洞犬在后方被浪花拍中，动作夸张有趣。（原创快节奏卡通冒险配乐，木管、拨弦和玩具打击乐，不得出现任何现有动画旋律）<海浪轰鸣、木船吱呀、短促欢呼、滑稽撞水声> 竖屏安全构图，无字幕，无Logo，无水印，无闪烁，五人身份独立，无同款分身，无穿模。",
    "first_frame":"/Users/eriklee/code/my_project/writing-agent-harness/content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S16.png",
    "duration":7,"ratio":"9:16","generate_audio":true,"watermark":false
  }
]
```

The installed batch script requires inline `prompt` text and accepts the absolute local `first_frame` paths shown above.

- [ ] **Step 3: Dry-run the preview batch**

Run one S06 task with the top-level `--dry-run` because `batch-submit` has no dry-run flag:

```bash
uv run .agents/skills/seedance-video-gen/scripts/generate_seedance_video.py \
  --prompt-file content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/prompts/S06.md \
  --first-frame content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/keyframes/S06.png \
  --model doubao-seedance-2-0-fast-260128 \
  --duration 9 --ratio 9:16 --resolution 720p \
  --generate-audio --no-watermark --dry-run
```

Verify:

- model is `doubao-seedance-2-0-fast-260128`
- resolution is `720p`
- ratio is `9:16`
- audio is enabled
- each task has exactly one `first_frame` and zero `reference_image` entries

- [ ] **Step 4: Submit and wait for previews**

Run:

```bash
uv run .agents/skills/seedance-video-gen/scripts/generate_seedance_video.py batch-submit \
  --shots-file content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/preview-shots.json \
  --model doubao-seedance-2-0-fast-260128 \
  --resolution 720p \
  --ratio 9:16 \
  --generate-audio \
  --no-watermark \
  --wait \
  --output-dir content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/previews
```

Expected: six succeeded tasks and six downloaded MP4 files.

- [ ] **Step 5: Grade the three high-risk scenes**

For each variant inspect opening, midpoint, and closing frames and listen to its audio. Score:

- character/style stability
- one readable action
- camera motion
- lack of duplicate characters or anatomy defects
- dialogue intelligibility
- music/effect fit
- clean final half-second

Select A or B for S06, S12, and S16. Carry only the winning prompt changes into the final prompt files.

- [ ] **Step 6: Record the preview checkpoint**

Add task IDs, output paths, scores, selected variants, and any rejected reasons to `manifest.json`. Do not delete rejected previews until the final master passes QA.

---

### Task 4: Generate the eighteen final Seedance clips

**Files:**
- Create: `seedance/final-shots.json`
- Create: `seedance/finals/batch-submit-*/batch_manifest.json`
- Create: eighteen 1080p final MP4 source clips

**Interfaces:**
- Consumes: S01–S18 final prompts and keyframes.
- Produces: one primary standard-model take per shot with native audio.

- [ ] **Step 1: Build `final-shots.json`**

Create eighteen objects. Each object contains absolute `first_frame`, inline `prompt`, the exact generation duration from Task 1, `ratio: "9:16"`, `resolution: "1080p"`, `generate_audio: true`, `watermark: false`, and `return_last_frame: true`.

- [ ] **Step 2: Dry-run S01 and S17**

Run both a normal-length task and the minimum narrative task through `--dry-run`. Confirm the payload uses standard model, valid 4–15 second durations, first-frame mode, native audio, and no watermark.

- [ ] **Step 3: Submit the final batch**

Run:

```bash
uv run .agents/skills/seedance-video-gen/scripts/generate_seedance_video.py batch-submit \
  --shots-file content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/final-shots.json \
  --model doubao-seedance-2-0-260128 \
  --resolution 1080p \
  --ratio 9:16 \
  --generate-audio \
  --no-watermark \
  --return-last-frame \
  --wait \
  --output-dir content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/finals
```

Expected: eighteen succeeded tasks. A failed task does not invalidate successful tasks.

- [ ] **Step 4: Retry only failed or unusable shots**

For each failure, read the specific manifest error and change only the offending parameter or prompt dimension. For visual/audio quality failures, revise one variable at a time and use fast 720p before re-running the standard 1080p final.

- [ ] **Step 5: Verify media properties**

For every selected final clip run:

```bash
find content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/seedance/finals \
  -name 'shot-*.mp4' -print0 |
  while IFS= read -r -d '' clip_path; do
    npx remotion ffprobe -v error \
      -show_entries stream=codec_type,codec_name,width,height \
      -show_entries format=duration -of json "$clip_path"
  done
```

Expected: portrait video, approximately the requested duration, and both video and audio streams. Record the result beside each task in `manifest.json`.

---

### Task 5: Select trims and create the deterministic edit manifest

**Files:**
- Create: `edit/edit-manifest.json`
- Create: `edit/captions.json`
- Create: `edit/selection-notes.md`

**Interfaces:**
- Consumes: eighteen verified final clips.
- Produces: a 3,600-frame edit description and valid `Caption[]`.

- [ ] **Step 1: Inspect every clip**

Extract opening, 25%, midpoint, 75%, and closing frames for every clip. Listen for dialogue placement, abrupt music starts, clicks, and noisy endings. Record a `trimBeforeFrames` value, selected `durationInFrames`, `gain`, `fadeInFrames`, and `fadeOutFrames` for each shot.

- [ ] **Step 2: Write `edit-manifest.json`**

Use:

```json
{
  "fps": 30,
  "width": 1080,
  "height": 1920,
  "shots": [
    {
      "id": "S01",
      "src": "clips/S01.mp4",
      "trimBeforeFrames": 0,
      "durationInFrames": 210,
      "gain": 1,
      "fadeInFrames": 4,
      "fadeOutFrames": 6
    }
  ]
}
```

Repeat through S18. The sum of `durationInFrames` must equal 3,600. Use the approved edit durations multiplied by 30 unless inspection requires a rebalance; any rebalance must preserve the 3,450–3,750 frame acceptance range.

- [ ] **Step 3: Write the initial `Caption[]`**

Create `captions.json` with objects:

```json
{"text":"我最想经历的冒险……","startMs":1200,"endMs":4300,"timestampMs":1200,"confidence":1}
```

Add all fourteen approved lines. Align their final `startMs` and `endMs` to the audible dialogue in selected clips rather than relying only on the draft timestamps.

- [ ] **Step 4: Validate edit data**

Check:

- exactly eighteen unique shot IDs
- every source file exists
- every duration is positive
- every trim plus duration fits inside the source clip
- total duration is 3,450–3,750 frames
- caption times are monotonic, positive, non-overlapping, and inside the composition

Expected: zero validation errors.

---

### Task 6: Scaffold and test the Remotion edit

**Files:**
- Create: `edit/remotion/package.json`
- Create: `edit/remotion/tsconfig.json`
- Create: `edit/remotion/src/index.ts`
- Create: `edit/remotion/src/Root.tsx`
- Create: `edit/remotion/src/Film.tsx`
- Create: `edit/remotion/src/Shot.tsx`
- Create: `edit/remotion/src/Captions.tsx`
- Create: `edit/remotion/src/FlashOverlay.tsx`
- Create: `edit/remotion/src/timeline.ts`
- Create: `edit/remotion/src/timeline.test.ts`
- Create: `edit/remotion/public/edit-manifest.json`
- Create: `edit/remotion/public/captions.json`
- Create: `edit/remotion/public/clips/S01.mp4` through `S18.mp4` as symlinks or local copies

**Interfaces:**
- Consumes: `edit-manifest.json`, `captions.json`, and eighteen selected clips.
- Produces: Remotion compositions `CleanMaster` and `SubtitledMaster`.

- [ ] **Step 1: Scaffold the blank Remotion project**

From `edit/`, run:

```bash
npx create-video@latest --yes --blank --no-tailwind remotion
```

Add current compatible packages through Remotion:

```bash
npx remotion add @remotion/media @remotion/captions
npm install --save-dev tsx
```

- [ ] **Step 2: Write the failing timeline tests**

Test these pure functions in `timeline.test.ts`:

```ts
assert.equal(totalFrames(manifest.shots), 3600);
assert.deepEqual(buildStarts([{durationInFrames: 210}, {durationInFrames: 180}]), [0, 210]);
assert.equal(validateManifest(manifest), true);
assert.throws(() => validateManifest({...manifest, shots: []}), /18 shots/);
assert.throws(() => validateManifest(manifestWithMissingClip), /missing clip/);
assert.equal(validateCaptions(captions, 120000), true);
```

- [ ] **Step 3: Run tests and verify failure**

Run:

```bash
npx tsx --test src/timeline.test.ts
```

Expected: FAIL because `totalFrames`, `buildStarts`, `validateManifest`, and `validateCaptions` do not exist.

- [ ] **Step 4: Implement `timeline.ts`**

Export:

```ts
export type ShotEdit = {
  id: string;
  src: string;
  trimBeforeFrames: number;
  durationInFrames: number;
  gain: number;
  fadeInFrames: number;
  fadeOutFrames: number;
};

export const totalFrames = (shots: ShotEdit[]): number;
export const buildStarts = (shots: Pick<ShotEdit, "durationInFrames">[]): number[];
export const validateManifest = (manifest: EditManifest): true;
export const validateCaptions = (captions: Caption[], totalMs: number): true;
```

Validation must enforce eighteen unique S01–S18 IDs, positive durations, non-negative trims, gains from 0 to 1.5, fades no longer than half the shot, and caption bounds.

- [ ] **Step 5: Run tests and verify pass**

Run:

```bash
npx tsx --test src/timeline.test.ts
```

Expected: all tests PASS.

- [ ] **Step 6: Implement `Shot.tsx`**

Render each source with:

```tsx
<Video
  src={staticFile(shot.src)}
  trimBefore={shot.trimBeforeFrames}
  trimAfter={shot.trimBeforeFrames + shot.durationInFrames}
  volume={(frame) => shot.gain * boundaryEnvelope(frame, shot)}
  style={{width: "100%", height: "100%", objectFit: "cover"}}
/>
```

Use `interpolate()` with clamped extrapolation for the boundary envelope. Do not use CSS transitions or animations.

- [ ] **Step 7: Implement `Film.tsx`**

Use `<Series>` with one premounted `<Series.Sequence>` per shot. Add deterministic flash overlays at the S05→S06 activation and S17 reset boundaries without changing total duration. Keep ordinary comic and motion-matched cuts as hard cuts.

- [ ] **Step 8: Implement captions**

Load `Caption[]` JSON with `useDelayRender()`. Render one or two lines at a time in a separate component. Use at least 44 px text, white fill, restrained dark outline/shadow, and a bottom position at least 180 px above the frame edge. Preserve whitespace and never show captions in `CleanMaster`.

- [ ] **Step 9: Register both compositions**

In `Root.tsx`, register:

```tsx
<Composition
  id="CleanMaster"
  component={Film}
  durationInFrames={totalFrames(editManifest.shots)}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{showCaptions: false}}
/>
<Composition
  id="SubtitledMaster"
  component={Film}
  durationInFrames={totalFrames(editManifest.shots)}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{showCaptions: true}}
/>
```

Set `fps={30}`, `width={1080}`, `height={1920}`, and calculate `durationInFrames` from the imported manifest.

- [ ] **Step 10: Run code and composition checks**

Run:

```bash
npm test
npx remotion compositions src/index.ts
```

Expected: tests pass and both compositions report 1080 × 1920, 30 fps, and the same duration.

---

### Task 7: Preview, refine, and render both masters

**Files:**
- Create: `final/doraemon-small-gadget-adventure-clean.mp4`
- Create: `final/doraemon-small-gadget-adventure-subtitled.mp4`
- Create: `final/poster.jpg`
- Create: `final/contact-sheet.jpg`
- Modify: `edit/edit-manifest.json`
- Modify: `edit/captions.json`

**Interfaces:**
- Consumes: working Remotion compositions.
- Produces: final clean/subtitled masters and visual QA artifacts.

- [ ] **Step 1: Render representative stills**

Render at frames `0`, `990`, `2310`, `3150`, `3450`, and the last valid frame for both compositions at quarter scale.

Expected: no black frames, wrong clip paths, subtitle overflow, unsafe cropping, or duplicate overlay artifacts.

- [ ] **Step 2: Preview the full timeline**

Start:

```bash
npx remotion studio src/index.ts
```

Review shot order, trims, audio boundaries, dialogue/caption sync, activation flash, reset flash, and the sunset ending. Modify only `edit-manifest.json` and `captions.json` for timing corrections.

- [ ] **Step 3: Render the clean master**

Run:

```bash
npx remotion render src/index.ts CleanMaster ../../final/doraemon-small-gadget-adventure-clean.mp4 --codec=h264
```

Expected: successful MP4 render with native Seedance audio and no captions.

- [ ] **Step 4: Render the subtitled master**

Run:

```bash
npx remotion render src/index.ts SubtitledMaster ../../final/doraemon-small-gadget-adventure-subtitled.mp4 --codec=h264
```

Expected: successful MP4 render with the same duration and Chinese captions.

- [ ] **Step 5: Generate the poster and contact sheet**

Extract a strong S16 or S18 frame as `poster.jpg`. Generate a 6 × 3 contact sheet:

```bash
npx remotion ffmpeg -i ../../final/doraemon-small-gadget-adventure-subtitled.mp4 \
  -vf "fps=1/6.6667,scale=180:320,tile=6x3" -frames:v 1 ../../final/contact-sheet.jpg
```

Expected: eighteen readable portrait thumbnails.

---

### Task 8: Verify and close out the local production package

**Files:**
- Modify: `manifest.json`
- Modify: `notes.md`

**Interfaces:**
- Consumes: both masters, poster, contact sheet, all prompts, task manifests, and QA results.
- Produces: a self-contained local handoff.

- [ ] **Step 1: Probe both masters**

Run:

```bash
for final_path in \
  content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/doraemon-small-gadget-adventure-clean.mp4 \
  content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/doraemon-small-gadget-adventure-subtitled.mp4
do
  npx remotion ffprobe -v error \
    -show_entries stream=codec_type,codec_name,width,height,r_frame_rate \
    -show_entries format=duration -of json "$final_path"
done
```

Expected for both:

- duration from 115 to 125 seconds
- 1080 × 1920 video
- H.264 video stream
- AAC audio stream
- 30 fps

- [ ] **Step 2: Perform visual and audio QA**

Inspect the opening frame, every shot boundary, S06 magic reveal, S12 hound reveal, S16 wave climax, S17 reset, and S18 ending. Listen through the complete subtitled master with headphones. Reject completion for missing dialogue, clipped peaks, harsh clicks, unintelligible speech, unwanted subtitles inside generated footage, visible logos/watermarks, or broken character anatomy.

- [ ] **Step 3: Confirm caption QA**

Check all fourteen lines for exact Chinese spelling, timing, two-line maximum, safe-area placement, and contrast over bright and dark frames.

- [ ] **Step 4: Finalize provenance**

Update `manifest.json` with:

- image generation prompts and local paths
- Seedance task IDs, model, resolution, durations, native-audio setting, and output paths
- selected take and trim metadata
- Remotion package version and render commands
- final media probes and QA status

Update `notes.md` with final duration, deliverable links, known minor limitations, and a reminder that public distribution was not performed.

- [ ] **Step 5: Run final artifact checks**

Run:

```bash
test -s content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/doraemon-small-gadget-adventure-clean.mp4
test -s content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/doraemon-small-gadget-adventure-subtitled.mp4
test -s content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/poster.jpg
test -s content/inbox/media/2026-07-25-doraemon-small-gadget-adventure/final/contact-sheet.jpg
```

Expected: all commands exit `0`.

- [ ] **Step 6: Report completion**

Provide clickable absolute paths to both MP4 files, poster, contact sheet, design spec, implementation plan, and local production package. Report Seedance task count, failed/retried shots, final duration, codec/resolution/audio verification, and any remaining limitation. Do not claim publication.
