import os
import uuid
from fastapi import UploadFile
from utils.errors.exceptions import APIError
from utils.errors.error_codes import ErrorCode

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".JPG", ".JPEG"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def save_upload_file(file: UploadFile, domain: str) -> str:
    """
    업로드된 파일을 로컬에 저장하고 URL 경로 반환
    domain: 'post' 또는 'profile'
    """
    # 1. 확장자 검증
    file_extension = os.path.splitext(file.filename)[1]
    if file_extension not in ALLOWED_EXTENSIONS:
        raise APIError(ErrorCode.BAD_REQUEST, message=f"허용되지 않은 파일 형식입니다. ({', '.join(ALLOWED_EXTENSIONS)})")

    # 2. 파일 크기 검증 (FastAPI UploadFile.size 사용)
    # size가 없는 경우를 대비해 file.file.seek 활용 가능하지만 최신 FastAPI 기준 size 활용
    if file.size and file.size > MAX_FILE_SIZE:
        raise APIError(ErrorCode.PAYLOAD_TOO_LARGE, message="파일 크기는 5MB를 초과할 수 없습니다.")

    base_dir = "public"
    sub_dir = f"image/{domain}"
    upload_path = os.path.join(base_dir, sub_dir)
    
    # 디렉토리 생성 (이미 main.py에서 생성하지만 안전을 위해)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)
        
    # 파일명 중복 방지를 위한 UUID 추가
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    file_path = os.path.join(upload_path, unique_filename)
    
    # 파일 포인터를 처음으로 되돌림 (검증 과정에서 읽었을 수 있음)
    file.file.seek(0)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
        
    # 접근 가능한 URL 경로 반환 (실무에서는 도메인 주소를 환경변수에서 가져옴)
    # 여기서는 상대 경로 기반의 URL 반환
    return f"/public/{sub_dir}/{unique_filename}"
