#!/bin/bash

# 백엔드 EC2 배포 스크립트
# 사용법:
#   FRONTEND_ORIGIN=http://3.36.120.10 AWS_SECRET_KEY=... AWS_DB_PASSWORD=... ./scripts/deploy.sh
#   AWS_SECRET_KEY=... AWS_DB_PASSWORD=... ./scripts/deploy.sh community-frontend

set -euo pipefail

echo "===== 백엔드 EC2 배포 시작 ====="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_EC2_NAME="${1:-${FRONTEND_EC2_NAME:-community-frontend}}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-}"
AWS_IP_FIELD="${AWS_IP_FIELD:-PublicIpAddress}"
SECRET_KEY="${AWS_SECRET_KEY:-}"
DB_PASSWORD="${AWS_DB_PASSWORD:-}"
APP_USER="${APP_USER:-$(whoami)}"
SERVICE_TEMPLATE_PATH="$PROJECT_DIR/deploy/community-be.service"
SERVICE_NAME="${SERVICE_NAME:-community-be.service}"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: '$1' 명령어가 필요합니다."
    exit 1
  fi
}

require_command python3
require_command sed
require_command systemctl

if [ -z "$SECRET_KEY" ]; then
  echo "ERROR: AWS_SECRET_KEY 환경변수를 설정하세요."
  exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
  echo "ERROR: AWS_DB_PASSWORD 환경변수를 설정하세요."
  exit 1
fi

if [ -z "$FRONTEND_ORIGIN" ]; then
  if command -v aws >/dev/null 2>&1; then
    echo "FRONTEND_ORIGIN 미설정: AWS CLI로 인스턴스 '$FRONTEND_EC2_NAME' 조회 중..."
    frontend_ip=$(aws ec2 describe-instances \
      --filters "Name=tag:Name,Values=$FRONTEND_EC2_NAME" "Name=instance-state-name,Values=running" \
      --query "Reservations[0].Instances[0].$AWS_IP_FIELD" \
      --output text 2>/dev/null || true)
    if [ -n "$frontend_ip" ] && [ "$frontend_ip" != "None" ]; then
      FRONTEND_ORIGIN="http://$frontend_ip"
    fi
  fi
fi

if [ -z "$FRONTEND_ORIGIN" ]; then
  echo "ERROR: FRONTEND_ORIGIN을 확인할 수 없습니다."
  echo "예시: FRONTEND_ORIGIN=http://3.36.120.10 ./scripts/deploy.sh"
  exit 1
fi

ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-$FRONTEND_ORIGIN,http://localhost:5500,http://127.0.0.1:5500}"

echo "프론트엔드 Origin: $FRONTEND_ORIGIN"
echo "CORS 허용 목록: $ALLOWED_ORIGINS"
echo "프로젝트 디렉토리: $PROJECT_DIR"

cd "$PROJECT_DIR"

echo ".env.production 생성 중..."
sed \
  -e "s|{{SECRET_KEY}}|$SECRET_KEY|g" \
  -e "s|{{DB_PASSWORD}}|$DB_PASSWORD|g" \
  -e "s|{{ALLOWED_ORIGINS}}|$ALLOWED_ORIGINS|g" \
  .env.production.template > .env.production
echo "✓ .env.production 생성 완료"

if [ ! -d venv ]; then
  echo "가상환경 생성..."
  python3 -m venv venv
fi

echo "Python 의존성 설치..."
source venv/bin/activate
pip install -e . -q
deactivate

if [ ! -f "$SERVICE_TEMPLATE_PATH" ]; then
  echo "ERROR: 서비스 템플릿이 없습니다: $SERVICE_TEMPLATE_PATH"
  exit 1
fi

echo "systemd 서비스 파일 배포: $SERVICE_PATH"
tmp_service_file="$(mktemp)"
sed \
  -e "s|__APP_USER__|$APP_USER|g" \
  -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  "$SERVICE_TEMPLATE_PATH" > "$tmp_service_file"
sudo cp "$tmp_service_file" "$SERVICE_PATH"
rm -f "$tmp_service_file"

echo "systemd 데몬 리로드 및 서비스 재시작..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager -l | head -n 20

echo ""
echo "===== 백엔드 배포 완료 ====="
echo "Health Check: curl http://localhost:8000/health"
