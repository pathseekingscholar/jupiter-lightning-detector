from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PLAN_CSV = OUTPUT_DIR / "first_pass_review_plan.csv"
PLAN_MD = OUTPUT_DIR / "first_pass_review_plan.md"


BATCH_LIMITS = {
    "01_known_validation_positive": None,
    "02_temporal_persistence_check": 30,
    "03_negative_artifact_examples": 20,
    "04_strong_single_frame_check": 20,
}


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


def numeric(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def batch_for_action(row: dict[str, str]) -> tuple[str, str, str]:
    action = row.get("next_action", "")
    if action == "confirm_known_validation_mark":
        return (
            "01_known_validation_positive",
            "known-lightning",
            "Confirm that the detector candidate matches the published lightning location.",
        )
    if action in {"priority_temporal_review", "temporal_review"}:
        return (
            "02_temporal_persistence_check",
            "uncertain",
            "Check whether the bright region repeats across neighboring frames with plausible motion.",
        )
    if action == "review_as_negative_example":
        artifact_flags = row.get("artifact_flags", "")
        if "single_pixel" in artifact_flags or "too_small" in artifact_flags:
            suggested = "cosmic-ray-hot-pixel"
        else:
            suggested = "artifact"
        return (
            "03_negative_artifact_examples",
            suggested,
            "Decide whether this is a clear non-lightning example for the negative set.",
        )
    if action == "single_frame_visual_review":
        return (
            "04_strong_single_frame_check",
            "uncertain",
            "Inspect the crop and original frame; single-frame candidates need caution.",
        )
    return (
        "05_low_priority_hold",
        row.get("suggested_label", "uncertain") or "uncertain",
        "Hold for later review after higher-value batches are labeled.",
    )


def build_plan() -> list[dict[str, object]]:
    dossier = read_csv(OUTPUT_DIR / "candidate_review_dossier.csv")
    buckets: dict[str, list[dict[str, str]]] = {name: [] for name in BATCH_LIMITS}
    buckets["05_low_priority_hold"] = []

    for row in dossier:
        batch, suggested_label, reviewer_task = batch_for_action(row)
        enriched = dict(row)
        enriched["_batch"] = batch
        enriched["_suggested_human_label"] = suggested_label
        enriched["_reviewer_task"] = reviewer_task
        buckets.setdefault(batch, []).append(enriched)

    for bucket_rows in buckets.values():
        bucket_rows.sort(
            key=lambda row: (
                int(numeric(row.get("review_rank"), 999999)),
                -numeric(row.get("candidate_score")),
                -numeric(row.get("snr")),
            )
        )

    rows: list[dict[str, object]] = []
    order = 1
    hold_rows: list[dict[str, str]] = list(buckets.get("05_low_priority_hold", []))
    for batch in [
        "01_known_validation_positive",
        "02_temporal_persistence_check",
        "03_negative_artifact_examples",
        "04_strong_single_frame_check",
    ]:
        limit = BATCH_LIMITS.get(batch)
        bucket_rows = buckets.get(batch, [])
        selected = bucket_rows
        if limit is not None:
            selected = bucket_rows[:limit]
            for leftover in bucket_rows[limit:]:
                postponed = dict(leftover)
                postponed["_batch"] = "05_low_priority_hold"
                postponed["_reviewer_task"] = "Hold for later review after the first labeling pass."
                hold_rows.append(postponed)
        for row in selected:
            rows.append({
                "review_order": order,
                "review_batch": batch,
                "candidate_id": row.get("candidate_id", ""),
                "image_id": row.get("image_id", ""),
                "run_date": row.get("run_date", ""),
                "x": row.get("x", ""),
                "y": row.get("y", ""),
                "crop_url": row.get("crop_url", ""),
                "next_action": row.get("next_action", ""),
                "suggested_human_label": row.get("_suggested_human_label", ""),
                "reviewer_task": row.get("_reviewer_task", ""),
                "snr": row.get("snr", ""),
                "blob_size": row.get("blob_size", ""),
                "artifact_flags": row.get("artifact_flags", ""),
                "frame_count": row.get("frame_count", ""),
                "motion_consistency": row.get("motion_consistency", ""),
                "candidate_score": row.get("candidate_score", ""),
                "review_note_prompt": note_prompt(row),
            })
            order += 1
    hold_rows.sort(
        key=lambda row: (
            int(numeric(row.get("review_rank"), 999999)),
            -numeric(row.get("candidate_score")),
            -numeric(row.get("snr")),
        )
    )
    for row in hold_rows:
        rows.append({
            "review_order": order,
            "review_batch": "05_low_priority_hold",
            "candidate_id": row.get("candidate_id", ""),
            "image_id": row.get("image_id", ""),
            "run_date": row.get("run_date", ""),
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "crop_url": row.get("crop_url", ""),
            "next_action": row.get("next_action", ""),
            "suggested_human_label": row.get("_suggested_human_label", row.get("suggested_label", "uncertain")),
            "reviewer_task": row.get("_reviewer_task", "Hold for later review after higher-value batches are labeled."),
            "snr": row.get("snr", ""),
            "blob_size": row.get("blob_size", ""),
            "artifact_flags": row.get("artifact_flags", ""),
            "frame_count": row.get("frame_count", ""),
            "motion_consistency": row.get("motion_consistency", ""),
            "candidate_score": row.get("candidate_score", ""),
            "review_note_prompt": note_prompt(row),
        })
        order += 1
    return rows


def note_prompt(row: dict[str, str]) -> str:
    action = row.get("next_action", "")
    if action == "confirm_known_validation_mark":
        return "Record whether the crop visually matches the published mark and whether the nearby context looks plausible."
    if action in {"priority_temporal_review", "temporal_review"}:
        return "Record which neighboring frames show the candidate and whether motion looks consistent or suspicious."
    if action == "review_as_negative_example":
        return "Record the artifact reason: single pixel, edge, streak, compression/noise, or other."
    if action == "single_frame_visual_review":
        return "Record whether it looks diffuse/multi-pixel or too isolated to trust."
    return "Record why this should be postponed or reviewed later."


def write_report(rows: list[dict[str, object]]) -> None:
    counts = Counter(row["review_batch"] for row in rows)
    lines = [
        "# First-Pass Review Plan",
        "",
        "This is the practical labeling order for turning detector candidates into human-reviewed evidence. It is intentionally small enough to start in a meeting or lab session.",
        "",
        "## Review Order",
        "",
        "1. Confirm the six known published lightning matches as positive validation examples.",
        "2. Review temporal candidates that repeat across frames.",
        "3. Label clear artifacts and cosmic-ray/hot-pixel examples as negatives.",
        "4. Inspect strong single-frame candidates, but do not overclaim them.",
        "",
        "## Batch Counts",
        "",
        "| Batch | Rows | Purpose |",
        "|---|---:|---|",
        f"| `01_known_validation_positive` | {counts['01_known_validation_positive']} | Confirm known positive validation examples. |",
        f"| `02_temporal_persistence_check` | {counts['02_temporal_persistence_check']} | Search for repeated candidates across frames. |",
        f"| `03_negative_artifact_examples` | {counts['03_negative_artifact_examples']} | Build negative examples for false-positive analysis. |",
        f"| `04_strong_single_frame_check` | {counts['04_strong_single_frame_check']} | Review high-SNR single-frame candidates cautiously. |",
        f"| `05_low_priority_hold` | {counts['05_low_priority_hold']} | Keep the rest without deleting them. |",
        "",
        "## Labeling Rule",
        "",
        "A row becomes training data only after a human fills in a label, confidence, reviewer name, and note. The detector suggestion is not the final truth.",
        "",
        "## Meeting-Friendly Explanation",
        "",
        "I am not training YOLO yet. I am building the labeled evidence set first: positives, negatives, uncertain cases, and temporal-review candidates. Once those labels exist, a learned model can be tested against this baseline.",
    ]
    PLAN_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_plan()
    write_csv(
        PLAN_CSV,
        rows,
        [
            "review_order",
            "review_batch",
            "candidate_id",
            "image_id",
            "run_date",
            "x",
            "y",
            "crop_url",
            "next_action",
            "suggested_human_label",
            "reviewer_task",
            "snr",
            "blob_size",
            "artifact_flags",
            "frame_count",
            "motion_consistency",
            "candidate_score",
            "review_note_prompt",
        ],
    )
    write_report(rows)
    print(f"Wrote {PLAN_CSV}")
    print(f"Wrote {PLAN_MD}")


if __name__ == "__main__":
    main()
