from typing import Dict, List, Optional, Union
from utils.common.id_utils import generate_id
from utils.database.db import fetch_one, fetch_all, execute


class CommentModel:
    """댓글 데이터 관리 Model"""

    def _normalizeId(self, idVal: Union[str, any]) -> str:
        """ID 정규화 (문자열로 변환)"""
        return str(idVal)

    def _format_datetime(self, value) -> Optional[str]:
        if not value:
            return None
        return value.isoformat()

    def _row_to_comment(self, row: Optional[Dict]) -> Optional[Dict]:
        if not row:
            return None
        return {
            "commentId": row["comment_id"],
            "postId": row["post_id"],
            "userId": row["user_id"],
            "userNickname": row.get("user_nickname"),
            "userProfileImageUrl": row.get("user_profile_image_url"),
            "content": row["content"],
            "createdAt": self._format_datetime(row.get("created_at")),
            "updatedAt": self._format_datetime(row.get("updated_at")),
        }

    async def clear(self):
        """저장소 초기화 (테스트용)"""
        await execute("DELETE FROM comments")

    def getNextCommentId(self) -> str:
        """다음 댓글 ID 생성 (ULID)"""
        return generate_id()

    async def createComment(
        self,
        postId: Union[str, any],
        userId: Union[str, any],
        userNickname: str,
        content: str,
    ) -> Dict:
        """댓글 생성"""
        commentId = self.getNextCommentId()
        postIdStr = self._normalizeId(postId)
        userIdStr = self._normalizeId(userId)

        await execute(
            """
            INSERT INTO comments (comment_id, post_id, user_id, content, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (commentId, postIdStr, userIdStr, content),
        )

        comment = await self.getCommentById(commentId)
        if comment:
            comment["userNickname"] = userNickname
        return comment

    async def getCommentsByPost(self, postId: Union[str, any]) -> List[Dict]:
        """특정 게시글의 모든 댓글 조회 (최신순)"""
        postIdStr = self._normalizeId(postId)
        rows = await fetch_all(
            """
            SELECT
                c.comment_id,
                c.post_id,
                c.user_id,
                u.nickname AS user_nickname,
                u.profile_image_url AS user_profile_image_url,
                c.content,
                c.created_at,
                c.updated_at
            FROM comments c
            LEFT JOIN users u ON u.user_id = c.user_id
            WHERE c.post_id = %s AND c.deleted_at IS NULL
            ORDER BY c.created_at DESC
            """,
            (postIdStr,),
        )
        return [self._row_to_comment(row) for row in rows]

    async def getCommentById(self, commentId: Union[str, any]) -> Optional[Dict]:
        """ID로 댓글 조회"""
        commentIdStr = self._normalizeId(commentId)
        row = await fetch_one(
            """
            SELECT
                c.comment_id,
                c.post_id,
                c.user_id,
                u.nickname AS user_nickname,
                u.profile_image_url AS user_profile_image_url,
                c.content,
                c.created_at,
                c.updated_at
            FROM comments c
            LEFT JOIN users u ON u.user_id = c.user_id
            WHERE c.comment_id = %s AND c.deleted_at IS NULL
            """,
            (commentIdStr,),
        )
        return self._row_to_comment(row)

    async def updateComment(self, commentId: Union[str, any], content: str) -> Optional[Dict]:
        """댓글 수정"""
        commentIdStr = self._normalizeId(commentId)
        await execute(
            """
            UPDATE comments
            SET content = %s, updated_at = NOW()
            WHERE comment_id = %s AND deleted_at IS NULL
            """,
            (content, commentIdStr),
        )
        return await self.getCommentById(commentIdStr)

    async def deleteComment(self, commentId: Union[str, any]) -> bool:
        """댓글 삭제"""
        commentIdStr = self._normalizeId(commentId)
        affected = await execute(
            "UPDATE comments SET deleted_at = NOW() WHERE comment_id = %s AND deleted_at IS NULL",
            (commentIdStr,),
        )
        return affected > 0

    async def getCommentsByUser(self, userId: Union[str, any]) -> List[Dict]:
        """특정 사용자의 모든 댓글 조회"""
        userIdStr = self._normalizeId(userId)
        rows = await fetch_all(
            """
            SELECT
                c.comment_id,
                c.post_id,
                c.user_id,
                u.nickname AS user_nickname,
                u.profile_image_url AS user_profile_image_url,
                c.content,
                c.created_at,
                c.updated_at
            FROM comments c
            LEFT JOIN users u ON u.user_id = c.user_id
            WHERE c.user_id = %s AND c.deleted_at IS NULL
            ORDER BY c.created_at DESC
            """,
            (userIdStr,),
        )
        return [self._row_to_comment(row) for row in rows]

    async def getCommentsCountByPost(self, postId: Union[str, any]) -> int:
        """특정 게시글의 댓글 수 조회"""
        postIdStr = self._normalizeId(postId)
        row = await fetch_one(
            "SELECT COUNT(*) AS cnt FROM comments WHERE post_id = %s AND deleted_at IS NULL",
            (postIdStr,),
        )
        return row["cnt"] if row else 0

    async def deleteCommentsByPost(self, postId: Union[str, any]) -> int:
        """특정 게시글의 모든 댓글 삭제"""
        postIdStr = self._normalizeId(postId)
        affected = await execute(
            "UPDATE comments SET deleted_at = NOW() WHERE post_id = %s AND deleted_at IS NULL",
            (postIdStr,),
        )
        return affected

    async def getTotalCommentsCount(self) -> int:
        """전체 댓글 수 조회"""
        row = await fetch_one("SELECT COUNT(*) AS cnt FROM comments WHERE deleted_at IS NULL")
        return row["cnt"] if row else 0

    def updateUserNickname(self, userId: str, newNickname: str) -> int:
        """사용자 닉네임 일괄 업데이트 (DB 정규화로 인해 no-op)"""
        return 0


# Model 인스턴스 생성
comment_model = CommentModel()
