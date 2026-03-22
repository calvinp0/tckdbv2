"""Application configuration via environment variables.

Reuses the same ``DB_*`` variables consumed by ``alembic/env.py`` and
``tests/conftest.py``.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_user: str = "tckdb"
    db_password: str = "tckdb"
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "tckdb_dev"
    db_client_encoding: str = "utf8"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?client_encoding={self.db_client_encoding}"
        )


settings = Settings()
