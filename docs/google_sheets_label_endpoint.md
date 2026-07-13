# Google Sheets label endpoint

The review page keeps a browser backup and can submit the same row to a shared
Google Sheet through a Google Apps Script web app.

Shared Sheet:

```text
Title: Jupiter Lightning Candidate Labels
Spreadsheet ID: 1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg
URL: https://docs.google.com/spreadsheets/d/1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg
Tab: Jupiter Lightning Candidate Labels
```

The header is frozen and filterable. The `reviewer_label` column accepts only:

```text
known-lightning
possible-lightning
artifact
cosmic-ray-hot-pixel
uncertain
```

## Deploy the append endpoint

1. Sign into the Google account that owns the Sheet.
2. Open the Sheet and choose **Extensions -> Apps Script**.
3. Replace the editor contents with `tools/apps_script_label_endpoint/Code.gs`.
4. Choose **Deploy -> New deployment -> Web app**.
5. Execute as **Me** and allow **Anyone** to access the web app.
6. Copy the URL ending in `/exec`.
7. Put it in `public_site/static-data/collaboration_config.json` as
   `apps_script_endpoint` and set `apps_script_status` to `deployed`.
8. Run `.\run.ps1 public-site-data`, redeploy, and save one test label.
9. Verify the appended row directly in the Sheet.

The script opens the spreadsheet by its exact ID, writes to the exact tab,
validates allowed labels, serializes concurrent saves with a lock, and prevents
review text from being interpreted as a spreadsheet formula.

The public site sends with `no-cors`, so a successful browser dispatch cannot
read the Apps Script response. CSV/JSON export remains the reviewer backup, and
the final integration test is the presence of the test row in the Sheet.
