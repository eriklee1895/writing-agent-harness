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
    intended_use: "research / writing material / visual reference / future short-video material",
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
