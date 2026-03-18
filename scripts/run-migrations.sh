#!/bin/bash
# ==============================================================================
# Phase 1 마이그레이션 실행 스크립트
# 사용법: ./scripts/run-migrations.sh
#   - 2-owen-community-be 디렉터리에서 실행하거나, 프로젝트 루트에서 실행
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BE_DIR"

# .env 로드 (프로젝트 루트 또는 백엔드 디렉터리)
load_env() {
    local env_file=""
    if [ -f "$BE_DIR/../.env" ]; then
        env_file="$BE_DIR/../.env"
    elif [ -f "$BE_DIR/.env" ]; then
        env_file="$BE_DIR/.env"
    else
        echo "⚠️  .env 파일을 찾을 수 없습니다. DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME을 수동으로 설정하세요."
        return 1
    fi

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
}

load_env

export DB_HOST="${DB_HOST:-127.0.0.1}"
export DB_PORT="${DB_PORT:-3306}"

if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "❌ .env에 DB_USER, DB_NAME이 필요합니다."
    exit 1
fi

echo "📦 마이그레이션 실행 중 (host=$DB_HOST port=$DB_PORT db=$DB_NAME)..."

for f in db/migrations/003_add_connected_accounts.sql \
         db/migrations/004_add_activity_tables.sql \
         db/migrations/005_add_activity_summaries.sql; do
    if [ -f "$f" ]; then
        echo "  → $f"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" "-p$DB_PASSWORD" "$DB_NAME" < "$f"
    fi
done

echo "✅ 마이그레이션 완료"
