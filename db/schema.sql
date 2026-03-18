CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(26) PRIMARY KEY,
    email VARCHAR(254) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_image_url VARCHAR(512) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    UNIQUE INDEX idx_email (email),
    UNIQUE INDEX idx_nickname (nickname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS posts (
    post_id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NULL,
    title VARCHAR(300) NOT NULL,
    content TEXT NOT NULL,
    post_type VARCHAR(20) NOT NULL DEFAULT 'manual'
        COMMENT '게시글 유형: manual | auto_log | weekly_digest',
    source_type VARCHAR(20) DEFAULT NULL
        COMMENT '소스 유형: github | notion 등',
    source_summary JSON DEFAULT NULL
        COMMENT '소스별 요약 데이터 (커밋 수, PR 수 등)',
    is_draft BOOLEAN NOT NULL DEFAULT FALSE
        COMMENT '임시저장 여부',
    post_image_url VARCHAR(512) NULL,
    hits INT UNSIGNED NOT NULL DEFAULT 0,
    comment_count INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_author_created ON posts(user_id, created_at DESC);
CREATE INDEX idx_created ON posts(created_at DESC);
CREATE INDEX idx_posts_deleted_created ON posts(deleted_at, created_at DESC);
CREATE INDEX idx_posts_post_type ON posts(post_type);
CREATE INDEX idx_posts_is_draft  ON posts(is_draft);

CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(26) PRIMARY KEY,
    post_id VARCHAR(26) NOT NULL,
    user_id VARCHAR(26) NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT fk_comments_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_post_created ON comments(post_id, created_at ASC);
CREATE INDEX idx_user ON comments(user_id);
CREATE INDEX idx_comments_post_deleted_created ON comments(post_id, deleted_at, created_at DESC);
CREATE INDEX idx_comments_user_deleted_created ON comments(user_id, deleted_at, created_at DESC);

CREATE TABLE IF NOT EXISTS post_likes (
    post_id VARCHAR(26) NOT NULL,
    user_id VARCHAR(26) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (post_id, user_id),
    CONSTRAINT fk_post_likes_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    CONSTRAINT fk_post_likes_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_post ON post_likes(post_id);

CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_key VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(26) NULL,
    data TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_expires ON sessions(expires_at);
CREATE INDEX idx_user_expires ON sessions(user_id, expires_at);

CREATE TABLE IF NOT EXISTS post_images (
    image_id VARCHAR(50) PRIMARY KEY,
    post_id VARCHAR(26) NOT NULL,
    image_url VARCHAR(512) NOT NULL,
    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_images_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_post_images_post_order ON post_images(post_id, sort_order ASC);
CREATE INDEX idx_post_images_post ON post_images(post_id);

-- Phase 1: GitHub OAuth 연동 계정
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

-- Phase 1: 활동 이벤트 수집
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

-- Phase 1: 수집 작업 관리
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

-- Phase 1: 자동 요약 초안
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
