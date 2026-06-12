// Headless QA for report.html using system Chrome via puppeteer-core.
// Collects console/page errors, key element counts, "stuck hidden" reveal
// elements, and screenshots at several scroll depths + mobile.
import puppeteer from 'puppeteer-core';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..', '..');
const FILE = 'file://' + join(ROOT, 'report.html');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT = join(HERE, 'qa');
mkdirSync(OUT, { recursive: true });
const wait = (ms) => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb'],
});
const page = await browser.newPage();
const errors = [], warnings = [];
page.on('console', m => { const t = m.type(); if (t === 'error') errors.push(m.text()); else if (t === 'warning') warnings.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
await page.goto(FILE, { waitUntil: 'networkidle0', timeout: 90000 });
await wait(1200);

const counts = await page.evaluate(() => ({
  title: document.title,
  h2: document.querySelectorAll('.prose h2').length,
  svg: document.querySelectorAll('figure.diagram svg').length,
  insetImgs: document.querySelectorAll('figure.illustration img').length,
  heroImg: document.querySelectorAll('.hero-illustration img').length,
  navlinks: document.querySelectorAll('.toc a').length,
  tables: document.querySelectorAll('table').length,
  codeblocks: document.querySelectorAll('pre code').length,
  docHeight: document.documentElement.scrollHeight,
}));

// scroll through (triggers GSAP reveals) and screenshot at depths
const H = await page.evaluate(() => document.documentElement.scrollHeight);
const depths = [0, 0.16, 0.32, 0.48, 0.64, 0.80, 0.92, 1];
for (const p of depths) {
  await page.evaluate(y => window.scrollTo(0, y), Math.floor(H * p));
  await wait(650);
  await page.screenshot({ path: join(OUT, 'd-' + String(Math.round(p * 100)).padStart(2, '0') + '.png') });
}

// after full scroll-through, nothing with .reveal should remain at opacity 0
const stuckHidden = await page.evaluate(() =>
  Array.from(document.querySelectorAll('.reveal'))
    .filter(el => parseFloat(getComputedStyle(el).opacity) === 0).length);

// active nav after scrolling near a mid section
await page.evaluate(() => { const h = document.querySelectorAll('.prose h2')[4]; if (h) h.scrollIntoView(); });
await wait(700);
const activeNav = await page.evaluate(() => { const a = document.querySelector('.toc a.active'); return a ? a.textContent.trim() : null; });

// mobile
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1, isMobile: true });
await page.reload({ waitUntil: 'networkidle0' });
await wait(900);
const mobile = await page.evaluate(() => ({
  horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
  scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth,
}));
await page.screenshot({ path: join(OUT, 'm-top.png') });
await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight * 0.34));
await wait(600);
await page.screenshot({ path: join(OUT, 'm-mid.png') });

await browser.close();
console.log(JSON.stringify({ counts, stuckHidden, activeNav, mobile, errors, warnings: warnings.slice(0, 6) }, null, 2));
