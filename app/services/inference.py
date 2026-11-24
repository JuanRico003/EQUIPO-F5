"""Servicio de inferencia.

Carga el modelo exportado (ONNX por defecto, TorchScript como respaldo) y
expone un unico metodo `predict()` que recibe una imagen PIL y devuelve la
prediccion con etiqueta, confianza y top-3.
"""

from __future__ import annotations

import io
import json
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image

_IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class InferenceError(RuntimeError):
    """Error controlado de inferencia (modelo ausente o imagen invalida)."""


class InferenceService:
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = Path(artifacts_dir)
        self.labels: list[dict] = []
        self.meta: dict = {}
        self.metrics: dict = {}
        self._session = None
        self._torch_model = None
        self._backend = None
        self._lock = threading.Lock()
        self.load()

    # ------------------------------------------------------------------ carga
    def load(self) -> None:
        labels_path = self.artifacts_dir / "labels.json"
        meta_path = self.artifacts_dir / "model_meta.json"
        if not labels_path.exists():
            raise InferenceError(
                f"No se encontro {labels_path}. Ejecuta primero: py -3 ml/train.py"
            )
        self.labels = json.loads(labels_path.read_text(encoding="utf-8"))
        self.meta = (
            json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        )
        metrics_path = self.artifacts_dir / "metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.metrics = {
                "test_acc": metrics.get("test_acc"),
                "test_samples": metrics.get("test_samples"),
                "best_epoch": metrics.get("best_epoch"),
                "trained_at": self.meta.get("trained_at"),
            }

        onnx_path = self.artifacts_dir / "model.onnx"
        if onnx_path.exists():
            import onnxruntime as ort

            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            self._session = ort.InferenceSession(
                str(onnx_path),
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            self._backend = "onnx"
            return

        ts_path = self.artifacts_dir / "model.ts"
        if ts_path.exists():
            import torch

            self._torch_model = torch.jit.load(str(ts_path), map_location="cpu")
            self._torch_model.eval()
            self._backend = "torchscript"
            return

        raise InferenceError("No hay model.onnx ni model.ts en los artefactos.")

    # -------------------------------------------------------------- preproceso
    @property
    def image_size(self) -> int:
        return int(self.meta.get("image_size", 224))

    def preprocess(self, image: Image.Image) -> np.ndarray:
        image = image.convert("RGB")
        size = self.image_size
        # Resize del lado corto + center crop, igual que en validacion.
        resize_to = int(size * 1.14)
        width, height = image.size
        if width < height:
            new_width, new_height = resize_to, max(1, round(height * resize_to / width))
        else:
            new_height, new_width = resize_to, max(1, round(width * resize_to / height))
        image = image.resize((new_width, new_height), Image.BILINEAR)

        left = (new_width - size) // 2
        top = (new_height - size) // 2
        image = image.crop((left, top, left + size, top + size))

        array = np.asarray(image, dtype=np.float32) / 255.0
        array = (array - _IMAGENET_MEAN) / _IMAGENET_STD
        return np.transpose(array, (2, 0, 1))[None, ...].astype(np.float32)

    # ------------------------------------------------------------------ inferencia
    def _forward(self, batch: np.ndarray) -> np.ndarray:
        if self._backend == "onnx":
            outputs = self._session.run(["logits"], {"input": batch})[0]
        else:
            import torch

            with torch.no_grad():
                outputs = self._torch_model(torch.from_numpy(batch)).numpy()
        return np.asarray(outputs, dtype=np.float32)

    def predict(self, image: Image.Image, top_k: int = 3) -> dict:
        if not self.labels:
            raise InferenceError("El modelo no tiene etiquetas cargadas.")

        with self._lock:
            batch = self.preprocess(image)
            started = time.perf_counter()
            logits = self._forward(batch)
            latency_ms = (time.perf_counter() - started) * 1000.0

        logits = logits[0]
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()

        order = np.argsort(probabilities)[::-1][:top_k]
        top = [
            {
                "label": self.labels[index]["label"],
                "display": self.labels[index]["display"],
                "confidence": float(probabilities[index]),
            }
            for index in order
        ]
        best = top[0]
        entry = self.labels[order[0]]

        return {
            "label": best["label"],
            "display_label": best["display"],
            "fruit": entry["fruit"],
            "state": entry["state"],
            "confidence": best["confidence"],
            "top_k": top,
            "latency_ms": latency_ms,
        }

    # ------------------------------------------------------------------ metadatos
    def health(self) -> dict:
        return {
            "backend": self._backend,
            "num_classes": len(self.labels),
            "image_size": self.image_size,
            "metrics": self.metrics,
        }

    def label_catalog(self) -> list[dict]:
        return [
            {
                "label": item["label"],
                "display": item["display"],
                "fruit": item["fruit"],
                "state": item["state"],
            }
            for item in self.labels
        ]


def extract_thumbnail(image: Image.Image, size: int = 96) -> str:
    """Devuelve un data-URI JPEG pequeno para el historial."""
    import base64

    thumb = image.convert("RGB")
    thumb.thumbnail((size, size))
    buffer = io.BytesIO()
    thumb.save(buffer, format="JPEG", quality=70)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


_service: InferenceService | None = None
_service_lock = threading.Lock()


def get_inference_service(artifacts_dir: Path) -> InferenceService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = InferenceService(artifacts_dir)
    return _service
