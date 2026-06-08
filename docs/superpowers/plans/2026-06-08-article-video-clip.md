# Article Video Clip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a project-level `article-video-clip` skill that turns an ingested video material package into a lightly packaged article-ready clip.

**Architecture:** Add one Node.js CLI and one skill runbook. The CLI reads a `video-material-ingest` package, validates human-specified time range and preset, builds `ffmpeg` trim/crop commands, generates a small HyperFrames wrapper project, renders `final.mp4`, and writes provenance metadata. Tests focus on pure planning helpers and dry-run behavior with injected command runners.

**Tech Stack:** Node.js ESM, Node built-in `node:test`, `ffmpeg`, HyperFrames CLI through `npx hyperframes`.

---

## File Structure

- Create `.agents/skills/article-video-clip/SKILL.md`
  - Agent-facing workflow, prerequisites, command examples, and boundaries.
- Create `.agents/skills/article-video-clip/scripts/create-article-video-clip.mjs`
  - CLI implementation and exported helpers.
- Create `.agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs`
  - Unit tests for timestamp parsing, package discovery, output planning, preset/crop args, manifest/notes, and dry-run command planning.
- Modify `docs/reference/skills.md`
  - Register `article-video-clip`.
- Modify `docs/reference/visuals.md`
  - Add article-ready video clip output rule.
- Modify `docs/project/prepare-environment.md`
  - Add `ffmpeg` and HyperFrames CLI checks for article video clipping.

---

### Task 1: Helper Tests And Minimal Stub

**Files:**
- Create: `.agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs`
- Create: `.agents/skills/article-video-clip/scripts/create-article-video-clip.mjs`

- [ ] **Step 1: Write helper tests**

Create tests that import these functions from `create-article-video-clip.mjs`:

```js
parseTimestamp
getPreset
buildClipSlug
inferArticleFolder
planOutputDirectory
findMediaFile
buildFfmpegArgs
createClipManifest
createNotesMarkdown
parseArgs
```

Test required behavior:

- `parseTimestamp("01:02.500")` returns `62.5`.
- `getPreset("wechat-landscape")` returns `width: 1920`, `height: 1080`, `aspect: "16:9"`.
- `getPreset("wechat-portrait")` returns `width: 1080`, `height: 1920`, `aspect: "9:16"`.
- `buildClipSlug("邯郸学步为什么火了")` returns `邯郸学步为什么火了`.
- `inferArticleFolder("/repo/content/drafts/topic/assets/media/source")` returns `/repo/content/drafts/topic`.
- `planOutputDirectory({ articleFolder, slug })` returns `<articleFolder>/assets/video-clips/<slug>`.
- `findMediaFile(["media.mp4", "manifest.json"])` returns `media.mp4`.
- `buildFfmpegArgs` includes `-ss`, `-to`, crop/scale filter, and output path.
- `createClipManifest` preserves source URLs, time range, preset, focus, and output names.
- `createNotesMarkdown` includes source URL and publication-rights reminder.
- `parseArgs` requires `--material`, `--start`, `--end`, `--preset`, and `--title`.

- [ ] **Step 2: Add minimal stubs**

Create exported functions returning simple placeholders so tests run and fail with assertions.

- [ ] **Step 3: Verify red tests**

Run:

```bash
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
```

Expected: FAIL because stub behavior is incomplete.

- [ ] **Step 4: Commit failing tests**

```bash
git add .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs .agents/skills/article-video-clip/scripts/create-article-video-clip.mjs
git commit -m "test: cover article video clip helpers"
```

---

### Task 2: Helper Implementation

**Files:**
- Modify: `.agents/skills/article-video-clip/scripts/create-article-video-clip.mjs`
- Test: `.agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs`

- [ ] **Step 1: Implement pure helpers**

Implement:

- timestamp parsing for seconds, `MM:SS`, and `HH:MM:SS`;
- slugging that preserves CJK and ASCII alphanumerics;
- preset lookup for `wechat-landscape` and `wechat-portrait`;
- media package discovery based on `manifest.json` and `media.*`;
- article folder inference from `assets/media/<slug>`;
- output directory planning under `assets/video-clips/<clip-slug>`;
- `ffmpeg` argument construction with center/left/right crop focus;
- clip manifest and notes generation;
- CLI argument parsing.

- [ ] **Step 2: Verify helper tests**

Run:

```bash
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
```

Expected: PASS.

- [ ] **Step 3: Commit helper implementation**

```bash
git add .agents/skills/article-video-clip/scripts/create-article-video-clip.mjs
git commit -m "feat: implement article video clip helpers"
```

---

### Task 3: CLI Pipeline And HyperFrames Wrapper

**Files:**
- Modify: `.agents/skills/article-video-clip/scripts/create-article-video-clip.mjs`
- Modify: `.agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs`

- [ ] **Step 1: Add dry-run pipeline test**

Test `createClip` with a temporary material package and injected `runCommandFn`. It should:

- read `manifest.json`;
- create planned output paths;
- return planned `ffmpeg`, `hyperframes lint`, `hyperframes inspect`, and `hyperframes render` commands;
- not execute commands when `dryRun` is true.

- [ ] **Step 2: Implement CLI pipeline**

Implement:

- `runCommand`;
- package validation;
- `ffmpeg` trim/crop/transcode to `hyperframes/assets/source-clip.mp4`;
- HyperFrames `index.html` generation with source video, title, optional caption, and source note;
- `npx hyperframes lint`, `inspect`, and `render --output final.mp4`;
- `clip-manifest.json`, `notes.md`, and `preview-frame.jpg` extraction through `ffmpeg`;
- `--dry-run` to print planned paths and commands without writing media outputs.

- [ ] **Step 3: Verify tests**

Run:

```bash
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
```

Expected: PASS.

- [ ] **Step 4: Commit CLI pipeline**

```bash
git add .agents/skills/article-video-clip/scripts/create-article-video-clip.mjs .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
git commit -m "feat: add article video clip cli"
```

---

### Task 4: Skill Runbook And Docs

**Files:**
- Create: `.agents/skills/article-video-clip/SKILL.md`
- Modify: `docs/reference/skills.md`
- Modify: `docs/reference/visuals.md`
- Modify: `docs/project/prepare-environment.md`

- [ ] **Step 1: Add skill runbook**

Document:

- use when converting a `video-material-ingest` package into an article-ready clip;
- prerequisites: `ffmpeg`, HyperFrames CLI, source package;
- default command;
- required human decisions: start/end, preset, title, optional caption/focus;
- out-of-scope: URL ingest, automatic clip selection, WeChat upload.

- [ ] **Step 2: Register docs**

Add concise references to skills, visuals, and environment docs.

- [ ] **Step 3: Run scans and tests**

Run:

```bash
rg -n "article-video-clip|ffmpeg|hyperframes" docs .agents/skills/article-video-clip
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
```

Expected: docs mention the new workflow; tests pass.

- [ ] **Step 4: Commit docs**

```bash
git add .agents/skills/article-video-clip/SKILL.md docs/reference/skills.md docs/reference/visuals.md docs/project/prepare-environment.md
git commit -m "docs: add article video clip skill"
```

---

### Task 5: Validation

**Files:**
- No required source changes.

- [ ] **Step 1: Verify tool availability**

Run:

```bash
ffmpeg -version
npx hyperframes --version
```

Expected: both commands are available, or missing dependency is reported clearly.

- [ ] **Step 2: Run unit tests**

Run:

```bash
node --test .agents/skills/article-video-clip/scripts/create-article-video-clip.test.mjs
```

Expected: PASS.

- [ ] **Step 3: Run dry-run against a real material package if available**

Use an existing `video-material-ingest` package under an article folder. If none exists, skip real-package smoke and report that only unit tests were run.

Expected: dry-run prints planned output directory and commands without creating rendered media.

---

## Self-Review

- Spec coverage: This plan covers material-package input, human-selected timestamps, two presets, ffmpeg trim/crop/transcode, HyperFrames wrapper generation, article-folder output, manifest/notes, docs, and WeChat upload boundary.
- Placeholder scan: No deferred implementation placeholders are included in task steps.
- Type consistency: Skill name is `article-video-clip`; script name is `create-article-video-clip.mjs`; output metadata is `clip-manifest.json`.

