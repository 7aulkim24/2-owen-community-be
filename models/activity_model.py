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
        INSERT IGNORE를 사용하여 배치로 처리 (UNIQUE KEY uq_provider_external 활용).
        rows: snake_case 키 — event_id, user_id, provider, event_type, external_id,
              title, description, event_url, repo_name, event_metadata(dict|None), event_occurred_at(datetime)
        """
        if not rows:
            return 0

        BATCH_SIZE = 50
        inserted = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            placeholders = []
            params: List[Any] = []
            for r in batch:
                meta = r.get("event_metadata")
                if meta is not None and isinstance(meta, (dict, list)):
                    meta = json.dumps(meta, ensure_ascii=False)
                placeholders.append("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
                params.extend([
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
                ])
            query = f"""
                INSERT IGNORE INTO activity_events (
                    event_id, user_id, provider, event_type, external_id,
                    title, description, event_url, repo_name, event_metadata,
                    event_occurred_at
                ) VALUES {', '.join(placeholders)}
            """
            
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*Duplicate entry.*for key.*uq_provider_external.*")
                n = await execute(query, tuple(params))
                
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
