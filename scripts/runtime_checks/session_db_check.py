#!/usr/bin/env python3
"""
세션 DB 저장 확인(런타임 체크)
"""
from utils.database.db import fetch_all, fetch_one


def check_session_storage() -> bool:
    print("=" * 60)
    print("  세션 DB 저장 확인")
    print("=" * 60)

    try:
        active_sessions = fetch_all(
            "SELECT session_key, user_id, expires_at, created_at "
            "FROM sessions WHERE expires_at > NOW() ORDER BY created_at DESC LIMIT 5"
        )

        if active_sessions:
            print(f"\n✅ 활성 세션 {len(active_sessions)}개 발견:")
            for i, session in enumerate(active_sessions, 1):
                print(f"\n  세션 {i}:")
                print(f"    - 세션 키: {session['session_key'][:20]}...")
                print(f"    - 사용자 ID: {session.get('user_id', 'N/A')}")
                print(f"    - 만료 시간: {session.get('expires_at')}")
                print(f"    - 생성 시간: {session.get('created_at')}")
        else:
            print("\n⚠️  활성 세션이 없습니다 (모든 세션이 만료되었거나 로그아웃됨)")

        expired_count = fetch_one("SELECT COUNT(*) as cnt FROM sessions WHERE expires_at <= NOW()")
        if expired_count and expired_count.get("cnt", 0) > 0:
            print(f"\n⚠️  만료된 세션 {expired_count['cnt']}개 존재")

        total_count = fetch_one("SELECT COUNT(*) as cnt FROM sessions")
        print(f"\n📊 전체 세션 수: {total_count.get('cnt', 0) if total_count else 0}")

        return True
    except Exception as e:
        print(f"\n❌ 세션 조회 실패: {e}")
        return False


if __name__ == "__main__":
    check_session_storage()

