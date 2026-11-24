"""Tests de la API usando un repositorio en memoria y sin modelo cargado."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.config import Config

class FakeRepository:
    def __init__(self):
        self.rows: list[dict] = []

    def init(self) -> None:
        pass

    def ping(self) -> bool:
        return True

    def insert(self, record: dict) -> dict:
        item = {"id": len(self.rows) + 1, **record}
        self.rows.append(item)
        return item

    def list(self, limit: int, offset: int) -> list[dict]:
        return list(reversed(self.rows))[offset : offset + limit]

    def count(self) -> int:
        return len(self.rows)

    def stats(self) -> dict:
        total = len(self.rows)
        avg = round(sum(r["confidence"] for r in self.rows) / total, 4) if total else None
        return {
            "total": total,
            "avg_confidence": avg,
            "by_state": {},
            "by_fruit": {},
            "last_prediction_at": self.rows[-1]["created_at"] if total else None,
        }

    def clear(self) -> int:
        deleted = len(self.rows)
        self.rows.clear()
        return deleted

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.build_repository", lambda _url: FakeRepository())

    class TestConfig(Config):
        TESTING = True
        ARTIFACTS_DIR = tmp_path / "artefactos_inexistentes"

    app = create_app(TestConfig)
    with app.test_client() as test_client:
        yield test_client

def test_health_responde_aunque_falte_el_modelo(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "degraded"
    assert payload["database"] == "ok"
    assert "error" in payload["model"]

def test_predict_sin_archivo_devuelve_400(client):
    response = client.post("/api/predict", data={})
    assert response.status_code == 400
    assert "image" in response.get_json()["error"]

def test_predict_formato_no_permitido_devuelve_415(client):
    data = {"image": (io.BytesIO(b"texto plano"), "nota.txt")}
    response = client.post("/api/predict", data=data, content_type="multipart/form-data")
    assert response.status_code == 415

def test_historial_vacio(client):
    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.get_json()["items"] == []
    assert response.get_json()["total"] == 0

def test_stats_vacio(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 0
    assert payload["avg_confidence"] is None

def test_ruta_api_desconocida_devuelve_json(client):
    response = client.get("/api/no-existe")
    assert response.status_code == 404
    assert "error" in response.get_json()