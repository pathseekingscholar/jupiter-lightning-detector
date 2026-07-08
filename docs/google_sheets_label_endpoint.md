# Google Sheets Label Endpoint

The public Vercel review page can append labels to a shared Google Sheet through
a Google Apps Script web app. This keeps the public site static while allowing
multiple reviewers to contribute rows.

## Sheet Columns

Create a Google Sheet with this header row:

```text
candidate_id,image_id,run_date,x,y,snr,blob_size,candidate_score,artifact_flags,reviewer_label,human_label,reviewer,notes,review_note,timestamp,reviewed_at,source
```

## Apps Script

Open **Extensions -> Apps Script** in the Sheet and paste:

```javascript
const SHEET_NAME = "Labels";

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const payload = JSON.parse(e.postData.contents || "{}");
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME)
      || SpreadsheetApp.getActiveSpreadsheet().insertSheet(SHEET_NAME);
    const headers = [
      "candidate_id",
      "image_id",
      "run_date",
      "x",
      "y",
      "snr",
      "blob_size",
      "candidate_score",
      "artifact_flags",
      "reviewer_label",
      "human_label",
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
```

Deploy it as a web app:

- Execute as: **Me**
- Who has access: choose the narrowest option that works for your reviewers
- Copy the web app URL

Paste that URL into the **Google Sheets connection** box on the public review
page. The browser stores the endpoint locally and sends future saved labels to
the Sheet.

## Current Limitation

The public site uses `no-cors` so the browser can send the row without a custom
backend, but it cannot verify the response body. Keep CSV/JSON export as a
backup after each review session.
