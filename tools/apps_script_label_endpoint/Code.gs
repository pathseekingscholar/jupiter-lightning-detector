const SHEET_NAME = "Labels";

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const payload = JSON.parse((e.postData && e.postData.contents) || "{}");
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME)
      || SpreadsheetApp.getActiveSpreadsheet().insertSheet(SHEET_NAME);
    const headers = [
      "candidate_id",
      "image_id",
      "run_date",
      "x",
      "y",
      "jupiter_latitude",
      "jupiter_longitude",
      "geometry_status",
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
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(headers);
    }
    sheet.appendRow(headers.map((header) => payload[header] || ""));
    return ContentService
      .createTextOutput(JSON.stringify({ok: true}))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}
