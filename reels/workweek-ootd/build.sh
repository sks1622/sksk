#!/usr/bin/env bash
# Work-week outfit reel (Mon-Fri). Text overlays are HTML/CSS rendered by Chromium (overlays.mjs).
# Usage: bash build.sh <clip folder> [editorial|spec|bold]
#   Clips (*.mp4) are assigned Mon->Fri in filename date order.
set -euo pipefail
SRC=${1:?clip folder}; STYLE=${2:-editorial}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
node "$HERE/overlays.mjs" "$STYLE" "$WORK/ov"

START=(2.0 0.5 0.5 0.5 0.5)   # skip the shaky first moment
LEN=(2.4 1.9 1.9 1.9 3.0)     # Mon holds the hook, Fri holds the question
HOOK=1.3; CTA_AT=1.4

mapfile -t CLIPS < <(ls "$SRC"/*.mp4 | awk -F/ '{n=$NF; sub(/^[^-]*-/,"",n); print n"\t"$0}' | sort | cut -f2)
[ ${#CLIPS[@]} -eq 5 ] || { echo "need exactly 5 clips (got ${#CLIPS[@]})"; exit 1; }

GRADE="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.08:saturation=0.88:gamma=0.97,colorbalance=rs=0.03:bs=-0.03:rh=0.02:bh=-0.02,noise=alls=6:allf=t,fps=30"
for i in 0 1 2 3 4; do
  d=${LEN[$i]}
  # slow push-in for movement
  zoom="scale=w='1080*(1+0.05*t/$d)':h='1920*(1+0.05*t/$d)':eval=frame,crop=1080:1920"
  if [ $i -eq 0 ]; then
    fc="[0:v]$GRADE,$zoom[v];[v][2:v]overlay=enable='gte(t,$HOOK)'[a];[a][3:v]overlay=enable='lt(t,$HOOK)'[o]"
    extra=(-loop 1 -i "$WORK/ov/day0.png" -loop 1 -i "$WORK/ov/hook.png")
  elif [ $i -eq 4 ]; then
    fc="[0:v]$GRADE,$zoom[v];[v][2:v]overlay=enable='lt(t,$CTA_AT)'[a];[a][3:v]overlay=enable='gte(t,$CTA_AT)'[o]"
    extra=(-loop 1 -i "$WORK/ov/day4.png" -loop 1 -i "$WORK/ov/cta.png")
  else
    fc="[0:v]$GRADE,$zoom[v];[v][2:v]overlay[o]"
    extra=(-loop 1 -i "$WORK/ov/day$i.png")
  fi
  ffmpeg -v error -y -ss "${START[$i]}" -t "$d" -i "${CLIPS[$i]}" -f lavfi -t "$d" -i anullsrc=r=48000:cl=stereo "${extra[@]}" \
    -filter_complex "$fc" -map "[o]" -map 1:a -t "$d" -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -c:a aac "$WORK/$i.mp4"
  echo "file '$WORK/$i.mp4'" >> "$WORK/list.txt"
done
mkdir -p "$HERE/exports"
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/workweek-$STYLE.mp4"
echo "done: $HERE/exports/workweek-$STYLE.mp4"
