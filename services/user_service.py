from typing import Dict, Union
from fastapi import Request
from models.user_model import user_model
from utils.auth import clear_auth_session, require_owner
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode
from schemas import UserUpdateRequest, PasswordChangeRequest, UserResponse, ResourceError, FieldError


class UserService:
    """사용자 관련 비즈니스 로직"""

    async def getUserById(self, userId: str) -> UserResponse:
        """사용자 정보 조회"""
        user = await user_model.getUserById(userId)
        if not user:
            raise APIError(ErrorCode.USER_NOT_FOUND, ResourceError(resource="사용자", id=userId))
        return UserResponse.model_validate(user)

    async def updateUser(self, userId: str, req: UserUpdateRequest, currentUser: Dict) -> UserResponse:
        """사용자 정보 수정"""
        require_owner(userId, currentUser["userId"], resource="사용자", resource_id=userId)

        # 닉네임 중복 체크 (본인 닉네임과 다를 경우만)
        if req.nickname != currentUser["nickname"] and await user_model.nicknameExists(req.nickname):
            raise APIError(ErrorCode.ALREADY_EXISTS, FieldError(field="nickname", value=req.nickname), message="이미 사용 중인 닉네임입니다.")

        updateData = {
            "nickname": req.nickname,
            "profileImageUrl": req.profileImageUrl
        }
        updatedUser = await user_model.updateUser(userId, updateData)

        return UserResponse.model_validate(updatedUser)

    async def changePassword(self, userId: str, req: PasswordChangeRequest, currentUser: Dict) -> Dict:
        """비밀번호 변경 (현재 비밀번호 검증 포함)"""
        require_owner(userId, currentUser["userId"], resource="사용자", resource_id=userId)

        # 현재 비밀번호 검증
        if req.currentPassword:
            user = await user_model.getUserByEmail(currentUser["email"])
            if not user or not user_model.verifyPassword(req.currentPassword, user.get("password", "")):
                raise APIError(ErrorCode.INVALID_CREDENTIALS, message="현재 비밀번호가 올바르지 않습니다.")

        await user_model.updateUser(userId, {"password": req.password})
        return {}

    async def deleteUser(self, userId: str, currentUser: Dict, request: Request) -> Dict:
        """회원 탈퇴"""
        require_owner(userId, currentUser["userId"], resource="사용자", resource_id=userId)

        await user_model.deleteUser(userId)
        clear_auth_session(request.session)
        return {}


user_service = UserService()
