# FruitScan – Clasificación de frescura de frutas y verduras

**Arquitectura:** Front‑End (HTML/CSS/JS + `getUserMedia` + canvas) → Flask (API + Gunicorn) → Modelo IA (MobileNetV3‑Small fine‑tuned, ONNX/TorchScript) → PostgreSQL (tabla `predictions`).

**Orquestación:** Docker Compose (servicios `app`, `db`, `adminer` opcional).

---

## 1. Arquitectura

```
Navegador (Front‑End)
  HTML5 + CSS3 + JS vanilla
  getUserMedia + canvas  ──> POST /api/predict (multipart/form-data)
                           │
                           ▼
Flask (Gunicorn)
  app/routes.py          │  inference.py (carga ONNX/TorchScript)
  app/services/inference.py
                           │
                           ▼
Modelo ONNX (ml/artifacts/model.onnx) o TorchScript (model.ts)
                           │
                           ▼
PostgreSQL 16          tabla: predictions (id, created_at, filename, label, display_label, fruit, state, confidence, top_k, latency_ms, thumbnail)
```

| Capa | Tecnología | Ubicación |
|---|---|---|
| Visualización / captura | HTML5, CSS3, JS (vanilla) | `app/templates`, `app/static` |
| Backend | Flask 3 + Gunicorn | `app/` |
| Modelo de IA | PyTorch (entrenamiento) + ONNX Runtime (servicio) | `ml/`, `app/services/inference.py` |
| Persistencia | PostgreSQL 16 + SQLAlchemy | `app/repository.py` |
| Orquestación | Docker + Docker Compose | `Dockerfile`, `docker-compose.yml` |

---

## 2. Dataset

- **30.357** imágenes organizadas en `Train/` y `Test/`, 9 frutas/verduras en estado fresco/podrido.
- Clases canónicas (18): `apples_fresh`, `apples_rotten`, `banana_fresh`, `banana_rotten`, `bittergourd_fresh`, `bittergourd_rotten`, `capsicum_fresh`, `capsicum_rotten`, `cucumber_fresh`, `cucumber_rotten`, `okra_fresh`, `okra_rotten`, `oranges_fresh`, `oranges_rotten`, `potato_fresh`, `potato_rotten`, `tomato_fresh`, `tomato_rotten`.
- **Problemas resueltos:** nombres inconsistentes, fuga de datos (4.040 imágenes de test idénticas a train), duplicados internos (7.287), clases ausentes en test, desbalance, resoluciones heterogéneas.
- Tras el pipeline: **23.070 imágenes únicas** con split estratificado 80/10/10 (train/val/test).
- Generar los splits: `py -3 ml/prepare_data.py --dataset dataset --output data`.

---

## 3. Modelo de IA y Transfer Learning

- **Arquitectura:** `MobileNetV3-Small` preentrenado en ImageNet (`IMAGENET1K_V1`).
- **Estrategia:** fine‑tuning completo con `CrossEntropyLoss(label_smoothing=0.1)` y `AdamW`.
- **Entrada:** tensor `1×3×192×192`, normalizado con media/desviación de ImageNet.
- **Aumentos:** `RandomResizedCrop`, flip horizontal, rotación ±15°, `ColorJitter`.
- **Balanceo:** `WeightedRandomSampler` con pesos inversos a la frecuencia de clase.
- **Regularización:** label smoothing, weight decay `1e-4`, early stopping (paciencia 4).
- **Exportación:** ONNX (opset 17) para servir sin PyTorch + TorchScript como respaldo.

Ejecutar entrenamiento:
```bash
py -3 ml/train.py --device cpu --epochs 10 --image-size 192 --workers 2
```
Artifacts generados en `ml/artifacts/`:
- `model.onnx` – para inferencia con ONNX Runtime.
- `model.ts` – respaldo TorchScript.
- `labels.json` – orden exacto de las 18 clases.
- `model_meta.json` – tamaño de entrada, normalización y backend.
- `metrics.json` – historial de epochs, accuracy y matriz de confusión.
- `curves.png` – curvas de pérdida y exactitud.
- `confusion_matrix.png` – matriz de confusión normalizada.
- `classification_report.txt` – precision / recall / F1 por clase.

**Resultados (ejecución real):** accuracy test 2.324 img: **98,41 %**; macro avg F1/Precisión/Recall: **0,976**.

---

## 4. API

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/health` | `GET` | Estado del servicio (200 si OK, 503 si modelo no cargado). |
| `/api/predict` | `POST` | Recibe `multipart/form-data` con campo `image`. Devuelve `{label, display_label, fruit, state, confidence, top_k, latency_ms}`. |
| `/api/history` | `GET` | Historial de predicciones guardadas en BD. |
| `/api/stats` | `GET` |Estadísticas generales (total, avg_confidence). |
| `/api/<path>` | `GET` | 404 con JSON `{"error": "not found"}`. |

Para probar sin modelo:
```bash
curl http://localhost:5000/api/health
# {"status":"degraded","model":{"error":"No hay model.onnx ni model.ts"}}
```

---

## 5. Instalación

### 5.1 Con Docker (recomendado)

```bash
# 1. Clonar o entrar al proyecto
cd trabajoRico

# 2. Copiar .env y ajustar (opcional)
Copy-Item .env.example .env   # edita SECRET_KEY y credenciales si es necesario

# 3. Levantar los servicios
docker compose up --build
```
- **App:** http://localhost:5000
- **PostgreSQL:** servicio `db` (puerto interno 5432). Volumen `pgdata`.
- **Adminer (opcional):** `docker compose --profile tools up --build` → http://localhost:8080.

Para detener y borrar volumen:
```bash
docker compose down -v
```

### 5.2 Instalación local (sin Docker)

```bash
# 1. Entorno virtual
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip

# 2. Dependencias
pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install -r ml/requirements.txt

# 3. Dataset y modelo
py -3 ml/prepare_data.py --dataset dataset --output data
py -3 ml/train.py --device cpu --epochs 10 --image-size 192

# 4. Servidor (usa SQLite si no defines DATABASE_URL)
py -3 run.py
```
Abre http://localhost:5000. Para PostgreSQL en local:
```bash
set DATABASE_URL=postgresql://fruitscan:fruitscan@localhost:5432/fruitscan
```

---

## 6. Mapeo contra la rúbrica

| Criterio (peso) | Dónde se cumple |
|---|---|
| **Dataset (10 %)** | `ml/prepare_data.py` – normalización, deduplicación, split estratificado |
| **Modelo IA / Transfer Learning (20 %)** | `ml/train.py`, `ml/artifacts/*.png`, `metrics.json` |
| **Backend y API (20 %)** | `app/routes.py`, `app/services/inference.py`, `app/__init__.py` |
| **UI, captura y visualización (20 %)** | `app/templates/index.html`, `app/static/*`, `/api/predict` |
| **Persistencia (15 %)** | `app/models.py`, PostgreSQL en `docker-compose.yml` |
| **Dockerización (15 %)** | `Dockerfile`, `docker-compose.yml`, `.env.example` |
| **Informe y repositorio** | Este README + `ml/artifacts/` con métricas |

---

## 7. Limitaciones y trabajo futuro

- El dataset original mezcla resoluciones y estilos; la confianza puede bajar con fotos muy distintas a la distribución de entrenamiento.
- La decisión *fresco/podrido* es binaria por clase; no mide grado de madurez.
- Posibles mejoras: Grad‑CAM para explicabilidad, cuantización INT8 para reducir latencia, autenticación en la API y despliegue con HTTPS.

---

## 8. Capturas (artifacts)

| Archivo | Contenido |
|---|---|
| `ml/artifacts/curves.png` | Curvas de pérdida y exactitud por epoch |
| `ml/artifacts/confusion_matrix.png` | Matriz de confusión normalizada (18 × 18) |
| `ml/artifacts/classification_report.txt` | Precision / recall / F1 por cada una de las 18 clases |
| `ml/artifacts/metrics.json` | Mejor val‑accuracy, test accuracy, epochs, tiempo de entrenamiento |

---

## 9. Ejecutar la demo en vivo

1. Asegúrate de que el contenedor `app` esté corriendo (`docker compose up --build`).
2. Abre http://localhost:5000 en el navegador.
3. concede permiso de cámara cuando el navegador lo solicite.
4. Apunta a una fruta/verdura sobre la cámara o carga una imagen desde disco.
5. La predicción aparecerá al instante con etiqueta, confianza y top‑3.

**Para la presentación:** tener a mano 2‑3 imágenes de respaldo por clase (guardadas localmente) por si la cámara falla.

---

## 10. Pruebas automatizadas

```bash
py -3 -m pytest tests/
```
Cubren: health degradado cuando falta modelo, predict sin archivo (400), formato no permitido (415), histogram vacío, stats vacío, ruta API desconocida (404).

---

*Generado automáticamente a partir de la estructura del proyecto y la rúbrica de evaluación.*