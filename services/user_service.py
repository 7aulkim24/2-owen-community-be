from typing import Dict, Union
from fastapi import Request
from models.user_model import user_model
from models.post_model import post_model
from models.comment_model import comment_model
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
        # 본인 확인
        if str(userId) != str(currentUser["userId"]):
            raise APIError(ErrorCode.FORBIDDEN)

        # 닉네임 중복 체크 (본인 닉네임과 다를 경우만)
        if req.nickname != currentUser["nickname"] and await user_model.nicknameExists(req.nickname):
            raise APIError(ErrorCode.ALREADY_EXISTS, FieldError(field="nickname", value=req.nickname), message="이미 사용 중인 닉네임입니다.")

        updateData = {
            "nickname": req.nickname,
            "profileImageUrl": req.profileImageUrl
        }
        updatedUser = await user_model.updateUser(userId, updateData)

        # 닉네임이 변경된 경우 게시글 및 댓글의 닉네임 동기화
        if req.nickname != currentUser["nickname"]:
            post_model.updateAuthorNickname(userId, req.nickname)
            comment_model.updateUserNickname(userId, req.nickname)

        return UserResponse.model_validate(updatedUser)

    async def changePassword(self, userId: str, req: PasswordChangeRequest, currentUser: Dict) -> Dict:
        """비밀번호 변경"""
        if str(userId) != str(currentUser["userId"]):
            raise APIError(ErrorCode.FORBIDDEN)

        await user_model.updateUser(userId, {"password": req.password})
        return {}

    async def deleteUser(self, userId: str, currentUser: Dict, request: Request) -> Dict:
        """회원 탈퇴"""
        if str(userId) != str(currentUser["userId"]):
            raise APIError(ErrorCode.FORBIDDEN)

        await user_model.deleteUser(userId)
        request.session.clear()
        return {}


user_service = UserService()
