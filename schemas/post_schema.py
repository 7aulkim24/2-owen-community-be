from pydantic import Field, field_validator
from typing import Any, Dict, Optional, List
from enum import Enum
from .base_schema import BaseSchema


class PostType(str, Enum):
    """게시글 유형"""
    manual = "manual"               # 수동 작성 (기본값)
    auto_log = "auto_log"           # 자동 기록 (GitHub 활동 기반)
    weekly_digest = "weekly_digest" # 주간 회고


class SourceType(str, Enum):
    """소스 유형"""
    github = "github"
    notion = "notion"


class PostCreateRequest(BaseSchema):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    fileUrls: Optional[List[str]] = None
    
    @field_validator('fileUrls')
    @classmethod
    def validate_file_urls(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError('최대 5개의 이미지만 업로드할 수 있습니다')
        return v

class PostUpdateRequest(BaseSchema):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    fileUrls: Optional[List[str]] = None
    
    @field_validator('fileUrls')
    @classmethod
    def validate_file_urls(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError('최대 5개의 이미지만 업로드할 수 있습니다')
        return v

class PostAuthor(BaseSchema):
    userId: str
    nickname: str
    profileImageUrl: Optional[str] = None

class PostImage(BaseSchema):
    imageId: str
    imageUrl: str
    sortOrder: int

class PostFile(BaseSchema):
    fileId: str
    fileUrl: str

class PostResponse(BaseSchema):
    postId: str
    title: str
    content: str
    postType: PostType = PostType.manual
    sourceType: Optional[SourceType] = None
    sourceSummary: Optional[Dict[str, Any]] = None
    isDraft: bool = False
    likeCount: int = 0
    commentCount: int = 0
    hits: int = 0
    author: PostAuthor
    files: Optional[List[PostImage]] = None
    createdAt: str
    updatedAt: Optional[str] = None
    isLiked: Optional[bool] = None

class PostImageUploadResponse(BaseSchema):
    postFileUrl: str

class PostImagesUploadResponse(BaseSchema):
    postFileUrls: List[str]
