"""2268 리뷰 릴스를 만든다: 장면 길이 계산 → 클립 자르기(assets/cuts) → index.html, compositions/captions.html 생성.

자막마다 글자 수로 읽는 시간을 정하고, 장면 길이는 그 장면 자막 시간의 합이다.
사용법 (reels/redwing-2268 폴더에서): python3 build_reel.py
"""

import pathlib
import subprocess

# 읽는 시간: 기본 0.9초 + 글자(공백 제외)당 0.1초, 최소 1.6초
READ_BASE, READ_PER_CHAR, READ_MIN = 0.9, 0.1, 1.6
END_HOLD = 0.8  # 마지막 자막이 사라진 뒤 착용샷만 남는 시간

# 장면: (이름, 원본, 시작 초, 원래 소리 유지, 최소 길이, 천천히 다가가기). 원본이 None 이면 사진.
# 카메라가 멈춰 있는 컷은 천천히 다가가게 해서 화면이 멈춘 느낌을 줄인다.
SCENES = [
    ("c01", "01-side-push.mp4", 0.0, False, 3.0, False),
    ("c02", "02-pair-buckle.mp4", 0.0, False, 0, True),
    ("c02b", "06-front-toes.mp4", 0.5, False, 0, True),
    ("c03", "03-leather-to-toe.mp4", 1.5, False, 0, False),
    ("c04", "04-toe-side.mp4", 0.3, False, 0, True),
    ("c05", "05-toe-tap.mp4", 1.8, True, 3.4, False),  # 2.35 / 3.35 / 4.3초 두드리는 소리를 다 담는 길이
    ("c06", "06-toe-pullback.mp4", 0.0, False, 0, False),
    ("c06b", "03-leather-to-toe.mp4", 7.0, False, 0, False),  # 같은 클립 끝부분의 앞코 광택
    ("c07", "07-orbit.mp4", 0.0, False, 0, False),
    ("c08", "08-tag.mp4", 2.7, False, 0, False),
    ("c09", "09-inside-pad.mp4", 0.4, False, 0, False),
    ("pad", None, 0, False, 0, False),
    ("c10", "10-wear-a.mp4", 1.5, False, 0, True),
]

# 슬로모션 (재생 속도). 0.75 = 원래의 75% 속도. 부족한 프레임은 보간해서 부드럽게 만든다.
SPEED = {"c01": 0.75, "c07": 0.8}

# 두드리는 순간(컷 안의 초)에 화면이 살짝 당겨졌다 돌아온다
TAP_PULSE = {"c05": [0.55, 1.55, 2.5]}

# 앞코 광택 위로 빛이 한 번 지나간다: (장면, 장면 시작부터 초)
SWEEPS = [("c01", 0.6)]  # "앞코가 둥글고" 장면의 빛은 사용자가 별로라고 해서 뺐다

# 색보정 (HyperFrames Product Polish 기준: 소재와 광택은 지키고 대비만 살짝, 가장자리를 아주 약하게 어둡게)
GRADING = ('{"intensity":0.75,"adjust":{"exposure":0.01,"contrast":0.08,"highlights":-0.12,"shadows":0.04,'
           '"whites":0.02,"blacks":-0.04,"vibrance":0.03,"saturation":0.02},"details":{"vignette":0.04}}')

# 주제가 바뀌는 장면 시작에 아주 작게 휙 소리
WHOOSH_AT, WHOOSH_FILE, WHOOSH_VOLUME = ["c03", "c04", "c08", "c09"], "assets/sfx/whoosh-short.mp3", 0.3

# 장면별 자막: (장면, [자막...], 보조 줄, 스타일)
# 긴 문장은 \n 으로 의미 단위에서 직접 줄을 나눈다.
# 스타일: "title" 첫 화면 제목, "" 기본, "low" 아래쪽(택처럼 글씨가 있는 장면), "dark" 흰 배경용 검은 글씨
CAPTIONS = [
    ("c01", ["레드윙 2268\n엔지니어 리뷰"], "feat. 힐슬립 해결법", "title"),
    ("c02", ["레드윙 엔지니어 부츠는\n2966과 2268 두 가지가 있어요", "2966은 지금도 판매 중이고"], None, ""),
    ("c02b", ["2268은 단종됐어요"], None, ""),
    ("c03", ["2966은 클론다이크 가죽이라 차심,", "2268은 블랙 크롬이라 흑심이에요"], None, ""),
    ("c04", ["가장 큰 차이는 스틸토예요"], None, ""),
    ("c05", ["2268은 앞코에\n스틸토가 들어가 있어서"], None, ""),
    ("c06", ["앞코가 둥글고 볼륨 있게 잡히고"], None, ""),
    ("c06b", ["오래 신어도 꺼지지 않아요"], None, ""),
    ("c07", ["이 앞코가 좋아서\n일본 중고로 직구했습니다"], None, ""),
    ("c08", ["평소 275, 다른 레드윙 9.5", "2268도 9.5로 샀어요"], None, "low"),
    ("c09", ["끈이 없어서 힐슬립이 있었는데"], None, ""),
    ("pad", ["페닥 수프라 텅 패드 붙이니\n확 잡혔어요"], None, "dark"),
    ("c10", ["2268 힐슬립 고민이면\n텅패드 추천해요"], None, ""),
]

FONT_FILE, FONT_FAMILY = "assets/fonts/GowunBatang-Bold.ttf", "Gowun Batang"
BASE_VF = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"


def read_time(text: str) -> float:
    return max(READ_MIN, READ_BASE + READ_PER_CHAR * len(text.replace(" ", "").replace("\n", "")))


def media_length(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


# 1) 자막 시간과 장면 길이
caption_times = {scene: [read_time(line) for line in lines] for scene, lines, _, _ in CAPTIONS}
durs = {}
for name, src, start, _, minimum, _ in SCENES:
    need = sum(caption_times[name]) + (END_HOLD if name == SCENES[-1][0] else 0)
    dur = round(max(need, minimum), 2)
    if src:
        available = (media_length(f"assets/clips/{src}") - start) / SPEED.get(name, 1)
        if dur > available:
            raise SystemExit(f"{name}: {dur:.2f}초가 필요한데 원본에 {available:.2f}초밖에 없습니다")
    durs[name] = dur

# 2) 클립 자르기
pathlib.Path("assets/cuts").mkdir(parents=True, exist_ok=True)
for name, src, start, keep_audio, _, push in SCENES:
    if not src:
        continue
    speed = SPEED.get(name, 1)
    filters = []
    if speed != 1:
        filters += [f"setpts=PTS/{speed}", "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1"]
    filters.append(BASE_VF.replace(",format=yuv420p", ""))
    if push:  # 1.00 → 1.05 로 아주 천천히 확대 (가운데 기준)
        filters.append(f"scale=w='trunc(1080*(1+0.05*t/{durs[name]})/2)*2':h=-2:eval=frame,crop=1080:1920")
    if name in TAP_PULSE:  # 두드릴 때마다 3.5% 당겨졌다 0.1초 만에 돌아온다
        bumps = "+".join(f"exp(-pow((t-{tt})/0.07,2))" for tt in TAP_PULSE[name])
        filters.append(f"scale=w='trunc(1080*(1+0.035*({bumps}))/2)*2':h=-2:eval=frame,crop=1080:1920")
    filters.append("format=yuv420p")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(start), "-i", f"assets/clips/{src}",
           "-t", str(round(durs[name] * speed, 3)), "-vf", ",".join(filters), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "15", "-movflags", "+faststart"]
    cmd += ["-c:a", "aac", "-b:a", "160k"] if keep_audio else ["-an"]
    subprocess.run(cmd + [f"assets/cuts/{name}.mp4"], check=True)

# 3) 영상 배치
starts, media, t = {}, [], 0.0
for i, (name, src, _, keep_audio, _, _) in enumerate(SCENES):
    starts[name] = round(t, 2)
    style = f"position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:{i + 1};"
    if not src:
        media.append(f'''      <img id="m-{name}" class="clip" src="assets/photos/tongue-pad-card.jpg" alt=""
        data-start="{t:.2f}" data-duration="{durs[name]}" data-track-index="1" style="{style}" />''')
    else:
        sound = 'data-has-audio="true"' if keep_audio else "muted"
        media.append(f'''      <video id="m-{name}" class="clip" src="assets/cuts/{name}.mp4" {sound} playsinline
        data-start="{t:.2f}" data-duration="{durs[name]}" data-track-index="1" style="{style}object-fit:cover;"></video>''')
    t += durs[name]
total = round(t, 2)
for n, name in enumerate(WHOOSH_AT, 1):
    media.append(f'      <audio id="sfx-whoosh{n}" src="{WHOOSH_FILE}" data-start="{max(0, starts[name] - 0.12):.2f}" '
                 f'data-duration="0.57" data-volume="{WHOOSH_VOLUME}" data-track-index="3"></audio>')

# 4) 빛 지나가기
sweep_els, sweep_tweens = [], []
for n, (scene, offset) in enumerate(SWEEPS, 1):
    a = starts[scene] + offset
    sweep_els.append(f'      <div id="sweep{n}" class="clip sweepwrap" data-start="{a:.2f}" data-duration="1.2">'
                     f'<div id="sweep{n}-band" class="band"></div></div>')
    sweep_tweens.append(f'    tl.fromTo("#sweep{n}-band", {{ x: -900, rotation: 18 }}, {{ x: 1300, rotation: 18, duration: 1.1, ease: "power2.inOut" }}, {a:.2f});')
fx = f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .sweepwrap {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; }}
    .band {{ position: absolute; left: 0; top: -200px; width: 180px; height: 2320px;
      background: linear-gradient(90deg, rgba(255,250,235,0) 0%, rgba(255,250,235,0.42) 50%, rgba(255,250,235,0) 100%);
      mix-blend-mode: screen; }}
  </style>
  <div id="root" data-composition-id="fx" data-width="1080" data-height="1920">
{chr(10).join(sweep_els)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(sweep_tweens)}
    window.__timelines["fx"] = tl;
  </script>
</template>
'''

# 5) 자막
groups, tweens, k = [], [], 0
for scene, lines, sub, style in CAPTIONS:
    a = starts[scene]
    for j, line in enumerate(lines):
        k += 1
        b = a + caption_times[scene][j]
        if j == len(lines) - 1:  # 장면이 자막보다 길면 마지막 자막을 장면 끝까지 둔다
            b = starts[scene] + durs[scene] - (END_HOLD if scene == SCENES[-1][0] else 0)
        cls = f"clip cap {style}".strip()
        subhtml = f'\n        <div class="sub">{sub}</div>' if sub and j == 0 else ""
        groups.append(f'''      <div id="cap{k}" class="{cls}" data-start="{a:.2f}" data-duration="{b - a:.2f}">
        <div id="cap{k}-in" class="in"><div class="main">{line.replace(chr(10), "<br>")}</div>{subhtml}</div>
      </div>''')
        if a > 0:  # 0초 프레임이 커버가 되므로 첫 자막은 처음부터 보인다
            tweens.append(f'    tl.fromTo("#cap{k}-in", {{ opacity: 0, y: 8 }}, '
                          f'{{ opacity: 1, y: 0, duration: 0.14, ease: "power2.out" }}, {a:.2f});')
        a = b

captions = f'''<template>
  <style>
    @font-face {{ font-family: "{FONT_FAMILY}"; font-weight: 700; src: url("{FONT_FILE}") format("truetype"); }}
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    .in {{ position: absolute; left: 80px; width: 920px; top: 620px; text-align: center; font-family: "{FONT_FAMILY}";
      font-weight: 700; color: #fffaf0; word-break: keep-all;
      text-shadow: 0 0 2px rgba(0,0,0,0.95), 0 0 6px rgba(0,0,0,0.75), 0 3px 16px rgba(0,0,0,0.6); }}
    .main {{ font-size: 60px; line-height: 1.34; letter-spacing: -0.01em; }}
    .low .in {{ top: 1120px; }}
    .dark .in {{ color: #17130f; text-shadow: none; }}
    .sub {{ margin-top: 12px; font-size: 42px; opacity: 0.95; }}
    .title .in {{ top: 560px; }}
    .title .main {{ font-size: 92px; line-height: 1.22; letter-spacing: -0.02em; }}
    .title .sub {{ margin-top: 26px; font-size: 40px; letter-spacing: 0.02em; opacity: 0.9; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(groups)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tweens)}
    window.__timelines["captions"] = tl;
  </script>
</template>
'''

index = f'''<!doctype html>
<html lang="ko" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #0c0b0a; }}
      #root {{ width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
{chr(10).join(media)}
      <div id="fx" data-composition-id="fx" data-composition-src="compositions/fx.html"
        data-start="0" data-duration="{total}" data-track-index="2" data-track-kind="graphics"
        data-width="1080" data-height="1920" style="z-index: 40;"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{total}" data-track-index="4" data-track-kind="captions"
        data-width="1080" data-height="1920" style="z-index: 50;"></div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''

pathlib.Path("compositions/captions.html").write_text(captions)
pathlib.Path("compositions/fx.html").write_text(fx)
pathlib.Path("index.html").write_text(index)
subprocess.run(["npx", "--yes", "hyperframes@0.8.203", "media-treatment", "--selector", "video", "--grading", GRADING,
                "--apply", "--json"], check=True, capture_output=True)
print("total", total)
for scene, lines, _, _ in CAPTIONS:
    for line, sec in zip(lines, caption_times[scene]):
        print(f"  {sec:.1f}s  {line!r}")
