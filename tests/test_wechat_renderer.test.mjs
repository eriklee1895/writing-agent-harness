import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const renderer = path.join(repoRoot, ".agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs");

function render(markdown) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-renderer-"));
  const input = path.join(directory, "article.md");
  const output = path.join(directory, "index.html");
  fs.writeFileSync(input, markdown);
  const result = JSON.parse(execFileSync(process.execPath, [renderer, input, output, "--style", "agent-flow"], { encoding: "utf8" }));
  return { result, html: fs.readFileSync(output, "utf8") };
}

test("frontmatter-only articles retain their declared title", () => {
  const { result, html } = render('---\ntitle: "Frontmatter title"\n---\n');
  assert.equal(result.title, "Frontmatter title");
  assert.match(html, /Frontmatter title/);
  assert.doesNotMatch(html, /未命名文章/);
});

test("plain strong HTML becomes real bold instead of visible source", () => {
  const { html } = render("---\ntitle: Demo\n---\n# Demo\n\n价格是 <strong>159.31 美元</strong>。\n");
  assert.match(html, /<strong style=[^>]+>159\.31 美元<\/strong>/);
  assert.doesNotMatch(html, /&lt;strong&gt;/);
  assert.doesNotMatch(html, /&amp;lt;strong/);
});
