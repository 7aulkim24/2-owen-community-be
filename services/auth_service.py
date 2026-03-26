from typing import Dict
from fastapi import Request
from models.user_model import user_model
from utils.auth import clear_auth_session, write_auth_session
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode
from schemas import SignupRequest, LoginRequest, UserResponse, FieldError


class AuthService:
    """인증 관련 비즈니스 로직"""

    async def signup(self, req: SignupRequest) -> UserResponse:
        """회원가입"""
        if await user_model.emailExists(req.email):
            raise APIError(ErrorCode.ALREADY_EXISTS, FieldError(field="email", value=req.email), message="이미 사용 중인 이메일입니다.")
        if await user_model.nicknameExists(req.nickname):
            raise APIError(ErrorCode.ALREADY_EXISTS, FieldError(field="nickname", value=req.nickname), message="이미 사용 중인 닉네임입니다.")

        user = await user_model.createUser(req.email, req.password, req.nickname, req.profileImageUrl)
        return UserResponse.model_validate(user)

    async def login(self, req: LoginRequest, request: Request) -> UserResponse:
        """로그인"""
        user = await user_model.authenticateUser(req.email, req.password)
        if not user:
            raise APIError(ErrorCode.INVALID_CREDENTIALS)

        write_auth_session(request.session, user)
        return UserResponse.model_validate(user)

    async def logout(self, request: Request) -> Dict:
        """로그아웃"""
        clear_auth_session(request.session)
        return {}

    async def getMe(self, user: Dict) -> UserResponse:
        """내 정보 조회"""
        return UserResponse.model_validate(user)

    async def checkEmailAvailability(self, email: str) -> Dict:
        """이메일 중복 확인"""
        return {"available": not await user_model.emailExists(email)}

    async def checkNicknameAvailability(self, nickname: str) -> Dict:
        """닉네임 중복 확인"""
        return {"available": not await user_model.nicknameExists(nickname)}


auth_service = AuthService()
