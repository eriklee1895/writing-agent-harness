import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const PRESETS = {
  "wechat-landscape": {
    name: "wechat-landscape",
    width: 1920,
    height: 1080,
    aspect: "16:9",
  },
  "wechat-portrait": {
    name: "wechat-portrait",
    width: 1080,
    height: 1920,
    aspect: "9:16",
  },
};

const DEFAULT_FOCUS = "center";
const DEFAULT_STYLE = "impact-rational";
const DEFAULT_SLUG = "article-video-clip";
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

export function getPreset(name) {
  const preset = PRESETS[name];
  if (!preset) {
    throw new Error(`Unknown preset: ${name}`);
  }
  return { ...preset };
}

export function buildClipSlug(value, fallback = DEFAULT_SLUG) {
  const cleaned = String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{Letter}\p{Number}]+/gu, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
  return cleaned || fallback;
}

export function inferArticleFolder(materialPath) {
  const normalized = path.resolve(materialPath);
  const parts = normalized.split(path.sep);
  const assetsIndex = parts.lastIndexOf("assets");
  if (assetsIndex === -1 || parts[assetsIndex + 1] !== "media" || parts.length <= assetsIndex + 2) {
    return "";
  }
  return parts.slice(0, assetsIndex).join(path.sep) || path.sep;
}

export function planOutputDirectory({ articleFolder, target, slug }) {
  const base = articleFolder || target;
  if (!base) {
    throw new Error("Cannot infer article folder. Pass --target.");
  }
  return path.join(path.resolve(base), "assets", "video-clips", slug);
}

export function findMediaFile(files) {
  return (
    files.find((file) => {
      const ext = path.extname(file).toLowerCase();
      return file.startsWith("media.") && MEDIA_EXTENSIONS.has(ext);
    }) || ""
  );
}

function cropExpression({ preset, focus }) {
  const horizontal = focus === "left" ? "0" : focus === "right" ? "iw-ow" : "(iw-ow)/2";
  return [
    `scale=${preset.width}:${preset.height}:force_original_aspect_ratio=increase`,
    `crop=${preset.width}:${preset.height}:${horizontal}:(ih-oh)/2`,
  ].join(",");
}

export function buildFfmpegArgs({ input, output, startSeconds, endSeconds, preset, focus }) {
  if (endSeconds <= startSeconds) {
    throw new Error("End timestamp must be greater than start timestamp");
  }
  return [
    "-y",
    "-ss",
    String(startSeconds),
    "-to",
    String(endSeconds),
    "-i",
    input,
    "-vf",
    cropExpression({ preset, focus }),
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-movflags",
    "+faststart",
    output,
  ];
}

export function createClipManifest({
  sourceManifest,
  materialPath,
  manifestPath,
  start,
  end,
  preset,
  focus,
  style,
  title,
  caption,
  outputFiles,
  generatedAt,
}) {
  return {
    schema_version: 1,
    original_url: sourceManifest.original_url || "",
    canonical_url: sourceManifest.canonical_url || sourceManifest.original_url || "",
    source: {
      title: sourceManifest.title || "",
      uploader: sourceManifest.uploader || "",
      platform: sourceManifest.platform || "",
      material_path: materialPath,
      manifest_path: manifestPath,
    },
    clip: {
      title,
      caption: caption || "",
      start,
      end,
    },
    output: {
      preset: preset.name,
      width: preset.width,
      height: preset.height,
      aspect: preset.aspect,
      focus,
      style,
      files: outputFiles,
    },
    generated_at: generatedAt,
    intended_use: "article embed / WeChat draft review",
  };
}

export function createNotesMarkdown({ manifest }) {
  return [
    "# Article Video Clip",
    "",
    `- Title: ${manifest.clip.title}`,
    `- Source URL: ${manifest.original_url}`,
    `- Source uploader: ${manifest.source.uploader || "Unknown"}`,
    `- Source platform: ${manifest.source.platform || "Unknown"}`,
    `- Time range: ${manifest.clip.start} -> ${manifest.clip.end}`,
    "",
    "## Review Note",
    "",
    "Confirm rights, citation, and platform terms before publication or redistribution.",
    "",
    "WeChat upload and insertion are handled by `wechat-publish-workflow`, not this skill.",
    "",
  ].join("\n");
}

export function parseArgs(argv) {
  const options = {
    material: "",
    target: "",
    start: "",
    end: "",
    preset: "",
    title: "",
    caption: "",
    focus: DEFAULT_FOCUS,
    style: DEFAULT_STYLE,
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--material") {
      options.material = argv[++index] || "";
    } else if (arg === "--target") {
      options.target = argv[++index] || "";
    } else if (arg === "--start") {
      options.start = argv[++index] || "";
    } else if (arg === "--end") {
      options.end = argv[++index] || "";
    } else if (arg === "--preset") {
      options.preset = argv[++index] || "";
    } else if (arg === "--title") {
      options.title = argv[++index] || "";
    } else if (arg === "--caption") {
      options.caption = argv[++index] || "";
    } else if (arg === "--focus") {
      options.focus = argv[++index] || "";
    } else if (arg === "--style") {
      options.style = argv[++index] || "";
    } else if (arg === "--dry-run") {
      options.dryRun = true;
    } else if (arg === "--help" || arg === "-h") {
      throw new Error(usage());
    } else {
      throw new Error(`Unknown option: ${arg}\n\n${usage()}`);
    }
  }

  if (!options.material || !options.start || !options.end || !options.preset || !options.title) {
    throw new Error(usage());
  }
  if (!["left", "center", "right"].includes(options.focus)) {
    throw new Error("--focus must be left, center, or right");
  }
  getPreset(options.preset);

  return options;
}

export function usage() {
  return [
    "Usage:",
    "  node .agents/skills/article-video-clip/scripts/create-article-video-clip.mjs --material <material-dir> --start <time> --end <time> --preset <wechat-landscape|wechat-portrait> --title <title> [--caption <text>] [--focus left|center|right] [--style impact-rational] [--target <article-folder>] [--dry-run]",
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function buildHyperframesHtml({ preset, title, caption, sourceLabel, durationSeconds = 999 }) {
  const safeTitle = escapeHtml(title);
  const safeCaption = escapeHtml(caption);
  const safeSource = escapeHtml(sourceLabel);
  const duration = Number(durationSeconds) > 0 ? Number(durationSeconds) : 999;
  const captionHtml = safeCaption
    ? `<div id="caption" class="caption clip" data-start="0" data-duration="${duration}" data-track-index="3">${safeCaption}</div>`
    : "";
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${safeTitle}</title>
    <style>
      html,
      body {
        margin: 0;
        width: 100%;
        height: 100%;
        background: #101214;
        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Segoe UI", sans-serif;
      }
      [data-composition-id="root"] {
        position: relative;
        overflow: hidden;
        background: #101214;
      }
      video {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      .shade {
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(0,0,0,.62), rgba(0,0,0,0) 30%, rgba(0,0,0,.7));
        z-index: 2;
        pointer-events: none;
      }
      .title {
        position: absolute;
        left: 6%;
        right: 6%;
        top: 6%;
        z-index: 3;
        color: #fff;
        font-size: ${preset.width > preset.height ? "64px" : "54px"};
        font-weight: 750;
        line-height: 1.12;
        letter-spacing: 0;
        text-shadow: 0 2px 18px rgba(0,0,0,.45);
      }
      .caption {
        position: absolute;
        left: 6%;
        right: 6%;
        bottom: 11%;
        z-index: 3;
        color: #f4f0e8;
        font-size: ${preset.width > preset.height ? "34px" : "38px"};
        line-height: 1.28;
        text-shadow: 0 2px 16px rgba(0,0,0,.5);
      }
      .source {
        position: absolute;
        left: 6%;
        right: 6%;
        bottom: 4%;
        z-index: 3;
        color: rgba(255,255,255,.72);
        font-size: ${preset.width > preset.height ? "22px" : "24px"};
        line-height: 1.25;
        text-shadow: 0 2px 12px rgba(0,0,0,.55);
      }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="root" data-start="0" data-duration="${duration}" data-width="${preset.width}" data-height="${preset.height}">
      <video id="source-video" src="assets/source-clip.mp4" data-start="0" data-track-index="0" data-volume="1" data-has-audio="true" playsinline></video>
      <div id="shade" class="shade clip" data-start="0" data-duration="${duration}" data-track-index="1"></div>
      <div id="title" class="title clip" data-start="0" data-duration="${duration}" data-track-index="2">${safeTitle}</div>
      ${captionHtml}
      <div id="source" class="source clip" data-start="0" data-duration="${duration}" data-track-index="4">${safeSource}</div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      window.__timelines["root"] = tl;
    </script>
  </body>
</html>
`;
}

function buildCommandPlan({ ffmpegArgs, hyperframesDirectory, finalPath, previewPath }) {
  return [
    { command: "ffmpeg", args: ffmpegArgs },
    { command: "npx", args: ["hyperframes", "lint", "."], cwd: hyperframesDirectory },
    { command: "npx", args: ["hyperframes", "inspect", "."], cwd: hyperframesDirectory },
    {
      command: "npx",
      args: ["hyperframes", "render", "--output", finalPath],
      cwd: hyperframesDirectory,
    },
    { command: "ffmpeg", args: ["-y", "-ss", "1", "-i", finalPath, "-frames:v", "1", previewPath] },
  ];
}

export async function createClip({ options, runCommandFn = runCommand, now = () => new Date() }) {
  const materialPath = path.resolve(options.material);
  const materialFiles = await listFiles(materialPath);
  const mediaFile = findMediaFile(materialFiles);
  if (!mediaFile) {
    throw new Error(`No media file found in ${materialPath}`);
  }

  const manifestPath = path.join(materialPath, "manifest.json");
  const sourceManifest = await readJson(manifestPath);
  const preset = getPreset(options.preset);
  const startSeconds = parseTimestamp(options.start);
  const endSeconds = parseTimestamp(options.end);
  const slug = buildClipSlug(options.title);
  const articleFolder = inferArticleFolder(materialPath);
  const outputDirectory = planOutputDirectory({
    articleFolder,
    target: options.target,
    slug,
  });
  const hyperframesDirectory = path.join(outputDirectory, "hyperframes");
  const hyperframesAssetsDirectory = path.join(hyperframesDirectory, "assets");
  const intermediatePath = path.join(hyperframesAssetsDirectory, "source-clip.mp4");
  const finalPath = path.join(outputDirectory, "final.mp4");
  const previewPath = path.join(outputDirectory, "preview-frame.jpg");
  const notesPath = path.join(outputDirectory, "notes.md");
  const clipManifestPath = path.join(outputDirectory, "clip-manifest.json");
  const sourceLabel = [sourceManifest.platform, sourceManifest.uploader].filter(Boolean).join(" / ");
  const ffmpegArgs = buildFfmpegArgs({
    input: path.join(materialPath, mediaFile),
    output: intermediatePath,
    startSeconds,
    endSeconds,
    preset,
    focus: options.focus,
  });
  const commands = buildCommandPlan({
    ffmpegArgs,
    hyperframesDirectory,
    finalPath,
    previewPath,
  });
  const clipManifest = createClipManifest({
    sourceManifest,
    materialPath,
    manifestPath,
    start: options.start,
    end: options.end,
    preset,
    focus: options.focus,
    style: options.style,
    title: options.title,
    caption: options.caption,
    outputFiles: ["final.mp4", "clip-manifest.json", "notes.md", "preview-frame.jpg"],
    generatedAt: now().toISOString(),
  });

  if (options.dryRun) {
    return {
      dryRun: true,
      outputDirectory,
      commands,
      manifest: clipManifest,
    };
  }

  await fs.mkdir(hyperframesAssetsDirectory, { recursive: true });
  await runCommandFn("ffmpeg", ffmpegArgs);
  await fs.writeFile(
    path.join(hyperframesDirectory, "index.html"),
    buildHyperframesHtml({
      preset,
      title: options.title,
      caption: options.caption,
      sourceLabel: sourceLabel || sourceManifest.original_url || "",
      durationSeconds: endSeconds - startSeconds,
    }),
  );

  for (const planned of commands.slice(1)) {
    await runCommandFn(planned.command, planned.args, { cwd: planned.cwd });
  }

  await fs.writeFile(clipManifestPath, `${JSON.stringify(clipManifest, null, 2)}\n`);
  await fs.writeFile(notesPath, createNotesMarkdown({ manifest: clipManifest }));

  return {
    dryRun: false,
    outputDirectory,
    finalPath,
    manifestPath: clipManifestPath,
    notesPath,
  };
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const result = await createClip({ options });
  if (result.dryRun) {
    console.log(`Dry run: ${result.manifest.clip.title}`);
    console.log(`Target: ${result.outputDirectory}`);
    for (const command of result.commands) {
      console.log(`Command: ${command.command} ${command.args.join(" ")}`);
    }
  } else {
    console.log(`Saved: ${result.finalPath}`);
    console.log(`Manifest: ${result.manifestPath}`);
    console.log(`Notes: ${result.notesPath}`);
  }
}

const isCli = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (isCli) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
