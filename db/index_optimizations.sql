-- 성능 측정 후 적용할 인덱스 후보
-- 실제 적용 전, EXPLAIN 결과와 슬로우 쿼리 로그를 확인하세요.

-- 게시글 목록: deleted_at 필터 + created_at 정렬 최적화
CREATE INDEX idx_posts_deleted_created ON posts(deleted_at, created_at DESC);

-- 댓글 목록(게시글): post_id + deleted_at + created_at 정렬 최적화
CREATE INDEX idx_comments_post_deleted_created ON comments(post_id, deleted_at, created_at DESC);

-- 댓글 목록(사용자): user_id + deleted_at + created_at 정렬 최적화
CREATE INDEX idx_comments_user_deleted_created ON comments(user_id, deleted_at, created_at DESC);
