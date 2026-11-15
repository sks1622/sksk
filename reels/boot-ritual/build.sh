#!/usr/bin/env bash
# Today's boots (chelsea boots): brush, put on, walk out. Same look as reels/boots-lacing:
# "Today's boots" on the first shot only, natural colour, original sound, jump cuts that
# alternate 1.0x / 1.2x punch-ins.
# The camera lost focus mid-shot in clips 3-6; those moments are cut out (found per frame
# with a Laplacian sharpness check) and the punch-ins hide the joins.
# Usage: bash build.sh <clip folder>   (needs *_1.mp4 ... *_6.mp4)
set -euo pipefail
SRC=${1:?clip folder}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
node "$HERE/overlays.mjs" "$WORK/ov"
clip() { ls "$SRC"/*_"$1".mp4 | head -1; }

# clip  start  length  zoom  title   (every segment is in focus)
SHOTS=(
  "1 0.00 2.60 1.0 1"   # boot waiting, title
  "1 2.60 1.23 1.2 0"   # brush comes in (focus drops at 3.87s)
  "2 0.30 2.70 1.0 0"   # brushing
  "3 0.35 2.00 1.2 0"   # brushing (focus drops at 2.4s)
  "3 3.85 1.05 1.0 0"   # clean boot (focus back at 3.83s)
  "4 0.05 1.20 1.2 0"   # boot on (focus drops at 1.3s)
  "5 3.10 1.60 1.0 0"   # walking off (soft 0.8-3.0s skipped)
  "6 1.40 3.00 1.2 0"   # out the door, empty floor (soft first 1.3s skipped)
)

n=0
for s in "${SHOTS[@]}"; do
  read -r c st len z title <<<"$s"
  # punch-in anchored low in the frame, where the boots are
  v="[0:v]fps=30,scale=iw*$z:ih*$z,crop=1080:1920:(iw-1080)/2:(ih-1920)*0.75,format=yuv420p"
  if [ "$title" = 1 ]; then fc="$v[b];[b][1:v]overlay,format=yuv420p[o]"; extra=(-loop 1 -i "$WORK/ov/title.png"); else fc="$v[o]"; extra=(); fi
  fo=$(echo "$len - 0.03" | bc)
  ffmpeg -v error -y -ss "$st" -t "$len" -i "$(clip "$c")" "${extra[@]}" \
    -filter_complex "$fc;[0:a]afade=t=in:d=0.03,afade=t=out:st=$fo:d=0.03[a]" -map "[o]" -map "[a]" -t "$len" \
    -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 160k "$WORK/$n.mp4"
  echo "file '$WORK/$n.mp4'" >> "$WORK/list.txt"; n=$((n+1))
done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/todays-boots.mp4"
echo "done: $HERE/exports/todays-boots.mp4"
