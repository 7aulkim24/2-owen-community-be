from typing import Dict, Optional, List, Union
import bcrypt
from utils.common.id_utils import generate_id
from utils.database.db import fetch_one, fetch_all, execute


class UserModel:
    """사용자 데이터 관리 Model"""

    def _normalizeId(self, idVal: Union[str, any]) -> str:
        """ID 정규화 (문자열로 변환)"""
        return str(idVal)

    def _format_datetime(self, value) -> Optional[str]:
        if not value:
            return None
        return value.isoformat()

    def _row_to_user(self, row: Optional[Dict]) -> Optional[Dict]:
        if not row:
            return None
        return {
            "userId": row["user_id"],
            "email": row["email"],
            "password": row["password"],
            "nickname": row["nickname"],
            "profileImageUrl": row.get("profile_image_url"),
            "createdAt": self._format_datetime(row.get("created_at")),
            "updatedAt": self._format_datetime(row.get("updated_at")),
        }

    def hashPassword(self, password: str) -> str:
        """비밀번호 해싱 (bcrypt 직접 사용)"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verifyPassword(self, plainPassword: str, hashedPassword: str) -> bool:
        """비밀번호 검증 (bcrypt 직접 사용)"""
        try:
            return bcrypt.checkpw(plainPassword.encode("utf-8"), hashedPassword.encode("utf-8"))
        except Exception:
            return False

    async def clear(self):
        """저장소 초기화 (테스트용)"""
        await execute("DELETE FROM users")

    def getNextUserId(self) -> str:
        """다음 사용자 ID 생성 (ULID)"""
        return generate_id()

    async def createUser(self, email: str, password: str, nickname: str, profileImageUrl: Optional[str] = None) -> Dict:
        """사용자 생성"""
        userId = self.getNextUserId()
        hashedPassword = self.hashPassword(password)

        await execute(
            """
            INSERT INTO users (user_id, email, password, nickname, profile_image_url, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (userId, email, hashedPassword, nickname, profileImageUrl),
        )

        return await self.getUserById(userId)

    async def getUserById(self, userId: Union[str, any]) -> Optional[Dict]:
        """ID로 사용자 조회"""
        userIdStr = self._normalizeId(userId)
        row = await fetch_one(
            """
            SELECT user_id, email, password, nickname, profile_image_url, created_at, updated_at
            FROM users
            WHERE user_id = %s AND deleted_at IS NULL
            """,
            (userIdStr,),
        )
        return self._row_to_user(row)

    async def getUserByEmail(self, email: str) -> Optional[Dict]:
        """이메일로 사용자 조회"""
        row = await fetch_one(
            """
            SELECT user_id, email, password, nickname, profile_image_url, created_at, updated_at
            FROM users
            WHERE email = %s AND deleted_at IS NULL
            """,
            (email,),
        )
        return self._row_to_user(row)

    async def emailExists(self, email: str) -> bool:
        """이메일 중복 체크"""
        row = await fetch_one(
            "SELECT 1 FROM users WHERE email = %s AND deleted_at IS NULL",
            (email,),
        )
        return row is not None

    async def nicknameExists(self, nickname: str) -> bool:
        """닉네임 중복 체크"""
        row = await fetch_one(
            "SELECT 1 FROM users WHERE nickname = %s AND deleted_at IS NULL",
            (nickname,),
        )
        return row is not None

    async def updateUser(self, userId: Union[str, any], updateData: Dict) -> Optional[Dict]:
        """사용자 정보 수정"""
        userIdStr = self._normalizeId(userId)
        fields = []
        params = []

        if "nickname" in updateData:
            fields.append("nickname = %s")
            params.append(updateData["nickname"])

        if "email" in updateData:
            fields.append("email = %s")
            params.append(updateData["email"])

        if "password" in updateData:
            fields.append("password = %s")
            params.append(self.hashPassword(updateData["password"]))

        if "profileImageUrl" in updateData:
            fields.append("profile_image_url = %s")
            params.append(updateData["profileImageUrl"])

        if fields:
            fields.append("updated_at = NOW()")
            params.append(userIdStr)
            await execute(
                f"UPDATE users SET {', '.join(fields)} WHERE user_id = %s AND deleted_at IS NULL",
                params,
            )

        return await self.getUserById(userIdStr)

    async def deleteUser(self, userId: Union[str, any]) -> bool:
        """사용자 삭제"""
        userIdStr = self._normalizeId(userId)
        affected = await execute(
            "UPDATE users SET deleted_at = NOW() WHERE user_id = %s AND deleted_at IS NULL",
            (userIdStr,),
        )
        return affected > 0

    async def getAllUsers(self) -> List[Dict]:
        """모든 사용자 조회"""
        rows = await fetch_all(
            """
            SELECT user_id, email, password, nickname, profile_image_url, created_at, updated_at
            FROM users
            WHERE deleted_at IS NULL
            """
        )
        return [self._row_to_user(row) for row in rows]

    async def authenticateUser(self, email: str, password: str) -> Optional[Dict]:
        """사용자 인증"""
        user = await self.getUserByEmail(email)
        if user and self.verifyPassword(password, user["password"]):
            return user
        return None


# Model 인스턴스 생성
user_model = UserModel()
