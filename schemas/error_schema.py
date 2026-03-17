from typing import Optional, Any
from .base_schema import BaseSchema

class FieldError(BaseSchema):
    """필드 이름과 값을 포함 (중복 확인용 등)"""
    field: str
    value: Optional[Any] = None

class ValidationErrorDetail(BaseSchema):
    """필드와 에러 사유 포함"""
    field: str
    reason: Optional[str] = None

class ResourceError(BaseSchema):
    """리소스 명칭과 ID 포함"""
    resource: str
    id: Optional[str] = None
