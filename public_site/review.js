(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const LABEL_STORAGE_KEY = "jupiterPublicReviewLabels";
  const REVIEWER_STORAGE_KEY = "jupiterReviewerName";
  const LABEL_FIELDS = [
    "candidate_id", "image_id", "run_date", "x", "y",
    "jupiter_latitude", "jupiter_longitude", "geometry_status", "geometry_group_id", "geometry_group_size",
    "snr", "blob_size", "candidate_score", "artifact_flags",
    "reviewer_label", "human_label", "label", "reviewer", "notes",
    "review_note", "timestamp", "reviewed_at", "sheet_status", "source"
  ];
  const LABEL_OPTIONS = [
    ["", "Choose a label"],
    ["known-lightning", "Known Lightning"],
    ["possible-lightning", "Possible Lightning"],
    ["artifact", "Artifact"],
    ["cosmic-ray-hot-pixel", "Cosmic Ray / Hot Pixel"],
    ["uncertain", "Uncertain"]
  ];

  const reviewState = {
    rows: [],
    selected: null,
    labels: readLocalLabels(),
    reviewer: localStorage.getItem(REVIEWER_STORAGE_KEY) || "",
    collaboration: {},
    geometry: {},
    filter: "all"
  };

  function readLocalLabels() {
    try {
      return JSON.parse(localStorage.getItem(LABEL_STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[character]);
  }

  function toNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function normalizeOptionalNumber(value) {
    return value === "" || value === null || value === undefined ? "" : toNumber(value, "");
  }

  function normalizeRow(row) {
    return {
      ...row,
      review_order: toNumber(row.review_order),
      x: toNumber(row.x),
      y: toNumber(row.y),
      snr: toNumber(row.snr),
      blob_size: toNumber(row.blob_size),
      frame_count: toNumber(row.frame_count),
      candidate_score: toNumber(row.candidate_score),
      jupiter_latitude: normalizeOptionalNumber(row.jupiter_latitude),
      jupiter_longitude: normalizeOptionalNumber(row.jupiter_longitude),
      geometry_group_size: normalizeOptionalNumber(row.geometry_group_size),
      image_subobserver_lat: normalizeOptionalNumber(row.image_subobserver_lat),
      image_subobserver_lon_w: normalizeOptionalNumber(row.image_subobserver_lon_w),
      image_center_resolution_km_px: normalizeOptionalNumber(row.image_center_resolution_km_px),
      image_center_phase_angle: normalizeOptionalNumber(row.image_center_phase_angle),
      geometry_status: row.geometry_status || "pending-backplane"
    };
  }

  function savedLabel(candidateId) {
    return reviewState.labels[candidateId] || {};
  }

  function writeLocalLabels() {
    localStorage.setItem(LABEL_STORAGE_KEY, JSON.stringify(reviewState.labels));
    renderProgress();
  }

  function filteredRows() {
    if (reviewState.filter === "unlabeled") {
      return reviewState.rows.filter((row) => !savedLabel(row.candidate_id).reviewer_label);
    }
    if (reviewState.filter === "labeled") {
      return reviewState.rows.filter((row) => savedLabel(row.candidate_id).reviewer_label);
    }
    if (reviewState.filter === "01_known_validation_positive") {
      return reviewState.rows.filter((row) => row.review_batch === reviewState.filter);
    }
    return reviewState.rows;
  }

  function renderProgress() {
    const total = reviewState.rows.length;
    const labels = Object.values(reviewState.labels).filter((row) => reviewState.rows.some((candidate) => candidate.candidate_id === row.candidate_id));
    const submitted = labels.filter((row) => row.sheet_status === "submitted" || row.sheet_status === "confirmed").length;
    const percent = total ? Math.round(labels.length / total * 100) : 0;
    byId("review-progress-copy").textContent = `${labels.length} of ${total} candidates labeled (${percent}%). ${submitted} submitted to the shared Sheet.`;
    byId("review-progress-fill").style.width = `${percent}%`;
  }

  function renderCandidateList() {
    const rows = filteredRows();
    const list = byId("first-pass-candidate-list");
    if (!rows.length) {
      list.innerHTML = "<p>No candidates match this filter.</p>";
      return;
    }
    list.innerHTML = rows.map((row) => {
      const label = savedLabel(row.candidate_id).reviewer_label;
      return `
        <button type="button" class="candidate-button ${reviewState.selected?.candidate_id === row.candidate_id ? "active" : ""}" data-first-pass-id="${escapeHtml(row.candidate_id)}">
          <b>#${row.review_order} ${escapeHtml(row.candidate_id)} ${label ? `<span class="saved-pill">${escapeHtml(label)}</span>` : ""}</b>
          <span>${escapeHtml(row.image_id)} | ${escapeHtml(row.run_date)} | score ${row.candidate_score.toFixed(3)}</span>
          <small>${escapeHtml(row.review_batch)} | SNR ${row.snr.toFixed(2)} | ${row.blob_size} px</small>
        </button>`;
    }).join("");
    list.querySelectorAll("[data-first-pass-id]").forEach((button) => {
      button.addEventListener("click", () => selectCandidate(button.dataset.firstPassId));
    });
  }

  function optionHtml(selected) {
    return LABEL_OPTIONS.map(([value, text]) => (
      `<option value="${value}" ${value === selected ? "selected" : ""}>${text}</option>`
    )).join("");
  }

  function geometryValue(value) {
    return value === "" ? "pending" : Number(value).toFixed(3);
  }

  function percentileFromHistogram(histogram, count, percentile) {
    const target = count * percentile / 100;
    let cumulative = 0;
    for (let index = 0; index < histogram.length; index += 1) {
      cumulative += histogram[index];
      if (cumulative >= target) return index;
    }
    return 255;
  }

  function drawReviewInspector(image, row) {
    const contextCanvas = byId("review-context-canvas");
    const cropCanvas = byId("review-stretch-canvas");
    if (!contextCanvas || !cropCanvas) return;
    const cropRequested = Number(byId("review-crop-size").value);
    const cropSize = Math.min(cropRequested, image.naturalWidth, image.naturalHeight);
    const x0 = Math.max(0, Math.min(image.naturalWidth - cropSize, row.x - cropSize / 2));
    const y0 = Math.max(0, Math.min(image.naturalHeight - cropSize, row.y - cropSize / 2));

    const contextWidth = 360;
    const contextHeight = Math.max(1, Math.round(contextWidth * image.naturalHeight / image.naturalWidth));
    contextCanvas.width = contextWidth;
    contextCanvas.height = contextHeight;
    const context = contextCanvas.getContext("2d");
    context.drawImage(image, 0, 0, contextWidth, contextHeight);
    const scaleX = contextWidth / image.naturalWidth;
    const scaleY = contextHeight / image.naturalHeight;
    context.strokeStyle = "#a52d25";
    context.lineWidth = 2;
    context.strokeRect(x0 * scaleX, y0 * scaleY, cropSize * scaleX, cropSize * scaleY);
    context.beginPath();
    context.arc(row.x * scaleX, row.y * scaleY, 5, 0, Math.PI * 2);
    context.stroke();

    const source = document.createElement("canvas");
    source.width = cropSize;
    source.height = cropSize;
    const sourceContext = source.getContext("2d", {willReadFrequently: true});
    sourceContext.drawImage(image, x0, y0, cropSize, cropSize, 0, 0, cropSize, cropSize);
    const pixels = sourceContext.getImageData(0, 0, cropSize, cropSize);
    const histogram = new Uint32Array(256);
    for (let index = 0; index < pixels.data.length; index += 4) {
      const luminance = Math.round(
        pixels.data[index] * 0.2126
        + pixels.data[index + 1] * 0.7152
        + pixels.data[index + 2] * 0.0722
      );
      histogram[luminance] += 1;
    }
    const lowPercent = Number(byId("review-black-point").value);
    const highPercent = Number(byId("review-white-point").value);
    const gamma = Number(byId("review-gamma").value);
    const black = percentileFromHistogram(histogram, cropSize * cropSize, lowPercent);
    const white = Math.max(black + 1, percentileFromHistogram(histogram, cropSize * cropSize, highPercent));
    for (let index = 0; index < pixels.data.length; index += 4) {
      const luminance = (
        pixels.data[index] * 0.2126
        + pixels.data[index + 1] * 0.7152
        + pixels.data[index + 2] * 0.0722
      );
      const normalized = Math.max(0, Math.min(1, (luminance - black) / (white - black)));
      const adjusted = Math.round(255 * Math.pow(normalized, 1 / gamma));
      pixels.data[index] = adjusted;
      pixels.data[index + 1] = adjusted;
      pixels.data[index + 2] = adjusted;
      pixels.data[index + 3] = 255;
    }
    sourceContext.putImageData(pixels, 0, 0);
    sourceContext.strokeStyle = "#a52d25";
    sourceContext.lineWidth = Math.max(2, cropSize / 128);
    sourceContext.beginPath();
    sourceContext.arc(row.x - x0, row.y - y0, Math.max(7, cropSize / 35), 0, Math.PI * 2);
    sourceContext.stroke();

    const outputScale = Number(byId("review-output-scale").value);
    cropCanvas.width = Math.max(1, Math.round(cropSize * outputScale));
    cropCanvas.height = cropCanvas.width;
    const cropContext = cropCanvas.getContext("2d");
    cropContext.imageSmoothingEnabled = false;
    cropContext.drawImage(source, 0, 0, cropCanvas.width, cropCanvas.height);
    byId("review-black-output").textContent = `${lowPercent.toFixed(1)}%`;
    byId("review-white-output").textContent = `${highPercent.toFixed(1)}%`;
    byId("review-gamma-output").textContent = gamma.toFixed(1);
  }

  async function setupReviewInspector(row) {
    if (!row.preview_url) return;
    const image = new Image();
    image.src = row.preview_url;
    await image.decode();
    const render = () => drawReviewInspector(image, row);
    ["review-output-scale", "review-crop-size", "review-black-point", "review-white-point", "review-gamma"]
      .forEach((id) => byId(id).addEventListener("input", render));
    byId("review-reset-stretch").addEventListener("click", () => {
      byId("review-output-scale").value = "1";
      byId("review-crop-size").value = "256";
      byId("review-black-point").value = "2";
      byId("review-white-point").value = "99.8";
      byId("review-gamma").value = "1";
      render();
    });
    render();
  }

  function renderCandidateDetail() {
    const detail = byId("first-pass-candidate-detail");
    const row = reviewState.selected;
    if (!row) {
      detail.innerHTML = "<p>Select a candidate to review.</p>";
      return;
    }
    const saved = savedLabel(row.candidate_id);
    const imageContext = row.image_subobserver_lat === ""
      ? "not available"
      : `${Number(row.image_subobserver_lat).toFixed(3)} deg lat, ${Number(row.image_subobserver_lon_w).toFixed(3)} deg W lon`;
    detail.innerHTML = `
      <p class="section-label">Candidate detail</p>
      <div>
        <h3>${escapeHtml(row.candidate_id)}</h3>
        <p>${escapeHtml(row.reviewer_task || "Review this detector candidate.")}</p>
        <p><b>What to check:</b> Is the feature multi-pixel and diffuse? Does it look like a streak, edge, hot pixel, or cosmic-ray hit? Is it repeated in a nearby frame?</p>
      </div>
      <div class="review-inspector">
        <div class="inspector-images">
          <figure>
            <figcaption>Full frame source context</figcaption>
            <canvas id="review-context-canvas"></canvas>
          </figure>
          <figure>
            <figcaption>Stretched candidate crop</figcaption>
            <canvas id="review-stretch-canvas"></canvas>
          </figure>
        </div>
        <div class="inspector-controls">
          <label>Output size
            <select id="review-output-scale">
              <option value="1" selected>100%</option>
              <option value="0.75">75%</option>
              <option value="0.5">50%</option>
              <option value="0.25">25%</option>
            </select>
          </label>
          <label>Inspection crop
            <select id="review-crop-size">
              <option value="1024">Full frame</option>
              <option value="512">512 x 512</option>
              <option value="256" selected>256 x 256</option>
              <option value="128">128 x 128</option>
            </select>
          </label>
          <label>Black point <output id="review-black-output">2.0%</output>
            <input id="review-black-point" type="range" min="0" max="20" step="0.5" value="2">
          </label>
          <label>White point <output id="review-white-output">99.8%</output>
            <input id="review-white-point" type="range" min="90" max="100" step="0.1" value="99.8">
          </label>
          <label>Midtone lift <output id="review-gamma-output">1.0</output>
            <input id="review-gamma" type="range" min="0.4" max="2.5" step="0.1" value="1">
          </label>
          <button type="button" id="review-reset-stretch">Reset stretch</button>
        </div>
        <p class="inspector-note">This interactive view stretches the hosted OPUS browse preview for visual review. Detector measurements come from the calibrated image product.</p>
      </div>
      <div class="detail-grid">
        <div><b>Image</b>${escapeHtml(row.image_id)}</div>
        <div><b>OPUS source</b>${row.opus_detail_url ? `<a href="${escapeHtml(row.opus_detail_url)}" target="_blank" rel="noreferrer">${escapeHtml(row.opus_id)}</a>` : "n/a"}</div>
        <div><b>UTC timestamp</b>${escapeHtml(row.timestamp_utc || "n/a")}</div>
        <div><b>Exposure</b>${escapeHtml(row.exposure_seconds || "n/a")} s</div>
        <div><b>Camera / filter</b>${escapeHtml(row.camera || "n/a")} / ${escapeHtml(row.filter_name || "n/a")}</div>
        <div><b>Date</b>${escapeHtml(row.run_date)}</div>
        <div><b>Image x/y</b>${row.x.toFixed(2)}, ${row.y.toFixed(2)}</div>
        <div><b>Peak SNR</b>${row.snr.toFixed(2)}</div>
        <div><b>Blob size</b>${row.blob_size} px</div>
        <div><b>Priority score</b>${row.candidate_score.toFixed(4)}</div>
        <div><b>Frames linked</b>${row.frame_count || "1"}</div>
        <div><b>Artifact flags</b>${escapeHtml(row.artifact_flags || "none")}</div>
        <div><b>Review batch</b>${escapeHtml(row.review_batch)}</div>
        <div><b>Jupiter latitude</b>${geometryValue(row.jupiter_latitude)}</div>
        <div><b>Jupiter longitude</b>${geometryValue(row.jupiter_longitude)}</div>
        <div><b>Surface group</b>${escapeHtml(row.geometry_group_id || "not grouped")}${row.geometry_group_size === "" ? "" : ` (${row.geometry_group_size} candidate${row.geometry_group_size === 1 ? "" : "s"})`}</div>
        <div><b>Geometry status</b>${escapeHtml(row.geometry_status)}</div>
        <div><b>Image viewing center</b>${escapeHtml(imageContext)}</div>
        <div><b>Image resolution</b>${row.image_center_resolution_km_px === "" ? "n/a" : `${Number(row.image_center_resolution_km_px).toFixed(2)} km/px`}</div>
        <div><b>Phase angle</b>${row.image_center_phase_angle === "" ? "n/a" : `${Number(row.image_center_phase_angle).toFixed(2)} deg`}</div>
      </div>
      <form class="first-pass-label-form" id="first-pass-label-form">
        <div class="label-row">
          <label>Reviewer label
            <select id="first-pass-label">${optionHtml(saved.reviewer_label || "")}</select>
          </label>
          <label>Reviewer name or initials
            <input id="first-pass-reviewer" type="text" value="${escapeHtml(saved.reviewer || reviewState.reviewer)}" placeholder="name or initials">
          </label>
        </div>
        <label>Review notes
          <textarea id="first-pass-notes" placeholder="${escapeHtml(row.review_note_prompt || "Why keep or reject this candidate?")}">${escapeHtml(saved.notes || saved.review_note || "")}</textarea>
        </label>
        <button type="submit" class="primary">Save label</button>
        <div class="save-result" id="first-pass-save-result">${escapeHtml(saved.save_message || "")}</div>
      </form>`;
    byId("first-pass-label-form").addEventListener("submit", (event) => {
      event.preventDefault();
      saveCandidate(row);
    });
    setupReviewInspector(row).catch((error) => {
      const note = detail.querySelector(".inspector-note");
      if (note) note.textContent = `Preview could not be loaded: ${error.message}`;
    });
  }

  function selectCandidate(candidateId) {
    reviewState.selected = reviewState.rows.find((row) => row.candidate_id === candidateId) || filteredRows()[0] || null;
    renderCandidateList();
    renderCandidateDetail();
  }

  function labelPayload(row) {
    const reviewerLabel = byId("first-pass-label").value;
    const reviewer = byId("first-pass-reviewer").value.trim() || "anonymous-reviewer";
    const notes = byId("first-pass-notes").value.trim();
    const now = new Date().toISOString();
    return {
      candidate_id: row.candidate_id,
      image_id: row.image_id,
      run_date: row.run_date,
      x: row.x.toFixed(2),
      y: row.y.toFixed(2),
      jupiter_latitude: row.jupiter_latitude === "" ? "" : String(row.jupiter_latitude),
      jupiter_longitude: row.jupiter_longitude === "" ? "" : String(row.jupiter_longitude),
      geometry_status: row.geometry_status,
      geometry_group_id: row.geometry_group_id || "",
      geometry_group_size: row.geometry_group_size === "" ? "" : String(row.geometry_group_size),
      snr: row.snr.toFixed(2),
      blob_size: row.blob_size,
      candidate_score: row.candidate_score.toFixed(4),
      artifact_flags: row.artifact_flags || "",
      reviewer_label: reviewerLabel,
      human_label: reviewerLabel,
      label: reviewerLabel,
      reviewer,
      notes,
      review_note: notes,
      timestamp: now,
      reviewed_at: now,
      sheet_status: "local-only",
      source: window.JupiterWorkbench?.backendAvailable ? "local-python-workbench" : "public-vercel-review"
    };
  }

  async function saveToLocalBackend(payload) {
    if (!window.JupiterWorkbench?.backendAvailable) return false;
    const response = await fetch("/api/candidate-label", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`local label API returned ${response.status}`);
    return true;
  }

  async function submitToSheet(payload) {
    const endpoint = reviewState.collaboration.apps_script_endpoint;
    if (!endpoint) return false;
    await fetch(endpoint, {
      method: "POST",
      mode: "no-cors",
      headers: {"Content-Type": "text/plain;charset=utf-8"},
      body: JSON.stringify(payload)
    });
    return true;
  }

  async function saveCandidate(row) {
    const payload = labelPayload(row);
    if (!payload.reviewer_label) {
      byId("first-pass-save-result").textContent = "Choose a label before saving.";
      return;
    }
    reviewState.reviewer = payload.reviewer;
    localStorage.setItem(REVIEWER_STORAGE_KEY, payload.reviewer);
    byId("reviewer-name").value = payload.reviewer;
    reviewState.labels[row.candidate_id] = payload;
    writeLocalLabels();
    byId("first-pass-save-result").textContent = "Saved in this browser. Sending shared copy...";

    const results = await Promise.allSettled([
      saveToLocalBackend(payload),
      submitToSheet(payload)
    ]);
    const backendSaved = results[0].status === "fulfilled" && results[0].value;
    const sheetSubmitted = results[1].status === "fulfilled" && results[1].value;
    payload.sheet_status = sheetSubmitted ? "submitted" : "local-only";
    payload.save_message = sheetSubmitted
      ? `Saved${backendSaved ? " locally" : ""} and submitted to the shared Google Sheet.`
      : `Saved${backendSaved ? " to the local project" : " in this browser"}. Shared Sheet endpoint is not connected yet.`;
    reviewState.labels[row.candidate_id] = payload;
    writeLocalLabels();
    renderCandidateList();
    renderCandidateDetail();
  }

  function longitudeDistance(left, right) {
    const delta = Math.abs(left - right) % 360;
    return Math.min(delta, 360 - delta);
  }

  function geometryGroups(tolerance) {
    const groups = [];
    reviewState.rows
      .filter((row) => row.jupiter_latitude !== "" && row.jupiter_longitude !== "")
      .forEach((row) => {
        const group = groups.find((item) => (
          Math.abs(item.latitude - row.jupiter_latitude) <= tolerance
          && longitudeDistance(item.longitude, row.jupiter_longitude) <= tolerance
        ));
        if (group) group.rows.push(row);
        else groups.push({latitude: row.jupiter_latitude, longitude: row.jupiter_longitude, rows: [row]});
      });
    return groups;
  }

  function downloadText(filename, content, type) {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function csvEscape(value) {
    const text = String(value ?? "");
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function exportCsv() {
    const rows = Object.values(reviewState.labels);
    const csv = [LABEL_FIELDS.join(","), ...rows.map((row) => LABEL_FIELDS.map((field) => csvEscape(row[field])).join(","))].join("\n");
    downloadText("jupiter_candidate_labels.csv", csv, "text/csv");
  }

  function exportJson() {
    downloadText("jupiter_candidate_labels.json", JSON.stringify(Object.values(reviewState.labels), null, 2), "application/json");
  }

  function renderConnectionStatus() {
    const endpoint = reviewState.collaboration.apps_script_endpoint;
    const status = byId("sheet-status");
    if (endpoint) {
      status.textContent = "Connected: Save label writes a browser backup and submits the same row to the shared Google Sheet.";
    } else {
      status.textContent = "Shared Sheet exists, but its append endpoint is not deployed. Labels still save in this browser and export to CSV/JSON.";
    }
    if (reviewState.collaboration.label_sheet_url) {
      byId("sheet-link").href = reviewState.collaboration.label_sheet_url;
      byId("sheet-link").hidden = false;
    }
  }

  function renderGeometryStatus(payload) {
    const hasCoordinates = reviewState.rows.some((row) => row.jupiter_latitude !== "" && row.jupiter_longitude !== "");
    byId("group-geometry").disabled = !hasCoordinates;
    byId("geometry-tolerance").value = payload.default_lat_lon_tolerance_degrees || reviewState.geometry.default_tolerance_degrees || 1;
    byId("geometry-status").textContent = hasCoordinates
      ? "Candidate coordinates are present. Grouping compares nearby latitude/longitude across frames."
      : reviewState.geometry.safe_interpretation || payload.geometry_note || "Candidate latitude/longitude are pending a validated backplane.";
  }

  async function loadJson(path, fallback = {}) {
    const response = await fetch(path);
    if (!response.ok) return fallback;
    return response.json();
  }

  async function initReviewQueue() {
    const [payload, collaboration, geometry] = await Promise.all([
      loadJson("/static-data/first_pass_review_queue.json", {rows: []}),
      loadJson("/static-data/collaboration_config.json", {}),
      loadJson("/static-data/geometry_readiness.json", {})
    ]);
    reviewState.rows = (payload.rows || []).map(normalizeRow).sort((left, right) => left.review_order - right.review_order);
    reviewState.collaboration = collaboration;
    reviewState.geometry = geometry;
    byId("reviewer-name").value = reviewState.reviewer;
    renderConnectionStatus();
    renderGeometryStatus(payload);
    renderProgress();
    renderCandidateList();
    selectCandidate(reviewState.rows[0]?.candidate_id);
  }

  byId("reviewer-name").addEventListener("input", (event) => {
    reviewState.reviewer = event.target.value.trim();
    localStorage.setItem(REVIEWER_STORAGE_KEY, reviewState.reviewer);
  });
  byId("review-filter").addEventListener("change", (event) => {
    reviewState.filter = event.target.value;
    const rows = filteredRows();
    if (!rows.some((row) => row.candidate_id === reviewState.selected?.candidate_id)) {
      reviewState.selected = rows[0] || null;
    }
    renderCandidateList();
    renderCandidateDetail();
  });
  byId("group-geometry").addEventListener("click", () => {
    const tolerance = toNumber(byId("geometry-tolerance").value, 1);
    const groups = geometryGroups(tolerance);
    const repeated = groups.filter((group) => group.rows.length > 1);
    byId("geometry-status").textContent = `${groups.length} location groups found; ${repeated.length} contain more than one candidate within ${tolerance.toFixed(1)} degrees.`;
  });
  byId("export-review-csv").addEventListener("click", exportCsv);
  byId("export-review-json").addEventListener("click", exportJson);

  initReviewQueue().catch((error) => {
    byId("first-pass-candidate-list").textContent = `Could not load candidate queue: ${error.message}`;
    byId("review-progress-copy").textContent = "Candidate queue unavailable.";
  });
})();
