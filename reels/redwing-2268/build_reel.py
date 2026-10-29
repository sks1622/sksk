"""index.html(영상 배치)과 compositions/captions.html(자막)을 만든다.

클립 길이는 assets/cuts 의 실제 길이를 읽어 쓰므로, make_cuts.py 로 길이를 바꾼 뒤 이 파일만 다시 실행하면 된다.
사용법 (reels/redwing-2268 폴더에서): python3 build_reel.py
"""

import pathlib
import subprocess

PAD_SECONDS = 2.4  # 텅패드 사진이 나오는 시간
END_HOLD = 0.5     # 마지막 자막이 사라진 뒤 착용샷만 남는 시간


def length(name: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          f"assets/cuts/{name}.mp4"], capture_output=True, text=True, check=True).stdout
    return round(float(out), 2)


# (이름, 원래 소리 유지)
SEQ = [("c01", False), ("c02", False), ("c03", False), ("c04", False), ("c05", True), ("c06", False),
       ("c07", False), ("c08", False), ("c09", False), ("pad", False), ("c10", False)]

# 장면별 자막. 한 장면에 두 줄이면 장면 길이를 반으로 나눠 차례로 보여준다.
# (장면, [자막...], 보조 줄, 스타일) 스타일: "" 기본, "low" 아래쪽(택처럼 글씨가 있는 장면), "dark" 흰 배경용 검은 글씨
CAPTIONS = [
    ("c01", ["레드윙 2268 엔지니어 리뷰"], "(feat. 힐슬립 해결법)", ""),
    ("c02", ["지금 새로 살 수 있는 엔지니어는 2966이고", "2268은 사실상 단종이에요"], None, ""),
    ("c03", ["2966은 클론다이크 가죽이라 차심,", "2268은 블랙 크롬이라 흑심이에요"], None, ""),
    ("c04", ["가장 큰 차이는 스틸토예요"], None, ""),
    ("c05", ["2268은 앞코에 스틸토가 들어가 있어서"], None, ""),
    ("c06", ["앞코가 둥글고 볼륨 있게 잡히고", "오래 신어도 꺼지지 않아요"], None, ""),
    ("c07", ["이 앞코가 좋아서 일본 중고로 직구했습니다"], None, ""),
    ("c08", ["평소 275, 다른 레드윙 9.5", "2268도 9.5로 샀어요"], None, "low"),
    ("c09", ["끈이 없어서 힐슬립이 있었는데"], None, ""),
    ("pad", ["페닥 수프라 텅 패드 붙이니 확 잡혔어요"], None, "dark"),
    ("c10", ["2268 힐슬립 고민이면 텅패드 추천해요"], None, ""),
]

starts, durs, media, t = {}, {}, [], 0.0
for i, (name, audio) in enumerate(SEQ):
    dur = PAD_SECONDS if name == "pad" else length(name)
    starts[name], durs[name] = round(t, 2), dur
    if name == "pad":
        media.append(f'''      <img id="m-pad" class="clip" src="assets/photos/tongue-pad-card.jpg" alt=""
        data-start="{t:.2f}" data-duration="{dur}" data-track-index="1"
        style="position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:{i + 1};" />''')
    else:
        sound = 'data-has-audio="true"' if audio else "muted"
        media.append(f'''      <video id="m-{name}" class="clip" src="assets/cuts/{name}.mp4" {sound} playsinline
        data-start="{t:.2f}" data-duration="{dur}" data-track-index="1"
        style="position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;z-index:{i + 1};"></video>''')
    t += dur
total = round(t, 2)

groups, tweens, k = [], [], 0
for scene, lines, sub, style in CAPTIONS:
    a0 = starts[scene]
    span = durs[scene] - (END_HOLD if scene == SEQ[-1][0] else 0)
    step = span / len(lines)
    for j, line in enumerate(lines):
        k += 1
        a, b = round(a0 + j * step, 2), round(a0 + (j + 1) * step, 2)
        cls = f"clip cap {style}".strip()
        subhtml = f'\n        <div class="sub">{sub}</div>' if sub and j == 0 else ""
        groups.append(f'''      <div id="cap{k}" class="{cls}" data-start="{a}" data-duration="{round(b - a, 2)}">
        <div id="cap{k}-in" class="in"><div class="main">{line}</div>{subhtml}</div>
      </div>''')
        if a == 0:
            continue  # 0초 프레임이 커버가 되므로 첫 자막은 처음부터 보인다
        tweens.append(f'    tl.fromTo("#cap{k}-in", {{ opacity: 0, y: 8 }}, '
                      f'{{ opacity: 1, y: 0, duration: 0.14, ease: "power2.out" }}, {a});')

captions = f'''<template>
  <style>
    @font-face {{ font-family: "Pretendard"; font-weight: 500; src: url("assets/fonts/Pretendard-Medium.woff2") format("woff2"); }}
    @font-face {{ font-family: "Pretendard"; font-weight: 700; src: url("assets/fonts/Pretendard-Bold.woff2") format("woff2"); }}
    #root {{ position: absolute; inset: 0; }}
    .cap {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    .in {{ position: absolute; left: 90px; width: 900px; top: 620px; text-align: center; font-family: "Pretendard"; color: #ffffff;
      word-break: keep-all; text-shadow: 0 0 3px rgba(0,0,0,0.85), 0 3px 14px rgba(0,0,0,0.55); }}
    .main {{ font-weight: 700; font-size: 58px; line-height: 1.32; letter-spacing: -0.02em; }}
    .low .in {{ top: 1120px; }}
    .dark .in {{ color: #17130f; text-shadow: none; }}
    .sub {{ margin-top: 10px; font-weight: 500; font-size: 42px; opacity: 0.95; }}
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
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{total}" data-track-index="2" data-track-kind="captions"
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
pathlib.Path("index.html").write_text(index)
print("total", total, "starts", starts)
