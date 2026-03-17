import ulid

def generate_id() -> str:
    """전역적으로 고유하고 시간순 정렬 가능한 ULID 생성"""
    return str(ulid.ULID())

def is_valid_id(id_str: str) -> bool:
    """ULID 유효성 검사 (26자 문자열 여부 확인)"""
    try:
        ulid.from_str(id_str)
        return True
    except (ValueError, AttributeError):
        return False
