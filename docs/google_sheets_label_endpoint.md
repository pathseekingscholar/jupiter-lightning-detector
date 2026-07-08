# Google Sheets Label Endpoint

The public Vercel review page can append labels to a shared Google Sheet through
a Google Apps Script web app. This keeps the public site static while allowing
multiple reviewers to contribute rows.

## Current Shared Sheet

The initial shared label sheet has been created:

```text
Title: Jupiter Lightning Candidate Labels
Spreadsheet ID: 1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg
URL: https://docs.google.com/spreadsheets/d/1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg
```

The public site also stores this in:

```text
public_site/static-data/collaboration_config.json
```

Direct browser appends still require the Apps Script web app deployment URL.

## Sheet Columns

Create a Google Sheet with this header row:

```text
candidate_id,image_id,run_date,x,y,jupiter_latitude,jupiter_longitude,geometry_status,snr,blob_size,candidate_score,artifact_flags,reviewer_label,human_label,label,reviewer,notes,review_note,timestamp,reviewed_at,source
```

## Apps Script

Open **Extensions -> Apps Script** in the Sheet and paste:

```javascript
Use the ready-to-copy script or deployable Apps Script folder in:

```text
tools/google_sheets_label_endpoint.gs
tools/apps_script_label_endpoint/
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
