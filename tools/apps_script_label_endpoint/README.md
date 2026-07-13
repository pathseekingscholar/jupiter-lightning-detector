# Google Apps Script Label Endpoint

This folder is a deployable Apps Script project for appending public review
labels to the shared Google Sheet.

Shared Sheet:

```text
https://docs.google.com/spreadsheets/d/1c8JX_e_Jcy8N-odK6AFEHUMP3NYIrJq7YCPTBuUI3bg
```

## Manual Deployment

1. Open the shared Sheet.
2. Go to **Extensions -> Apps Script**.
3. Replace the default code with `Code.gs`.
4. Confirm the spreadsheet ID and `SHEET_NAME` match the shared project Sheet.
5. Deploy as **Web app**.
6. Execute as **Me**.
7. Access: choose **Anyone** so invited public reviewers can submit without a Google Apps Script login prompt.
8. Copy the web app URL ending in `/exec`.
9. Store that URL in `public_site/static-data/collaboration_config.json` as `apps_script_endpoint`.
10. Open the URL in a browser and verify the health response before deploying the site.

## Optional `clasp` Deployment

If `clasp` is installed and authenticated:

```powershell
cd tools\apps_script_label_endpoint
clasp create --type webapp --title "Jupiter Lightning Label Endpoint"
clasp push
clasp deploy --description "Public review label append endpoint"
```

Then copy the deployment web app URL into:

```text
public_site/static-data/collaboration_config.json
```

and redeploy the public site.
