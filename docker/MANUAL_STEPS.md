# Manual Steps

Codex가 자동으로 처리하지 못하는 작업만 정리했습니다. 이미 끝낸 단계는 건너뛰고, 아직 남은 단계만 수행하면 됩니다.

## 1. DuckDNS 생성

- [DuckDNS](https://www.duckdns.org) 로그인
- 원하는 서브도메인 생성
- `token` 복사
- `.env`에 `DUCKDNS_DOMAIN`, `DUCKDNS_TOKEN` 반영

## 2. Docker Hub 준비

- Docker Hub 로그인
- `community-fe`, `community-be`, `community-db` 저장소 생성
- Personal Access Token 생성

## 3. EC2 생성

- AWS Console > `EC2` > `Instances` > `Launch instances`
- Ubuntu 24.04 LTS
- `t3.small`
- `gp3 30GiB`
- Security Group:
  - `22/tcp` from `My IP`
  - `80/tcp` from `Anywhere`

## 4. GitHub Secrets / Variables 등록

- BE 저장소:
  - Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `EC2_ENV_FILE_B64`, `FE_REPO_PAT`
  - Variables: `DOCKERHUB_NAMESPACE`, `EC2_DEPLOY_DIR`, `FE_REPO_OWNER`, `FE_REPO_NAME`, `FE_REPO_REF`
- FE 저장소:
  - Secrets: `BE_REPO_DISPATCH_TOKEN`
  - Variables: `BE_REPO_OWNER`, `BE_REPO_NAME`

## 5. EC2 초기 설정

- `/home/ubuntu/community` 생성
- `.env` 작성
- `chmod 600 .env`

## 6. DuckDNS 자동 갱신 구성

이 단계는 사용자가 직접 실행해야 합니다.

```bash
cd /home/ubuntu/community
chmod +x scripts/update-duckdns.sh scripts/install-duckdns-refresh.sh
sudo ./scripts/install-duckdns-refresh.sh /home/ubuntu/community
sudo systemctl start community-duckdns-refresh.service
sudo systemctl start community-duckdns-refresh.timer
```

확인:

```bash
sudo systemctl status community-duckdns-refresh.service --no-pager
sudo systemctl status community-duckdns-refresh.timer --no-pager
journalctl -u community-duckdns-refresh.service -n 50 --no-pager
```
