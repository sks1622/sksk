#!/usr/bin/env bash
# 출근룩 월~금 릴스: 클립 5개를 요일 라벨, 아이템 자막, 요일 진행바와 함께 이어 붙입니다.
# 사용법: bash build.sh <클립 폴더>   (폴더 안의 *.mp4 를 파일명 날짜순으로 월~금에 배정)
set -euo pipefail
SRC=${1:?클립 폴더를 지정하세요}
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
N=/usr/share/fonts/opentype/noto
FONT_B=$N/NotoSansCJK-Bold.ttc
FONT_K=$N/NotoSansCJK-Black.ttc; [ -f "$FONT_K" ] || FONT_K=$FONT_B

DAYS=(월 화 수 목 금); EN=(MON TUE WED THU FRI)
ITEMS=(
  "올리브 퀼팅 라이너 · 화이트 스웻 · 생지 데님 · 부츠"
  "M-65 피쉬테일 · 블랙 니트 · 데님 · 스니커즈"
  "카키 블루종 · 그레이 스웻 · 생지 데님 · 부츠"
  "M-65 피쉬테일 · 베이지 팬츠 · 부츠"
  "올리브 필드자켓 · 데님 재킷 · 화이트 팬츠"
)
START=(2.0 0.5 0.5 0.5 0.5)   # 흔들리는 첫 부분 건너뛰기
LEN=(2.6 2.4 2.4 2.4 3.4)     # 금요일은 질문 자막 때문에 길게

mapfile -t CLIPS < <(ls "$SRC"/*.mp4 | awk -F/ '{n=$NF; sub(/^[^-]*-/,"",n); print n"\t"$0}' | sort | cut -f2)
[ ${#CLIPS[@]} -eq 5 ] || { echo "클립이 5개여야 합니다 (${#CLIPS[@]}개)"; exit 1; }

esc() { printf '%s' "$1" | sed -e "s/\\\\/\\\\\\\\/g" -e "s/'/\\\\'/g" -e 's/:/\\:/g' -e 's/,/\\,/g'; }
SH="shadowcolor=black@0.55:shadowx=0:shadowy=4"

for i in 0 1 2 3 4; do
  d=${LEN[$i]}
  vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,scale=1134:2016,crop=1080:1920,eq=contrast=1.06:saturation=0.92:brightness=0.01,fps=30"
  # 글자 뒤 반투명 띠 (아래쪽은 인스타 캡션 UI에 가리지 않는 높이)
  vf+=",drawbox=x=0:y=200:w=1080:h=260:color=black@0.22:t=fill,drawbox=x=0:y=1300:w=1080:h=200:color=black@0.28:t=fill"
  # 요일 라벨
  vf+=",drawtext=fontfile='$FONT_B':text='${EN[$i]}':fontsize=46:fontcolor=white@0.85:x=(w-tw)/2:y=250:$SH"
  vf+=",drawtext=fontfile='$FONT_K':text='$(esc "${DAYS[$i]}요일 출근룩")':fontsize=104:fontcolor=white:x=(w-tw)/2:y=310:$SH"
  # 아이템
  vf+=",drawtext=fontfile='$FONT_B':text='$(esc "${ITEMS[$i]}")':fontsize=40:fontcolor=white:x=(w-tw)/2:y=1330:$SH"
  # 요일 진행바
  for j in 0 1 2 3 4; do
    a=0.38; [ $j -eq $i ] && a=1
    vf+=",drawtext=fontfile='$FONT_K':text='${DAYS[$j]}':fontsize=50:fontcolor=white@$a:x=340+$j*90:y=1400:$SH"
  done
  vf+=",drawbox=x=340+$i*90-6:y=1470:w=62:h=6:color=white:t=fill"
  if [ $i -eq 0 ]; then  # 첫 프레임 훅
    vf+=",drawbox=x=0:y=760:w=1080:h=420:color=black@0.45:t=fill:enable='lt(t,1.5)'"
    vf+=",drawtext=fontfile='$FONT_B':text='$(esc "아메카지 직장인")':fontsize=64:fontcolor=white:x=(w-tw)/2:y=820:enable='lt(t,1.5)'"
    vf+=",drawtext=fontfile='$FONT_K':text='$(esc "출근룩 월→금")':fontsize=128:fontcolor=white:x=(w-tw)/2:y=920:enable='lt(t,1.5)'"
  fi
  if [ $i -eq 4 ]; then  # 마지막 질문
    vf+=",drawbox=x=0:y=820:w=1080:h=260:color=black@0.5:t=fill:enable='gte(t,1.6)'"
    vf+=",drawtext=fontfile='$FONT_K':text='$(esc "어떤 요일이 제일 좋아요?")':fontsize=72:fontcolor=white:x=(w-tw)/2:y=880:enable='gte(t,1.6)'"
    vf+=",drawtext=fontfile='$FONT_B':text='$(esc "댓글로 알려주세요")':fontsize=46:fontcolor=white@0.9:x=(w-tw)/2:y=985:enable='gte(t,1.6)'"
  fi
  ffmpeg -v error -y -ss "${START[$i]}" -t "$d" -i "${CLIPS[$i]}" -f lavfi -t "$d" -i anullsrc=r=48000:cl=stereo \
    -vf "$vf" -map 0:v -map 1:a -c:v libx264 -preset medium -crf 21 -pix_fmt yuv420p -c:a aac -shortest "$WORK/$i.mp4"
  echo "file '$WORK/$i.mp4'" >> "$WORK/list.txt"
done
ffmpeg -v error -y -f concat -safe 0 -i "$WORK/list.txt" -c copy -movflags +faststart "$HERE/exports/workweek-ootd.mp4"
echo "완료: $HERE/exports/workweek-ootd.mp4"
