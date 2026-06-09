import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const DEFAULT_FRAME_COUNT = 12;
const DEFAULT_COLUMNS = 4;
const DEFAULT_PRESET = "wechat-landscape";
const MEDIA_EXTENSIONS = new Set([".mp4", ".mov", ".m4v", ".webm", ".mkv"]);

export function parseTimestamp(value) {
  const text = String(value || "").trim();
  if (!text) {
    throw new Error("Timestamp is required");
  }
  const parts = text.split(":").map((part) => Number(part));
  if (parts.some((part) => Number.isNaN(part))) {
    throw new Error(`Invalid timestamp: ${value}`);
  }
  if (parts.length === 1) {
    return parts[0];
  }
  if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  }
  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }
  throw new Error(`Invalid timestamp: ${value}`);
}

export function formatTimestamp(seconds) {
  const value = Number(seconds);
  if (!Number.isFinite(value) || value < 0) {
    throw new Error(`Invalid seconds: ${seconds}`);
  }
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const wholeSeconds = Math.floor(value % 60);
  const milliseconds = Math.round((value - Math.floor(value)) * 1000);
  const suffix = milliseconds ? `.${String(milliseconds).padStart(3, "0")}` : "";
  const mm = String(minutes).padStart(2, "0");
  const ss = `${String(wholeSeconds).padStart(2, "0")}${suffix}`;
  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${mm}:${ss}`;
  }
  return `${mm}:${ss}`;
}

export function parseCandidate(value) {
  const [range = "", title = "", caption = "", preset = DEFAULT_PRESET, notes = ""] = String(value)
    .split("|")
    .map((part) => part.trim());
  const [start = "", end = ""] = range.split("-").map((part) => part.trim());
  if (!start || !end || !title) {
    throw new Error("Candidate format: start-end|title|caption|preset|notes");
  }
  if (parseTimestamp(end) <= parseTimestamp(start)) {
    throw new Error("Candidate end must be greater than start");
  }
  return {
    start,
    end,
    title,
    caption,
    preset: preset || DEFAULT_PRESET,
    notes,
  };
}

export function planOutputDirectory({ materialPath, target }) {
  if (target) {
    return path.resolve(target);
  }
  return path.join(path.resolve(materialPath), "highlight-select");
}

export function findMediaFile(files) {
  return (
    files.find((file) => {
      const ext = path.extname(file).toLowerCase();
      return file.startsWith("media.") && MEDIA_EXTENSIONS.has(ext);
    }) || ""
  );
}

export function buildContactSheetArgs({
  input,
  output,
  durationSeconds,
  frameCount = DEFAULT_FRAME_COUNT,
  columns = DEFAULT_COLUMNS,
}) {
  const safeFrameCount = Math.max(1, Number(frameCount) || DEFAULT_FRAME_COUNT);
  const safeColumns = Math.max(1, Number(columns) || DEFAULT_COLUMNS);
  const rows = Math.max(1, Math.ceil(safeFrameCount / safeColumns));
  const interval = Math.max(1, Math.floor((Number(durationSeconds) || safeFrameCount) / safeFrameCount));
  const filter = [`fps=1/${interval}`, "scale=360:-1", `tile=${safeColumns}x${rows}`].join(",");
  return ["-y", "-i", input, "-vf", filter, "-frames:v", "1", output];
}

export function createContactSheetIndex({
  durationSeconds,
  frameCount = DEFAULT_FRAME_COUNT,
  columns = DEFAULT_COLUMNS,
}) {
  const safeFrameCount = Math.max(1, Number(frameCount) || DEFAULT_FRAME_COUNT);
  const safeColumns = Math.max(1, Number(columns) || DEFAULT_COLUMNS);
  const interval = Math.max(1, Math.floor((Number(durationSeconds) || safeFrameCount) / safeFrameCount));
  return Array.from({ length: safeFrameCount }, (_, index) => ({
    index: index + 1,
    row: Math.floor(index / safeColumns) + 1,
    column: (index % safeColumns) + 1,
    timestamp: formatTimestamp(index * interval),
  }));
}

export function createHighlightsJson({
  sourceManifest,
  materialPath,
  media,
  intent,
  contactSheet,
  contactSheetIndex = [],
  candidates,
  generatedAt,
}) {
  return {
    schema_version: 1,
    generated_at: generatedAt,
    intent: intent || "",
    source: {
      title: sourceManifest.title || "",
      original_url: sourceManifest.original_url || "",
      canonical_url: sourceManifest.canonical_url || sourceManifest.original_url || "",
      platform: sourceManifest.platform || "",
      uploader: sourceManifest.uploader || "",
      material_path: materialPath,
    },
    media,
    review_assets: {
      contact_sheet: contactSheet,
      contact_sheet_index: contactSheetIndex,
    },
    candidates,
    next_step: {
      skill: "article-video-clip",
      instruction: "After the user confirms a candidate, pass its start/end/title/caption/preset to article-video-clip.",
    },
  };
}

function candidateRows(candidates) {
  if (candidates.length === 0) {
    return [
      "| 1 |  |  |  |  | wechat-landscape |  |",
      "| 2 |  |  |  |  | wechat-landscape |  |",
      "| 3 |  |  |  |  | wechat-landscape |  |",
    ].join("\n");
  }
  return candidates
    .map(
      (candidate, index) =>
        `| ${index + 1} | ${candidate.start} | ${candidate.end} | ${candidate.title} | ${candidate.caption || ""} | ${candidate.preset || DEFAULT_PRESET} | ${candidate.notes || ""} |`,
    )
    .join("\n");
}

export function createHighlightsMarkdown({
  sourceManifest,
  media,
  materialPath,
  intent,
  contactSheet,
  contactSheetIndex = [],
  candidates,
}) {
  const firstCandidate = candidates[0];
  const handoff = firstCandidate
    ? [
        "```bash",
        "node .agents/skills/article-video-clip/scripts/create-article-video-clip.mjs \\",
        `  --material ${materialPath || "<material-package>"} \\`,
        `  --start ${firstCandidate.start} --end ${firstCandidate.end} \\`,
        `  --preset ${firstCandidate.preset || DEFAULT_PRESET} \\`,
        `  --title "${firstCandidate.title}" \\`,
        `  --caption "${firstCandidate.caption || ""}"`,
        "```",
      ].join("\n")
    : "After choosing a row, run `article-video-clip` with its start/end/title/caption/preset.";

  return [
    "# Video Highlight Select",
    "",
    `- Source title: ${sourceManifest.title || "Unknown"}`,
    `- Source URL: ${sourceManifest.original_url || ""}`,
    `- Source platform: ${sourceManifest.platform || "Unknown"}`,
    `- Source uploader: ${sourceManifest.uploader || "Unknown"}`,
    `- Media: ${media.file || "media"} / ${media.width || "?"}x${media.height || "?"} / ${formatTimestamp(media.duration_seconds || 0)} / audio=${media.has_audio ? "yes" : "no"}`,
    `- Article intent: ${intent || "Not specified"}`,
    "",
    "## Review Asset",
    "",
    `![Contact sheet](${contactSheet})`,
    "",
    "### Contact Sheet Index",
    "",
    "| # | row | column | approx timestamp |",
    "|---|-----|--------|------------------|",
    ...contactSheetIndex.map(
      (frame) => `| ${frame.index} | ${frame.row} | ${frame.column} | ${frame.timestamp} |`,
    ),
    "",
    "## Candidate Clips",
    "",
    "| # | start | end | title | caption | preset | notes |",
    "|---|-------|-----|-------|---------|--------|-------|",
    candidateRows(candidates),
    "",
    "## Handoff",
    "",
    handoff,
    "",
    "## Boundary",
    "",
    "This file helps a human choose highlights. It does not auto-select the best moment, render final video, or upload to WeChat.",
    "",
  ].join("\n");
}

export function parseArgs(argv) {
  const options = {
    material: "",
    target: "",
    intent: "",
    frameCount: DEFAULT_FRAME_COUNT,
    columns: DEFAULT_COLUMNS,
    candidates: [],
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--material") {
      options.material = argv[++index] || "";
    } else if (arg === "--target") {
      options.target = argv[++index] || "";
    } else if (arg === "--intent") {
      options.intent = argv[++index] || "";
    } else if (arg === "--frame-count") {
      options.frameCount = Number(argv[++index] || DEFAULT_FRAME_COUNT);
    } else if (arg === "--columns") {
      options.columns = Number(argv[++index] || DEFAULT_COLUMNS);
    } else if (arg === "--candidate") {
      options.candidates.push(parseCandidate(argv[++index] || ""));
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--help" || arg === "-h") {
      throw new Error(usage());
    } else {
      throw new Error(`Unknown option: ${arg}\n\n${usage()}`);
    }
  }

  if (!options.material) {
    throw new Error(usage());
  }
  return options;
}

export function usage() {
  return [
    "Usage:",
    "  node .agents/skills/video-highlight-select/scripts/select-video-highlights.mjs --material <material-dir> [--intent <text>] [--candidate '00:03-00:11|title|caption|preset|notes'] [--frame-count 12] [--columns 4] [--target <dir>] [--dry-run]",
  ].join("\n");
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
        reject(new Error(`Command failed (${code}): ${command} ${args.join(" ")}\n${stderr || stdout}`));
      }
    });
  });
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function listFiles(directory) {
  return (await fs.readdir(directory)).sort();
}

export async function probeMedia({ input, mediaFile, runCommandFn = runCommand }) {
  const result = await runCommandFn("ffprobe", [
    "-v",
    "error",
    "-show_entries",
    "stream=codec_type,width,height:format=duration",
    "-of",
    "json",
    input,
  ]);
  const data = JSON.parse(result.stdout);
  const video = (data.streams || []).find((stream) => stream.codec_type === "video") || {};
  const hasAudio = (data.streams || []).some((stream) => stream.codec_type === "audio");
  return {
    file: mediaFile,
    duration_seconds: Number(data.format?.duration || 0),
    width: video.width || 0,
    height: video.height || 0,
    has_audio: hasAudio,
  };
}

export async function createHighlightCandidates({
  options,
  runCommandFn = runCommand,
  probeMediaFn = probeMedia,
  now = () => new Date(),
}) {
  const materialPath = path.resolve(options.material);
  const materialFiles = await listFiles(materialPath);
  const mediaFile = findMediaFile(materialFiles);
  if (!mediaFile) {
    throw new Error(`No media file found in ${materialPath}`);
  }

  const manifestPath = path.join(materialPath, "manifest.json");
  const sourceManifest = await readJson(manifestPath);
  const mediaPath = path.join(materialPath, mediaFile);
  const outputDirectory = planOutputDirectory({ materialPath, target: options.target });
  const contactSheetName = "contact-sheet.jpg";
  const contactSheetPath = path.join(outputDirectory, contactSheetName);
  const media = await probeMediaFn({
    input: mediaPath,
    mediaFile,
    runCommandFn,
  });
  const contactSheetArgs = buildContactSheetArgs({
    input: mediaPath,
    output: contactSheetPath,
    durationSeconds: media.duration_seconds,
    frameCount: options.frameCount,
    columns: options.columns,
  });
  const contactSheetIndex = createContactSheetIndex({
    durationSeconds: media.duration_seconds,
    frameCount: options.frameCount,
    columns: options.columns,
  });
  const commands = [{ command: "ffmpeg", args: contactSheetArgs }];

  if (options.dryRun) {
    return {
      dryRun: true,
      outputDirectory,
      commands,
      media,
      contactSheetIndex,
      candidates: options.candidates,
    };
  }

  await fs.mkdir(outputDirectory, { recursive: true });
  await runCommandFn("ffmpeg", contactSheetArgs);

  const json = createHighlightsJson({
    sourceManifest,
    materialPath,
    media,
    intent: options.intent,
    contactSheet: contactSheetName,
    contactSheetIndex,
    candidates: options.candidates,
    generatedAt: now().toISOString(),
  });
  const markdown = createHighlightsMarkdown({
    sourceManifest,
    media,
    materialPath,
    intent: options.intent,
    contactSheet: contactSheetName,
    contactSheetIndex,
    candidates: options.candidates,
  });
  const jsonPath = path.join(outputDirectory, "highlight-candidates.json");
  const markdownPath = path.join(outputDirectory, "highlight-candidates.md");
  await fs.writeFile(jsonPath, `${JSON.stringify(json, null, 2)}\n`);
  await fs.writeFile(markdownPath, markdown);

  return {
    dryRun: false,
    outputDirectory,
    contactSheetPath,
    jsonPath,
    markdownPath,
  };
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const result = await createHighlightCandidates({ options });
  if (result.dryRun) {
    console.log(`Dry run: ${result.outputDirectory}`);
    for (const command of result.commands) {
      console.log(`Command: ${command.command} ${command.args.join(" ")}`);
    }
  } else {
    console.log(`Saved: ${result.markdownPath}`);
    console.log(`JSON: ${result.jsonPath}`);
    console.log(`Contact sheet: ${result.contactSheetPath}`);
  }
}

const isCli = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isCli) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
