// Extract ```mermaid fenced blocks from article.md into separate .mmd files,
// in document order, so the rendered SVGs always match the canonical article.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const mdPath = process.argv[2];
const outDir = process.argv[3];
const md = readFileSync(mdPath, 'utf8');
mkdirSync(outDir, { recursive: true });

const names = ['01-semantics', '02-dataflow', '03-decision', '04-loop'];
const re = /```mermaid\n([\s\S]*?)```/g;
let m, i = 0;
while ((m = re.exec(md)) !== null) {
  const name = names[i] || `diagram-${i}`;
  writeFileSync(`${outDir}/${name}.mmd`, m[1].replace(/\s+$/, '') + '\n', 'utf8');
  i++;
}
console.log(`extracted ${i} mermaid block(s) to ${outDir}`);
if (i !== 4) console.error(`WARNING: expected 4 mermaid blocks, got ${i}`);
