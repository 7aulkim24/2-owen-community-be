"""
일별 activity_events 집계 → 요약 초안 → activity_summaries 저장
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from models.activity_model import activity_model
from models.summary_model import summary_model
from utils.integrations.summarizer import TemplateSummarizer

logger = logging.getLogger(__name__)


def _utc_day_bounds_naive(summary_date: date) -> Tuple[datetime, datetime]:
    """activity_events.event_occurred_at은 naive UTC 기준으로 저장됨."""
    start = datetime.combine(summary_date, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end


class SummaryService:
    def __init__(self) -> None:
        self._summarizer = TemplateSummarizer()

    async def generate_daily_summary(
        self,
        user_id: str,
        summary_date: date,
        summary_type: str = "daily",
    ) -> Optional[str]:
        start_dt, end_dt = _utc_day_bounds_naive(summary_date)
        events: List[Dict[str, Any]] = await activity_model.get_events_by_user_date(
            user_id, start_dt, end_dt
        )
        if not events:
            logger.debug(
                "Skip daily summary: no events user_id=%s date=%s",
                user_id,
                summary_date,
            )
            return None

        out = self._summarizer.generate(events, summary_date)
        providers_set: Set[str] = {str(e.get("provider") or "") for e in events}
        providers_set.discard("")
        providers_list = sorted(providers_set) if providers_set else ["github"]

        summary_id = await summary_model.upsert_summary(
            user_id=user_id,
            summary_date=summary_date,
            summary_type=summary_type,
            event_count=len(events),
            providers=providers_list,
            generated_title=out["title"],
            generated_content=out["content"],
        )
        logger.info(
            "Daily summary upserted summary_id=%s user_id=%s date=%s events=%s",
            summary_id,
            user_id,
            summary_date,
            len(events),
        )
        return summary_id


summary_service = SummaryService()
