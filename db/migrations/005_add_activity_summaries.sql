-- ============================================================
-- Migration 005: activity_summaries 테이블 생성
-- Date: 2026-03-18
-- Description:
--   Phase 1 — 자동 생성된 요약 초안 저장.
--   UNIQUE KEY uq_user_date_type로 같은 날 재생성 시 UPDATE 처리.
--   post_id FK: 승인 시 posts 테이블과 연결.
-- Rollback:
--   DROP TABLE IF EXISTS activity_summaries;
-- ============================================================

CREATE TABLE IF NOT EXISTS activity_summaries (
    summary_id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NOT NULL,
    summary_date DATE NOT NULL,
    summary_type VARCHAR(20) NOT NULL DEFAULT 'daily',
    event_count INT NOT NULL DEFAULT 0,
    providers JSON,
    generated_title VARCHAR(200),
    generated_content TEXT,
    post_id VARCHAR(26),
    status VARCHAR(20) NOT NULL DEFAULT 'generated',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_activity_summaries_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_activity_summaries_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE SET NULL,
    UNIQUE KEY uq_user_date_type (user_id, summary_date, summary_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
