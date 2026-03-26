# Prooflog 백엔드

FastAPI 기반 커뮤니티/자동 기록 백엔드입니다.  
현재는 게시글·댓글·사용자 관리에 더해 GitHub 연동, 활동 수집, 초안/요약 흐름까지 포함하는 방향으로 확장 중입니다.

## 현재 범위

- 세션 기반 회원 인증/로그아웃
- 게시글/댓글/좋아요/프로필 API
- 이미지 업로드 및 정적 파일 서빙 (`/public`)
- GitHub OAuth 연동, 활동 수집, 요약/초안 관련 도메인
- Request ID, 접근 로그, 표준 에러 응답, 백그라운드 동기화 스케줄러

## 구조

- `routers/`: HTTP 엔드포인트
- `services/`: 비즈니스 로직
- `models/`: Raw SQL 기반 DB 접근
- `schemas/`: Pydantic 요청/응답 스키마
- `utils/`: 인증, 세션, 로깅, 에러, DB, 외부 연동 유틸
- `db/`: 스키마, 시드, 마이그레이션
- `tests/`: pytest 기반 테스트

## 기술 스택

- FastAPI
- Pydantic v2
- MySQL + aiomysql
- DB 세션 미들웨어 + HttpOnly 쿠키
- ULID

## 실행

1. `.env.example`을 복사해 `.env`를 만듭니다.
2. MySQL을 실행하고 `db/schema.sql`을 적용합니다.
3. `pip install -e .`
4. `uvicorn main:app --reload`
5. `http://localhost:8000/docs` 에서 Swagger UI를 확인합니다.

테스트는 `./scripts/run-tests.sh`로 실행할 수 있습니다.

## 핵심 환경 변수

- 필수: `SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- 연동 기능 사용 시 추가: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `TOKEN_ENCRYPT_KEY`
- 선택: `DB_PORT`, `ALLOWED_ORIGINS`, `FRONTEND_URL`, `GITHUB_CALLBACK_URL`, `DEBUG`

## 인증/인가 원칙

- 웹 인증은 DB 세션 기반으로 유지합니다.
- 외부 OAuth 토큰은 웹 로그인 세션과 분리해 저장합니다.
- 인가는 owner check 중심으로 유지하고, 역할 체계는 실제 필요가 생길 때 확장합니다.

## 방향

관련 기획 문서:

- `docs/pl-plan/커뮤니티 서비스 발전 종합 기획안.md`
- `docs/pl-plan/개발 로드맵.md`

현재 백엔드는 위 문서 기준으로 다음 흐름을 지원하는 방향으로 정리되고 있습니다.

- Phase 0: 확장 가능한 코드베이스 정비
- Phase 1: GitHub 기반 Auto Log MVP
- Phase 2 이후: 다중 소스 수집, 회고, 포트폴리오 연결
