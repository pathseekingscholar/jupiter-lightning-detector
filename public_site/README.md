# Jupiter Lightning Detector Public Site

This folder contains the static public workbench deployed on Vercel:

https://jupiter-lightning-detector-public.vercel.app

It is generated from the same `web/index.html`, `web/styles.css`, `web/app.js`,
and `web/review.js` files used by the local workbench. It includes the 106-row
first-pass queue, candidate crops, full-frame display previews, adjustable
review stretching, date contact sheets, compact evidence tables, and CSV/JSON
label backups.

The online build is an evidence and review surface, not the detector engine. New
detector runs and calibrated-product processing still require Python and the
local OPUS data. The header states which mode is active.

The current candidate data snapshot is:

```text
public_site/static-data/first_pass_review_queue.json
```

The current collaboration and geometry snapshots are:

```text
public_site/static-data/collaboration_config.json
public_site/static-data/geometry_readiness.json
```

Regenerate the complete public bundle before a deployment when detector outputs
change:

```powershell
.\run.ps1 public-site-data
```

For shared labels, configure the Google Apps Script endpoint described in:

```text
docs/google_sheets_label_endpoint.md
```

Redeploy from this folder:

```powershell
npx vercel@latest --prod
```

Keep `.vercel/` local. It is ignored because it contains deployment metadata.
