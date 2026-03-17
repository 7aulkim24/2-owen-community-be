-- 관리자 계정 초기 삽입용 예시
-- password 값은 bcrypt로 해싱된 문자열로 교체하세요.

INSERT INTO users (user_id, email, password, nickname, profile_image_url, created_at)
VALUES (
    '01JADMIN000000000000000000',
    'admin@test.com',
    '$2b$12$H3d3ZwnDXlrainByLhM1Tu1zwFkDU9VLu35cKTv9POiX/.jAMO5fi',
    'admin',
    NULL,
    NOW()
);
