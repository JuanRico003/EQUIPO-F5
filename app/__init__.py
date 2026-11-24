"""Application factory."""

from __future__ import annotations

import logging
import time

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from .config import Config
from .repository import build_repository


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    repository = build_repository(app.config["DATABASE_URL"])
    app.extensions["repository"] = repository

    from .routes import api, main

    app.register_blueprint(main)
    app.register_blueprint(api)

    _init_database(app, repository)
    _register_error_handlers(app)

    with app.app_context():
        app.logger.info("Base de datos: %s", type(repository).__name__)
        app.logger.info("Artefactos: %s", app.config["ARTIFACTS_DIR"])

    return app


def _init_database(app: Flask, repository, attempts: int = 30, delay: float = 1.5) -> None:
    """Espera a que PostgreSQL responda e inicializa las tablas."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            repository.init()
            return
        except Exception as exc:  # pragma: no cover - depende del entorno
            last_error = exc
            app.logger.warning("BD no disponible (intento %s/%s): %s", attempt, attempts, exc)
            time.sleep(delay)
    app.logger.error("No se pudo inicializar la base de datos: %s", last_error)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(413)
    def too_large(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "La imagen supera el tamano maximo permitido."}), 413
        return "Archivo demasiado grande", 413

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Ruta no encontrada."}), 404
        return "No encontrado", 404

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def unhandled(error: Exception):  # pragma: no cover
        app.logger.exception("Error no controlado: %s", error)
        return jsonify({"error": "Error interno del servidor."}), 500