// Transparent 1080x1920 text overlays for the boot-ritual reel (editorial style:
// Instrument Serif italic + Space Mono, same look as reels/workweek-ootd).
// Usage: node overlays.mjs <out dir>
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = require(join(execSync("npm root -g").toString().trim(), "playwright"))); }

const FONTS = pathToFileURL(join(HERE, "..", "workweek-ootd", "fonts")).href;
const out = process.argv[2] || join(HERE, "build", "overlays");

const css = `
@font-face{font-family:IS;font-style:italic;src:url(${FONTS}/instrument-serif-latin-400-italic.woff2)}
@font-face{font-family:SM;src:url(${FONTS}/space-mono-latin-400-normal.woff2)}
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
body{position:relative;color:#fff;-webkit-font-smoothing:antialiased}.abs{position:absolute}
.sh{text-shadow:0 2px 24px rgba(0,0,0,.55),0 1px 4px rgba(0,0,0,.5)}
.mono{font-family:SM;font-size:32px;letter-spacing:.14em;text-transform:uppercase}
.serif{font-family:IS;font-style:italic;line-height:.9;letter-spacing:-.01em}`;

const step = (n, word) => `
  <div class="abs sh mono" style="left:84px;top:270px;opacity:.9">(${n}/03) &nbsp;before work</div>
  <div class="abs sh serif" style="left:72px;top:318px;font-size:200px">${word}</div>`;

const shots = {
  hook: `
    <div class="abs sh serif" style="left:0;right:0;top:330px;text-align:center;font-size:150px">before work,</div>
    <div class="abs sh mono" style="left:0;right:0;top:500px;text-align:center">my morning boot ritual</div>`,
  brush: step("01", "brush."),
  wear: step("02", "wear."),
  go: step("03", "go."),
  end: `
    <div class="abs sh serif" style="left:0;right:0;top:330px;text-align:center;font-size:150px">see you<br>tomorrow.</div>
    <div class="abs sh mono" style="left:0;right:0;top:640px;text-align:center">brush · wear · go</div>`,
};

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
for (const [name, body] of Object.entries(shots)) {
  const html = resolve(out, `${name}.html`);
  writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${css}</style><body>${body}</body>`);
  await page.goto(pathToFileURL(html).href);
  await page.evaluate(() => document.fonts.ready);
  const bad = await page.evaluate(() => [...document.fonts].filter((f) => f.status === "error").map((f) => f.family));
  if (bad.length) throw new Error(`fonts failed to load: ${bad}`);
  await page.screenshot({ path: resolve(out, `${name}.png`), omitBackground: true });
  unlinkSync(html);
}
await browser.close();
console.log(`overlays → ${out}`);
