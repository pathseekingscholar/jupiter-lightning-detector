const state = {
  data: null,
  current: null,
  detectionDate: "2001-01-01",
  detection: null,
  validation: null,
  characteristics: null,
  labels: {labels: {}, counts: {}},
  detectorStatusTimer: null,
  timer: null,
  historyTimer: null,
  originalObjectUrl: null,
  processedDataUrl: null,
  storageWarned: false,
  backendAvailable: false,
  runtimeKnown: false,
};

window.JupiterWorkbench = {
  backendAvailable: false,
  runtimeKnown: false,
};

const $ = (id) => document.getElementById(id);
const controls = ["scale", "crop", "low", "high", "gamma", "x", "y", "mark"];
const DB_NAME = "jupiter-lightning-library";
const DB_VERSION = 1;
const IMAGE_STORE = "images";

async function jsonResponse(url) {
  const response = await fetch(url);
  const contentType = response.headers.get("content-type") || "";
  if (!response.ok || !contentType.includes("application/json")) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function loadRuntime() {
  try {
    state.data = await jsonResponse("/api/observations");
    state.backendAvailable = true;
  } catch {
    state.data = await jsonResponse("/static-data/api/observations.json");
    state.backendAvailable = false;
    state.data.notes = {
      ...(state.data.notes || {}),
      ...JSON.parse(localStorage.getItem("jupiterPublicObservationNotes") || "{}")
    };
  }
  state.runtimeKnown = true;
  window.JupiterWorkbench.backendAvailable = state.backendAvailable;
  window.JupiterWorkbench.runtimeKnown = true;
  $("runtime-mode").textContent = state.backendAvailable
    ? "Python backend connected"
    : "Public evidence snapshot";
}

function configureRuntimeNavigation() {
  if (state.backendAvailable) return;
  ["manual", "automation"].forEach((name) => {
    document.querySelector(`[data-tab-target="${name}"]`)?.setAttribute("hidden", "");
  });
  $("brief-title").textContent = "Review a Cassini candidate. Inspect the image. Record what the feature looks like.";
}

function publicDataPath(name) {
  return `/static-data/api/${name}.json`;
}

function openLibraryDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(IMAGE_STORE)) {
        db.createObjectStore(IMAGE_STORE, {keyPath: "id"});
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function libraryPut(record) {
  try {
    const db = await openLibraryDb();
    await new Promise((resolve, reject) => {
      const transaction = db.transaction(IMAGE_STORE, "readwrite");
      transaction.objectStore(IMAGE_STORE).put(record);
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error);
    });
    db.close();
  } catch (error) {
    if (error?.name === "QuotaExceededError") {
      const shouldExport = confirm("The local image library is full. Export a backup now before adding more data?");
      if (shouldExport) await exportLibrary();
    }
    throw error;
  }
}

async function libraryGet(id) {
  const db = await openLibraryDb();
  const result = await new Promise((resolve, reject) => {
    const request = db.transaction(IMAGE_STORE).objectStore(IMAGE_STORE).get(id);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  db.close();
  return result;
}

async function libraryAll() {
  const db = await openLibraryDb();
  const result = await new Promise((resolve, reject) => {
    const request = db.transaction(IMAGE_STORE).objectStore(IMAGE_STORE).getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
  db.close();
  return result.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
}

async function libraryDelete(id) {
  const db = await openLibraryDb();
  await new Promise((resolve, reject) => {
    const transaction = db.transaction(IMAGE_STORE, "readwrite");
    transaction.objectStore(IMAGE_STORE).delete(id);
    transaction.oncomplete = resolve;
    transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

function processUrl(exporting = false) {
  const params = new URLSearchParams({
    image: state.current.image_number,
    scale: $("scale").value,
    crop: $("crop").value,
    low: $("low").value,
    high: $("high").value,
    gamma: $("gamma").value,
    x: $("x").value,
    y: $("y").value,
    mark: $("mark").checked ? "1" : "0",
    t: Date.now().toString(),
  });
  return `/api/${exporting ? "export" : "process"}?${params}`;
}

function renderStrip() {
  const strip = $("observation-strip");
  strip.innerHTML = "";
  state.data.observations.forEach((observation) => {
    const button = document.createElement("button");
    button.className = "observation-tab";
    button.innerHTML = `N${observation.image_number}<span>${observation.start_time.slice(0, 10)} - ${observation.filter_name} - ${observation.exposure_seconds}s</span>`;
    button.addEventListener("click", () => selectObservation(observation));
    button.dataset.opus = observation.opus_id;
    strip.appendChild(button);
  });
}

function revokeOriginalUrl() {
  if (state.originalObjectUrl) {
    URL.revokeObjectURL(state.originalObjectUrl);
    state.originalObjectUrl = null;
  }
}

function configureCoordinateBounds(width, height) {
  $("x").max = width;
  $("y").max = height;
  [...$("crop").options].forEach((option) => {
    option.disabled = Number(option.value) > Math.min(width, height);
  });
  if (Number($("crop").value) > Math.min(width, height)) {
    const allowed = [...$("crop").options].filter((option) => !option.disabled);
    $("crop").value = allowed[allowed.length - 1].value;
  }
}

function selectObservation(observation) {
  revokeOriginalUrl();
  state.current = {...observation, source_type: "opus", width: 1024, height: 1024};
  document.querySelectorAll(".observation-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.opus === observation.opus_id);
  });
  configureCoordinateBounds(1024, 1024);
  $("image-title").textContent = `N${observation.image_number}`;
  $("original").src = observation.preview_image.replaceAll("\\", "/").replace(/^.*\/data\//, "/data/");
  $("metadata").innerHTML = `
    <dt>Source</dt><dd>OPUS calibrated product</dd>
    <dt>Record</dt><dd><a href="${observation.opus_detail_url}" target="_blank" rel="noreferrer">${observation.opus_id}</a></dd>
    <dt>UTC</dt><dd>${observation.start_time.replace("T", " ")}</dd>
    <dt>Exposure</dt><dd>${observation.exposure_seconds}s</dd>
    <dt>Camera/filter</dt><dd>NAC / ${observation.filter_name}</dd>
    <dt>Scale</dt><dd>${observation.center_resolution_km.toFixed(1)} km/px</dd>`;
  renderCandidates();
  const saved = state.data.notes[observation.opus_id] || {};
  $("classification").value = saved.classification || "known-lightning";
  $("note").value = saved.text || "";
  const first = observation.candidates[0];
  $("x").value = saved.x || first?.x || 512;
  $("y").value = saved.y || first?.y || 512;
  updateProcessed();
}

async function selectUpload(record) {
  revokeOriginalUrl();
  state.current = {
    ...record,
    source_type: "upload",
    opus_id: record.id,
    candidates: [],
  };
  document.querySelectorAll(".observation-tab").forEach((tab) => tab.classList.remove("active"));
  configureCoordinateBounds(record.width, record.height);
  state.originalObjectUrl = URL.createObjectURL(record.blob);
  $("original").src = state.originalObjectUrl;
  $("image-title").textContent = record.name;
  $("metadata").innerHTML = `
    <dt>Source</dt><dd>Local upload</dd>
    <dt>Added</dt><dd>${new Date(record.created_at).toLocaleString()}</dd>
    <dt>Dimensions</dt><dd>${record.width} x ${record.height}</dd>
    <dt>File type</dt><dd>${record.type || "image"}</dd>
    <dt>History</dt><dd>${record.history?.length || 0} settings</dd>`;
  $("x").value = record.last_settings?.x || Math.round(record.width / 2);
  $("y").value = record.last_settings?.y || Math.round(record.height / 2);
  $("classification").value = record.classification || "uncertain";
  $("note").value = record.note || "";
  renderCandidates();
  updateProcessed();
}

function renderCandidates() {
  const candidates = state.current.candidates || [];
  if (!candidates.length) {
    $("candidate-body").innerHTML = `<tr><td colspan="5">No published marks. Use the coordinate fields and field note for this upload.</td></tr>`;
    return;
  }
  $("candidate-body").innerHTML = candidates.map((candidate) => `
    <tr data-x="${candidate.x}" data-y="${candidate.y}">
      <td>${candidate.label}</td>
      <td>(${candidate.x}, ${candidate.y})</td>
      <td>${candidate.peak_snr.toFixed(1)}</td>
      <td>${candidate.bright_pixel_count}</td>
      <td>${(candidate.published_power_w / 1e9).toFixed(3)} GW</td>
    </tr>`).join("");
  document.querySelectorAll("#candidate-body tr[data-x]").forEach((row) => {
    row.addEventListener("click", () => {
      $("x").value = row.dataset.x;
      $("y").value = row.dataset.y;
      updateProcessed();
    });
  });
}

function observationForDetection(candidate) {
  return state.data.observations.find((observation) => observation.opus_id === candidate.opus_id);
}

function selectDetectionCandidate(candidate) {
  const knownObservation = observationForDetection(candidate);
  if (knownObservation) {
    selectObservation(knownObservation);
  } else {
    revokeOriginalUrl();
    state.current = {
      opus_id: candidate.opus_id,
      image_number: candidate.image_number,
      start_time: candidate.time,
      exposure_seconds: "32",
      camera: "NAC",
      filter_name: "HAL",
      center_resolution_km: 60,
      preview_image: candidate.preview_image,
      candidates: [],
      opus_detail_url: candidate.opus_detail_url,
      source_type: "opus",
      width: 1024,
      height: 1024,
    };
    document.querySelectorAll(".observation-tab").forEach((tab) => tab.classList.remove("active"));
    configureCoordinateBounds(1024, 1024);
    $("image-title").textContent = `N${candidate.image_number}`;
    $("original").src = candidate.preview_image;
    $("metadata").innerHTML = `
      <dt>Source</dt><dd>OPUS detector sequence</dd>
      <dt>Record</dt><dd><a href="${candidate.opus_detail_url}" target="_blank" rel="noreferrer">${candidate.opus_id}</a></dd>
      <dt>UTC</dt><dd>${candidate.time.replace("T", " ")}</dd>
      <dt>Exposure</dt><dd>32s</dd>
      <dt>Camera/filter</dt><dd>NAC / HAL</dd>
      <dt>Track</dt><dd>${candidate.track_id}</dd>`;
    renderCandidates();
  }
  $("x").value = Math.round(candidate.x);
  $("y").value = Math.round(candidate.y);
  $("crop").value = "128";
  $("mark").checked = true;
  updateProcessed();
  document.querySelectorAll(".track-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.candidateId === candidate.candidate_id);
  });
}

function renderDetectionReview() {
  const summary = state.detection?.summary || {};
  const tracks = state.detection?.tracks || [];
  if (!state.detection?.available) {
    $("detection-summary").textContent = state.detection?.message || "No detector output found yet.";
    $("track-list").innerHTML = "";
    $("contact-sheet").removeAttribute("src");
    $("all-csv-link").href = `/outputs/detection/${state.detectionDate}/candidates.csv`;
    $("contact-sheet-link").href = `/outputs/detection/${state.detectionDate}/candidate_contact_sheet.png`;
    return;
  }
  $("contact-sheet-link").href = state.detection.contact_sheet_url;
  $("all-csv-link").href = state.detection.all_csv_url || `/outputs/detection/${state.detectionDate}/candidates.csv`;
  $("contact-sheet").src = `${state.detection.contact_sheet_url}?t=${Date.now()}`;
  $("detection-summary").textContent =
    `${state.detectionDate}: ${summary.frames || 0} long-exposure H-alpha frames scanned, ${summary.candidates || 0} bright regions found, ` +
    `${summary.review_candidates || 0} review candidates after artifact filters, ` +
    `${Math.max(0, (summary.candidates || 0) - (summary.review_candidates || 0))} rejected or artifact-flagged candidates. This is a review queue, not a confirmed lightning catalog.`;
  if (!$("run-detector").disabled) {
    $("detector-status").textContent =
      `Loaded ${state.detectionDate}: ${summary.frames || 0} images processed, ${summary.candidates || 0} saved candidates.`;
  }

  const topTracks = tracks.slice(0, 20);
  const flatCandidates = topTracks.map((track) => track.items[0]).filter(Boolean);
  renderCandidateTable(flatCandidates);
  renderReviewBuckets(flatCandidates);
  $("track-list").innerHTML = topTracks.map((track) => {
    const lead = track.items[0];
    const cropUrl = lead.crop_url || `/api/detection-crop?image=${encodeURIComponent(lead.image_number)}&x=${Math.round(lead.x)}&y=${Math.round(lead.y)}&crop=128`;
    const frames = track.items.map((item) => `N${item.image_number}`).join(" -> ");
    const savedLabel = lead.human_label || state.labels.labels?.[lead.candidate_id]?.human_label || "";
    const savedNote = lead.review_note || state.labels.labels?.[lead.candidate_id]?.review_note || "";
    const savedConfidence = state.labels.labels?.[lead.candidate_id]?.confidence || "medium";
    const savedReviewer = state.labels.labels?.[lead.candidate_id]?.reviewer || localStorage.getItem("jupiterReviewerName") || "local-reviewer";
    return `
      <article class="track-card" data-candidate-id="${lead.candidate_id}">
        <button type="button" class="track-open" data-candidate-id="${lead.candidate_id}">
          <img src="${cropUrl}" alt="">
          <span>
            <b>Candidate ${lead.candidate_id}</b>
            <small title="Candidate score is a review priority rank, not a calibrated probability.">score ${track.confidence.toFixed(2)} / seen in ${track.track_length} frame(s)</small>
          </span>
        </button>
        <dl>
          <dt title="Cassini image identifier.">Image ID</dt><dd>N${lead.image_number}</dd>
          <dt title="Pixel coordinate in the displayed image.">x/y</dt><dd>${lead.x.toFixed(1)}, ${lead.y.toFixed(1)}</dd>
          <dt title="Peak local signal-to-noise ratio.">Brightness</dt><dd>${lead.peak_snr.toFixed(1)}</dd>
          <dt title="Number of connected bright pixels.">Blob size</dt><dd>${lead.area_px} px</dd>
          <dt title="Artifact warnings. Empty means no obvious artifact flag.">Flags</dt><dd>${escapeHtml(lead.flags || "none")}</dd>
        </dl>
        <p>${escapeHtml(track.reason)}</p>
        <p class="track-frames">Frames linked by detector: ${escapeHtml(frames)}</p>
        <label>
          Human label
          <select data-label-for="${lead.candidate_id}">
            ${labelOptions(savedLabel)}
          </select>
        </label>
        <label>
          Confidence
          <select data-confidence-for="${lead.candidate_id}">
            ${confidenceOptions(savedConfidence)}
          </select>
        </label>
        <label>
          Reviewer
          <input data-reviewer-for="${lead.candidate_id}" type="text" value="${escapeHtml(savedReviewer)}" placeholder="reviewer name or initials">
        </label>
        <label>
          Review note
          <textarea data-note-for="${lead.candidate_id}" rows="3" placeholder="Why keep or reject this candidate?">${escapeHtml(savedNote)}</textarea>
        </label>
        <button type="button" data-save-label="${lead.candidate_id}">Save label</button>
      </article>`;
  }).join("");
  const candidatesById = new Map();
  topTracks.forEach((track) => track.items.forEach((item) => candidatesById.set(item.candidate_id, item)));
  document.querySelectorAll(".track-open").forEach((button) => {
    button.addEventListener("click", () => selectDetectionCandidate(candidatesById.get(button.dataset.candidateId)));
  });
  document.querySelectorAll("[data-save-label]").forEach((button) => {
    button.addEventListener("click", async () => {
      await saveCandidateLabel(candidatesById.get(button.dataset.saveLabel));
    });
  });
}

function labelOptions(selected = "") {
  const labels = [
    ["", "unlabeled"],
    ["known-lightning", "known lightning"],
    ["possible-lightning", "possible lightning"],
    ["artifact", "artifact"],
    ["cosmic-ray-hot-pixel", "cosmic ray/hot pixel"],
    ["uncertain", "uncertain"],
  ];
  return labels.map(([value, text]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${text}</option>`).join("");
}

function confidenceOptions(selected = "medium") {
  const values = [
    ["low", "low"],
    ["medium", "medium"],
    ["high", "high"],
  ];
  return values.map(([value, text]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${text}</option>`).join("");
}

function renderCandidateTable(candidates) {
  const body = $("candidate-review-body");
  if (!body) return;
  if (!candidates.length) {
    body.innerHTML = `<tr><td colspan="9">No review candidates loaded for this date yet.</td></tr>`;
    return;
  }
  body.innerHTML = candidates.map((candidate) => {
    const label = candidate.human_label || state.labels.labels?.[candidate.candidate_id]?.human_label || "unlabeled";
    return `
      <tr data-candidate-row="${candidate.candidate_id}">
        <td>N${candidate.image_number}</td>
        <td>${escapeHtml(candidate.candidate_id)}</td>
        <td>${candidate.x.toFixed(1)}, ${candidate.y.toFixed(1)}</td>
        <td>${candidate.peak_snr.toFixed(1)}</td>
        <td>${candidate.area_px}</td>
        <td>${candidate.mean_snr.toFixed(1)} / peak ${candidate.peak_snr.toFixed(1)}</td>
        <td>${escapeHtml(candidate.flags || "none")}</td>
        <td>${candidate.confidence.toFixed(2)}</td>
        <td>${escapeHtml(label)}</td>
      </tr>`;
  }).join("");
}

function renderReviewBuckets(candidates = []) {
  const labelRows = Object.values(state.labels.labels || {});
  const falsePositives = labelRows.filter((row) => ["artifact", "cosmic-ray-hot-pixel"].includes(row.human_label));
  const unmatched = candidates.filter((candidate) => {
    const label = candidate.human_label || state.labels.labels?.[candidate.candidate_id]?.human_label || "";
    return !label;
  });
  const falseNegatives = (state.validation?.results || []).filter((row) => !row.recovered);
  $("false-positive-list").innerHTML = falsePositives.length
    ? falsePositives.slice(0, 8).map((row) => `<p><b>${escapeHtml(row.candidate_id)}</b> N${escapeHtml(row.image_number)} ${escapeHtml(row.human_label)}</p>`).join("")
    : "<p>No human-reviewed false positives saved yet.</p>";
  $("false-negative-list").innerHTML = falseNegatives.length
    ? falseNegatives.map((row) => `<p><b>N${row.image_number}</b> paper coordinate (${row.published_x}, ${row.published_y}) was not recovered.</p>`).join("")
    : "<p>No false negatives in the generated validation outputs.</p>";
  $("unmatched-list").innerHTML = unmatched.length
    ? unmatched.slice(0, 8).map((candidate) => `<p><b>${escapeHtml(candidate.candidate_id)}</b> N${candidate.image_number} at ${candidate.x.toFixed(1)}, ${candidate.y.toFixed(1)} remains for review.</p>`).join("")
    : "<p>Top review candidates shown here have labels or no candidates are loaded.</p>";
}

async function loadCandidateLabels() {
  try {
    state.labels = state.backendAvailable
      ? await jsonResponse("/api/candidate-labels")
      : {labels: JSON.parse(localStorage.getItem("jupiterPublicReviewLabels") || "{}"), counts: {}};
    if (state.labels.csv_url) $("labels-csv-link").href = state.labels.csv_url;
    if (state.labels.json_url) $("labels-json-link").href = state.labels.json_url;
  } catch (error) {
    state.labels = {labels: {}, counts: {}, error: error.message};
  }
}

async function saveCandidateLabel(candidate) {
  if (!candidate) return;
  const humanLabel = document.querySelector(`[data-label-for="${candidate.candidate_id}"]`)?.value || "";
  if (!humanLabel) {
    alert("Choose a human label before saving.");
    return;
  }
  const note = document.querySelector(`[data-note-for="${candidate.candidate_id}"]`)?.value || "";
  const confidence = document.querySelector(`[data-confidence-for="${candidate.candidate_id}"]`)?.value || "medium";
  const reviewer = document.querySelector(`[data-reviewer-for="${candidate.candidate_id}"]`)?.value || "local-reviewer";
  localStorage.setItem("jupiterReviewerName", reviewer);
  if (!state.backendAvailable) {
    const labels = JSON.parse(localStorage.getItem("jupiterPublicReviewLabels") || "{}");
    labels[candidate.candidate_id] = {
      run_date: state.detectionDate,
      candidate_id: candidate.candidate_id,
      image_id: `N${candidate.image_number}`,
      image_number: candidate.image_number,
      x: candidate.x.toFixed(2),
      y: candidate.y.toFixed(2),
      brightness: candidate.peak_snr.toFixed(2),
      blob_size: candidate.area_px,
      snr: candidate.peak_snr.toFixed(2),
      artifact_flags: candidate.flags || "",
      candidate_score: candidate.confidence.toFixed(4),
      reviewer_label: humanLabel,
      human_label: humanLabel,
      label: humanLabel,
      confidence,
      reviewer,
      notes: note,
      review_note: note,
      timestamp: new Date().toISOString(),
      reviewed_at: new Date().toISOString(),
      source: "public-vercel-review"
    };
    localStorage.setItem("jupiterPublicReviewLabels", JSON.stringify(labels));
    state.labels = {labels, counts: {}};
    renderDetectionReview();
    return;
  }
  const response = await fetch("/api/candidate-label", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      run_date: state.detectionDate,
      candidate_id: candidate.candidate_id,
      image_id: `N${candidate.image_number}`,
      image_number: candidate.image_number,
      x: candidate.x.toFixed(2),
      y: candidate.y.toFixed(2),
      brightness: candidate.peak_snr.toFixed(2),
      blob_size: candidate.area_px,
      snr: candidate.peak_snr.toFixed(2),
      artifact_flags: candidate.flags || "",
      candidate_score: candidate.confidence.toFixed(4),
      human_label: humanLabel,
      confidence,
      reviewer,
      review_note: note,
      updated_at: new Date().toISOString(),
    }),
  });
  if (!response.ok) {
    alert(`Could not save label: server returned ${response.status}`);
    return;
  }
  state.labels = await response.json();
  await loadDetectionReview();
}

async function loadDetectionReview() {
  try {
    state.detection = state.backendAvailable
      ? await jsonResponse(`/api/detection?date=${encodeURIComponent(state.detectionDate)}`)
      : await jsonResponse(publicDataPath(`detection-${state.detectionDate}`));
    renderDetectionReview();
  } catch (error) {
    state.detection = {
      available: false,
      message: `Detector output could not be loaded: ${error.message}`,
      tracks: [],
      summary: {},
    };
    renderDetectionReview();
  }
}

function renderDetectionDateTabs() {
  document.querySelectorAll("#detection-date-tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.date === state.detectionDate);
  });
}

async function selectDetectionDate(runDate) {
  state.detectionDate = runDate;
  renderDetectionDateTabs();
  await loadDetectionReview();
}

function renderValidation() {
  if (!state.validation?.available) {
    $("validation-summary").textContent = state.validation?.message || "Validation is not available yet.";
    $("validation-body").innerHTML = `<tr><td colspan="5">Run the detector first.</td></tr>`;
    return;
  }
  $("validation-summary").textContent = `${state.validation.summary} Source: ${state.validation.source}.`;
  $("validation-body").innerHTML = state.validation.results.map((row) => {
    const paper = `(${row.published_x}, ${row.published_y})`;
    const detector = row.detected_x === null ? "not in current run" : `(${row.detected_x}, ${row.detected_y})`;
    const offset = row.distance_px === null ? row.note : `${row.distance_px} px`;
    const result = row.recovered ? "Recovered" : row.note;
    return `
      <tr>
        <td>N${row.image_number}</td>
        <td>${paper}</td>
        <td>${detector}</td>
        <td>${offset}</td>
        <td>${result}</td>
      </tr>`;
  }).join("");
  renderReviewBuckets(state.detection?.tracks?.slice(0, 20).map((track) => track.items[0]).filter(Boolean) || []);
}

async function loadValidation() {
  try {
    state.validation = state.backendAvailable
      ? await jsonResponse("/api/validation")
      : await jsonResponse(publicDataPath("validation"));
  } catch (error) {
    state.validation = {
      available: false,
      message: `Validation could not be loaded: ${error.message}`,
    };
  }
  renderValidation();
}

function renderDetectorCharacteristics() {
  if (!state.characteristics) return;
  const classification = state.characteristics.classification || {};
  const totals = state.characteristics.totals || {};
  $("classification-copy").innerHTML = `
    <b>Positive:</b> ${escapeHtml(classification.positive || "")}<br>
    <b>Negative / uncertain:</b> ${escapeHtml(classification.negative_or_uncertain || "")}<br>
    <b>Important limitation:</b> ${escapeHtml(classification.not_claimed || "")}`;

  $("detector-rule-list").innerHTML = (state.characteristics.rules || [])
    .map((rule) => `<li>${escapeHtml(rule)}</li>`)
    .join("");

  $("error-set-body").innerHTML = (state.characteristics.dates || []).map((row) => {
    if (!row.available) {
      return `<tr><td>${row.date}</td><td colspan="4">${escapeHtml(row.message)}</td></tr>`;
    }
    const rejected = Math.max(0, (row.raw_candidates || 0) - (row.review_candidates || 0));
    return `
      <tr>
        <td>${row.date}</td>
        <td>${row.known_recovered}</td>
        <td>${row.raw_candidates}</td>
        <td>${rejected}</td>
        <td>${row.unmatched_review}</td>
      </tr>`;
  }).join("");

  const flagText = (state.characteristics.flag_counts || [])
    .slice(0, 4)
    .map((item) => `${item.flag}: ${item.count}`)
    .join("; ");
  $("detector-warning").textContent =
    `${totals.known_recovered || 0} of ${totals.known_total || 0} published marks recovered. ` +
    `${totals.unmatched_review || 0} unmatched review candidates remain to classify. ` +
    `Common artifact flags: ${flagText || "none yet"}.`;
}

async function loadDetectorCharacteristics() {
  try {
    state.characteristics = state.backendAvailable
      ? await jsonResponse("/api/detector-characteristics")
      : await jsonResponse(publicDataPath("detector-characteristics"));
  } catch (error) {
    state.characteristics = {
      classification: {
        positive: "",
        negative_or_uncertain: "",
        not_claimed: `Detector characteristics could not be loaded: ${error.message}`,
      },
      rules: [],
      dates: [],
      totals: {},
      flag_counts: [],
    };
  }
  renderDetectorCharacteristics();
}

function renderDetectorStatus(status) {
  $("detector-status").textContent = status.message || "Detector idle.";
  $("run-detector").disabled = Boolean(status.running);
}

async function refreshDetectorStatus() {
  let status;
  try {
    status = state.backendAvailable
      ? await jsonResponse("/api/detection-status")
      : {
          running: false,
          message: "Public view: current outputs are loaded. Starting a new detector run requires the local Python backend."
        };
  } catch (error) {
    renderDetectorStatus({running: false, message: `Detector status could not be loaded: ${error.message}`});
    return;
  }
  renderDetectorStatus(status);
  if (status.running) {
    clearTimeout(state.detectorStatusTimer);
    state.detectorStatusTimer = setTimeout(refreshDetectorStatus, 1800);
    return;
  }
  await loadDetectionReview();
  await loadValidation();
}

async function runDetectorAgain() {
  if (!state.backendAvailable) {
    renderDetectorStatus({running: false, message: "New detector runs require the local Python backend and calibrated OPUS products. The public site shows the latest generated outputs."});
    return;
  }
  renderDetectorStatus({running: true, message: `Starting detector for ${state.detectionDate}...`});
  const response = await fetch(`/api/run-detection?date=${encodeURIComponent(state.detectionDate)}`, {method: "POST"});
  if (!response.ok) {
    renderDetectorStatus({running: false, message: `Could not start detector: server returned ${response.status}`});
    return;
  }
  await refreshDetectorStatus();
}

function updateOutputs() {
  $("low-out").textContent = `${Number($("low").value).toFixed(1)}%`;
  $("high-out").textContent = `${Number($("high").value).toFixed(1)}%`;
  $("gamma-out").textContent = Number($("gamma").value).toFixed(1);
}

function currentSettings() {
  return {
    scale: Number($("scale").value),
    crop: Number($("crop").value),
    low: Number($("low").value),
    high: Number($("high").value),
    gamma: Number($("gamma").value),
    x: Number($("x").value),
    y: Number($("y").value),
    mark: $("mark").checked,
  };
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

async function renderBitmapWithSettings(bitmap) {
  const settings = currentSettings();
  const crop = Math.min(settings.crop, bitmap.width, bitmap.height);
  const x0 = Math.max(0, Math.min(bitmap.width - crop, settings.x - crop / 2));
  const y0 = Math.max(0, Math.min(bitmap.height - crop, settings.y - crop / 2));
  const source = document.createElement("canvas");
  source.width = crop;
  source.height = crop;
  const context = source.getContext("2d", {willReadFrequently: true});
  context.drawImage(bitmap, x0, y0, crop, crop, 0, 0, crop, crop);
  bitmap.close();

  const pixels = context.getImageData(0, 0, crop, crop);
  const histogram = new Uint32Array(256);
  for (let index = 0; index < pixels.data.length; index += 4) {
    const luminance = Math.round(
      pixels.data[index] * 0.2126 +
      pixels.data[index + 1] * 0.7152 +
      pixels.data[index + 2] * 0.0722
    );
    histogram[luminance] += 1;
  }
  const pixelCount = crop * crop;
  const black = percentileFromHistogram(histogram, pixelCount, settings.low);
  const white = Math.max(black + 1, percentileFromHistogram(histogram, pixelCount, settings.high));
  for (let index = 0; index < pixels.data.length; index += 4) {
    const luminance =
      pixels.data[index] * 0.2126 +
      pixels.data[index + 1] * 0.7152 +
      pixels.data[index + 2] * 0.0722;
    const normalized = Math.max(0, Math.min(1, (luminance - black) / (white - black)));
    const adjusted = Math.round(255 * Math.pow(normalized, 1 / settings.gamma));
    pixels.data[index] = adjusted;
    pixels.data[index + 1] = adjusted;
    pixels.data[index + 2] = adjusted;
    pixels.data[index + 3] = 255;
  }
  context.putImageData(pixels, 0, 0);
  if (settings.mark) {
    context.strokeStyle = "#b1261d";
    context.lineWidth = Math.max(2, crop / 128);
    context.beginPath();
    context.arc(settings.x - x0, settings.y - y0, Math.max(6, crop / 40), 0, Math.PI * 2);
    context.stroke();
  }

  const output = document.createElement("canvas");
  output.width = Math.max(1, Math.round(crop * settings.scale));
  output.height = Math.max(1, Math.round(crop * settings.scale));
  output.getContext("2d").drawImage(source, 0, 0, output.width, output.height);
  state.processedDataUrl = output.toDataURL("image/png");
  return state.processedDataUrl;
}

async function renderUploadedImage() {
  const record = await libraryGet(state.current.id);
  return renderBitmapWithSettings(await createImageBitmap(record.blob));
}

async function renderPublicObservation() {
  const response = await fetch(state.current.preview_image);
  if (!response.ok) throw new Error(`Preview image returned ${response.status}`);
  return renderBitmapWithSettings(await createImageBitmap(await response.blob()));
}

async function updateProcessed() {
  if (!state.current) return;
  updateOutputs();
  $("loading").classList.add("visible");
  const image = $("processed");
  image.style.opacity = ".55";
  image.onload = () => {
    $("loading").classList.remove("visible");
    image.style.opacity = "1";
  };
  if (state.current.source_type === "upload") {
    image.src = await renderUploadedImage();
    scheduleHistorySave();
  } else if (!state.backendAvailable) {
    image.src = await renderPublicObservation();
  } else {
    image.src = processUrl();
  }
}

function scheduleUpdate() {
  clearTimeout(state.timer);
  state.timer = setTimeout(updateProcessed, 120);
}

function scheduleHistorySave() {
  clearTimeout(state.historyTimer);
  state.historyTimer = setTimeout(saveUploadHistory, 650);
}

async function saveUploadHistory() {
  if (state.current?.source_type !== "upload") return;
  const record = await libraryGet(state.current.id);
  const settings = currentSettings();
  const signature = JSON.stringify(settings);
  const history = record.history || [];
  if (history[history.length - 1]?.signature !== signature) {
    history.push({saved_at: new Date().toISOString(), settings, signature});
  }
  record.history = history.slice(-50);
  record.last_settings = settings;
  record.updated_at = new Date().toISOString();
  await libraryPut(record);
  await renderLibrary();
}

function placeCoordinate(event, imageElement, fullFrame = false) {
  if (!state.current) return;
  const rect = imageElement.getBoundingClientRect();
  const width = state.current.width || 1024;
  const height = state.current.height || 1024;
  const crop = fullFrame ? Math.min(width, height) : Math.min(Number($("crop").value), width, height);
  const currentX = Number($("x").value);
  const currentY = Number($("y").value);
  const x0 = fullFrame ? 0 : Math.max(0, Math.min(width - crop, currentX - crop / 2));
  const y0 = fullFrame ? 0 : Math.max(0, Math.min(height - crop, currentY - crop / 2));
  const localX = ((event.clientX - rect.left) / rect.width) * (fullFrame ? width : crop);
  const localY = ((event.clientY - rect.top) / rect.height) * (fullFrame ? height : crop);
  $("x").value = Math.max(1, Math.min(width, Math.round(x0 + localX)));
  $("y").value = Math.max(1, Math.min(height, Math.round(y0 + localY)));
  updateProcessed();
}

async function saveNote(event) {
  event.preventDefault();
  $("save-state").textContent = "saving...";
  if (state.current.source_type === "upload") {
    const record = await libraryGet(state.current.id);
    record.classification = $("classification").value;
    record.note = $("note").value;
    record.updated_at = new Date().toISOString();
    await libraryPut(record);
    state.current = {...state.current, ...record};
    await renderLibrary();
    $("save-state").textContent = "saved locally";
    return;
  }
  if (!state.backendAvailable) {
    const notes = JSON.parse(localStorage.getItem("jupiterPublicObservationNotes") || "{}");
    notes[state.current.opus_id] = {
      classification: $("classification").value,
      text: $("note").value,
      x: Number($("x").value),
      y: Number($("y").value),
      updated_at: new Date().toISOString()
    };
    localStorage.setItem("jupiterPublicObservationNotes", JSON.stringify(notes));
    state.data.notes[state.current.opus_id] = notes[state.current.opus_id];
    $("save-state").textContent = "saved in this browser";
    return;
  }
  const response = await fetch("/api/notes", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      opus_id: state.current.opus_id,
      classification: $("classification").value,
      text: $("note").value,
      x: Number($("x").value),
      y: Number($("y").value),
    }),
  });
  $("save-state").textContent = response.ok ? "saved locally" : "save failed";
  if (response.ok) {
    state.data.notes[state.current.opus_id] = {
      classification: $("classification").value,
      text: $("note").value,
      x: Number($("x").value),
      y: Number($("y").value),
    };
  }
}

async function handleUpload(file) {
  if (!file) return;
  const bitmap = await createImageBitmap(file);
  const now = new Date().toISOString();
  const record = {
    id: `upload-${crypto.randomUUID()}`,
    name: file.name,
    type: file.type,
    size: file.size,
    width: bitmap.width,
    height: bitmap.height,
    created_at: now,
    updated_at: now,
    blob: file,
    classification: "review",
    note: "",
    history: [],
  };
  bitmap.close();
  await libraryPut(record);
  await renderLibrary();
  await checkStorage();
  await selectUpload(record);
}

async function addDroppedFile(file) {
  try {
    await handleUpload(file);
    selectTab("manual");
  } catch (error) {
    alert(`Could not add image: ${error.message}`);
  }
}

async function renderLibrary() {
  const records = await libraryAll();
  const container = $("library-list");
  if (!records.length) {
    container.innerHTML = `<p class="empty-library">No uploaded images yet. Add a PNG or JPEG from OPUS to begin an open-ended local collection.</p>`;
    return;
  }
  container.innerHTML = "";
  records.forEach((record) => {
    const row = document.createElement("article");
    row.className = "library-item";
    const imageUrl = URL.createObjectURL(record.blob);
    const recentHistory = (record.history || []).slice(-8).reverse();
    const historyHtml = recentHistory.length
      ? recentHistory.map((entry) => `
          <li>
            ${new Date(entry.saved_at).toLocaleString()} -
            crop ${entry.settings.crop}px -
            output ${Math.round(entry.settings.scale * 100)}% -
            stretch ${entry.settings.low}-${entry.settings.high}% -
            gamma ${entry.settings.gamma}
          </li>`).join("")
      : "<li>No processing changes saved yet.</li>";
    row.innerHTML = `
      <img src="${imageUrl}" alt="">
      <div>
        <h3>${escapeHtml(record.name)}</h3>
        <p>${record.width} x ${record.height} - ${formatBytes(record.size)} - ${record.history?.length || 0} history entries - ${escapeHtml(record.classification || "review")}</p>
        <details>
          <summary>Recent processing history</summary>
          <ol>${historyHtml}</ol>
        </details>
      </div>
      <div class="library-item-actions">
        <button type="button" data-open>Open</button>
        <button type="button" data-delete>Remove</button>
      </div>`;
    row.querySelector("[data-open]").addEventListener("click", async () => {
      await selectUpload(await libraryGet(record.id));
    });
    row.querySelector("[data-delete]").addEventListener("click", async () => {
      if (!confirm(`Remove "${record.name}" from the local library?`)) return;
      if (state.current?.id === record.id) selectObservation(state.data.observations[0]);
      await libraryDelete(record.id);
      URL.revokeObjectURL(imageUrl);
      await renderLibrary();
      await checkStorage();
    });
    row.querySelector("img").addEventListener("load", () => URL.revokeObjectURL(imageUrl), {once: true});
    container.appendChild(row);
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

function dataUrlToBlob(dataUrl) {
  const [header, data] = dataUrl.split(",");
  const mime = header.match(/data:(.*?);base64/)?.[1] || "application/octet-stream";
  const bytes = Uint8Array.from(atob(data), (character) => character.charCodeAt(0));
  return new Blob([bytes], {type: mime});
}

async function exportLibrary() {
  const records = await libraryAll();
  const portable = [];
  for (const record of records) {
    portable.push({...record, blob: await blobToDataUrl(record.blob)});
  }
  const backup = {
    format: "jupiter-lightning-library",
    version: 1,
    exported_at: new Date().toISOString(),
    images: portable,
  };
  const blob = new Blob([JSON.stringify(backup, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `jupiter-lightning-library-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function importLibrary(file) {
  const backup = JSON.parse(await file.text());
  if (backup.format !== "jupiter-lightning-library" || !Array.isArray(backup.images)) {
    throw new Error("This is not a Jupiter Lightning Workbench library backup.");
  }
  for (const image of backup.images) {
    await libraryPut({...image, blob: dataUrlToBlob(image.blob)});
  }
  await renderLibrary();
  await checkStorage();
}

async function checkStorage() {
  if (!navigator.storage?.estimate) return;
  const {usage = 0, quota = 0} = await navigator.storage.estimate();
  const ratio = quota ? usage / quota : 0;
  $("storage-copy").textContent = `${formatBytes(usage)} used of ${formatBytes(quota)} browser storage (${Math.round(ratio * 100)}%)`;
  $("storage-fill").style.width = `${Math.min(100, ratio * 100)}%`;
  if (ratio >= 0.85 && !state.storageWarned) {
    state.storageWarned = true;
    const shouldExport = confirm("Local browser storage is nearly full. Export the image library now?");
    if (shouldExport) await exportLibrary();
  }
}

function exportProcessed() {
  if (state.current.source_type !== "upload" && state.backendAvailable) {
    window.location.href = processUrl(true);
    return;
  }
  const anchor = document.createElement("a");
  anchor.href = state.processedDataUrl;
  anchor.download = `${state.current.name.replace(/\.[^.]+$/, "")}-processed.png`;
  anchor.click();
}

function selectTab(name) {
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tabTarget === name);
  });
  document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.tabPanel === name);
  });
}

async function init() {
  await loadRuntime();
  configureRuntimeNavigation();
  renderStrip();
  controls.forEach((id) => $(id).addEventListener("input", scheduleUpdate));
  $("run-detector").addEventListener("click", runDetectorAgain);
  document.querySelectorAll("#detection-date-tabs button").forEach((button) => {
    button.addEventListener("click", () => selectDetectionDate(button.dataset.date));
  });
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.addEventListener("click", () => selectTab(button.dataset.tabTarget));
  });
  $("notes-form").addEventListener("submit", saveNote);
  $("export").addEventListener("click", exportProcessed);
  $("upload").addEventListener("click", () => $("upload-file").click());
  $("drop-zone").addEventListener("click", () => $("upload-file").click());
  $("drop-zone").addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      $("upload-file").click();
    }
  });
  $("drop-zone").addEventListener("dragover", (event) => {
    event.preventDefault();
    $("drop-zone").classList.add("drag-over");
  });
  $("drop-zone").addEventListener("dragleave", () => $("drop-zone").classList.remove("drag-over"));
  $("drop-zone").addEventListener("drop", async (event) => {
    event.preventDefault();
    $("drop-zone").classList.remove("drag-over");
    await addDroppedFile(event.dataTransfer.files[0]);
  });
  $("upload-file").addEventListener("change", async () => {
    try {
      await handleUpload($("upload-file").files[0]);
    } catch (error) {
      alert(`Could not add image: ${error.message}`);
    } finally {
      $("upload-file").value = "";
    }
  });
  $("export-library").addEventListener("click", exportLibrary);
  $("import-library").addEventListener("click", () => $("import-file").click());
  $("import-file").addEventListener("change", async () => {
    try {
      await importLibrary($("import-file").files[0]);
    } catch (error) {
      alert(`Could not import library: ${error.message}`);
    } finally {
      $("import-file").value = "";
    }
  });
  $("original").addEventListener("click", (event) => placeCoordinate(event, $("original"), true));
  $("processed").addEventListener("click", (event) => placeCoordinate(event, $("processed")));
  await renderLibrary();
  await checkStorage();
  selectObservation(state.data.observations[0]);
  await loadCandidateLabels();
  await Promise.allSettled([
    loadDetectionReview(),
    loadValidation(),
    loadDetectorCharacteristics(),
    refreshDetectorStatus(),
  ]);
  if (!state.backendAvailable) selectTab("review");
}

init();
