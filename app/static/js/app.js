/* ============================================================
   FruitScan · lógica de captura, inferencia e historial
   ============================================================ */

(() => {
  "use strict";

  const els = {
    video: document.getElementById("video"),
    snapshot: document.getElementById("snapshot"),
    stage: document.getElementById("stage"),
    stageBadge: document.getElementById("stageBadge"),
    btnStart: document.getElementById("btnStart"),
    btnCapture: document.getElementById("btnCapture"),
    btnUpload: document.getElementById("btnUpload"),
    fileInput: document.getElementById("fileInput"),
    liveToggle: document.getElementById("liveToggle"),
    cameraHint: document.getElementById("cameraHint"),

    verdict: document.getElementById("verdict"),
    verdictState: document.getElementById("verdictState"),
    predLabel: document.getElementById("predLabel"),
    chipFruit: document.getElementById("chipFruit"),
    chipState: document.getElementById("chipState"),
    predConfidence: document.getElementById("predConfidence"),
    confidenceFill: document.getElementById("confidenceFill"),
    predTop3: document.getElementById("predTop3"),
    predLatency: document.getElementById("predLatency"),
    predTimestamp: document.getElementById("predTimestamp"),
    predSource: document.getElementById("predSource"),

    historyList: document.getElementById("historyList"),
    btnClear: document.getElementById("btnClear"),
    statTotal: document.getElementById("statTotal"),
    statAvg: document.getElementById("statAvg"),
    statFresh: document.getElementById("statFresh"),
    statRotten: document.getElementById("statRotten"),

    statusDot: document.getElementById("statusDot"),
    statusText: document.getElementById("statusText"),
    modelAccuracy: document.getElementById("modelAccuracy"),
    footerCount: document.getElementById("footerCount"),
    toast: document.getElementById("toast"),
  };

  const state = {
    stream: null,
    inFlight: false,
    liveTimer: null,
    lastCaptureAt: 0,
    analysisCount: 0,
  };

  const timeFormatter = new Intl.DateTimeFormat("es", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  /* ------------------------------------------------------------ utilidades */
  let toastTimer = null;
  function toast(message, kind) {
    els.toast.textContent = message;
    els.toast.classList.toggle("ok", kind === "ok");
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("show"), 3800);
  }

  function setStatus(kind, text) {
    els.statusDot.classList.remove("offline", "loading");
    if (kind === "offline") els.statusDot.classList.add("offline");
    if (kind === "loading") els.statusDot.classList.add("loading");
    els.statusText.textContent = text;
  }

  function pct(value) {
    return (value * 100).toFixed(1) + "%";
  }

  async function api(path, options) {
    const response = await fetch(path, options);
    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }
    if (!response.ok) {
      const message = (payload && payload.error) || "Error " + response.status;
      throw new Error(message);
    }
    return payload;
  }

  /* ------------------------------------------------------------ cámara */
  async function startCamera() {
    if (state.stream) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast("Este navegador no soporta captura de cámara. Usa 'Subir imagen'.");
      return;
    }
    try {
      els.btnStart.disabled = true;
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      state.stream = stream;
      els.video.srcObject = stream;
      await els.video.play().catch(() => {});
      els.video.classList.add("active");
      els.snapshot.hidden = true;
      els.stage.classList.add("has-frame");
      els.btnCapture.disabled = false;
      els.btnStart.textContent = "Cámara activa";
      els.cameraHint.textContent = "Cámara lista. Pulsa 'Analizar' o activa el modo en vivo.";
    } catch (error) {
      console.error(error);
      toast("No se pudo acceder a la cámara: " + error.message);
      els.btnStart.disabled = false;
    }
  }

  function stopCamera() {
    if (state.stream) {
      state.stream.getTracks().forEach((track) => track.stop());
      state.stream = null;
    }
    els.video.srcObject = null;
    els.video.classList.remove("active");
    els.btnStart.disabled = false;
    els.btnCapture.disabled = true;
    els.btnStart.innerHTML = els.btnStart.dataset.originalHtml;
    setLive(false);
  }

  function captureFrame() {
    const video = els.video;
    if (!video.videoWidth) return null;
    const canvas = document.createElement("canvas");
    const maxSide = 960;
    const scale = Math.min(1, maxSide / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
  }

  /* ------------------------------------------------------------ inferencia */
  async function analyzeBlob(blob, filename) {
    if (state.inFlight) return;
    state.inFlight = true;
    state.lastCaptureAt = Date.now();
    els.stageBadge.hidden = false;

    const form = new FormData();
    form.append("image", blob, filename || "captura.jpg");

    try {
      const payload = await api("/api/predict", { method: "POST", body: form });
      renderPrediction(payload.prediction, payload.record);
      prependHistory(payload.record);
      loadStats();
      state.analysisCount += 1;
      els.footerCount.textContent = state.analysisCount + " análisis en esta sesión";
    } catch (error) {
      console.error(error);
      toast(error.message);
    } finally {
      state.inFlight = false;
      els.stageBadge.hidden = true;
    }
  }

  function renderPrediction(prediction, record) {
    const isRotten = prediction.state === "rotten";
    els.verdict.classList.remove("is-fresh", "is-rotten");
    els.verdict.classList.add(isRotten ? "is-rotten" : "is-fresh");

    els.verdictState.textContent = isRotten ? "podrido" : "fresco";
    els.predLabel.textContent = prediction.display_label;
    els.chipFruit.textContent = "Fruta/verdura: " + prediction.fruit;
    els.chipState.textContent = "Estado: " + (isRotten ? "podrido" : "fresco");

    els.predConfidence.textContent = pct(prediction.confidence);
    els.confidenceFill.style.width = Math.max(2, prediction.confidence * 100) + "%";
    els.confidenceFill.classList.toggle("is-rotten", isRotten);

    els.predLatency.textContent = Math.round(prediction.latency_ms) + " ms";

    els.predTop3.innerHTML = "";
    prediction.top_k.forEach((item) => {
      const li = document.createElement("li");
      li.className = "topk-item";
      const name = document.createElement("span");
      name.textContent = item.display || item.label;
      const score = document.createElement("strong");
      score.textContent = pct(item.confidence);
      li.append(name, score);
      els.predTop3.appendChild(li);
    });

    const created = record && record.created_at ? new Date(record.created_at) : new Date();
    els.predTimestamp.textContent = timeFormatter.format(created);
    els.predSource.textContent = record ? record.filename : "cámara";
  }

  /* ------------------------------------------------------------ historial */
  function historyItem(record) {
    const li = document.createElement("li");
    li.className = "history-item";

    const img = document.createElement("img");
    img.className = "history-thumb";
    img.alt = record.display_label;
    img.src = record.thumbnail || "";
    img.loading = "lazy";

    const main = document.createElement("div");
    main.className = "history-main";
    const label = document.createElement("span");
    label.className = "history-label";
    label.textContent = record.display_label;
    const time = document.createElement("span");
    time.className = "history-time";
    const when = record.created_at ? new Date(record.created_at) : new Date();
    time.textContent = timeFormatter.format(when) + " · " + Math.round(record.latency_ms) + " ms";
    main.append(label, time);

    const score = document.createElement("span");
    score.className = "history-score" + (record.state === "rotten" ? " is-rotten" : "");
    score.textContent = pct(record.confidence);

    li.append(img, main, score);
    return li;
  }

  function prependHistory(record) {
    const empty = els.historyList.querySelector(".history-empty");
    if (empty) empty.remove();
    els.historyList.prepend(historyItem(record));
    while (els.historyList.children.length > 24) {
      els.historyList.lastElementChild.remove();
    }
  }

  async function loadHistory() {
    try {
      const payload = await api("/api/history?limit=24");
      els.historyList.innerHTML = "";
      if (!payload.items.length) {
        const empty = document.createElement("li");
        empty.className = "history-empty";
        empty.textContent = "Aún no hay inferencias registradas";
        els.historyList.appendChild(empty);
        return;
      }
      payload.items.forEach((record) => els.historyList.appendChild(historyItem(record)));
    } catch (error) {
      console.error(error);
    }
  }

  async function loadStats() {
    try {
      const stats = await api("/api/stats");
      els.statTotal.textContent = stats.total;
      els.statAvg.textContent = stats.avg_confidence === null ? "—" : pct(stats.avg_confidence);
      els.statFresh.textContent = stats.by_state.fresh || 0;
      els.statRotten.textContent = stats.by_state.rotten || 0;
      els.footerCount.textContent = stats.total + " inferencias registradas";
    } catch (error) {
      console.error(error);
    }
  }

  /* ------------------------------------------------------------ modo en vivo */
  function setLive(enabled) {
    els.liveToggle.checked = enabled;
    if (state.liveTimer) {
      clearInterval(state.liveTimer);
      state.liveTimer = null;
    }
    if (!enabled) return;
    if (!state.stream) {
      toast("Activa la cámara antes del modo en vivo.");
      els.liveToggle.checked = false;
      return;
    }
    state.liveTimer = setInterval(async () => {
      if (state.inFlight || document.hidden) return;
      const blob = await captureFrame();
      if (blob) analyzeBlob(blob, "live.jpg");
    }, 1200);
  }

  /* ------------------------------------------------------------ eventos */
  els.btnStart.addEventListener("click", () => {
    if (state.stream) stopCamera();
    else startCamera();
  });

  els.btnCapture.addEventListener("click", async () => {
    const blob = await captureFrame();
    if (blob) analyzeBlob(blob, "captura.jpg");
  });

  els.btnUpload.addEventListener("click", () => els.fileInput.click());

  els.fileInput.addEventListener("change", () => {
    const file = els.fileInput.files && els.fileInput.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    els.snapshot.src = url;
    els.snapshot.hidden = false;
    els.stage.classList.add("has-frame");
    els.video.classList.remove("active");
    analyzeBlob(file, file.name);
    els.fileInput.value = "";
  });

  els.liveToggle.addEventListener("change", () => setLive(els.liveToggle.checked));

  els.btnClear.addEventListener("click", async () => {
    if (!confirm("¿Borrar todo el historial de inferencias?")) return;
    try {
      await api("/api/history", { method: "DELETE" });
      await Promise.all([loadHistory(), loadStats()]);
      toast("Historial eliminado", "ok");
    } catch (error) {
      toast(error.message);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.code === "Space" && state.stream && document.activeElement === document.body) {
      event.preventDefault();
      els.btnCapture.click();
    }
  });

  /* ------------------------------------------------------------ arranque */
  async function init() {
    els.btnStart.dataset.originalHtml = els.btnStart.innerHTML;
    setStatus("loading", "conectando…");
    try {
      const health = await api("/api/health");
      if (health.model && health.model.metrics && health.model.metrics.test_acc != null) {
        els.modelAccuracy.textContent = "Modelo " + pct(health.model.metrics.test_acc) + " test";
      } else if (health.model && health.model.num_classes) {
        els.modelAccuracy.textContent = health.model.num_classes + " clases";
      } else {
        els.modelAccuracy.textContent = "modelo";
      }
      if (health.status === "ok") setStatus("ok", "en línea");
      else setStatus("offline", "revisar");
    } catch (error) {
      setStatus("offline", "sin conexión");
      toast("No se pudo contactar con el backend.");
    }
    await Promise.all([loadHistory(), loadStats()]);
  }

  window.addEventListener("beforeunload", () => {
    if (state.stream) state.stream.getTracks().forEach((track) => track.stop());
  });

  init();
})();
