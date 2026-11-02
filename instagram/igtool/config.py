"""환경 변수와 .env 파일에서 설정을 읽는다."""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # instagram/


def _load_dotenv(path: Path) -> None:
    """의존성 없이 KEY=VALUE 형식의 .env 파일을 읽는다. 이미 설정된 환경 변수는 덮어쓰지 않는다."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class Config:
    access_token: str
    user_id: str
    graph_base: str
    graph_version: str
    claude_model: str
    brand_file: Path
    out_dir: Path

    @property
    def brand(self) -> str:
        if self.brand_file.exists():
            return self.brand_file.read_text(encoding="utf-8")
        return ""


def load_config(require_instagram: bool = True) -> Config:
    _load_dotenv(ROOT / ".env")
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    user_id = os.environ.get("IG_USER_ID", "me")
    if require_instagram and not token:
        raise SystemExit(
            "IG_ACCESS_TOKEN 이 설정되지 않았습니다. instagram/.env.example 을 참고해 instagram/.env 를 만들어 주세요."
        )
    # 'Instagram 로그인' 방식 토큰(IGAA...)은 graph.instagram.com,
    # 'Facebook 로그인' 방식 토큰(EAA...)은 graph.facebook.com 을 사용한다.
    default_base = "https://graph.facebook.com" if token.startswith("EAA") else "https://graph.instagram.com"
    return Config(
        access_token=token,
        user_id=user_id,
        graph_base=os.environ.get("IG_GRAPH_BASE", default_base).rstrip("/"),
        graph_version=os.environ.get("IG_GRAPH_VERSION", "v23.0"),
        claude_model=os.environ.get("IG_CLAUDE_MODEL", "claude-opus-5-5"),
        brand_file=Path(os.environ.get("IG_BRAND_FILE", ROOT / "brand.md")),
        out_dir=Path(os.environ.get("IG_OUT_DIR", ROOT / "out")),
    )
