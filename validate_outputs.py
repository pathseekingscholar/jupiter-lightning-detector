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
    "candidate_geometry_plan.csv": {
        "candidate_id",
        "image_id",
        "x",
        "y",
        "geometry_readiness",
        "required_method",
        "next_step",
    },
    "geometry_input_inventory.csv": {
        "image_id",
        "calibrated_image_exists",
        "calibrated_label_exists",
        "metadata_exists",
        "pds_timing_ready",
        "image_level_geometry_ready",
        "projection_input_status",
        "blocking_inputs",
    },
    "geometry_acquisition_checklist.csv": {
        "input_id",
        "kernel_kind",
        "source_url",
        "local_glob",
        "local_match_count",
        "status",
        "required_for",
        "minimum_acceptance",
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
    "review_labeling_checklist.csv": {
        "review_batch",
        "candidate_count",
        "review_goal",
        "preferred_labels",
        "required_fields",
        "training_use",
        "pass_condition",
    },
    "review_session_plan.csv": {
        "session_id",
        "session_order",
        "review_batch",
        "candidate_count",
        "output_csv",
        "review_goal",
        "allowed_labels",
        "pass_condition",
        "training_use",
        "status",
    },
    "review_session_audit.csv": {
        "session_id",
        "review_batch",
        "candidate_count",
        "filled_labels",
        "valid_labels",
        "invalid_labels",
        "missing_confidence",
        "missing_reviewer",
        "missing_review_note",
        "import_ready_rows",
        "training_ready_rows",
        "session_status",
        "next_action",
    },
    "temporal_validation_plan.csv": {
        "review_rank",
        "track_id",
        "run_date",
        "temporal_quality",
        "frame_count",
        "first_image_id",
        "last_image_id",
        "motion_consistency",
        "candidate_score",
        "geometry_status",
        "review_priority",
        "review_questions",
        "required_next_evidence",
    },
    "blind_review_packet.csv": {
        "blind_id",
        "image_id",
        "run_date",
        "crop_url",
        "reviewer_label",
        "reviewer_confidence",
        "reviewer_note",
        "needs_second_review",
    },
    "blind_review_key.csv": {
        "blind_id",
        "candidate_id",
        "review_batch",
        "next_action",
        "suggested_human_label",
    },
    "blind_review_reconciliation.csv": {
        "blind_id",
        "candidate_id",
        "reviewer_label",
        "suggested_human_label",
        "agreement",
        "label_valid",
        "confidence_valid",
    },
    "evidence_integrity_audit.csv": {
        "check",
        "status",
        "value",
        "expected",
        "evidence_file",
        "next_action",
    },
    "training_readiness.csv": {
        "gate",
        "status",
        "value",
        "minimum",
        "evidence_file",
        "interpretation",
        "next_action",
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
    "manuscript_claim_matrix.csv": {
        "claim_id",
        "paper_section",
        "claim",
        "status",
        "safe_wording",
        "unsafe_wording",
        "evidence_file",
        "proof_command",
        "current_value",
        "remaining_work",
    },
    "github_issue_backlog.csv": {
        "issue_id",
        "priority",
        "title",
        "gate",
        "gate_status",
        "labels",
        "evidence_file",
        "acceptance_criteria",
    },
    "github_project_board.csv": {
        "issue_id",
        "title",
        "lane",
        "priority",
        "gate",
        "gate_status",
        "dependency",
        "proof_command",
        "proof_artifact",
        "owner_role",
        "definition_of_done",
    },
    "review_agreement_audit.csv": {
        "metric",
        "value",
        "status",
        "meaning",
        "next_action",
    },
    "processed_date_coverage_summary.csv": {
        "run_date",
        "images_processed",
        "review_candidates",
        "published_matches",
        "unmatched_review_candidates",
        "interpretation",
    },
}


REQUIRED_FILES = [
    "review_metrics_report.html",
    "candidate_review_dossier.html",
    "geometry_readiness_report.md",
    "candidate_geometry_plan.md",
    "geometry_input_inventory.md",
    "geometry_acquisition_checklist.md",
    "nearby_filter_context_report.md",
    "human_review_audit.md",
    "first_pass_review_plan.md",
    "first_pass_review_plan.html",
    "review_session_plan.md",
    "review_session_audit.md",
    "temporal_validation_plan.md",
    "blind_review_packet.md",
    "blind_review_reconciliation.md",
    "evidence_integrity_audit.md",
    "review_labeling_protocol.md",
    "training_readiness.md",
    "doc_claim_audit.md",
    "research_gate_audit.md",
    "manuscript_claim_matrix.md",
    "github_issue_backlog.md",
    "github_project_board.md",
    "review_agreement_audit.md",
    "processed_date_coverage_summary.md",
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
    "review_sessions/S001_01_known_validation_positive.csv",
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

    session_plan_path = OUTPUT_DIR / "review_session_plan.csv"
    session_dir = OUTPUT_DIR / "review_sessions"
    if review_plan_path.exists() and session_plan_path.exists() and session_dir.exists():
        plan_rows = read_csv(review_plan_path)
        session_plan_rows = read_csv(session_plan_path)
        session_rows = []
        for session_path in sorted(session_dir.glob("S*.csv")):
            rows = read_csv(session_path)
            session_rows.extend(rows)
            if rows:
                required = {"human_label", "confidence", "reviewer", "review_note", "needs_second_review"}
                missing = required - set(rows[0].keys())
                assert_true(not missing, f"{session_path.name} missing review columns: {sorted(missing)}", errors)
        assert_true(len(session_rows) == len(plan_rows), "Review session CSV row counts do not add up to the full review plan", errors)
        assert_true(len(session_plan_rows) == len(list(session_dir.glob("S*.csv"))), "Session plan row count does not match session CSV count", errors)

    session_audit_path = OUTPUT_DIR / "review_session_audit.csv"
    if session_plan_path.exists() and session_audit_path.exists():
        session_plan_rows = read_csv(session_plan_path)
        audit_rows = read_csv(session_audit_path)
        assert_true(len(audit_rows) == len(session_plan_rows), "Review session audit row count does not match session plan", errors)
        statuses = {row.get("session_status") for row in audit_rows}
        assert_true(statuses <= {"missing_session_rows", "not_started", "needs_cleanup", "partial_review", "import_ready"}, f"Unexpected review session statuses: {sorted(statuses)}", errors)

    provenance_path = OUTPUT_DIR / "provenance_manifest.json"
    if provenance_path.exists():
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        artifact_paths = {row["path"] for row in payload.get("artifacts", [])}
        assert_true("outputs/detection/candidate_review_dossier.csv" in artifact_paths, "Provenance missing candidate dossier CSV", errors)
        assert_true("outputs/detection/threshold_recommendations.csv" in artifact_paths, "Provenance missing threshold recommendations CSV", errors)
        assert_true("outputs/detection/geometry_readiness.csv" in artifact_paths, "Provenance missing geometry readiness CSV", errors)
        assert_true("outputs/detection/candidate_geometry_plan.csv" in artifact_paths, "Provenance missing candidate geometry plan CSV", errors)
        assert_true("outputs/detection/geometry_input_inventory.csv" in artifact_paths, "Provenance missing geometry input inventory CSV", errors)
        assert_true("outputs/detection/geometry_acquisition_checklist.csv" in artifact_paths, "Provenance missing geometry acquisition checklist CSV", errors)
        assert_true("outputs/detection/nearby_filter_context.csv" in artifact_paths, "Provenance missing nearby filter context CSV", errors)
        assert_true("outputs/detection/human_review_audit.csv" in artifact_paths, "Provenance missing human review audit CSV", errors)
        assert_true("outputs/detection/first_pass_review_plan.csv" in artifact_paths, "Provenance missing first-pass review plan CSV", errors)
        assert_true("outputs/detection/review_session_plan.csv" in artifact_paths, "Provenance missing review session plan CSV", errors)
        assert_true("outputs/detection/review_session_audit.csv" in artifact_paths, "Provenance missing review session audit CSV", errors)
        assert_true("outputs/detection/temporal_validation_plan.csv" in artifact_paths, "Provenance missing temporal validation plan CSV", errors)
        assert_true("outputs/detection/review_sessions/S001_01_known_validation_positive.csv" in artifact_paths, "Provenance missing first review session CSV", errors)
        assert_true("outputs/detection/blind_review_packet.csv" in artifact_paths, "Provenance missing blind review packet CSV", errors)
        assert_true("outputs/detection/blind_review_reconciliation.csv" in artifact_paths, "Provenance missing blind review reconciliation CSV", errors)
        assert_true("outputs/detection/evidence_integrity_audit.csv" in artifact_paths, "Provenance missing evidence integrity audit CSV", errors)
        assert_true("outputs/detection/review_labeling_checklist.csv" in artifact_paths, "Provenance missing review labeling checklist CSV", errors)
        assert_true("outputs/detection/training_readiness.csv" in artifact_paths, "Provenance missing training readiness CSV", errors)
        assert_true("outputs/detection/doc_claim_audit.csv" in artifact_paths, "Provenance missing documentation claim audit CSV", errors)
        assert_true("outputs/detection/research_gate_audit.csv" in artifact_paths, "Provenance missing research gate audit CSV", errors)
        assert_true("outputs/detection/manuscript_claim_matrix.csv" in artifact_paths, "Provenance missing manuscript claim matrix CSV", errors)
        assert_true("outputs/detection/github_issue_backlog.csv" in artifact_paths, "Provenance missing GitHub issue backlog CSV", errors)
        assert_true("outputs/detection/github_project_board.csv" in artifact_paths, "Provenance missing GitHub project board CSV", errors)
        assert_true("outputs/detection/review_agreement_audit.csv" in artifact_paths, "Provenance missing review agreement audit CSV", errors)
        assert_true("outputs/detection/candidate_label_summary.csv" in artifact_paths, "Provenance missing candidate label summary CSV", errors)
        assert_true("outputs/detection/processed_date_coverage_summary.csv" in artifact_paths, "Provenance missing processed date coverage summary CSV", errors)

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
