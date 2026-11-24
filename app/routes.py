"""Blueprint de la API y ruta de la interfaz."""

from __future__ import annotations

import io
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request
from PIL import Image, UnidentifiedImageError

from .repository import utcnow_iso
from .services import InferenceError, extract_thumbnail, get_inference_service

main = Blueprint("main", __name__)
api = Blueprint("api", __name__, url_prefix="/api")


def _repo():
    return current_app.extensions["repository"]


def _inference():
    return get_inference_service(Path(current_app.config["ARTIFACTS_DIR"]))


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


@main.get("/")
def index():
    return render_template("index.html")


@api.get("/health")
def health():
    payload = {"status": "ok", "database": "ok"}
    try:
        _repo().ping()
    except Exception as exc:  # pragma: no cover - depende del entorno
        payload["database"] = f"error: {exc}"
        payload["status"] = "degraded"
    try:
        payload["model"] = _inference().health()
    except InferenceError as exc:
        payload["model"] = {"error": str(exc)}
        payload["status"] = "degraded"
    return jsonify(payload)


@api.get("/labels")
def labels():
    try:
        return jsonify({"labels": _inference().label_catalog()})
    except InferenceError as exc:
        return jsonify({"error": str(exc)}), 503


@api.post("/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"error": "Falta el archivo 'image' en el formulario."}), 400

    uploaded = request.files["image"]
    if not uploaded or uploaded.filename == "":
        return jsonify({"error": "Archivo vacio."}), 400
    if not _allowed(uploaded.filename):
        return jsonify({"error": "Formato no permitido. Usa PNG, JPG, WEBP o BMP."}), 415

    raw = uploaded.read()
    if not raw:
        return jsonify({"error": "El archivo no tiene contenido."}), 400

    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "No se pudo decodificar la imagen."}), 400

    try:
        result = _inference().predict(image)
    except InferenceError as exc:
        return jsonify({"error": str(exc)}), 503

    try:
        record = _repo().insert(
            {
                "created_at": utcnow_iso(),
                "filename": uploaded.filename[:255],
                "label": result["label"],
                "display_label": result["display_label"],
                "fruit": result["fruit"],
                "state": result["state"],
                "confidence": result["confidence"],
                "top_k": result["top_k"],
                "latency_ms": result["latency_ms"],
                "thumbnail": extract_thumbnail(image),
            }
        )
    except Exception as exc:  # pragma: no cover - depende del entorno
        current_app.logger.exception("No se pudo guardar la prediccion")
        return jsonify({"error": f"No se pudo guardar en la base de datos: {exc}"}), 503

    return jsonify({"prediction": result, "record": record}), 200


@api.get("/history")
def history():
    try:
        limit = int(request.args.get("limit", current_app.config["HISTORY_DEFAULT_LIMIT"]))
    except ValueError:
        limit = current_app.config["HISTORY_DEFAULT_LIMIT"]
    limit = max(1, min(limit, current_app.config["HISTORY_MAX_LIMIT"]))
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0

    try:
        items = _repo().list(limit, offset)
        total = _repo().count()
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Error leyendo el historial")
        return jsonify({"error": f"No se pudo leer el historial: {exc}"}), 503

    return jsonify({"items": items, "total": total})


@api.get("/stats")
def stats():
    try:
        payload = _repo().stats()
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Error calculando estadisticas")
        return jsonify({"error": f"No se pudieron calcular las estadisticas: {exc}"}), 503
    return jsonify(payload)


@api.delete("/history")
def clear_history():
    try:
        deleted = _repo().clear()
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Error borrando historial")
        return jsonify({"error": f"No se pudo borrar el historial: {exc}"}), 503
    return jsonify({"deleted": deleted})
