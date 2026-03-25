"""
sync_jobs 테이블 접근 — 동기화 작업 큐·상태
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from utils.common.id_utils import generate_id
from utils.database.db import execute, fetch_all, fetch_one

logger = logging.getLogger(__name__)


class SyncModel:
    async def create_job(self, user_id: str, provider: str) -> str:
        job_id = generate_id()
        await execute(
            """
            INSERT INTO sync_jobs (job_id, user_id, provider, status)
            VALUES (%s, %s, %s, 'pending')
            """,
            (job_id, user_id, provider),
        )
        return job_id

    async def get_pending_jobs(self) -> List[Dict[str, Any]]:
        rows = await fetch_all(
            """
            SELECT job_id, user_id, provider, status, started_at, completed_at,
                   last_synced_at, retry_count, max_retries, error_message,
                   created_at, updated_at
            FROM sync_jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            """,
            (),
        )
        return list(rows) if rows else []

    async def get_retryable_jobs(self) -> List[Dict[str, Any]]:
        rows = await fetch_all(
            """
            SELECT job_id, user_id, provider, status, started_at, completed_at,
                   last_synced_at, retry_count, max_retries, error_message,
                   created_at, updated_at
            FROM sync_jobs
            WHERE status = 'failed' AND retry_count < max_retries
            ORDER BY updated_at ASC
            """,
            (),
        )
        return list(rows) if rows else []

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        return await fetch_one(
            """
            SELECT job_id, user_id, provider, status, started_at, completed_at,
                   last_synced_at, retry_count, max_retries, error_message,
                   created_at, updated_at
            FROM sync_jobs
            WHERE job_id = %s
            """,
            (job_id,),
        )

    async def get_latest_job_for_user_provider(
        self, user_id: str, provider: str
    ) -> Optional[Dict[str, Any]]:
        """해당 사용자·provider의 가장 최근 sync_job (updated_at 기준)"""
        return await fetch_one(
            """
            SELECT job_id, user_id, provider, status, started_at, completed_at,
                   last_synced_at, retry_count, max_retries, error_message,
                   created_at, updated_at
            FROM sync_jobs
            WHERE user_id = %s AND provider = %s
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, provider),
        )

    async def update_job(
        self,
        job_id: str,
        status: str,
        *,
        started_at: Any = None,
        completed_at: Any = None,
        last_synced_at: Any = None,
        error_message: Optional[str] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        """동적 SET 절 — None이 아닌 인자만 반영"""
        sets = ["status = %s"]
        params: List[Any] = [status]
        if started_at is not None:
            sets.append("started_at = %s")
            params.append(started_at)
        if completed_at is not None:
            sets.append("completed_at = %s")
            params.append(completed_at)
        if last_synced_at is not None:
            sets.append("last_synced_at = %s")
            params.append(last_synced_at)
        if error_message is not None:
            sets.append("error_message = %s")
            params.append(error_message)
        if retry_count is not None:
            sets.append("retry_count = %s")
            params.append(retry_count)
        params.append(job_id)
        q = f"UPDATE sync_jobs SET {', '.join(sets)} WHERE job_id = %s"
        await execute(q, tuple(params))

    async def mark_job_completed(self, job_id: str) -> None:
        """성공 완료: 재시도 카운트 초기화, 마지막 동기화 시각 기록."""
        await execute(
            """
            UPDATE sync_jobs
            SET status = 'completed',
                completed_at = NOW(),
                last_synced_at = NOW(),
                retry_count = 0,
                error_message = NULL
            WHERE job_id = %s
            """,
            (job_id,),
        )

    async def increment_retry(self, job_id: str, err: str) -> Dict[str, Any]:
        """실패 시 retry_count +1 후 행 반환"""
        await execute(
            """
            UPDATE sync_jobs
            SET retry_count = retry_count + 1,
                error_message = %s,
                status = 'failed',
                completed_at = NOW()
            WHERE job_id = %s
            """,
            (err[:2000] if err else None, job_id),
        )
        row = await self.get_job_by_id(job_id)
        return row or {}

    async def mark_job_failed_permanent(self, job_id: str, err: str) -> None:
        """
        재시도 불가 실패(DB에 잘못된 provider 등).
        retry_count를 max_retries와 동일하게 맞춰 get_retryable_jobs에서 제외한다.
        """
        await execute(
            """
            UPDATE sync_jobs
            SET status = 'failed',
                completed_at = NOW(),
                error_message = %s,
                retry_count = max_retries
            WHERE job_id = %s
            """,
            (err[:2000] if err else None, job_id),
        )

    async def ensure_pending_job_after_connect(self, user_id: str, provider: str) -> None:
        """
        OAuth 연동 직후: 동일 user+provider에 pending/running 작업이 없으면 pending job 생성.
        """
        row = await fetch_one(
            """
            SELECT job_id FROM sync_jobs
            WHERE user_id = %s AND provider = %s AND status IN ('pending', 'running')
            LIMIT 1
            """,
            (user_id, provider),
        )
        if row:
            return
        await self.create_job(user_id, provider)
        logger.info("Ensured pending sync job: user_id=%s provider=%s", user_id, provider)

    async def ensure_recurring_github_jobs(self, min_interval_seconds: int = 900) -> None:
        """
        주기 동기화: GitHub 연동 사용자 중 completed 상태이고
        last_synced_at이 min_interval_seconds 이전이면 다시 pending.
        """
        users = await fetch_all(
            """
            SELECT user_id FROM connected_accounts
            WHERE provider = 'github' AND disconnected_at IS NULL
            """,
            (),
        )
        if not users:
            return
        threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=min_interval_seconds)
        for u in users:
            uid = u["user_id"]
            job = await fetch_one(
                """
                SELECT job_id, status, last_synced_at, retry_count, max_retries, started_at
                FROM sync_jobs
                WHERE user_id = %s AND provider = 'github'
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (uid,),
            )
            if not job:
                await self.create_job(uid, "github")
                continue
            st = job["status"]
            if st in ("pending", "running"):
                continue
            if st == "failed" and job["retry_count"] < job["max_retries"]:
                continue
            if st == "failed":
                continue
            if st != "completed":
                continue
            ls = job.get("last_synced_at")
            if ls is None or (isinstance(ls, datetime) and ls < threshold):
                await execute(
                    """
                    UPDATE sync_jobs
                    SET status = 'pending',
                        started_at = NULL,
                        completed_at = NULL,
                        error_message = NULL
                    WHERE job_id = %s
                    """,
                    (job["job_id"],),
                )
                logger.info("Re-queued sync job %s for user_id=%s", job["job_id"], uid)


sync_model = SyncModel()
