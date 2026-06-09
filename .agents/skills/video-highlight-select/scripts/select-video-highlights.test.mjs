import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  buildContactSheetArgs,
  createContactSheetIndex,
  createHighlightCandidates,
  createHighlightsJson,
  createHighlightsMarkdown,
  formatTimestamp,
  parseArgs,
  parseCandidate,
  parseTimestamp,
  planOutputDirectory,
} from "./select-video-highlights.mjs";

test("parseTimestamp supports seconds, mm:ss, and hh:mm:ss", () => {
  assert.equal(parseTimestamp("12.5"), 12.5);
  assert.equal(parseTimestamp("01:02"), 62);
  assert.equal(parseTimestamp("01:02:03"), 3723);
});

test("formatTimestamp emits compact hh:mm:ss style timestamps", () => {
  assert.equal(formatTimestamp(8), "00:08");
  assert.equal(formatTimestamp(68.4), "01:08.400");
  assert.equal(formatTimestamp(3723), "01:02:03");
});

test("parseCandidate accepts range, title, caption, and preset", () => {
  assert.deepEqual(parseCandidate("00:03-00:11|曲裾入场|素材再包装|wechat-landscape"), {
    start: "00:03",
    end: "00:11",
    title: "曲裾入场",
    caption: "素材再包装",
    preset: "wechat-landscape",
    notes: "",
  });
  assert.throws(() => parseCandidate("00:11-00:03|bad"), /end must be greater/i);
});

test("planOutputDirectory writes highlight workspace inside material package by default", () => {
  assert.equal(
    planOutputDirectory({
      materialPath: "/repo/content/drafts/topic/assets/media/source",
      target: "",
    }),
    path.join("/repo/content/drafts/topic/assets/media/source", "highlight-select"),
  );
  assert.equal(
    planOutputDirectory({ materialPath: "/repo/source", target: "/repo/out" }),
    "/repo/out",
  );
});

test("buildContactSheetArgs samples source video into a single sheet", () => {
  const args = buildContactSheetArgs({
    input: "/repo/source/media.mp4",
    output: "/repo/source/highlight-select/contact-sheet.jpg",
    durationSeconds: 120,
    frameCount: 12,
    columns: 4,
  });

  assert.deepEqual(args.slice(0, 3), ["-y", "-i", "/repo/source/media.mp4"]);
  assert.match(args[args.indexOf("-vf") + 1], /fps=1\/10/);
  assert.match(args[args.indexOf("-vf") + 1], /tile=4x3/);
  assert.equal(args.at(-1), "/repo/source/highlight-select/contact-sheet.jpg");
});

test("createContactSheetIndex maps row-major cells to timestamps", () => {
  assert.deepEqual(createContactSheetIndex({ durationSeconds: 120, frameCount: 4, columns: 2 }), [
    { index: 1, row: 1, column: 1, timestamp: "00:00" },
    { index: 2, row: 1, column: 2, timestamp: "00:30" },
    { index: 3, row: 2, column: 1, timestamp: "01:00" },
    { index: 4, row: 2, column: 2, timestamp: "01:30" },
  ]);
});

test("createHighlightsMarkdown includes article intent and article-video-clip handoff", () => {
  const markdown = createHighlightsMarkdown({
    sourceManifest: {
      title: "Source Title",
      original_url: "https://example.com/video",
      platform: "Bilibili",
      uploader: "Author",
    },
    media: {
      file: "media.mp4",
      duration_seconds: 120,
      width: 1920,
      height: 1080,
      has_audio: true,
    },
    materialPath: "/repo/source",
    intent: "放在文章开头抓人",
    contactSheet: "contact-sheet.jpg",
    contactSheetIndex: createContactSheetIndex({ durationSeconds: 120, frameCount: 4, columns: 2 }),
    candidates: [
      {
        start: "00:03",
        end: "00:11",
        title: "曲裾入场",
        caption: "素材再包装",
        preset: "wechat-landscape",
        notes: "",
      },
    ],
  });

  assert.match(markdown, /# Video Highlight Select/);
  assert.match(markdown, /放在文章开头抓人/);
  assert.match(markdown, /contact-sheet\.jpg/);
  assert.match(markdown, /\| 1 \| 1 \| 1 \| 00:00 \|/);
  assert.match(markdown, /article-video-clip/);
  assert.match(markdown, /--material \/repo\/source/);
  assert.match(markdown, /--start 00:03 --end 00:11/);
});

test("createHighlightsJson preserves manual candidates", () => {
  const json = createHighlightsJson({
    sourceManifest: { original_url: "https://example.com/video", title: "Source Title" },
    materialPath: "/repo/source",
    media: { file: "media.mp4", duration_seconds: 120 },
    intent: "文章开头",
    contactSheet: "contact-sheet.jpg",
    contactSheetIndex: createContactSheetIndex({ durationSeconds: 120, frameCount: 4, columns: 2 }),
    candidates: [{ start: "00:03", end: "00:11", title: "A", caption: "", preset: "wechat-landscape" }],
    generatedAt: "2026-06-08T00:00:00.000Z",
  });

  assert.equal(json.intent, "文章开头");
  assert.equal(json.review_assets.contact_sheet_index[1].timestamp, "00:30");
  assert.equal(json.candidates[0].title, "A");
  assert.equal(json.next_step.skill, "article-video-clip");
});

test("parseArgs supports dry-run and repeated candidates", () => {
  const parsed = parseArgs([
    "--material",
    "/repo/source",
    "--intent",
    "文章开头",
    "--candidate",
    "00:03-00:11|A",
    "--candidate",
    "00:20-00:30|B|说明|wechat-portrait",
    "--dry-run",
  ]);

  assert.equal(parsed.material, "/repo/source");
  assert.equal(parsed.intent, "文章开头");
  assert.equal(parsed.candidates.length, 2);
  assert.equal(parsed.dryRun, true);
});

test("createHighlightCandidates dry run plans without running commands", async () => {
  const temp = await fs.mkdtemp(path.join(os.tmpdir(), "video-highlight-select-"));
  const material = path.join(temp, "assets", "media", "source");
  await fs.mkdir(material, { recursive: true });
  await fs.writeFile(path.join(material, "media.mp4"), "fake media");
  await fs.writeFile(
    path.join(material, "manifest.json"),
    JSON.stringify({ original_url: "https://example.com/video", title: "Source Title" }, null, 2),
  );
  await fs.writeFile(path.join(material, "sources.md"), "# Source\n");

  const calls = [];
  const result = await createHighlightCandidates({
    options: {
      material,
      target: "",
      intent: "文章开头",
      frameCount: 12,
      columns: 4,
      candidates: [parseCandidate("00:03-00:11|A")],
      dryRun: true,
    },
    runCommandFn: async (command, args) => {
      calls.push({ command, args });
      return { stdout: "", stderr: "" };
    },
    probeMediaFn: async () => ({
      file: "media.mp4",
      duration_seconds: 120,
      width: 1920,
      height: 1080,
      has_audio: true,
    }),
  });

  assert.equal(calls.length, 0);
  assert.equal(result.dryRun, true);
  assert.equal(result.outputDirectory, path.join(material, "highlight-select"));
  assert.equal(result.commands[0].command, "ffmpeg");
  assert.equal(result.candidates.length, 1);
});
