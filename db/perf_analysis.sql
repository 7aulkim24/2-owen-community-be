-- 주요 조회 쿼리 EXPLAIN용 템플릿
-- 실행 전, 실제 파라미터로 교체하세요.

-- 게시글 목록 (페이징)
EXPLAIN
SELECT
    p.post_id,
    p.user_id AS author_id,
    u.nickname AS author_nickname,
    p.title,
    p.content,
    p.post_image_url,
    p.created_at,
    p.updated_at,
    p.hits,
    p.comment_count,
    (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id) AS like_count
FROM posts p
LEFT JOIN users u ON u.user_id = p.user_id
WHERE p.deleted_at IS NULL
ORDER BY p.created_at DESC
LIMIT 20 OFFSET 0;

-- 게시글 상세
EXPLAIN
SELECT
    p.post_id,
    p.user_id AS author_id,
    u.nickname AS author_nickname,
    p.title,
    p.content,
    p.post_image_url,
    p.created_at,
    p.updated_at,
    p.hits,
    p.comment_count,
    (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.post_id) AS like_count
FROM posts p
LEFT JOIN users u ON u.user_id = p.user_id
WHERE p.post_id = '01JEXAMPLEPOST00000000000000' AND p.deleted_at IS NULL;

-- 댓글 목록 (게시글 기준)
EXPLAIN
SELECT
    c.comment_id,
    c.post_id,
    c.user_id,
    u.nickname AS user_nickname,
    c.content,
    c.created_at,
    c.updated_at
FROM comments c
LEFT JOIN users u ON u.user_id = c.user_id
WHERE c.post_id = '01JEXAMPLEPOST00000000000000' AND c.deleted_at IS NULL
ORDER BY c.created_at DESC;

-- 댓글 목록 (사용자 기준)
EXPLAIN
SELECT
    c.comment_id,
    c.post_id,
    c.user_id,
    u.nickname AS user_nickname,
    c.content,
    c.created_at,
    c.updated_at
FROM comments c
LEFT JOIN users u ON u.user_id = c.user_id
WHERE c.user_id = '01JEXAMPLEUSER00000000000000' AND c.deleted_at IS NULL
ORDER BY c.created_at DESC;
