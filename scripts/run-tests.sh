#!/bin/bash
# ==============================================================================
# 테스트 실행 스크립트 (.env 로드 후 pytest 실행)
# 사용법: ./scripts/run-tests.sh [pytest 인자...]
# 예: ./scripts/run-tests.sh tests/test_db_migrations.py -v
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BE_DIR"

# .env 로드
load_env() {
    local env_file=""
    if [ -f "$BE_DIR/../.env" ]; then
        env_file="$BE_DIR/../.env"
    elif [ -f "$BE_DIR/.env" ]; then
        env_file="$BE_DIR/.env"
    fi

    if [ -n "$env_file" ]; then
        while IFS= read -r line || [ -n "$line" ]; do
            line="${line%$'\r'}"
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]]; then
                key="${BASH_REMATCH[1]}"
                raw_value="${BASH_REMATCH[2]}"
                raw_value="${raw_value#"${raw_value%%[![:space:]]*}"}"
                raw_value="${raw_value%"${raw_value##*[![:space:]]}"}"
                if [[ "$raw_value" =~ ^\"(.*)\"$ ]]; then
                    value="${BASH_REMATCH[1]}"
                elif [[ "$raw_value" =~ ^\'(.*)\'$ ]]; then
                    value="${BASH_REMATCH[1]}"
                else
                    value="${raw_value%%[[:space:]]#*}"
                fi
                export "$key=$value"
            fi
        done < "$env_file"
    fi
}

load_env

# 테스트 DB 기본값 (conftest와 동일)
export DB_HOST="${DB_HOST:-127.0.0.1}"
export DB_PORT="${DB_PORT:-3306}"
export DB_NAME="${DB_NAME:-prooflog_test}"
export DB_USER="${DB_USER:-root}"
export DB_PASSWORD="${DB_PASSWORD:-password}"
export SECRET_KEY="${SECRET_KEY:-test-secret-key}"

# GitHub OAuth (테스트용 기본값)
export GITHUB_CLIENT_ID="${GITHUB_CLIENT_ID:-test-client-id}"
export GITHUB_CLIENT_SECRET="${GITHUB_CLIENT_SECRET:-test-secret}"
export GITHUB_CALLBACK_URL="${GITHUB_CALLBACK_URL:-http://localhost:8000/v1/integrations/github/callback}"
export TOKEN_ENCRYPT_KEY="${TOKEN_ENCRYPT_KEY:-dGVzdC1rZXktMzItYnl0ZXMtbG9uZy1lbm91Z2g=}"

python -m pytest "$@"
