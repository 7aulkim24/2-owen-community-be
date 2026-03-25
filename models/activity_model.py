"""
activity_events 테이블 접근 — 수집 이벤트 저장·조회
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.common.id_utils import generate_id
from utils.database.db import execute, fetch_all, fetch_one


class ActivityModel:
    """GitHub 등 외부 소스에서 정규화된 활동 이벤트"""

    async def insert_events_ignore(self, rows: List[Dict[str, Any]]) -> int:
        """
        (provider, external_id) 중복이면 삽입 생략.
        INSERT IGNORE 대신 NOT EXISTS를 쓰면 MySQL이 중복마다 Warning(1062)을 내지 않음.
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
                INSERT INTO activity_events (
                    event_id, user_id, provider, event_type, external_id,
                    title, description, event_url, repo_name, event_metadata,
                    event_occurred_at
                )
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1 FROM activity_events ae
                    WHERE ae.provider = %s AND ae.external_id = %s
                )
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
                    r["provider"],
                    r["external_id"],
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

    async def count_events_by_user(self, user_id: str) -> int:
        """사용자별 수집된 activity_events 총 건수 (대시보드용)"""
        row = await fetch_one(
            """
            SELECT COUNT(*) AS c
            FROM activity_events
            WHERE user_id = %s
            """,
            (user_id,),
        )
        if not row:
            return 0
        return int(row.get("c") or 0)


activity_model = ActivityModel()
