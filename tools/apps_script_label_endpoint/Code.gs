const SPREADSHEET_ID = "1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg";
const SHEET_NAME = "Jupiter Lightning Candidate Labels";
const HEADERS = [
  "candidate_id",
  "image_id",
  "run_date",
  "x",
  "y",
  "jupiter_latitude",
  "jupiter_longitude",
  "geometry_status",
  "geometry_group_id",
  "geometry_group_size",
  "snr",
  "blob_size",
  "candidate_score",
  "artifact_flags",
  "reviewer_label",
  "human_label",
  "label",
  "reviewer",
  "notes",
  "review_note",
  "timestamp",
  "reviewed_at",
  "source"
];
const ALLOWED_LABELS = [
  "known-lightning",
  "possible-lightning",
  "artifact",
  "cosmic-ray-hot-pixel",
  "uncertain"
];

function jsonResponse(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function sheetForLabels() {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  return spreadsheet.getSheetByName(SHEET_NAME) || spreadsheet.insertSheet(SHEET_NAME);
}

function safeCell(value) {
  if (value === null || value === undefined) return "";
  const text = String(value).slice(0, 5000);
  return /^[=+\-@]/.test(text) ? `'${text}` : text;
}

function doGet() {
  const sheet = sheetForLabels();
  return jsonResponse({
    ok: true,
    service: "jupiter-lightning-candidate-labels",
    sheet: SHEET_NAME,
    saved_rows: Math.max(0, sheet.getLastRow() - 1)
  });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const payload = JSON.parse((e.postData && e.postData.contents) || "{}");
    if (!payload.candidate_id || !ALLOWED_LABELS.includes(String(payload.reviewer_label || payload.human_label || payload.label))) {
      return jsonResponse({ok: false, error: "candidate_id and an allowed reviewer label are required"});
    }
    const sheet = sheetForLabels();
    if (sheet.getLastRow() === 0) sheet.appendRow(HEADERS);
    sheet.appendRow(HEADERS.map((header) => safeCell(payload[header])));
    SpreadsheetApp.flush();
    return jsonResponse({
      ok: true,
      candidate_id: String(payload.candidate_id),
      row: sheet.getLastRow()
    });
  } catch (error) {
    return jsonResponse({ok: false, error: String(error && error.message || error)});
  } finally {
    lock.releaseLock();
  }
}
