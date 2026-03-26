import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from utils.auth import build_auth_context
from utils.database.db import fetch_one, execute

logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseHTTPMiddleware):
    """DB 기반 세션 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        session_key = request.cookies.get(settings.session_cookie_name)
        session: Dict = {}

        clear_cookie = False
        if session_key:
            session_load_failed = False
            try:
                row = await fetch_one(
                    "SELECT data, expires_at FROM sessions WHERE session_key = %s AND expires_at > NOW()",
                    (session_key,),
                )
            except Exception:
                logger.exception(
                    "세션 조회 실패(DB 연결·쿼리 오류). 빈 세션으로 진행합니다."
                )
                row = None
                session_load_failed = True

            if session_load_failed:
                session = {}
                clear_cookie = False
            elif row and row.get("data"):
                session = json.loads(row["data"])
            else:
                session_key = None
                clear_cookie = True

        request.scope["session"] = session
        request.state.auth = build_auth_context(session)
        request.state.user_id = request.state.auth.user_id
        request.state._session_key = session_key
        request.state._session_snapshot = json.dumps(session, sort_keys=True)
        request.state._clear_cookie = clear_cookie

        response: Response = await call_next(request)

        current_session = request.scope.get("session", {})
        current_snapshot = json.dumps(current_session, sort_keys=True)

        if current_snapshot != request.state._session_snapshot:
            if not current_session:
                if session_key:
                    await execute(
                        "DELETE FROM sessions WHERE session_key = %s",
                        (session_key,),
                    )
                response.delete_cookie(settings.session_cookie_name)
                return response

            if not session_key:
                session_key = secrets.token_urlsafe(32)

            expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.session_timeout)
            data_json = json.dumps(current_session)
            user_id = current_session.get("userId")

            # MySQL 8.0.19+ : VALUES(col) ON DUPLICATE 구문은 폐기 예정 → 행 별칭 사용
            await execute(
                """
                INSERT INTO sessions (session_key, user_id, data, expires_at, created_at)
                VALUES (%s, %s, %s, %s, NOW()) AS new_row
                ON DUPLICATE KEY UPDATE
                    user_id = new_row.user_id,
                    data = new_row.data,
                    expires_at = new_row.expires_at
                """,
                (session_key, user_id, data_json, expires_at),
            )

            response.set_cookie(
                settings.session_cookie_name,
                session_key,
                max_age=settings.session_timeout,
                httponly=True,
                samesite=settings.cookie_samesite,
                secure=settings.cookie_secure,
            )

        if request.state._clear_cookie:
            response.delete_cookie(settings.session_cookie_name)

        return response
