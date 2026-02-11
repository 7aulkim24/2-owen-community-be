#!/bin/bash

# 백엔드 EC2 배포 스크립트
# 사용법: ./scripts/deploy.sh [FRONTEND_EC2_NAME]

set -e

echo "===== 백엔드 EC2 배포 시작 ====="

# 설정
FRONTEND_EC2_NAME="${1:-community-frontend}"
PROJECT_DIR="/home/ec2-user/assignment/2-owen-community-be"
SECRET_KEY="${AWS_SECRET_KEY:-CHANGE_THIS_IN_ENV_VAR}"
DB_PASSWORD="${AWS_DB_PASSWORD:-CHANGE_THIS_IN_ENV_VAR}"

# AWS CLI로 프론트엔드 EC2 IP 가져오기
echo "프론트엔드 EC2 IP를 가져오는 중..."
FRONTEND_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=$FRONTEND_EC2_NAME" \
            "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

if [ "$FRONTEND_IP" = "None" ] || [ -z "$FRONTEND_IP" ]; then
  echo "ERROR: 프론트엔드 EC2 IP를 찾을 수 없습니다."
  echo "EC2 인스턴스에 Name 태그 '$FRONTEND_EC2_NAME'가 설정되어 있는지 확인하세요."
  exit 1
fi

echo "프론트엔드 IP: $FRONTEND_IP"
FRONTEND_URL="http://$FRONTEND_IP"

# .env.production 생성
echo ".env.production 파일 생성 중..."
cd "$PROJECT_DIR"
sed -e "s|{{SECRET_KEY}}|$SECRET_KEY|g" \
    -e "s|{{DB_PASSWORD}}|$DB_PASSWORD|g" \
    -e "s|{{FRONTEND_URL}}|$FRONTEND_URL|g" \
    .env.production.template > .env.production

echo ".env.production 파일이 생성되었습니다."

# Python 의존성 설치 (가상환경)
if [ ! -d "venv" ]; then
  echo "Python 가상환경 생성 중..."
  python3 -m venv venv
fi

source venv/bin/activate
echo "Python 패키지 설치 중..."
pip install -e . -q

# 기존 백엔드 프로세스 종료
echo "기존 백엔드 프로세스 종료 중..."
pkill -f "uvicorn main:app" || true

# 백엔드 서버 시작
echo "백엔드 서버 시작 중..."
nohup uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --env-file .env.production \
  > backend.log 2>&1 &

echo "백엔드 서버가 백그라운드로 시작되었습니다."
echo "로그 확인: tail -f $PROJECT_DIR/backend.log"
echo ""
echo "===== 백엔드 배포 완료 ====="
echo "Health Check: curl http://localhost:8000/health"
