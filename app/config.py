"""Configuración de la aplicación Flask."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuración base; los valores sensibles vienen de variables de entorno."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # En docker-compose se sobrescribe con host 'db'; en local apunta a 'localhost'.
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://fruitscan:fruitscan@localhost:5432/fruitscan",
    )

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}

    ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", BASE_DIR / "ml" / "artifacts"))

    HISTORY_DEFAULT_LIMIT = 24
    HISTORY_MAX_LIMIT = 200

    JSON_AS_ASCII = False