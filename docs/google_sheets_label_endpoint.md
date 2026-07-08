# Google Sheets Label Endpoint

The public Vercel review page can append labels to a shared Google Sheet through
a Google Apps Script web app. This keeps the public site static while allowing
multiple reviewers to contribute rows.

## Sheet Columns

Create a Google Sheet with this header row:

```text
candidate_id,image_id,run_date,x,y,jupiter_latitude,jupiter_longitude,geometry_status,snr,blob_size,candidate_score,artifact_flags,reviewer_label,human_label,label,reviewer,notes,review_note,timestamp,reviewed_at,source
```

## Apps Script

Open **Extensions -> Apps Script** in the Sheet and paste:

```javascript
Use the ready-to-copy script in:

```text
tools/google_sheets_label_endpoint.gs
```

It includes the current review fields plus reserved geometry columns:

```text
jupiter_latitude,jupiter_longitude,geometry_status
```
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
