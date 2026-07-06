from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"


REQUIRED_COLUMNS = {
    "detection_summary.csv": {
        "run_date",
        "images_processed",
        "candidates_found",
        "review_candidates",
        "published_matches",
        "unmatched_review_candidates",
    },
    "known_match_report.csv": {
        "image_id",
        "published_x",
        "published_y",
        "nearest_candidate_id",
        "offset_px",
        "recovered_within_8_px",
    },
    "review_decision_matrix.csv": {
        "review_rank",
        "candidate_id",
        "image_id",
        "x",
        "y",
        "next_action",
        "reason",
    },
    "candidate_review_dossier.csv": {
        "review_rank",
        "candidate_id",
        "crop_url",
        "next_action",
        "suggested_label",
        "snr",
        "blob_size",
    },
    "temporal_track_quality.csv": {
        "track_id",
        "frame_count",
        "motion_consistency",
        "temporal_quality",
        "quality_reason",
    },
    "threshold_recommendations.csv": {
        "snr_threshold",
        "min_blob_size",
        "published_matches",
        "published_recall",
        "interpretation",
    },
    "candidate_label_template.csv": {
        "candidate_id",
        "human_label",
        "confidence",
        "reviewer",
        "review_note",
    },
    "candidate_label_summary.csv": {
        "summary_item",
        "label_group",
        "human_label",
        "count",
        "meaning",
    },
    "geometry_readiness.csv": {
        "image_id",
        "opus_id",
        "metadata_available",
        "geometry_context_available",
        "candidate_latlon_ready",
        "readiness_note",
    },
    "nearby_filter_context.csv": {
        "candidate_id",
        "image_id",
        "candidate_time",
        "context_status",
        "context_filter",
        "delta_minutes",
    },
    "human_review_audit.csv": {
        "audit_item",
        "value",
        "status",
        "meaning",
        "next_action",
    },
    "first_pass_review_plan.csv": {
        "review_order",
        "review_batch",
        "candidate_id",
        "suggested_human_label",
        "reviewer_task",
        "review_note_prompt",
    },
    "doc_claim_audit.csv": {
        "file",
        "line",
        "pattern",
        "severity",
        "status",
        "context",
        "meaning",
    },
    "research_gate_audit.csv": {
        "gate",
        "status",
        "value",
        "evidence_file",
        "interpretation",
        "next_action",
    },
}


REQUIRED_FILES = [
    "review_metrics_report.html",
    "candidate_review_dossier.html",
    "geometry_readiness_report.md",
    "nearby_filter_context_report.md",
    "human_review_audit.md",
    "first_pass_review_plan.md",
    "first_pass_review_plan.html",
    "doc_claim_audit.md",
    "research_gate_audit.md",
    "provenance_manifest.json",
    "provenance_manifest.md",
    "review_artifacts/published_match.png",
    "review_artifacts/top_unmatched_temporal_track.png",
    "review_artifacts/temporal_track_strips.png",
    "review_batches/01_known_validation_positive.csv",
    "review_batches/02_temporal_persistence_check.csv",
    "review_batches/03_negative_artifact_examples.csv",
    "review_batches/04_strong_single_frame_check.csv",
    "review_batches/05_low_priority_hold.csv",
    "candidate_labels_grouped.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def assert_true(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate() -> list[str]:
    errors: list[str] = []
    for name, required in REQUIRED_COLUMNS.items():
        path = OUTPUT_DIR / name
        assert_true(path.exists(), f"Missing required CSV: {name}", errors)
        if not path.exists():
            continue
        rows = read_csv(path)
        assert_true(bool(rows), f"{name} has no rows", errors)
        if rows:
            missing = required - set(rows[0].keys())
            assert_true(not missing, f"{name} missing columns: {sorted(missing)}", errors)

    for name in REQUIRED_FILES:
        path = OUTPUT_DIR / name
        assert_true(path.exists(), f"Missing required artifact: {name}", errors)
        if path.exists():
            assert_true(path.stat().st_size > 0, f"Artifact is empty: {name}", errors)

    summary_path = OUTPUT_DIR / "detection_summary.csv"
    if summary_path.exists():
        summary = read_csv(summary_path)
        images = sum(int(float(row["images_processed"])) for row in summary)
        published = sum(int(float(row["published_matches"])) for row in summary)
        assert_true(images == 221, f"Expected 221 images processed; found {images}", errors)
        assert_true(published == 6, f"Expected 6 published matches; found {published}", errors)

    known_path = OUTPUT_DIR / "known_match_report.csv"
    if known_path.exists():
        known = read_csv(known_path)
        recovered = [row for row in known if row.get("recovered_within_8_px") == "yes"]
        assert_true(len(known) == 6, f"Expected 6 known-match rows; found {len(known)}", errors)
        assert_true(len(recovered) == 6, f"Expected 6 recovered known marks; found {len(recovered)}", errors)

    matrix_path = OUTPUT_DIR / "review_decision_matrix.csv"
    dossier_path = OUTPUT_DIR / "candidate_review_dossier.csv"
    if matrix_path.exists() and dossier_path.exists():
        matrix = read_csv(matrix_path)
        dossier = read_csv(dossier_path)
        assert_true(len(matrix) == len(dossier), "Decision matrix and dossier row counts differ", errors)
        actions = {row["next_action"] for row in matrix}
        assert_true("confirm_known_validation_mark" in actions, "Decision matrix lacks known validation action", errors)
        assert_true("review_as_negative_example" in actions, "Decision matrix lacks negative-review action", errors)

    claim_audit_path = OUTPUT_DIR / "doc_claim_audit.csv"
    if claim_audit_path.exists():
        claim_rows = read_csv(claim_audit_path)
        unsafe_review = [
            row for row in claim_rows
            if row.get("severity") == "unsafe" and row.get("status") == "review"
        ]
        stale_temporal = [
            row for row in claim_rows
            if row.get("pattern") == "temporal tracking planned" and row.get("status") == "needs_attention"
        ]
        assert_true(not unsafe_review, f"Documentation claim audit has unsafe review rows: {len(unsafe_review)}", errors)
        assert_true(not stale_temporal, "Documentation still says temporal tracking is only planned", errors)

    review_plan_path = OUTPUT_DIR / "first_pass_review_plan.csv"
    batch_dir = OUTPUT_DIR / "review_batches"
    if review_plan_path.exists() and batch_dir.exists():
        plan_rows = read_csv(review_plan_path)
        batch_rows = []
        for batch_path in sorted(batch_dir.glob("*.csv")):
            batch_rows.extend(read_csv(batch_path))
        assert_true(len(batch_rows) == len(plan_rows), "Review batch CSV row counts do not add up to the full review plan", errors)

    provenance_path = OUTPUT_DIR / "provenance_manifest.json"
    if provenance_path.exists():
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        artifact_paths = {row["path"] for row in payload.get("artifacts", [])}
        assert_true("outputs/detection/candidate_review_dossier.csv" in artifact_paths, "Provenance missing candidate dossier CSV", errors)
        assert_true("outputs/detection/threshold_recommendations.csv" in artifact_paths, "Provenance missing threshold recommendations CSV", errors)
        assert_true("outputs/detection/geometry_readiness.csv" in artifact_paths, "Provenance missing geometry readiness CSV", errors)
        assert_true("outputs/detection/nearby_filter_context.csv" in artifact_paths, "Provenance missing nearby filter context CSV", errors)
        assert_true("outputs/detection/human_review_audit.csv" in artifact_paths, "Provenance missing human review audit CSV", errors)
        assert_true("outputs/detection/first_pass_review_plan.csv" in artifact_paths, "Provenance missing first-pass review plan CSV", errors)
        assert_true("outputs/detection/doc_claim_audit.csv" in artifact_paths, "Provenance missing documentation claim audit CSV", errors)
        assert_true("outputs/detection/research_gate_audit.csv" in artifact_paths, "Provenance missing research gate audit CSV", errors)
        assert_true("outputs/detection/candidate_label_summary.csv" in artifact_paths, "Provenance missing candidate label summary CSV", errors)

    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("Output validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("Output validation passed.")


if __name__ == "__main__":
    main()
