import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import asyncpg
from mcp.server.fastmcp import FastMCP


@dataclass
class PostgresAppContext:
    db_pool: asyncpg.Pool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[PostgresAppContext]:
    db_pool = None
    db_url = os.environ.get("POSTGRES_DATABASE_URL")
    if not db_url:
        raise ValueError("POSTGRES_DATABASE_URL not set.")
    try:
        print("PostgreSQL Lifespan: Connecting...")
        db_pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=10)
        print("PostgreSQL Lifespan: Connection pool established.")
        yield PostgresAppContext(db_pool=db_pool)
    finally:
        if db_pool:
            print("PostgreSQL Lifespan: Closing connection pool...")
            await db_pool.close()
