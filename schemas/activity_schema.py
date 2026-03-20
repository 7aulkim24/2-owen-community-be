"""
활동 이벤트(activity_events) · 동기화 작업(sync_jobs) 스키마
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

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
