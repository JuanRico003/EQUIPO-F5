# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

# curl se usa en el healthcheck; pg8000 es un driver puro Python (sin libpq).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.9.1"
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ml/artifacts ./ml/artifacts
COPY wsgi.py run.py ./

# Usuario sin privilegios
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=20s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:5000/api/health > /dev/null || exit 1

# Un worker con varios hilos: el modelo ONNX se carga una sola vez en memoria.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "90", "--access-logfile", "-", "wsgi:app"]
