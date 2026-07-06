from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PROTOCOL_MD = OUTPUT_DIR / "review_labeling_protocol.md"
CHECKLIST_CSV = OUTPUT_DIR / "review_labeling_checklist.csv"


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


def batch_goal(batch: str) -> dict[str, str]:
    goals = {
        "01_known_validation_positive": {
            "review_goal": "Confirm published validation marks after visual inspection.",
            "preferred_labels": "known-lightning or uncertain",
            "training_use": "positive validation only after visual confirmation",
            "pass_condition": "All six published matches have reviewer, confidence, note, and reviewed_at.",
        },
        "02_temporal_persistence_check": {
            "review_goal": "Check whether candidate tracks persist across nearby frames.",
            "preferred_labels": "possible-lightning, artifact, cosmic-ray-hot-pixel, or uncertain",
            "training_use": "do not train as positive until temporal and geometry checks agree",
            "pass_condition": "Every strong temporal case has a note about repeat behavior.",
        },
        "03_negative_artifact_examples": {
            "review_goal": "Build negative examples for false-positive analysis.",
            "preferred_labels": "artifact or cosmic-ray-hot-pixel",
            "training_use": "negative training examples after reviewer agrees artifact is clear",
            "pass_condition": "At least 20 clear negative labels with short reason notes.",
        },
        "04_strong_single_frame_check": {
            "review_goal": "Inspect strong one-frame detections without overclaiming them.",
            "preferred_labels": "possible-lightning, artifact, cosmic-ray-hot-pixel, or uncertain",
            "training_use": "hold out unless second review supports the label",
            "pass_condition": "Each row notes why single-frame evidence is or is not credible.",
        },
        "05_low_priority_hold": {
            "review_goal": "Keep lower-priority examples available without using them too early.",
            "preferred_labels": "uncertain, artifact, or hold unlabeled",
            "training_use": "not for first training pass unless explicitly reviewed",
            "pass_condition": "No discovery claim comes from this batch alone.",
        },
    }
    return goals.get(batch, {
        "review_goal": "Review candidate according to the detector note.",
        "preferred_labels": "known-lightning, possible-lightning, artifact, cosmic-ray-hot-pixel, or uncertain",
        "training_use": "requires reviewer note before training use",
        "pass_condition": "Reviewer records a label, confidence, and reason.",
    })


def build_checklist_rows() -> list[dict[str, object]]:
    plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    by_batch = Counter(row.get("review_batch", "") for row in plan)
    rows: list[dict[str, object]] = []
    for batch, count in sorted(by_batch.items()):
        goal = batch_goal(batch)
        rows.append({
            "review_batch": batch,
            "candidate_count": count,
            "review_goal": goal["review_goal"],
            "preferred_labels": goal["preferred_labels"],
            "required_fields": "human_label, confidence, reviewer, review_note, review_stage, needs_second_review, reviewed_at",
            "training_use": goal["training_use"],
            "pass_condition": goal["pass_condition"],
        })
    return rows


def label_rules() -> list[dict[str, str]]:
    return [
        {
            "label": "known-lightning",
            "when_to_use": "Candidate matches a published Dyudina et al. validation mark and the reviewer visually confirms the mark.",
            "do_not_use_when": "The row is merely near a published image but not the validation mark.",
            "training_role": "Positive validation example.",
        },
        {
            "label": "possible-lightning",
            "when_to_use": "Diffuse bright blob or repeated candidate that remains scientifically interesting after artifact checks.",
            "do_not_use_when": "Only one sharp pixel, streak, edge effect, or no temporal/geometric support.",
            "training_role": "Candidate positive only after second review; not a confirmed discovery.",
        },
        {
            "label": "artifact",
            "when_to_use": "Likely edge, streak, processing residual, line defect, saturated artifact, or shape inconsistent with lightning.",
            "do_not_use_when": "The candidate is diffuse and repeated enough to need more review.",
            "training_role": "Negative example.",
        },
        {
            "label": "cosmic-ray-hot-pixel",
            "when_to_use": "Single-pixel or very sharp point-like event that disappears in nearby frames.",
            "do_not_use_when": "Multi-pixel diffuse blob with repeat behavior.",
            "training_role": "Negative example.",
        },
        {
            "label": "uncertain",
            "when_to_use": "Evidence is mixed, too faint, too ambiguous, or needs another frame/filter/geometry check.",
            "do_not_use_when": "A clear positive validation mark or clear artifact can be labeled directly.",
            "training_role": "Holdout; not used for first training pass.",
        },
    ]


def write_protocol(checklist_rows: list[dict[str, object]]) -> None:
    total = sum(int(row["candidate_count"]) for row in checklist_rows)
    lines = [
        "# Human Labeling Protocol",
        "",
        "This protocol explains how to turn detector candidates into review evidence without making unsupported discovery claims.",
        "",
        "## Current Review Set",
        "",
        f"- First-pass candidates: {total}",
        "- Required label file: `outputs/detection/candidate_label_template.csv`",
        "- Import command after review: `.\\run.ps1 label-import -LabelCsv outputs\\detection\\candidate_label_template.csv`",
        "- Regenerate summaries after import: `.\\run.ps1 label-summary`",
        "",
        "## Reviewer Rule",
        "",
        "A detector candidate is not lightning by itself. A label records what the reviewer thinks the candidate is, and the note explains why.",
        "",
        "## Label Definitions",
        "",
        "| Label | Use when | Do not use when | Training role |",
        "|---|---|---|---|",
    ]
    for rule in label_rules():
        lines.append(
            f"| `{rule['label']}` | {rule['when_to_use']} | {rule['do_not_use_when']} | {rule['training_role']} |"
        )
    lines.extend([
        "",
        "## Required Fields",
        "",
        "| Field | Meaning |",
        "|---|---|",
        "| `human_label` | One of the allowed labels above. |",
        "| `confidence` | Reviewer confidence: `low`, `medium`, or `high`. |",
        "| `reviewer` | Name or initials of the person reviewing. |",
        "| `review_note` | Short reason for the label; do not leave this blank for training rows. |",
        "| `review_stage` | `first-review`, `second-review`, or `consensus`. |",
        "| `needs_second_review` | `yes` when the row should not be used alone. |",
        "| `reviewed_at` | Review timestamp; the importer can fill this if blank. |",
        "",
        "## Batch Checklist",
        "",
        "| Batch | Count | Goal | Preferred labels | Pass condition |",
        "|---|---:|---|---|---|",
    ])
    for row in checklist_rows:
        lines.append(
            f"| `{row['review_batch']}` | {row['candidate_count']} | {row['review_goal']} | "
            f"{row['preferred_labels']} | {row['pass_condition']} |"
        )
    lines.extend([
        "",
        "## Positive / Negative Meaning",
        "",
        "- Positive examples are `known-lightning` or carefully reviewed `possible-lightning` rows.",
        "- Negative examples are `artifact` or `cosmic-ray-hot-pixel` rows.",
        "- `uncertain` rows stay out of training until more evidence exists.",
        "- Published validation marks should be labeled before any unmatched candidate is presented as interesting.",
        "",
        "## Minimum First Review Target",
        "",
        "- 6 known validation positives.",
        "- 20 clear negative artifact or cosmic-ray/hot-pixel examples.",
        "- Notes for every temporal candidate that might become `possible-lightning`.",
        "",
        "## What This Enables",
        "",
        "Once labels exist, the project can report false positives, false negatives, training-ready examples, and reviewer disagreement. Only after that should YOLO or another learned model be compared against the explainable detector.",
    ])
    PROTOCOL_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    checklist_rows = build_checklist_rows()
    write_csv(
        CHECKLIST_CSV,
        checklist_rows,
        [
            "review_batch",
            "candidate_count",
            "review_goal",
            "preferred_labels",
            "required_fields",
            "training_use",
            "pass_condition",
        ],
    )
    write_protocol(checklist_rows)
    print(f"Wrote {CHECKLIST_CSV}")
    print(f"Wrote {PROTOCOL_MD}")


if __name__ == "__main__":
    main()
