const $ = (id) => document.getElementById(id);

const state = {
  rows: [],
  selected: null,
  labels: JSON.parse(localStorage.getItem("jupiterPublicReviewLabels") || "{}"),
  endpoint: localStorage.getItem("jupiterGoogleSheetEndpoint") || "",
  reviewer: localStorage.getItem("jupiterReviewerName") || ""
};

const labelOptions = [
  ["", "Choose label"],
  ["known-lightning", "Known Lightning"],
  ["possible-lightning", "Possible Lightning"],
  ["artifact", "Artifact"],
  ["cosmic-ray-hot-pixel", "Cosmic Ray / Hot Pixel"],
  ["uncertain", "Uncertain"]
];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeRow(row) {
  return {
    ...row,
    review_order: Number(row.review_order),
    x: toNumber(row.x),
    y: toNumber(row.y),
    jupiter_latitude: row.jupiter_latitude === "" ? "" : toNumber(row.jupiter_latitude, ""),
    jupiter_longitude: row.jupiter_longitude === "" ? "" : toNumber(row.jupiter_longitude, ""),
    geometry_status: row.geometry_status || "pending-backplane",
    snr: toNumber(row.snr),
    blob_size: toNumber(row.blob_size),
    frame_count: toNumber(row.frame_count),
    candidate_score: toNumber(row.candidate_score)
  };
}

function labelFor(candidateId) {
  return state.labels[candidateId] || {};
}

function saveLabels() {
  localStorage.setItem("jupiterPublicReviewLabels", JSON.stringify(state.labels));
  const labels = Object.values(state.labels);
  const sheetsSent = labels.filter((row) => row.sheet_status === "sent").length;
  $("label-count").textContent = `${labels.length} labels saved in this browser${sheetsSent ? `; ${sheetsSent} sent to Sheets endpoint` : ""}`;
}

function activateTab(target) {
  document.querySelectorAll("[data-tab-target]").forEach((button) => {
    button.classList.toggle("active", button.dataset.tabTarget === target);
  });
  document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
    panel.classList.toggle("active", panel.dataset.tabPanel === target);
  });
}

function renderCoverage(payload) {
  const grid = $("coverage-grid");
  const summary = payload.summary || {};
  const coverage = payload.coverage || [];
  const totalImages = coverage.reduce((sum, row) => sum + toNumber(row.image_count || row.images || row.processed_images), 0);
  grid.innerHTML = `
    <article><b>First-pass rows</b><p>${payload.row_count || state.rows.length} prioritized review candidates loaded from detector outputs.</p></article>
    <article><b>Known validation</b><p>Published matches remain validation targets, not training shortcuts.</p></article>
    <article><b>Processed images</b><p>${totalImages || "221"} image records in the current processed review subset.</p></article>
    <article><b>Static boundary</b><p>New detector runs and crop rendering require the Python backend.</p></article>
    <article><b>Candidate status</b><p>${summary.review_candidates || "Review"} candidates are for classification, not confirmed lightning.</p></article>
    <article><b>Training use</b><p>Saved labels become examples for later model comparison.</p></article>
    <article><b>Geometry</b><p>${escapeHtml(payload.geometry_note || "Latitude/longitude are pending backplane support.")}</p></article>
  `;
  $("geometry-status").textContent = payload.geometry_note || "Jupiter latitude/longitude are pending backplane support.";
  $("geometry-tolerance").value = payload.default_lat_lon_tolerance_degrees || 1.0;
  const hasGeometry = state.rows.some((row) => row.jupiter_latitude !== "" && row.jupiter_longitude !== "");
  $("group-geometry").disabled = !hasGeometry;
  if (hasGeometry) {
    $("geometry-status").textContent = "Latitude/longitude fields are present. Grouping can compare candidates within the selected tolerance.";
  }
}

function geometryGroups(toleranceDegrees) {
  const groups = [];
  const rowsWithGeometry = state.rows.filter((row) => row.jupiter_latitude !== "" && row.jupiter_longitude !== "");
  rowsWithGeometry.forEach((row) => {
    const existing = groups.find((group) => (
      Math.abs(group.latitude - Number(row.jupiter_latitude)) <= toleranceDegrees
      && Math.abs(group.longitude - Number(row.jupiter_longitude)) <= toleranceDegrees
    ));
    if (existing) {
      existing.rows.push(row);
    } else {
      groups.push({
        latitude: Number(row.jupiter_latitude),
        longitude: Number(row.jupiter_longitude),
        rows: [row]
      });
    }
  });
  return groups;
}

function renderCandidateList() {
  const list = $("candidate-list");
  if (!state.rows.length) {
    list.textContent = "No candidates loaded.";
    return;
  }
  list.innerHTML = state.rows.map((row) => {
    const saved = labelFor(row.candidate_id).reviewer_label;
    return `
      <button type="button" class="candidate-button ${state.selected?.candidate_id === row.candidate_id ? "active" : ""}" data-candidate-id="${escapeHtml(row.candidate_id)}">
        <b>#${row.review_order} ${escapeHtml(row.candidate_id)} ${saved ? `<span class="saved-pill">${escapeHtml(saved)}</span>` : ""}</b>
        <span>${escapeHtml(row.image_id)} | ${escapeHtml(row.run_date)} | score ${row.candidate_score.toFixed(3)}</span>
        <small>${escapeHtml(row.review_batch)} | SNR ${row.snr.toFixed(2)} | blob ${row.blob_size}</small>
      </button>
    `;
  }).join("");
  list.querySelectorAll("[data-candidate-id]").forEach((button) => {
    button.addEventListener("click", () => selectCandidate(button.dataset.candidateId));
  });
}

function renderCandidateDetail() {
  const detail = $("candidate-detail");
  const row = state.selected;
  if (!row) {
    detail.innerHTML = "<p>Select a candidate to review.</p>";
    return;
  }
  const saved = labelFor(row.candidate_id);
  const options = labelOptions.map(([value, text]) => (
    `<option value="${value}" ${saved.reviewer_label === value ? "selected" : ""}>${text}</option>`
  )).join("");
  const cropMessage = row.crop_url?.startsWith("/api/")
    ? "Crop rendering is backend-only for this row. Use the local Python workbench for image crops."
    : "Static crop is available.";
  const latText = row.jupiter_latitude === "" ? "pending" : Number(row.jupiter_latitude).toFixed(3);
  const lonText = row.jupiter_longitude === "" ? "pending" : Number(row.jupiter_longitude).toFixed(3);
  detail.innerHTML = `
    <p class="section-label">Candidate Detail</p>
    <h3>${escapeHtml(row.candidate_id)}</h3>
    <p>${escapeHtml(row.reviewer_task || "Review this detector candidate.")}</p>
    <div class="detail-grid">
      <div><b>Image</b>${escapeHtml(row.image_id)}</div>
      <div><b>Date</b>${escapeHtml(row.run_date)}</div>
      <div><b>X/Y</b>${row.x.toFixed(2)}, ${row.y.toFixed(2)}</div>
      <div><b>SNR</b>${row.snr.toFixed(2)}</div>
      <div><b>Blob size</b>${row.blob_size}</div>
      <div><b>Score</b>${row.candidate_score.toFixed(4)}</div>
      <div><b>Frame count</b>${row.frame_count || ""}</div>
      <div><b>Suggested</b>${escapeHtml(row.suggested_human_label || "")}</div>
      <div><b>Flags</b>${escapeHtml(row.artifact_flags || "none")}</div>
      <div><b>Jupiter lat</b>${escapeHtml(latText)}</div>
      <div><b>Jupiter lon</b>${escapeHtml(lonText)}</div>
      <div><b>Geometry</b>${escapeHtml(row.geometry_status)}</div>
    </div>
    <div class="backend-box">
      <b>Image crop</b>
      <span>${cropMessage}</span>
      <code>${escapeHtml(row.crop_url || "")}</code>
    </div>
    <form class="label-form" id="label-form">
      <div class="label-row">
        <label>Reviewer label
          <select id="candidate-label">${options}</select>
        </label>
        <label>Reviewer
          <input id="candidate-reviewer" type="text" value="${escapeHtml(saved.reviewer || state.reviewer || "")}" placeholder="name or initials">
        </label>
      </div>
      <label>Notes
        <textarea id="candidate-notes" placeholder="${escapeHtml(row.review_note_prompt || "Why keep or reject this candidate?")}">${escapeHtml(saved.notes || "")}</textarea>
      </label>
      <button type="submit" class="primary">Save label</button>
    </form>
  `;
  $("label-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await saveCandidateLabel(row);
  });
}

function selectCandidate(candidateId) {
  state.selected = state.rows.find((row) => row.candidate_id === candidateId) || state.rows[0] || null;
  renderCandidateList();
  renderCandidateDetail();
}

function labelPayload(row) {
  const reviewerLabel = $("candidate-label").value;
  const reviewer = $("candidate-reviewer").value.trim() || "anonymous-reviewer";
  const notes = $("candidate-notes").value.trim();
  const now = new Date().toISOString();
  return {
    candidate_id: row.candidate_id,
    image_id: row.image_id,
    run_date: row.run_date,
    x: row.x.toFixed(2),
    y: row.y.toFixed(2),
    jupiter_latitude: row.jupiter_latitude === "" ? "" : String(row.jupiter_latitude),
    jupiter_longitude: row.jupiter_longitude === "" ? "" : String(row.jupiter_longitude),
    geometry_status: row.geometry_status || "pending-backplane",
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
    source: "public-vercel-static-review"
  };
}

async function saveCandidateLabel(row) {
  const payload = labelPayload(row);
  if (!payload.reviewer_label) {
    alert("Choose a label before saving.");
    return;
  }
  state.reviewer = payload.reviewer;
  localStorage.setItem("jupiterReviewerName", payload.reviewer);
  state.labels[row.candidate_id] = payload;
  saveLabels();
  renderCandidateList();
  renderCandidateDetail();
  if (state.endpoint) {
    try {
      await fetch(state.endpoint, {
        method: "POST",
        mode: "no-cors",
        headers: {"Content-Type": "text/plain;charset=utf-8"},
        body: JSON.stringify(payload)
      });
      payload.sheet_status = "sent";
      state.labels[row.candidate_id] = payload;
      saveLabels();
      $("sheet-status").textContent = "Label sent to configured Google Sheets endpoint. Browser cannot verify no-cors response.";
    } catch (error) {
      $("sheet-status").textContent = `Local label saved. Google Sheets append failed: ${error.message}`;
    }
  } else {
    $("sheet-status").textContent = "Local label saved. Configure a Google Apps Script URL to append future labels to a shared sheet.";
  }
}

function downloadText(filename, content, type) {
  const blob = new Blob([content], {type});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function exportJson() {
  downloadText("jupiter_candidate_labels.json", JSON.stringify(Object.values(state.labels), null, 2), "application/json");
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function exportCsv() {
  const rows = Object.values(state.labels);
  const fields = ["candidate_id", "image_id", "run_date", "x", "y", "jupiter_latitude", "jupiter_longitude", "geometry_status", "snr", "blob_size", "candidate_score", "artifact_flags", "reviewer_label", "human_label", "label", "reviewer", "notes", "review_note", "timestamp", "reviewed_at", "sheet_status", "source"];
  const csv = [fields.join(","), ...rows.map((row) => fields.map((field) => csvEscape(row[field])).join(","))].join("\n");
  downloadText("jupiter_candidate_labels.csv", csv, "text/csv");
}

async function loadData() {
  const response = await fetch("/static-data/first_pass_review_queue.json");
  const payload = await response.json();
  state.rows = payload.rows.map(normalizeRow);
  $("snapshot-count").textContent = `${state.rows.length} first-pass review rows loaded`;
  $("reviewer-name").value = state.reviewer;
  $("sheet-endpoint").value = state.endpoint;
  if (state.endpoint) {
    $("sheet-status").textContent = "Google Sheets endpoint configured in this browser.";
  }
  saveLabels();
  renderCoverage(payload);
  renderCandidateList();
  selectCandidate(state.rows[0]?.candidate_id);
}

document.querySelectorAll("[data-tab-target]").forEach((button) => {
  button.addEventListener("click", () => activateTab(button.dataset.tabTarget));
});

$("reviewer-name").addEventListener("input", (event) => {
  state.reviewer = event.target.value.trim();
  localStorage.setItem("jupiterReviewerName", state.reviewer);
});

$("save-sheet-endpoint").addEventListener("click", () => {
  state.endpoint = $("sheet-endpoint").value.trim();
  localStorage.setItem("jupiterGoogleSheetEndpoint", state.endpoint);
  $("sheet-status").textContent = state.endpoint
    ? "Google Sheets endpoint saved in this browser. Future labels will be sent when saved."
    : "Google Sheets endpoint cleared. Labels will remain local until exported.";
});

$("group-geometry").addEventListener("click", () => {
  const tolerance = toNumber($("geometry-tolerance").value, 1.0);
  const groups = geometryGroups(tolerance);
  $("geometry-status").textContent = groups.length
    ? `${groups.length} geometry group(s) found within ${tolerance} degree tolerance.`
    : "No candidates currently have latitude/longitude values to group.";
});

$("export-json").addEventListener("click", exportJson);
$("export-csv").addEventListener("click", exportCsv);

loadData().catch((error) => {
  $("candidate-list").textContent = `Could not load candidate queue: ${error.message}`;
  $("snapshot-count").textContent = "Candidate queue failed to load";
});
