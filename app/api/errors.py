"""API exception types and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound


class DomainError(Exception):
    """Business logic violation (valid payload, invalid operation)."""


class NotFoundError(Exception):
    """Explicit 404 raised by service code."""


def _value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


def _domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def _not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


def _no_result_found_handler(
    _request: Request, _exc: NoResultFound
) -> JSONResponse:
    return JSONResponse(
        status_code=404, content={"detail": "Resource not found"}
    )


def _integrity_error_handler(
    _request: Request, exc: IntegrityError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": f"Constraint violation: {exc.orig}"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to *app*."""
    app.add_exception_handler(ValueError, _value_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(DomainError, _domain_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(NotFoundError, _not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(NoResultFound, _no_result_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(IntegrityError, _integrity_error_handler)  # type: ignore[arg-type]
