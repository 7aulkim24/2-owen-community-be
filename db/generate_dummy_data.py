import argparse
import asyncio
import os
import random
import sys
from typing import Iterable, List, Sequence, Tuple

# 프로젝트 루트 디렉토리를 sys.path에 추가하여 config, utils 등을 임포트할 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
import aiomysql
from faker import Faker

from config import settings
from utils.common.id_utils import generate_id


def _chunks(items: Sequence[Tuple], size: int) -> Iterable[List[Tuple]]:
    for idx in range(0, len(items), size):
        yield list(items[idx:idx + size])


async def _connect():
    return await aiomysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        autocommit=False,
    )


async def _maybe_clear(cursor, clear: bool):
    if not clear:
        return
    await cursor.execute("DELETE FROM post_likes")
    await cursor.execute("DELETE FROM comments")
    await cursor.execute("DELETE FROM posts")
    await cursor.execute("DELETE FROM sessions")
    await cursor.execute("DELETE FROM users")


def _get_image_files(directory: str) -> List[str]:
    if not os.path.exists(directory):
        return []
    return [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]


async def _insert_users(cursor, faker: Faker, total: int, batch_size: int) -> List[str]:
    user_ids: List[str] = []
    hashed_password = bcrypt.hashpw(b"password1234!", bcrypt.gensalt()).decode("utf-8")

    # 프로필 이미지 목록 가져오기
    profile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "image", "profile")
    profile_images = _get_image_files(profile_dir)

    insert_sql = """
        INSERT INTO users (user_id, email, password, nickname, profile_image_url, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """
    while len(user_ids) < total:
        batch = min(batch_size, total - len(user_ids))
        rows: List[Tuple] = []
        for _ in range(batch):
            user_id = generate_id()
            email = faker.unique.email()
            nickname = faker.unique.user_name()[:50]

            # 30% 확률로 프로필 이미지 할당
            profile_image_url = None
            if profile_images and random.random() < 0.3:
                img_name = random.choice(profile_images)
                profile_image_url = f"/public/image/profile/{img_name}"

            rows.append((user_id, email, hashed_password, nickname, profile_image_url))
            user_ids.append(user_id)
        await cursor.executemany(insert_sql, rows)
    return user_ids


async def _insert_posts(
    cursor,
    faker: Faker,
    user_ids: Sequence[str],
    total: int,
    batch_size: int,
) -> List[str]:
    post_ids: List[str] = []

    # 게시글 이미지 목록 가져오기
    post_img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "image", "post")
    post_images = _get_image_files(post_img_dir)

    insert_sql = """
        INSERT INTO posts (post_id, user_id, title, content, post_image_url, hits, comment_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, 0, NOW())
    """
    while len(post_ids) < total:
        batch = min(batch_size, total - len(post_ids))
        rows: List[Tuple] = []
        for _ in range(batch):
            post_id = generate_id()
            user_id = random.choice(user_ids)
            title = faker.sentence(nb_words=8)[:300]
            content = faker.paragraph(nb_sentences=5)
            hits = random.randint(0, 500)

            # 40% 확률로 게시글 이미지 할당
            post_image_url = None
            if post_images and random.random() < 0.4:
                img_name = random.choice(post_images)
                post_image_url = f"/public/image/post/{img_name}"

            rows.append((post_id, user_id, title, content, post_image_url, hits))
            post_ids.append(post_id)
        await cursor.executemany(insert_sql, rows)
    return post_ids


async def _insert_comments(
    cursor,
    faker: Faker,
    user_ids: Sequence[str],
    post_ids: Sequence[str],
    total: int,
    batch_size: int,
):
    insert_sql = """
        INSERT INTO comments (comment_id, post_id, user_id, content, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """
    inserted = 0
    while inserted < total:
        batch = min(batch_size, total - inserted)
        rows: List[Tuple] = []
        for _ in range(batch):
            comment_id = generate_id()
            post_id = random.choice(post_ids)
            user_id = random.choice(user_ids)
            content = faker.sentence(nb_words=18)
            rows.append((comment_id, post_id, user_id, content))
        await cursor.executemany(insert_sql, rows)
        inserted += batch


async def _sync_comment_counts(cursor):
    await cursor.execute(
        """
        UPDATE posts p
        LEFT JOIN (
            SELECT post_id, COUNT(*) AS cnt
            FROM comments
            WHERE deleted_at IS NULL
            GROUP BY post_id
        ) c ON c.post_id = p.post_id
        SET p.comment_count = COALESCE(c.cnt, 0)
        WHERE p.deleted_at IS NULL
        """
    )


async def _insert_admin(cursor):
    admin_id = '01JADMIN000000000000000000'
    admin_email = 'admin@test.com'
    # 'admin' 비밀번호에 대한 bcrypt 해시 (seed.sql과 동일)
    admin_password = '$2b$12$H3d3ZwnDXlrainByLhM1Tu1zwFkDU9VLu35cKTv9POiX/.jAMO5fi'
    admin_nickname = 'admin'

    insert_sql = """
        INSERT IGNORE INTO users (user_id, email, password, nickname, profile_image_url, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """
    await cursor.execute(insert_sql, (admin_id, admin_email, admin_password, admin_nickname, None))


async def main():
    parser = argparse.ArgumentParser(description="Generate and insert dummy data.")
    parser.add_argument("--users", type=int, default=10_000)
    parser.add_argument("--posts", type=int, default=40_000)
    parser.add_argument("--comments", type=int, default=50_000)
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing data before inserting dummy data.",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    faker = Faker("en_US")
    faker.seed_instance(args.seed)

    conn = await _connect()
    try:
        async with conn.cursor() as cursor:
            await _maybe_clear(cursor, args.clear)

            await _insert_admin(cursor)
            user_ids = await _insert_users(cursor, faker, args.users, args.batch_size)
            await conn.commit()
            print(f"Inserted users: {len(user_ids)}")

            post_ids = await _insert_posts(cursor, faker, user_ids, args.posts, args.batch_size)
            await conn.commit()
            print(f"Inserted posts: {len(post_ids)}")

            await _insert_comments(cursor, faker, user_ids, post_ids, args.comments, args.batch_size)
            await conn.commit()
            print(f"Inserted comments: {args.comments}")

            await _sync_comment_counts(cursor)
            await conn.commit()
            print("Synced comment_count for posts.")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
