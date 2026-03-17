import logging

logger = logging.getLogger(__name__)


def seed_database():
    """데이터베이스 초기화 및 시드 데이터 삽입"""
    # import 시점에 config/env 검증이 발생하므로 런타임에 import
    from models.comment_model import comment_model
    from models.post_model import post_model
    from models.user_model import user_model
    from utils.database.db import execute

    logger.info("Seeding database...")

    execute("DELETE FROM sessions")
    user_model.clear()
    post_model.clear()
    comment_model.clear()

    admin_user = user_model.createUser(
        email="admin@test.com",
        password="Admin123!",
        nickname="테스트관리자",
        profileImageUrl=None,
    )

    logger.info("Database seeded. Admin user created: %s", admin_user["email"])
    return {
        "message": "Database reset and seeded successfully",
        "admin_user": {"email": admin_user["email"], "nickname": admin_user["nickname"]},
    }

