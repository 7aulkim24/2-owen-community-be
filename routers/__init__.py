from routers.post_router import router as post_router
from routers.comment_router import router as comment_router
from routers.auth_router import router as auth_router
from routers.user_router import router as user_router

try:
    from routers.test_router import router as test_router
except ModuleNotFoundError:
    test_router = None

__all__ = ["post_router", "comment_router", "auth_router", "user_router"]
if test_router is not None:
    __all__.append("test_router")
