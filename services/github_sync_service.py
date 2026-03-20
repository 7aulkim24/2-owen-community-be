"""
GitHub 공개 이벤트 수집 → activity_events 정규화 저장
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.activity_model import activity_model
from services.integration_service import integration_service
from utils.integrations import github

logger = logging.getLogger(__name__)

GITHUB_PROVIDER = "github"

_GITHUB_TYPE_TO_EVENT_TYPE = {
    "PushEvent": "push",
    "PullRequestEvent": "pull_request",
    "IssuesEvent": "issues",
    "PullRequestReviewEvent": "review",
}


def _parse_github_datetime(iso: Optional[str]) -> datetime:
    if not iso:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    s = iso.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _truncate(s: Optional[str], max_len: int) -> Optional[str]:
    if s is None:
        return None
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _normalize_github_event(user_id: str, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    etype = raw.get("type")
    if etype not in _GITHUB_TYPE_TO_EVENT_TYPE:
        return None
    eid = raw.get("id")
    if eid is None:
        return None
    external_id = str(eid)

    repo = raw.get("repo") or {}
    repo_name = repo.get("name")
    payload = raw.get("payload") or {}

    title: Optional[str] = None
    desc: Optional[str] = None
    url: Optional[str] = None

    if etype == "PushEvent":
        commits = payload.get("commits") or []
        n = len(commits)
        title = f"Push to {repo_name}" if repo_name else "Push"
        desc = f"{n} commit(s)" if n else None
        if commits and isinstance(commits[0], dict):
            url = commits[0].get("url") or commits[0].get("html_url")
        if not url and repo_name:
            url = f"https://github.com/{repo_name}"
    elif etype == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        title = pr.get("title")
        desc = pr.get("body")
        url = pr.get("html_url")
    elif etype == "IssuesEvent":
        issue = payload.get("issue") or {}
        title = issue.get("title")
        desc = issue.get("body")
        url = issue.get("html_url")
    elif etype == "PullRequestReviewEvent":
        pr = payload.get("pull_request") or {}
        title = pr.get("title")
        review = payload.get("review") or {}
        if not title:
            title = review.get("body") or "Pull request review"
        url = pr.get("html_url") or review.get("html_url")

    created_at = _parse_github_datetime(raw.get("created_at"))

    meta: Dict[str, Any] = {
        "github_type": etype,
        "action": payload.get("action"),
    }

    return {
        "event_id": activity_model.new_event_id(),
        "user_id": user_id,
        "provider": GITHUB_PROVIDER,
        "event_type": _GITHUB_TYPE_TO_EVENT_TYPE[etype],
        "external_id": external_id,
        "title": _truncate(title, 500),
        "description": desc,
        "event_url": _truncate(url, 500) if url else None,
        "repo_name": _truncate(repo_name, 200) if repo_name else None,
        "event_metadata": meta,
        "event_occurred_at": created_at,
    }


def _last_sync_to_since_iso(last_synced_at: Optional[datetime]) -> Optional[str]:
    if last_synced_at is None:
        return None
    dt = last_synced_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class GitHubSyncService:
    """GitHub /users/{login}/events → activity_events"""

    async def sync_github_events_for_user(
        self,
        user_id: str,
        last_synced_at: Optional[datetime] = None,
    ) -> int:
        creds = await integration_service.get_decrypted_token_and_username_for_sync(
            user_id, GITHUB_PROVIDER
        )
        if not creds:
            raise RuntimeError("활성 GitHub 연동이 없습니다.")

        access_token, username = creds
        if not username:
            user_info = await github.get_user_info(access_token)
            username = user_info.get("login") or ""
        if not username:
            raise RuntimeError("GitHub 로그인 이름을 확인할 수 없습니다.")

        since_iso = _last_sync_to_since_iso(last_synced_at)

        events, headers = await github.get_user_events_with_headers(
            username, access_token, since_iso
        )
        await github.respect_github_rate_limit(headers)

        rows: List[Dict[str, Any]] = []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            row = _normalize_github_event(user_id, ev)
            if row:
                rows.append(row)

        if not rows:
            logger.info("No normalizable GitHub events for user_id=%s", user_id)
            return 0

        inserted = await activity_model.insert_events_ignore(rows)
        logger.info(
            "GitHub sync user_id=%s events_fetched=%s db_rowcount_sum=%s",
            user_id,
            len(rows),
            inserted,
        )
        return inserted


github_sync_service = GitHubSyncService()
