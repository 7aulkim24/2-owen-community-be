# Single EC2 Docker Deploy Runbook

이 문서는 `2-owen-community-be` 저장소를 배포 오너로 사용하는 현재 기준 런북입니다.

## 아키텍처

- EC2 1대에서 `frontend`, `backend`, `db` 3개 컨테이너를 `docker compose`로 구동
- 프론트 저장소는 CI만 수행
- 백엔드 저장소가 FE/BE/DB 이미지를 빌드하고 EC2에 배포
- 외부 접속 주소는 `http://<duckdns-subdomain>.duckdns.org`
- 배포 기준 디렉토리는 `/home/ubuntu/community`

## 사전 조건

- EC2에 Docker Engine, Docker Compose plugin, git 설치 완료
- EC2 경로 `/home/ubuntu/community` 생성 완료
- 운영용 `.env` 작성 완료
- GitHub Secrets/Variables 등록 완료
- DuckDNS 도메인과 토큰 발급 완료

## 첫 배포 전 점검

```bash
cd /home/ubuntu/community
ls -la
test -f .env
docker --version
docker compose version
```

## 자동 배포 흐름

1. 프론트 저장소 `Frontend CI` 성공
2. 프론트 저장소 `Trigger Backend CD`가 백엔드 저장소에 repository dispatch 전송
3. 백엔드 저장소 `Backend CD`가 FE/BE 저장소를 checkout
4. FE/BE/DB 이미지를 Docker Hub에 push
5. 백엔드 저장소의 `docker/` 배포 자산을 EC2로 업로드
6. EC2에서 `scripts/deploy-on-ec2.sh` 실행
7. `update-duckdns.sh` 실행
8. `docker compose pull && up -d`
9. `http://localhost/api/health`, `http://localhost/posts.html` 검증

## 수동 재배포

```bash
cd /home/ubuntu/community
IMAGE_TAG=<tag> DOCKERHUB_NAMESPACE=<dockerhub-id> ./scripts/deploy-on-ec2.sh
```

## 배포 후 확인

```bash
cd /home/ubuntu/community
docker compose ps
curl -i http://localhost/api/health
curl -i http://localhost/posts.html
```
