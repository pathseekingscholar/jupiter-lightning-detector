from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PACKET_CSV = OUTPUT_DIR / "blind_review_packet.csv"
KEY_CSV = OUTPUT_DIR / "blind_review_key.csv"
IMPORT_CSV = OUTPUT_DIR / "blind_review_label_import.csv"
RECONCILE_CSV = OUTPUT_DIR / "blind_review_reconciliation.csv"
RECONCILE_MD = OUTPUT_DIR / "blind_review_reconciliation.md"

VALID_LABELS = {
    "known-lightning",
    "possible-lightning",
    "artifact",
    "cosmic-ray-hot-pixel",
    "uncertain",
}
VALID_CONFIDENCE = {"low", "medium", "high", ""}


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


def normalize_label(value: str) -> str:
    return value.strip().lower()


def label_group(label: str) -> str:
    if label in {"known-lightning", "possible-lightning"}:
        return "positive"
    if label in {"artifact", "cosmic-ray-hot-pixel"}:
        return "negative"
    if label == "uncertain":
        return "uncertain"
    return "unlabeled"


def build_reconciliation_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    packet = read_csv(PACKET_CSV)
    key = {row.get("blind_id", ""): row for row in read_csv(KEY_CSV)}
    rows: list[dict[str, object]] = []
    import_rows: list[dict[str, object]] = []
    for row in packet:
        blind_id = row.get("blind_id", "")
        key_row = key.get(blind_id, {})
        reviewer_label = normalize_label(row.get("reviewer_label", ""))
        confidence = normalize_label(row.get("reviewer_confidence", ""))
        label_valid = reviewer_label in VALID_LABELS or reviewer_label == ""
        confidence_valid = confidence in VALID_CONFIDENCE
        suggested_label = key_row.get("suggested_human_label", "")
        reviewer_group = label_group(reviewer_label)
        suggested_group = label_group(suggested_label)
        if reviewer_label == "":
            agreement = "unlabeled"
        elif reviewer_label == suggested_label:
            agreement = "exact_match"
        elif reviewer_group == suggested_group:
            agreement = "same_group"
        else:
            agreement = "disagree"

        output = {
            "blind_id": blind_id,
            "candidate_id": key_row.get("candidate_id", ""),
            "image_id": row.get("image_id", ""),
            "run_date": row.get("run_date", ""),
            "reviewer_label": reviewer_label,
            "reviewer_confidence": confidence,
            "reviewer_note": row.get("reviewer_note", ""),
            "needs_second_review": row.get("needs_second_review", ""),
            "suggested_human_label": suggested_label,
            "review_batch": key_row.get("review_batch", ""),
            "next_action": key_row.get("next_action", ""),
            "agreement": agreement,
            "label_valid": "yes" if label_valid else "no",
            "confidence_valid": "yes" if confidence_valid else "no",
        }
        rows.append(output)

        if reviewer_label:
            import_rows.append({
                "review_rank": key_row.get("review_order", ""),
                "candidate_id": key_row.get("candidate_id", ""),
                "image_id": row.get("image_id", ""),
                "image_number": row.get("image_id", "").lstrip("N"),
                "run_date": row.get("run_date", ""),
                "x": row.get("x", ""),
                "y": row.get("y", ""),
                "snr": row.get("snr", ""),
                "blob_size": row.get("blob_size", ""),
                "artifact_flags": row.get("artifact_flags_visible", ""),
                "candidate_score": "",
                "next_action": key_row.get("next_action", ""),
                "suggested_label": suggested_label,
                "human_label": reviewer_label,
                "confidence": confidence or "medium",
                "reviewer": "blind-reviewer",
                "review_note": row.get("reviewer_note", ""),
                "review_stage": "first-review",
                "needs_second_review": row.get("needs_second_review", ""),
                "reviewed_at": "",
            })
    return rows, import_rows


def write_report(rows: list[dict[str, object]], import_rows: list[dict[str, object]]) -> None:
    status_counts = Counter(str(row["agreement"]) for row in rows)
    label_counts = Counter(str(row["reviewer_label"] or "unlabeled") for row in rows)
    invalid_labels = sum(1 for row in rows if row["label_valid"] != "yes")
    invalid_confidence = sum(1 for row in rows if row["confidence_valid"] != "yes")
    lines = [
        "# Blind Review Reconciliation",
        "",
        "This report joins completed blind-review labels back to the hidden answer key. It does not import labels automatically; it writes an import-ready CSV that can be reviewed before use.",
        "",
        "## Files",
        "",
        "- Input reviewer file: `outputs/detection/blind_review_packet.csv`",
        "- Input answer key: `outputs/detection/blind_review_key.csv`",
        "- Import-ready output: `outputs/detection/blind_review_label_import.csv`",
        "- Reconciliation output: `outputs/detection/blind_review_reconciliation.csv`",
        "",
        "## Summary",
        "",
        f"- Blind rows checked: {len(rows)}",
        f"- Labeled rows ready for import review: {len(import_rows)}",
        f"- Invalid labels: {invalid_labels}",
        f"- Invalid confidence values: {invalid_confidence}",
        "",
        "## Agreement Counts",
        "",
        "| Agreement | Rows |",
        "|---|---:|",
    ]
    for name, count in sorted(status_counts.items()):
        lines.append(f"| `{name}` | {count} |")
    lines.extend([
        "",
        "## Reviewer Label Counts",
        "",
        "| Reviewer label | Rows |",
        "|---|---:|",
    ])
    for name, count in sorted(label_counts.items()):
        lines.append(f"| `{name}` | {count} |")
    lines.extend([
        "",
        "## How To Import After Review",
        "",
        "After checking `blind_review_reconciliation.csv` for invalid labels/confidence and disagreement cases, run:",
        "",
        "```powershell",
        ".\\run.ps1 label-import -LabelCsv outputs\\detection\\blind_review_label_import.csv",
        ".\\run.ps1 label-summary",
        "```",
        "",
        "Rows without `reviewer_label` are intentionally skipped from the import CSV. Disagreement is not automatically bad; it is evidence for second review or clearer labeling rules.",
    ])
    RECONCILE_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows, import_rows = build_reconciliation_rows()
    write_csv(
        RECONCILE_CSV,
        rows,
        [
            "blind_id",
            "candidate_id",
            "image_id",
            "run_date",
            "reviewer_label",
            "reviewer_confidence",
            "reviewer_note",
            "needs_second_review",
            "suggested_human_label",
            "review_batch",
            "next_action",
            "agreement",
            "label_valid",
            "confidence_valid",
        ],
    )
    write_csv(
        IMPORT_CSV,
        import_rows,
        [
            "review_rank",
            "candidate_id",
            "image_id",
            "image_number",
            "run_date",
            "x",
            "y",
            "snr",
            "blob_size",
            "artifact_flags",
            "candidate_score",
            "next_action",
            "suggested_label",
            "human_label",
            "confidence",
            "reviewer",
            "review_note",
            "review_stage",
            "needs_second_review",
            "reviewed_at",
        ],
    )
    write_report(rows, import_rows)
    print(f"Wrote {RECONCILE_CSV}")
    print(f"Wrote {IMPORT_CSV}")
    print(f"Wrote {RECONCILE_MD}")


if __name__ == "__main__":
    main()
