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

async function getYtDlpVersion({ runCommandFn = runCommand } = {}) {
  const result = await runCommandFn("yt-dlp", ["--version"]);
  return result.stdout.trim();
}

async function getVideoInfo({ url, cookiesFromBrowser, runCommandFn = runCommand }) {
  const args = buildYtDlpArgs({
    url,
    outputTemplate: "%(title)s.%(ext)s",
    cookiesFromBrowser,
    dumpJson: true,
  });
  const result = await runCommandFn("yt-dlp", args);
  return JSON.parse(result.stdout);
}

async function listRelativeFiles(directory) {
  const entries = await fs.readdir(directory);
  return entries.sort();
}

export async function ingestOne({
  url,
  options,
  cwd,
  today,
  runCommandFn = runCommand,
  now = () => new Date(),
}) {
  const info = await getVideoInfo({
    url,
    cookiesFromBrowser: options.cookiesFromBrowser,
    runCommandFn,
  });
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

  await runCommandFn("yt-dlp", downloadArgs);

  const filesBeforeManifest = await listRelativeFiles(outputDirectory);
  const infoFile = filesBeforeManifest.find((file) => file.endsWith(".info.json"));
  if (infoFile) {
    await fs.rename(path.join(outputDirectory, infoFile), path.join(outputDirectory, "info.json"));
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
    ytDlpVersion: await getYtDlpVersion({ runCommandFn }),
    cookiesFromBrowser: options.cookiesFromBrowser,
    audioOnly: options.audioOnly,
    downloadedAt: now().toISOString(),
  });

  await fs.writeFile(path.join(outputDirectory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  await fs.writeFile(path.join(outputDirectory, "sources.md"), createSourcesMarkdown({ manifest }));

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
      if (result.platform) {
        console.log(`Platform: ${result.platform}`);
      }
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
