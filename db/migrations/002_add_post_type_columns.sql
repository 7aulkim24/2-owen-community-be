-- ============================================================
-- Migration 002: posts 테이블 콘텐츠 유형 컬럼 추가
-- Date: 2026-03-17
-- Description:
--   Phase 0 — 자동 기록(auto_log), 수동 작성(manual), 주간 회고(weekly_digest)를
--   구분하기 위한 컬럼을 posts 테이블에 추가합니다.
--   DEFAULT 값으로 기존 데이터 하위 호환성을 보장합니다.
-- Rollback:
--   ALTER TABLE posts DROP COLUMN post_type, DROP COLUMN source_type,
--                    DROP COLUMN source_summary, DROP COLUMN is_draft;
--   DROP INDEX idx_posts_post_type ON posts;
--   DROP INDEX idx_posts_is_draft ON posts;
-- ============================================================

ALTER TABLE posts
  ADD COLUMN post_type VARCHAR(20) NOT NULL DEFAULT 'manual'
      COMMENT '게시글 유형: manual | auto_log | weekly_digest'
      AFTER content,
  ADD COLUMN source_type VARCHAR(20) DEFAULT NULL
      COMMENT '소스 유형: github | notion 등'
      AFTER post_type,
  ADD COLUMN source_summary JSON DEFAULT NULL
      COMMENT '소스별 요약 데이터 (커밋 수, PR 수 등)'
      AFTER source_type,
  ADD COLUMN is_draft BOOLEAN NOT NULL DEFAULT FALSE
      COMMENT '임시저장 여부'
      AFTER source_summary;

CREATE INDEX idx_posts_post_type ON posts(post_type);
CREATE INDEX idx_posts_is_draft  ON posts(is_draft);
