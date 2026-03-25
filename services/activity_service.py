"""
활동 요약 초안(activity_summaries) — 목록·상세·수정·승인·거절
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import aiomysql

from models.activity_model import activity_model
from models.summary_model import summary_model
from schemas.activity_schema import (
    ActivityEventPublic,
    ActivitySummaryApproveResponse,
    ActivitySummaryDetailResponse,
    ActivitySummaryListItem,
)
from utils.common.id_utils import generate_id
from utils.database.db import execute, run_in_transaction
from utils.errors.error_codes import ErrorCode
from utils.errors.exceptions import APIError
from utils.integrations.summarizer import TemplateSummarizer


def _parse_json_field(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, bytes):
        val = val.decode("utf-8")
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return val
    return val


def _row_to_list_item(row: Dict[str, Any]) -> ActivitySummaryListItem:
    return ActivitySummaryListItem(
        summaryId=str(row["summary_id"]),
        summaryDate=row["summary_date"],
        summaryType=str(row["summary_type"]),
        status=str(row["status"]),
        eventCount=int(row["event_count"] or 0),
        providers=_parse_json_field(row.get("providers")),
        generatedTitle=str(row.get("generated_title") or ""),
        generatedContent=str(row.get("generated_content") or ""),
        postId=str(row["post_id"]) if row.get("post_id") else None,
        createdAt=row.get("created_at"),
        updatedAt=row.get("updated_at"),
    )


def _utc_day_bounds_naive(summary_d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(summary_d, datetime.min.time())
    end = start + timedelta(days=1)
    return start, end


def _event_row_to_public(row: Dict[str, Any]) -> ActivityEventPublic:
    return ActivityEventPublic(
        eventId=str(row["event_id"]),
        eventType=str(row.get("event_type") or ""),
        title=row.get("title"),
        description=row.get("description"),
        eventUrl=row.get("event_url"),
        repoName=row.get("repo_name"),
        eventOccurredAt=row["event_occurred_at"],
    )


class ActivityService:
    def __init__(self) -> None:
        self._summarizer = TemplateSummarizer()

    async def get_summaries(
        self, user_id: str, status: Optional[str] = None
    ) -> List[ActivitySummaryListItem]:
        rows = await summary_model.list_summaries_for_user(user_id, status=status)
        return [_row_to_list_item(r) for r in rows]

    async def get_summary_detail(
        self, summary_id: str, user_id: str
    ) -> ActivitySummaryDetailResponse:
        row = await summary_model.get_summary_by_id_for_user(summary_id, user_id)
        if not row:
            raise APIError(ErrorCode.NOT_FOUND, message="초안을 찾을 수 없습니다.")

        start_dt, end_dt = _utc_day_bounds_naive(row["summary_date"])
        raw_events = await activity_model.get_events_by_user_date(
            user_id, start_dt, end_dt
        )
        events = [_event_row_to_public(e) for e in raw_events]

        return ActivitySummaryDetailResponse(
            summaryId=str(row["summary_id"]),
            summaryDate=row["summary_date"],
            summaryType=str(row["summary_type"]),
            status=str(row["status"]),
            eventCount=int(row["event_count"] or 0),
            providers=_parse_json_field(row.get("providers")),
            generatedTitle=str(row.get("generated_title") or ""),
            generatedContent=str(row.get("generated_content") or ""),
            postId=str(row["post_id"]) if row.get("post_id") else None,
            createdAt=row.get("created_at"),
            updatedAt=row.get("updated_at"),
            events=events,
        )

    async def update_summary(
        self,
        summary_id: str,
        user_id: str,
        *,
        generated_title: Optional[str] = None,
        generated_content: Optional[str] = None,
    ) -> ActivitySummaryDetailResponse:
        row = await summary_model.get_summary_by_id_for_user(summary_id, user_id)
        if not row:
            raise APIError(ErrorCode.NOT_FOUND, message="초안을 찾을 수 없습니다.")
        if row.get("status") != "generated":
            raise APIError(
                ErrorCode.CONFLICT,
                message="검토 대기 상태의 초안만 수정할 수 있습니다.",
            )
        if generated_title is None and generated_content is None:
            raise APIError(ErrorCode.INVALID_INPUT, message="수정할 필드가 없습니다.")

        fields = []
        params: List[Any] = []
        if generated_title is not None:
            fields.append("generated_title = %s")
            params.append(generated_title[:200])
        if generated_content is not None:
            fields.append("generated_content = %s")
            params.append(generated_content)
        params.extend([summary_id, user_id])

        n = await execute(
            f"""
            UPDATE activity_summaries
            SET {", ".join(fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE summary_id = %s AND user_id = %s AND status = 'generated'
            """,
            tuple(params),
        )
        if n != 1:
            raise APIError(
                ErrorCode.CONFLICT,
                message="초안을 수정할 수 없습니다. 상태를 확인해 주세요.",
            )
        return await self.get_summary_detail(summary_id, user_id)

    async def dismiss_summary(self, summary_id: str, user_id: str) -> None:
        row = await summary_model.get_summary_by_id_for_user(summary_id, user_id)
        if not row:
            raise APIError(ErrorCode.NOT_FOUND, message="초안을 찾을 수 없습니다.")
        if row.get("status") != "generated":
            raise APIError(
                ErrorCode.CONFLICT,
                message="이미 처리된 초안입니다.",
            )
        n = await execute(
            """
            UPDATE activity_summaries
            SET status = 'dismissed', updated_at = CURRENT_TIMESTAMP
            WHERE summary_id = %s AND user_id = %s AND status = 'generated'
            """,
            (summary_id, user_id),
        )
        if n != 1:
            raise APIError(ErrorCode.CONFLICT, message="초안 상태를 변경할 수 없습니다.")

    async def approve_summary(
        self,
        summary_id: str,
        user_id: str,
        manual_context: Optional[str] = None,
    ) -> ActivitySummaryApproveResponse:
        row = await summary_model.get_summary_by_id_for_user(summary_id, user_id)
        if not row:
            raise APIError(ErrorCode.NOT_FOUND, message="초안을 찾을 수 없습니다.")
        if row.get("status") != "generated":
            raise APIError(
                ErrorCode.CONFLICT,
                message="검토 대기 상태의 초안만 승인할 수 있습니다.",
            )
        if row.get("post_id"):
            raise APIError(ErrorCode.CONFLICT, message="이미 게시글과 연결된 초안입니다.")

        summary_d: date = row["summary_date"]
        start_dt, end_dt = _utc_day_bounds_naive(summary_d)
        events = await activity_model.get_events_by_user_date(
            user_id, start_dt, end_dt
        )
        summarizer_out = self._summarizer.generate(events, summary_d)
        source_summary = summarizer_out.get("source_summary") or {}
        if isinstance(source_summary, dict):
            source_summary.setdefault("summary_date", summary_d.isoformat())

        title = (
            row.get("generated_title")
            or summarizer_out.get("title")
            or f"{summary_d.isoformat()} 활동 로그"
        )
        title = str(title).strip()[:300]

        base_content = str(
            row.get("generated_content") or summarizer_out.get("content") or ""
        ).strip()
        if not base_content:
            base_content = "자동 생성된 활동 요약입니다."

        manual = (manual_context or "").strip()
        if manual:
            content = f"{base_content}\n\n---\n\n[추가 메모]\n{manual}"
        else:
            content = base_content

        post_id = generate_id()
        source_json = json.dumps(source_summary, ensure_ascii=False)
        user_id_s = str(user_id)
        sid = str(summary_id)

        async def _tx(cursor: aiomysql.Cursor) -> None:
            await cursor.execute(
                """
                UPDATE activity_summaries
                SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE summary_id = %s AND user_id = %s AND status = 'generated'
                """,
                (sid, user_id_s),
            )
            if cursor.rowcount != 1:
                raise APIError(
                    ErrorCode.CONFLICT,
                    message="초안을 승인할 수 없습니다. 상태를 확인해 주세요.",
                )
            await cursor.execute(
                """
                INSERT INTO posts (
                    post_id, user_id, title, content,
                    post_type, source_type, source_summary, is_draft,
                    post_image_url, hits, comment_count, created_at
                ) VALUES (
                    %s, %s, %s, %s,
                    'auto_log', 'github', %s, 0,
                    NULL, 0, 0, NOW()
                )
                """,
                (post_id, user_id_s, title, content, source_json),
            )
            await cursor.execute(
                """
                UPDATE activity_summaries
                SET post_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE summary_id = %s AND user_id = %s
                """,
                (post_id, sid, user_id_s),
            )

        await run_in_transaction(_tx)
        return ActivitySummaryApproveResponse(summaryId=sid, postId=post_id)


activity_service = ActivityService()
