"""assets/clips 의 원본 영상에서 릴스에 쓰는 구간을 잘라 assets/cuts 에 세로 1080x1920 으로 저장한다.

사용법 (reels/redwing-2268 폴더에서): python3 make_cuts.py
"""

import subprocess

# (출력 이름, 원본, 시작 초, 길이 초, 원래 소리 유지)
CUTS = [
    ("c01", "01-side-static.mp4", 0.5, 3.5, False),  # 고정 컷 (들고 찍은 01-side-push 는 흔들려서 교체)
    ("c02", "02-pair-buckle.mp4", 0.0, 3.8, False),
    ("c03", "03-leather-to-toe.mp4", 1.5, 4.2, False),
    ("c04", "04-toe-side.mp4", 0.3, 2.4, False),
    ("c05", "05-toe-tap.mp4", 1.8, 3.4, True),  # 2.35 / 3.35 / 4.3초에 두드리는 소리
    ("c06", "06-toe-pullback.mp4", 0.0, 4.0, False),
    ("c07", "07-orbit.mp4", 0.0, 3.0, False),
    ("c08", "08-tag.mp4", 3.0, 4.0, False),
    ("c09", "09-inside-pad.mp4", 0.4, 3.0, False),
    ("c10", "10-wear-a.mp4", 1.5, 4.4, False),
]

BASE = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"

# 컷별 추가 처리. c01: 고정 컷을 부츠 쪽으로 확대하고 3.5초 동안 아주 천천히 다가간다.
EXTRA = {
    "c01": "scale=w='trunc(1080*(1.14+0.04*t/3.5)/2)*2':h=-2:eval=frame,crop=1080:1920:(in_w-1080)*0.3:(in_h-1920)*0.08",
}

for name, src, start, length, keep_audio in CUTS:
    vf = ",".join(f for f in (BASE, EXTRA.get(name), "format=yuv420p") if f)
    cmd = [
        "ffmpeg", "-loglevel", "error", "-y", "-ss", str(start), "-i", f"assets/clips/{src}", "-t", str(length),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "15", "-movflags", "+faststart",
    ]
    cmd += ["-c:a", "aac", "-b:a", "160k"] if keep_audio else ["-an"]
    cmd.append(f"assets/cuts/{name}.mp4")
    subprocess.run(cmd, check=True)
    print(name, "ok")
