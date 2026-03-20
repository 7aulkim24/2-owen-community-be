#!/usr/bin/env bash
# GitHub OAuth 콜백 엔드포인트 스모크 테스트 (GET만 사용 — curl -I/HEAD는 405)
# 선행: 백엔드 기동, 프로젝트 루트 .env 에 SECRET_KEY 존재
# 사용: ./scripts/oauth_callback_smoke_test.sh
#       BASE_URL=http://127.0.0.1:8000 ./scripts/oauth_callback_smoke_test.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$BE_DIR/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
CALLBACK="${BASE_URL}/v1/integrations/github/callback"
ROOT_ENV="${ROOT_DIR}/.env"

if [[ ! -f "$ROOT_ENV" ]]; then
  echo "❌ 루트 .env 없음: $ROOT_ENV"
  exit 1
fi

PYTHON="python3"
if [[ -x "/opt/anaconda3/envs/community/bin/python3" ]]; then
  PYTHON="/opt/anaconda3/envs/community/bin/python3"
fi

STATE_ENC="$(ENV_FILE="$ROOT_ENV" "$PYTHON" << 'PY'
import base64
import hashlib
import hmac
import os
import re
import secrets
import time
from pathlib import Path
from urllib.parse import quote

path = Path(os.environ["ENV_FILE"])


def parse_env(p: Path) -> dict:
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if not m:
            continue
        k, raw = m.group(1), m.group(2).strip()
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            raw = raw[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        out[k] = raw
    return out


env = parse_env(path)
sk = env["SECRET_KEY"]


def encode_state(user_id: str) -> str:
    nonce = secrets.token_urlsafe(12)
    ts = str(int(time.time()))
    payload = f"{user_id}|{ts}|{nonce}"
    sig = hmac.new(sk.encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = base64.urlsafe_b64encode(f"{payload}|{sig}".encode()).decode()
    return raw.rstrip("=")


print(quote(encode_state("01JADMIN000000000000000000"), safe=""))
PY
)"

echo "=== OAuth callback smoke: $CALLBACK ==="
echo ""

check() {
  local name="$1"
  local url="$2"
  local expect_location_substr="$3"
  echo "→ $name"
  loc=$(curl -sS -D - -o /dev/null "$url" | tr -d '\r' | awk -F': ' 'tolower($1)=="location" {print $2; exit}')
  if [[ -z "$loc" ]]; then
    echo "   ❌ Location 헤더 없음"
    return 1
  fi
  if [[ "$loc" != *"$expect_location_substr"* ]]; then
    echo "   ❌ 예상과 다른 Location: $loc"
    return 1
  fi
  echo "   ✅ 302 → ...$expect_location_substr..."
}

check "1) code 없음" "$CALLBACK" "integration.html?error=1"
check "2) error=access_denied" "$CALLBACK?error=access_denied" "integration.html?error=1"
check "3) code만 (state 없음)" "$CALLBACK?code=dummy" "login.html?error=session_expired"
check "4) 잘못된 state" "$CALLBACK?code=dummy&state=invalid" "login.html?error=session_expired"
check "5) 유효 state + 가짜 code" "$CALLBACK?code=fake_code&state=${STATE_ENC}" "integration.html?error=1"

echo ""
echo "✅ OAuth callback 스모크 테스트 완료"
