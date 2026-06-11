const state = {
  data: null,
  current: null,
  timer: null,
};

const $ = (id) => document.getElementById(id);
const controls = ["scale", "crop", "low", "high", "gamma", "x", "y", "mark"];

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

function selectObservation(observation) {
  state.current = observation;
  document.querySelectorAll(".observation-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.opus === observation.opus_id);
  });
  $("image-title").textContent = `N${observation.image_number}`;
  $("original").src = observation.preview_image.replaceAll("\\", "/").replace(/^.*\/data\//, "/data/");
  $("metadata").innerHTML = `
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

function renderCandidates() {
  $("candidate-body").innerHTML = state.current.candidates.map((candidate) => `
    <tr data-x="${candidate.x}" data-y="${candidate.y}">
      <td>${candidate.label}</td>
      <td>(${candidate.x}, ${candidate.y})</td>
      <td>${candidate.peak_snr.toFixed(1)}</td>
      <td>${candidate.bright_pixel_count}</td>
      <td>${(candidate.published_power_w / 1e9).toFixed(3)} GW</td>
    </tr>`).join("");
  document.querySelectorAll("#candidate-body tr").forEach((row) => {
    row.addEventListener("click", () => {
      $("x").value = row.dataset.x;
      $("y").value = row.dataset.y;
      updateProcessed();
    });
  });
}

function updateOutputs() {
  $("low-out").textContent = `${Number($("low").value).toFixed(1)}%`;
  $("high-out").textContent = `${Number($("high").value).toFixed(1)}%`;
  $("gamma-out").textContent = Number($("gamma").value).toFixed(1);
}

function updateProcessed() {
  if (!state.current) return;
  updateOutputs();
  $("loading").classList.add("visible");
  const image = $("processed");
  image.style.opacity = ".55";
  image.onload = () => {
    $("loading").classList.remove("visible");
    image.style.opacity = "1";
  };
  image.src = processUrl();
}

function scheduleUpdate() {
  clearTimeout(state.timer);
  state.timer = setTimeout(updateProcessed, 120);
}

function placeCoordinate(event, imageElement, fullFrame = false) {
  if (!state.current) return;
  const rect = imageElement.getBoundingClientRect();
  const crop = fullFrame ? 1024 : Number($("crop").value);
  const currentX = Number($("x").value);
  const currentY = Number($("y").value);
  const x0 = fullFrame ? 0 : Math.max(0, Math.min(1024 - crop, currentX - crop / 2));
  const y0 = fullFrame ? 0 : Math.max(0, Math.min(1024 - crop, currentY - crop / 2));
  const localX = ((event.clientX - rect.left) / rect.width) * crop;
  const localY = ((event.clientY - rect.top) / rect.height) * crop;
  $("x").value = Math.max(1, Math.min(1024, Math.round(x0 + localX)));
  $("y").value = Math.max(1, Math.min(1024, Math.round(y0 + localY)));
  updateProcessed();
}

async function saveNote(event) {
  event.preventDefault();
  $("save-state").textContent = "saving…";
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

async function init() {
  const response = await fetch("/api/observations");
  state.data = await response.json();
  renderStrip();
  controls.forEach((id) => $(id).addEventListener("input", scheduleUpdate));
  $("notes-form").addEventListener("submit", saveNote);
  $("export").addEventListener("click", () => { window.location.href = processUrl(true); });
  $("original").addEventListener("click", (event) => placeCoordinate(event, $("original"), true));
  $("processed").addEventListener("click", (event) => placeCoordinate(event, $("processed")));
  selectObservation(state.data.observations[0]);
}

init();
