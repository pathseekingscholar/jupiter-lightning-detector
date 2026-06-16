const state = {
  data: null,
  current: null,
  detection: null,
  validation: null,
  detectorStatusTimer: null,
  timer: null,
  historyTimer: null,
  originalObjectUrl: null,
  processedDataUrl: null,
  storageWarned: false,
};

const $ = (id) => document.getElementById(id);
const controls = ["scale", "crop", "low", "high", "gamma", "x", "y", "mark"];
const DB_NAME = "jupiter-lightning-library";
const DB_VERSION = 1;
const IMAGE_STORE = "images";

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
    button.innerHTML = `N${observation.image_number}<span>${observation.start_time.slice(0, 10)} · ${observation.filter_name} · ${observation.exposure_seconds}s</span>`;
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
    <dt>Scale</dt><dd>${observation.center_resolution_km.toFixed(1)} km px⁻¹</dd>`;
  renderCandidates();
  const saved = state.data.notes[observation.opus_id] || {};
  $("classification").value = saved.classification || "published";
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
    <dt>Dimensions</dt><dd>${record.width} × ${record.height}</dd>
    <dt>File type</dt><dd>${record.type || "image"}</dd>
    <dt>History</dt><dd>${record.history?.length || 0} settings</dd>`;
  $("x").value = record.last_settings?.x || Math.round(record.width / 2);
  $("y").value = record.last_settings?.y || Math.round(record.height / 2);
  $("classification").value = record.classification || "review";
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
    return;
  }
  $("contact-sheet-link").href = state.detection.contact_sheet_url;
  $("contact-sheet").src = `${state.detection.contact_sheet_url}?t=${Date.now()}`;
  $("detection-summary").textContent =
    `${summary.frames || 0} long-exposure H-alpha frames scanned, ${summary.candidates || 0} bright regions found, ` +
    `${summary.review_candidates || 0} review candidates after artifact filters. This is a review queue, not a confirmed lightning catalog.`;

  const topTracks = tracks.slice(0, 18);
  $("track-list").innerHTML = topTracks.map((track) => {
    const lead = track.items[0];
    const cropUrl = `/api/detection-crop?image=${encodeURIComponent(lead.image_number)}&x=${Math.round(lead.x)}&y=${Math.round(lead.y)}&crop=128`;
    const frames = track.items.map((item) => `N${item.image_number}`).join(" -> ");
    return `
      <article class="track-card" data-candidate-id="${lead.candidate_id}">
        <button type="button" class="track-open" data-candidate-id="${lead.candidate_id}">
          <img src="${cropUrl}" alt="">
          <span>
            <b>Possible track ${track.track_id}</b>
            <small>review priority ${track.confidence.toFixed(2)} / seen in ${track.track_length} frame(s)</small>
          </span>
        </button>
        <dl>
          <dt>Lead frame</dt><dd>N${lead.image_number}</dd>
          <dt>Coordinate</dt><dd>${lead.x.toFixed(1)}, ${lead.y.toFixed(1)}</dd>
          <dt>Peak SNR</dt><dd>${lead.peak_snr.toFixed(1)}</dd>
          <dt>Area</dt><dd>${lead.area_px} px</dd>
        </dl>
        <p>${escapeHtml(track.reason)}</p>
        <p class="track-frames">Frames linked by detector: ${escapeHtml(frames)}</p>
      </article>`;
  }).join("");
  const candidatesById = new Map();
  topTracks.forEach((track) => track.items.forEach((item) => candidatesById.set(item.candidate_id, item)));
  document.querySelectorAll(".track-open").forEach((button) => {
    button.addEventListener("click", () => selectDetectionCandidate(candidatesById.get(button.dataset.candidateId)));
  });
}

async function loadDetectionReview() {
  const response = await fetch("/api/detection");
  state.detection = await response.json();
  renderDetectionReview();
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
}

async function loadValidation() {
  const response = await fetch("/api/validation");
  state.validation = await response.json();
  renderValidation();
}

function renderDetectorStatus(status) {
  $("detector-status").textContent = status.message || "Detector idle.";
  $("run-detector").disabled = Boolean(status.running);
}

async function refreshDetectorStatus() {
  const response = await fetch("/api/detection-status");
  const status = await response.json();
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
  renderDetectorStatus({running: true, message: "Starting detector..."});
  await fetch("/api/run-detection", {method: "POST"});
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

async function renderUploadedImage() {
  const record = await libraryGet(state.current.id);
  const bitmap = await createImageBitmap(record.blob);
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
  $("save-state").textContent = "saving…";
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
            ${new Date(entry.saved_at).toLocaleString()} ·
            crop ${entry.settings.crop}px ·
            output ${Math.round(entry.settings.scale * 100)}% ·
            stretch ${entry.settings.low}–${entry.settings.high}% ·
            gamma ${entry.settings.gamma}
          </li>`).join("")
      : "<li>No processing changes saved yet.</li>";
    row.innerHTML = `
      <img src="${imageUrl}" alt="">
      <div>
        <h3>${escapeHtml(record.name)}</h3>
        <p>${record.width} × ${record.height} · ${formatBytes(record.size)} · ${record.history?.length || 0} history entries · ${escapeHtml(record.classification || "review")}</p>
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
  if (state.current.source_type !== "upload") {
    window.location.href = processUrl(true);
    return;
  }
  const anchor = document.createElement("a");
  anchor.href = state.processedDataUrl;
  anchor.download = `${state.current.name.replace(/\.[^.]+$/, "")}-processed.png`;
  anchor.click();
}

async function init() {
  const response = await fetch("/api/observations");
  state.data = await response.json();
  renderStrip();
  await loadDetectionReview();
  await loadValidation();
  await refreshDetectorStatus();
  controls.forEach((id) => $(id).addEventListener("input", scheduleUpdate));
  $("run-detector").addEventListener("click", runDetectorAgain);
  $("notes-form").addEventListener("submit", saveNote);
  $("export").addEventListener("click", exportProcessed);
  $("upload").addEventListener("click", () => $("upload-file").click());
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
}

init();
