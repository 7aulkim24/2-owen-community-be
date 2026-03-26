from typing import Optional

from schemas import ResourceError
from utils.errors.error_codes import ErrorCode
from utils.errors.exceptions import APIError


def require_owner(
    resource_owner_id: str,
    actor_user_id: str,
    *,
    resource: str,
    resource_id: Optional[str] = None,
) -> None:
    """현재 사용자가 리소스 소유자인지 검증한다."""
    if str(resource_owner_id) == str(actor_user_id):
        return

    raise APIError(
        ErrorCode.FORBIDDEN,
        ResourceError(resource=resource, id=resource_id),
    )
