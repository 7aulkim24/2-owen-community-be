"""
activity_events 테이블 접근 — 수집 이벤트 저장·조회
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.common.id_utils import generate_id
from utils.database.db import execute, fetch_all


class ActivityModel:
    """GitHub 등 외부 소스에서 정규화된 활동 이벤트"""

    async def insert_events_ignore(self, rows: List[Dict[str, Any]]) -> int:
        """
        INSERT IGNORE — uq_provider_external (provider, external_id) 중복 시 무시.
        rows: snake_case 키 — event_id, user_id, provider, event_type, external_id,
              title, description, event_url, repo_name, event_metadata(dict|None), event_occurred_at(datetime)
        """
        inserted = 0
        for r in rows:
            meta = r.get("event_metadata")
            if meta is not None and isinstance(meta, (dict, list)):
                meta = json.dumps(meta, ensure_ascii=False)
            n = await execute(
                """
                INSERT IGNORE INTO activity_events (
                    event_id, user_id, provider, event_type, external_id,
                    title, description, event_url, repo_name, event_metadata,
                    event_occurred_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    r["event_id"],
                    r["user_id"],
                    r["provider"],
                    r["event_type"],
                    r["external_id"],
                    r.get("title"),
                    r.get("description"),
                    r.get("event_url"),
                    r.get("repo_name"),
                    meta,
                    r["event_occurred_at"],
                ),
            )
            inserted += int(n)
        return inserted

    def new_event_id(self) -> str:
        return generate_id()

    async def get_events_by_user_date(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Dict[str, Any]]:
        """user_id + event_occurred_at 구간 조회 (일별 요약 등 후속 단계용)"""
        rows = await fetch_all(
            """
            SELECT event_id, user_id, provider, event_type, external_id,
                   title, description, event_url, repo_name, event_metadata,
                   event_occurred_at, created_at
            FROM activity_events
            WHERE user_id = %s
              AND event_occurred_at >= %s
              AND event_occurred_at < %s
            ORDER BY event_occurred_at ASC
            """,
            (user_id, start_dt, end_dt),
        )
        return list(rows) if rows else []


activity_model = ActivityModel()
