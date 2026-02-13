# 커뮤니티 서비스 백엔드 (FastAPI)

FastAPI 기반의 고성능 커뮤니티 백엔드 API입니다. 실무 수준의 운영 안정성과 성능 최적화를 목표로 **Router-Controller-Model-Schema** 아키텍처를 따르며, 최신 백엔드 엔지니어링 패턴이 적용되어 있습니다.

## 주요 기능
- **인증 및 보안**: 회원가입, 세션 기반 로그인/로그아웃, **bcrypt 비밀번호 해싱**, 권한 기반 접근 제어(RBAC)
- **게시글 관리**: CRUD 기능, **다중 이미지 업로드(최대 5장)**, 좋아요 토글
  - **이미지 처리**: 다중 이미지 업로드 지원 및 정적 파일 서빙(`/public`)
  - **데이터 무결성**: 트랜잭션 관리를 통한 데이터 일관성 보장
- **댓글 시스템**: 계층형 댓글 구조 지원을 위한 데이터 모델링 및 CRUD
- **마이페이지**: 프로필 정보 수정, 비밀번호 변경 등 개인정보 관리 API
- **운영 안정성**: **Request ID** 추적 미들웨어 및 **구조화된 JSON 로깅** 시스템

## 기술적 특징 및 최적화
- **아키텍처**: 
  - **Router-Controller-Model-Schema** 계층 분리 아키텍처로 유지보수성 향상
  - Pydantic v2 도입으로 강력한 타입 힌트와 유효성 검사 수행
- **성능 최적화**: 
  - **ULID 도입**: UUID를 대체하여 시간순 정렬 가능하고 인덱스 성능이 우수한 식별자 체계 구축
  - **비동기 처리**: `async/await` 기반의 비동기 I/O 처리로 높은 동시성 지원
- **안정성 및 모니터링**: 
  - **통합 로깅 시스템**: Request ID를 통해 FE-BE-DB 로그를 하나로 연결하여 추적 가능
  - **전역 예외 처리**: 표준화된 에러 응답 포맷(Code-Details)으로 클라이언트와의 통신 규약 확립

## 프로젝트 구조
- **`app/`**: 애플리케이션 핵심 로직
  - `routers/`: API 엔드포인트 정의 (v1)
  - `controllers/`: 비즈니스 로직 및 DTO 변환
  - `models/`: 데이터 접근 및 MySQL DB 연동
  - `schemas/`: Pydantic 기반 Request/Response DTO
- **`utils/`**: 공통 유틸리티
  - `common/`: 공통 응답 및 ID 유틸리티
  - `database/`: MySQL 커넥션 풀 및 쿼리 실행기
  - `middleware/`: 인증, 세션, Request ID 미들웨어
- **`db/`**: SQL 스키마 및 초기 데이터 스크립트
- **`public/`**: 업로드된 이미지 저장소

## 기술 스택
- **Framework**: FastAPI (v0.128.0)
- **Validation**: Pydantic v2
- **Database**: MySQL
- **Security**: bcrypt, Starlette Session
- **ID System**: ULID (python-ulid)

## 시작하기
1. **환경 설정**: `.env` 파일 생성 및 설정 입력
2. **데이터베이스**: MySQL 실행 및 `db/schema.sql` 스크립트로 테이블 생성
3. **설치**: `pip install -e .` 로 의존성 패키지 설치
4. **실행**: `uvicorn main:app --reload` 명령어로 서버 시작
5. **API 문서**: `http://localhost:8000/docs` 에서 Swagger UI 확인

## EC2 배포 요약 (최신)
- 서비스 실행 방식을 `nohup`에서 `systemd`(`community-be.service`)로 전환했습니다.
- 배포 스크립트는 `FRONTEND_ORIGIN` 직접 지정 또는 EC2 태그 조회를 지원합니다.
- CORS는 `ALLOWED_ORIGINS`(쉼표 구분) 기반으로 동작하며 로컬 QA origin을 함께 허용할 수 있습니다.
- 상세 절차는 `docs/DEPLOY_QA.md`를 참고하세요.

---
*AWS AI School 2기 과제물*
