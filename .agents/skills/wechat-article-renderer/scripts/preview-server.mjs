#!/usr/bin/env node
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const PORT = parseInt(process.env.PORT || "49255", 10);
const ROOT = path.resolve(process.argv[2] || process.cwd());

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css",
  ".js": "application/javascript",
  ".mjs": "application/javascript",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
};

function serveFile(filePath, res) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME[ext] || "application/octet-stream";
  try {
    const data = fs.readFileSync(filePath);
    res.writeHead(200, { "Content-Type": contentType });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end("404 Not Found");
  }
}

const server = http.createServer((req, res) => {
  const rawPath = req.url.split("?")[0];
  let safePath;
  try {
    safePath = path.normalize(decodeURIComponent(rawPath)).replace(/^\/+/, "");
  } catch {
    res.writeHead(400);
    res.end("400 Bad Request");
    return;
  }
  let fullPath = path.join(ROOT, safePath);

  // Serve directory index
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    fullPath = path.join(fullPath, "index.html");
  }

  // Security: ensure the resolved path is within ROOT
  if (!path.resolve(fullPath).startsWith(path.resolve(ROOT))) {
    res.writeHead(403);
    res.end("403 Forbidden");
    return;
  }

  serveFile(fullPath, res);
});

server.listen(PORT, () => {
  console.log(`Preview: http://localhost:${PORT}/`);
  console.log(`Serving: ${ROOT}`);
  console.log("Press Ctrl+C to stop.");
});
