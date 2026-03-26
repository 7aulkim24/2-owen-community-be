from utils.auth import AuthContext, build_auth_context, clear_auth_session, require_owner, write_auth_session
from utils.errors.exceptions import APIError


def test_build_auth_context_from_session():
    """세션 딕셔너리에서 인증 컨텍스트를 복원한다."""
    auth = build_auth_context(
        {
            "userId": "u1",
            "email": "user@example.com",
            "nickname": "tester",
            "profileImageUrl": "/public/image/profile/u1.png",
        }
    )

    assert isinstance(auth, AuthContext)
    assert auth.is_authenticated is True
    assert auth.user_id == "u1"
    assert auth.email == "user@example.com"


def test_write_and_clear_auth_session():
    """로그인 세션 저장과 초기화 helper가 같은 규약을 사용한다."""
    session = {}

    auth = write_auth_session(
        session,
        {
            "userId": "u1",
            "email": "user@example.com",
            "nickname": "tester",
            "profileImageUrl": None,
        },
    )

    assert auth.user_id == "u1"
    assert session["userId"] == "u1"
    assert session["nickname"] == "tester"
    assert "profileImageUrl" not in session

    clear_auth_session(session)
    assert session == {}


def test_require_owner_allows_owner():
    """소유자 본인은 예외 없이 통과한다."""
    require_owner("u1", "u1", resource="게시글", resource_id="p1")


def test_require_owner_rejects_non_owner():
    """소유자가 아니면 FORBIDDEN 예외가 발생한다."""
    try:
        require_owner("u1", "u2", resource="게시글", resource_id="p1")
    except APIError as exc:
        assert exc.code.name == "FORBIDDEN"
        assert exc.details["resource"] == "게시글"
        return

    raise AssertionError("소유자가 아닌 접근에서는 APIError 가 발생해야 합니다")
