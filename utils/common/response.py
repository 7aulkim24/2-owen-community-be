"""
표준 API 응답 포맷
- Enum 기반 코드 사용
- 계층적 에러 구조 지원
"""

from typing import Any, Dict, List, Optional
from ..errors.error_codes import ErrorCode, SuccessCode, get_success_message


class StandardResponse:
    """모든 API 응답의 표준 포맷"""

    @staticmethod
    def success(code: SuccessCode, data: Any = None) -> Dict:
        """성공 응답 생성 (메시지는 FE에서 관리)"""
        return {
            "code": code.name,
            "message": "",
            "data": data if data is not None else {}
        }

    @staticmethod
    def error(code: ErrorCode, details: Any = None, message: Optional[str] = None) -> Dict:
        """
        에러 응답 생성
        - code: FE에서 메시지 맵핑의 키로 사용
        - message: 백엔드 내부 디버깅용 (FE에는 빈 문자열 전달)
        - details: 구체적인 에러 정보 (필드 에러 등)
        """
        return {
            "code": code.name,
            "message": "",  # 책임 분리를 위해 메시지는 무조건 비워서 보냄
            "details": details if details is not None else {}
        }

    @staticmethod
    def validation_error(errors: List) -> Dict:
        """
        Pydantic 검증 실패 응답
        """
        field_details = {}
        # ... (생략된 로직은 유지) ...
        for error in errors:
            field_name = str(error["loc"][-1])
            error_type = error["type"]
            
            # 설계도 예시: "email": ["REQUIRED", "INVALID_FORMAT"]
            if field_name not in field_details:
                field_details[field_name] = []
            
            # Pydantic 에러 타입을 설계도 태그로 매핑
            tag = "INVALID_FORMAT"
            if "missing" in error_type:
                tag = "REQUIRED"
            elif "too_long" in error_type:
                tag = "TOO_LONG"
            elif "too_short" in error_type:
                tag = "TOO_SHORT"
                
            if tag not in field_details[field_name]:
                field_details[field_name].append(tag)
                
        return {
            "code": ErrorCode.INVALID_INPUT.name,
            "message": "",
            "details": field_details
        }
