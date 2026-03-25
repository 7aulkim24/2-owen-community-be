"""
활동 요약 초안 API — 목록·상세·수정·승인·거절
"""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, status

from schemas import StandardResponse as StandardResponseSchema
from schemas.activity_schema import (
    ActivitySummaryApproveRequest,
    ActivitySummaryApproveResponse,
    ActivitySummaryDetailResponse,
    ActivitySummaryListItem,
    ActivitySummaryPatchRequest,
)
from services.activity_service import activity_service
from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode
from utils.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/v1/activities", tags=["활동·초안"])


@router.get(
    "/summaries",
    response_model=StandardResponseSchema[List[ActivitySummaryListItem]],
    status_code=status.HTTP_200_OK,
)
async def list_summaries(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="generated | approved | dismissed (미지정 시 전체)",
    ),
    user: dict = Depends(get_current_user),
):
    data = await activity_service.get_summaries(
        user["userId"], status=status_filter
    )
    return StandardResponse.success(
        SuccessCode.SUCCESS, [d.model_dump(mode="json") for d in data]
    )


@router.get(
    "/summaries/{summaryId}",
    response_model=StandardResponseSchema[ActivitySummaryDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def get_summary(
    summaryId: str,
    user: dict = Depends(get_current_user),
):
    data = await activity_service.get_summary_detail(summaryId, user["userId"])
    return StandardResponse.success(SuccessCode.SUCCESS, data.model_dump(mode="json"))


@router.patch(
    "/summaries/{summaryId}",
    response_model=StandardResponseSchema[ActivitySummaryDetailResponse],
    status_code=status.HTTP_200_OK,
)
async def patch_summary(
    summaryId: str,
    body: ActivitySummaryPatchRequest,
    user: dict = Depends(get_current_user),
):
    data = await activity_service.update_summary(
        summaryId,
        user["userId"],
        generated_title=body.generatedTitle,
        generated_content=body.generatedContent,
    )
    return StandardResponse.success(SuccessCode.UPDATED, data.model_dump(mode="json"))


@router.post(
    "/summaries/{summaryId}/approve",
    response_model=StandardResponseSchema[ActivitySummaryApproveResponse],
    status_code=status.HTTP_200_OK,
)
async def approve_summary(
    summaryId: str,
    user: dict = Depends(get_current_user),
    body: ActivitySummaryApproveRequest = Body(default_factory=ActivitySummaryApproveRequest),
):
    manual = body.manualContext
    data = await activity_service.approve_summary(
        summaryId, user["userId"], manual_context=manual
    )
    return StandardResponse.success(SuccessCode.SUCCESS, data.model_dump(mode="json"))


@router.post(
    "/summaries/{summaryId}/dismiss",
    response_model=StandardResponseSchema[dict],
    status_code=status.HTTP_200_OK,
)
async def dismiss_summary(
    summaryId: str,
    user: dict = Depends(get_current_user),
):
    await activity_service.dismiss_summary(summaryId, user["userId"])
    return StandardResponse.success(
        SuccessCode.SUCCESS, {"summaryId": summaryId, "status": "dismissed"}
    )
