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
}


REQUIRED_FILES = [
    "review_metrics_report.html",
    "candidate_review_dossier.html",
    "provenance_manifest.json",
    "provenance_manifest.md",
    "review_artifacts/published_match.png",
    "review_artifacts/top_unmatched_temporal_track.png",
    "review_artifacts/temporal_track_strips.png",
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

    provenance_path = OUTPUT_DIR / "provenance_manifest.json"
    if provenance_path.exists():
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        artifact_paths = {row["path"] for row in payload.get("artifacts", [])}
        assert_true("outputs/detection/candidate_review_dossier.csv" in artifact_paths, "Provenance missing candidate dossier CSV", errors)
        assert_true("outputs/detection/threshold_recommendations.csv" in artifact_paths, "Provenance missing threshold recommendations CSV", errors)

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
