from pydantic import Field
from typing import Optional
from .base_schema import BaseSchema

class CommentCreateRequest(BaseSchema):
    content: str = Field(..., min_length=1)

class CommentUpdateRequest(BaseSchema):
    content: str = Field(..., min_length=1)

class CommentAuthor(BaseSchema):
    userId: str
    nickname: str
    profileImageUrl: Optional[str] = None

class CommentResponse(BaseSchema):
    commentId: str
    postId: str
    content: str
    author: CommentAuthor
    createdAt: str
    updatedAt: Optional[str] = None
