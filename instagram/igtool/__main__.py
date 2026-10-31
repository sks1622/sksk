"""인스타그램 운영 도구.

사용법 (instagram/ 폴더에서):
  python -m igtool comments            답글 초안 만들기 (out/ 에 저장, 실제로 달지 않음)
  python -m igtool comments --auto     안전한 댓글에 바로 답글, 스팸은 숨김
  python -m igtool approve FILE        초안 파일을 검토한 뒤 실제로 답글 달기
  python -m igtool insights            성과 리포트 + 운영 조언
  python -m igtool ideas               다음 게시물 아이디어 추천
  python -m igtool caption "설명"      캡션과 해시태그 작성
  python -m igtool publish ...         게시물 업로드
  python -m igtool refresh-token       액세스 토큰 연장
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .ai import AI
from .config import load_config
from .graph import Graph, GraphError

# GitHub Actions 처럼 공개 로그가 남는 곳에서는 댓글 내용과 수치를 출력하지 않는다.
QUIET = os.environ.get("IG_QUIET_LOGS") == "1"


def log(msg: str, private: bool = False) -> None:
    if private and QUIET:
        return
    print(msg, flush=True)


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def save(cfg, name: str, text: str) -> Path:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.out_dir / name
    path.write_text(text, encoding="utf-8")
    return path


def parse_time(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z")


# ---------------------------------------------------------------- comments
def pending_comments(graph: Graph, username: str, posts: int, days: int) -> list[tuple[dict, list[dict]]]:
    """아직 내가 답하지 않은 다른 사람의 최상위 댓글을 게시물별로 모은다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = []
    for post in graph.recent_media(limit=posts):
        if not post.get("comments_count"):
            continue
        todo = []
        for c in graph.comments(post["id"]):
            if c.get("hidden") or c.get("username") == username or parse_time(c["timestamp"]) < cutoff:
                continue
            replies = c.get("replies", {}).get("data", [])
            if any(r.get("username") == username for r in replies):
                continue
            todo.append(c)
        if todo:
            result.append((post, todo))
    return result


def execute(graph: Graph, decision: dict) -> str:
    if decision["action"] == "reply" and decision["reply"].strip():
        graph.reply(decision["comment_id"], decision["reply"].strip())
        return "답글"
    if decision["action"] == "hide":
        graph.hide(decision["comment_id"])
        return "숨김"
    return "건너뜀"


def cmd_comments(args) -> None:
    cfg = load_config()
    graph, ai = Graph(cfg), AI(cfg)
    me = graph.profile()["username"]
    batches = pending_comments(graph, me, args.posts, args.days)
    total = sum(len(c) for _, c in batches)
    log(f"답하지 않은 댓글 {total}개 (최근 게시물 {args.posts}개, {args.days}일 이내)")
    if not total:
        return

    drafts, done, skipped = [], {"답글": 0, "숨김": 0}, 0
    for post, comments in batches:
        by_id = {c["id"]: c for c in comments}
        for d in ai.decide_replies(me, post, comments):
            c = by_id[d["comment_id"]]
            entry = {**d, "username": c.get("username"), "comment": c.get("text"),
                     "post": post.get("permalink")}
            if args.auto and d["action"] != "skip" and done["답글"] + done["숨김"] < args.max_actions:
                try:
                    kind = execute(graph, d)
                    done[kind] += 1
                    log(f"  [{kind}] @{c.get('username')}: {c.get('text')} -> {d['reply']}", private=True)
                    continue
                except GraphError as e:
                    entry["error"] = str(e)
                    log(f"  실패: {e}")
            if d["action"] == "skip":
                skipped += 1
            drafts.append(entry)

    if args.auto:
        log(f"완료: 답글 {done['답글']}개, 숨김 {done['숨김']}개, 직접 확인 필요 {skipped}개")
    if drafts and not QUIET:
        path = save(cfg, f"comments-{stamp()}.json", json.dumps(drafts, ensure_ascii=False, indent=2))
        md = ["# 댓글 처리 초안", "",
              f"검토 후 `python -m igtool approve {path}` 로 실행합니다.",
              "JSON 파일에서 답글을 고치거나, 원하지 않는 항목의 action 을 \"skip\" 으로 바꾸세요.", ""]
        for e in drafts:
            md += [f"## [{e['action']}] @{e['username']}", f"- 댓글: {e['comment']}",
                   f"- 답글: {e['reply'] or '-'}", f"- 이유: {e['reason']}", f"- 게시물: {e['post']}", ""]
        save(cfg, path.with_suffix(".md").name, "\n".join(md))
        log(f"초안 저장: {path} (.md 파일로 읽기 편하게 볼 수 있어요)")


def cmd_approve(args) -> None:
    cfg = load_config()
    graph = Graph(cfg)
    entries = json.loads(Path(args.file).read_text(encoding="utf-8"))
    counts = {"답글": 0, "숨김": 0, "건너뜀": 0}
    for e in entries:
        try:
            counts[execute(graph, e)] += 1
        except GraphError as err:
            log(f"실패 @{e.get('username')}: {err}")
    log(f"완료: 답글 {counts['답글']}개, 숨김 {counts['숨김']}개, 건너뜀 {counts['건너뜀']}개")


# ---------------------------------------------------------------- insights / ideas
def collect_stats(graph: Graph, posts: int, days: int) -> dict:
    profile = graph.profile()
    media = graph.recent_media(limit=posts)
    for m in media:
        m["insights"] = graph.media_insights(m["id"])
        m["caption"] = (m.get("caption") or "")[:300]
    return {"profile": profile, "account_insights_days": days,
            "account_insights": graph.account_insights(days), "recent_posts": media}


def cmd_insights(args) -> None:
    cfg = load_config()
    graph, ai = Graph(cfg), AI(cfg)
    data = collect_stats(graph, args.posts, args.days)
    report = ai.advise(
        f"최근 {args.days}일 계정 성과와 최근 게시물 {args.posts}개 데이터입니다. 다음 순서로 리포트를 작성해 주세요.\n"
        "1. 한눈에 보는 요약 (핵심 숫자 3~5개)\n"
        "2. 잘된 게시물 / 아쉬운 게시물과 그 이유 (형식, 주제, 캡션, 업로드 시간)\n"
        "3. 팔로워와 참여율에 대한 진단\n"
        "4. 이번 주에 바로 해볼 것 5가지 (구체적으로)\n"
        "5. 다음 주 업로드 계획 예시 (요일, 형식, 주제)",
        data,
    )
    ts = stamp()
    path = save(cfg, f"insights-{ts}.md", report)
    save(cfg, f"insights-{ts}.json", json.dumps(data, ensure_ascii=False, indent=2))
    log(report, private=True)
    log(f"\n리포트 저장: {path}")


def cmd_ideas(args) -> None:
    cfg = load_config(require_instagram=not args.offline)
    ai = AI(cfg)
    data = None if args.offline else collect_stats(Graph(cfg), 12, 30)
    text = ai.advise(
        f"다음 게시물 아이디어 {args.count}개를 추천해 주세요. {args.brief}\n"
        "각 아이디어마다: 형식(릴스/캐러셀/단일 이미지/스토리), 제목, 첫 1초 후킹 문구, 구성(장면 또는 슬라이드별),"
        " 캡션 초안, 해시태그 10~15개, 추천 업로드 요일과 시간, 이 아이디어를 고른 이유(데이터 근거).",
        data,
    )
    path = save(cfg, f"ideas-{stamp()}.md", text)
    log(text)
    log(f"\n저장: {path}")


def cmd_caption(args) -> None:
    cfg = load_config(require_instagram=False)
    text = AI(cfg).advise(
        f"다음 게시물의 캡션을 써 주세요: {args.brief}\n"
        "톤이 다른 캡션 3가지(짧은 버전, 스토리텔링 버전, 정보형 버전), 각각 첫 줄 후킹 문구 포함."
        " 공통 해시태그 15개(대형/중형/소형 태그 섞어서)와 댓글을 유도하는 마무리 질문 2개도 추가하세요.",
        effort="medium",
    )
    log(text)


def cmd_publish(args) -> None:
    cfg = load_config()
    caption = Path(args.caption_file).read_text(encoding="utf-8") if args.caption_file else (args.caption or "")
    kind = "릴스" if args.video else ("캐러셀" if len(args.image) > 1 else "이미지")
    log(f"[{kind}] 업로드 준비\n--- 캡션 ---\n{caption}\n------------")
    if args.dry_run:
        log("--dry-run: 실제로 업로드하지 않았습니다.")
        return
    graph = Graph(cfg)
    if args.video:
        res = graph.publish_reel(args.video, caption)
    elif len(args.image) > 1:
        res = graph.publish_carousel(args.image, caption)
    else:
        res = graph.publish_image(args.image[0], caption)
    link = graph.get(res["id"], fields="permalink").get("permalink")
    log(f"업로드 완료: {link}")


def cmd_refresh_token(args) -> None:
    cfg = load_config()
    if "graph.instagram.com" not in cfg.graph_base:
        sys.exit("Facebook 로그인 토큰은 Graph API 탐색기나 Meta 앱 대시보드에서 다시 발급해 주세요.")
    graph = Graph(cfg)
    data = graph._request("GET", f"{cfg.graph_base}/refresh_access_token", {"grant_type": "ig_refresh_token"})
    days = int(data.get("expires_in", 0)) // 86400
    log(f"새 토큰 ({days}일 유효). .env 와 GitHub Secrets 의 IG_ACCESS_TOKEN 을 이 값으로 바꾸세요:\n{data['access_token']}")


def main() -> None:
    p = argparse.ArgumentParser(prog="igtool", description="인스타그램 운영 도구")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("comments", help="새 댓글 확인 후 답글 초안 작성 / 자동 답글")
    c.add_argument("--auto", action="store_true", help="안전한 댓글은 바로 답글, 스팸은 숨김")
    c.add_argument("--posts", type=int, default=10, help="확인할 최근 게시물 수 (기본 10)")
    c.add_argument("--days", type=int, default=14, help="이 기간 이내의 댓글만 (기본 14일)")
    c.add_argument("--max-actions", type=int, default=20, help="한 번에 처리할 최대 답글/숨김 수 (기본 20)")
    c.set_defaults(func=cmd_comments)

    a = sub.add_parser("approve", help="검토한 초안 JSON 을 실제로 실행")
    a.add_argument("file")
    a.set_defaults(func=cmd_approve)

    i = sub.add_parser("insights", help="성과 리포트 + 운영 조언")
    i.add_argument("--days", type=int, default=7)
    i.add_argument("--posts", type=int, default=12)
    i.set_defaults(func=cmd_insights)

    d = sub.add_parser("ideas", help="게시물 아이디어 추천")
    d.add_argument("--count", type=int, default=5)
    d.add_argument("--brief", default="", help="원하는 주제나 상황 (예: '다음 주 신메뉴 출시')")
    d.add_argument("--offline", action="store_true", help="인스타그램 데이터 없이 브랜드 가이드만으로 추천")
    d.set_defaults(func=cmd_ideas)

    cp = sub.add_parser("caption", help="캡션과 해시태그 작성")
    cp.add_argument("brief", help="게시물 설명")
    cp.set_defaults(func=cmd_caption)

    pb = sub.add_parser("publish", help="게시물 업로드 (이미지/영상은 공개 URL 이어야 함)")
    pb.add_argument("--image", action="append", default=[], help="이미지 URL (여러 번 쓰면 캐러셀)")
    pb.add_argument("--video", help="릴스 영상 URL")
    pb.add_argument("--caption")
    pb.add_argument("--caption-file")
    pb.add_argument("--dry-run", action="store_true")
    pb.set_defaults(func=cmd_publish)

    r = sub.add_parser("refresh-token", help="액세스 토큰 연장 (60일마다 필요)")
    r.set_defaults(func=cmd_refresh_token)

    args = p.parse_args()
    if args.cmd == "publish" and not (args.image or args.video):
        p.error("--image 또는 --video 가 필요합니다.")
    try:
        args.func(args)
    except GraphError as e:
        sys.exit(f"Instagram API 오류: {e}")


if __name__ == "__main__":
    main()
