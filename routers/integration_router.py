"""
연동 계정 API — GitHub OAuth, 연동 목록, 연동 해제
"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse

from config import settings
from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode, ErrorCode
from utils.errors.exceptions import APIError
from utils.middleware.auth_middleware import get_current_user
from services.integration_service import integration_service
from schemas import StandardResponse as StandardResponseSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/integrations", tags=["연동"])


def _get_frontend_redirect_url(path: str = "/integration.html") -> str:
    """FE 리다이렉트 URL (frontend_url 우선, 없으면 allowed_origins 첫 항목)"""
    return settings.get_frontend_base_url() + path


@router.get("", response_model=StandardResponseSchema[list])
async def get_integrations(user: dict = Depends(get_current_user)):
    """내 연동 계정 목록"""
    data = await integration_service.get_user_integrations(user["userId"])
    return StandardResponse.success(SuccessCode.SUCCESS, [d.model_dump() for d in data])


@router.get("/github/authorize")
async def github_authorize(user: dict = Depends(get_current_user)):
    """GitHub OAuth 인증 URL 반환 (FE에서 이 URL로 리다이렉트)"""
    url = integration_service.get_authorize_url(user["userId"])
    return StandardResponse.success(SuccessCode.SUCCESS, {"authorizeUrl": url})


@router.get("/github/callback")
async def github_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """
    OAuth 콜백 — 토큰 교환 후 FE 연동 관리 페이지로 리다이렉트.
    사용자 식별은 서명된 state만 신뢰 (세션 폴백 없음 — OAuth 완료 주체와 Prooflog 계정 바인딩).
    """
    redirect_url = _get_frontend_redirect_url("/integration.html")
    fail_url = redirect_url + "?error=1"
    login_url = _get_frontend_redirect_url("/login.html")

    if error:
        return RedirectResponse(url=fail_url, status_code=status.HTTP_302_FOUND)

    if not code:
        return RedirectResponse(url=fail_url, status_code=status.HTTP_302_FOUND)

    # state에서만 user_id 추출 (만료/변조 시 재로그인 유도)
    user_id = integration_service.decode_oauth_state(state)

    if not user_id:
        return RedirectResponse(
            url=login_url + "?error=session_expired&return_to=integration",
            status_code=status.HTTP_302_FOUND,
        )

    try:
        await integration_service.handle_callback(code, user_id)
    except Exception as e:
        logger.error("GitHub OAuth callback failed: %s", e, exc_info=True)
        return RedirectResponse(url=fail_url, status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url=redirect_url + "?connected=1", status_code=status.HTTP_302_FOUND)


@router.delete("/{accountId}")
async def disconnect_integration(accountId: str, user: dict = Depends(get_current_user)):
    """연동 해제"""
    ok = await integration_service.disconnect(accountId, user["userId"])
    if not ok:
        raise APIError(
            ErrorCode.NOT_FOUND,
            message="연동 해제에 실패했거나 이미 해제된 계정입니다.",
        )
    return StandardResponse.success(SuccessCode.DELETED, {})
