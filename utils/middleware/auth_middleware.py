from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from models.user_model import user_model
from utils.auth import build_auth_context, clear_auth_session
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 세션에서 인증 컨텍스트를 복원해 후속 레이어에서 일관되게 사용한다.
        auth_context = getattr(request.state, "auth", build_auth_context(request.session))
        request.state.auth = auth_context
        request.state.user_id = auth_context.user_id
        
        response = await call_next(request)
        return response

async def get_current_user(request: Request):
    """요청에 인증된 사용자 반환 (없으면 401, 검증 역할)"""
    auth_context = getattr(request.state, "auth", build_auth_context(request.session))
    user_id = auth_context.user_id
    
    if not user_id:
        raise APIError(ErrorCode.UNAUTHORIZED)
        
    # 실제 DB(메모리)에서 최신 사용자 정보 조회
    user = await user_model.getUserById(user_id)
    if not user:
        # 사용자가 없는 경우 세션 클리어 후 401
        clear_auth_session(request.session)
        raise APIError(ErrorCode.UNAUTHORIZED)
        
    return user


async def get_optional_user(request: Request):
    """요청에 인증된 사용자 반환 (없으면 None)"""
    auth_context = getattr(request.state, "auth", build_auth_context(request.session))
    user_id = auth_context.user_id
    if not user_id:
        return None

    user = await user_model.getUserById(user_id)
    if not user:
        # 사용자가 없는 경우 세션 클리어
        clear_auth_session(request.session)
        return None

    return user
