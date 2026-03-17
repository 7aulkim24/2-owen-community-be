#!/usr/bin/env python3
"""
DB 연결 및 테이블/세션 스키마 존재 여부 검증 스크립트
"""
import sys

from utils.database.db import fetch_all, fetch_one


def check_db_connection() -> bool:
    """DB 연결 및 필수 테이블 확인"""
    try:
        result = fetch_one("SELECT 1 as test")
        if result and result.get("test") == 1:
            print("✅ DB 연결 성공")
        else:
            print("❌ DB 연결 실패: 쿼리 결과가 예상과 다름")
            return False
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return False

    required_tables = ["users", "posts", "comments", "post_likes", "sessions"]
    missing_tables = []

    for table in required_tables:
        try:
            result = fetch_one(f"SELECT COUNT(*) as cnt FROM {table}")
            if result is not None:
                print(f"✅ 테이블 '{table}' 존재 확인 (레코드 수: {result.get('cnt', 0)})")
            else:
                missing_tables.append(table)
        except Exception as e:
            print(f"❌ 테이블 '{table}' 확인 실패: {e}")
            missing_tables.append(table)

    if missing_tables:
        print(f"\n⚠️  누락된 테이블: {', '.join(missing_tables)}")
        return False

    # 세션 테이블 구조 확인
    try:
        result = fetch_all("SHOW COLUMNS FROM sessions")
        if result:
            columns = [col["Field"] for col in result]
            required_columns = ["session_key", "user_id", "data", "expires_at"]
            missing_columns = [col for col in required_columns if col not in columns]

            if missing_columns:
                print(f"⚠️  세션 테이블에 누락된 컬럼: {', '.join(missing_columns)}")
            else:
                print(f"✅ 세션 테이블 구조 정상 (컬럼: {', '.join(columns)})")
        else:
            print("⚠️  세션 테이블 구조 확인 불가")
    except Exception as e:
        print(f"⚠️  세션 테이블 구조 확인 실패: {e}")

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("DB 연결 및 테이블 검증 시작")
    print("=" * 50)

    success = check_db_connection()

    print("=" * 50)
    if success:
        print("✅ 모든 검증 통과")
        sys.exit(0)
    else:
        print("❌ 일부 검증 실패")
        sys.exit(1)

