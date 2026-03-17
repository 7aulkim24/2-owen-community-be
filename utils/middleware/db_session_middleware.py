import json
import secrets
from datetime import datetime, timedelta
from typing import Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from utils.database.db import fetch_one, execute


class DBSessionMiddleware(BaseHTTPMiddleware):
    """DB 기반 세션 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        session_key = request.cookies.get(settings.session_cookie_name)
        session: Dict = {}

        clear_cookie = False
        if session_key:
            row = await fetch_one(
                "SELECT data, expires_at FROM sessions WHERE session_key = %s AND expires_at > NOW()",
                (session_key,),
            )
            if row and row.get("data"):
                session = json.loads(row["data"])
            else:
                session_key = None
                clear_cookie = True

        request.scope["session"] = session
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

            expires_at = datetime.utcnow() + timedelta(seconds=settings.session_timeout)
            data_json = json.dumps(current_session)
            user_id = current_session.get("userId")

            await execute(
                """
                INSERT INTO sessions (session_key, user_id, data, expires_at, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    user_id = VALUES(user_id),
                    data = VALUES(data),
                    expires_at = VALUES(expires_at)
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
