"""
GitHub API 어댑터
- OAuth 토큰 교환
- 사용자 정보 조회
- 사용자 이벤트 조회 (커밋, PR, 이슈 등)
- OAuth grant 철회 (연동 해제 시 GitHub에서 앱 인증 삭제)
"""

import asyncio
import base64
import logging
from datetime import datetime, timedelta, timezone
from time import time as unix_now
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


async def get_access_token(
    code: str,
    client_id: str,
    client_secret: str,
    callback_url: str,
) -> Dict[str, Any]:
    """
    인증 코드를 access token으로 교환.
    POST https://github.com/login/oauth/access_token

    반환 키:
      - access_token  (str, 필수)
      - refresh_token (str | None) — Expiring user tokens 설정 시에만 포함
      - token_expires_at (str | None) — ISO8601, expires_in 값 기반 계산
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": callback_url,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")

        # expires_in(초) → token_expires_at(ISO8601) 변환
        expires_in: Optional[int] = data.get("expires_in")
        token_expires_at: Optional[str] = None
        if expires_in:
            token_expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            ).isoformat()

        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token"),
            "token_expires_at": token_expires_at,
        }


async def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    GitHub 사용자 정보 조회
    GET https://api.github.com/user
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        return response.json()


async def get_user_events(
    username: str,
    access_token: str,
    since: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    사용자 이벤트 조회 (커밋, PR, 이슈 등)
    GET https://api.github.com/users/{username}/events
    since: ISO8601 형식의 날짜 문자열 (이 시점 이후 이벤트만 반환)
    """
    events, _ = await get_user_events_with_headers(username, access_token, since)
    return events


async def respect_github_rate_limit(headers: httpx.Headers) -> None:
    """
    X-RateLimit-Remaining이 0이면 X-RateLimit-Reset까지 대기.
    100 이하이면 경고 로그만 남김.
    """
    rem_raw = headers.get("x-ratelimit-remaining")
    reset_raw = headers.get("x-ratelimit-reset")
    if rem_raw is None:
        return
    try:
        remaining = int(rem_raw)
    except ValueError:
        return
    if 0 < remaining <= 100:
        logger.warning("GitHub rate limit remaining: %s", remaining)
    if remaining > 0:
        return
    if not reset_raw:
        await asyncio.sleep(60)
        return
    try:
        reset_ts = int(reset_raw)
    except ValueError:
        await asyncio.sleep(60)
        return
    sleep_s = max(0, reset_ts - int(unix_now())) + 1
    logger.warning("GitHub rate limit exhausted, sleeping %s seconds until reset", sleep_s)
    await asyncio.sleep(sleep_s)


async def get_user_events_with_headers(
    username: str,
    access_token: str,
    since: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], httpx.Headers]:
    """
    GET /users/{username}/events — 본문과 응답 헤더(레이트 리밋) 반환.
    """
    url = f"https://api.github.com/users/{username}/events"
    params = {}
    if since:
        params["since"] = since

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params if params else None,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return [], response.headers
        return data, response.headers


async def revoke_grant(client_id: str, client_secret: str, access_token: str) -> None:
    """
    GitHub OAuth grant 철회 — 앱이 사용자 계정에 대한 접근 권한을 완전히 제거
    DELETE https://api.github.com/applications/{client_id}/grant
    인증: Basic Auth (client_id:client_secret)
    철회 후 GitHub 설정 화면에서 앱이 목록에서 사라짐
    """
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    async with httpx.AsyncClient() as client:
        # httpx.AsyncClient.delete()는 json= 인자를 지원하지 않음 → request(DELETE, json=...) 사용
        response = await client.request(
            "DELETE",
            f"https://api.github.com/applications/{client_id}/grant",
            json={"access_token": access_token},
            headers={
                "Authorization": f"Basic {basic}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
