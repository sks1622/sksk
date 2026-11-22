// Captions and markings for the M-65 patch reel
// (Pretendard Bold, white, soft shadow, centered). Usage: node overlays.mjs <out dir>
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
const fontDir = join(HERE, "fonts");
const f = (n) => pathToFileURL(join(fontDir, n)).href;
const css = `@font-face{font-family:PT;font-weight:700;src:url(${f("Pretendard-Bold.otf")})}
@font-face{font-family:PT;font-weight:800;src:url(${f("Pretendard-ExtraBold.otf")})}
*{margin:0;padding:0}html,body{width:1080px;height:1920px;background:transparent;overflow:hidden}
.in{position:absolute;left:50px;width:980px;top:1250px;text-align:center;font-family:PT;font-weight:700;color:#fff;
  letter-spacing:-.02em;word-break:keep-all;
  text-shadow:0 0 3px rgba(0,0,0,.9),0 0 8px rgba(0,0,0,.6),0 3px 18px rgba(0,0,0,.55)}
.main,.sub{font-size:58px;line-height:1.38}
.title .main{font-size:96px;font-weight:800;line-height:1.15;letter-spacing:-.03em}
.title .sub{margin-top:18px;font-size:48px}`;

// Edit the wording here. Each key is used by one shot in build.sh.
export const CAPTIONS = {
  title: { cls: "title", main: "M-65 피쉬테일", sub: "feat. 70년대 오리지널 인디언헤드 패치" },
  why1: { main: "그냥 입기엔 좀 밋밋하기도 했고," },
  why2: { main: "이전 주인이 패치를 뗀 자국도", sub: "그대로 남아 있었거든요" },
  which: { top: 330, main: "그래서 고른 건 인디언헤드 패치" },
  korea: { top: 330, main: "한국에 주둔하는", sub: "미 2보병사단의 상징이에요" },
  orig1: { main: "제 M-65가 만들어진 70년대에", sub: "실제로 쓰인 오리지널 패치예요" },
  orig2: { main: "국내에선 구할 수가 없어서" },
  orig3: { main: "이베이, 메루카리 같은 해외에서", sub: "디깅해서 겨우 구했어요" },
  rule: { main: "부대 패치는 왼쪽 어깨에 달아요" },
  place: { main: "어깨 솔기에서 1.3cm(½인치) 아래,", sub: "소매 한가운데가 정석이에요" },
  label: { main: "파카는 1971년 계약분,", sub: "알파 인더스트리 제품이에요" },
  end: { main: "드디어 완성된 M-65", sub: "70년대 그 모습 그대로" },
};

// Markings drawn on freeze frames (coordinates are in the 1080x1920 frame).
const Y = "#F5D76E";
const ring = (x, y, r) => `<circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="${Y}" stroke-width="7"/>`;
const tag = (x, y, t, anchor = "start") =>
  `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="PT" font-weight="700" font-size="46" fill="${Y}" stroke="rgba(0,0,0,.65)" stroke-width="8" paint-order="stroke">${t}</text>`;
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
