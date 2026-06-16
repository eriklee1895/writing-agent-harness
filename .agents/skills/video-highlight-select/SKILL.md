---
name: video-highlight-select
description: Help a human choose article-relevant highlight moments from a local video-material-ingest package. Use this whenever the user wants to find/select/review video highlights, create a contact sheet, choose clips for an article, or prepare start/end/title/caption candidates before running article-video-clip.
---

# Video Highlight Select

Use this skill when a video has already been ingested or wrapped as a local `video-material-ingest` package and the user wants help choosing useful moments for an article.

This is a human-assisted selection skill. It does not auto-detect the best highlight, render final clips, generate subtitles, download URLs, or upload to WeChat.

## Prerequisites

- A local material package with `media.ext`, `manifest.json`, and `sources.md`.
- `ffprobe` and `ffmpeg` available on `PATH`.
- An article intent, section purpose, or rough editorial goal if available.

Bare `.mp4` files in `content/inbox/` should be wrapped into a material package first. Use a `media.mp4` symlink to avoid copying large local files.

## Default Workflow

1. Confirm the material package path.
2. Ask for the article intent if it is not obvious:
   - opening hook
   - visual proof
   - cultural/context detail
   - transition/atmosphere
   - quote or argument support
3. Run a dry-run first.
4. Generate a contact sheet and candidate workspace.
5. Let the human review the contact sheet and choose or edit candidate rows.
6. Pass the confirmed candidate to `article-video-clip`.

## Default Command

```bash
node scripts/select-video-highlights.mjs \
  --material /absolute/path/to/article/assets/media/source-slug \
  --intent "放在文章开头抓人，展示这段舞为什么有传播性"
```

With an already-known candidate:

```bash
node scripts/select-video-highlights.mjs \
  --material /absolute/path/to/article/assets/media/source-slug \
  --intent "放在文章开头抓人" \
  --candidate "00:03-00:11|邯郸学步：曲裾入场|素材再包装|wechat-landscape|开头视觉钩子"
```

Use `--dry-run` when checking paths and planned commands:

```bash
node scripts/select-video-highlights.mjs \
  --material /absolute/path/to/article/assets/media/source-slug \
  --intent "文章段落意图" \
  --dry-run
```

## Output

The default output lives inside the material package:

```text
<material-package>/highlight-select/
├── contact-sheet.jpg
├── highlight-candidates.md
└── highlight-candidates.json
```

`highlight-candidates.md` is the human review surface. It records source metadata, media metadata, the article intent, a contact sheet, a candidate table, and an `article-video-clip` handoff command.

## Compatibility Rule

Do not rely on FFmpeg `drawtext` for contact-sheet timestamps. Homebrew's regular `ffmpeg` formula may not include the optional font-rendering filters needed for `drawtext`, even when FFmpeg itself is current.

Use a plain `contact-sheet.jpg` plus the generated contact-sheet index table in `highlight-candidates.md` / `highlight-candidates.json`. If richer labels are needed later, add a Pillow/ImageMagick post-processing step instead of requiring `ffmpeg-full`.

## Candidate Format

Use this format for each manual candidate:

```text
start-end|title|caption|preset|notes
```

Example:

```text
00:03-00:11|邯郸学步：曲裾入场|素材再包装|wechat-landscape|开头抓人
```

Supported presets should match `article-video-clip`, currently:

- `wechat-landscape`
- `wechat-portrait`

## Handoff

After the human chooses a row, run `article-video-clip` with the selected candidate:

```bash
node ../article-video-clip/scripts/create-article-video-clip.mjs \
  --material /absolute/path/to/article/assets/media/source-slug \
  --start 00:03 \
  --end 00:11 \
  --preset wechat-landscape \
  --title "邯郸学步：曲裾入场" \
  --caption "素材再包装"
```

## Boundaries

- `video-material-ingest` downloads/wraps known video URLs and records provenance.
- `video-highlight-select` helps humans choose candidate moments.
- `article-video-clip` renders the confirmed clip.
- `wechat-publish-workflow` handles whether/how the final video enters a WeChat draft.

Do not claim the highlight has been automatically selected. The human still decides which candidate is editorially right for the article.
