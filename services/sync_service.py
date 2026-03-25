"""
sync_jobs 폴링 스케줄러 및 동기화 디스패치
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from models.sync_model import sync_model
from services.github_sync_service import github_sync_service
from services.summary_service import summary_service

logger = logging.getLogger(__name__)

# 로드맵: 기본 15분 주기 (환경별 조정은 추후 config로)
SYNC_INTERVAL_SECONDS = 900

# DB에 잘못된 provider가 들어온 경우 재시도해도 의미 없음 → mark_job_failed_permanent
SUPPORTED_SYNC_PROVIDERS = frozenset({"github"})


async def dispatch_sync_job(row: Dict[str, Any]) -> None:
    """단일 sync_job 실행 — running → completed | failed(+retry)"""
    job_id = row["job_id"]
    user_id = row["user_id"]
    provider = row["provider"]
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

    await sync_model.update_job(job_id, "running", started_at=now_naive)

    if provider not in SUPPORTED_SYNC_PROVIDERS:
        msg = f"지원하지 않는 provider: {provider}"
        logger.error(
            "Sync job aborted (non-retriable) job_id=%s user_id=%s %s",
            job_id,
            user_id,
            msg,
        )
        await sync_model.mark_job_failed_permanent(job_id, msg)
        return

    try:
        _inserted, summary_dates = await github_sync_service.sync_github_events_for_user(
            user_id, row.get("last_synced_at")
        )
        await sync_model.mark_job_completed(job_id)
        logger.info("Sync job completed job_id=%s user_id=%s provider=%s", job_id, user_id, provider)
        for summary_d in sorted(summary_dates):
            try:
                await summary_service.generate_daily_summary(user_id, summary_d)
            except Exception:
                logger.exception(
                    "Daily summary generation failed (sync already completed) "
                    "job_id=%s user_id=%s summary_date=%s",
                    job_id,
                    user_id,
                    summary_d,
                )
    except Exception as e:
        logger.exception("Sync job failed job_id=%s", job_id)
        await sync_model.increment_retry(job_id, str(e))


async def trigger_manual_sync(user_id: str, provider: str) -> str:
    """
    수동 동기화 (Unit 6 API에서 사용 예정).
    pending job을 생성한 뒤 즉시 1회 실행합니다.
    """
    job_id = await sync_model.create_job(user_id, provider)
    row = await sync_model.get_job_by_id(job_id)
    if row:
        await dispatch_sync_job(row)
    return job_id


async def run_scheduler() -> None:
    """
    앱 기동 시 백그라운드 태스크로 실행.
    주기마다 주기적 GitHub 큐 적재 후 pending·재시도 가능 failed job 처리.
    """
    logger.info("Sync scheduler started (interval=%ss)", SYNC_INTERVAL_SECONDS)
    while True:
        try:
            await sync_model.ensure_recurring_github_jobs(SYNC_INTERVAL_SECONDS)
            pending = await sync_model.get_pending_jobs()
            retryable = await sync_model.get_retryable_jobs()
            jobs = pending + retryable
            for row in jobs:
                await dispatch_sync_job(row)
        except asyncio.CancelledError:
            logger.info("Sync scheduler cancelled")
            raise
        except Exception:
            logger.exception("Sync scheduler tick error")

        try:
            await asyncio.sleep(SYNC_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Sync scheduler sleep interrupted (cancelled)")
            raise
