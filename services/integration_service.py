"""
연동 계정 OAuth 비즈니스 로직
- GitHub OAuth Authorization URL 생성
- 콜백 처리 (토큰 교환, 암호화, DB 저장)
- 연동 해제
"""

import base64
import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

from config import settings
from models.integration_model import integration_model
from models.sync_model import sync_model
from utils.integrations import github
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode
from cryptography.fernet import Fernet
from schemas import ConnectedAccountResponse


class IntegrationService:
    """연동 계정 비즈니스 로직"""

    def _get_fernet(self) -> Fernet:
        key = settings.token_encrypt_key.encode() if isinstance(settings.token_encrypt_key, str) else settings.token_encrypt_key
        return Fernet(key)

    def _encode_state(self, user_id: str) -> str:
        """user_id를 서명하여 state 생성 (콜백 시 세션 없이 사용자 식별)"""
        nonce = secrets.token_urlsafe(12)
        ts = str(int(time.time()))
        payload = f"{user_id}|{ts}|{nonce}"
        sig_hex = hmac.new(
            settings.secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        raw = base64.urlsafe_b64encode(f"{payload}|{sig_hex}".encode()).decode()
        return raw.rstrip("=")

    def decode_oauth_state(self, state: Optional[str]) -> Optional[str]:
        """
        OAuth 콜백 state 검증 후 user_id 반환.
        라우터 등 외부에서 호출 — 서명·만료(10분) 불일치 시 None.
        """
        if not state:
            return None
        try:
            raw = state + "=" * (4 - len(state) % 4)
            decoded = base64.urlsafe_b64decode(raw).decode()
            parts = decoded.rsplit("|", 1)
            if len(parts) != 2:
                return None
            payload, sig_hex = parts
            payload_parts = payload.split("|")
            if len(payload_parts) != 3:
                return None
            user_id, ts, _ = payload_parts
            expected = hmac.new(
                settings.secret_key.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, sig_hex):
                return None
            if int(time.time()) - int(ts) > 600:  # 10분
                return None
            return user_id
        except Exception:
            return None

    def _parse_token_expires_for_db(self, iso: Optional[str]) -> Optional[datetime]:
        """GitHub expires_in 기반 ISO 문자열 → MySQL DATETIME용 naive UTC"""
        if not iso:
            return None
        try:
            s = iso.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except (ValueError, TypeError, OSError):
            logger.warning("token_expires_at 파싱 실패, NULL로 저장: %r", iso)
            return None

    def get_authorize_url(self, user_id: str) -> str:
        """
        GitHub OAuth Authorization URL 생성
        state에 서명된 user_id 포함 (콜백 시 세션 쿠키 없이도 사용자 식별)
        """
        state = self._encode_state(user_id)
        # 스코프는 자동 활동 수집(auto_log)에 필요한 최소 범위 — 세분화 시 Phase 이후 검토
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_callback_url,
            "scope": "read:user repo",
            "state": state,
        }
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        return f"https://github.com/login/oauth/authorize?{qs}"

    async def handle_callback(self, code: str, user_id: str) -> Dict:
        """
        OAuth 콜백 처리: 토큰 교환 → 사용자 정보 조회 → 암호화 저장
        """
        token_data = await github.get_access_token(
            code=code,
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            callback_url=settings.github_callback_url,
        )
        access_token: str = token_data["access_token"]
        refresh_token: Optional[str] = token_data.get("refresh_token")
        token_expires_at = self._parse_token_expires_for_db(token_data.get("token_expires_at"))

        user_info = await github.get_user_info(access_token)
        provider_user_id = str(user_info.get("id", ""))
        provider_username = user_info.get("login")

        fernet = self._get_fernet()
        token_bytes = access_token.encode() if isinstance(access_token, str) else access_token
        encrypted = fernet.encrypt(token_bytes)
        access_token_encrypted = encrypted.decode()

        # refresh_token도 존재하면 암호화하여 저장
        refresh_token_encrypted: Optional[str] = None
        if refresh_token:
            rt_bytes = refresh_token.encode() if isinstance(refresh_token, str) else refresh_token
            refresh_token_encrypted = fernet.encrypt(rt_bytes).decode()

        result = await integration_model.upsert(
            user_id=user_id,
            provider="github",
            provider_user_id=provider_user_id,
            provider_username=provider_username,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expires_at=token_expires_at,
        )
        await sync_model.ensure_pending_job_after_connect(user_id, "github")
        return result

    async def get_decrypted_token_and_username_for_sync(
        self, user_id: str, provider: str
    ) -> Optional[tuple[str, Optional[str]]]:
        """
        GitHub 이벤트 수집용: 평문 access_token과 provider_username(login) 반환.
        username이 비어 있으면 호출 측에서 get_user_info로 보완 가능.
        """
        row = await integration_model.get_encrypted_token_and_username_for_sync(user_id, provider)
        if not row:
            return None
        enc = row.get("encrypted_token")
        if not enc:
            return None
        fernet = self._get_fernet()
        access_token = fernet.decrypt(enc.encode()).decode()
        uname = row.get("provider_username")
        return access_token, uname

    async def get_user_integrations(self, user_id: str) -> List[ConnectedAccountResponse]:
        """연동 계정 목록 조회"""
        rows = await integration_model.get_by_user_id(user_id)
        return [ConnectedAccountResponse.model_validate(r) for r in rows]

    async def disconnect(self, account_id: str, user_id: str) -> bool:
        """연동 해제 (소유권 검증 포함) — GitHub grant 철회 후 DB soft_delete"""
        existing = await integration_model.get_by_account_id(account_id)
        if not existing:
            raise APIError(ErrorCode.NOT_FOUND, message="연동 계정을 찾을 수 없습니다.")
        if existing["userId"] != user_id:
            raise APIError(ErrorCode.FORBIDDEN, message="해당 연동 계정에 대한 권한이 없습니다.")
        if existing.get("disconnectedAt"):
            raise APIError(ErrorCode.NOT_FOUND, message="이미 연동 해제된 계정입니다.")

        # GitHub OAuth grant 철회 (설정 화면에서 앱 제거)
        encrypted_token = await integration_model.get_encrypted_token_for_revoke(account_id, user_id)
        if encrypted_token and existing.get("provider") == "github":
            try:
                fernet = self._get_fernet()
                access_token = fernet.decrypt(encrypted_token.encode()).decode()
                await github.revoke_grant(
                    client_id=settings.github_client_id,
                    client_secret=settings.github_client_secret,
                    access_token=access_token,
                )
            except Exception:
                # 토큰 만료/이미 철회 등으로 실패해도 DB 연동 해제는 진행 (운영 추적용 로그)
                logger.warning(
                    "GitHub grant 철회 실패(로컬 DB 해제는 계속): account_id=%s",
                    account_id,
                    exc_info=True,
                )

        return await integration_model.soft_delete(account_id, user_id)


integration_service = IntegrationService()
