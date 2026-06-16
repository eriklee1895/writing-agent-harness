---
name: video-material-ingest
description: Ingest known video URLs with yt-dlp into traceable local asset folders for writing, visuals, short-video production, and HyperFrames.
---

# Video Material Ingest

Use this skill when the user provides, selects, or confirms a known video URL that should become local writing or production material.

Do not use this skill for web search, image search, stock photo selection, copyright judgment, or final publication decisions.

## Prerequisites

- `yt-dlp` must be installed and available on `PATH`.
- Chrome should be logged into platforms that need authentication, such as Bilibili or Douyin.
- The script defaults to `--cookies-from-browser chrome`.

Never export, print, store, or commit cookies. Browser login state stays local.

## Default Command

For an article folder:

```bash
node scripts/ingest-video-material.mjs \
  "<video-url>" \
  --target /absolute/path/to/content/drafts/YYYY-MM-DD-topic
```

Without `--target`, the script writes to:

```text
content/inbox/media/YYYY-MM-DD-<source-slug>/
```

## Output

Each ingest folder should contain:

- `media.ext`
- `thumbnail.*`, when available
- `info.json`
- `manifest.json`
- `sources.md`

Use `sources.md` during article review. It records source URL, retrieved date, title, uploader, and the publication-rights reminder.

## Login Failures

If `yt-dlp` fails with authentication, forbidden, login, or cookie-related errors:

1. Ask the user to open the platform in Chrome and confirm they are logged in.
2. Retry the same command with `--cookies-from-browser chrome`.
3. Do not ask the user to paste cookies into chat.

## Follow-Ups

After ingest, suggest only the next useful step:

- transcribe audio for research notes
- capture screenshots for article visuals
- cut clips for short-video or HyperFrames work
- convert video to a production-friendly format

Do not perform these follow-ups unless the user asks.
