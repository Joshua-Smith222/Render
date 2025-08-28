# config.py
import os
from dotenv import load_dotenv

# load .flaskenv and .env before reading
load_dotenv()

class Config:
    # pull from env
    DB_USER     = os.getenv("DB_USER")
    DB_PASS     = os.getenv("DB_PASS")
    DB_HOST     = os.getenv("DB_HOST")
    DB_PORT     = os.getenv("DB_PORT", 3306)
    DB_NAME     = os.getenv("DB_NAME")
    CHARSET     = os.getenv("DB_CHARSET", "utf8mb4")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset={CHARSET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
