-- Migration: Add post_images table for multi-image support
-- This migration creates a new table to store multiple images per post
-- and migrates existing single images from posts.post_image_url

-- Create post_images table
CREATE TABLE IF NOT EXISTS post_images (
    image_id VARCHAR(50) PRIMARY KEY,
    post_id VARCHAR(26) NOT NULL,
    image_url VARCHAR(512) NOT NULL,
    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_post_images_post FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create indexes for efficient queries
CREATE INDEX idx_post_images_post_order ON post_images(post_id, sort_order ASC);
CREATE INDEX idx_post_images_post ON post_images(post_id);

-- Migrate existing images from posts.post_image_url to post_images table
-- Only migrate posts that have an image_url and are not deleted
INSERT INTO post_images (image_id, post_id, image_url, sort_order, created_at)
SELECT 
    CONCAT(post_id, '_img_0'),  -- Generate image_id based on post_id
    post_id,
    post_image_url,
    0,  -- First image has sort_order 0
    created_at
FROM posts
WHERE post_image_url IS NOT NULL 
  AND post_image_url != '' 
  AND deleted_at IS NULL;

-- Note: We keep the post_image_url column for backward compatibility
-- Future posts will use post_images table exclusively
