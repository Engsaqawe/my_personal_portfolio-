"""MySQL connection helpers for ENGSAQAWE."""

import os
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv


# Load the project-local secret file before building the connection settings.
load_dotenv(Path(__file__).resolve().with_name(".env"), override=False)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "engsaqawe_app"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "engsaqawe"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": False,
}


def get_db():
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "DB_PASSWORD is missing. Add the rotated password for DB_USER in the project .env file."
        )
    return pymysql.connect(**DB_CONFIG)
