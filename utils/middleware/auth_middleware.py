from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from models.user_model import user_model
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 세션에서 userId 추출하여 state에 가볍게 저장 (식별 역할)
        request.state.user_id = request.session.get("userId")
        
        response = await call_next(request)
        return response

async def get_current_user(request: Request):
    """요청에 인증된 사용자 반환 (없으면 401, 검증 역할)"""
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise APIError(ErrorCode.UNAUTHORIZED)
        
    # 실제 DB(메모리)에서 최신 사용자 정보 조회
    user = await user_model.getUserById(user_id)
    if not user:
        # 사용자가 없는 경우 세션 클리어 후 401
        request.session.clear()
        raise APIError(ErrorCode.UNAUTHORIZED)
        
    return user


async def get_optional_user(request: Request):
    """요청에 인증된 사용자 반환 (없으면 None)"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return None

    user = await user_model.getUserById(user_id)
    if not user:
        # 사용자가 없는 경우 세션 클리어
        request.session.clear()
        return None

    return user
