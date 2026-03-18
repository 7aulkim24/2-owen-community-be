-- ============================================================
-- Migration 003: connected_accounts 테이블 생성
-- Date: 2026-03-18
-- Description:
--   Phase 1 — GitHub OAuth 연동 계정 정보 저장.
--   access_token은 Fernet 암호화 후 저장합니다.
--   UNIQUE KEY uq_user_provider로 사용자당 provider 1개 연동 보장.
-- Rollback:
--   DROP TABLE IF EXISTS connected_accounts;
-- ============================================================

CREATE TABLE IF NOT EXISTS connected_accounts (
    account_id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    provider_user_id VARCHAR(100) NOT NULL,
    provider_username VARCHAR(100),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at DATETIME,
    scopes VARCHAR(500),
    connected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    disconnected_at DATETIME,
    CONSTRAINT fk_connected_accounts_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_provider (user_id, provider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
