# Jupiter Lightning Detector Public Site

This folder contains the static public workbench deployed on Vercel:

https://jupiter-lightning-detector-public.vercel.app

It mirrors the major workbench tabs and includes a static snapshot of the
first-pass candidate review queue. Reviewers can label candidates in the browser
and export CSV/JSON backups.

It is not the full detector engine. New detector runs, OPUS downloads, calibrated
image loading, and crop rendering still run from the Python workbench because
they need local OPUS image products, generated outputs, and label files.

The current candidate data snapshot is:

```text
public_site/static-data/first_pass_review_queue.json
```

The current collaboration and geometry snapshots are:

```text
public_site/static-data/collaboration_config.json
public_site/static-data/geometry_readiness.json
```

Regenerate the candidate snapshot from
`outputs/detection/first_pass_review_plan.csv` before a new public deployment
when detector outputs change.

For shared labels, configure the Google Apps Script endpoint described in:

```text
docs/google_sheets_label_endpoint.md
```

Redeploy from this folder:

```powershell
npx vercel@latest --prod
```

Keep `.vercel/` local. It is ignored because it contains deployment metadata.
