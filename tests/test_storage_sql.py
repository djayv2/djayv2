import os
import pytest

from ferc_scraper.config import Settings
from ferc_scraper.storage import PostgresStorage


def require_db_env():
    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        pytest.skip("DB env not set: " + ",".join(missing))


def make_settings() -> Settings:
    return Settings(
        db_host=os.getenv("DB_HOST"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME"),
        db_user=os.getenv("DB_USER"),
        db_password=os.getenv("DB_PASSWORD"),
        db_schema=os.getenv("DB_SCHEMA", "test_external"),
    )


def test_ensure_schema_and_tables():
    require_db_env()
    settings = make_settings()
    with PostgresStorage(settings) as storage:
        storage.ensure_schema_and_tables()