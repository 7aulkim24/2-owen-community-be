-- ============================================================
-- Migration 004: activity_events, sync_jobs 테이블 생성
-- Date: 2026-03-18
-- Description:
--   Phase 1 — GitHub 이벤트 수집 및 동기화 작업 관리.
--   activity_events: UNIQUE KEY uq_provider_external로 idempotency 보장.
--   sync_jobs: 수집 작업 상태 및 재시도 관리.
-- Rollback:
--   DROP TABLE IF EXISTS sync_jobs;
--   DROP TABLE IF EXISTS activity_events;
-- ============================================================

CREATE TABLE IF NOT EXISTS activity_events (
    event_id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    external_id VARCHAR(200) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    event_url VARCHAR(500),
    repo_name VARCHAR(200),
    event_metadata JSON,
    event_occurred_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activity_events_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uq_provider_external (provider, external_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_activity_events_user_date ON activity_events(user_id, event_occurred_at);

CREATE TABLE IF NOT EXISTS sync_jobs (
    job_id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at DATETIME,
    completed_at DATETIME,
    last_synced_at DATETIME,
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_sync_jobs_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);
