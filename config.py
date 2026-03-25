"""
환경 설정 관리
pydantic-settings를 사용하여 타입 안전성과 자동 검증을 제공합니다.
"""

import os
from typing import Optional
from urllib.parse import urlparse

from pydantic_settings import BaseSettings


def _is_loopback_origin(origin: str) -> bool:
    """CORS 목록에 공인 도메인이 앞에 있어도 OAuth 리다이렉트는 루프백 FE를 우선."""
    try:
        parsed = urlparse(origin.strip())
        host = (parsed.hostname or "").lower()
        return host in ("localhost", "127.0.0.1")
    except Exception:
        return False


def _ensure_token_encrypt_key_from_legacy_env() -> None:
    """
    프로젝트 루트 .env 등에서 예전 이름(INTEGRATION_TOKEN_ENCRYPTION_KEY)만
    정의된 경우 TOKEN_ENCRYPT_KEY로 맞춥니다. dev.sh는 ../.env 를 export 하므로
    여기서 통일해야 Settings 검증이 통과합니다.
    """
    if os.environ.get("TOKEN_ENCRYPT_KEY"):
        return
    legacy = os.environ.get("INTEGRATION_TOKEN_ENCRYPTION_KEY")
    if legacy:
        os.environ["TOKEN_ENCRYPT_KEY"] = legacy


class Settings(BaseSettings):
    """환경 설정 클래스"""

    # 쿠키 보안 설정 (환경별)
    cookie_secure: bool = False  # 로컬: False (HTTP에서도 작동), 배포: True (HTTPS만 작동)
    cookie_samesite: str = "lax"  # 로컬: "lax" (같은 도메인 내 cross-site 요청 허용), 배포: "strict"
    session_cookie_name: str = "session"

    # 세션 설정
    session_timeout: int = 86400  # 24시간 (초 단위)

    # 보안 키
    secret_key: str

    # CORS 설정 (쉼표로 구분된 URL 목록)
    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    # 로컬 개발: FE가 Live Server 등으로 임의 포트를 쓸 때 .env 누락을 보완
    # 프로덕션에서 완전 차단하려면 환경 변수로 빈 문자열("")을 주면 비활성화됨
    cors_allow_origin_regex: Optional[str] = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    )

    # OAuth 콜백 후 브라우저 리다이렉트용 프론트 베이스 URL
    # 미설정 시 allowed_origins 중 localhost/127.0.0.1 을 먼저 쓰고, 없으면 목록 첫 항목
    frontend_url: Optional[str] = None

    # DB 설정
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    db_pool_size: int = 5

    # GitHub 설정 (OAuth 연동용 — .env 필수)
    github_client_id: str
    github_client_secret: str
    github_callback_url: str = "http://localhost:8000/v1/integrations/github/callback"
    # Fernet URL-safe base64 키(44자). 생성: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # 환경 변수명: TOKEN_ENCRYPT_KEY (호환: INTEGRATION_TOKEN_ENCRYPTION_KEY → config 로드 시 TOKEN_ENCRYPT_KEY 로 승격)
    token_encrypt_key: str
    
    # 디버그 모드
    debug: bool = False

    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        case_sensitive = False  # 환경 변수명 대소문자 구분하지 않음

    def get_allowed_origins_list(self) -> list:
        """CORS allowed origins를 리스트로 반환"""
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        if origins:
            return origins
        return ["http://localhost:5500", "http://127.0.0.1:5500"]

    def get_frontend_base_url(self) -> str:
        """OAuth 콜백 등 브라우저 리다이렉트용 프론트 오리진 (슬래시 없음)"""
        if self.frontend_url and str(self.frontend_url).strip():
            return str(self.frontend_url).strip().rstrip("/")
        origins = self.get_allowed_origins_list()
        if not origins:
            return "http://localhost:5500"
        # dev.sh 등이 붙이는 :5500 루프백을, 포트 없는 http://localhost 보다 우선
        for o in origins:
            if _is_loopback_origin(o) and ":5500" in o:
                return o.rstrip("/")
        for o in origins:
            if _is_loopback_origin(o):
                return o.rstrip("/")
        return origins[0].rstrip("/")

# 설정 인스턴스 생성 (서버 시작 시 자동 검증)
_ensure_token_encrypt_key_from_legacy_env()
settings = Settings()
