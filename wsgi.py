"""Punto de entrada para Gunicorn en produccion."""

from app import create_app

app = create_app()
