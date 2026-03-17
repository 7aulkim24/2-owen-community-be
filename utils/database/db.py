from typing import Any, Dict, Iterable, Optional
import logging
import aiomysql
from config import settings


_pool: Optional[aiomysql.Pool] = None
_logger = logging.getLogger("db")


async def init_pool() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = await aiomysql.create_pool(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        db=settings.db_name,
        minsize=1,
        maxsize=settings.db_pool_size,
        autocommit=False,
    )


async def close_pool() -> None:
    global _pool
    if _pool is None:
        return
    _pool.close()
    await _pool.wait_closed()
    _pool = None


async def _ensure_pool() -> None:
    if _pool is None:
        await init_pool()


async def _execute(
    query: str,
    params: Optional[Iterable[Any]] = None,
    fetchone: bool = False,
    fetchall: bool = False,
) -> Any:
    await _ensure_pool()
    if _pool is None:
        raise RuntimeError("DB pool is not initialized")

    async with _pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            try:
                await cursor.execute(query, params or ())
                result = None
                if fetchone:
                    result = await cursor.fetchone()
                elif fetchall:
                    result = await cursor.fetchall()
                await conn.commit()
                return result
            except Exception as e:
                await conn.rollback()
                _logger.error(f"DB Error: {str(e)} | Query: {query} | Params: {params}")
                raise e


async def fetch_one(query: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    return await _execute(query, params=params, fetchone=True)


async def fetch_all(query: str, params: Optional[Iterable[Any]] = None) -> Iterable[Dict[str, Any]]:
    return await _execute(query, params=params, fetchall=True)


async def execute(query: str, params: Optional[Iterable[Any]] = None) -> int:
    await _ensure_pool()
    if _pool is None:
        raise RuntimeError("DB pool is not initialized")

    async with _pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(query, params or ())
                await conn.commit()
                return cursor.rowcount
            except Exception as e:
                await conn.rollback()
                _logger.error(f"DB Error: {str(e)} | Query: {query} | Params: {params}")
                raise e
