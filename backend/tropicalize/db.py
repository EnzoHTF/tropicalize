"""Acesso ao Postgres (Supabase) com pool assíncrono do psycopg."""
from contextlib import asynccontextmanager

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from . import config

_pool: AsyncConnectionPool | None = None


async def abrir_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        if not config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL não configurada")
        # prepare_threshold=None: o pooler do Supabase (modo transação) não aceita prepared statements
        _pool = AsyncConnectionPool(
            config.DATABASE_URL, min_size=1, max_size=10, open=False,
            kwargs={"row_factory": dict_row, "prepare_threshold": None, "autocommit": True},
        )
        await _pool.open()
    return _pool


async def fechar_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def conexao():
    pool = await abrir_pool()
    async with pool.connection() as conn:
        yield conn


async def buscar_todos(sql: str, params=None) -> list[dict]:
    async with conexao() as conn:
        cur = await conn.execute(sql, params)
        return await cur.fetchall()


async def buscar_um(sql: str, params=None) -> dict | None:
    async with conexao() as conn:
        cur = await conn.execute(sql, params)
        return await cur.fetchone()


async def executar(sql: str, params=None) -> None:
    async with conexao() as conn:
        await conn.execute(sql, params)


def vetor(valores: list[float]) -> str:
    """Formata um embedding no literal aceito pelo pgvector."""
    return "[" + ",".join(f"{v:.7f}" for v in valores) + "]"


__all__ = ["Jsonb", "abrir_pool", "fechar_pool", "conexao", "buscar_todos", "buscar_um", "executar", "vetor"]
