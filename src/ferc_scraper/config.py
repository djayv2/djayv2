from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    # HTTP/scraper settings
    base_url: str = Field(default=os.getenv("BASE_URL", "https://www.ferc.gov/news-events/news"))
    max_pages: int = Field(default=int(os.getenv("MAX_PAGES", "1")))
    request_timeout_seconds: float = Field(default=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")))
    max_retries: int = Field(default=int(os.getenv("MAX_RETRIES", "6")))
    scd_type: int = Field(default=int(os.getenv("SCD_TYPE", "2")))  # 1 or 2
    fetch_details: bool = Field(default=os.getenv("FETCH_DETAILS", "true").lower() in {"1", "true", "yes"})

    # Networking
    outbound_proxy_url: Optional[str] = Field(default=os.getenv("OUTBOUND_PROXY_URL"))
    source_ip: Optional[str] = Field(default=os.getenv("SOURCE_IP"))

    # Database
    db_host: str = Field(default=os.getenv("DB_HOST", ""))
    db_port: int = Field(default=int(os.getenv("DB_PORT", "5432")))
    db_name: str = Field(default=os.getenv("DB_NAME", ""))
    db_user: str = Field(default=os.getenv("DB_USER", ""))
    db_password: str = Field(default=os.getenv("DB_PASSWORD", ""))
    db_sslmode: str = Field(default=os.getenv("DB_SSLMODE", "prefer"))
    db_connect_timeout_seconds: int = Field(default=int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "20")))
    db_schema: str = Field(default=os.getenv("DB_SCHEMA", "test_external"))

    application_name: str = Field(default=os.getenv("APPLICATION_NAME", "ferc_scraper"))

    @field_validator("scd_type")
    @classmethod
    def validate_scd_type(cls, value: int) -> int:
        if value not in (1, 2):
            raise ValueError("SCD_TYPE must be 1 or 2")
        return value

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        if not value.startswith("http://") and not value.startswith("https://"):
            raise ValueError("BASE_URL must start with http:// or https://")
        return value


def get_settings() -> Settings:
    return Settings()