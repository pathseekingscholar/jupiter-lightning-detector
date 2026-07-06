from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import label_tools


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
AGREEMENT_CSV = OUTPUT_DIR / "review_agreement_audit.csv"
AGREEMENT_MD = OUTPUT_DIR / "review_agreement_audit.md"


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


def build_agreement_audit() -> list[dict[str, object]]:
    labels = read_csv(OUTPUT_DIR / "candidate_labels.csv")
    total = len(labels)
    group_counts = Counter(label_tools.label_group(row.get("human_label") or row.get("label")) for row in labels)
    stage_counts = Counter(row.get("review_stage") or "unspecified" for row in labels)
    needs_second = sum(1 for row in labels if label_tools.truthy(row.get("needs_second_review")))
    high_confidence = sum(1 for row in labels if row.get("confidence") == "high")
    reviewed_with_notes = sum(1 for row in labels if row.get("review_note", "").strip())
    training_ready = sum(
        1 for row in labels
        if row.get("confidence") == "high"
        and row.get("review_note", "").strip()
        and not label_tools.truthy(row.get("needs_second_review"))
    )

    rows: list[dict[str, object]] = [
        audit_row("total_saved_labels", total, "ready" if total else "not_started", "All saved human labels.", "Start labeling from the first-pass review batches."),
        audit_row("positive_labels", group_counts["positive"], "ready" if group_counts["positive"] >= 6 else "needs_work", "Known or possible lightning labels.", "Human-confirm the six published validation marks first."),
        audit_row("negative_labels", group_counts["negative"], "ready" if group_counts["negative"] >= 20 else "needs_work", "Artifact or cosmic-ray/hot-pixel labels.", "Label clear negatives for false-positive analysis."),
        audit_row("uncertain_labels", group_counts["uncertain"], "observed", "Reviewed but unresolved labels.", "Use second review, temporal checks, or geometry before training."),
        audit_row("needs_second_review", needs_second, "needs_review" if needs_second else "ok", "Labels explicitly marked for another reviewer.", "Prioritize these before using labels for training."),
        audit_row("high_confidence_labels", high_confidence, "observed", "Labels marked high confidence.", "Use with notes and no second-review flag for first validation splits."),
        audit_row("labels_with_notes", reviewed_with_notes, "observed", "Labels with human review notes.", "Require notes for training-ready labels."),
        audit_row("training_ready_labels", training_ready, "ready" if training_ready >= 26 else "not_ready", "High-confidence labels with notes and no second-review flag.", "Need at least 6 positives plus 20 negatives before model comparison."),
    ]
    for stage, count in sorted(stage_counts.items()):
        rows.append(audit_row(f"review_stage_{stage}", count, "observed", "Saved labels by review stage.", "Use stages to separate first review from consensus review."))
    return rows


def audit_row(metric: str, value: object, status: str, meaning: str, next_action: str) -> dict[str, object]:
    return {
        "metric": metric,
        "value": value,
        "status": status,
        "meaning": meaning,
        "next_action": next_action,
    }


def write_report(rows: list[dict[str, object]]) -> None:
    lookup = {row["metric"]: row for row in rows}

    def value(metric: str) -> object:
        return lookup.get(metric, {}).get("value", "")

    lines = [
        "# Review Agreement Audit",
        "",
        "This audit separates saved human labels from labels that are strong enough to use for validation or training. A single saved label is useful evidence, but it is not automatically consensus.",
        "",
        "## Current Label State",
        "",
        f"- Total saved labels: {value('total_saved_labels')}",
        f"- Positive labels: {value('positive_labels')}",
        f"- Negative labels: {value('negative_labels')}",
        f"- Labels needing second review: {value('needs_second_review')}",
        f"- Training-ready labels: {value('training_ready_labels')}",
        "",
        "## Rules",
        "",
        "- A training-ready label must be high confidence, have a note, and not be marked as needing second review.",
        "- Possible-lightning labels still need scientific validation before any discovery claim.",
        "- Disagreements or uncertain labels should stay out of training splits until resolved.",
        "",
        "## Metrics",
        "",
        "| Metric | Status | Value | Meaning | Next action |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['metric']}` | `{row['status']}` | {row['value']} | {row['meaning']} | {row['next_action']} |")
    AGREEMENT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_agreement_audit()
    write_csv(AGREEMENT_CSV, rows, ["metric", "value", "status", "meaning", "next_action"])
    write_report(rows)
    print(f"Wrote {AGREEMENT_CSV}")
    print(f"Wrote {AGREEMENT_MD}")


if __name__ == "__main__":
    main()
