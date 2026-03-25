"""
활동 이벤트(activity_events) · 동기화 작업(sync_jobs) · 초안 요약(activity_summaries) 스키마
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .base_schema import BaseSchema


class SyncJobStatus(str, Enum):
    """sync_jobs.status"""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ActivityEventType(str, Enum):
    """GitHub 이벤트 타입 → DB event_type 정규화"""

    push = "push"
    pull_request = "pull_request"
    issues = "issues"
    review = "review"


class ActivityEventRow(BaseSchema):
    """activity_events DB row → 서비스/내부용 (camelCase)"""

    eventId: str
    userId: str
    provider: str
    eventType: str
    externalId: str
    title: Optional[str] = None
    description: Optional[str] = None
    eventUrl: Optional[str] = None
    repoName: Optional[str] = None
    eventMetadata: Optional[Dict[str, Any]] = None
    eventOccurredAt: datetime
    createdAt: Optional[datetime] = None


class SyncJobRow(BaseSchema):
    """sync_jobs DB row → 스케줄러 디스패치용"""

    jobId: str
    userId: str
    provider: str
    status: str
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    lastSyncedAt: Optional[datetime] = None
    retryCount: int = 0
    maxRetries: int = 3
    errorMessage: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# --- 초안 검토 & 승인 (Unit 5) ---


class ActivitySummaryListItem(BaseSchema):
    """초안 목록 한 건"""

    summaryId: str
    summaryDate: date
    summaryType: str
    status: str
    eventCount: int
    providers: Optional[Any] = None
    generatedTitle: str
    generatedContent: str
    postId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class ActivityEventPublic(BaseSchema):
    """초안 상세에 포함되는 근거 이벤트"""

    eventId: str
    eventType: str
    title: Optional[str] = None
    description: Optional[str] = None
    eventUrl: Optional[str] = None
    repoName: Optional[str] = None
    eventOccurredAt: datetime


class ActivitySummaryDetailResponse(BaseSchema):
    """초안 상세 + 해당 일자 근거 이벤트"""

    summaryId: str
    summaryDate: date
    summaryType: str
    status: str
    eventCount: int
    providers: Optional[Any] = None
    generatedTitle: str
    generatedContent: str
    postId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    events: List[ActivityEventPublic] = []


class ActivitySummaryPatchRequest(BaseSchema):
    """초안 본문 수정 (검토 대기 상태에서만)"""

    generatedTitle: Optional[str] = None
    generatedContent: Optional[str] = None


class ActivitySummaryApproveRequest(BaseSchema):
    """승인 시 피드 본문에 덧붙일 선택 메모"""

    manualContext: Optional[str] = None


class ActivitySummaryApproveResponse(BaseSchema):
    """승인 결과"""

    summaryId: str
    postId: str
