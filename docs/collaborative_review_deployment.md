# Collaborative Review Deployment

This note explains how to share the Jupiter Lightning Detector with remote reviewers without making the workbench confusing or overclaiming the science.

## Current Dataset Scope

The current local detector dataset is not every Cassini Jupiter image. It is the processed Cassini ISS Narrow Angle Camera H-alpha/HAL Jupiter subset around the selected flyby dates.

- Processed date windows: 9
- Processed images: 221
- Local `data/` folder size: about 955 MB
- Local `outputs/` folder size: about 59 MB

The current workbench can truthfully say it has processed the 221-image NAC/HAL review subset. A broader OPUS inventory is a separate task.

## Recommended Sharing Path

Use one central server that has the data and outputs folders. Reviewers connect through a browser. They do not need to download the full dataset or run their own virtual machines.

Recommended first setup:

1. Run the app on one machine that has the repo, `data/`, and `outputs/`.
2. Set a `REVIEW_KEY` before exposing the app.
3. Expose that app through a temporary HTTPS tunnel for review sessions.
4. Save human labels to `outputs/detection/candidate_labels.csv` and `outputs/detection/candidate_labels.json`.
5. Commit small label/export files back to GitHub after each review session.

This keeps costs near zero and keeps the label history versioned.

## Why GitHub Pages Is Not Enough

GitHub Pages is useful for static HTML/CSS/JavaScript pages. This project needs a Python server for:

- loading local data products,
- rendering image crops,
- starting detector runs,
- saving reviewer labels,
- serving generated outputs.

So GitHub Pages can host documentation, but not the full live detector/review app.

## Andromeda / Campus Compute Option

If Boston College Andromeda allows a long-running Python process and outbound tunnel connections, it is a good central host:

- data can stay on campus storage,
- reviewers only need a browser,
- labels are saved on the server,
- the app can run with `HOST=0.0.0.0` and a chosen `PORT`.

Example command:

```powershell
$env:HOST = "0.0.0.0"
$env:PORT = "8765"
$env:OPEN_BROWSER = "0"
$env:REVIEW_KEY = "choose-a-review-key"
.\run.ps1 app
```

Then expose it with an approved campus method, SSH tunnel, or Cloudflare Tunnel if allowed by policy.

## Cloudflare Tunnel Session

For a temporary review session from a trusted machine:

```powershell
$env:REVIEW_KEY = "choose-a-review-key"
cloudflared tunnel --url http://127.0.0.1:8765
```

This gives a temporary HTTPS URL that reviewers can open. The URL changes each time unless a named tunnel/domain is configured.
Do not share a tunnel URL without setting `REVIEW_KEY`.

## Label Storage

The first real training data is not the raw images. It is the human decision table:

- candidate ID,
- image ID,
- human label,
- confidence,
- reviewer,
- review note,
- second-review flag.

For the current stage, CSV/JSON files are enough. A hosted database such as Supabase should only be added when multiple reviewers need simultaneous editing with accounts and audit trails.

## Training Path

Current detector:

- classical computer vision,
- explainable measurements,
- no YOLO yet,
- no reinforcement learning.

Training later:

1. collect human labels,
2. split labels into train/validation/test sets,
3. compare classical CV against a trained model,
4. keep false positives and false negatives visible,
5. only adopt a learned model if it improves review accuracy without hiding errors.

## Safe Public Wording

Safe:

> The system processed a 221-image Cassini ISS NAC/HAL Jupiter subset, recovered the published validation detections, and generated a human-review queue for unmatched candidates.

Not safe yet:

> The system discovered new Jupiter lightning.

That claim requires human review, temporal/geometric validation, and source-image audit.
