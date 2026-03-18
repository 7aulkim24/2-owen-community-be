import logging
import os
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

app = FastAPI(
    title="Prooflog Backend",
    description="FastAPI 기반 커뮤니티 백엔드 API",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    await init_pool()


@app.on_event("shutdown")
async def shutdown_event():
    await close_pool()

# 정적 파일 서빙
UPLOAD_DIR = "public"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    os.makedirs(os.path.join(UPLOAD_DIR, "image/post"))
    os.makedirs(os.path.join(UPLOAD_DIR, "image/profile"))

app.mount("/public", StaticFiles(directory=UPLOAD_DIR), name="public")

# 미들웨어 등록 (LIFO 순서로 실행됨: RequestID -> AccessLog -> CORS -> Session -> Auth -> App)
app.add_middleware(AuthMiddleware)
app.add_middleware(DBSessionMiddleware)
app.add_middleware(CORSMiddleware,
                   allow_origins=settings.get_allowed_origins_list(),
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)

# 예외 핸들러 등록
register_exception_handlers(app)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return StandardResponse.success(SuccessCode.SUCCESS, {"status": "healthy"})

# 라우터 등록
from routers import post_router, comment_router, auth_router, user_router
app.include_router(post_router)
app.include_router(comment_router)
app.include_router(auth_router)
app.include_router(user_router)

# 개발 환경(Debug Mode)에서만 테스트 라우터 포함
if settings.debug:
    from routers import test_router
    app.include_router(test_router)
    logger.info("Test router included (Debug Mode: ON)")
