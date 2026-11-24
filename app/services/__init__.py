"""Punto de entrada de servicios."""

from .inference import InferenceError, get_inference_service, extract_thumbnail

__all__ = ["InferenceError", "get_inference_service", "extract_thumbnail"]
