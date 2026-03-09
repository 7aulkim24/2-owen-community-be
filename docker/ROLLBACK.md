# Rollback

## 수동 롤백

이전 이미지 태그를 알고 있을 때:

```bash
cd /home/ubuntu/community
IMAGE_TAG=<previous-tag> DOCKERHUB_NAMESPACE=<dockerhub-id> ./scripts/deploy-on-ec2.sh
```

## GitHub Actions에서 롤백

- 백엔드 저장소 > `Actions`
- `Backend CD`
- `Run workflow`
- `image_tag`에 이전 태그 입력
- 실행 후 `deploy` job 성공 여부 확인

태그 형식 기본값:

- `r<run-number>-<short-sha>`

## 롤백 후 확인

```bash
cd /home/ubuntu/community
docker compose ps
curl -i http://localhost/api/health
curl -i http://localhost/posts.html
```
