# 백엔드 EC2 배포 및 QA 가이드

## 1. 사전 준비
- Python 3.10 이상
- `systemd` 사용 가능 환경
- MySQL이 백엔드 EC2 내부에서 실행 중
- 보안그룹: 백엔드 `8000` 포트는 프론트/관리자 대역만 허용

## 2. 필수 환경변수
```bash
export AWS_SECRET_KEY='강력한_시크릿_키'
export AWS_DB_PASSWORD='DB_비밀번호'
export FRONTEND_ORIGIN='http://<프론트엔드_EC2_퍼블릭_IP>'
```

선택 환경변수:
```bash
export ALLOWED_ORIGINS='http://<프론트_IP>,http://localhost:5500,http://127.0.0.1:5500'
export APP_USER='ec2-user'
export SERVICE_NAME='community-be.service'
```

## 3. 배포 실행
```bash
cd /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be
./scripts/deploy.sh
```

## 4. 서비스 점검
```bash
sudo systemctl status community-be.service --no-pager -l
journalctl -u community-be.service -n 100 --no-pager
curl -i http://localhost:8000/health
```

## 5. 스모크 QA
```bash
cd /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be
./scripts/qa-smoke.sh http://localhost:8000
```

검증 항목:
- 헬스체크
- 회원가입/로그인/로그아웃
- 게시글 CRUD(생성/수정/삭제)
- 댓글 CRUD(생성/삭제)

## 6. 트러블슈팅
- `ERROR: AWS_SECRET_KEY ...`: 필수 환경변수가 누락된 상태입니다.
- `community-be.service` 실패: `backend.log`, `journalctl -u community-be.service` 로그 확인.
- DB 연결 실패: `.env.production`의 DB 설정과 MySQL 상태 확인.
