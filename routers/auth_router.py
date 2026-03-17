from fastapi import APIRouter, Request, status, Query, UploadFile, File, Depends
from typing import Dict
from utils.common.response import StandardResponse
from utils.errors.error_codes import SuccessCode
from controllers.auth_controller import auth_controller
from schemas import SignupRequest, LoginRequest, UserResponse, EmailAvailabilityResponse, NicknameAvailabilityResponse, UserProfileImageResponse, StandardResponse as StandardResponseSchema
from utils.common.file_utils import save_upload_file
from utils.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/v1/auth", tags=["인증"])


@router.post("/signup", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest):
    """회원가입"""
    data = await auth_controller.signup(req)
    return StandardResponse.success(SuccessCode.CREATED, data)


@router.post("/login", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def login(req: LoginRequest, request: Request):
    """로그인"""
    data = await auth_controller.login(req, request)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.post("/logout", response_model=StandardResponseSchema[Dict], status_code=status.HTTP_200_OK)
async def logout(request: Request):
    """로그아웃"""
    data = await auth_controller.logout(request)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.get("/me", response_model=StandardResponseSchema[UserResponse], status_code=status.HTTP_200_OK)
async def get_me(user: Dict = Depends(get_current_user)):
    """내 정보 조회 (로그인 상태 검증)"""
    data = await auth_controller.getMe(user)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.get("/emails/availability", response_model=StandardResponseSchema[EmailAvailabilityResponse], status_code=status.HTTP_200_OK)
async def check_email_availability(email: str = Query(..., description="중복 확인할 이메일")):
    """이메일 중복 체크"""
    data = await auth_controller.checkEmailAvailability(email)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.get("/nicknames/availability", response_model=StandardResponseSchema[NicknameAvailabilityResponse], status_code=status.HTTP_200_OK)
async def check_nickname_availability(nickname: str = Query(..., description="중복 확인할 닉네임")):
    """닉네임 중복 체크"""
    data = await auth_controller.checkNicknameAvailability(nickname)
    return StandardResponse.success(SuccessCode.SUCCESS, data)


@router.post("/profile-image", response_model=StandardResponseSchema[UserProfileImageResponse], status_code=status.HTTP_201_CREATED)
async def upload_signup_profile_image(profileImage: UploadFile = File(...)):
    """회원가입용 프로필 이미지 업로드 (인증 불필요)"""
    fileUrl = save_upload_file(profileImage, "profile")
    return StandardResponse.success(SuccessCode.UPDATED, {"profileImageUrl": fileUrl})
