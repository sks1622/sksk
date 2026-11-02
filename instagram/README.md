# 인스타그램 운영 도구

공식 Instagram API와 Claude를 함께 써서 인스타그램 운영을 돕는 도구입니다.

| 할 수 있는 일 | 명령 |
|---|---|
| 새 댓글에 답글 초안 만들기 (검토 후 실행) | `python -m igtool comments` → `python -m igtool approve 파일` |
| 안전한 댓글에 바로 답글 달고 스팸 숨기기 | `python -m igtool comments --auto` |
| 3시간마다 자동 답글 | GitHub Actions (아래 "자동 답글 켜기") |
| 성과 리포트와 운영 조언 | `python -m igtool insights` |
| 다음 게시물 아이디어 추천 | `python -m igtool ideas --brief "다음 주 신메뉴 출시"` |
| 캡션과 해시태그 작성 | `python -m igtool caption "비 오는 날 창가 자리 사진"` |
| 게시물 업로드 (이미지, 캐러셀, 릴스) | `python -m igtool publish --image URL --caption "..."` |
| 액세스 토큰 연장 | `python -m igtool refresh-token` |

결과물은 `instagram/out/` 폴더에 저장됩니다. 이 폴더는 git에 올라가지 않습니다.

Claude Code에서 "댓글 확인해줘", "다음 주 게시물 기획해줘", "요즘 인사이트 어때?"처럼 말로 요청해도 됩니다.
`.claude/skills/` 에 있는 스킬이 이 도구를 대신 실행해 줍니다.

---

## 설정 (처음 한 번)

### 1. 인스타그램을 프로페셔널 계정으로 바꾸기
인스타그램 앱에서 설정 → 계정 유형 및 도구 → **프로페셔널 계정으로 전환**을 누르고, 크리에이터나 비즈니스 중 하나를 고르세요. 무료입니다.

### 2. Meta 개발자 앱 만들고 토큰 받기
1. https://developers.facebook.com 에 로그인한 뒤 **내 앱 → 앱 만들기**를 누르세요. 사용 사례는 "Instagram에서 메시지 및 콘텐츠 관리"를 고르세요.
2. 앱 대시보드에서 **Instagram → Instagram 로그인을 통한 API 설정**으로 들어가세요.
3. **계정 추가**를 눌러 내 인스타그램 계정을 연결하세요. 권한은 기본, 댓글 관리, 콘텐츠 게시, 인사이트를 모두 허용하세요.
4. **토큰 생성**을 누르면 `IGAA...`로 시작하는 토큰이 나옵니다. 60일 동안 유효합니다. 같은 화면에 보이는 Instagram 계정 ID도 복사해 두세요.

> 앱은 "개발 모드"인 채로 두면 됩니다. 내 계정만 쓴다면 앱 검수를 받지 않아도 동작합니다.

### 3. Claude API 키 받기
https://console.anthropic.com 에서 **API Keys → Create Key**를 누르세요. 사용한 만큼 요금이 나갑니다. 댓글 수십 개를 처리하는 데 보통 몇십~몇백 원 수준입니다.

### 4. 설정 파일 만들기
```bash
cd instagram
pip install -r requirements.txt
cp .env.example .env      # .env 를 열어 위에서 받은 값 3개를 채우세요
```

### 5. 브랜드 가이드 채우기
`brand.md`에 계정 소개, 말투, 자주 묻는 질문과 답을 적어 두세요. Claude가 답글과 캡션을 쓸 때 이 파일을 따릅니다. 내용이 구체적일수록 결과가 좋아집니다.

### 6. 확인
```bash
python -m igtool comments          # 초안만 만들어지고 실제로 달리지는 않습니다
```

---

## 자동 답글 켜기 (GitHub Actions)
GitHub 저장소에서 **Settings → Secrets and variables → Actions**로 들어가세요.

1. **Secrets** 탭에 `ANTHROPIC_API_KEY`, `IG_ACCESS_TOKEN`, `IG_USER_ID` 3개를 추가하세요.
2. **Variables** 탭에 `IG_AUTO_REPLY`를 추가하고 값을 `true`로 넣으세요.

그러면 3시간마다 최근 7일 안에 달린 새 댓글을 확인합니다. 칭찬이나 가벼운 질문에는 답글을 달고, 명백한 스팸은 숨깁니다. 불만이나 가격 문의처럼 확인이 필요한 댓글은 건드리지 않고 남겨 둡니다. 한 번에 최대 15개까지만 처리합니다.
끄려면 `IG_AUTO_REPLY` 값을 `false`로 바꾸면 됩니다.

> 이 저장소는 **공개 저장소**입니다. 그래서 Actions 로그에는 처리한 개수만 남고, 댓글 내용과 인사이트 수치는 출력되지 않습니다.
> 토큰과 키는 반드시 Secrets에만 넣고, `.env` 파일은 절대 커밋하지 마세요. `.gitignore`에 이미 등록되어 있습니다.

## 토큰 연장 (50일마다)
```bash
python -m igtool refresh-token
```
출력된 새 토큰으로 `.env` 파일과 GitHub Secrets의 `IG_ACCESS_TOKEN`을 바꿔 주세요.

## 공식 API로는 안 되는 것
- 남의 게시물에 댓글이나 좋아요 달기, 자동 팔로우·언팔로우는 공식 API에서 막혀 있습니다. 이런 기능을 쓰는 비공식 툴은 계정 정지 위험이 있습니다.
- 업로드할 이미지와 영상은 인터넷에서 열리는 공개 URL이어야 합니다.
- 스토리 업로드, DM 자동응답은 이 도구에 아직 들어 있지 않습니다.
