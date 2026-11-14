// Renders transparent 1080x1920 text overlays (PNG) for the work-week reel.
// Usage: node overlays.mjs <style: editorial|spec|bold> <out dir>
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import { mkdirSync, unlinkSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
// Playwright is installed globally in this environment; fall back to a local install.
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = require(join(execSync("npm root -g").toString().trim(), "playwright"))); }
const FONTS = pathToFileURL(join(HERE, "fonts")).href;
const [style = "editorial", out = join(HERE, "build", "overlays")] = process.argv.slice(2);

export const DAYS = [
  { en: "Monday", short: "MON", items: ["Olive quilted liner", "White sweat", "Rigid denim", "Black boots"] },
  { en: "Tuesday", short: "TUE", items: ["M-65 fishtail parka", "Black knit", "Denim", "Sneakers"] },
  { en: "Wednesday", short: "WED", items: ["Khaki blouson", "Grey sweat", "Raw denim", "Black boots"] },
  { en: "Thursday", short: "THU", items: ["M-65 fishtail parka", "Beige trousers", "Black boots"] },
  { en: "Friday", short: "FRI", items: ["Olive field jacket", "Denim jacket", "White pants", "Sneakers"] },
];

const fontFaces = `
@font-face{font-family:IS;src:url(${FONTS}/instrument-serif-latin-400-normal.woff2)}
@font-face{font-family:IS;font-style:italic;src:url(${FONTS}/instrument-serif-latin-400-italic.woff2)}
@font-face{font-family:SM;src:url(${FONTS}/space-mono-latin-400-normal.woff2)}
@font-face{font-family:SM;font-weight:700;src:url(${FONTS}/space-mono-latin-700-normal.woff2)}
@font-face{font-family:JB;src:url(${FONTS}/jetbrains-mono-latin-400-normal.woff2)}
@font-face{font-family:JB;font-weight:700;src:url(${FONTS}/jetbrains-mono-latin-700-normal.woff2)}
@font-face{font-family:AN;src:url(${FONTS}/anton-latin-400-normal.woff2)}
@font-face{font-family:IN;src:url(${FONTS}/inter-latin-400-normal.woff2)}
@font-face{font-family:IN;font-weight:700;src:url(${FONTS}/inter-latin-700-normal.woff2)}`;

const base = `*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
body{position:relative;color:#fff;-webkit-font-smoothing:antialiased}.abs{position:absolute}`;

const pad = (n) => String(n).padStart(2, "0");

const STYLES = {
  // Soft editorial: big italic serif + small typewriter mono, no boxes
  editorial: {
    css: `.sh{text-shadow:0 2px 24px rgba(0,0,0,.55),0 1px 4px rgba(0,0,0,.5)}
      .mono{font-family:SM;font-size:32px;letter-spacing:.14em;text-transform:uppercase}
      .serif{font-family:IS;font-style:italic;line-height:.9;letter-spacing:-.01em}`,
    day: (d, i) => `
      <div class="abs sh mono" style="left:84px;top:270px;opacity:.9">(${pad(i + 1)}/05) &nbsp;work week</div>
      <div class="abs sh serif" style="left:72px;top:318px;font-size:200px">${d.en}</div>
      <div class="abs sh mono" style="left:84px;top:1150px;line-height:1.75">${d.items.map((t) => `— ${t}`).join("<br>")}</div>`,
    hook: () => `
      <div class="abs sh serif" style="left:0;right:0;top:690px;text-align:center;font-size:150px">what I wear<br>to work</div>
      <div class="abs sh mono" style="left:0;right:0;top:1010px;text-align:center">as a vintage military nerd</div>`,
    cta: () => `
      <div class="abs" style="inset:0;background:rgba(0,0,0,.38)"></div>
      <div class="abs sh serif" style="left:0;right:0;top:760px;text-align:center;font-size:150px">which day<br>wins?</div>
      <div class="abs sh mono" style="left:0;right:0;top:1080px;text-align:center">mon · tue · wed · thu · fri</div>`,
  },
  // Military spec tag: cream issue label with olive mono type
  spec: {
    css: `.tag{background:#ECE5D2;color:#2E3820;font-family:JB;box-shadow:0 10px 40px rgba(0,0,0,.28)}
      .row{display:flex;gap:28px;font-size:28px;line-height:1.7;letter-spacing:.06em;text-transform:uppercase}
      .row b{width:150px;font-weight:700;opacity:.6}`,
    day: (d, i) => {
      const keys = d.items.length === 3 ? ["outer", "pants", "boots"] : ["outer", "top", "pants", "shoes"];
      return `
      <div class="abs tag" style="left:72px;top:260px;padding:26px 34px 30px;border-left:14px solid #4B5A2E">
        <div style="font-size:26px;letter-spacing:.2em;opacity:.65">DAY ${pad(i + 1)} / 05 — WORK UNIFORM</div>
        <div style="font-size:112px;font-weight:700;line-height:1.05;letter-spacing:-.02em">${d.en.toUpperCase()}</div>
      </div>
      <div class="abs tag" style="left:72px;top:1130px;padding:22px 34px">
        ${d.items.map((t, k) => `<div class="row"><b>${keys[k] || ""}</b><span>${t}</span></div>`).join("")}
      </div>`;
    },
    hook: () => `
      <div class="abs tag" style="left:110px;right:110px;top:700px;padding:40px 46px;border-left:16px solid #4B5A2E">
        <div style="font-size:28px;letter-spacing:.22em;opacity:.65">ISSUE NO. 01 — 5 DAYS</div>
        <div style="font-size:120px;font-weight:700;line-height:1;letter-spacing:-.03em;margin-top:10px">WORK<br>UNIFORM</div>
        <div style="font-size:30px;letter-spacing:.12em;margin-top:18px">MON → FRI / VINTAGE MILITARY</div>
      </div>`,
    cta: () => `
      <div class="abs tag" style="left:110px;right:110px;top:760px;padding:40px 46px;border-left:16px solid #4B5A2E">
        <div style="font-size:28px;letter-spacing:.22em;opacity:.65">END OF WEEK</div>
        <div style="font-size:104px;font-weight:700;line-height:1;letter-spacing:-.03em;margin-top:10px">WHICH DAY<br>WINS?</div>
        <div style="font-size:30px;letter-spacing:.12em;margin-top:18px">COMMENT 1 — 5</div>
      </div>`,
  },
  // Bold poster: giant condensed day + small clean sans
  bold: {
    css: `.an{font-family:AN;line-height:.86;text-transform:uppercase;text-shadow:0 6px 40px rgba(0,0,0,.35)}
      .in{font-family:IN;font-weight:700;font-size:30px;letter-spacing:.08em;text-transform:uppercase;text-shadow:0 2px 16px rgba(0,0,0,.5)}`,
    day: (d, i) => `
      <div class="abs an" style="left:0;right:0;top:230px;text-align:center;font-size:400px;letter-spacing:-.01em">${d.short}</div>
      <div class="abs in" style="left:0;right:0;top:600px;text-align:center;opacity:.92">${pad(i + 1)} / 05</div>
      <div class="abs in" style="left:60px;right:60px;top:1260px;text-align:center;line-height:1.6">${d.items.join("&nbsp; / &nbsp;")}</div>`,
    hook: () => `
      <div class="abs an" style="left:0;right:0;top:660px;text-align:center;font-size:210px;white-space:nowrap">5 days<br>5 work fits</div>`,
    cta: () => `
      <div class="abs" style="inset:0;background:rgba(0,0,0,.35)"></div>
      <div class="abs an" style="left:0;right:0;top:700px;text-align:center;font-size:220px;white-space:nowrap">which day<br>wins?</div>
      <div class="abs in" style="left:0;right:0;top:1110px;text-align:center">comment 1 — 5</div>`,
  },
};

const s = STYLES[style];
if (!s) throw new Error(`unknown style ${style}`);
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
const shots = [["hook", s.hook()], ["cta", s.cta()], ...DAYS.map((d, i) => [`day${i}`, s.day(d, i)])];
for (const [name, body] of shots) {
  // Load from a file URL so the local font files are allowed to load.
  const html = resolve(out, `${name}.html`);
  writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${fontFaces}${base}${s.css}</style><body>${body}</body>`);
  await page.goto(pathToFileURL(html).href);
  await page.evaluate(() => document.fonts.ready);
  const missing = await page.evaluate(() => [...document.fonts].filter((f) => f.status === "error").map((f) => f.family));
  if (missing.length) throw new Error(`fonts failed to load: ${missing}`);
  unlinkSync(html);
  await page.screenshot({ path: resolve(out, `${name}.png`), omitBackground: true });
}
await browser.close();
console.log(`${style}: ${shots.length} overlays → ${out}`);
