"""
Phase 1 Unit 4 완료 기준 체크리스트 검증

1. activity_summaries에 (user_id, summary_date) 기준 레코드 생성
2. 동일 날짜 재생성 시 동일 summary_id·행 1건 (UPDATE 경로)
3. generated_title / generated_content에 이벤트 기반 내용
4. status = 'generated'
5. summary_service 예외 시 sync_job은 completed 유지 (increment_retry 미호출)

통합 테스트는 MySQL(prooflog_test)이 필요합니다. DB 없으면 스킵됩니다.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# conftest와 동일: 앱 루트 탐색
def _app_root() -> Path:
    here = Path(__file__).resolve().parent
    for parent in [here, *here.parents]:
        for cand in (parent, parent / "2-owen-community-be"):
            if (cand / "main.py").is_file() and (cand / "models").is_dir():
                return cand.resolve()
    raise RuntimeError("앱 루트를 찾을 수 없습니다.")


ROOT = _app_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_NAME", "prooflog_test")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-client-secret")
os.environ.setdefault(
    "TOKEN_ENCRYPT_KEY",
    "sneykqErN0KOArVsMTlsCO8tBxOkfuFOZ2qvNWWwZP0=",
)
os.environ.setdefault("DISABLE_SYNC_SCHEDULER", "1")

from tests.helpers.db_seed import seed_database  # noqa: E402


def _async_run(coro):
    import utils.database.db as db_mod
    from utils.database.db import close_pool, init_pool

    async def _inner():
        db_mod._pool = None
        await init_pool()
        try:
            return await coro
        finally:
            await close_pool()
            db_mod._pool = None

    return asyncio.run(_inner())


@pytest.mark.skipif(
    os.environ.get("SKIP_DB_INTEGRATION", "").strip().lower() in ("1", "true", "yes"),
    reason="SKIP_DB_INTEGRATION=1",
)
def test_unit4_checklist_db_integration():
    """체크리스트 1~4: 실제 DB + activity_events → summary 파이프라인"""

    async def ping_db():
        from utils.database.db import fetch_one

        await fetch_one("SELECT 1 AS ok", ())

    try:
        _async_run(ping_db)
    except Exception as e:
        pytest.skip(f"MySQL(prooflog_test) 없음 또는 연결 실패 — 로컬에서 확인: {e}")

    seed_database()

    async def body():
        from utils.database.db import execute, fetch_all, fetch_one

        from models.activity_model import activity_model
        from models.user_model import user_model
        from services.summary_service import summary_service

        await execute("DELETE FROM activity_summaries")
        await execute("DELETE FROM activity_events")

        u = await user_model.getUserByEmail("admin@test.com")
        assert u is not None
        uid = u["userId"]

        summary_d = date(2030, 1, 15)
        occurred = datetime(2030, 1, 15, 14, 30, 0)

        ev_rows = [
            {
                "event_id": activity_model.new_event_id(),
                "user_id": uid,
                "provider": "github",
                "event_type": "push",
                "external_id": "unit4-ext-push-1",
                "title": "Push",
                "description": "3 commit(s)",
                "event_url": None,
                "repo_name": "acme/app",
                "event_metadata": None,
                "event_occurred_at": occurred,
            },
            {
                "event_id": activity_model.new_event_id(),
                "user_id": uid,
                "provider": "github",
                "event_type": "pull_request",
                "external_id": "unit4-ext-pr-1",
                "title": "Fix thing",
                "description": None,
                "event_url": "https://github.com/acme/app/pull/1",
                "repo_name": "acme/app",
                "event_metadata": None,
                "event_occurred_at": occurred,
            },
        ]
        await activity_model.insert_events_ignore(ev_rows)

        sid1 = await summary_service.generate_daily_summary(uid, summary_d)
        assert sid1, "요약이 생성되어 summary_id가 반환되어야 함"

        row = await fetch_one(
            """
            SELECT summary_id, user_id, summary_date, generated_title, generated_content, status, event_count
            FROM activity_summaries
            WHERE user_id = %s AND summary_date = %s AND summary_type = 'daily'
            """,
            (uid, summary_d),
        )
        assert row is not None
        assert row["user_id"] == uid
        assert row["summary_date"] == summary_d
        assert row["status"] == "generated"
        assert row["event_count"] == 2

        title = row["generated_title"] or ""
        content = row["generated_content"] or ""
        assert "커밋" in content or "3" in content
        assert "PR" in title or "PR" in content
        assert "acme/app" in content

        sid2 = await summary_service.generate_daily_summary(uid, summary_d)
        assert sid2 == sid1

        cnt_rows = await fetch_all(
            """
            SELECT COUNT(*) AS c FROM activity_summaries
            WHERE user_id = %s AND summary_date = %s AND summary_type = 'daily'
            """,
            (uid, summary_d),
        )
        assert int(cnt_rows[0]["c"]) == 1

        row2 = await fetch_one(
            """
            SELECT summary_id, updated_at FROM activity_summaries
            WHERE summary_id = %s
            """,
            (sid1,),
        )
        assert row2["summary_id"] == sid1

    _async_run(body)


def test_unit4_checklist_sync_stays_completed_on_summary_error():
    """체크리스트 5: 요약 단계 예외 시에도 sync는 completed, 재시도 없음"""

    async def body():
        row = {
            "job_id": "01HZTESTJOB000000000000000",
            "user_id": "01HZTESTUSER00000000000000",
            "provider": "github",
            "last_synced_at": None,
        }
        with (
            patch(
                "services.sync_service.sync_model.update_job",
                new_callable=AsyncMock,
            ),
            patch(
                "services.sync_service.sync_model.mark_job_completed",
                new_callable=AsyncMock,
            ) as mc,
            patch(
                "services.sync_service.sync_model.increment_retry",
                new_callable=AsyncMock,
            ) as ir,
            patch(
                "services.sync_service.github_sync_service.sync_github_events_for_user",
                new_callable=AsyncMock,
                return_value=(1, frozenset({date(2030, 1, 15)})),
            ),
            patch(
                "services.sync_service.summary_service.generate_daily_summary",
                new_callable=AsyncMock,
                side_effect=RuntimeError("summary pipeline failed"),
            ),
        ):
            from services.sync_service import dispatch_sync_job

            await dispatch_sync_job(row)

        mc.assert_awaited_once()
        ir.assert_not_awaited()

    asyncio.run(body())
