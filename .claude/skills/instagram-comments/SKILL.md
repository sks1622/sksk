---
name: instagram-comments
description: 인스타그램 댓글 관리. 새 댓글 확인, 답글 초안 작성과 검토, 답글 달기, 스팸 숨기기, 자동 답글 설정. "댓글 확인해줘", "답글 달아줘", "악플 정리", "자동 답글" 같은 요청에 사용.
---

# 인스타그램 댓글 관리

도구: `instagram/igtool` (공식 Instagram Graph API). 설정이 안 되어 있으면 `instagram/README.md` 의 설정 순서를 안내한다.

## 기본 흐름 (초안 → 검토 → 실행)
1. 초안 만들기 (실제로는 아무것도 달지 않음):
   ```bash
   cd instagram && python -m igtool comments --posts 10 --days 14
   ```
2. `instagram/out/comments-*.md` 를 읽고 사용자에게 표로 보여준다: 작성자 · 댓글 · 제안 답글 · 처리(reply/hide/skip).
   `skip` 은 사람이 직접 봐야 하는 댓글이다. 각각에 대해 어떻게 답하면 좋을지 제안만 하고, 사실(가격, 일정 등)은 지어내지 않는다.
3. 사용자가 고치라고 한 부분을 같은 이름의 `.json` 파일에서 수정한다(답글 문구 수정, 원하지 않는 항목은 action 을 "skip" 으로).
4. 사용자가 확인하면 실행한다:
   ```bash
   python -m igtool approve out/comments-XXXX.json
   ```
   답글은 공개적으로 달리므로, 사용자가 이번에 확인하지 않은 초안은 실행하지 않는다.

## 자동 모드
- 한 번에 바로 처리: `python -m igtool comments --auto` (안전한 댓글만 답글, 명백한 스팸만 숨김, 나머지는 초안으로 남김)
- 3시간마다 자동 실행: `.github/workflows/instagram-comments.yml`. 켜는 방법은 README 의 "자동 답글 켜기" 를 참고한다.

## 말투 조정
답글 말투나 규칙을 바꾸고 싶다고 하면 `instagram/brand.md` 의 "말투" 와 "답글 규칙" 섹션을 고친다. 자주 묻는 질문과 그 답을 거기에 적어 두면 Claude 가 그 답만 사용한다.
