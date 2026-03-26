from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional


@dataclass(frozen=True)
class AuthContext:
    """세션에서 복원한 최소 인증 컨텍스트."""

    user_id: Optional[str] = None
    email: Optional[str] = None
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.user_id)

    def to_session_payload(self) -> dict[str, Any]:
        payload = {
            "userId": self.user_id,
            "email": self.email,
            "nickname": self.nickname,
            "profileImageUrl": self.profile_image_url,
        }
        return {key: value for key, value in payload.items() if value is not None}


def build_auth_context(session: Optional[Mapping[str, Any]]) -> AuthContext:
    """세션 딕셔너리에서 인증 컨텍스트를 복원한다."""
    session = session or {}
    return AuthContext(
        user_id=session.get("userId"),
        email=session.get("email"),
        nickname=session.get("nickname"),
        profile_image_url=session.get("profileImageUrl"),
    )


def write_auth_session(session: MutableMapping[str, Any], user: Mapping[str, Any]) -> AuthContext:
    """로그인된 사용자 정보를 세션 표준 형식으로 저장한다."""
    auth_context = AuthContext(
        user_id=str(user["userId"]),
        email=user.get("email"),
        nickname=user.get("nickname"),
        profile_image_url=user.get("profileImageUrl"),
    )
    session.clear()
    session.update(auth_context.to_session_payload())
    return auth_context


def clear_auth_session(session: MutableMapping[str, Any]) -> None:
    """웹 로그인 세션을 비운다."""
    session.clear()
