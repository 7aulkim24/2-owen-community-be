from fastapi import APIRouter, Depends, status
from typing import Dict, List, Optional
from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode
from controllers.comment_controller import comment_controller
from schemas import CommentCreateRequest, CommentUpdateRequest, CommentResponse, StandardResponse as StandardResponseSchema
from utils.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/v1/posts", tags=["댓글"])


@router.get("/{postId}/comments", response_model=StandardResponseSchema[List[CommentResponse]], status_code=status.HTTP_200_OK)
async def get_comments(postId: str):
    """
    댓글 목록 조회
    """
    data = await comment_controller.getCommentsByPost(postId)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.post("/{postId}/comments", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_201_CREATED)
async def create_comment(postId: str, req: CommentCreateRequest, user: Dict = Depends(get_current_user)):
    """
    댓글 작성
    """
    data = await comment_controller.createComment(postId, req, user)
    return StandardResponse.success(SuccessCode.CREATED, {"commentId": data.commentId})


@router.patch("/{postId}/comments/{commentId}", response_model=StandardResponseSchema[CommentResponse], status_code=status.HTTP_200_OK)
async def update_comment(postId: str, commentId: str, req: CommentUpdateRequest, user: Dict = Depends(get_current_user)):
    """
    댓글 수정
    """
    data = await comment_controller.updateComment(postId, commentId, req, user)
    return StandardResponse.success(SuccessCode.UPDATED, data)


@router.delete("/{postId}/comments/{commentId}", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def delete_comment(postId: str, commentId: str, user: Dict = Depends(get_current_user)):
    """
    댓글 삭제
    """
    deletedComment = await comment_controller.deleteComment(postId, commentId, user)
    return StandardResponse.success(
        SuccessCode.DELETED,
        {"commentId": deletedComment["commentId"], "message": "댓글이 삭제되었습니다"}
    )
