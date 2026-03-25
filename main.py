import asyncio
import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode
from utils.middleware.auth_middleware import AuthMiddleware
from utils.middleware.db_session_middleware import DBSessionMiddleware
from utils.middleware.request_id_middleware import RequestIDMiddleware, request_id_ctx
from utils.middleware.access_log_middleware import AccessLogMiddleware
from utils.errors.exception_handlers import register_exception_handlers
from utils.database.db import init_pool, close_pool
from services.sync_service import run_scheduler

# 로깅 필터: 로그에 request_id 추가
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

# 로깅 설정
logging_handler = logging.StreamHandler()
logging_handler.addFilter(RequestIDFilter())
logging_handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s'
))

file_handler = logging.FileHandler("backend.log", encoding="utf-8")
file_handler.addFilter(RequestIDFilter())
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging_handler, file_handler],
    force=True
)
logger = logging.getLogger(__name__)

_scheduler_task: Optional[asyncio.Task] = None

app = FastAPI(
    title="Prooflog Backend",
    description="FastAPI 기반 커뮤니티 백엔드 API",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await init_pool()
    global _scheduler_task
    # pytest / TestClient 등에서 백그라운드 루프 방지: DISABLE_SYNC_SCHEDULER=1
    if os.environ.get("DISABLE_SYNC_SCHEDULER", "").strip().lower() in ("1", "true", "yes"):
        logger.info("Background sync scheduler disabled (DISABLE_SYNC_SCHEDULER)")
    else:
        _scheduler_task = asyncio.create_task(run_scheduler())
        logger.info("Background sync scheduler task created")


@app.on_event("shutdown")
async def shutdown_event():
    global _scheduler_task
    if _scheduler_task is not None:
        t = _scheduler_task
        _scheduler_task = None
        if not t.done():
            t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Background sync scheduler task ended with an error")
        logger.info("Background sync scheduler task shutdown complete")
    await close_pool()

# 정적 파일 서빙
UPLOAD_DIR = "public"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    os.makedirs(os.path.join(UPLOAD_DIR, "image/post"))
    os.makedirs(os.path.join(UPLOAD_DIR, "image/profile"))

app.mount("/public", StaticFiles(directory=UPLOAD_DIR), name="public")

# 미들웨어 등록 (Starlette: 나중에 add 한 것이 요청 시 먼저 실행됨)
# CORSMiddleware는 반드시 마지막에 등록해 응답이 나갈 때 가장 마지막에 실행되게 한다.
# 그래야 500·예외 응답에도 Access-Control-Allow-Origin이 붙고, 브라우저가 CORS 오류로만 보이는 현상을 줄인다.
app.add_middleware(AuthMiddleware)
app.add_middleware(DBSessionMiddleware)
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)
_raw_regex = settings.cors_allow_origin_regex
_cors_regex = _raw_regex.strip() if isinstance(_raw_regex, str) and _raw_regex.strip() else None
_cors_kwargs = {
    "allow_origins": settings.get_allowed_origins_list(),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if _cors_regex:
    _cors_kwargs["allow_origin_regex"] = _cors_regex
app.add_middleware(CORSMiddleware, **_cors_kwargs)

# 예외 핸들러 등록
register_exception_handlers(app)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return StandardResponse.success(SuccessCode.SUCCESS, {"status": "healthy"})

# 라우터 등록
from routers import (
    post_router,
    comment_router,
    auth_router,
    user_router,
    integration_router,
    activity_router,
)
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(integration_router)
app.include_router(activity_router)

# 개발 환경(Debug Mode)에서만 테스트 라우터 포함
if settings.debug:
    from routers import test_router
    app.include_router(test_router)
    logger.info("Test router included (Debug Mode: ON)")
