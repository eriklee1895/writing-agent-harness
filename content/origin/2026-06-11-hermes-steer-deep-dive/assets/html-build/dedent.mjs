// Dedent verbatim code excerpts in article.md to a clean baseline.
// Strips the common leading indentation from each fenced code block's body
// (preserving relative indentation), leaving the leading "# path.py:lines"
// caption line untouched. Skips ```mermaid blocks.
import { readFileSync, writeFileSync } from 'node:fs';

const p = process.argv[2];
let md = readFileSync(p, 'utf8');
const changed = [];

md = md.replace(/```(\w*)\n([\s\S]*?)```/g, (m, lang, body) => {
  if (lang === 'mermaid') return m;
  let lines = body.replace(/\n$/, '').split('\n');
  const capIdx = (lines[0] && /^#\s+\S+\.py(\b|:)/.test(lines[0])) ? 0 : -1;
  const code = lines.filter((l, i) => i !== capIdx && l.trim() !== '');
  if (!code.length) return m;
  const min = Math.min(...code.map(l => l.match(/^ */)[0].length));
  if (min > 0) {
    changed.push((capIdx === 0 ? lines[0] : '(no caption)') + '  -' + min + 'sp');
    lines = lines.map((l, i) => (i === capIdx || l.trim() === '') ? l : l.slice(min));
  }
  return '```' + lang + '\n' + lines.join('\n') + '\n```';
});

writeFileSync(p, md);
console.log('dedented ' + changed.length + ' block(s):\n' + changed.join('\n'));
