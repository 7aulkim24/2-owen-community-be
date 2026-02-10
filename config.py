"""
환경 설정 관리
pydantic-settings를 사용하여 타입 안전성과 자동 검증을 제공합니다.
"""

from pydantic_settings import BaseSettings


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

    # DB 설정
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str
    db_pool_size: int = 5

    # 디버그 모드
    debug: bool = False

    # CORS 설정
    allowed_origins: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        case_sensitive = False  # 환경 변수명 대소문자 구분하지 않음


# 설정 인스턴스 생성 (서버 시작 시 자동 검증)
settings = Settings()
