# Video Material Ingest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a project-level `video-material-ingest` skill that uses local `yt-dlp` to ingest known video URLs into traceable article or inbox asset folders.

**Architecture:** Add one project skill and one focused Node.js CLI script. The script owns argument parsing, `yt-dlp` invocation, output normalization, manifest writing, and provenance notes; docs explain when and how agents should use it. Tests cover pure helpers and failure paths without downloading large external media.

**Tech Stack:** Node.js ESM, Node built-in `node:test`, `yt-dlp`, Chrome browser login state through `--cookies-from-browser chrome`.

---

## File Structure

- Create `.agents/skills/video-material-ingest/SKILL.md`
  - Agent-facing runbook and safety boundary for known video URL ingestion.
- Create `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`
  - Node CLI and exported helper functions for tests.
- Create `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs`
  - Unit tests for slugging, path planning, manifest creation, command construction, and missing tool errors.
- Modify `docs/skills/skills-list.md`
  - Register `video-material-ingest` as a current project skill.
- Modify `docs/reference/visuals.md`
  - Point video-derived screenshots and covers back to `video-material-ingest`.
- Modify `docs/project/automation-roadmap.md`
  - Add video material ingest to the mid-term asset/reference-links track.
- Modify `docs/project/prepare-environment.md`
  - Add `yt-dlp` and Chrome login state as optional-but-required-for-video-ingest prerequisites.

---

### Task 1: Script Helper Tests

**Files:**
- Create: `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs`
- Create: `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`

- [ ] **Step 1: Create the failing helper tests**

Create `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs` with:

```js
import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import {
  buildYtDlpArgs,
  createManifest,
  createSourcesMarkdown,
  planOutputDirectory,
  slugify,
} from "./ingest-video-material.mjs";

test("slugify keeps useful ASCII and CJK title text", () => {
  assert.equal(slugify("赵都礼宴--《邯郸学步》 4K 纯享!!"), "赵都礼宴-邯郸学步-4k-纯享");
});

test("slugify falls back when title has no usable characters", () => {
  assert.equal(slugify("!!!"), "video");
});

test("planOutputDirectory uses article assets/media when target is provided", () => {
  const planned = planOutputDirectory({
    cwd: "/repo",
    target: "/repo/content/drafts/2026-06-08-topic",
    slug: "demo-video",
    today: "2026-06-08",
  });
  assert.equal(
    planned,
    path.join("/repo/content/drafts/2026-06-08-topic", "assets", "media", "demo-video"),
  );
});

test("planOutputDirectory uses content inbox when target is omitted", () => {
  const planned = planOutputDirectory({
    cwd: "/repo",
    target: "",
    slug: "demo-video",
    today: "2026-06-08",
  });
  assert.equal(planned, path.join("/repo", "content", "inbox", "media", "2026-06-08-demo-video"));
});

test("buildYtDlpArgs includes chrome cookies without exporting cookie files", () => {
  const args = buildYtDlpArgs({
    url: "https://www.bilibili.com/video/BV1gBmTBtEoy",
    outputTemplate: "/tmp/work/%(title)s.%(ext)s",
    cookiesFromBrowser: "chrome",
    audioOnly: false,
    dumpJson: false,
  });

  assert.deepEqual(args, [
    "--cookies-from-browser",
    "chrome",
    "--write-info-json",
    "--write-thumbnail",
    "--no-progress",
    "-o",
    "/tmp/work/%(title)s.%(ext)s",
    "https://www.bilibili.com/video/BV1gBmTBtEoy",
  ]);
});

test("buildYtDlpArgs supports metadata dry run", () => {
  const args = buildYtDlpArgs({
    url: "https://example.com/video",
    outputTemplate: "/tmp/work/%(title)s.%(ext)s",
    cookiesFromBrowser: "chrome",
    audioOnly: false,
    dumpJson: true,
  });

  assert.ok(args.includes("--dump-json"));
  assert.ok(!args.includes("--write-info-json"));
});

test("createManifest records provenance without secrets", () => {
  const manifest = createManifest({
    inputUrl: "https://example.com/watch/1",
    info: {
      webpage_url: "https://example.com/canonical",
      title: "Demo",
      uploader: "Author",
      extractor_key: "Example",
      id: "abc123",
    },
    downloadedFiles: ["media.mp4", "thumbnail.jpg", "info.json"],
    ytDlpVersion: "2026.01.01",
    cookiesFromBrowser: "chrome",
    audioOnly: false,
    downloadedAt: "2026-06-08T00:00:00.000Z",
  });

  assert.equal(manifest.original_url, "https://example.com/watch/1");
  assert.equal(manifest.canonical_url, "https://example.com/canonical");
  assert.equal(manifest.title, "Demo");
  assert.equal(manifest.command_options.cookies_from_browser, "chrome");
  assert.equal(JSON.stringify(manifest).includes("cookiejar"), false);
});

test("createSourcesMarkdown includes final-review reminder", () => {
  const markdown = createSourcesMarkdown({
    manifest: {
      title: "Demo",
      original_url: "https://example.com/watch/1",
      canonical_url: "https://example.com/canonical",
      uploader: "Author",
      platform: "Example",
      downloaded_at: "2026-06-08T00:00:00.000Z",
    },
  });

  assert.match(markdown, /# Video Source/);
  assert.match(markdown, /https:\/\/example.com\/watch\/1/);
  assert.match(markdown, /Confirm rights, citation, and platform terms before publication/);
});
```

- [ ] **Step 2: Add a minimal module stub**

Create `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs` with:

```js
export function slugify() {
  return "video";
}

export function planOutputDirectory() {
  return "";
}

export function buildYtDlpArgs() {
  return [];
}

export function createManifest() {
  return {};
}

export function createSourcesMarkdown() {
  return "";
}
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
node --test .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
```

Expected: FAIL with assertion errors for slugging, paths, command args, manifest fields, and Markdown content.

- [ ] **Step 4: Commit failing tests**

```bash
git add .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs
git commit -m "test: cover video material ingest helpers"
```

---

### Task 2: Script Helper Implementation

**Files:**
- Modify: `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`
- Test: `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs`

- [ ] **Step 1: Implement pure helpers**

Replace `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs` with:

```js
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const DEFAULT_COOKIE_BROWSER = "chrome";

export function slugify(value, fallback = "video") {
  const cleaned = String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
  return cleaned || fallback;
}

export function planOutputDirectory({ cwd, target, slug, today }) {
  if (target) {
    return path.join(path.resolve(target), "assets", "media", slug);
  }
  return path.join(path.resolve(cwd), "content", "inbox", "media", `${today}-${slug}`);
}

export function buildYtDlpArgs({
  url,
  outputTemplate,
  cookiesFromBrowser = DEFAULT_COOKIE_BROWSER,
  audioOnly = false,
  dumpJson = false,
}) {
  const args = [];
  if (cookiesFromBrowser) {
    args.push("--cookies-from-browser", cookiesFromBrowser);
  }
  if (dumpJson) {
    args.push("--dump-json", "--no-progress", url);
    return args;
  }
  if (audioOnly) {
    args.push("-x", "--audio-format", "m4a");
  }
  args.push("--write-info-json", "--write-thumbnail", "--no-progress", "-o", outputTemplate, url);
  return args;
}

export function createManifest({
  inputUrl,
  info,
  downloadedFiles,
  ytDlpVersion,
  cookiesFromBrowser,
  audioOnly,
  downloadedAt,
}) {
  return {
    schema_version: 1,
    original_url: inputUrl,
    canonical_url: info.webpage_url || inputUrl,
    title: info.title || "",
    uploader: info.uploader || info.channel || info.creator || "",
    platform: info.extractor_key || info.extractor || "",
    source_id: info.id || "",
    downloaded_at: downloadedAt,
    local_files: downloadedFiles,
    yt_dlp_version: ytDlpVersion,
    command_options: {
      cookies_from_browser: cookiesFromBrowser || "",
      audio_only: Boolean(audioOnly),
    },
    intended_use:
      "research / writing material / visual reference / future short-video material",
  };
}

export function createSourcesMarkdown({ manifest }) {
  return [
    "# Video Source",
    "",
    `- Title: ${manifest.title || "Unknown"}`,
    `- Original URL: ${manifest.original_url}`,
    `- Canonical URL: ${manifest.canonical_url || manifest.original_url}`,
    `- Uploader: ${manifest.uploader || "Unknown"}`,
    `- Platform: ${manifest.platform || "Unknown"}`,
    `- Retrieved: ${manifest.downloaded_at}`,
    "",
    "## Review Note",
    "",
    "Confirm rights, citation, and platform terms before publication or redistribution.",
    "",
  ].join("\n");
}

export async function pathExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}
```

- [ ] **Step 2: Run helper tests**

Run:

```bash
node --test .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
```

Expected: PASS for all helper tests.

- [ ] **Step 3: Commit helper implementation**

```bash
git add .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs
git commit -m "feat: implement video material ingest helpers"
```

---

### Task 3: CLI Download Workflow

**Files:**
- Modify: `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`
- Test: `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs`

- [ ] **Step 1: Add tests for argument parsing and command failures**

Append to `.agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs`:

```js
import {
  parseArgs,
  redactCommandForDisplay,
} from "./ingest-video-material.mjs";

test("parseArgs accepts url, target, cookies browser, and dry run", () => {
  const parsed = parseArgs([
    "https://example.com/video",
    "--target",
    "/repo/content/drafts/topic",
    "--cookies-from-browser",
    "chrome",
    "--dry-run",
  ]);

  assert.deepEqual(parsed.urls, ["https://example.com/video"]);
  assert.equal(parsed.target, "/repo/content/drafts/topic");
  assert.equal(parsed.cookiesFromBrowser, "chrome");
  assert.equal(parsed.dryRun, true);
});

test("parseArgs defaults cookies browser to chrome", () => {
  const parsed = parseArgs(["https://example.com/video"]);
  assert.equal(parsed.cookiesFromBrowser, "chrome");
});

test("parseArgs rejects missing url", () => {
  assert.throws(() => parseArgs([]), /Usage:/);
});

test("redactCommandForDisplay keeps browser name but never cookie file paths", () => {
  const display = redactCommandForDisplay("yt-dlp", [
    "--cookies-from-browser",
    "chrome",
    "--cookies",
    "/Users/me/cookies.txt",
    "https://example.com/video",
  ]);

  assert.match(display, /--cookies-from-browser chrome/);
  assert.match(display, /--cookies \[redacted\]/);
  assert.doesNotMatch(display, /cookies\.txt/);
});
```

- [ ] **Step 2: Implement CLI functions**

Append these functions to `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`:

```js
export function parseArgs(argv) {
  const options = {
    urls: [],
    target: "",
    cookiesFromBrowser: DEFAULT_COOKIE_BROWSER,
    audioOnly: false,
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--target") {
      options.target = argv[++index] || "";
    } else if (arg === "--cookies-from-browser") {
      options.cookiesFromBrowser = argv[++index] || "";
    } else if (arg === "--audio-only") {
      options.audioOnly = true;
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--help" || arg === "-h") {
      throw new Error(usage());
    } else if (arg.startsWith("--")) {
      throw new Error(`Unknown option: ${arg}\n\n${usage()}`);
    } else {
      options.urls.push(arg);
    }
  }

  if (options.urls.length === 0) {
    throw new Error(usage());
  }

  return options;
}

export function usage() {
  return [
    "Usage:",
    "  node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs <url...> [--target <article-folder>] [--cookies-from-browser chrome] [--audio-only] [--dry-run]",
  ].join("\n");
}

export function redactCommandForDisplay(command, args) {
  const redacted = [];
  for (let index = 0; index < args.length; index += 1) {
    redacted.push(args[index]);
    if (args[index] === "--cookies") {
      index += 1;
      redacted.push("[redacted]");
    }
  }
  return [command, ...redacted].join(" ");
}

export function runCommand(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(
          new Error(
            `Command failed (${code}): ${redactCommandForDisplay(command, args)}\n${stderr || stdout}`,
          ),
        );
      }
    });
  });
}
```

- [ ] **Step 3: Run tests**

Run:

```bash
node --test .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
```

Expected: PASS for helper and CLI parsing tests.

- [ ] **Step 4: Add the end-to-end ingest implementation**

Append to `.agents/skills/video-material-ingest/scripts/ingest-video-material.mjs`:

```js
async function getYtDlpVersion() {
  const result = await runCommand("yt-dlp", ["--version"]);
  return result.stdout.trim();
}

async function getVideoInfo({ url, cookiesFromBrowser }) {
  const args = buildYtDlpArgs({
    url,
    outputTemplate: "%(title)s.%(ext)s",
    cookiesFromBrowser,
    dumpJson: true,
  });
  const result = await runCommand("yt-dlp", args);
  return JSON.parse(result.stdout);
}

async function listRelativeFiles(directory) {
  const entries = await fs.readdir(directory);
  return entries.sort();
}

async function ingestOne({ url, options, cwd, today }) {
  const info = await getVideoInfo({ url, cookiesFromBrowser: options.cookiesFromBrowser });
  const slug = slugify(info.title || info.id || "video");
  const outputDirectory = planOutputDirectory({
    cwd,
    target: options.target,
    slug,
    today,
  });

  if (options.dryRun) {
    return {
      url,
      title: info.title || "",
      outputDirectory,
      dryRun: true,
    };
  }

  await fs.mkdir(outputDirectory, { recursive: true });
  const outputTemplate = path.join(outputDirectory, "media.%(ext)s");
  const downloadArgs = buildYtDlpArgs({
    url,
    outputTemplate,
    cookiesFromBrowser: options.cookiesFromBrowser,
    audioOnly: options.audioOnly,
    dumpJson: false,
  });

  await runCommand("yt-dlp", downloadArgs);

  const filesBeforeManifest = await listRelativeFiles(outputDirectory);
  const infoFile = filesBeforeManifest.find((file) => file.endsWith(".info.json"));
  if (infoFile) {
    await fs.rename(
      path.join(outputDirectory, infoFile),
      path.join(outputDirectory, "info.json"),
    );
  }
  const thumbnailFile = filesBeforeManifest.find((file) =>
    /^media\.(jpg|jpeg|png|webp)$/i.test(file),
  );
  if (thumbnailFile) {
    await fs.rename(
      path.join(outputDirectory, thumbnailFile),
      path.join(outputDirectory, thumbnailFile.replace(/^media\./, "thumbnail.")),
    );
  }

  const downloadedFiles = await listRelativeFiles(outputDirectory);
  const manifest = createManifest({
    inputUrl: url,
    info,
    downloadedFiles,
    ytDlpVersion: await getYtDlpVersion(),
    cookiesFromBrowser: options.cookiesFromBrowser,
    audioOnly: options.audioOnly,
    downloadedAt: new Date().toISOString(),
  });

  await fs.writeFile(
    path.join(outputDirectory, "manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
  await fs.writeFile(
    path.join(outputDirectory, "sources.md"),
    createSourcesMarkdown({ manifest }),
  );

  return {
    url,
    title: manifest.title,
    platform: manifest.platform,
    outputDirectory,
    files: await listRelativeFiles(outputDirectory),
  };
}

export async function main(argv = process.argv.slice(2), cwd = process.cwd()) {
  const options = parseArgs(argv);
  const today = new Date().toISOString().slice(0, 10);
  const results = [];
  for (const url of options.urls) {
    results.push(await ingestOne({ url, options, cwd, today }));
  }

  for (const result of results) {
    if (result.dryRun) {
      console.log(`Dry run: ${result.title || result.url}`);
      console.log(`Target: ${result.outputDirectory}`);
    } else {
      console.log(`Saved: ${result.title || result.url}`);
      if (result.platform) console.log(`Platform: ${result.platform}`);
      console.log(`Directory: ${result.outputDirectory}`);
      console.log(`Files: ${result.files.join(", ")}`);
    }
  }
}

const isCli = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isCli) {
  main().catch((error) => {
    console.error(error.message);
    if (/cookies|login|sign in|authentication|forbidden|unauthorized/i.test(error.message)) {
      console.error(
        "If this platform requires login, open it in Chrome first, then retry with --cookies-from-browser chrome.",
      );
    }
    process.exitCode = 1;
  });
}
```

- [ ] **Step 5: Run tests again**

Run:

```bash
node --test .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
```

Expected: PASS.

- [ ] **Step 6: Run a dry-run smoke test**

Run:

```bash
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
  "https://www.bilibili.com/video/BV1gBmTBtEoy" \
  --target /Users/eriklee/code/my_project/writing-agent-harness/content/drafts/2026-06-08-luolebai-handanxuebu \
  --dry-run
```

Expected: prints `Dry run:` and a target directory under `content/drafts/2026-06-08-luolebai-handanxuebu/assets/media/`. If Bilibili login is required, Chrome must already be logged in.

- [ ] **Step 7: Commit CLI workflow**

```bash
git add .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
git commit -m "feat: add video material ingest cli"
```

---

### Task 4: Project Skill Runbook

**Files:**
- Create: `.agents/skills/video-material-ingest/SKILL.md`

- [ ] **Step 1: Create the skill runbook**

Create `.agents/skills/video-material-ingest/SKILL.md` with:

```markdown
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
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
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
```

- [ ] **Step 2: Commit the skill runbook**

```bash
git add .agents/skills/video-material-ingest/SKILL.md
git commit -m "docs: add video material ingest skill"
```

---

### Task 5: Documentation Integration

**Files:**
- Modify: `docs/skills/skills-list.md`
- Modify: `docs/reference/visuals.md`
- Modify: `docs/project/automation-roadmap.md`
- Modify: `docs/project/prepare-environment.md`

- [ ] **Step 1: Update `docs/skills/skills-list.md`**

Add this bullet under `## Current Core`:

```markdown
- `video-material-ingest`
  - 用 `yt-dlp` 把已知视频 URL 摄取到本地可追溯素材目录。
  - 第一版只负责下载、metadata、manifest 和 sources 留痕；不负责搜索视频、图片搜索、版权判断或剪辑生产。
  - 默认使用 `--cookies-from-browser chrome` 读取本机 Chrome 登录态，但不导出、打印或提交 cookies。
```

- [ ] **Step 2: Update `docs/reference/visuals.md`**

Add this section after `## Asset Rule`:

```markdown
## Video Material

已知视频 URL 的素材摄取使用 `video-material-ingest` skill。

- 视频素材优先放在文章目录的 `assets/media/<slug>/`。
- 没有文章上下文时放在 `content/inbox/media/YYYY-MM-DD-<slug>/`。
- 每个素材包必须保留 `manifest.json` 和 `sources.md`，用于后续写作、配图、短视频或 HyperFrames 生产前复核。
- `video-material-ingest` 不负责图片 web search；图片搜索、图片生成和最终版权判断仍走独立 workflow。
```

- [ ] **Step 3: Update `docs/project/automation-roadmap.md`**

Add this bullet under `## Mid Term`:

```markdown
- `video-material-ingest`：基于 `yt-dlp` 摄取已知视频 URL，沉淀 metadata、manifest 和 sources，为后续转写、抽帧、切片、HyperFrames 和短视频生产做素材入口。
```

- [ ] **Step 4: Update `docs/project/prepare-environment.md`**

Add this bullet under `## Optional Runtime`:

```markdown
- yt-dlp
  - `video-material-ingest` 使用本机 `yt-dlp` 抓取 YouTube / Bilibili / Douyin 等已知视频 URL。
  - 需要登录态的平台依赖本机浏览器状态，默认命令使用 `--cookies-from-browser chrome`。
  - 不要导出、打印或提交 cookies。
```

Add `yt-dlp --version` to the `## Quick Verification` command block:

```bash
yt-dlp --version # optional, required for video-material-ingest
```

- [ ] **Step 5: Run documentation scans**

Run:

```bash
rg -n "video-material-ingest|yt-dlp|cookies-from-browser" docs .agents/skills/video-material-ingest
```

Expected: matches in the new skill, spec, plan, and updated docs. No cookie values or cookie file paths appear.

- [ ] **Step 6: Commit docs integration**

```bash
git add docs/skills/skills-list.md docs/reference/visuals.md docs/project/automation-roadmap.md docs/project/prepare-environment.md
git commit -m "docs: register video material ingest workflow"
```

---

### Task 6: Manual Smoke Validation

**Files:**
- No required source changes.
- May create ignored or untracked downloaded media under user-selected article folder during manual validation.

- [ ] **Step 1: Confirm no cookie artifacts exist**

Run:

```bash
find . -iname '*cookie*' -o -iname '*cookies*'
```

Expected: no new cookie files created by the implementation.

- [ ] **Step 2: Run all local tests**

Run:

```bash
node --test .agents/skills/video-material-ingest/scripts/ingest-video-material.test.mjs
```

Expected: PASS.

- [ ] **Step 3: Run dry-run against the known Bilibili URL**

Run:

```bash
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
  "https://www.bilibili.com/video/BV1gBmTBtEoy" \
  --target /Users/eriklee/code/my_project/writing-agent-harness/content/drafts/2026-06-08-luolebai-handanxuebu \
  --dry-run
```

Expected: command prints the planned output directory and does not download media.

- [ ] **Step 4: Optionally run a real download only if the user wants it**

Run only with explicit user consent:

```bash
node .agents/skills/video-material-ingest/scripts/ingest-video-material.mjs \
  "https://www.bilibili.com/video/BV1gBmTBtEoy" \
  --target /Users/eriklee/code/my_project/writing-agent-harness/content/drafts/2026-06-08-luolebai-handanxuebu
```

Expected: media package appears under `assets/media/<slug>/` with `media.ext`, `thumbnail.*` if available, `info.json`, `manifest.json`, and `sources.md`.

- [ ] **Step 5: Final git status review**

Run:

```bash
git status --short
```

Expected: only intentional source and doc changes are committed. Any downloaded videos remain untracked unless the user explicitly asks to add them.

---

## Self-Review

- Spec coverage: The plan implements the project skill, `yt-dlp` script, Chrome cookie prerequisite, article/inbox output layout, manifest, sources notes, docs integration, and manual validation. It keeps image web search and full editing pipeline out of scope.
- Placeholder scan: No `TBD`, `TODO`, or unspecified "add tests" steps remain.
- Type consistency: Script helper names are consistent across tests, implementation, docs, and commands: `video-material-ingest`, `ingest-video-material.mjs`, `slugify`, `planOutputDirectory`, `buildYtDlpArgs`, `createManifest`, `createSourcesMarkdown`, `parseArgs`, and `redactCommandForDisplay`.

