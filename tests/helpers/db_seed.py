import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_app_root(start_dir: Path) -> Path:
    candidates: list[Path] = []
    for parent in [start_dir, *start_dir.parents]:
        candidates.append(parent)
        candidates.append(parent / "2-owen-community-be")

    for cand in candidates:
        if (cand / "main.py").is_file() and (cand / "models").is_dir():
            return cand.resolve()

    raise RuntimeError(
        f"앱 루트를 찾을 수 없습니다. start_dir={start_dir}. "
        "main.py 와 models/ 가 있는 디렉토리(예: 2-owen-community-be)를 확인해주세요."
    )


async def _seed_async():
    """비동기 DB 초기화 및 시드 데이터 삽입 (내부용)"""
    from models.comment_model import comment_model
    from models.post_model import post_model
    from models.user_model import user_model
    from utils.database.db import execute

    logger.info("Seeding database...")

    await execute("DELETE FROM sessions")
    await user_model.clear()
    await post_model.clear()
    await comment_model.clear()

    admin_user = await user_model.createUser(
        email="admin@test.com",
        password="Admin123!",
        nickname="테스트관리자",
        profileImageUrl=None,
    )

    from utils.database.db import close_pool
    await close_pool()

    import utils.database.db as db_mod
    db_mod._pool = None

    logger.info("Database seeded. Admin user created: %s", admin_user["email"])
    return {
        "message": "Database reset and seeded successfully",
        "admin_user": {"email": admin_user["email"], "nickname": admin_user["nickname"]},
    }

def seed_database():
    """데이터베이스 초기화 및 시드 데이터 삽입"""
    app_root = _find_app_root(Path(__file__).resolve().parent)
    if str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))

    import utils.database.db as db_mod
    db_mod._pool = None

    return asyncio.run(_seed_async())
