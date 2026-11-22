// Captions for the M-65 patch reel, in the style of the Red Wing 2268 review
// (Gowun Batang Bold, warm white, soft shadow, centered). Usage: node overlays.mjs <out dir>
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

const out = process.argv[2] || join(HERE, "build", "overlays");
const font = pathToFileURL(join(HERE, "..", "boot-ritual", "fonts", "GowunBatang-Bold.ttf")).href;
const css = `@font-face{font-family:GB;font-weight:700;src:url(${font})}
*{margin:0;padding:0}html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
.in{position:absolute;left:80px;width:920px;top:1230px;text-align:center;font-family:GB;font-weight:700;color:#fffaf0;
  text-shadow:0 0 2px rgba(0,0,0,.95),0 0 6px rgba(0,0,0,.75),0 3px 16px rgba(0,0,0,.6)}
.main{font-size:60px;line-height:1.3;letter-spacing:-.01em}
.sub{margin-top:14px;font-size:42px;opacity:.95}
.title .main{font-size:92px;line-height:1.18;letter-spacing:-.02em}
.title .sub{margin-top:24px;font-size:42px}`;

// Edit the wording here. Each key is used by one shot in build.sh.
export const CAPTIONS = {
  title: { cls: "title", main: "M-65 Fishtail", sub: "feat. an original 2ID patch" },
  why: { main: "It looked too plain.", sub: "It needed a patch." },
  which: { main: "2nd Infantry Division", sub: "The “Indianhead”" },
  korea: { main: "The US division", sub: "stationed in Korea" },
  original: { main: "Original, not a repro.", sub: "Hard to find. Tracked one down overseas." },
  label: { main: "The parka: 1971 contract", sub: "Alpha Industries" },
  spot: { main: "Left shoulder,", sub: "where the unit patch goes." },
  end: { main: "Patch or no patch?" },
};

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
for (const [name, c] of Object.entries(CAPTIONS)) {
  const html = resolve(out, `${name}.html`);
  const body = `<div class="in ${c.cls || ""}"><div class="main">${c.main}</div>${c.sub ? `<div class="sub">${c.sub}</div>` : ""}</div>`;
  writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${css}</style>${body}`);
  await page.goto(pathToFileURL(html).href);
  await page.evaluate(() => document.fonts.ready);
  if (await page.evaluate(() => [...document.fonts].some((f) => f.status === "error"))) throw new Error("font failed to load");
  await page.screenshot({ path: resolve(out, `${name}.png`), omitBackground: true });
  unlinkSync(html);
}
await browser.close();
console.log(`overlays → ${out}`);
