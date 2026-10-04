from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import (
    ProblemError,
    http_exception_handler,
    problem_error_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.redis_client import close_redis, get_redis
from app.db.session import dispose_engine, get_engine
from app.middleware.request_id import RequestIdMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.log_level)
    yield
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mimicron Control API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(api_router)

    app.add_exception_handler(ProblemError, problem_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"], response_model=None)
    async def readyz(_request: Request) -> Response | dict[str, Any]:
        checks: dict[str, str] = {}
        try:
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
        except Exception:
            checks["postgres"] = "fail"
        try:
            redis = get_redis()
            pong = await redis.ping()
            checks["redis"] = "ok" if pong else "fail"
        except Exception:
            checks["redis"] = "fail"
        # Redpanda wired in a later milestone when control-api publishes/consumes.
        checks["redpanda"] = "skipped"
        ready = checks["postgres"] == "ok" and checks["redis"] == "ok"
        body = {"status": "ready" if ready else "not_ready", "checks": checks}
        if not ready:
            return JSONResponse(status_code=503, content=body)
        return body

    @app.get("/metrics", tags=["ops"])
    def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
