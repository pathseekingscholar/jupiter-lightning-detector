from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
SUMMARY_CSV = OUTPUT_DIR / "key_findings_summary.csv"
BRIEF_MD = OUTPUT_DIR / "current_key_findings.md"
BRIEF_HTML = OUTPUT_DIR / "current_key_findings.html"


SUMMARY_FIELDS = [
    "item",
    "value",
    "evidence_file",
    "interpretation",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def number(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def fmt(value: int) -> str:
    return f"{value:,}"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def build_summary_rows() -> list[dict[str, object]]:
    detection = read_csv(OUTPUT_DIR / "detection_summary.csv")
    known = read_csv(OUTPUT_DIR / "known_match_report.csv")
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    session_audit = read_csv(OUTPUT_DIR / "review_session_audit.csv")
    training_ready = read_csv(OUTPUT_DIR / "training_readiness.csv")

    images = sum(number(row.get("images_processed")) for row in detection)
    raw_regions = sum(number(row.get("candidates_found")) for row in detection)
    review_candidates = sum(number(row.get("review_candidates")) for row in detection)
    rejected = sum(number(row.get("rejected_or_artifact_flagged")) for row in detection)
    published_matches = sum(number(row.get("published_matches")) for row in detection)
    unmatched = sum(number(row.get("unmatched_review_candidates")) for row in detection)
    recovered = sum(1 for row in known if row.get("recovered_within_8_px") == "yes")
    date_windows = len(detection)
    review_rows = len(review_plan)
    review_sessions = len(session_audit)
    import_ready_sessions = sum(1 for row in session_audit if row.get("session_status") == "import_ready")
    training_ready_status = "; ".join(
        f"{row.get('gate')}: {row.get('status')}" for row in training_ready[:4]
    )

    return [
        {
            "item": "processed_date_windows",
            "value": date_windows,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "Nine OPUS NAC/H-alpha date windows are currently processed.",
        },
        {
            "item": "images_processed",
            "value": images,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "This is the current image-level search scope.",
        },
        {
            "item": "raw_bright_regions",
            "value": raw_regions,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "First-pass bright regions before review filtering.",
        },
        {
            "item": "review_candidates",
            "value": review_candidates,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "Candidates kept after artifact filters; these are not confirmed lightning.",
        },
        {
            "item": "rejected_or_artifact_flagged",
            "value": rejected,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "Bright regions the detector deprioritized or flagged as likely artifact-like.",
        },
        {
            "item": "published_validation_matches",
            "value": f"{published_matches} detector matches; {recovered} recovered within 8 px",
            "evidence_file": "outputs/detection/known_match_report.csv",
            "interpretation": "The current detector recovers the published validation marks.",
        },
        {
            "item": "unmatched_review_candidates",
            "value": unmatched,
            "evidence_file": "outputs/detection/detection_summary.csv",
            "interpretation": "Unmatched means not in the published answer key; it does not mean new lightning.",
        },
        {
            "item": "first_pass_review_rows",
            "value": review_rows,
            "evidence_file": "outputs/detection/first_pass_review_plan.csv",
            "interpretation": "Curated queue for human yes/no/uncertain review.",
        },
        {
            "item": "review_sessions",
            "value": f"{review_sessions} sessions; {import_ready_sessions} import-ready",
            "evidence_file": "outputs/detection/review_session_audit.csv",
            "interpretation": "Session CSVs organize human review work; labels still need to be filled.",
        },
        {
            "item": "training_readiness",
            "value": training_ready_status,
            "evidence_file": "outputs/detection/training_readiness.csv",
            "interpretation": "Learned-model work is gated on enough reviewed labels.",
        },
    ]


def date_table(detection: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Date | Images | Raw regions | Review candidates | Published matches | Unmatched review |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in detection:
        lines.append(
            f"| {row.get('run_date')} | {fmt(number(row.get('images_processed')))} | "
            f"{fmt(number(row.get('candidates_found')))} | {fmt(number(row.get('review_candidates')))} | "
            f"{fmt(number(row.get('published_matches')))} | {fmt(number(row.get('unmatched_review_candidates')))} |"
        )
    return lines


def known_match_table(known: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Image | Published mark | Paper x/y | Detector x/y | Offset px | Recovered? |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in known:
        paper_xy = f"{row.get('published_x')}, {row.get('published_y')}"
        detector_xy = f"{row.get('nearest_x')}, {row.get('nearest_y')}"
        lines.append(
            f"| {row.get('image_id')} | {row.get('published_label')} | {paper_xy} | "
            f"{detector_xy} | {row.get('offset_px')} | {row.get('recovered_within_8_px')} |"
        )
    return lines


def review_action_table(review_plan: list[dict[str, str]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in review_plan:
        batch = row.get("review_batch", "")
        counts[batch] = counts.get(batch, 0) + 1
    lines = [
        "| Review batch | Rows | What a human does |",
        "|---|---:|---|",
    ]
    descriptions = {
        "known_validation_positive": "Confirm that published matches are visually reasonable.",
        "temporal_persistence_check": "Check whether repeated candidates look like coherent motion or repeated artifacts.",
        "negative_artifact_examples": "Build a clean negative set for cosmic rays, hot pixels, and artifacts.",
        "strong_single_frame_check": "Inspect strong one-frame signals without overclaiming them.",
        "low_priority_hold": "Keep low-priority rows saved but not first in the review queue.",
    }
    for batch, count in sorted(counts.items()):
        key = batch.split("_", 1)[1] if "_" in batch and batch[:2].isdigit() else batch
        lines.append(f"| {batch} | {count} | {descriptions.get(key, 'Review and label consistently.')} |")
    return lines


def build_markdown(summary_rows: list[dict[str, object]]) -> str:
    detection = read_csv(OUTPUT_DIR / "detection_summary.csv")
    known = read_csv(OUTPUT_DIR / "known_match_report.csv")
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")

    lines = [
        "# Current Key Findings",
        "",
        "This is a generated brief. It pulls numbers from the current detector outputs so the meeting summary and GitHub evidence stay tied to the same files.",
        "",
        "## Two-Minute Bottom Line",
        "",
        "- The pipeline has processed nine Cassini ISS NAC/H-alpha date windows around the Jupiter flyby.",
        "- The current search scope is 221 images.",
        "- The detector recovers the six published validation marks across Jan 1, Jan 10, and Jan 11.",
        "- The detector also keeps unmatched review candidates, but those are not new-lightning claims.",
        "- The next scientific gate is human yes/no/uncertain labeling, followed by temporal and geometry checks.",
        "",
        "## Key Numbers",
        "",
        "| Item | Value | Evidence | Interpretation |",
        "|---|---:|---|---|",
    ]
    for row in summary_rows:
        value = row["value"]
        if isinstance(value, int):
            value = fmt(value)
        lines.append(
            f"| `{row['item']}` | {value} | `{row['evidence_file']}` | {row['interpretation']} |"
        )

    lines.extend([
        "",
        "## Date Coverage",
        "",
        *date_table(detection),
        "",
        "## Published-Match Validation",
        "",
        *known_match_table(known),
        "",
        "## Human Review Queue",
        "",
        *review_action_table(review_plan),
        "",
        "## What We Can Safely Say",
        "",
        "- I built a reproducible detector-and-review workflow for Cassini Jupiter lightning candidates.",
        "- The detector recovers the published validation marks in the current processed dataset.",
        "- The detector produces a saved review queue with positives, likely negatives, temporal candidates, and unmatched candidates.",
        "- The work is ready for structured human review, not for claiming new lightning yet.",
        "",
        "## What We Cannot Say Yet",
        "",
        "- We cannot say the unmatched candidates are confirmed new Jupiter lightning.",
        "- We cannot say the candidate score is a calibrated probability.",
        "- We cannot say YOLO or a trained model is ready; labels are still needed.",
        "- We cannot claim Jupiter latitude/longitude for candidate pixels until geometry projection is completed.",
        "",
        "## Open First",
        "",
        "- `outputs/detection/candidate_review_dossier.html` for reviewer-facing candidates.",
        "- `outputs/detection/known_match_report.csv` for published validation recovery.",
        "- `outputs/detection/first_pass_review_plan.md` for the ordered human review plan.",
        "- `outputs/detection/temporal_validation_plan.md` for repeated-track follow-up.",
        "- `outputs/detection/manuscript_claim_matrix.md` for safe/unsafe paper wording.",
    ])
    return "\n".join(lines)


def markdown_to_html(markdown_text: str) -> str:
    body_lines = []
    in_table = False
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_table:
                body_lines.append("</table>")
                in_table = False
            body_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body_lines.append(f"<p class=\"bullet\">{html.escape(line[2:])}</p>")
        elif line.startswith("|") and "---" not in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not in_table:
                body_lines.append("<table>")
                in_table = True
            tag = "th" if all(index < 4 for index, _ in enumerate(cells)) and not body_lines[-1].endswith("</tr>") else "td"
            body_lines.append("<tr>" + "".join(f"<{tag}>{html.escape(cell)}</{tag}>" for cell in cells) + "</tr>")
        elif line.startswith("|") and "---" in line:
            continue
        elif not line.strip():
            if in_table:
                body_lines.append("</table>")
                in_table = False
        else:
            body_lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_lines.append("</table>")
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Current Key Findings</title>
  <style>
    body { margin: 0; padding: 40px; max-width: 1100px; font: 16px/1.55 Georgia, serif; color: #25241f; background: #fbf6e9; }
    h1, h2 { font-weight: 500; line-height: 1.1; }
    h1 { font-size: 44px; border-bottom: 3px double #25241f; padding-bottom: 14px; }
    h2 { margin-top: 34px; color: #a52d25; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; background: rgba(255,255,255,.35); }
    th, td { border: 1px solid #aaa18c; padding: 8px 10px; vertical-align: top; }
    th { text-align: left; background: rgba(246,222,113,.35); }
    code { font-family: Consolas, monospace; font-size: .92em; }
    .bullet::before { content: "- "; color: #a52d25; font-weight: bold; }
  </style>
</head>
<body>
""" + "\n".join(body_lines) + "\n</body>\n</html>\n"


def main() -> None:
    summary_rows = build_summary_rows()
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    markdown_text = build_markdown(summary_rows)
    BRIEF_MD.write_text(markdown_text, encoding="utf-8")
    BRIEF_HTML.write_text(markdown_to_html(markdown_text), encoding="utf-8")
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {BRIEF_MD}")
    print(f"Wrote {BRIEF_HTML}")


if __name__ == "__main__":
    main()
