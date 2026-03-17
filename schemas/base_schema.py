from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, Optional, Any, Dict

T = TypeVar("T")

class BaseSchema(BaseModel):
    """모든 Pydantic 스키마의 기본 클래스"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class StandardResponse(BaseSchema, Generic[T]):
    """모든 API 응답의 표준 Pydantic 모델"""
    code: str
    message: str
    data: Optional[T] = None
    details: Optional[Dict[str, Any]] = None

class PaginationMeta(BaseSchema):
    """페이징 메타데이터"""
    totalCount: int
    limit: int
    offset: int
    currentPage: int
    totalPage: int
    hasNext: bool

class PaginatedData(BaseSchema, Generic[T]):
    """페이징 데이터와 메타데이터 결합"""
    items: T
    pagination: PaginationMeta

class PaginatedResponse(StandardResponse, Generic[T]):
    """페이징이 적용된 표준 API 응답"""
    data: Optional[PaginatedData[T]] = None
