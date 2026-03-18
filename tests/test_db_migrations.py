"""
Phase 1 Unit 1 — DB 마이그레이션 검증 테스트

connected_accounts, activity_events, sync_jobs, activity_summaries 테이블이
올바르게 생성되었는지 확인합니다.
"""

import asyncio

import pytest

from tests.helpers.db_seed import seed_database


@pytest.fixture(autouse=True)
def setup_db():
    """DB 풀 초기화 및 시드 (기존 test_api와 동일)"""
    seed_database()
    yield


@pytest.fixture
def db():
    """동기 래퍼: DB 쿼리 실행 (fetch_all). 각 호출마다 새 풀 사용(이벤트 루프 충돌 방지)."""
    import utils.database.db as db_mod

    async def _run_query(query: str, params=None):
        from utils.database.db import fetch_all, init_pool, close_pool

        db_mod._pool = None
        await init_pool()
        try:
            return await fetch_all(query, params)
        finally:
            await close_pool()
            db_mod._pool = None

    def sync_query(query: str, params=None):
        return asyncio.run(_run_query(query, params))

    yield sync_query


def test_phase1_tables_exist(db):
    """Phase 1 Unit 1 테이블 4개가 존재하는지 확인"""
    rows = db(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name IN ('connected_accounts', 'activity_events', 'sync_jobs', 'activity_summaries')
        ORDER BY table_name
        """
    )
    found = {r.get("table_name") or r.get("TABLE_NAME") for r in rows}
    expected = {"connected_accounts", "activity_events", "sync_jobs", "activity_summaries"}
    assert found == expected, f"누락된 테이블: {expected - found}"


def test_connected_accounts_columns_and_constraints(db):
    """connected_accounts 테이블 컬럼 및 UNIQUE KEY 확인"""
    rows = db(
        """
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'connected_accounts'
        ORDER BY ordinal_position
        """
    )
    columns = {r.get("column_name") or r.get("COLUMN_NAME") for r in rows}
    required = {
        "account_id",
        "user_id",
        "provider",
        "provider_user_id",
        "provider_username",
        "access_token",
        "refresh_token",
        "token_expires_at",
        "scopes",
        "connected_at",
        "updated_at",
        "disconnected_at",
    }
    assert required.issubset(columns), f"누락된 컬럼: {required - columns}"

    # UNIQUE KEY uq_user_provider 확인
    rows = db(
        """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = DATABASE() AND table_name = 'connected_accounts'
        AND constraint_type = 'UNIQUE'
        """
    )
    names = {r.get("constraint_name") or r.get("CONSTRAINT_NAME") for r in rows}
    assert "uq_user_provider" in names


def test_activity_events_columns_and_unique_key(db):
    """activity_events 테이블 컬럼 및 UNIQUE KEY 확인"""
    rows = db(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'activity_events'
        ORDER BY ordinal_position
        """
    )
    columns = {r.get("column_name") or r.get("COLUMN_NAME") for r in rows}
    required = {
        "event_id",
        "user_id",
        "provider",
        "event_type",
        "external_id",
        "title",
        "description",
        "event_url",
        "repo_name",
        "event_metadata",
        "event_occurred_at",
        "created_at",
    }
    assert required.issubset(columns), f"누락된 컬럼: {required - columns}"

    rows = db(
        """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = DATABASE() AND table_name = 'activity_events'
        AND constraint_type = 'UNIQUE'
        """
    )
    names = {r.get("constraint_name") or r.get("CONSTRAINT_NAME") for r in rows}
    assert "uq_provider_external" in names


def test_sync_jobs_columns(db):
    """sync_jobs 테이블 컬럼 확인"""
    rows = db(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'sync_jobs'
        ORDER BY ordinal_position
        """
    )
    columns = {r.get("column_name") or r.get("COLUMN_NAME") for r in rows}
    required = {
        "job_id",
        "user_id",
        "provider",
        "status",
        "started_at",
        "completed_at",
        "last_synced_at",
        "retry_count",
        "max_retries",
        "error_message",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"누락된 컬럼: {required - columns}"


def test_activity_summaries_columns_and_unique_key(db):
    """activity_summaries 테이블 컬럼 및 UNIQUE KEY, post_id FK 확인"""
    rows = db(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'activity_summaries'
        ORDER BY ordinal_position
        """
    )
    columns = {r.get("column_name") or r.get("COLUMN_NAME") for r in rows}
    required = {
        "summary_id",
        "user_id",
        "summary_date",
        "summary_type",
        "event_count",
        "providers",
        "generated_title",
        "generated_content",
        "post_id",
        "status",
        "created_at",
        "updated_at",
    }
    assert required.issubset(columns), f"누락된 컬럼: {required - columns}"

    rows = db(
        """
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_schema = DATABASE() AND table_name = 'activity_summaries'
        AND constraint_type = 'UNIQUE'
        """
    )
    names = {r.get("constraint_name") or r.get("CONSTRAINT_NAME") for r in rows}
    assert "uq_user_date_type" in names


def test_existing_tables_unchanged(db):
    """기존 테이블(users, posts, comments)이 그대로 존재하는지 확인"""
    rows = db(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name IN ('users', 'posts', 'comments')
        """
    )
    found = {r.get("table_name") or r.get("TABLE_NAME") for r in rows}
    assert found == {"users", "posts", "comments"}
