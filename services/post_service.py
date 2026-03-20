from typing import List, Dict, Union, Optional
from models.post_model import post_model
from models.comment_model import comment_model
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode
from schemas import (
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
    PostAuthor,
    PostFile,
    PaginatedData,
    PaginationMeta,
    ResourceError,
)
from schemas.post_schema import PostType, SourceType


class PostService:
    """게시글 관련 비즈니스 로직"""

    async def _formatPost(
        self,
        post: Dict,
        current_user_id: Optional[str] = None,
        images: Optional[List[Dict]] = None,
    ) -> PostResponse:
        """Post 데이터를 API 응답 규격에 맞게 변환"""
        author_id = post["authorId"]

        nickname = post.get("authorNickname")
        profile_image_url = post.get("authorProfileImageUrl")
        
        author_data = PostAuthor(
            userId=author_id,
            nickname=nickname,
            profileImageUrl=profile_image_url
        )

        is_liked = post.get("isLiked")
        if is_liked is None and current_user_id:
            is_liked = await post_model.isLikedByUser(post["postId"], current_user_id)
        
        # 다중 이미지 처리
        if images is not None:
            post_images = images
        else:
            post_images = await post_model.getPostImages(post["postId"])
        from schemas import PostImage
        files_list = [
            PostImage(
                imageId=img["imageId"],
                imageUrl=img["imageUrl"],
                sortOrder=img["sortOrder"]
            )
            for img in post_images
        ] if post_images else None

        raw_pt = post.get("postType", "manual")
        try:
            post_type = PostType(raw_pt) if isinstance(raw_pt, str) else raw_pt
        except ValueError:
            post_type = PostType.manual

        source_type: Optional[SourceType] = None
        raw_st = post.get("sourceType")
        if raw_st:
            try:
                source_type = SourceType(raw_st) if isinstance(raw_st, str) else raw_st
            except ValueError:
                source_type = None

        return PostResponse(
            postId=post["postId"],
            title=post["title"],
            content=post["content"],
            postType=post_type,
            sourceType=source_type,
            sourceSummary=post.get("sourceSummary"),
            isDraft=bool(post.get("isDraft", False)),
            likeCount=post.get("likeCount", 0), # 캐시된 값 사용
            commentCount=post.get("commentCount", 0), # 캐시된 값 사용
            hits=post["hits"],
            author=author_data,
            files=files_list,
            createdAt=post["createdAt"],
            updatedAt=post.get("updatedAt"),
            isLiked=is_liked,
        )

    async def getAllPosts(self, limit: int = 10, offset: int = 0, current_user_id: Optional[str] = None, post_type: Optional[str] = None) -> PaginatedData[List[PostResponse]]:
        """게시글 목록 조회 로직 (페이징 메타데이터 포함)"""
        result = await post_model.getPosts(limit=limit, offset=offset, current_user_id=current_user_id, post_type=post_type)
        posts_data = result["posts"]
        total_count = result["totalCount"]

        # N+1 문제 해결을 위한 배치 이미지 조회
        post_ids = [post["postId"] for post in posts_data]
        images_batch = await post_model.getPostImagesBatch(post_ids)

        formatted_posts = [await self._formatPost(post, current_user_id=current_user_id, images=images_batch.get(post["postId"], [])) for post in posts_data]
        
        # 페이징 메타데이터 계산
        total_page = (total_count + limit - 1) // limit if total_count > 0 else 0
        current_page = (offset // limit) + 1
        has_next = offset + limit < total_count

        return PaginatedData(
            items=formatted_posts,
            pagination=PaginationMeta(
                totalCount=total_count,
                limit=limit,
                offset=offset,
                currentPage=current_page,
                totalPage=total_page,
                hasNext=has_next
            )
        )

    async def getPostById(
        self,
        postId: str,
        incHits: bool = True,
        current_user_id: Optional[str] = None,
    ) -> PostResponse:
        """게시글 상세 조회 로직"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(
                ErrorCode.POST_NOT_FOUND, 
                ResourceError(resource="게시글", id=postId)
            )

        # 조회수 증가 (필요한 경우만)
        if incHits:
            await post_model.incrementViewCount(postId)
            # 증가된 데이터 반영을 위해 다시 조회
            post = await post_model.getPostById(postId)

        return await self._formatPost(post, current_user_id=current_user_id)

    async def createPost(self, req: PostCreateRequest, user: Dict) -> PostResponse:
        """게시글 생성 로직"""
        post_data = await post_model.createPost(
            title=req.title,
            content=req.content,
            authorId=user["userId"],
            authorNickname=user["nickname"],
            fileUrls=req.fileUrls
        )

        return await self._formatPost(post_data, current_user_id=user["userId"])

    async def updatePost(self, postId: str, req: PostUpdateRequest, user: Dict) -> PostResponse:
        """게시글 수정 로직"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(
                ErrorCode.POST_NOT_FOUND, 
                ResourceError(resource="게시글", id=postId)
            )

        # 권한 확인 (작성자 확인)
        if str(post["authorId"]) != str(user["userId"]):
            raise APIError(ErrorCode.FORBIDDEN, ResourceError(resource="게시글"))

        updated_post = await post_model.updatePost(
            postId=postId,
            title=req.title,
            content=req.content,
            fileUrls=req.fileUrls
        )

        return await self._formatPost(updated_post, current_user_id=user["userId"])

    async def deletePost(self, postId: str, user: Dict) -> Dict:
        """게시글 삭제 로직"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(
                ErrorCode.POST_NOT_FOUND, 
                ResourceError(resource="게시글", id=postId)
            )

        # 권한 확인
        if str(post["authorId"]) != str(user["userId"]):
            raise APIError(ErrorCode.FORBIDDEN, ResourceError(resource="게시글"))

        # 게시글 삭제 시 관련 댓글들도 함께 삭제
        await comment_model.deleteCommentsByPost(postId)

        # Model을 통해 게시글 삭제
        await post_model.deletePost(postId)

        return post

    async def togglePostLike(self, postId: str, userId: str) -> Dict:
        """게시글 좋아요 토글"""
        post = await post_model.getPostById(postId)
        if not post:
            raise APIError(ErrorCode.POST_NOT_FOUND, ResourceError(resource="게시글", id=postId))
            
        likeCount = await post_model.toggleLike(postId, userId)
        return {"likeCount": likeCount}


post_service = PostService()
