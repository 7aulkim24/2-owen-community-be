import pytest

from tests.helpers.db_seed import seed_database


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 데이터베이스 초기화
    seed_database()
    yield


# --- Auth API Tests ---


def test_signup_success(api_client):
    """회원가입 성공 케이스"""
    response = api_client.post(
        "/v1/auth/signup",
        json={"email": "test@example.com", "password": "Password123!", "nickname": "tester"},
    )
    assert response.status_code == 201
    assert response.json()["code"] == "CREATED"
    assert response.json()["data"]["email"] == "test@example.com"


def test_signup_failure_invalid_input(api_client):
    """회원가입 실패: 유효하지 않은 입력"""
    response = api_client.post(
        "/v1/auth/signup",
        json={"email": "invalid-email", "password": "short", "nickname": ""},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_INPUT"
    details = response.json()["details"]
    assert "email" in details
    assert "password" in details
    assert "nickname" in details


def test_signup_failure_duplicate(api_client):
    """회원가입 실패: 이메일 또는 닉네임 중복"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "dup@example.com", "password": "Password123!", "nickname": "user1"},
    )

    # 이메일 중복
    response = api_client.post(
        "/v1/auth/signup",
        json={"email": "dup@example.com", "password": "Password123!", "nickname": "user2"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_EXISTS"
    assert response.json()["details"]["field"] == "email"

    # 닉네임 중복
    response = api_client.post(
        "/v1/auth/signup",
        json={"email": "other@example.com", "password": "Password123!", "nickname": "user1"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_EXISTS"
    assert response.json()["details"]["field"] == "nickname"


def test_login_lifecycle(api_client):
    """로그인, 내 정보 조회, 로그아웃 라이프사이클"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "login@example.com", "password": "Password123!", "nickname": "tester"},
    )

    # 로그인 성공
    resp = api_client.post(
        "/v1/auth/login", json={"email": "login@example.com", "password": "Password123!"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["nickname"] == "tester"

    # 내 정보 조회 성공
    resp = api_client.get("/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "login@example.com"

    # 로그아웃
    resp = api_client.post("/v1/auth/logout")
    assert resp.status_code == 200

    # 로그아웃 후 내 정보 조회 실패
    resp = api_client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_login_failure(api_client):
    """로그인 실패 케이스"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "fail@example.com", "password": "Password123!", "nickname": "tester"},
    )

    # 잘못된 비밀번호
    resp = api_client.post(
        "/v1/auth/login", json={"email": "fail@example.com", "password": "wrongpassword"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"

    # 존재하지 않는 이메일
    resp = api_client.post(
        "/v1/auth/login", json={"email": "none@example.com", "password": "Password123!"}
    )
    assert resp.status_code == 401


# --- User API Tests ---


def test_user_update_success(api_client):
    """사용자 정보 수정 및 비밀번호 변경 성공"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "update@test.com", "password": "Password123!", "nickname": "oldNick"},
    )
    api_client.post("/v1/auth/login", json={"email": "update@test.com", "password": "Password123!"})

    # 닉네임 수정
    resp = api_client.patch("/v1/users/me", json={"nickname": "newNick"})
    assert resp.status_code == 200
    assert resp.json()["data"]["nickname"] == "newNick"

    # 비밀번호 변경
    resp = api_client.patch("/v1/users/password", json={"password": "newPassword123!"})
    assert resp.status_code == 200

    # 새 비밀번호로 로그인 확인
    api_client.post("/v1/auth/logout")
    resp = api_client.post(
        "/v1/auth/login", json={"email": "update@test.com", "password": "newPassword123!"}
    )
    assert resp.status_code == 200


def test_user_delete_success(api_client):
    """회원 탈퇴 성공"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "del@test.com", "password": "Password123!", "nickname": "deleted"},
    )
    api_client.post("/v1/auth/login", json={"email": "del@test.com", "password": "Password123!"})

    # 탈퇴
    resp = api_client.delete("/v1/users/me")
    assert resp.status_code == 200

    # 탈퇴 후 로그인 불가 확인
    resp = api_client.post(
        "/v1/auth/login", json={"email": "del@test.com", "password": "Password123!"}
    )
    assert resp.status_code == 401


# --- Post API Tests ---


def test_post_list_pagination(api_client):
    """게시글 목록 조회 및 페이징 기능 검증 (인피니티 스크롤 대응)"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "list@t.com", "password": "Password123!", "nickname": "lister"},
    )
    api_client.post("/v1/auth/login", json={"email": "list@t.com", "password": "Password123!"})

    # 여러 게시글 생성 (페이징 테스트용)
    post_ids = []
    for i in range(5):
        resp = api_client.post(
            "/v1/posts", json={"title": f"Test Title {i + 1}", "content": f"Test Content {i + 1}"}
        )
        assert resp.status_code == 201
        post_ids.append(resp.json()["data"]["postId"])

    # 기본 목록 조회 (limit=10, offset=0)
    resp = api_client.get("/v1/posts")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 5  # 생성한 5개 게시글 모두 조회
    assert data["pagination"]["totalCount"] == 5
    assert data["pagination"]["offset"] == 0
    assert data["pagination"]["limit"] == 10

    # 페이징 테스트 (limit=2, offset=0)
    resp = api_client.get("/v1/posts?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    assert data["pagination"]["totalCount"] == 5
    assert data["pagination"]["offset"] == 0
    assert data["pagination"]["limit"] == 2

    # 다음 페이지 조회 (limit=2, offset=2)
    resp = api_client.get("/v1/posts?limit=2&offset=2")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["items"]) == 2
    assert data["pagination"]["totalCount"] == 5
    assert data["pagination"]["offset"] == 2
    assert data["pagination"]["limit"] == 2


def test_post_full_lifecycle(api_client):
    """게시글 생성, 조회, 수정, 좋아요, 삭제 전체 흐름"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "p@t.com", "password": "Password123!", "nickname": "writer"},
    )
    api_client.post("/v1/auth/login", json={"email": "p@t.com", "password": "Password123!"})

    # 1. 생성
    resp = api_client.post("/v1/posts", json={"title": "Test Title", "content": "Test Content"})
    assert resp.status_code == 201
    post_id = resp.json()["data"]["postId"]

    # 2. 상세 조회 및 조회수 증가 확인
    resp = api_client.get(f"/v1/posts/{post_id}")
    assert resp.json()["data"]["hits"] == 1

    # 3. 좋아요 토글 (캐시된 카운트 확인)
    resp = api_client.post(f"/v1/posts/{post_id}/likes")
    assert resp.json()["data"]["likeCount"] == 1

    # 다시 토글해서 취소
    resp = api_client.post(f"/v1/posts/{post_id}/likes")
    assert resp.json()["data"]["likeCount"] == 0

    # 4. 수정
    resp = api_client.patch(
        f"/v1/posts/{post_id}", json={"title": "Updated Title", "content": "Updated Content"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated Title"

    # 5. 권한 없는 수정 시도
    api_client.post(
        "/v1/auth/signup",
        json={"email": "h@t.com", "password": "Password123!", "nickname": "hacker"},
    )
    api_client.post("/v1/auth/login", json={"email": "h@t.com", "password": "Password123!"})
    resp = api_client.patch(f"/v1/posts/{post_id}", json={"title": "Hacked", "content": "Hacked Content"})
    assert resp.status_code == 403

    # 6. 삭제
    api_client.post("/v1/auth/login", json={"email": "p@t.com", "password": "Password123!"})
    resp = api_client.delete(f"/v1/posts/{post_id}")
    assert resp.status_code == 200

    # 삭제 후 조회 실패 확인
    resp = api_client.get(f"/v1/posts/{post_id}")
    assert resp.status_code == 404


# --- Comment API Tests ---


def test_comment_list(api_client):
    """댓글 목록 조회 기능 검증"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "commentlist@t.com", "password": "Password123!", "nickname": "commenter"},
    )
    api_client.post(
        "/v1/auth/login", json={"email": "commentlist@t.com", "password": "Password123!"}
    )

    # 게시글 생성
    post_resp = api_client.post("/v1/posts", json={"title": "Post for Comments", "content": "Content"})
    post_id = post_resp.json()["data"]["postId"]

    # 여러 댓글 생성
    for i in range(3):
        resp = api_client.post(
            f"/v1/posts/{post_id}/comments", json={"content": f"Comment {i + 1}"}
        )
        assert resp.status_code == 201

    # 댓글 목록 조회
    resp = api_client.get(f"/v1/posts/{post_id}/comments")
    assert resp.status_code == 200
    comments = resp.json()["data"]
    assert len(comments) == 3  # 생성한 3개 댓글 모두 조회

    # 각 댓글이 올바르게 표시되는지 확인 (최신순 정렬이므로 역순)
    for i, comment in enumerate(comments):
        assert comment["content"] == f"Comment {3 - i}"
        assert comment["author"]["nickname"] == "commenter"


def test_comment_lifecycle_and_cache(api_client):
    """댓글 작성, 수정, 삭제 및 게시글 내 캐시 카운트 검증"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "c@t.com", "password": "Password123!", "nickname": "comm"},
    )
    api_client.post("/v1/auth/login", json={"email": "c@t.com", "password": "Password123!"})

    # 게시글 생성
    post_resp = api_client.post("/v1/posts", json={"title": "Post", "content": "Content"})
    post_id = post_resp.json()["data"]["postId"]

    # 1. 댓글 작성
    resp = api_client.post(f"/v1/posts/{post_id}/comments", json={"content": "First Comment"})
    assert resp.status_code == 201
    comment_id = resp.json()["data"]["commentId"]

    # 게시글 조회 시 commentCount가 1인지 확인 (최적화 기능 검증)
    post_resp = api_client.get(f"/v1/posts/{post_id}")
    assert post_resp.json()["data"]["commentCount"] == 1

    # 2. 댓글 수정
    resp = api_client.patch(
        f"/v1/posts/{post_id}/comments/{comment_id}", json={"content": "Updated Comment"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["content"] == "Updated Comment"

    # 3. 댓글 삭제
    resp = api_client.delete(f"/v1/posts/{post_id}/comments/{comment_id}")
    assert resp.status_code == 200

    # 게시글 조회 시 commentCount가 0인지 확인
    post_resp = api_client.get(f"/v1/posts/{post_id}")
    assert post_resp.json()["data"]["commentCount"] == 0


# --- File Upload Tests ---


def test_image_upload_and_directory_creation(api_client):
    """이미지 업로드 기능 검증"""
    api_client.post(
        "/v1/auth/signup",
        json={"email": "f@t.com", "password": "Password123!", "nickname": "file"},
    )
    api_client.post("/v1/auth/login", json={"email": "f@t.com", "password": "Password123!"})

    # 프로필 이미지 업로드
    files = {"profileImage": ("profile.png", b"fake_image_content", "image/png")}
    resp = api_client.post("/v1/users/me/profile-image", files=files)
    assert resp.status_code == 201
    assert "profileImageUrl" in resp.json()["data"]

    # 게시글 이미지 업로드
    files = {"postFile": ("post.jpg", b"fake_post_image", "image/jpeg")}
    resp = api_client.post("/v1/posts/image", files=files)
    assert resp.status_code == 201
    assert "postFileUrl" in resp.json()["data"]

