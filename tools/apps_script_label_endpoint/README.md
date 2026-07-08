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
4. Confirm `SHEET_NAME` is `Labels`.
5. Deploy as **Web app**.
6. Execute as **Me**.
7. Access: choose the narrowest option that still lets reviewers submit.
8. Copy the web app URL.
9. Paste that URL into the public review page's Google Sheets endpoint field.

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
