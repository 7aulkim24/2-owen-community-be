from enum import Enum
from typing import Optional
from .base_schema import BaseSchema


class ProviderEnum(str, Enum):
    """연동 제공자"""
    github = "github"
    notion = "notion"


class ConnectedAccountResponse(BaseSchema):
    """연동 계정 응답 스키마"""
    accountId: str
    provider: str
    providerUsername: Optional[str] = None
    connectedAt: Optional[str] = None
    disconnectedAt: Optional[str] = None
