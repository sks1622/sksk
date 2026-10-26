---
name: instagram-reels
description: 인스타그램 릴스 편집. 사진이나 영상으로 9:16 릴스(코디 모음, 에이징 기록, 출근룩 모음 등)를 HyperFrames 로 만들고 MP4 로 렌더링. "릴스 만들어줘", "릴스 편집", "사진으로 영상", "코디 모음 영상" 같은 요청에 사용.
---

# 인스타그램 릴스 편집 (HyperFrames)

먼저 `/hyperframes` 스킬을 읽는다. 이 스킬은 이 계정(@poten502, 아메카지·워크웨어)에 맞춘 작업 순서만 다룬다.

## 템플릿
`reels/outfit-recap/` — 후킹(2.2초) → 코디 4장(각 2.2초) → 댓글 유도(3초), 총 14초.
- 사진: `assets/photos/photo1.jpg` ~ `photo4.jpg` (세로 4:5 사진이 가장 잘 맞음. 화면을 꽉 채우도록 잘림)
- 문구: `index.html` 의 변수(spec, headline, outroQuestion, outroCta), 아이템 이름은 `compositions/lookN.html`
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
