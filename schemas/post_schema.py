from pydantic import Field, field_validator
from typing import Optional, List
from .base_schema import BaseSchema

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
