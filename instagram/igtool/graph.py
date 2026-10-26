"""Instagram Graph API(공식 API) 클라이언트.

비즈니스/크리에이터 계정 전용. 필요한 권한:
  instagram_business_basic, instagram_business_manage_comments,
  instagram_business_content_publish, instagram_business_manage_insights
(Facebook 로그인 방식이면 instagram_basic, instagram_manage_comments,
 instagram_content_publish, instagram_manage_insights, pages_show_list)
"""

import time
from typing import Any, Iterator

import requests

from .config import Config

MEDIA_FIELDS = "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count"
COMMENT_FIELDS = "id,text,username,timestamp,like_count,hidden,replies{id,text,username,timestamp}"

ACCOUNT_METRICS = [
    "reach", "views", "accounts_engaged", "total_interactions",
    "likes", "comments", "shares", "saves", "follows_and_unfollows", "profile_links_taps",
]
MEDIA_METRICS = ["reach", "views", "likes", "comments", "shares", "saved", "total_interactions"]


class GraphError(RuntimeError):
    pass


class Graph:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.base = f"{cfg.graph_base}/{cfg.graph_version}"
        self.session = requests.Session()

    # ---- 저수준 요청 ----
    def _request(self, method: str, url: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["access_token"] = self.cfg.access_token
        resp = self.session.request(method, url, params=params if method == "GET" else None,
                                    data=params if method != "GET" else None, timeout=60)
        try:
            data = resp.json()
        except ValueError:
            raise GraphError(f"{resp.status_code} 응답을 해석할 수 없습니다: {resp.text[:200]}")
        if "error" in data:
            err = data["error"]
            raise GraphError(f"[{err.get('code')}] {err.get('message')}")
        return data

    def get(self, path: str, **params: Any) -> dict:
        return self._request("GET", f"{self.base}/{path}", params)

    def post(self, path: str, **params: Any) -> dict:
        return self._request("POST", f"{self.base}/{path}", params)

    def paginate(self, path: str, max_items: int | None = None, **params: Any) -> Iterator[dict]:
        data = self.get(path, **params)
        count = 0
        while True:
            for item in data.get("data", []):
                yield item
                count += 1
                if max_items and count >= max_items:
                    return
            next_url = data.get("paging", {}).get("next")
            if not next_url:
                return
            data = self._request("GET", next_url)  # next URL 에 이미 파라미터가 포함되어 있음

    # ---- 계정 / 게시물 ----
    def profile(self) -> dict:
        return self.get(self.cfg.user_id, fields="id,username,name,followers_count,follows_count,media_count")

    def recent_media(self, limit: int = 10) -> list[dict]:
        return list(self.paginate(f"{self.cfg.user_id}/media", max_items=limit, fields=MEDIA_FIELDS))

    # ---- 댓글 ----
    def comments(self, media_id: str) -> list[dict]:
        return list(self.paginate(f"{media_id}/comments", fields=COMMENT_FIELDS))

    def reply(self, comment_id: str, message: str) -> dict:
        return self.post(f"{comment_id}/replies", message=message)

    def hide(self, comment_id: str) -> dict:
        return self.post(comment_id, hide="true")

    # ---- 인사이트 ----
    def _insights(self, path: str, metrics: list[str], **params: Any) -> dict[str, Any]:
        """지표를 한 번에 요청하고, 실패하면 지원되지 않는 지표를 건너뛰며 하나씩 다시 요청한다."""
        def parse(data: dict) -> dict[str, Any]:
            out = {}
            for m in data.get("data", []):
                if "total_value" in m:
                    tv = m["total_value"]
                    out[m["name"]] = tv.get("breakdowns") or tv.get("value")
                elif m.get("values"):
                    out[m["name"]] = sum(v.get("value", 0) for v in m["values"] if isinstance(v.get("value"), (int, float)))
            return out

        try:
            return parse(self.get(path, metric=",".join(metrics), **params))
        except GraphError:
            result: dict[str, Any] = {}
            for metric in metrics:
                try:
                    result.update(parse(self.get(path, metric=metric, **params)))
                except GraphError:
                    continue
            return result

    def account_insights(self, days: int = 7) -> dict[str, Any]:
        until = int(time.time())
        since = until - days * 86400
        return self._insights(f"{self.cfg.user_id}/insights", ACCOUNT_METRICS,
                              period="day", metric_type="total_value", since=since, until=until)

    def media_insights(self, media_id: str) -> dict[str, Any]:
        return self._insights(f"{media_id}/insights", MEDIA_METRICS)

    # ---- 게시 ----
    def _wait_container(self, container_id: str, timeout: int = 300) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get(container_id, fields="status_code").get("status_code")
            if status == "FINISHED":
                return
            if status in ("ERROR", "EXPIRED"):
                raise GraphError(f"미디어 처리 실패: {status}")
            time.sleep(5)
        raise GraphError("미디어 처리 대기 시간이 초과되었습니다.")

    def _publish(self, container_id: str) -> dict:
        self._wait_container(container_id)
        return self.post(f"{self.cfg.user_id}/media_publish", creation_id=container_id)

    def publish_image(self, image_url: str, caption: str) -> dict:
        c = self.post(f"{self.cfg.user_id}/media", image_url=image_url, caption=caption)
        return self._publish(c["id"])

    def publish_reel(self, video_url: str, caption: str) -> dict:
        c = self.post(f"{self.cfg.user_id}/media", media_type="REELS", video_url=video_url, caption=caption)
        return self._publish(c["id"])

    def publish_carousel(self, image_urls: list[str], caption: str) -> dict:
        children = [
            self.post(f"{self.cfg.user_id}/media", image_url=url, is_carousel_item="true")["id"]
            for url in image_urls
        ]
        for child in children:
            self._wait_container(child)
        c = self.post(f"{self.cfg.user_id}/media", media_type="CAROUSEL",
                      children=",".join(children), caption=caption)
        return self._publish(c["id"])
