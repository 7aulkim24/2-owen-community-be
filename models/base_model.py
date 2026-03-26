"""
모든 Model 클래스의 공통 헬퍼 메서드를 제공하는 Base 클래스
"""

from typing import Optional, Union


class BaseModel:
    """공통 유틸리티 메서드를 제공하는 기본 모델 클래스"""

    def _normalizeId(self, idVal: Union[str, any]) -> str:
        """ID 정규화 (문자열로 변환)"""
        return str(idVal)

    def _format_datetime(self, value) -> Optional[str]:
        if not value:
            return None
        return value.isoformat()
