"""
연동 계정(connected_accounts) 데이터 관리 Model
"""

from datetime import datetime
from typing import Dict, List, Optional

from models.base_model import BaseModel
from utils.common.id_utils import generate_id
from utils.database.db import fetch_one, fetch_all, execute


class IntegrationModel(BaseModel):
    """연동 계정 데이터 관리 Model"""

    def _row_to_dict(self, row: Optional[Dict]) -> Optional[Dict]:
        if not row:
            return None
        return {
            "accountId": row["account_id"],
            "userId": row["user_id"],
            "provider": row["provider"],
            "providerUserId": row["provider_user_id"],
            "providerUsername": row.get("provider_username"),
            "connectedAt": self._format_datetime(row.get("connected_at")),
            "updatedAt": self._format_datetime(row.get("updated_at")),
            "disconnectedAt": self._format_datetime(row.get("disconnected_at")),
        }

    async def get_by_user_id(self, user_id: str) -> List[Dict]:
        """
        해당 유저의 연동 계정 목록 조회 (disconnected_at IS NULL인 활성 연동만)
        """
        rows = await fetch_all(
            """
            SELECT account_id, user_id, provider, provider_user_id, provider_username,
                   connected_at, updated_at, disconnected_at
            FROM connected_accounts
            WHERE user_id = %s AND disconnected_at IS NULL
            ORDER BY connected_at DESC
            """,
            (user_id,),
        )
        return [self._row_to_dict(row) for row in rows]

    async def get_by_account_id(self, account_id: str) -> Optional[Dict]:
        """
        단건 조회 (소유권 검증용)
        """
        row = await fetch_one(
            """
            SELECT account_id, user_id, provider, provider_user_id, provider_username,
                   connected_at, updated_at, disconnected_at
            FROM connected_accounts
            WHERE account_id = %s
            """,
            (account_id,),
        )
        return self._row_to_dict(row)

    async def get_encrypted_token_and_username_for_sync(
        self, user_id: str, provider: str
    ) -> Optional[Dict[str, Optional[str]]]:
        """
        동기화용: 활성 연동의 암호화된 access_token + provider_username 조회.
        """
        row = await fetch_one(
            """
            SELECT access_token, provider_username
            FROM connected_accounts
            WHERE user_id = %s AND provider = %s AND disconnected_at IS NULL
            """,
            (user_id, provider),
        )
        if not row or not row.get("access_token"):
            return None
        return {
            "encrypted_token": row["access_token"],
            "provider_username": row.get("provider_username"),
        }

    async def get_encrypted_token_for_revoke(self, account_id: str, user_id: str) -> Optional[str]:
        """
        연동 해제 시 GitHub grant 철회용으로 암호화된 access_token 조회
        account_id + user_id 소유권 검증 후에만 반환
        """
        row = await fetch_one(
            """
            SELECT access_token
            FROM connected_accounts
            WHERE account_id = %s AND user_id = %s AND disconnected_at IS NULL
            """,
            (account_id, user_id),
        )
        return row["access_token"] if row and row.get("access_token") else None

    async def upsert(
        self,
        user_id: str,
        provider: str,
        provider_user_id: str,
        provider_username: Optional[str],
        access_token_encrypted: str,
        refresh_token_encrypted: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
    ) -> Dict:
        """
        신규 연동 또는 재연동.
        UNIQUE KEY (user_id, provider) 충돌 시 기존 레코드를 갱신합니다.
        - 신규: account_id를 새로 발급하여 삽입
        - 재연동: 기존 account_id를 유지하고 토큰·상태만 업데이트
        ON DUPLICATE 시 INSERT 행 별칭(new) 참조 — MySQL 8.0.19+ (VALUES() 폐기 경고 방지)
        """
        account_id = generate_id()
        await execute(
            """
            INSERT INTO connected_accounts
                (account_id, user_id, provider, provider_user_id, provider_username,
                 access_token, refresh_token, token_expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) AS new
            ON DUPLICATE KEY UPDATE
                provider_user_id  = new.provider_user_id,
                provider_username = new.provider_username,
                access_token      = new.access_token,
                refresh_token     = new.refresh_token,
                token_expires_at  = new.token_expires_at,
                disconnected_at   = NULL,
                updated_at        = NOW()
            """,
            (
                account_id, user_id, provider, provider_user_id, provider_username,
                access_token_encrypted, refresh_token_encrypted, token_expires_at,
            ),
        )
        result = await self.get_by_user_id_and_provider(user_id, provider)
        return result

    async def get_by_user_id_and_provider(self, user_id: str, provider: str) -> Dict:
        """user_id + provider로 단건 조회 (upsert 후 반환용)"""
        row = await fetch_one(
            """
            SELECT account_id, user_id, provider, provider_user_id, provider_username,
                   connected_at, updated_at, disconnected_at
            FROM connected_accounts
            WHERE user_id = %s AND provider = %s AND disconnected_at IS NULL
            """,
            (user_id, provider),
        )
        result = self._row_to_dict(row)
        if not result:
            raise RuntimeError(f"Expected row after upsert for user_id={user_id}, provider={provider}")
        return result

    async def soft_delete(self, account_id: str, user_id: str) -> bool:
        """
        연동 해제 — disconnected_at 업데이트
        소유권 검증: user_id 일치 시에만 업데이트
        """
        affected = await execute(
            """
            UPDATE connected_accounts
            SET disconnected_at = NOW()
            WHERE account_id = %s AND user_id = %s
            """,
            (account_id, user_id),
        )
        return affected > 0


integration_model = IntegrationModel()
