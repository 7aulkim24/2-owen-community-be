"""
공통 JSON 필드 파싱 유틸리티
"""

import json
from typing import Any, Dict, Optional


def parse_json_field(val: Any) -> Any:
    """
    MySQL JSON 컬럼이 aiomysql에서 str/bytes/dict로 올 수 있음.
    일관된 Python 객체(dict/list/None)로 변환합니다.
    """
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, (bytes, bytearray)):
        val = val.decode("utf-8")
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return val
    return val


def parse_source_summary(val: Any) -> Optional[Dict[str, Any]]:
    """
    posts 테이블의 source_summary JSON 컬럼 파싱.
    dict가 아닌 값은 None으로 반환합니다.
    """
    result = parse_json_field(val)
    return result if isinstance(result, dict) else None
