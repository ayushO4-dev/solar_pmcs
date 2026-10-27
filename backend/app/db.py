"""Postgres connection pool and small query helpers."""

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import settings

pool = AsyncConnectionPool(settings.database_url, open=False, kwargs={"row_factory": dict_row})


async def fetch_one(query: str, params=None) -> dict | None:
    async with pool.connection() as conn:
        cur = await conn.execute(query, params)
        return await cur.fetchone()


async def fetch_all(query: str, params=None) -> list[dict]:
    async with pool.connection() as conn:
        cur = await conn.execute(query, params)
        return await cur.fetchall()


async def execute(query: str, params=None) -> int:
    """Run a statement and return the number of affected rows."""
    async with pool.connection() as conn:
        cur = await conn.execute(query, params)
        return cur.rowcount
