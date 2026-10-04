from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ProblemError(Exception):
    def __init__(
        self,
        *,
        status: int,
        title: str,
        type_: str = "about:blank",
        detail: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.type_ = type_
        self.detail = detail
        self.extra = extra or {}


def problem_response(
    request: Request | None,
    *,
    status: int,
    title: str,
    type_: str = "about:blank",
    detail: str | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
    }
    if detail:
        body["detail"] = detail
    request_id = getattr(request.state, "request_id", None) if request is not None else None
    if request_id:
        body["request_id"] = request_id
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status, content=body, media_type="application/problem+json")


async def problem_error_handler(request: Request, exc: ProblemError) -> JSONResponse:
    response = problem_response(
        request,
        status=exc.status,
        title=exc.title,
        type_=exc.type_,
        detail=exc.detail,
        extra=exc.extra,
    )
    if exc.status == 429:
        response.headers["Retry-After"] = str(exc.extra.get("retry_after", 1))
    return response


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem_response(request, status=exc.status_code, title=str(exc.detail))


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return problem_response(
        request,
        status=422,
        title="Validation failed",
        type_="https://mimicron.dev/problems/validation",
        detail="Request validation failed",
        extra={"errors": exc.errors()},
    )
