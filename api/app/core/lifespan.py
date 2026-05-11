from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.core.redis_client import close_redis_client
from app.db.session import engine
from app.logging.setup import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    yield

    await close_redis_client()
    await engine.dispose()
