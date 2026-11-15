// "Today's boots" title, styled like reels/boots-lacing (Gowun Batang Bold, warm white,
// soft shadow, centered near the top). Usage: node overlays.mjs <out dir>
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
const font = pathToFileURL(join(HERE, "fonts", "GowunBatang-Bold.ttf")).href;
const css = `@font-face{font-family:GB;font-weight:700;src:url(${font})}
*{margin:0;padding:0}html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
.t{position:absolute;left:0;right:0;top:322px;text-align:center;font-family:GB;font-weight:700;font-size:60px;
  color:#fffaf0;text-shadow:0 0 2px rgba(0,0,0,.6),0 2px 12px rgba(0,0,0,.45)}`;

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
const html = resolve(out, "title.html");
writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${css}</style><div class="t">Today's boots</div>`);
await page.goto(pathToFileURL(html).href);
await page.evaluate(() => document.fonts.ready);
if (await page.evaluate(() => [...document.fonts].some((f) => f.status === "error"))) throw new Error("font failed to load");
await page.screenshot({ path: resolve(out, "title.png"), omitBackground: true });
unlinkSync(html);
await browser.close();
console.log(`overlays → ${out}`);
