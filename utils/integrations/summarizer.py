"""
활동 이벤트 → 일일 요약 텍스트 (Strategy 패턴).
MVP: TemplateSummarizer. 이후 LLMSummarizer 등으로 교체·추가 가능.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List


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


class TemplateSummarizer(BaseSummarizer):
    """로드맵 MVP 템플릿 기반 요약."""

    def generate(
        self,
        events: List[Dict[str, Any]],
        summary_date: date,
    ) -> Dict[str, Any]:
        commit_total = 0
        pr_count = 0
        issue_count = 0
        repo_commits: Dict[str, int] = defaultdict(int)

        for ev in events:
            et = ev.get("event_type") or ""
            repo = ev.get("repo_name") or "(저장소 미상)"

            if et == "push":
                n = _commits_from_push_event(ev)
                commit_total += n
                repo_commits[repo] += n
            elif et == "pull_request":
                pr_count += 1
            elif et == "issues":
                issue_count += 1
            elif et == "review":
                pr_count += 1

        repos_sorted = sorted(
            [{"name": name, "commit_count": cnt} for name, cnt in repo_commits.items()],
            key=lambda x: x["commit_count"],
            reverse=True,
        )

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

        content = "\n".join(lines)
        title = (
            f"{summary_date.isoformat()} · 커밋 {commit_total} · PR {pr_count} · 이슈 {issue_count}"
        )[:200]

        source_summary = {
            "commit_count": commit_total,
            "pr_count": pr_count,
            "issue_count": issue_count,
            "repos": repos_sorted,
        }

        return {
            "title": title,
            "content": content,
            "source_summary": source_summary,
        }
