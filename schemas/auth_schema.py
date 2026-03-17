import re
from pydantic import EmailStr, Field, field_validator
from typing import Optional
from .base_schema import BaseSchema
from .user_schema import UserResponse

class SignupRequest(BaseSchema):
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=20,
        description="영문 대소문자, 숫자, 특수문자를 포함해야 함"
    )
    nickname: str = Field(..., min_length=1, max_length=10)
    profileImageUrl: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        비밀번호 복잡성 검사
        - 소문자, 대문자, 숫자, 특수문자 포함 여부 확인
        - Python re 모듈은 Look-around를 지원하므로 기존 정규식 사용 가능
        """
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$"
        if not re.match(password_pattern, v):
            raise ValueError("비밀번호는 영문 대소문자, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다.")
        return v

class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(...)

class EmailAvailabilityResponse(BaseSchema):
    available: bool

class NicknameAvailabilityResponse(BaseSchema):
    available: bool
