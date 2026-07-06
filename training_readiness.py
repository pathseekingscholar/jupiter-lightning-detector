from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
READINESS_CSV = OUTPUT_DIR / "training_readiness.csv"
READINESS_MD = OUTPUT_DIR / "training_readiness.md"

MIN_POSITIVES = 6
MIN_NEGATIVES = 20
MIN_TRAINING_READY = MIN_POSITIVES + MIN_NEGATIVES


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


def summary_count(rows: list[dict[str, str]], item: str) -> int:
    for row in rows:
        if row.get("summary_item") == item or row.get("metric") == item:
            return int(float(row.get("count", row.get("value", 0)) or 0))
    return 0


def build_readiness_rows() -> list[dict[str, object]]:
    labels = read_csv(OUTPUT_DIR / "candidate_label_summary.csv")
    agreement = read_csv(OUTPUT_DIR / "review_agreement_audit.csv")
    training_manifest = read_csv(OUTPUT_DIR / "training_manifest.csv")
    active_learning = read_csv(OUTPUT_DIR / "active_learning_queue.csv")
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")

    split_counts = Counter(row.get("training_split", "") for row in training_manifest)
    batch_counts = Counter(row.get("review_batch", "") for row in review_plan)

    positives = summary_count(labels, "group_positive")
    negatives = summary_count(labels, "group_negative")
    uncertain = summary_count(labels, "group_uncertain")
    total_labels = summary_count(labels, "total_labels")
    training_ready = summary_count(agreement, "training_ready_labels")
    high_confidence = summary_count(agreement, "high_confidence_labels")
    labels_with_notes = summary_count(agreement, "labels_with_notes")

    rows = [
        {
            "gate": "saved_labels_exist",
            "status": "ready" if total_labels > 0 else "not_ready",
            "value": total_labels,
            "minimum": 1,
            "evidence_file": "outputs/detection/candidate_label_summary.csv",
            "interpretation": "Human labels exist." if total_labels else "No human labels have been saved yet.",
            "next_action": "Save reviewer labels through the workbench or label CSV import.",
        },
        {
            "gate": "positive_examples",
            "status": "ready" if positives >= MIN_POSITIVES else "not_ready",
            "value": positives,
            "minimum": MIN_POSITIVES,
            "evidence_file": "outputs/detection/candidate_label_summary.csv",
            "interpretation": "Enough positive validation examples exist." if positives >= MIN_POSITIVES else "Positive labels are below the first validation target.",
            "next_action": "Label the six published validation matches first.",
        },
        {
            "gate": "negative_examples",
            "status": "ready" if negatives >= MIN_NEGATIVES else "not_ready",
            "value": negatives,
            "minimum": MIN_NEGATIVES,
            "evidence_file": "outputs/detection/candidate_label_summary.csv",
            "interpretation": "Enough negative examples exist for first false-positive analysis." if negatives >= MIN_NEGATIVES else "Negative labels are below the first false-positive target.",
            "next_action": "Label at least 20 clear artifacts or cosmic-ray/hot-pixel rows.",
        },
        {
            "gate": "training_ready_labels",
            "status": "ready" if training_ready >= MIN_TRAINING_READY else "not_ready",
            "value": training_ready,
            "minimum": MIN_TRAINING_READY,
            "evidence_file": "outputs/detection/review_agreement_audit.csv",
            "interpretation": "High-confidence labels with notes are sufficient for first model comparison." if training_ready >= MIN_TRAINING_READY else "Training-ready labels are not sufficient for model comparison.",
            "next_action": "Require high confidence, reviewer notes, and no second-review flag for first training-ready rows.",
        },
        {
            "gate": "active_learning_queue",
            "status": "ready" if active_learning else "not_ready",
            "value": len(active_learning),
            "minimum": 1,
            "evidence_file": "outputs/detection/active_learning_queue.csv",
            "interpretation": "Unlabeled candidates are prioritized for human review." if active_learning else "No active-learning queue exists.",
            "next_action": "Review top active-learning rows after known positives and clear negatives.",
        },
        {
            "gate": "validation_split",
            "status": "ready" if split_counts.get("validation", 0) >= MIN_POSITIVES else "not_ready",
            "value": split_counts.get("validation", 0),
            "minimum": MIN_POSITIVES,
            "evidence_file": "outputs/detection/training_manifest.csv",
            "interpretation": "Validation split has enough published-match rows available for review." if split_counts.get("validation", 0) >= MIN_POSITIVES else "Validation split does not include enough published-match rows.",
            "next_action": "Keep published matches separate from candidate training rows.",
        },
        {
            "gate": "negative_review_batch",
            "status": "ready" if batch_counts.get("03_negative_artifact_examples", 0) >= MIN_NEGATIVES else "not_ready",
            "value": batch_counts.get("03_negative_artifact_examples", 0),
            "minimum": MIN_NEGATIVES,
            "evidence_file": "outputs/detection/review_labeling_checklist.csv",
            "interpretation": "A curated negative batch exists for reviewers." if batch_counts.get("03_negative_artifact_examples", 0) >= MIN_NEGATIVES else "Negative review batch is too small.",
            "next_action": "Use the negative artifact batch to create first negative labels.",
        },
        {
            "gate": "model_comparison_allowed",
            "status": "ready" if positives >= MIN_POSITIVES and negatives >= MIN_NEGATIVES and training_ready >= MIN_TRAINING_READY else "not_ready",
            "value": f"{positives} positives; {negatives} negatives; {training_ready} training-ready",
            "minimum": f"{MIN_POSITIVES} positives; {MIN_NEGATIVES} negatives; {MIN_TRAINING_READY} training-ready",
            "evidence_file": "outputs/detection/candidate_label_summary.csv",
            "interpretation": "A first model comparison can be planned." if positives >= MIN_POSITIVES and negatives >= MIN_NEGATIVES and training_ready >= MIN_TRAINING_READY else "Do not train or compare YOLO yet.",
            "next_action": "Finish human labels before training a learned detector.",
        },
        {
            "gate": "notes_and_confidence",
            "status": "ready" if high_confidence >= MIN_TRAINING_READY and labels_with_notes >= MIN_TRAINING_READY else "not_ready",
            "value": f"{high_confidence} high confidence; {labels_with_notes} with notes; {uncertain} uncertain",
            "minimum": f"{MIN_TRAINING_READY} high confidence and noted labels",
            "evidence_file": "outputs/detection/review_agreement_audit.csv",
            "interpretation": "Labels are well documented enough for first training use." if high_confidence >= MIN_TRAINING_READY and labels_with_notes >= MIN_TRAINING_READY else "Labels need confidence and notes before training use.",
            "next_action": "Do not use unlabeled or weakly noted rows as training truth.",
        },
    ]
    return rows


def write_markdown(rows: list[dict[str, object]]) -> None:
    ready = sum(1 for row in rows if row["status"] == "ready")
    not_ready = sum(1 for row in rows if row["status"] != "ready")
    model_gate = next(row for row in rows if row["gate"] == "model_comparison_allowed")
    lines = [
        "# Training Readiness Report",
        "",
        "This report answers whether the project is ready to train or compare a learned detector such as YOLO. It is generated from saved human labels and review artifacts.",
        "",
        "## Summary",
        "",
        f"- Ready gates: {ready}",
        f"- Not-ready gates: {not_ready}",
        f"- Model comparison status: `{model_gate['status']}`",
        f"- Model comparison value: {model_gate['value']}",
        "",
        "## Gates",
        "",
        "| Gate | Status | Value | Minimum | Evidence | Next action |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate']}` | `{row['status']}` | {row['value']} | {row['minimum']} | "
            f"`{row['evidence_file']}` | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Safe Interpretation",
        "",
        "The current detector is an explainable candidate generator. YOLO or another learned model should not be trained or compared until human labels include at least the six published validation positives, at least twenty clear negatives, and training-ready notes/confidence for those rows.",
        "",
        "## First Labeling Target",
        "",
        "1. Label the six `01_known_validation_positive` rows as `known-lightning` only after visual confirmation.",
        "2. Label at least twenty `03_negative_artifact_examples` rows as `artifact` or `cosmic-ray-hot-pixel` when visually clear.",
        "3. Leave ambiguous temporal candidates as `uncertain` until temporal and geometry checks improve.",
    ])
    READINESS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_readiness_rows()
    write_csv(
        READINESS_CSV,
        rows,
        ["gate", "status", "value", "minimum", "evidence_file", "interpretation", "next_action"],
    )
    write_markdown(rows)
    print(f"Wrote {READINESS_CSV}")
    print(f"Wrote {READINESS_MD}")


if __name__ == "__main__":
    main()
