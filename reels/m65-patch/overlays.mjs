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
.in{position:absolute;left:80px;width:920px;top:1260px;text-align:center;font-family:GB;font-weight:700;color:#fffaf0;
  text-shadow:0 0 2px rgba(0,0,0,.95),0 0 6px rgba(0,0,0,.75),0 3px 16px rgba(0,0,0,.6)}
.main{font-size:60px;line-height:1.3;letter-spacing:-.01em}
.sub{margin-top:14px;font-size:42px;opacity:.95}
.title .main{font-size:92px;line-height:1.18;letter-spacing:-.02em}
.title .sub{margin-top:24px;font-size:42px}`;

// Edit the wording here. Each key is used by one shot in build.sh.
export const CAPTIONS = {
  title: { cls: "title", main: "M-65 피쉬테일", sub: "feat. 오리지널 2사단 패치" },
  why: { main: "밋밋하기도 했고,", sub: "이전 주인이 패치를 뗀 자국이 있었어요" },
  which: { top: 330, main: "미 2보병사단", sub: "\u2018인디언헤드\u2019 패치" },
  korea: { top: 330, main: "한국에 주둔하는", sub: "미군 사단이에요" },
  original: { main: "레플리카 아닌 오리지널", sub: "해외에서 어렵게 구했어요" },
  rule: { main: "부대 패치는 왼쪽 어깨", sub: "지금 소속된 부대 자리예요" },
  place: { main: "어깨 솔기에서 1.3cm 아래,", sub: "소매 가운데에 달아요" },
  label: { main: "파카는 1971년 계약분", sub: "알파 인더스트리" },
  end: { main: "패치, 있다 vs 없다?" },
};

// Markings drawn on freeze frames (coordinates are in the 1080x1920 frame).
const Y = "#F5D76E";
const ring = (x, y, r) => `<circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="${Y}" stroke-width="7"/>`;
const tag = (x, y, t, anchor = "start") =>
  `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="GB" font-weight="700" font-size="46" fill="${Y}" stroke="rgba(0,0,0,.65)" stroke-width="8" paint-order="stroke">${t}</text>`;
const arrow = (x, y1, y2) => `<g stroke="${Y}" stroke-width="6" fill="none" stroke-linecap="round">
  <line x1="${x}" y1="${y1}" x2="${x}" y2="${y2}"/><path d="M${x - 14} ${y1 + 18} L${x} ${y1} L${x + 14} ${y1 + 18}"/>
  <path d="M${x - 14} ${y2 - 18} L${x} ${y2} L${x + 14} ${y2 - 18}"/></g>`;
const SEAM = [[150, 590], [700, 330]];
const seam = `<line x1="${SEAM[0][0]}" y1="${SEAM[0][1]}" x2="${SEAM[1][0]}" y2="${SEAM[1][1]}" stroke="${Y}" stroke-width="7" stroke-dasharray="22 14" stroke-linecap="round"/>`;
const svg = (inner) => `<svg width="1080" height="1920" style="position:absolute;inset:0">${inner}</svg>`;
export const MARKS = {
  marks1: svg(ring(655, 909, 62)),
  marks2: svg(ring(655, 909, 62) + ring(689, 1118, 62) + ring(486, 837, 44) + tag(770, 1030, "패치 뗀 자국")),
  place1: svg(seam + tag(120, 470, "어깨 솔기")),
  place2: svg(seam + tag(120, 470, "어깨 솔기") + arrow(520, 432, 530) + tag(570, 500, "1.3cm")),
};

mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
const shots = [
  ...Object.entries(CAPTIONS).map(([k, c]) => [k, `<div class="in ${c.cls || ""}"${c.top ? ` style="top:${c.top}px"` : ""}><div class="main">${c.main}</div>${c.sub ? `<div class="sub">${c.sub}</div>` : ""}</div>`]),
  ...Object.entries(MARKS),
];
for (const [name, body] of shots) {
  const html = resolve(out, `${name}.html`);
  writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${css}</style>${body}`);
  await page.goto(pathToFileURL(html).href);
  await page.evaluate(() => document.fonts.ready);
  if (await page.evaluate(() => [...document.fonts].some((f) => f.status === "error"))) throw new Error("font failed to load");
  await page.screenshot({ path: resolve(out, `${name}.png`), omitBackground: true });
  unlinkSync(html);
}
await browser.close();
console.log(`overlays → ${out}`);
