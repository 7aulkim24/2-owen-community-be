from enum import Enum


class ErrorCode(Enum):
    """에러 코드 열거형 (계층화 및 세분화 버전)"""
    
    # (상태코드, 기본 메시지)
    
    # --- 공통 및 시스템 에러 ---
    BAD_REQUEST = (400, "잘못된 요청입니다.")
    UNAUTHORIZED = (401, "로그인이 필요합니다.")
    FORBIDDEN = (403, "권한이 없습니다.")
    NOT_FOUND = (404, "리소스를 찾을 수 없습니다.")
    METHOD_NOT_ALLOWED = (405, "허용되지 않은 메서드입니다.")
    CONFLICT = (409, "리소스 충돌이 발생했습니다.")
    TOO_MANY_REQUEST = (429, "너무 많은 요청이 발생했습니다.")
    INTERNAL_SERVER_ERROR = (500, "서버 내부 오류가 발생했습니다.")

    # --- 검증 및 입력 에러 ---
    INVALID_INPUT = (422, "입력 값이 올바르지 않습니다.")
    INVALID_CREDENTIALS = (401, "인증 정보가 올바르지 않습니다.")
    
    # --- 상태 에러 ---
    ALREADY_EXISTS = (409, "이미 존재하는 리소스입니다.")
    ALREADY_LOGIN = (409, "이미 로그인된 상태입니다.")

    # --- 리소스 존재 여부 핵심 에러 ---
    USER_NOT_FOUND = (404, "사용자를 찾을 수 없습니다.")
    POST_NOT_FOUND = (404, "게시글을 찾을 수 없습니다.")
    COMMENT_NOT_FOUND = (404, "댓글을 찾을 수 없습니다.")

    # --- 기타 설계도 명시 특수 에러 ---
    POST_ALREADY_LIKED = (409, "이미 좋아요를 누른 게시글입니다.")
    POST_ALREADY_UNLIKED = (409, "좋아요를 누르지 않은 게시글입니다.")
    PAYLOAD_TOO_LARGE = (413, "파일 크기가 너무 큽니다.")
    RATE_LIMIT_EXCEEDED = (429, "요청 빈도가 너무 높습니다.")

    @property
    def status_code(self) -> int:
        return self.value[0]

    @property
    def default_message(self) -> str:
        return self.value[1]


class SuccessCode(Enum):
    """성공 코드 열거형 (통합 및 구조화 버전)"""
    
    # (상태코드, 기본 메시지)
    SUCCESS = (200, "요청이 성공적으로 처리되었습니다.")
    CREATED = (201, "리소스가 성공적으로 생성되었습니다.")
    UPDATED = (200, "리소스가 성공적으로 수정되었습니다.")
    DELETED = (200, "리소스가 성공적으로 삭제되었습니다.")

    @property
    def status_code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]


def get_error_status(code: ErrorCode) -> int:
    """하위 호환성을 위한 함수"""
    return code.status_code


def get_success_message(code: SuccessCode) -> str:
    """성공 메시지 조회"""
    return code.message
