import contextvars
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# 전역적으로 접근 가능한 Request ID 컨텍스트
request_id_ctx = contextvars.ContextVar("request_id", default="N/A")

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    모든 요청에 고유한 Request ID를 부여하고 Context에 저장하는 미들웨어.
    - 응답 헤더 X-Request-ID에 포함
    - contextvars를 사용하여 로깅 시스템에서 접근 가능하게 함
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", os.urandom(8).hex())
        
        # Context 설정
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # 요청 종료 후 Context 복구
            request_id_ctx.reset(token)
