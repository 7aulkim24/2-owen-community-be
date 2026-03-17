#!/usr/bin/env python3
"""
API 통합 테스트(런타임 체크):
- Health check
- 게시글 목록(비인증)
- 회원가입/로그인(세션 생성)
- 인증된 요청(/v1/auth/me)
- 로그아웃(세션 삭제)
"""
import json
from datetime import datetime

import requests


BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_health() -> bool:
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health Check 성공: {data.get('data', {}).get('status')}")
        return True
    except Exception as e:
        print(f"❌ Health Check 실패: {e}")
        return False


def check_posts_list() -> bool:
    print_section("2. 게시글 목록 조회 (인증 불필요)")
    try:
        response = requests.get(f"{BASE_URL}/v1/posts?offset=0&limit=10", timeout=5)
        response.raise_for_status()
        data = response.json()
        items = data.get("data", {}).get("items", [])
        pagination = data.get("data", {}).get("pagination", {})
        print("✅ 게시글 목록 조회 성공")
        print(f"   - 게시글 수: {len(items)}")
        print(f"   - 전체 게시글 수: {pagination.get('totalCount', 0)}")
        return True
    except Exception as e:
        print(f"❌ 게시글 목록 조회 실패: {e}")
        return False


def signup_and_login() -> tuple[requests.Session | None, str | None]:
    print_section("3. 회원가입 및 로그인 (세션 생성)")

    # 닉네임 최대 10자, 비밀번호 허용 특수문자(@$!%*?&) 고려
    timestamp = datetime.now().strftime("%H%M%S")
    test_email = f"test{timestamp}@example.com"
    test_password = "Test1234@$"
    test_nickname = f"test{timestamp}"

    session = requests.Session()

    try:
        response = session.post(
            f"{BASE_URL}/v1/auth/signup",
            json={"email": test_email, "password": test_password, "nickname": test_nickname},
            timeout=5,
        )
        response.raise_for_status()
        print("✅ 회원가입 성공")
        print(f"   - 이메일: {test_email}")
        print(f"   - 닉네임: {test_nickname}")

        response = session.post(
            f"{BASE_URL}/v1/auth/login",
            json={"email": test_email, "password": test_password},
            timeout=5,
        )
        response.raise_for_status()
        login_result = response.json()

        session_cookie = session.cookies.get_dict().get("session")
        if session_cookie:
            print("✅ 로그인 성공 (세션 쿠키 생성됨)")
            print(f"   - 세션 쿠키 존재: {bool(session_cookie)}")
            print(f"   - 사용자 ID: {login_result.get('data', {}).get('userId', 'N/A')}")
            return session, test_email

        print("⚠️  로그인 성공했으나 세션 쿠키가 없음")
        return None, None

    except requests.exceptions.HTTPError as e:
        print(f"❌ 회원가입/로그인 실패: HTTP {e.response.status_code}")
        if e.response.text:
            try:
                error_data = e.response.json()
                print(f"   에러 코드: {error_data.get('code', 'N/A')}")
                print(f"   에러 메시지: {error_data.get('message', 'N/A')}")
                details = error_data.get("details", {})
                if details:
                    print(f"   상세 에러: {json.dumps(details, indent=2, ensure_ascii=False)}")
                else:
                    print(f"   전체 응답: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except Exception:
                print(f"   응답: {e.response.text[:500]}")
        return None, None
    except Exception as e:
        print(f"❌ 회원가입/로그인 실패: {e}")
        return None, None


def check_auth_me(session: requests.Session | None) -> bool:
    print_section("4. 인증된 요청 테스트 (/v1/auth/me)")
    if not session:
        print("⚠️  세션이 없어 테스트 스킵")
        return False

    try:
        response = session.get(f"{BASE_URL}/v1/auth/me", timeout=5)
        response.raise_for_status()
        data = response.json()
        user_data = data.get("data", {})
        print("✅ 인증된 요청 성공")
        print(f"   - 사용자 ID: {user_data.get('userId', 'N/A')}")
        print(f"   - 이메일: {user_data.get('email', 'N/A')}")
        print(f"   - 닉네임: {user_data.get('nickname', 'N/A')}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ 인증된 요청 실패: HTTP {e.response.status_code}")
        if e.response.status_code == 401:
            print("   - 세션 쿠키가 유효하지 않거나 만료됨")
        return False
    except Exception as e:
        print(f"❌ 인증된 요청 실패: {e}")
        return False


def check_logout(session: requests.Session | None) -> bool:
    print_section("5. 로그아웃 테스트 (세션 삭제)")
    if not session:
        print("⚠️  세션이 없어 테스트 스킵")
        return False

    try:
        response = session.post(f"{BASE_URL}/v1/auth/logout", timeout=5)
        response.raise_for_status()
        print("✅ 로그아웃 성공")

        response = session.get(f"{BASE_URL}/v1/auth/me", timeout=5)
        if response.status_code == 401:
            print("✅ 세션 삭제 확인됨 (로그아웃 후 인증 실패)")
            return True
        print("⚠️  로그아웃 후에도 인증이 성공함 (세션 삭제 미확인)")
        return False
    except Exception as e:
        print(f"❌ 로그아웃 테스트 실패: {e}")
        return False


def main() -> int:
    print("\n" + "=" * 60)
    print("  API 통합 테스트 시작")
    print("=" * 60)

    results: list[tuple[str, bool]] = []

    results.append(("Health Check", check_health()))
    results.append(("게시글 목록 조회", check_posts_list()))

    session, _ = signup_and_login()
    results.append(("회원가입/로그인", session is not None))

    if session:
        results.append(("인증된 요청", check_auth_me(session)))
        results.append(("로그아웃", check_logout(session)))

    print_section("테스트 결과 요약")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        print(f"  {name}: {'✅ 통과' if ok else '❌ 실패'}")

    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed * 100 // total}%)")

    if passed == total:
        print("\n✅ 모든 테스트 통과!")
        return 0

    print(f"\n⚠️  {total - passed}개 테스트 실패")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

