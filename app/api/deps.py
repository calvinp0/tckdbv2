"""FastAPI dependency callables: DB session, auth, pagination."""

from __future__ import annotations

import hashlib
from typing import Iterator

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.config import settings
from app.db.models.app_user import AppUser

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Yield a read-only database session.

    Does not commit — just closes the session when done.  Write endpoints
    should use :func:`get_write_db` instead.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_write_db() -> Iterator[Session]:
    """Yield a database session that commits on success, rolls back on error.

    Use this for endpoints that mutate data (uploads, creates).
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def get_current_user(
    x_api_key: str | None = Header(None),
    session: Session = Depends(get_db),
) -> AppUser:
    """Look up the authenticated user via ``X-API-Key`` header."""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    key_hash = _hash_api_key(x_api_key)
    user = session.scalar(
        select(AppUser).where(AppUser.api_key_hash == key_hash)
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


def get_current_user_optional(
    x_api_key: str | None = Header(None),
    session: Session = Depends(get_db),
) -> AppUser | None:
    """Same as :func:`get_current_user` but returns ``None`` when no key is
    provided.  Useful during development."""
    if x_api_key is None:
        return None
    return get_current_user(x_api_key=x_api_key, session=session)


class PaginationParams:
    """Dependency that extracts ``skip`` / ``limit`` query params."""

    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=200),
    ):
        self.skip = skip
        self.limit = limit
