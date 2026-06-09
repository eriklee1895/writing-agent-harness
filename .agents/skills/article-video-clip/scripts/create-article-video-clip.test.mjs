import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  buildClipSlug,
  buildFfmpegArgs,
  buildHyperframesHtml,
  createClip,
  createClipManifest,
  createNotesMarkdown,
  findMediaFile,
  getPreset,
  inferArticleFolder,
  parseArgs,
  parseTimestamp,
  planOutputDirectory,
} from "./create-article-video-clip.mjs";

test("parseTimestamp supports seconds, mm:ss, and hh:mm:ss", () => {
  assert.equal(parseTimestamp("12.5"), 12.5);
  assert.equal(parseTimestamp("01:02.500"), 62.5);
  assert.equal(parseTimestamp("01:02:03"), 3723);
});

test("getPreset returns WeChat landscape and portrait dimensions", () => {
  assert.deepEqual(getPreset("wechat-landscape"), {
    name: "wechat-landscape",
    width: 1920,
    height: 1080,
    aspect: "16:9",
  });
  assert.deepEqual(getPreset("wechat-portrait"), {
    name: "wechat-portrait",
    width: 1080,
    height: 1920,
    aspect: "9:16",
  });
});

test("buildClipSlug preserves useful CJK and ASCII text", () => {
  assert.equal(buildClipSlug("邯郸学步为什么火了?! 4K"), "邯郸学步为什么火了-4k");
  assert.equal(buildClipSlug("!!!"), "article-video-clip");
});

test("inferArticleFolder detects assets/media package layout", () => {
  assert.equal(
    inferArticleFolder("/repo/content/drafts/topic/assets/media/source-slug"),
    "/repo/content/drafts/topic",
  );
  assert.equal(inferArticleFolder("/repo/content/inbox/media/source-slug"), "");
});

test("planOutputDirectory writes article derivatives under assets/video-clips", () => {
  assert.equal(
    planOutputDirectory({
      articleFolder: "/repo/content/drafts/topic",
      target: "",
      slug: "demo",
    }),
    path.join("/repo/content/drafts/topic", "assets", "video-clips", "demo"),
  );
  assert.equal(
    planOutputDirectory({
      articleFolder: "",
      target: "/repo/out",
      slug: "demo",
    }),
    path.join("/repo/out", "assets", "video-clips", "demo"),
  );
});

test("findMediaFile picks media file and ignores metadata", () => {
  assert.equal(findMediaFile(["manifest.json", "sources.md", "media.mp4"]), "media.mp4");
  assert.equal(findMediaFile(["manifest.json", "thumbnail.jpg"]), "");
});

test("buildFfmpegArgs creates trim and crop command", () => {
  const args = buildFfmpegArgs({
    input: "/repo/source/media.mp4",
    output: "/repo/out/hyperframes/assets/source-clip.mp4",
    startSeconds: 12,
    endSeconds: 38,
    preset: getPreset("wechat-portrait"),
    focus: "left",
  });

  assert.deepEqual(args.slice(0, 4), ["-y", "-ss", "12", "-to"]);
  assert.equal(args[4], "38");
  assert.ok(args.includes("/repo/source/media.mp4"));
  assert.ok(args.includes("-vf"));
  assert.match(args[args.indexOf("-vf") + 1], /crop=1080:1920:0:/);
  assert.equal(args.at(-1), "/repo/out/hyperframes/assets/source-clip.mp4");
});

test("createClipManifest preserves source provenance and clip settings", () => {
  const manifest = createClipManifest({
    sourceManifest: {
      original_url: "https://example.com/watch/1",
      canonical_url: "https://example.com/canonical",
      title: "Source Title",
      uploader: "Author",
      platform: "Example",
    },
    materialPath: "/repo/article/assets/media/source",
    manifestPath: "/repo/article/assets/media/source/manifest.json",
    start: "00:12",
    end: "00:38",
    preset: getPreset("wechat-landscape"),
    focus: "center",
    style: "impact-rational",
    title: "Clip Title",
    caption: "Clip caption",
    outputFiles: ["final.mp4", "notes.md"],
    generatedAt: "2026-06-08T00:00:00.000Z",
  });

  assert.equal(manifest.original_url, "https://example.com/watch/1");
  assert.equal(manifest.clip.title, "Clip Title");
  assert.equal(manifest.clip.start, "00:12");
  assert.equal(manifest.output.preset, "wechat-landscape");
  assert.deepEqual(manifest.output.files, ["final.mp4", "notes.md"]);
});

test("createNotesMarkdown includes source and WeChat boundary", () => {
  const notes = createNotesMarkdown({
    manifest: {
      clip: { title: "Clip Title", start: "00:12", end: "00:38" },
      original_url: "https://example.com/watch/1",
      source: { uploader: "Author", platform: "Example" },
    },
  });

  assert.match(notes, /# Article Video Clip/);
  assert.match(notes, /https:\/\/example.com\/watch\/1/);
  assert.match(notes, /Confirm rights, citation, and platform terms/);
  assert.match(notes, /wechat-publish-workflow/);
});

test("parseArgs requires material, timestamps, preset, and title", () => {
  const parsed = parseArgs([
    "--material",
    "/repo/article/assets/media/source",
    "--start",
    "00:12",
    "--end",
    "00:38",
    "--preset",
    "wechat-landscape",
    "--title",
    "Clip Title",
    "--caption",
    "Caption",
    "--focus",
    "right",
    "--style",
    "tech-blog",
    "--dry-run",
  ]);

  assert.equal(parsed.material, "/repo/article/assets/media/source");
  assert.equal(parsed.start, "00:12");
  assert.equal(parsed.end, "00:38");
  assert.equal(parsed.preset, "wechat-landscape");
  assert.equal(parsed.title, "Clip Title");
  assert.equal(parsed.caption, "Caption");
  assert.equal(parsed.focus, "right");
  assert.equal(parsed.style, "tech-blog");
  assert.equal(parsed.dryRun, true);

  assert.throws(() => parseArgs(["--material", "/repo/source"]), /Usage:/);
});

test("createClip dry run plans output without executing commands", async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), "article-video-clip-"));
  const article = path.join(temp, "content", "drafts", "topic");
  const material = path.join(article, "assets", "media", "source");
  await fs.mkdir(material, { recursive: true });
  await fs.writeFile(path.join(material, "media.mp4"), "fake media");
  await fs.writeFile(
    path.join(material, "manifest.json"),
    JSON.stringify(
      {
        original_url: "https://example.com/watch/1",
        canonical_url: "https://example.com/canonical",
        title: "Source Title",
        uploader: "Author",
        platform: "Example",
      },
      null,
      2,
    ),
  );
  await fs.writeFile(path.join(material, "sources.md"), "# Source\n");

  const calls = [];
  const result = await createClip({
    options: {
      material,
      target: "",
      start: "00:12",
      end: "00:38",
      preset: "wechat-landscape",
      title: "Clip Title",
      caption: "Caption",
      focus: "center",
      style: "impact-rational",
      dryRun: true,
    },
    runCommandFn: async (command, args) => {
      calls.push({ command, args });
      return { stdout: "", stderr: "" };
    },
    now: () => new Date("2026-06-08T00:00:00.000Z"),
  });

  assert.equal(calls.length, 0);
  assert.equal(result.dryRun, true);
  assert.equal(result.outputDirectory, path.join(article, "assets", "video-clips", "clip-title"));
  assert.equal(result.commands[0].command, "ffmpeg");
  assert.equal(result.commands[1].command, "npx");
  assert.deepEqual(result.manifest.clip, {
    title: "Clip Title",
    caption: "Caption",
    start: "00:12",
    end: "00:38",
  });
});

test("buildHyperframesHtml preserves clip audio by default", () => {
  const html = buildHyperframesHtml({
    preset: getPreset("wechat-landscape"),
    title: "Clip Title",
    caption: "Caption",
    sourceLabel: "Example / Author",
  });

  assert.match(html, /<video[^>]+src="assets\/source-clip\.mp4"/);
  assert.doesNotMatch(html, /\smuted\b/);
  assert.match(html, /data-volume="1"/);
});

test("buildHyperframesHtml emits current HyperFrames lint contract", () => {
  const html = buildHyperframesHtml({
    preset: getPreset("wechat-landscape"),
    title: "Clip Title",
    caption: "Caption",
    sourceLabel: "Example / Author",
  });

  assert.match(html, /id="root"/);
  assert.match(html, /data-composition-id="root"/);
  assert.match(html, /data-start="0"/);
  assert.match(html, /data-duration="999"/);
  assert.match(html, /id="source-video"/);
  assert.match(html, /data-has-audio="true"/);
  assert.match(html, /class="shade clip"/);
  assert.match(html, /class="title clip"/);
  assert.match(html, /window\.__timelines\["root"\] = tl/);
});
