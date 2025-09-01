# app/config.py
from __future__ import annotations
import os

def _normalize_db_url(url: str | None) -> str | None:
    """
    Render/Postgres often provides 'postgres://...'
    SQLAlchemy 2.x prefers 'postgresql+psycopg2://...'
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        # keep as-is (driver default is fine)
        pass
    return url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    # Auto run `flask db upgrade` at boot (we guard it in create_app)
    AUTO_MIGRATE = True

class ProductionConfig(Config):
    # Prefer explicit SQLALCHEMY_DATABASE_URI; otherwise use DATABASE_URL (Render default)
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    )
    # No silent fallback in prod — fail loudly so misconfig is obvious
    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError(
            "DATABASE_URL or SQLALCHEMY_DATABASE_URI must be set for ProductionConfig."
        )

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.getenv("DEV_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///dev.db"
    )

class TestingConfig(Config):
    TESTING = True
    AUTO_MIGRATE = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
