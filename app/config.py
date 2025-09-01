# app/config.py
import os

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "1") == "1"  # only used outside tests

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Render sets DATABASE_URL (e.g. postgresql://...); SQLAlchemy picks psycopg2 driver
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    AUTO_MIGRATE = False  # never run migrations in tests

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
