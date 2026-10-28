"""assets/clips 의 원본 영상에서 릴스에 쓰는 구간을 잘라 assets/cuts 에 세로 1080x1920 으로 저장한다.

사용법 (reels/redwing-2268 폴더에서): python3 make_cuts.py
"""

import subprocess

# (출력 이름, 원본, 시작 초, 길이 초, 원래 소리 유지)
CUTS = [
    ("c01", "01-side-push.mp4", 0.0, 3.0, False),
    ("c02", "02-pair-buckle.mp4", 0.0, 3.2, False),
    ("c03", "03-leather-to-toe.mp4", 1.5, 3.5, False),
    ("c04", "04-toe-side.mp4", 0.3, 2.0, False),
    ("c05", "05-toe-tap.mp4", 1.8, 3.0, True),  # 2.35 / 3.35 / 4.3초에 두드리는 소리
    ("c06", "06-toe-pullback.mp4", 0.0, 3.4, False),
    ("c07", "07-orbit.mp4", 0.0, 2.6, False),
    ("c08", "08-tag.mp4", 3.0, 3.5, False),
    ("c09", "09-inside-pad.mp4", 0.4, 2.5, False),
    ("c10", "10-wear-a.mp4", 1.5, 4.0, False),
]

for name, src, start, length, keep_audio in CUTS:
    cmd = [
        "ffmpeg", "-loglevel", "error", "-y", "-ss", str(start), "-i", f"assets/clips/{src}", "-t", str(length),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-g", "15", "-movflags", "+faststart",
    ]
    cmd += ["-c:a", "aac", "-b:a", "160k"] if keep_audio else ["-an"]
    cmd.append(f"assets/cuts/{name}.mp4")
    subprocess.run(cmd, check=True)
    print(name, "ok")
