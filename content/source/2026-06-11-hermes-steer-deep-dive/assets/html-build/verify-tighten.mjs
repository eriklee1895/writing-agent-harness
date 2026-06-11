// Verify the concision pass: surviving code blocks must be byte-identical to
// baseline, headings/mermaid/markers/citations preserved, and any removed block
// must still appear (by caption) elsewhere — i.e. only true duplicates dropped.
import { readFileSync } from 'node:fs';
const A = '/tmp/article.dedented.md';
const B = '/Users/eriklee/code/my_project/writing-agent-harness/content/source/2026-06-11-hermes-steer-deep-dive/article.md';
const rd = f => readFileSync(f, 'utf8');
const blocks = s => s.match(/```\w*\n[\s\S]*?```/g) || [];
const count = (s, re) => (s.match(re) || []).length;
const a = rd(A), b = rd(B);
const ba = blocks(a), bb = blocks(b);
const setA = new Set(ba), setB = new Set(bb);
const removed = ba.filter(x => !setB.has(x));
const altered = bb.filter(x => !setA.has(x)); // surviving block not in baseline => code changed (BAD)

console.log('metric            baseline   new');
console.log('h1                ', count(a, /^# /gm), '       ', count(b, /^# /gm));
console.log('h2                ', count(a, /^## /gm), '      ', count(b, /^## /gm));
console.log('mermaid blocks    ', count(a, /```mermaid/g), '       ', count(b, /```mermaid/g));
console.log('fenced blocks     ', ba.length, '      ', bb.length);
console.log('http(s) links     ', count(a, /https?:\/\//g), '      ', count(b, /https?:\/\//g));
console.log('"截至 2026"        ', count(a, /截至 2026/g), '       ', count(b, /截至 2026/g));
console.log('OUT-OF-BAND marker', count(a, /OUT-OF-BAND USER MESSAGE/g), '      ', count(b, /OUT-OF-BAND USER MESSAGE/g));
console.log('fact/inference tag', count(a, /\((?:fact|inference|speculation)/g), '      ', count(b, /\((?:fact|inference|speculation)/g));
console.log('chars (JS length) ', a.length, '  ', b.length, '  delta', b.length - a.length);
console.log('\nALTERED surviving code blocks (MUST be 0):', altered.length);
altered.forEach(x => console.log('  !! ' + x.split('\n')[0]));
console.log('\nREMOVED blocks (' + removed.length + ') — caption must survive elsewhere or be a subset:');
removed.forEach(x => { const cap = x.split('\n')[0]; console.log('  - ' + cap + '   | caption still present: ' + b.includes(cap)); });
