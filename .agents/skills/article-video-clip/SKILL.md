---
name: article-video-clip
description: Create a lightly packaged article-ready video clip from a video-material-ingest package using ffmpeg and HyperFrames.
---

# Article Video Clip

Use this skill when a known video has already been ingested with `video-material-ingest` skill and the user wants a short, lightly packaged clip for an article.

Do not use this skill to download URLs, search for videos, auto-select highlights, auto-generate subtitles, or upload to WeChat.

## Prerequisites

- A `video-material-ingest` package with `media.ext`, `manifest.json`, and `sources.md`.
- `ffmpeg` available on `PATH`.
- HyperFrames CLI available through `npx hyperframes`.

Bare `.mp4` files in `content/inbox/` are not valid `--material` inputs. Wrap or migrate them into a material package first; use a `media.mp4` symlink when avoiding large local copies.

## Required Human Decisions

Ask for these before creating a clip:

- material package path
- start timestamp
- end timestamp
- preset: `wechat-landscape` or `wechat-portrait`
- title
- optional caption
- optional crop focus: `left`, `center`, or `right`

Default focus is `center`. If converting landscape footage to portrait and the subject may be off-center, ask for focus.

## Default Command

```bash
node scripts/create-article-video-clip.mjs \
  --material /absolute/path/to/article/assets/media/source-slug \
  --start 00:12 \
  --end 00:38 \
  --preset wechat-landscape \
  --title "视频标题" \
  --caption "可选说明" \
  --focus center
```

Use `--dry-run` first when checking paths and command planning.

Before calling the clip ready, verify `final.mp4` with `ffprobe` and inspect `preview-frame.jpg` for black frames, overflow, or obviously wrong crop.

## Output

The default output lives beside article assets:

```text
<article-folder>/assets/video-clips/<clip-slug>/
├── final.mp4
├── clip-manifest.json
├── notes.md
├── preview-frame.jpg
└── hyperframes/
```

`clip-manifest.json` and `notes.md` preserve source provenance and remind the user to confirm rights before publication.

## Boundaries

- `video-material-ingest` handles URL download and source material provenance.
- `article-video-clip` handles local clipping and light article packaging.
- `wechat-publish-workflow` handles whether and where the resulting clip is inserted into a WeChat draft.
- `wechat-article-publisher` may later automate actual WeChat video upload/insert.

Do not claim WeChat video upload is complete from this skill alone.
