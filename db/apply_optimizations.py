import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가 (db 폴더 내부이므로 한 단계 더 위로)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database.db import execute, init_pool, close_pool

OPTIMIZATION_SQL = [
    "CREATE INDEX idx_posts_deleted_created ON posts(deleted_at, created_at DESC)",
    "CREATE INDEX idx_comments_post_deleted_created ON comments(post_id, deleted_at, created_at DESC)",
    "CREATE INDEX idx_comments_user_deleted_created ON comments(user_id, deleted_at, created_at DESC)"
]

async def apply_indexes():
    print("추천 인덱스 적용을 시작합니다...")
    await init_pool()
    for sql in OPTIMIZATION_SQL:
        try:
            print(f"실행 중: {sql}")
            await execute(sql)
            print("성공")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("이미 존재하는 인덱스입니다. 건너뜀")
            else:
                print(f"오류 발생: {str(e)}")
    await close_pool()

if __name__ == "__main__":
    asyncio.run(apply_indexes())
import sys
import os
import asyncio

# 프로젝트 루트를 path에 추가 (db 폴더 내부이므로 한 단계 더 위로)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.database.db import execute, init_pool, close_pool

OPTIMIZATION_SQL = [
    "CREATE INDEX idx_posts_deleted_created ON posts(deleted_at, created_at DESC)",
    "CREATE INDEX idx_comments_post_deleted_created ON comments(post_id, deleted_at, created_at DESC)",
    "CREATE INDEX idx_comments_user_deleted_created ON comments(user_id, deleted_at, created_at DESC)"
]

def apply_indexes():
    print("추천 인덱스 적용을 시작합니다...")
    for sql in OPTIMIZATION_SQL:
        try:
            print(f"실행 중: {sql}")
            execute(sql)
            print("성공")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("이미 존재하는 인덱스입니다. 건너뜜")
            else:
                print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    apply_indexes()
