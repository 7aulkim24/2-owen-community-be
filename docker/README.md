# Docker Deploy Guide

이 디렉토리는 현재 운영 기준 배포 자산의 단일 기준 경로입니다.

## 구성

- `Dockerfile.fe`, `Dockerfile.be`, `Dockerfile.db`
- `docker-compose.yml`
- `scripts/build-and-push.sh`
- `scripts/deploy-on-ec2.sh`
- `scripts/update-duckdns.sh`
- `scripts/install-duckdns-refresh.sh`
- `systemd/community-duckdns-refresh.service`
- `systemd/community-duckdns-refresh.timer`

프론트 저장소와 루트 디렉토리의 중복 `docker/` 자산은 제거했고, 이제 이 디렉토리만 유지합니다.

## 로컬 통합 실행

```bash
cd /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be/docker
cp .env.example .env
docker compose --env-file .env -f docker-compose.local.yml up --build -d
```

검증:

```bash
curl -i http://localhost/health
curl -i http://localhost/api/health
/Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be/scripts/qa-smoke.sh http://localhost/api
/Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-fe/scripts/qa-smoke.sh http://localhost
```

종료:

```bash
docker compose -f docker-compose.local.yml down
```

## 이미지 빌드 및 푸시

백엔드 저장소 기준으로 실행:

```bash
cd /Users/eskim00/Documents/Programming/KDT_AWS/Assignment
PROJECT_ROOT="$(pwd)" \
DOCKERHUB_NAMESPACE=<dockerhub-id> \
IMAGE_TAG=<tag> \
./2-owen-community-be/docker/scripts/build-and-push.sh
```

옵션:

- `PUSH_LATEST=true`
- `EXTRA_TAG=v1.0.0`
- `TARGET_PLATFORM=linux/amd64`

## EC2 배포

EC2 기준 디렉토리는 `/home/ubuntu/community`입니다.

최초 준비:

```bash
mkdir -p /home/ubuntu/community/scripts
cd /home/ubuntu/community
```

백엔드 저장소의 배포 자산 업로드:

```bash
scp -i /path/to/key.pem /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be/docker/docker-compose.yml ubuntu@<ec2-host>:/home/ubuntu/community/
scp -i /path/to/key.pem /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be/docker/scripts/*.sh ubuntu@<ec2-host>:/home/ubuntu/community/scripts/
scp -i /path/to/key.pem /Users/eskim00/Documents/Programming/KDT_AWS/Assignment/2-owen-community-be/docker/.env.example ubuntu@<ec2-host>:/home/ubuntu/community/
```

수동 재배포:

```bash
cd /home/ubuntu/community
IMAGE_TAG=<tag> DOCKERHUB_NAMESPACE=<dockerhub-id> ./scripts/deploy-on-ec2.sh
```

직접 compose 실행:

```bash
cd /home/ubuntu/community
docker compose --env-file .env -f docker-compose.yml pull
docker compose --env-file .env -f docker-compose.yml up -d
```

## 자동 배포

현재 GitHub Actions 구성:

- 백엔드 저장소: `.github/workflows/ci.yml`
- 백엔드 저장소: `.github/workflows/cd.yml`
- 프론트 저장소: `.github/workflows/ci.yml`
- 프론트 저장소: `.github/workflows/trigger-backend-cd.yml`

동작:

1. 프론트 저장소 CI 성공
2. 프론트 저장소가 백엔드 저장소로 `repository_dispatch` 전송
3. 백엔드 저장소 CD가 FE/BE를 checkout
4. FE/BE/DB 이미지를 Docker Hub에 push
5. EC2로 배포 자산 업로드
6. EC2에서 `deploy-on-ec2.sh` 실행
7. `update-duckdns.sh` 실행 후 `docker compose pull && up -d`
8. `http://localhost/api/health`, `http://localhost/posts.html` 검증

## DuckDNS 자동 갱신

이 단계는 사용자가 직접 실행합니다.

```bash
cd /home/ubuntu/community
chmod +x scripts/update-duckdns.sh scripts/install-duckdns-refresh.sh
sudo ./scripts/install-duckdns-refresh.sh /home/ubuntu/community
sudo systemctl start community-duckdns-refresh.service
sudo systemctl start community-duckdns-refresh.timer
```

상태 확인:

```bash
sudo systemctl status community-duckdns-refresh.service --no-pager
sudo systemctl status community-duckdns-refresh.timer --no-pager
journalctl -u community-duckdns-refresh.service -n 50 --no-pager
```

## 관련 문서

- `DEPLOY_RUNBOOK.md`
- `MANUAL_STEPS.md`
- `SECRETS_REFERENCE.md`
- `ROLLBACK.md`
