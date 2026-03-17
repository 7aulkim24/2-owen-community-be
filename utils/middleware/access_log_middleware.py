import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("access_logger")

class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    모든 HTTP 요청과 응답을 로깅하는 미들웨어.
    - 요청: Method, URL, Client IP
    - 응답: Status Code, 처리 시간(ms)
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 정보 추출
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # 특정 경로 제외 (정적 파일 및 빈번한 폴링성 요청)
        # /public: 정적 파일
        # /v1/posts: 게시글 목록/상세/댓글 (폴링성)
        # /v1/users/me: 내 정보 조회 (폴링성)
        excluded_paths = ["/v1/posts", "/v1/users/me"]
        
        is_excluded = (
            path.startswith("/public") or 
            path in excluded_paths or
            (path.startswith("/v1/posts/") and not path.endswith("/likes"))
        )

        if is_excluded:
            return await call_next(request)

        # 요청 로깅
        logger.info(f"Request: {method} {path} - IP: {client_ip}")
        
        try:
            response = await call_next(request)
            
            # 처리 시간 계산
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code
            
            # 응답 로깅
            logger.info(f"Response: {method} {path} - Status: {status_code} - Time: {process_time:.2f}ms")
            
            return response
            
        except Exception as e:
            # 예외 발생 시 로깅 (이미 exception_handler에서 처리되지만, 미들웨어 레벨에서도 기록)
            process_time = (time.time() - start_time) * 1000
            logger.error(f"Error: {method} {path} - Message: {str(e)} - Time: {process_time:.2f}ms")
            raise e
