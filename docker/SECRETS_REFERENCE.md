# Secrets Reference

## Backend Repository Secrets

- `DOCKERHUB_USERNAME`: Docker Hub 계정명
- `DOCKERHUB_TOKEN`: Docker Hub access token
- `EC2_HOST`: EC2 공인 IP
- `EC2_USER`: EC2 로그인 계정명, Ubuntu면 `ubuntu`
- `EC2_SSH_KEY`: `.pem` 파일 전체 내용
- `EC2_ENV_FILE_B64`: 운영 `.env` 파일 base64 문자열
- `FE_REPO_PAT`: 백엔드 저장소 CD가 프론트 저장소를 checkout할 때 사용할 PAT

## Backend Repository Variables

- `DOCKERHUB_NAMESPACE`: Docker Hub namespace
- `EC2_DEPLOY_DIR`: `/home/ubuntu/community`
- `FE_REPO_OWNER`: 프론트 저장소 owner
- `FE_REPO_NAME`: 프론트 저장소 이름
- `FE_REPO_REF`: 프론트 checkout branch, 기본 `main`

주의:

- `DOCKERHUB_NAMESPACE`, `EC2_DEPLOY_DIR`는 `Repository variables`
- 나머지 민감 값은 `Repository secrets`

## Frontend Repository Secrets

- `BE_REPO_DISPATCH_TOKEN`: 백엔드 저장소 repository dispatch 호출용 PAT

## Frontend Repository Variables

- `BE_REPO_OWNER`: 백엔드 저장소 owner
- `BE_REPO_NAME`: 백엔드 저장소 이름
