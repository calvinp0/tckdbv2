"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TCKDB",
        version="0.1.0",
        description="Thermochemical and Kinetics Database API",
    )
    app.include_router(api_router, prefix="/api/v1")
    register_exception_handlers(app)
    return app
