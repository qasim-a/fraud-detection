"""Problem Details responses for consistent API failures."""

from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ExceptionHandler


class FieldError(BaseModel):
    field: str
    message: str


def _empty_field_errors() -> list[FieldError]:
    return []


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
    errors: list[FieldError] = Field(default_factory=_empty_field_errors)


def _problem(problem: ProblemDetails) -> JSONResponse:
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        FieldError(field=".".join(str(part) for part in error["loc"]), message=error["msg"])
        for error in exc.errors()
    ]
    return _problem(
        ProblemDetails(
            type="https://fraud.local/problems/validation",
            title="Request validation failed",
            status=422,
            detail="One or more request fields are invalid.",
            instance=str(request.url.path),
            errors=errors,
        )
    )


async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _problem(
        ProblemDetails(
            title="HTTP error",
            status=exc.status_code,
            detail=exc.detail,
            instance=str(request.url.path),
        )
    )


async def _unhandled_handler(request: Request, _exc: Exception) -> JSONResponse:
    return _problem(
        ProblemDetails(
            type="https://fraud.local/problems/internal",
            title="Internal server error",
            status=500,
            detail="The request could not be completed.",
            instance=str(request.url.path),
        )
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, _validation_handler),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, _http_handler),
    )
    app.add_exception_handler(Exception, _unhandled_handler)
