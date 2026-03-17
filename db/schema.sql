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
