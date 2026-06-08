import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import {
  buildYtDlpArgs,
  createManifest,
  createSourcesMarkdown,
  ingestOne,
  parseArgs,
  planOutputDirectory,
  redactCommandForDisplay,
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

test("ingestOne dry run resolves metadata and planned output without downloading", async () => {
  const calls = [];
  const result = await ingestOne({
    url: "https://example.com/video",
    options: {
      target: "/repo/content/drafts/topic",
      cookiesFromBrowser: "chrome",
      audioOnly: false,
      dryRun: true,
    },
    cwd: "/repo",
    today: "2026-06-08",
    runCommandFn: async (command, args) => {
      calls.push({ command, args });
      return {
        stdout: JSON.stringify({
          id: "abc123",
          title: "Demo Video",
          webpage_url: "https://example.com/canonical",
          extractor_key: "Example",
        }),
        stderr: "",
      };
    },
  });

  assert.equal(result.dryRun, true);
  assert.equal(result.title, "Demo Video");
  assert.equal(result.outputDirectory, "/repo/content/drafts/topic/assets/media/demo-video");
  assert.equal(calls.length, 1);
  assert.ok(calls[0].args.includes("--dump-json"));
});
