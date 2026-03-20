"""GitHub 이벤트 정규화 단위 테스트 (외부 API·DB 없음)"""

from services.github_sync_service import _normalize_github_event


def test_normalize_push_event():
    raw = {
        "id": 999001,
        "type": "PushEvent",
        "created_at": "2024-06-01T10:00:00Z",
        "repo": {"name": "acme/app"},
        "payload": {
            "commits": [
                {"url": "https://github.com/acme/app/commit/abc123"},
            ]
        },
    }
    row = _normalize_github_event("user_ulid_01", raw)
    assert row is not None
    assert row["event_type"] == "push"
    assert row["external_id"] == "999001"
    assert row["user_id"] == "user_ulid_01"
    assert row["provider"] == "github"
    assert row["repo_name"] == "acme/app"
    assert "event_id" in row


def test_normalize_pull_request_event():
    raw = {
        "id": "999002",
        "type": "PullRequestEvent",
        "created_at": "2024-06-02T15:30:00Z",
        "repo": {"name": "acme/app"},
        "payload": {
            "action": "opened",
            "pull_request": {
                "title": "Fix bug",
                "body": "desc",
                "html_url": "https://github.com/acme/app/pull/1",
            },
        },
    }
    row = _normalize_github_event("user_ulid_01", raw)
    assert row is not None
    assert row["event_type"] == "pull_request"
    assert row["external_id"] == "999002"
    assert row["title"] == "Fix bug"


def test_normalize_skips_unknown_type():
    raw = {
        "id": 1,
        "type": "WatchEvent",
        "created_at": "2024-06-01T10:00:00Z",
        "repo": {"name": "acme/app"},
        "payload": {},
    }
    assert _normalize_github_event("u1", raw) is None
