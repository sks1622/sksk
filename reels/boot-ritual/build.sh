#!/usr/bin/env bash
# Boot-ritual reel: brush, wear, go. The camera lost focus mid-shot in clips 3-6, so those
# moments are cut out (measured per frame with a Laplacian sharpness check) and the joins
# are hidden with alternating punch-ins, the way jump cuts are usually disguised.
# Usage: bash build.sh <clip folder>   (needs *_1.mp4 ... *_6.mp4)
set -euo pipefail
SRC=${1:?clip folder}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
node "$HERE/overlays.mjs" "$WORK/ov"
clip() { ls "$SRC"/*_"$1".mp4 | head -1; }

# clip  start  length  zoom  overlay   (all segments are in focus)
SHOTS=(
  "1 0.00 1.20 1.00 hook"    # boot alone, hook on frame 0
  "1 2.60 1.20 1.12 brush"   # hand comes in with the brush
  "2 0.40 2.00 1.00 brush"   # brushing
  "3 0.80 1.45 1.12 brush"   # brushing, ends before focus drops at 2.4s
  "3 3.85 0.85 1.00 brush"   # clean boot (focus back at 3.83s)
  "4 0.05 1.25 1.00 wear"    # boot on, before focus drops at 1.3s
  "5 3.10 1.60 1.12 go"      # walking off (skips the soft 0.8-3.0s)
  "6 1.40 1.00 1.00 go"      # out the door (skips the soft first 1.3s)
  "6 3.00 1.80 1.00 end"     # empty floor, end card
)

GRADE="eq=contrast=1.08:saturation=0.9:gamma=0.97,colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02,unsharp=5:5:0.5,noise=alls=6:allf=t"
n=0
for s in "${SHOTS[@]}"; do
  read -r c st len z ov <<<"$s"
  # zoom anchored low in the frame, where the boots are
  zf="scale=iw*$z:ih*$z,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.75"
  fc="[0:v]fps=30,$zf,$GRADE[v];[v][2:v]overlay,format=yuv420p[o]"
  ffmpeg -v error -y -ss "$st" -t "$len" -i "$(clip "$c")" -f lavfi -t "$len" -i anullsrc=r=48000:cl=stereo \
    -loop 1 -i "$WORK/ov/$ov.png" -filter_complex "$fc" -map "[o]" -map 1:a -t "$len" \
    -c:v libx264 -preset medium -crf 20 -c:a aac "$WORK/$n.mp4"
  echo "file '$WORK/$n.mp4'" >> "$WORK/list.txt"; n=$((n+1))
done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/boot-ritual.mp4"
echo "done: $HERE/exports/boot-ritual.mp4"
