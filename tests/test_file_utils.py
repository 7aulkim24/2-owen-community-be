import io

import pytest
from fastapi import UploadFile

from utils.common.file_utils import MAX_FILE_SIZE, save_upload_file
from utils.errors.error_codes import ErrorCode
from utils.errors.exceptions import APIError


def _make_upload(filename: str, payload: bytes, size=None) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(payload), size=size)


def test_blocks_oversized_upload_even_when_size_metadata_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = _make_upload("too-large.jpg", b"a" * (MAX_FILE_SIZE + 1), size=None)

    with pytest.raises(APIError) as exc:
        save_upload_file(upload, "post")

    assert exc.value.code == ErrorCode.PAYLOAD_TOO_LARGE
    created_files = list((tmp_path / "public" / "image" / "post").glob("*"))
    assert created_files == []


def test_accepts_small_upload_when_size_metadata_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = _make_upload("ok.jpg", b"a" * 1024, size=None)

    saved_url = save_upload_file(upload, "profile")

    assert saved_url.startswith("/public/image/profile/")
    created_files = list((tmp_path / "public" / "image" / "profile").glob("*"))
    assert len(created_files) == 1


def test_blocks_unknown_domain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = _make_upload("ok.jpg", b"a" * 1024, size=1024)

    with pytest.raises(APIError) as exc:
        save_upload_file(upload, "admin")

    assert exc.value.code == ErrorCode.BAD_REQUEST
