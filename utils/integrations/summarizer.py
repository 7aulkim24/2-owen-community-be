"""
활동 이벤트 → 일일 요약 텍스트 (Strategy 패턴).
MVP: TemplateSummarizer. 이후 LLMSummarizer 등으로 교체·추가 가능.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Optional, Set, Tuple


class BaseSummarizer(ABC):
    """요약 생성기 인터페이스 — activity_events 행(dict) 목록을 받아 초안 필드 생성."""

    @abstractmethod
    def generate(
        self,
        events: List[Dict[str, Any]],
        summary_date: date,
    ) -> Dict[str, Any]:
        """
        Returns:
            title: str
            content: str
            source_summary: dict — Unit 6 카드 근거 섹션용
        """
        raise NotImplementedError


def _commits_from_push_event(ev: Dict[str, Any]) -> int:
    """PushEvent 정규화 시 description 예: '3 commit(s)'."""
    if ev.get("event_type") != "push":
        return 0
    desc = ev.get("description") or ""
    m = re.search(r"(\d+)\s+commit", str(desc), re.IGNORECASE)
    if m:
        return max(1, int(m.group(1)))
    return 1


def _parse_event_metadata(ev: Dict[str, Any]) -> Dict[str, Any]:
    m = ev.get("event_metadata")
    if m is None:
        return {}
    if isinstance(m, dict):
        return m
    if isinstance(m, bytes):
        m = m.decode("utf-8")
    if isinstance(m, str):
        try:
            parsed = json.loads(m)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _github_repo_url(repo_name: str) -> Optional[str]:
    if not repo_name or repo_name == "(저장소 미상)":
        return None
    name = repo_name.strip()
    if "/" in name and " " not in name:
        return f"https://github.com/{name}"
    return None


def _truncate_line(s: str, max_len: int = 120) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


class TemplateSummarizer(BaseSummarizer):
    """로드맵 MVP 템플릿 기반 요약 + 커밋 메시지·PR/이슈 제목 (Unit 6)."""

    def generate(
        self,
        events: List[Dict[str, Any]],
        summary_date: date,
    ) -> Dict[str, Any]:
        commit_total = 0
        pr_count = 0
        issue_count = 0
        repo_commits: Dict[str, int] = defaultdict(int)

        commit_rows: List[Tuple[str, str]] = []  # (repo, message) 순서 유지
        seen_commit: Set[Tuple[str, str]] = set()

        pr_items: List[Dict[str, Any]] = []
        issue_items: List[Dict[str, Any]] = []
        seen_pr: Set[str] = set()
        seen_issue: Set[str] = set()

        for ev in events:
            et = ev.get("event_type") or ""
            repo = ev.get("repo_name") or "(저장소 미상)"

            if et == "push":
                n = _commits_from_push_event(ev)
                commit_total += n
                repo_commits[repo] += n
                meta = _parse_event_metadata(ev)
                for c in meta.get("commits") or []:
                    if not isinstance(c, dict):
                        continue
                    msg = c.get("message")
                    if not msg or not str(msg).strip():
                        continue
                    msg_clean = _truncate_line(str(msg), 200)
                    key = (repo, msg_clean.lower())
                    if key in seen_commit:
                        continue
                    seen_commit.add(key)
                    commit_rows.append((repo, msg_clean))
            elif et == "pull_request":
                pr_count += 1
                t = ev.get("title")
                if t and str(t).strip():
                    tid = f"pr:{repo}:{str(t).strip()}"
                    if tid not in seen_pr:
                        seen_pr.add(tid)
                        pr_items.append(
                            {
                                "title": _truncate_line(str(t), 200),
                                "repo": repo,
                                "url": ev.get("event_url"),
                            }
                        )
            elif et == "issues":
                issue_count += 1
                t = ev.get("title")
                if t and str(t).strip():
                    tid = f"iss:{repo}:{str(t).strip()}"
                    if tid not in seen_issue:
                        seen_issue.add(tid)
                        issue_items.append(
                            {
                                "title": _truncate_line(str(t), 200),
                                "repo": repo,
                                "url": ev.get("event_url"),
                            }
                        )
            elif et == "review":
                pr_count += 1
                t = ev.get("title")
                if t and str(t).strip():
                    tid = f"rv:{repo}:{str(t).strip()}"
                    if tid not in seen_pr:
                        seen_pr.add(tid)
                        pr_items.append(
                            {
                                "title": _truncate_line(str(t), 200),
                                "repo": repo,
                                "url": ev.get("event_url"),
                            }
                        )

        repos_sorted = sorted(
            [{"name": name, "commit_count": cnt} for name, cnt in repo_commits.items()],
            key=lambda x: x["commit_count"],
            reverse=True,
        )
        for r in repos_sorted:
            url = _github_repo_url(r["name"])
            if url:
                r["github_url"] = url

        all_repo_names = sorted(
            {ev.get("repo_name") or "(저장소 미상)" for ev in events}
        )
        if all_repo_names:
            repo_list = ", ".join(all_repo_names[:5])
            if len(all_repo_names) > 5:
                repo_list += f" 외 {len(all_repo_names) - 5}곳"
        else:
            repo_list = "기록된 저장소"

        lines = [
            f"오늘은 {repo_list}에서 작업을 진행했습니다.",
            f"• 커밋 {commit_total}건  • PR {pr_count}건  • 이슈 {issue_count}건",
            "",
            "[작업 상세]",
        ]
        if repos_sorted:
            for r in repos_sorted:
                lines.append(f"- {r['name']}: {r['commit_count']}건 커밋")
        else:
            lines.append("- 해당 일자에 푸시 기반 커밋 수 집계가 없습니다 (PR/이슈/리뷰만 있을 수 있음).")

        if commit_rows:
            lines.extend(["", "[주요 커밋]"])
            for repo, msg in commit_rows[:12]:
                lines.append(f"- {repo}: {msg}")

        if pr_items or issue_items:
            lines.extend(["", "[PR / 이슈]"])
            for p in pr_items[:8]:
                lines.append(f"- PR ({p['repo']}): {p['title']}")
            for i in issue_items[:8]:
                lines.append(f"- 이슈 ({i['repo']}): {i['title']}")

        content = "\n".join(lines)
        title = (
            f"{summary_date.isoformat()} · 커밋 {commit_total} · PR {pr_count} · 이슈 {issue_count}"
        )[:200]

        commits_for_json = [{"repo": r, "message": m} for r, m in commit_rows[:5]]

        source_summary: Dict[str, Any] = {
            "summary_date": summary_date.isoformat(),
            "commit_count": commit_total,
            "pr_count": pr_count,
            "issue_count": issue_count,
            "repos": repos_sorted,
            "commits": commits_for_json,
            "pull_requests": pr_items[:8],
            "issues": issue_items[:8],
        }

        return {
            "title": title,
            "content": content,
            "source_summary": source_summary,
        }
