"""
Central configuration, loaded from environment variables.

On Render, set these under your service's "Environment" tab.
Locally, copy .env.example to .env and edit it (docker-compose reads it automatically).
"""
import os
from datetime import timedelta


class Settings:
    # --- Auth ---
    # IMPORTANT: change these. The firmware currently ships with the same
    # admin/admin123 defaults, which is fine for a bench prototype but must
    # be changed before this touches anything with real patient data.
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_DEV_ONLY_NOT_SECURE")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # --- Database ---
    # Render Postgres gives you a DATABASE_URL like:
    #   postgres://user:pass@host/dbname
    # SQLAlchemy needs the "postgresql://" scheme, so we rewrite it below.
    # Falls back to a local SQLite file if nothing is set (fine for dev).
    _raw_db_url: str = os.getenv("DATABASE_URL", "sqlite:///./medmon.db")
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = _raw_db_url

    # --- CORS ---
    # Comma-separated list of allowed origins, e.g. "https://myapp.com,https://foo.com"
    # "*" allows everything (fine while you're building the dashboard).
    CORS_ORIGINS: list = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

    # --- Readings retention (basic sanity limits, not medical-grade) ---
    MAX_READINGS_RETURNED: int = 500


settings = Settings()
JWT_EXPIRE_DELTA = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
