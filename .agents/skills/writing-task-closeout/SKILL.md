---
name: writing-task-closeout
description: "写作任务发布后 closeout。Use after WeChat/blog draft creation, publishing, or final handoff when the user says 任务收尾/归档/复盘/回填链接/清理素材/整理 memory/git/task; archive final article state, move image/video binaries to .local-archive/YYYY-MM-DD-slug/, preserve prompts/metadata/manifests/notes, update publish status, decide memory/skill improvements, and prepare git/task handoff without publishing."
---

# Writing Task Closeout

## Overview

这个 skill 用于 `wechat-publish-workflow`、blog build/publish 或其他渠道交付之后，关闭一次写作任务。

它不负责判断文章内容是否 ready；pre-publish 内容检查交给 `article-readiness-check`。它也不点击最终发布/群发，除非用户已经明确授权并且当前任务就是发布 workflow。

`.local-archive/` 是本机二进制素材库，不是跨机器 canonical source。这个 repo 的 canonical source 是 Markdown / MDX、prompt、metadata、manifest、notes 和发布状态。跨机器工作时，需要手动同步 `.local-archive/`、从外部资产库取回、从平台 CDN 回填，或按 metadata 重新生成素材。

## Workflow

1. 确认任务状态：
   - `draft-created`: 已创建草稿，但还未正式发布。
   - `published`: 已发布，需要回填链接、`appmsgid` 或平台 ID。
   - `handoff-only`: 已交给用户 final review，暂不发布。
   - `abandoned`: 本次写作停止，但需要清理和记录原因。
2. 找到 canonical Markdown / MDX 和渠道产物：
   - article source；
   - generated preview / draft notes；
   - images / prompts / metadata；
   - video material packages / clips；
   - publish URL、`appmsgid`、blog URL 或其他平台 ID。
3. 按 `YYYY-MM-DD-slug` 创建或使用本机归档目录：

   ```text
   .local-archive/
     YYYY-MM-DD-slug/
       images/
       video-materials/
       video-clips/
       archive-manifest.md
   ```

4. 移动或确认二进制素材归档；repo 只保留轻量 provenance。
5. 写复盘、memory / skill 决策、git / task handoff。
6. 最终回复说明 closeout 状态和剩余人工动作。

## Archive Policy

### What Stays In Git

- Markdown / MDX source and channel-specific text versions.
- Frontmatter and publish status.
- Image prompt / metadata JSON, if small and not containing secrets.
- Asset manifest / notes, alt text, caption, usage, insertion point.
- `sources.md`, `manifest.json`, `clip-manifest.json`, `notes.md`.
- Published URL, CDN URL, `appmsgid`, blog repo path, or platform ID.
- Retrospective notes and reusable workflow updates.

### What Does Not Stay In Git

- Article image binaries: `*.png`, `*.jpg`, `*.jpeg`, `*.webp`, `*.gif`, `*.avif`, `*.heic`, `*.tif`, `*.tiff`.
- Design/source binaries such as PSD, large layered files, or generated image variants.
- Video binaries: `*.mp4`, `*.mov`, `*.m4v`, `*.webm`, `*.mkv`, `*.avi`.
- Raw video downloads, final clips, transcode intermediates, HyperFrames rendered video outputs.

Keep binary media in `.local-archive/YYYY-MM-DD-slug/` or external storage. If future blog assets move to a separate Astro repo, record the target repo/path or published URL in tracked notes here.

Do not use base64 as an archive strategy. It bloats HTML and Git history while making failures harder to debug.

### Image Archive

- Move final images and generated variants to `.local-archive/YYYY-MM-DD-slug/images/`.
- Keep source prompt, style profile, model/provider, size/ratio, generation time, usage and article reference.
- If `article-illustration` generated `.json` metadata, preserve it with the image.
- If an image was compressed/cropped/retouched, record the post-processing note.
- Repo should retain only prompt/metadata/manifest/alt/caption/published URL unless the user explicitly force-adds an exception.
- For WeChat, publishing should resolve `.local-archive` paths at CDP time, upload images to WeChat, replace `src` with WeChat CDN URLs, and then record the final CDN URL / draft status in tracked notes when available.

### Video Archive

- Move `media.*`, `final.*`, transcode intermediates and rendered video outputs to `.local-archive/YYYY-MM-DD-slug/video-materials/` or `video-clips/`.
- Keep tracked `sources.md`, `manifest.json`, `clip-manifest.json`, `notes.md` with source URL, retrieved date, segment timestamps, rights reminder, publish status and recovery hint.
- Do not record cookies, login state, account state, private browser profile paths, or sensitive absolute local paths. If needed, use a relative `.local-archive/YYYY-MM-DD-slug/...` hint.
- Do not `git add` video files.

## Cleanup

- Clean only files clearly belonging to this task and safe to regenerate or discard.
- `inbox/` material can be deleted, moved, or summarized only after confirming it has no independent future value.
- Failed `drafts/` intermediate versions can be removed or moved to `.local-archive/YYYY-MM-DD-slug/` when they are not meaningful writing variants.
- Do not delete user edits, source material, or unconfirmed assets.

## Retrospective

Record the useful parts of the run:

- final status and timeline;
- what changed during channel publishing;
- failures, error messages, workaround and verification;
- good prompts, styles, editorial moves, renderer fixes or upload lessons;
- remaining follow-ups.

Write verified, reusable workflow improvements to `docs/` or the relevant skill. Keep one-off observations and unverified local context in `.local-memory/`.

## Memory And Skill Decisions

- `SOUL.md`: only update for durable author voice, register or anti-style lessons validated in real writing.
- `AGENTS.md`: only update high-frequency repo behavior boundaries; keep it short.
- `docs/`: use for workflow improvements, retrospectives, checklists and publishing lessons.
- `.local-memory/`: use for short-term, local, not-yet-validated context.
- Existing skill bug: make a small fix when obvious; otherwise record in `docs/project/todolist.md` or the user's issue tracker.
- New skill: suggest one only when the workflow is likely to repeat 3+ times and has clear boundaries.

## Git And Task Handoff

- Inspect working tree before staging. There may be unrelated user changes.
- If the user asks for a commit, stage only files belonging to this writing task.
- Never stage ignored media binaries unless the user explicitly force-adds a specific exception.
- If a task system or `TaskCreate` item exists, mark it complete or report the remaining blocker.
- Final response should state archive path, tracked provenance files, publish status, retrospective/memory/skill actions and git/task status.

## Output Format

```markdown
## Closeout Status

Complete / Needs follow-up / Blocked

## Published State

- Status:
- URL / appmsgid / platform ID:

## Archive

- Local archive:
- Tracked provenance:
- Media not committed:

## Retrospective

- ...

## Memory / Skill

- ...

## Git / Task

- ...
```
