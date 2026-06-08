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
