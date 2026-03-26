"""
공통 날짜/시간 유틸리티
"""

from datetime import date, datetime, timedelta
from typing import Tuple


def utc_day_bounds_naive(summary_date: date) -> Tuple[datetime, datetime]:
    """
    activity_events.event_occurred_at은 naive UTC 기준으로 저장됨.
    해당 날짜(UTC)의 시작과 끝(다음 날 0시)을 반환합니다.
    """
    start = datetime.combine(summary_date, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end
