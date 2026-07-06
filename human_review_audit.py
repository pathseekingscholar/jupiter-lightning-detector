from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
AUDIT_CSV = OUTPUT_DIR / "human_review_audit.csv"
AUDIT_MD = OUTPUT_DIR / "human_review_audit.md"


POSITIVE_LABELS = {"known-lightning", "possible-lightning"}
NEGATIVE_LABELS = {"artifact", "cosmic-ray-hot-pixel"}
NEEDS_REVIEW_LABELS = {"uncertain"}


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


def load_labels() -> dict[str, dict[str, object]]:
    path = OUTPUT_DIR / "candidate_labels.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("labels", {})


def label_group(label: str) -> str:
    if label in POSITIVE_LABELS:
        return "positive"
    if label in NEGATIVE_LABELS:
        return "negative"
    if label in NEEDS_REVIEW_LABELS:
        return "uncertain"
    return "unlabeled"


def build_audit() -> list[dict[str, object]]:
    training = read_csv(OUTPUT_DIR / "training_manifest.csv")
    matrix = read_csv(OUTPUT_DIR / "review_decision_matrix.csv")
    labels = load_labels()

    training_ids = {row.get("candidate_id", "") for row in training}
    labels_in_manifest = {
        candidate_id: label
        for candidate_id, label in labels.items()
        if candidate_id in training_ids
    }
    labels_outside_manifest = {
        candidate_id: label
        for candidate_id, label in labels.items()
        if candidate_id not in training_ids
    }

    label_counts = Counter()
    group_counts = Counter()
    confidence_counts = Counter()
    for label in labels_in_manifest.values():
        human_label = str(label.get("human_label") or label.get("label") or "")
        label_counts[human_label or "unlabeled"] += 1
        group_counts[label_group(human_label)] += 1
        confidence_counts[str(label.get("confidence") or "unspecified")] += 1

    review_status_counts = Counter()
    for row in training:
        candidate_id = row.get("candidate_id", "")
        if candidate_id in labels_in_manifest:
            review_status_counts["human_labeled"] += 1
        else:
            review_status_counts["unlabeled"] += 1

    published_rows = [row for row in training if row.get("review_category") == "published_match"]
    published_ids = {row.get("candidate_id", "") for row in published_rows}
    published_labeled = [
        candidate_id for candidate_id in published_ids
        if candidate_id in labels_in_manifest
    ]
    published_positive = [
        candidate_id for candidate_id in published_labeled
        if label_group(str(labels_in_manifest[candidate_id].get("human_label") or "")) == "positive"
    ]

    next_actions = Counter(row.get("next_action", "") for row in matrix)
    artifact_review_rows = [
        row for row in matrix
        if row.get("next_action") == "review_as_negative_example"
    ]
    temporal_rows = [
        row for row in matrix
        if row.get("next_action") in {"priority_temporal_review", "temporal_review"}
    ]

    rows: list[dict[str, object]] = [
        {
            "audit_item": "candidate_rows_available_for_review",
            "value": len(training),
            "status": "ready" if training else "missing",
            "meaning": "Rows in the review/training manifest.",
            "next_action": "Use these rows as the controlled review queue.",
        },
        {
            "audit_item": "human_labels_saved_inside_manifest",
            "value": len(labels_in_manifest),
            "status": "needs_work" if len(labels_in_manifest) == 0 else "in_progress",
            "meaning": "Human-reviewed labels attached to current candidate IDs.",
            "next_action": "Start by labeling published matches and obvious artifacts.",
        },
        {
            "audit_item": "human_labels_saved_outside_manifest",
            "value": len(labels_outside_manifest),
            "status": "check" if labels_outside_manifest else "ok",
            "meaning": "Labels exist but do not match the current manifest candidate IDs.",
            "next_action": "Keep if from older runs; reconcile before training.",
        },
        {
            "audit_item": "positive_training_examples",
            "value": group_counts["positive"],
            "status": "needs_work" if group_counts["positive"] < 6 else "in_progress",
            "meaning": "Known or possible lightning examples reviewed by a human.",
            "next_action": "Confirm all published validation matches first.",
        },
        {
            "audit_item": "negative_training_examples",
            "value": group_counts["negative"],
            "status": "needs_work" if group_counts["negative"] < 20 else "in_progress",
            "meaning": "Reviewed artifacts and cosmic-ray/hot-pixel examples.",
            "next_action": "Label artifact examples so future models learn what not to select.",
        },
        {
            "audit_item": "uncertain_review_examples",
            "value": group_counts["uncertain"],
            "status": "ok",
            "meaning": "Candidates explicitly marked as unresolved.",
            "next_action": "Use second review or temporal/geometric checks.",
        },
        {
            "audit_item": "unlabeled_candidates_remaining",
            "value": review_status_counts["unlabeled"],
            "status": "needs_review" if review_status_counts["unlabeled"] else "done",
            "meaning": "Candidates still waiting for human review.",
            "next_action": "Review active-learning and temporal-priority rows first.",
        },
        {
            "audit_item": "published_validation_marks_labeled",
            "value": f"{len(published_positive)} of {len(published_rows)}",
            "status": "needs_work" if len(published_positive) < len(published_rows) else "ready",
            "meaning": "Known published detections that have been human-confirmed in this label set.",
            "next_action": "Label these as known-lightning with high confidence after visual check.",
        },
        {
            "audit_item": "artifact_negative_review_queue",
            "value": len(artifact_review_rows),
            "status": "ready" if artifact_review_rows else "missing",
            "meaning": "Rows suggested as negative examples because artifact flags were present.",
            "next_action": "Inspect and label clear non-lightning examples.",
        },
        {
            "audit_item": "temporal_review_queue",
            "value": len(temporal_rows),
            "status": "ready" if temporal_rows else "missing",
            "meaning": "Rows needing repeated-frame review.",
            "next_action": "Check whether the candidate persists across nearby frames.",
        },
    ]

    for label, count in sorted(label_counts.items()):
        rows.append({
            "audit_item": f"label_count_{label}",
            "value": count,
            "status": "observed",
            "meaning": "Saved human label count.",
            "next_action": "Use for validation/training only after review notes are complete.",
        })

    for confidence, count in sorted(confidence_counts.items()):
        rows.append({
            "audit_item": f"confidence_count_{confidence}",
            "value": count,
            "status": "observed",
            "meaning": "Reviewer confidence count.",
            "next_action": "Prefer high-confidence labels for first validation splits.",
        })

    for action, count in sorted(next_actions.items()):
        rows.append({
            "audit_item": f"next_action_{action}",
            "value": count,
            "status": "queue",
            "meaning": "Decision-matrix action count.",
            "next_action": "Use this to divide review work into positives, negatives, and temporal checks.",
        })

    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    values = {str(row["audit_item"]): row for row in rows}
    label_rows = [row for row in rows if str(row["audit_item"]).startswith("label_count_")]
    action_rows = [row for row in rows if str(row["audit_item"]).startswith("next_action_")]

    def value(name: str) -> object:
        return values.get(name, {}).get("value", "")

    lines = [
        "# Human Review And Training Audit",
        "",
        "This report answers the review-loop question: what has a human actually labeled, what is still only a detector candidate, and what is ready to become training data.",
        "",
        "## Current State",
        "",
        f"- Candidate rows available for review: {value('candidate_rows_available_for_review')}",
        f"- Human labels saved inside the current manifest: {value('human_labels_saved_inside_manifest')}",
        f"- Positive training examples: {value('positive_training_examples')}",
        f"- Negative training examples: {value('negative_training_examples')}",
        f"- Uncertain review examples: {value('uncertain_review_examples')}",
        f"- Unlabeled candidates remaining: {value('unlabeled_candidates_remaining')}",
        f"- Published validation marks labeled positive: {value('published_validation_marks_labeled')}",
        "",
        "## What Counts As Positive And Negative",
        "",
        "- Positive: `known-lightning` or `possible-lightning` after human review.",
        "- Negative: `artifact` or `cosmic-ray-hot-pixel` after human review.",
        "- Uncertain: useful for follow-up, but not clean training data yet.",
        "- Unlabeled: detector output only; it is not evidence of lightning by itself.",
        "",
        "## Why This Matters",
        "",
        "A future YOLO or learned detector needs both positive and negative examples. The current classical detector proposes candidates, but the human label is the scientific gate. Until enough labels exist, the project should not claim that a trained AI model understands lightning.",
        "",
        "## Decision-Matrix Queues",
        "",
        "| Queue | Count | Meaning |",
        "|---|---:|---|",
    ]
    for row in action_rows:
        item = str(row["audit_item"]).replace("next_action_", "")
        lines.append(f"| `{item}` | {row['value']} | {row['meaning']} |")

    lines.extend([
        "",
        "## Saved Label Counts",
        "",
    ])
    if label_rows:
        lines.extend([
            "| Label | Count |",
            "|---|---:|",
        ])
        for row in label_rows:
            item = str(row["audit_item"]).replace("label_count_", "")
            lines.append(f"| `{item}` | {row['value']} |")
    else:
        lines.append("No human labels have been saved yet for the current manifest.")

    lines.extend([
        "",
        "## Safe Claim",
        "",
        "The detector has produced a reviewable candidate set and a structure for human-in-the-loop training. Human labels are the next required evidence layer before claiming new lightning or training a YOLO-style model.",
    ])
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_audit()
    write_csv(AUDIT_CSV, rows, ["audit_item", "value", "status", "meaning", "next_action"])
    write_report(rows)
    print(f"Wrote {AUDIT_CSV}")
    print(f"Wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
