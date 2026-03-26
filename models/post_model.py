from typing import Any, Dict, List, Optional, Union

from models.base_model import BaseModel
from utils.common.id_utils import generate_id
from utils.common.json_utils import parse_source_summary
from utils.database.db import fetch_one, fetch_all, execute


class PostModel(BaseModel):
    """게시글 데이터 관리 Model"""

    def _row_to_post(self, row: Optional[Dict]) -> Optional[Dict]:
        if not row:
            return None
        return {
            "postId": row["post_id"],
            "title": row["title"],
            "content": row["content"],
            "postType": row.get("post_type", "manual"),
            "sourceType": row.get("source_type"),
            "sourceSummary": parse_source_summary(row.get("source_summary")),
            "isDraft": bool(row.get("is_draft", False)),
            "authorId": row["author_id"],
            "authorNickname": row.get("author_nickname"),
            "authorProfileImageUrl": row.get("author_profile_image_url"),
            "fileUrl": row.get("post_image_url"),
            "createdAt": self._format_datetime(row.get("created_at")),
            "updatedAt": self._format_datetime(row.get("updated_at")),
            "hits": row.get("hits", 0),
            "likeCount": row.get("like_count", 0),
            "commentCount": row.get("comment_count", 0),
            "isLiked": bool(row.get("is_liked", 0)),
        }

    async def clear(self):
        """저장소 초기화 (테스트용)"""
        await execute("DELETE FROM post_likes")
        await execute("DELETE FROM posts")

    def getNextPostId(self) -> str:
        """다음 게시글 ID 생성 (ULID)"""
        return generate_id()

    async def createPost(
        self,
        title: str,
        content: str,
        authorId: Union[str, any],
        authorNickname: str,
        fileUrls: Optional[List[str]] = None,
    ) -> Dict:
        """게시글 생성"""
        postId = self.getNextPostId()
        authorIdStr = self._normalizeId(authorId)

        await execute(
            """
            INSERT INTO posts (post_id, user_id, title, content, post_image_url, hits, comment_count, created_at)
            VALUES (%s, %s, %s, %s, %s, 0, 0, NOW())
            """,
            (postId, authorIdStr, title, content, None),  # post_image_url is now NULL
        )
        
        # 여러 이미지 저장
        if fileUrls:
            await self.addPostImages(postId, fileUrls)

        post = await self.getPostById(postId)
        if post:
            post["authorNickname"] = authorNickname
        return post

    async def getPosts(
        self,
        limit: int = 10,
        offset: int = 0,
        current_user_id: Optional[str] = None,
        post_type: Optional[str] = None,
        sort_by: str = "published",
    ) -> Dict[str, Union[List[Dict], int]]:
        """게시글 목록 조회 (페이징 지원, post_type 필터링 추가)

        sort_by:
          - published: 게시(생성) 시각 기준 최신순 (기본)
          - activity: 자동 로그는 활동 근거일(summary_date JSON 또는 제목의 YYYY-MM-DD) 기준, 그 외는 게시일
        """
        if sort_by not in ("published", "activity"):
            sort_by = "published"

        current_user_id_str = self._normalizeId(current_user_id) if current_user_id else None

        if sort_by == "activity":
            # aiomysql가 query % params 전에 %를 해석하므로 MySQL 날짜 포맷은 %% 로 이스케이프
            order_clause = """
            ORDER BY
                COALESCE(
                    STR_TO_DATE(
                        NULLIF(TRIM(JSON_UNQUOTE(JSON_EXTRACT(p.source_summary, '$.summary_date'))), ''),
                        '%%Y-%%m-%%d'
                    ),
                    CASE
                        WHEN p.post_type = 'auto_log' AND p.title REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                            THEN STR_TO_DATE(SUBSTRING_INDEX(p.title, ' · ', 1), '%%Y-%%m-%%d')
                        ELSE NULL
                    END,
                    DATE(p.created_at)
                ) DESC,
                p.created_at DESC
            """
        else:
            order_clause = "ORDER BY p.created_at DESC"

        where_clause = "WHERE p.deleted_at IS NULL"
        # aiomysql: %s는 쿼리 텍스트 등장 순서대로 바인딩됨. is_liked(SELECT) → post_type(WHERE) → LIMIT → OFFSET.
        params_list = [current_user_id_str]

        if post_type:
            where_clause += " AND p.post_type = %s"
            params_list.append(post_type)

        params_list.extend([limit, offset])

        rows = await fetch_all(
            f"""
            SELECT
                p.post_id,
                p.user_id AS author_id,
                u.nickname AS author_nickname,
                u.profile_image_url AS author_profile_image_url,
                p.title,
                p.content,
                p.post_type,
                p.source_type,
                p.source_summary,
                p.is_draft,
                p.post_image_url,
                p.created_at,
                p.updated_at,
                p.hits,
                p.comment_count,
                (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id) AS like_count,
                (SELECT EXISTS(SELECT 1 FROM post_likes pl WHERE pl.post_id = p.post_id AND pl.user_id = %s)) AS is_liked
            FROM posts p
            LEFT JOIN users u ON u.user_id = p.user_id
            {where_clause}
            {order_clause}
            LIMIT %s OFFSET %s
            """,
            tuple(params_list),
        )

        total_where_clause = "WHERE deleted_at IS NULL"
        total_params = []
        if post_type:
            total_where_clause += " AND post_type = %s"
            total_params.append(post_type)

        total_row = await fetch_one(f"SELECT COUNT(*) AS total FROM posts {total_where_clause}", tuple(total_params))
        totalCount = total_row["total"] if total_row else 0

        return {
            "posts": [self._row_to_post(row) for row in rows],
            "totalCount": totalCount,
        }

    async def getPostById(self, postId: Union[str, any]) -> Optional[Dict]:
        """게시글 ID로 조회"""
        postIdStr = self._normalizeId(postId)
        row = await fetch_one(
            """
            SELECT
                p.post_id,
                p.user_id AS author_id,
                u.nickname AS author_nickname,
                u.profile_image_url AS author_profile_image_url,
                p.title,
                p.content,
                p.post_type,
                p.source_type,
                p.source_summary,
                p.is_draft,
                p.post_image_url,
                p.created_at,
                p.updated_at,
                p.hits,
                p.comment_count,
                (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id) AS like_count
            FROM posts p
            LEFT JOIN users u ON u.user_id = p.user_id
            WHERE p.post_id = %s AND p.deleted_at IS NULL
            """,
            (postIdStr,),
        )
        return self._row_to_post(row)

    async def incrementViewCount(self, postId: Union[str, any]) -> bool:
        """조회수 증가"""
        postIdStr = self._normalizeId(postId)
        affected = await execute(
            "UPDATE posts SET hits = hits + 1 WHERE post_id = %s AND deleted_at IS NULL",
            (postIdStr,),
        )
        return affected > 0

    async def updatePost(
        self,
        postId: Union[str, any],
        title: str,
        content: str,
        fileUrls: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """게시글 수정"""
        postIdStr = self._normalizeId(postId)
        fields = ["title = %s", "content = %s", "updated_at = NOW()"]
        params = [title, content]

        # post_image_url은 NULL로 설정 (이제 post_images 테이블 사용)
        fields.append("post_image_url = %s")
        params.append(None)

        params.append(postIdStr)
        await execute(
            f"""
            UPDATE posts
            SET {', '.join(fields)}
            WHERE post_id = %s AND deleted_at IS NULL
            """,
            params,
        )
        
        # 기존 이미지 삭제 후 새 이미지 추가
        if fileUrls is not None:
            await self.deletePostImages(postIdStr)
            if fileUrls:  # 빈 리스트가 아니면
                await self.addPostImages(postIdStr, fileUrls)
        
        return await self.getPostById(postIdStr)

    async def deletePost(self, postId: Union[str, any]) -> bool:
        """게시글 삭제"""
        postIdStr = self._normalizeId(postId)
        affected = await execute(
            "UPDATE posts SET deleted_at = NOW() WHERE post_id = %s AND deleted_at IS NULL",
            (postIdStr,),
        )
        return affected > 0

    async def getTotalPostsCount(self) -> int:
        """전체 게시글 수 조회"""
        row = await fetch_one("SELECT COUNT(*) AS total FROM posts WHERE deleted_at IS NULL")
        return row["total"] if row else 0

    async def toggleLike(self, postId: Union[str, any], userId: Union[str, any]) -> int:
        """좋아요 토글"""
        postIdStr = self._normalizeId(postId)
        userIdStr = self._normalizeId(userId)

        existing = await fetch_one(
            "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
            (postIdStr, userIdStr),
        )

        if existing:
            await execute(
                "DELETE FROM post_likes WHERE post_id = %s AND user_id = %s",
                (postIdStr, userIdStr),
            )
        else:
            await execute(
                "INSERT INTO post_likes (post_id, user_id, created_at) VALUES (%s, %s, NOW())",
                (postIdStr, userIdStr),
            )

        count_row = await fetch_one(
            "SELECT COUNT(*) AS cnt FROM post_likes WHERE post_id = %s",
            (postIdStr,),
        )
        return count_row["cnt"] if count_row else 0

    async def updateCommentCount(self, postId: Union[str, any], delta: int) -> int:
        """댓글 수 업데이트 (캐시)"""
        postIdStr = self._normalizeId(postId)
        await execute(
            "UPDATE posts SET comment_count = comment_count + %s WHERE post_id = %s AND deleted_at IS NULL",
            (delta, postIdStr),
        )
        row = await fetch_one(
            "SELECT comment_count FROM posts WHERE post_id = %s AND deleted_at IS NULL",
            (postIdStr,),
        )
        return row["comment_count"] if row else 0

    async def getLikeCount(self, postId: Union[str, any]) -> int:
        """좋아요 수 조회"""
        postIdStr = self._normalizeId(postId)
        row = await fetch_one(
            "SELECT COUNT(*) AS cnt FROM post_likes WHERE post_id = %s",
            (postIdStr,),
        )
        return row["cnt"] if row else 0

    async def isLikedByUser(self, postId: Union[str, any], userId: Union[str, any]) -> bool:
        """특정 사용자의 좋아요 여부"""
        postIdStr = self._normalizeId(postId)
        userIdStr = self._normalizeId(userId)
        row = await fetch_one(
            "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s",
            (postIdStr, userIdStr),
        )
        return row is not None

    async def getPostImages(self, postId: Union[str, any]) -> List[Dict]:
        """특정 게시글의 이미지 리스트 조회"""
        postIdStr = self._normalizeId(postId)
        rows = await fetch_all(
            "SELECT image_id, post_id, image_url, sort_order FROM post_images WHERE post_id = %s ORDER BY sort_order ASC",
            (postIdStr,),
        )
        return [
            {
                "imageId": row["image_id"],
                "postId": row["post_id"],
                "imageUrl": row["image_url"],
                "sortOrder": row["sort_order"],
            }
            for row in rows
        ]

    async def getPostImagesBatch(self, postIds: List[Union[str, any]]) -> Dict[str, List[Dict]]:
        """여러 게시글의 이미지 리스트를 한번에 조회 (N+1 문제 해결)"""
        if not postIds:
            return {}
        
        normalized_ids = [self._normalizeId(pid) for pid in postIds]
        placeholders = ", ".join(["%s"] * len(normalized_ids))
        rows = await fetch_all(
            f"SELECT image_id, post_id, image_url, sort_order FROM post_images WHERE post_id IN ({placeholders}) ORDER BY post_id, sort_order ASC",
            tuple(normalized_ids),
        )
        
        result = {pid: [] for pid in normalized_ids}
        for row in rows:
            result[row["post_id"]].append({
                "imageId": row["image_id"],
                "postId": row["post_id"],
                "imageUrl": row["image_url"],
                "sortOrder": row["sort_order"],
            })
        return result

    async def addPostImages(self, postId: Union[str, any], imageUrls: List[str]) -> int:
        """게시글에 여러 이미지 추가 (배치 INSERT)"""
        if not imageUrls:
            return 0
        
        postIdStr = self._normalizeId(postId)
        placeholders = []
        params = []
        
        for idx, imageUrl in enumerate(imageUrls):
            imageId = generate_id()
            placeholders.append("(%s, %s, %s, %s, NOW())")
            params.extend([imageId, postIdStr, imageUrl, idx])
        
        query = f"INSERT INTO post_images (image_id, post_id, image_url, sort_order, created_at) VALUES {', '.join(placeholders)}"
        affected = await execute(query, tuple(params))
        return affected

    async def deletePostImages(self, postId: Union[str, any]) -> int:
        """게시글의 모든 이미지 삭제"""
        postIdStr = self._normalizeId(postId)
        affected = await execute(
            "DELETE FROM post_images WHERE post_id = %s",
            (postIdStr,),
        )
        return affected


# Model 인스턴스 생성
post_model = PostModel()
