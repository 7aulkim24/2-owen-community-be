from fastapi import APIRouter, Depends, status, Request, UploadFile, File
from typing import Dict
from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode
from controllers.user_controller import user_controller
from schemas import UserResponse, UserUpdateRequest, PasswordChangeRequest, UserProfileImageResponse, StandardResponse as StandardResponseSchema
from utils.middleware.auth_middleware import get_current_user
from utils.common.file_utils import save_upload_file

router = APIRouter(prefix="/v1/users", tags=["사용자"])


@router.get("/me", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def get_my_info(user: Dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return StandardResponse.success(SuccessCode.SUCCESS, UserResponse.model_validate(user))


@router.patch("/me", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def update_my_info(req: UserUpdateRequest, user: Dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 수정"""
    data = await user_controller.updateUser(user["userId"], req, user)
    return StandardResponse.success(SuccessCode.UPDATED, data)


@router.patch("/password", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def change_my_password(req: PasswordChangeRequest, user: Dict = Depends(get_current_user)):
    """비밀번호 변경 (현재 사용자)"""
    await user_controller.changePassword(user["userId"], req, user)
    return StandardResponse.success(SuccessCode.UPDATED, None)


@router.delete("/me", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def delete_my_account(request: Request, user: Dict = Depends(get_current_user)):
    """회원 탈퇴 (현재 사용자)"""
    await user_controller.deleteUser(user["userId"], user, request)
    return StandardResponse.success(SuccessCode.SUCCESS, None)


@router.get("/{userId}", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def get_user_info(userId: str):
    """특정 사용자 정보 조회"""
    data = await user_controller.getUserById(userId)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.patch("/{userId}", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def update_user_info(userId: str, req: UserUpdateRequest, user: Dict = Depends(get_current_user)):
    """특정 사용자 정보 수정 (본인만 가능)"""
    data = await user_controller.updateUser(userId, req, user)
    return StandardResponse.success(SuccessCode.UPDATED, data)


@router.patch("/{userId}/password", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def change_user_password(userId: str, req: PasswordChangeRequest, user: Dict = Depends(get_current_user)):
    """비밀번호 변경 (본인만 가능)"""
    await user_controller.changePassword(userId, req, user)
    return StandardResponse.success(SuccessCode.UPDATED, None)


@router.delete("/{userId}", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def delete_user_account(userId: str, request: Request, user: Dict = Depends(get_current_user)):
    """회원 탈퇴 (본인만 가능)"""
    await user_controller.deleteUser(userId, user, request)
    return StandardResponse.success(SuccessCode.SUCCESS, None)


@router.post("/me/profile-image", response_model=StandardResponseSchema[UserProfileImageResponse], status_code=status.HTTP_201_CREATED)
async def upload_profile_image(profileImage: UploadFile = File(...), user: Dict = Depends(get_current_user)):
    """프로필 이미지 업로드"""
    fileUrl = save_upload_file(profileImage, "profile")
    return StandardResponse.success(SuccessCode.UPDATED, {"profileImageUrl": fileUrl})
