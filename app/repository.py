"""Persistencia del historial de inferencias en PostgreSQL usando pg8000."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

import pg8000.dbapi

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id            SERIAL PRIMARY KEY,
    created_at    TEXT             NOT NULL,
    filename      VARCHAR(255)     NOT NULL,
    label         VARCHAR(64)      NOT NULL,
    display_label VARCHAR(96)      NOT NULL,
    fruit         VARCHAR(48)      NOT NULL,
    state         VARCHAR(16)      NOT NULL,
    confidence    DOUBLE PRECISION NOT NULL,
    top_k         TEXT             NOT NULL,
    latency_ms    DOUBLE PRECISION NOT NULL,
    thumbnail     TEXT
);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_state ON predictions (state);
"""

STATS_TOTAL = "SELECT COUNT(*), AVG(confidence), MAX(created_at) FROM predictions"
STATS_STATE = "SELECT state, COUNT(*) FROM predictions GROUP BY state"
STATS_FRUIT = "SELECT fruit, COUNT(*) FROM predictions GROUP BY fruit"

COLUMNS = (
    "id, created_at, filename, label, display_label, fruit, state, "
    "confidence, top_k, latency_ms, thumbnail"
)

def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def row_to_dict(row) -> dict:
    (record_id, created_at, filename, label, display_label, fruit, state, confidence, top_k, latency_ms, thumbnail) = row
    if hasattr(created_at, "isoformat"):
        created_at = created_at.astimezone(timezone.utc).isoformat(timespec="seconds")
    try:
        parsed_top_k = json.loads(top_k) if isinstance(top_k, str) else top_k
    except (TypeError, ValueError):
        parsed_top_k = []

    return {
        "id": record_id,
        "created_at": created_at,
        "filename": filename,
        "label": label,
        "display_label": display_label,
        "fruit": fruit,
        "state": state,
        "confidence": round(float(confidence), 4),
        "top_k": parsed_top_k or [],
        "latency_ms": round(float(latency_ms or 0.0), 2),
        "thumbnail": thumbnail,
    }

class PostgresRepository:
    def __init__(self, dsn: str):
        parsed = urlparse(dsn)
        self.settings = {
            "user": unquote(parsed.username or "fruitscan"),
            "password": unquote(parsed.password or ""),
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": (parsed.path or "/fruitscan").lstrip("/") or "fruitscan",
        }
        self._lock = threading.Lock()

    def _connect(self):
        return pg8000.dbapi.connect(**self.settings, timeout=10)

    def init(self) -> None:
        statements = [statement.strip() for statement in SCHEMA.split(";") if statement.strip()]
        with self._connect() as connection:
            cursor = connection.cursor()
            for statement in statements:
                cursor.execute(statement)
            connection.commit()

    def ping(self) -> bool:

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True

    def insert(self, record: dict) -> dict:
        payload = (
            record["created_at"], record["filename"], record["label"], record["display_label"],
            record["fruit"], record["state"], record["confidence"],
            json.dumps(record["top_k"], ensure_ascii=False), record["latency_ms"], record.get("thumbnail"),
        )
        sql = (
            "INSERT INTO predictions (created_at, filename, label, display_label, fruit, state, "
            "confidence, top_k, latency_ms, thumbnail) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "RETURNING " + COLUMNS
        )
        with self._lock, self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, payload)
            row = cursor.fetchone()
            connection.commit()
        return row_to_dict(row) if row else {}

    def list(self, limit: int, offset: int) -> list[dict]:
        sql = f"SELECT {COLUMNS} FROM predictions ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, (limit, offset))
            rows = cursor.fetchall()
        return [row_to_dict(row) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            return int(cursor.fetchone()[0])


    def stats(self) -> dict:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(STATS_TOTAL)
            total, avg_confidence, last = cursor.fetchone()
            cursor.execute(STATS_STATE)
            by_state = dict(cursor.fetchall())
            cursor.execute(STATS_FRUIT)
            by_fruit = dict(cursor.fetchall())
        if hasattr(last, "isoformat"):
            last = last.astimezone(timezone.utc).isoformat(timespec="seconds")
        return {
            "total": int(total or 0),
            "avg_confidence": round(float(avg_confidence), 4) if avg_confidence is not None else None,
            "by_state": by_state,
            "by_fruit": by_fruit,
            "last_prediction_at": last,
        }

    def clear(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM predictions")
            deleted = cursor.rowcount
            connection.commit()
        return int(deleted or 0)

def build_repository(database_url: str) -> PostgresRepository:
    url = (database_url or "").strip()
    if url.startswith(("postgresql://", "postgres://", "postgresql+pg8000://")):
        normalized = url.replace("postgresql+pg8000://", "postgresql://", 1)
        return PostgresRepository(normalized)
    raise ValueError("DATABASE_URL no soportada. Usa postgresql://usuario:clave@host:5432/bd")