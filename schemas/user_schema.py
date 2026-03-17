from pydantic import Field, EmailStr
from typing import Optional
from .base_schema import BaseSchema

class UserUpdateRequest(BaseSchema):
    nickname: str = Field(..., min_length=1)
    profileImageUrl: Optional[str] = None

class PasswordChangeRequest(BaseSchema):
    password: str = Field(..., min_length=8)

class UserProfileImageResponse(BaseSchema):
    profileImageUrl: str

class UserResponse(BaseSchema):
    userId: str
    email: EmailStr
    nickname: str
    profileImageUrl: Optional[str] = None
    createdAt: str
    updatedAt: Optional[str] = None
