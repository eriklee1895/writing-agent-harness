# Video Article Clip Design

## Context

`writing-agent-harness` now has `video-material-ingest`: a skill and script for ingesting known external video URLs into traceable local material packages. The next useful layer is not general video creation. It is article-focused video clipping: turning an ingested source video into a short, lightly packaged clip that can be embedded in a Markdown / WeChat article.

HyperFrames skills are prerequisites and underlying production tools, not the product boundary of this workflow. The harness-level capability should decide what an article-ready clip is, where it lives, how provenance is preserved, and what decisions require human input.

## Goal

Create a future project-level skill named `video-article-clip`.

The first version should take a `video-material-ingest` material package, a human-selected time range, and a target preset, then produce an article-ready video clip with light packaging.

The output should improve the article reading experience, not try to become a full short-video publishing system.

## First-Version Scope

The first version is **material repackaging**:

```text
video-material-ingest package
+ human-selected time range
+ output preset
+ title / caption / source note
-> article-ready video clip
```

It should:

- read an existing material package directory or `manifest.json`;
- require explicit `--start` and `--end` timestamps;
- support `wechat-landscape` and `wechat-portrait` presets;
- trim and crop/transcode with `ffmpeg`;
- wrap the clip with HyperFrames for title/caption/source overlay;
- output a final MP4 plus a clip manifest and notes;
- preserve source provenance from the original material package.

## Non-Goals

- Do not ingest external URLs directly. Use `video-material-ingest` first.
- Do not search for videos or images.
- Do not automatically choose the best source segment in the first version.
- Do not generate full article summary videos.
- Do not default to automatic transcription or auto subtitles.
- Do not upload the result to WeChat.
- Do not implement WeChat video insertion via CDP in this skill.
- Do not create a root-level Bun workspace just for this first version.

## Capability Boundary

`video-article-clip` is the derivative layer after `video-material-ingest`.

Responsibilities:

- turn a local, traceable video source package into an article-ready derived clip;
- keep source provenance visible in `clip-manifest.json` and `notes.md`;
- apply a restrained visual wrapper suitable for article insertion;
- hand the final file to publishing workflows.

Other skills:

- `video-material-ingest`: known video URL -> local source material package.
- HyperFrames skills: underlying composition authoring, preview, render, and media preprocessing.
- `wechat-publish-workflow`: decide whether and where a generated clip is inserted into a WeChat draft.
- `baoyu-post-to-wechat`: future CDP/browser automation for actual WeChat video upload/insert.

## Prerequisites

The environment should have:

- `video-material-ingest` material package with `media.ext`, `manifest.json`, and `sources.md`;
- `ffmpeg` available on `PATH`;
- Node.js and HyperFrames CLI available through `npx hyperframes`;
- local browser/render dependencies required by HyperFrames.

Do not add a root `package.json` or Bun workspace until shared project-level JS dependencies are actually needed. Revisit that when implementing WeChat video upload via CDP or when multiple project JS tools need shared dependencies and scripts.

## User Experience

Example command shape:

```bash
node .agents/skills/video-article-clip/scripts/create-video-article-clip.mjs \
  --material /absolute/path/to/content/drafts/2026-06-08-topic/assets/media/source-slug \
  --start 00:12 \
  --end 00:38 \
  --preset wechat-landscape \
  --title "邯郸学步为什么火了" \
  --caption "一段古典舞意外变成全民模仿模板" \
  --focus center \
  --style impact-rational
```

The user or author chooses:

- the source material package;
- start and end timestamps;
- `wechat-landscape` or `wechat-portrait`;
- title and optional caption;
- crop focus when needed.

The agent handles:

- verifying the source package;
- deriving output paths;
- trimming and crop/transcoding with `ffmpeg`;
- generating the HyperFrames wrapper;
- rendering the final MP4;
- writing metadata.

## Input Contract

Primary input is a material package directory, not a raw video file:

```text
assets/media/<source-slug>/
├── media.ext
├── thumbnail.*
├── info.json
├── manifest.json
└── sources.md
```

The script may accept `--manifest /path/to/manifest.json`, but package directory should be the default.

Using a package keeps provenance attached and avoids silently clipping untracked local videos.

## Output Contract

Default output:

```text
<article-folder>/assets/video-clips/<clip-slug>/
├── final.mp4
├── clip-manifest.json
├── notes.md
├── preview-frame.jpg
└── hyperframes/
    ├── index.html
    └── assets/
```

`<article-folder>` is inferred when material lives under:

```text
<article-folder>/assets/media/<source-slug>/
```

If the article folder cannot be inferred, require `--target`.

Do not write derived clips back into the source material package. A single source material package may produce multiple article clips.

## Presets

First version supports exactly two presets:

- `wechat-landscape`
  - 16:9 output.
  - Suitable for landscape source footage, stage performance, screen recording, product demo, and article embeds where the source composition matters.
- `wechat-portrait`
  - 9:16 output.
  - Suitable for mobile reading, vertical article inserts, and short opinion cards.

Do not support `source-aspect`, square, or arbitrary `--width --height` in the first version.

## Cropping

Default crop strategy:

- center crop;
- optional `--focus left|center|right`;
- default `--focus center`.

No AI subject detection in the first version.

When converting landscape source to portrait output, the agent should warn if the subject may be cropped and ask for focus if unclear.

## Visual Packaging

Default packaging is light:

- source video remains the visual body;
- title overlay or short intro title;
- optional caption / note strip;
- source note at the end or lower corner;
- restrained motion and transitions.

Do not add heavy motion graphics, AI voiceover, or generated article-summary scenes in the first version.

Style should be lightly tied to WeChat renderer presets:

- default: `impact-rational`;
- later: `literary-essay`, `tech-blog`.

Do not import or depend on the renderer's internal CSS. Keep a separate video template that only echoes the article style.

## Processing Pipeline

Recommended first-version pipeline:

```text
read material manifest
-> validate media file and timestamps
-> ffmpeg trim/crop/transcode intermediate clip
-> generate HyperFrames project wrapper
-> npx hyperframes lint / inspect
-> npx hyperframes render
-> write clip-manifest.json and notes.md
```

`ffmpeg` owns media operations: trim, crop, transcode, audio handling.

HyperFrames owns visual packaging: title, caption, source overlay, simple motion, final render.

## Metadata

`clip-manifest.json` should include:

- schema version;
- source material package path;
- source material manifest path;
- original URL and canonical URL;
- title / uploader / platform from source manifest;
- selected start and end timestamps;
- output preset;
- crop focus;
- style preset;
- clip title and caption;
- output file names;
- generation timestamp;
- tools used: `ffmpeg`, `hyperframes`, Node script version if available;
- intended use: article embed / WeChat draft review.

`notes.md` should include:

- clip title;
- source URL;
- source creator/uploader if available;
- selected time range;
- publication-rights reminder;
- instruction that WeChat upload/insert is handled by `wechat-publish-workflow`, not this skill.

## WeChat Boundary

`video-article-clip` stops after creating article-ready local files.

WeChat-specific workflow:

1. `wechat-publish-workflow` detects or is told about `assets/video-clips/<clip-slug>/final.mp4`.
2. User confirms the clip should be inserted into the WeChat article and where.
3. If CDP video upload exists, `baoyu-post-to-wechat` performs upload/insert and checks the editor.
4. If CDP video upload does not exist, the workflow stops at a human-editable draft state and asks the user to upload/insert manually.

Do not claim WeChat video upload is automated until it has been implemented and validated.

## Testing And Validation

First implementation should avoid large real media downloads in routine tests.

Automated tests:

- package discovery and article folder inference;
- timestamp parsing and validation;
- preset dimensions and crop filter construction;
- output path planning;
- clip manifest generation;
- missing `manifest.json`, missing media file, and invalid time range errors.

Manual smoke test:

1. Use `video-material-ingest` to create or locate a material package.
2. Create a 10-30 second landscape clip.
3. Create a 10-30 second portrait clip with `--focus center`.
4. Confirm `final.mp4`, `clip-manifest.json`, and `notes.md` exist.
5. Open/render preview and confirm title/caption/source overlays are readable on mobile.
6. Confirm no WeChat upload is attempted.

## Open Questions

- Exact visual template details for `impact-rational` video style.
- Whether captions should support multiple timed lines in v1 or only one static caption.
- Whether source note should be visible throughout, only at end, or in `notes.md` only.
- Whether `ffmpeg` output should preserve original audio by default or support `--mute`.
- Whether the first implementation should use a Node `.mjs` script only, or split media operations into small Python helpers if processing grows.

## Deferred Future Work

- transcript-assisted clip recommendations;
- automatic subtitle generation through HyperFrames media transcription;
- article viewpoint dynamic-summary videos;
- root-level Bun workspace if CDP video upload requires shared JS dependencies;
- WeChat video upload and insert automation in `baoyu-post-to-wechat`;
- reusable visual templates shared across blog, WeChat, and short-video outputs.

