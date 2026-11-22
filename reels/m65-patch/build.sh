#!/usr/bin/env bash
# M-65 fishtail + original 2ID "Indianhead" patch review reel (Korean captions).
# Usage: bash build.sh <clip folder>   (clips are found by their timestamp in the filename)
set -euo pipefail
SRC=${1:?clip folder}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
node "$HERE/overlays.mjs" "$WORK/ov"
clip() { ls "$SRC"/*"$1".mp4 | head -1; }

# live   <clip> <start> <length> <zoom> <caption|->
# freeze <clip> <frame time> <length> <marks@sec,marks@sec> <caption>   (still frame, markings pop in)
SHOTS=(
  "live   20261122_143350 0.30 2.60 1.00 title"     # patched shoulder (the result first)
  "live   20261101_104820 1.60 1.00 1.12 why"       # bare shoulder, before
  "freeze 20261101_104820 2.60 2.40 marks1@0.2,marks2@0.8 why"   # circle the old patch holes
  "live   20261101_104632 0.00 2.40 1.00 which"     # the patch on its own
  "live   20261101_104632 2.40 2.20 1.15 korea"     # the patch, closer
  "live   20261101_104910 0.40 2.80 1.00 original"  # placing it on the shoulder
  "live   20261101_104910 4.60 2.80 1.12 rule"      # pressing it in: left shoulder = current unit
  "freeze 20261122_143350 2.50 3.00 place1@0.2,place2@0.9 place" # seam, 1.3cm, centred
  "live   20261122_143614 2.40 2.80 1.00 label"     # spec label
  "live   20261122_151947 0.00 3.20 1.00 -"         # wearing it outside, turn to the patch
  "live   20261122_144521 0.30 3.00 1.00 end"       # mirror
)

GRADE="eq=contrast=1.05:saturation=0.95,colorbalance=rs=0.02:bs=-0.02"
FIT="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
n=0
for s in "${SHOTS[@]}"; do
  read -r kind c a len d cap <<<"$s"
  inputs=(-f lavfi -t "$len" -i anullsrc=r=48000:cl=stereo)
  if [ "$kind" = live ]; then
    inputs+=(-ss "$a" -t "$len" -i "$(clip "$c")")
    fc="[1:v]fps=30,$FIT,scale=iw*$d:ih*$d,crop=1080:1920,$GRADE[v]"; k=2
  else
    ffmpeg -v error -y -ss "$a" -i "$(clip "$c")" -frames:v 1 -vf "$FIT" "$WORK/still$n.png"
    inputs+=(-loop 1 -framerate 30 -t "$len" -i "$WORK/still$n.png")
    fc="[1:v]$GRADE[v0]"; k=2; prev=v0
    IFS=, read -ra marks <<<"$d"
    for m in "${marks[@]}"; do
      inputs+=(-loop 1 -framerate 30 -t "$len" -i "$WORK/ov/${m%@*}.png")
      fc+=";[$prev][$k:v]overlay=enable='gte(t,${m#*@})'[v$k]"; prev=v$k; k=$((k+1))
    done
    # slow push-in so the still frame doesn't feel frozen
    fc+=";[$prev]scale=w='1080*(1+0.04*t/$len)':h='1920*(1+0.04*t/$len)':eval=frame,crop=1080:1920[v]"
  fi
  if [ "$cap" = "-" ]; then fc+=";[v]format=yuv420p[o]"; else
    inputs+=(-loop 1 -framerate 30 -t "$len" -i "$WORK/ov/$cap.png")
    fc+=";[v][$k:v]overlay=enable='gte(t,0.15)',format=yuv420p[o]"; fi
  ffmpeg -v error -y "${inputs[@]}" -filter_complex "$fc" -map "[o]" -map 0:a -t "$len" -r 30 \
    -c:v libx264 -preset medium -crf 20 -c:a aac "$WORK/$n.mp4"
  echo "file '$WORK/$n.mp4'" >> "$WORK/list.txt"; n=$((n+1))
done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/m65-patch.mp4"
echo "done: $HERE/exports/m65-patch.mp4"
