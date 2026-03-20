import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

# 테스트 컬렉션/임포트 단계에서 Settings 검증이 터지지 않도록 기본 env 제공
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "password")
os.environ.setdefault("DB_NAME", "prooflog_test")
# GitHub OAuth / 토큰 암호화 — 테스트·임포트 시 Settings 검증 통과용 (실제 호출 없음)
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-client-secret")
os.environ.setdefault(
    "TOKEN_ENCRYPT_KEY",
    "sneykqErN0KOArVsMTlsCO8tBxOkfuFOZ2qvNWWwZP0=",
)
# TestClient 기동 시 무한 스케줄 루프 방지 (main.py startup)
os.environ.setdefault("DISABLE_SYNC_SCHEDULER", "1")

def _find_app_root(start_dir: Path) -> Path:
    """
    tests 디렉토리 위치가 바뀌어도 동작하도록,
    main.py 와 models/ 가 존재하는 '앱 루트'를 자동으로 찾는다.
    """
    candidates: list[Path] = []
    for parent in [start_dir, *start_dir.parents]:
        candidates.append(parent)
        candidates.append(parent / "2-owen-community-be")

    for cand in candidates:
        if (cand / "main.py").is_file() and (cand / "models").is_dir():
            return cand.resolve()

    raise RuntimeError(
        f"앱 루트를 찾을 수 없습니다. start_dir={start_dir}. "
        "main.py 와 models/ 가 있는 디렉토리(예: 2-owen-community-be)를 확인해주세요."
    )


# tests 실행 시 앱 루트를 import path에 포함
APP_ROOT = _find_app_root(Path(__file__).resolve().parent)
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# 각 테스트별 API 호출 로그를 저장할 전역 변수
test_call_logs = {}


@pytest.fixture
def api_client(request):
    """API 호출 입출력을 기록하는 래퍼 클라이언트 피스처"""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    nodeid = request.node.nodeid
    test_call_logs[nodeid] = []

    def log_call(method, url, request_data, response):
        try:
            resp_json = response.json()
        except Exception:
            resp_json = response.text

        test_call_logs[nodeid].append(
            {
                "method": method,
                "url": str(url),
                "input": request_data,
                "output": {"status_code": response.status_code, "body": resp_json},
            }
        )

    class WrappedClient:
        def __init__(self, inner):
            self.inner = inner

        def post(self, url, **kwargs):
            resp = self.inner.post(url, **kwargs)
            log_call(
                "POST",
                url,
                kwargs.get("json")
                or kwargs.get("data")
                or (
                    f"Files: {list(kwargs.get('files').keys())}"
                    if kwargs.get("files")
                    else None
                ),
                resp,
            )
            return resp

        def get(self, url, **kwargs):
            resp = self.inner.get(url, **kwargs)
            log_call("GET", url, kwargs.get("params"), resp)
            return resp

        def patch(self, url, **kwargs):
            resp = self.inner.patch(url, **kwargs)
            log_call("PATCH", url, kwargs.get("json") or kwargs.get("data"), resp)
            return resp

        def delete(self, url, **kwargs):
            resp = self.inner.delete(url, **kwargs)
            log_call("DELETE", url, None, resp)
            return resp

    with TestClient(app) as client:
        yield WrappedClient(client)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """테스트 실행 결과와 API 호출 로그를 JSON으로 병합 저장"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": terminalreporter._numcollected,
            "passed": len(terminalreporter.stats.get("passed", [])),
            "failed": len(terminalreporter.stats.get("failed", [])),
            "skipped": len(terminalreporter.stats.get("skipped", [])),
            "error": len(terminalreporter.stats.get("error", [])),
        },
        "details": [],
    }

    # 각 테스트별 상세 결과 및 호출 로그 수집
    for status in ["passed", "failed", "skipped", "error"]:
        for report in terminalreporter.stats.get(status, []):
            nodeid = report.nodeid
            results["details"].append(
                {
                    "nodeid": nodeid,
                    "status": status,
                    "duration": getattr(report, "duration", 0),
                    "calls": test_call_logs.get(nodeid, []),
                    "message": str(report.longrepr) if report.longrepr else None,
                }
            )

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n[JSON Log] 상세 리포트가 생성되었습니다: {log_path}")

