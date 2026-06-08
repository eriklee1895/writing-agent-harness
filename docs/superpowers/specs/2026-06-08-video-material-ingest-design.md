# Video Material Ingest Design

## Context

`writing-agent-harness` already handles ideation, drafting, polishing, illustration, WeChat rendering, and publishing. The missing layer is video material ingestion: collecting known video URLs from external platforms so they can later support writing research, screenshots, short video production, HyperFrames compositions, and article visuals.

Erik has already validated that local `yt-dlp` can download YouTube, Bilibili, and Douyin links successfully. The first version should preserve that working path instead of rebuilding a downloader.

## Goal

Create a project-level `video-material-ingest` skill backed by one `yt-dlp` script.

The first version is an ingest layer, not a full editing pipeline. It should reliably download source media, save metadata, and place files into predictable directories with provenance preserved. Future workflows can add transcription, screenshots, clips, transcoding, and HyperFrames-ready outputs on top of the same manifest.

## Non-Goals

- Do not build a new downloader.
- Do not search for videos or images on the web.
- Do not handle general image search or visual asset discovery.
- Do not automate final publication or reuse of copyrighted media.
- Do not extract or store browser cookies.
- Do not build the full short-video pipeline in the first version.
- Do not move existing user-downloaded inbox files unless explicitly requested.

## Prerequisites

The local environment must have:

- `yt-dlp` installed and available on `PATH`.
- Browser login state prepared for platforms that need authentication.
- Chrome is the default browser cookie source for the first version.

The expected authenticated command shape is:

```bash
yt-dlp --cookies-from-browser chrome <url>
```

The skill should explain this requirement clearly. If a platform fails because the browser is not logged in, the agent should ask the user to log in through the browser and retry. The script must not print cookie values, export cookie jars, or commit any local account state.

## User Experience

Typical usage:

```bash
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
  "https://www.bilibili.com/video/BV1gBmTBtEoy" \
  --target /Users/eriklee/code/my_project/writing-agent-harness/content/drafts/2026-06-08-luolebai-handanxuebu
```

When `--target` points to an article folder, media should land in:

```text
<article-folder>/assets/media/<source-slug>/
```

When no target is provided, media should land in:

```text
content/inbox/media/YYYY-MM-DD-<source-slug>/
```

The script should print a short completion summary with the saved directory, title, platform if known, and downloaded files. It should not print secrets or noisy `yt-dlp` internals unless the command fails.

## Output Contract

Each ingest directory should include:

```text
media.ext                 # downloaded source video or audio, using yt-dlp's chosen extension
thumbnail.*               # best available thumbnail or cover, when available
info.json                 # yt-dlp metadata
manifest.json             # project-level normalized manifest
sources.md                # human-readable provenance notes
```

`manifest.json` should include:

- original URL
- canonical webpage URL if available
- title
- uploader / author if available
- platform / extractor
- download timestamp
- local filenames
- yt-dlp version
- command options used, excluding secrets
- intended use note: research / writing material / visual reference / future short-video material

`sources.md` should be readable inside an article folder and useful during final review. It should include the original URL, retrieved date, title, uploader, and a reminder to confirm rights and citation before publication.

## Capability Boundary

`video-material-ingest` is a known-video-URL ingest skill, not a discovery skill.

It should accept a URL the user or agent already selected, then download and preserve it as a traceable local asset package. It should not search the web for images, choose stock photos, rank visual candidates, or decide copyright suitability.

Image search and image generation remain separate workflows. Selected images may eventually get their own direct-asset ingest helper, but that should not be part of the first `video-material-ingest` implementation.

## Script Behavior

The first script should:

1. Validate that `yt-dlp` exists.
2. Accept one or more URLs.
3. Accept optional `--target`, `--cookies-from-browser`, `--audio-only`, and `--dry-run` flags.
4. Default `--cookies-from-browser` to `chrome`.
5. Create a stable slug from title or URL metadata.
6. Run `yt-dlp` with metadata and thumbnail writing enabled.
7. Normalize downloaded files into the output contract.
8. Write `manifest.json` and `sources.md`.
9. Fail clearly when login, network, platform extraction, or file layout problems occur.

The script can call `yt-dlp --dump-json` first to get metadata, then run the download into a temporary directory before moving normalized outputs into place. This avoids relying on fragile filename parsing.

## Skill Behavior

The project skill should help an agent:

- Decide whether media belongs in a specific article folder or generic inbox.
- Run the ingest script with the right target.
- Explain browser-cookie login prerequisites.
- Preserve source provenance for later review.
- Avoid leaking cookies, account state, or private downloaded files.
- Recommend follow-up steps without performing them automatically.

The skill should make the first version boring and reliable. Future subcommands can grow from the manifest:

- `transcribe`: extract audio and generate transcript.
- `screenshots`: capture selected frames for article visuals.
- `clips`: cut selected time ranges.
- `convert`: create HyperFrames-friendly normalized video assets.
- `storyboard`: collect frame stills and notes for short-video ideation.

## Directory And Docs Updates

Implementation should update:

- `.agents/skills/video-material-ingest/SKILL.md`
- `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`
- `docs/reference/skills.md`
- `docs/reference/visuals.md` or a new `docs/reference/media-assets.md`
- `docs/project/automation-roadmap.md`
- `docs/project/prepare-environment.md`

`AGENTS.md` may get one short high-frequency rule only after the workflow has been validated in real use.

## Safety And Review Boundary

Downloaded media is source material. The workflow may support research, private drafting, screenshots, reference review, and future production, but final public use still needs human review.

The skill should remind agents to check rights, citation, and platform-specific terms before publication or redistribution. This is especially important for short-video and HyperFrames reuse.

## Testing

Use local tests that avoid downloading large public media during routine runs:

- Unit-test slug generation and manifest writing.
- Test missing `yt-dlp` handling by overriding PATH.
- Test dry-run metadata behavior with a known URL only when network is available.
- Provide a manual smoke test command for a Bilibili URL using `--cookies-from-browser chrome`.

Manual validation for the first version:

```bash
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
  "https://www.bilibili.com/video/BV1gBmTBtEoy" \
  --target /Users/eriklee/code/my_project/writing-agent-harness/content/drafts/2026-06-08-luolebai-handanxuebu
```

Expected result:

- Media files are inside the article folder's `assets/media/` directory.
- `manifest.json` and `sources.md` preserve provenance.
- No cookie files or secrets are created in the repo.
- The command works with the already logged-in local Chrome session.
