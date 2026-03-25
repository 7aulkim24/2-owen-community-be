"""
activity_summaries 테이블 접근 — 일일 요약 초안 저장·조회
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, Optional

from typing import List

from utils.common.id_utils import generate_id
from utils.database.db import execute, fetch_one, fetch_all


class SummaryModel:
    async def get_summary_by_user_date(
        self,
        user_id: str,
        summary_date: date,
        summary_type: str = "daily",
    ) -> Optional[Dict[str, Any]]:
        row = await fetch_one(
            """
            SELECT summary_id, user_id, summary_date, summary_type, event_count,
                   providers, generated_title, generated_content, post_id, status,
                   created_at, updated_at
            FROM activity_summaries
            WHERE user_id = %s AND summary_date = %s AND summary_type = %s
            """,
            (user_id, summary_date, summary_type),
        )
        return row

    async def upsert_summary(
        self,
        *,
        user_id: str,
        summary_date: date,
        summary_type: str = "daily",
        event_count: int,
        providers: Any,
        generated_title: str,
        generated_content: str,
    ) -> str:
        """
        동일 (user_id, summary_date, summary_type)이 있으면 UPDATE(단, status='generated'일 때만).
        approved/dismissed 인 경우 기존 행을 유지하고 summary_id만 반환.
        """
        existing = await self.get_summary_by_user_date(
            user_id, summary_date, summary_type
        )
        if isinstance(providers, (list, dict)):
            providers_json = json.dumps(providers, ensure_ascii=False)
        else:
            providers_json = json.dumps([providers], ensure_ascii=False)

        if existing:
            if existing.get("status") != "generated":
                return str(existing["summary_id"])
            sid = str(existing["summary_id"])
            await execute(
                """
                UPDATE activity_summaries
                SET event_count = %s,
                    providers = %s,
                    generated_title = %s,
                    generated_content = %s,
                    status = 'generated'
                WHERE summary_id = %s
                """,
                (
                    event_count,
                    providers_json,
                    generated_title[:200],
                    generated_content,
                    sid,
                ),
            )
            return sid

        sid = generate_id()
        await execute(
            """
            INSERT INTO activity_summaries (
                summary_id, user_id, summary_date, summary_type,
                event_count, providers, generated_title, generated_content,
                post_id, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, 'generated')
            """,
            (
                sid,
                user_id,
                summary_date,
                summary_type,
                event_count,
                providers_json,
                generated_title[:200],
                generated_content,
            ),
        )
        return sid

    async def get_summary_by_id(self, summary_id: str) -> Optional[Dict[str, Any]]:
        row = await fetch_one(
            """
            SELECT summary_id, user_id, summary_date, summary_type, event_count,
                   providers, generated_title, generated_content, post_id, status,
                   created_at, updated_at
            FROM activity_summaries
            WHERE summary_id = %s
            """,
            (summary_id,),
        )
        return row

    async def get_summary_by_id_for_user(
        self, summary_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        row = await fetch_one(
            """
            SELECT summary_id, user_id, summary_date, summary_type, event_count,
                   providers, generated_title, generated_content, post_id, status,
                   created_at, updated_at
            FROM activity_summaries
            WHERE summary_id = %s AND user_id = %s
            """,
            (summary_id, user_id),
        )
        return row

    async def list_summaries_for_user(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if status:
            rows = await fetch_all(
                """
                SELECT summary_id, user_id, summary_date, summary_type, event_count,
                       providers, generated_title, generated_content, post_id, status,
                       created_at, updated_at
                FROM activity_summaries
                WHERE user_id = %s AND status = %s
                ORDER BY summary_date DESC, created_at DESC
                """,
                (user_id, status),
            )
        else:
            rows = await fetch_all(
                """
                SELECT summary_id, user_id, summary_date, summary_type, event_count,
                       providers, generated_title, generated_content, post_id, status,
                       created_at, updated_at
                FROM activity_summaries
                WHERE user_id = %s
                ORDER BY summary_date DESC, created_at DESC
                """,
                (user_id,),
            )
        return list(rows) if rows else []


summary_model = SummaryModel()
