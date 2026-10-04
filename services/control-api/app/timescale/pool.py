from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None


def get_timescale_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.timescale_url, pool_pre_ping=True)
    return _engine


async def dispose_timescale() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
