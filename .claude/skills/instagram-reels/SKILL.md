---
name: instagram-reels
description: 인스타그램 릴스 편집. 사진이나 영상으로 9:16 릴스(코디 모음, 에이징 기록, 출근룩 모음 등)를 HyperFrames 로 만들고 MP4 로 렌더링. "릴스 만들어줘", "릴스 편집", "사진으로 영상", "코디 모음 영상" 같은 요청에 사용.
---

# 인스타그램 릴스 편집 (HyperFrames)

먼저 `/hyperframes` 스킬을 읽는다. 이 스킬은 이 계정(@poten502, 아메카지·워크웨어)에 맞춘 작업 순서만 다룬다.

## 템플릿
`reels/outfit-recap/` — 6×6 필름 콘택트시트 스타일. 정사각형 사진 4장이 필름처럼 한 칸씩 넘어가고, 코디마다 루페로 신발·밑단을 확대. 4번 다음 1번으로 이어지는 루프(10.2초).
- 사진: `assets/photos/photo1.jpg` ~ `photo4.jpg` (정사각형, 자르지 않음). 필름 입자는 media-treatment 로 grain 0.08 만 적용(색은 그대로)
- 맨 위 라벨: `index.html` 의 label 변수 (기본 `roll 01`, 캡션과 같은 고정폭 글씨). 아이템 캡션, 루페 초점, 타이밍은 `compositions/sheet.html` (python 으로 생성한 정적 HTML, 1번 프레임과 루프용 복사본에 문구가 붙음)
- 새 릴스는 폴더를 복사해서 만든다: `cp -r reels/outfit-recap reels/<새 이름>` (`.hyperframes/`, `renders/` 는 빼고)

## 사진 받기
이 환경에서는 인스타그램 이미지 서버가 네트워크 정책상 막혀 있다. 사용자에게 다음 중 하나를 요청한다.
- GitHub 웹(모바일 브라우저 가능)에서 `reels/<폴더>/assets/photos/` 에 **Add file → Upload files** 로 photo1.jpg~photo4.jpg 이름으로 올리기 → 받으면 `git pull`
- 채팅에 사진 첨부 (세션에서 파일로 보이는 경우)
사진이 HEIC 면 `ffmpeg -i in.heic out.jpg` 로 바꾼다.

## 작업 순서
1. 사진과 문구를 바꾼다. 장면 수를 바꾸면 `index.html` 의 host `data-start` 와 루트 `data-duration` 도 맞춘다.
2. `npx --yes hyperframes@0.8.203 check --json` → 오류 0 확인.
3. `npx --yes hyperframes@0.8.203 snapshot --at <각 장면 시점>` → contact-sheet 를 직접 보고 확인 (잘린 글자, 사진 위 글자 가독성).
4. `npx --yes hyperframes@0.8.203 render -o renders/<이름>.mp4 --skill hyperframes`
5. SendUserFile 로 MP4 를 보낸다. 캡션·해시태그(instagram-content 스킬)와 추천 업로드 시간(일요일 17시 또는 밤 9시)을 같이 준다.

## 주의
- GSAP 은 CDN 이 막혀 있으므로 `assets/vendor/gsap.min.js` 를 쓴다. 한글은 `assets/fonts/` 의 Pretendard.
- 음악은 넣지 않는다. 인스타 앱에서 업로드할 때 인기 음원을 붙이는 게 도달에 유리하고 저작권 문제도 없다.
- 글자는 위쪽 168px 아래, 1330px 위 영역 안에 둔다(인스타 UI 가림 방지).

## 이 계정의 취향 (사용자 피드백)
- "AI 티" 나는 것 싫어함: 큰 제목 카드, 대문자 칩, 튀는 애니메이션, 계속 줌인, 댓글 구걸 멘트 금지.
- 코디 전체가 한눈에 보여야 함: 사진을 크게 잘라 쓰지 않는다.
- 촬영 날짜는 넣지 않는다.
- 설명하는 한국어 멘트("옥상에서 4벌 갈아입음" 같은 것)도 싫어함. 영상 안 글씨는 필름 라벨처럼 최소한으로.
- 끝은 마지막 카드 대신 루프.
- 루페(확대)는 무엇을 보여주는지 분명해야 함: 초점은 사진을 격자로 잘라 직접 재서 디테일 하나(밑단, 부츠)에 맞추고, 아래에 `selvedge` 같은 짧은 표시를 단다. 신발 두 짝 사이를 겨누면 땅바닥만 보인다.
