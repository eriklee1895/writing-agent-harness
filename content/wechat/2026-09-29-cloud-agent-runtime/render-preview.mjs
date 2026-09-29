// Article-local rendering. Keep the shared renderer and other articles unchanged.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
const slug = path.basename(here);
const root = path.resolve(here, '../../..');
const source = path.join(root, 'content/origin', slug, 'index.md');
const channel = path.join(here, 'article.md');
const output = path.join(here, 'index.html');
let markdown = fs.readFileSync(source, 'utf8');
if (!markdown.startsWith('---\n') || !markdown.includes('status: draft\n')) {
  throw new Error('Expected the canonical draft frontmatter; review before rendering.');
}
markdown = markdown
  .replace('status: draft\n', `status: draft\nsource: "../../origin/${slug}/index.md"\n`)
  .replaceAll('(assets/', `(../../origin/${slug}/assets/`);
fs.writeFileSync(channel, markdown);

const rendered = spawnSync(process.execPath, [
  path.join(root, '.agents/skills/wechat-article-renderer/scripts/render-wechat-article.mjs'),
  channel, output, '--style', 'warm-editorial',
], { stdio: 'inherit' });
if (rendered.error) throw rendered.error;
if (rendered.status !== 0) process.exit(rendered.status ?? 1);

const tableLayouts = [
  { header: '比较维度', widths: [20, 40, 40], expectedRows: 8 },
  { header: '实现', widths: [20, 32, 48], expectedRows: 4 },
];
const applied = [];
let html = fs.readFileSync(output, 'utf8');
// Match only the shared renderer's flex-table sections, then scope by header.
html = html.replace(
  /<section\b[^>]*style="[^"]*border-top:1\.5px solid rgba\(0,0,0,\.10\);[^"]*"[^>]*>[\s\S]*?<\/section>/g,
  (table) => {
    const layout = tableLayouts.find(({ header }) => table.includes(`>${header}</div>`));
    if (!layout) return table;
    let cellCount = 0;
    const adjusted = table.replace(
      /<div style="([^"]*flex:0 0 (?:30|35)%[^"]*)">/g,
      (_cell, style) => {
        const columnIndex = cellCount++ % 3;
        const width = layout.widths[columnIndex];
        let cellStyle = style
          .replace(/width:(?:30|35)%;/g, `width:${width}%;`)
          .replace(/flex:0 0 (?:30|35)%;/g, `flex:0 0 ${width}%;`)
          .replace('padding:10px 10px;', `padding:10px ${columnIndex === 0 ? 5 : 7}px;`);
        if (columnIndex === 0) {
          cellStyle = cellStyle.replace('font-size:14px;', 'font-size:13px;') + ' white-space:nowrap;';
        }
        return `<div style="${cellStyle}">`;
      },
    );
    if (cellCount !== layout.expectedRows * 3) {
      throw new Error(`Unexpected table shape for ${layout.header}: ${cellCount} cells`);
    }
    applied.push(layout.header);
    return adjusted.replace('<section ', `<section data-table-layout="${layout.widths.join('-')}" `);
  },
);
if (applied.length !== tableLayouts.length || new Set(applied).size !== tableLayouts.length) {
  throw new Error(`Expected exactly two article tables; matched ${applied.join(', ')}`);
}
fs.writeFileSync(output, html);
console.log(JSON.stringify({ articleTableLayouts: tableLayouts.map(({ header, widths }) => ({ header, widths })) }));
