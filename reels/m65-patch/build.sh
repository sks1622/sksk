#!/usr/bin/env bash
# M-65 fishtail + original 2ID "Indianhead" patch review reel.
# Usage: bash build.sh <clip folder>   (clips are found by their timestamp in the filename)
set -euo pipefail
SRC=${1:?clip folder}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
node "$HERE/overlays.mjs" "$WORK/ov"
clip() { ls "$SRC"/*"$1".mp4 | head -1; }

# clip-timestamp   start  length  zoom  caption
SHOTS=(
  "20261122_143350 0.30 2.60 1.00 title"     # patched shoulder (the result first)
  "20261101_104820 1.60 2.40 1.12 why"       # bare shoulder, before
  "20261101_104632 0.00 2.40 1.00 which"     # the patch on its own
  "20261101_104632 2.40 2.20 1.15 korea"     # the patch, closer
  "20261101_104910 0.40 2.80 1.00 original"  # placing it on the shoulder
  "20261101_104910 4.60 2.80 1.12 spot"      # pressing it into place
  "20261122_143614 2.40 2.80 1.00 label"     # spec label
  "20261122_151947 0.00 3.20 1.00 -"         # wearing it outside, turn to the patch
  "20261122_144521 0.30 3.00 1.00 end"       # mirror
)

GRADE="eq=contrast=1.05:saturation=0.95,colorbalance=rs=0.02:bs=-0.02"
n=0
for s in "${SHOTS[@]}"; do
  read -r c st len z cap <<<"$s"
  v="[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,scale=iw*$z:ih*$z,crop=1080:1920,$GRADE,format=yuv420p"
  if [ "$cap" = "-" ]; then fc="$v[o]"; extra=(); else
    fc="$v[b];[b][2:v]overlay=enable='gte(t,0.15)',format=yuv420p[o]"; extra=(-loop 1 -i "$WORK/ov/$cap.png"); fi
  ffmpeg -v error -y -ss "$st" -t "$len" -i "$(clip "$c")" -f lavfi -t "$len" -i anullsrc=r=48000:cl=stereo "${extra[@]}" \
    -filter_complex "$fc" -map "[o]" -map 1:a -t "$len" -c:v libx264 -preset medium -crf 20 -c:a aac "$WORK/$n.mp4"
  echo "file '$WORK/$n.mp4'" >> "$WORK/list.txt"; n=$((n+1))
done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/m65-patch.mp4"
echo "done: $HERE/exports/m65-patch.mp4"
