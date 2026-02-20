from typing import List, Dict, Union
from models.comment_model import comment_model
from models.post_model import post_model
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode
from schemas import CommentCreateRequest, CommentUpdateRequest, CommentResponse, CommentAuthor, ResourceError


class CommentController:
    """댓글 관련 비즈니스 로직"""

    async def _formatComment(self, comment: Dict) -> CommentResponse:
        """Comment 데이터를 API 응답 규격에 맞게 변환"""
        # JOIN으로 가져온 최신 사용자 정보 사용 (N+1 문제 해결)
        author_data = CommentAuthor(
            userId=comment["userId"],
            nickname=comment.get("userNickname"),
            profileImageUrl=comment.get("userProfileImageUrl")
        )

        return CommentResponse(
            commentId=comment["commentId"],
            postId=comment["postId"],
            content=comment["content"],
            author=author_data,
            createdAt=comment["createdAt"],
            updatedAt=comment.get("updatedAt")
        )

    async def getCommentsByPost(self, postId: str) -> List[CommentResponse]:
        """특정 게시글의 댓글 목록 조회"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(ErrorCode.POST_NOT_FOUND, ResourceError(resource="게시글", id=postId))

        comments = await comment_model.getCommentsByPost(postId)
        return [await self._formatComment(c) for c in comments]

    async def createComment(self, postId: str, req: CommentCreateRequest, user: Dict) -> CommentResponse:
        """댓글 작성"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(ErrorCode.POST_NOT_FOUND, ResourceError(resource="게시글", id=postId))

        comment_data = await comment_model.createComment(
            postId=postId,
            userId=user["userId"],
            userNickname=user["nickname"],
            content=req.content
        )
        
        # 게시글의 댓글 수 캐시 업데이트
        await post_model.updateCommentCount(postId, 1)

        return await self._formatComment(comment_data)

    async def updateComment(self, postId: str, commentId: str, req: CommentUpdateRequest, user: Dict) -> CommentResponse:
        """댓글 수정"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(ErrorCode.POST_NOT_FOUND, ResourceError(resource="게시글", id=postId))

        comment = await comment_model.getCommentById(commentId)
        if not comment:
            raise APIError(ErrorCode.COMMENT_NOT_FOUND, ResourceError(resource="댓글", id=commentId))

        if str(comment["postId"]) != postId:
            raise APIError(ErrorCode.COMMENT_NOT_FOUND, ResourceError(resource="댓글", id=commentId))

        if str(comment["userId"]) != str(user["userId"]):
            raise APIError(ErrorCode.FORBIDDEN, ResourceError(resource="댓글"))

        updated_comment = await comment_model.updateComment(
            commentId=commentId,
            content=req.content
        )

        return await self._formatComment(updated_comment)

    async def deleteComment(self, postId: str, commentId: str, user: Dict) -> Dict:
        """댓글 삭제"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(ErrorCode.POST_NOT_FOUND, ResourceError(resource="게시글", id=postId))

        comment = await comment_model.getCommentById(commentId)
        if not comment:
            raise APIError(ErrorCode.COMMENT_NOT_FOUND, ResourceError(resource="댓글", id=commentId))

        if str(comment["postId"]) != postId:
            raise APIError(ErrorCode.COMMENT_NOT_FOUND, ResourceError(resource="댓글", id=commentId))

        if str(comment["userId"]) != str(user["userId"]):
            raise APIError(ErrorCode.FORBIDDEN, ResourceError(resource="댓글"))

        await comment_model.deleteComment(commentId)
        
        # 게시글의 댓글 수 캐시 업데이트
        await post_model.updateCommentCount(postId, -1)

        return comment


comment_controller = CommentController()
