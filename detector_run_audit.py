from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import detection_pipeline as detector


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def integer(row: dict[str, str], key: str) -> int:
    return int(float(row.get(key, 0) or 0))


def build_manifest() -> dict[str, object]:
    summaries = read_csv(OUTPUT_DIR / "detection_summary.csv")
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm_family": "custom classical computer vision",
        "implementation": ["Python", "NumPy", "Pillow"],
        "not_used": ["YOLO", "reinforcement learning", "deep learning", "OpenCV"],
        "parameters": {
            "background_blur_radius_px": detector.BACKGROUND_BLUR_RADIUS,
            "detection_snr_threshold": detector.DETECTION_SNR_THRESHOLD,
            "review_snr_threshold": detector.REVIEW_SNR_THRESHOLD,
            "minimum_review_blob_area_px": 3,
            "maximum_component_area_px": detector.MAX_COMPONENT_AREA,
            "maximum_track_displacement_px": detector.MAX_TRACK_DISPLACEMENT_PX,
            "maximum_track_gap_minutes": detector.MAX_TRACK_GAP_MINUTES,
        },
        "measured_outputs": {
            "date_windows": len(summaries),
            "images_processed": sum(integer(row, "images_processed") for row in summaries),
            "candidate_regions": sum(integer(row, "candidates_found") for row in summaries),
            "review_candidates": sum(integer(row, "review_candidates") for row in summaries),
            "first_pass_review_rows": len(review_plan),
            "known_validation_rows_in_first_pass": sum(
                row.get("review_batch") == "01_known_validation_positive" for row in review_plan
            ),
        },
        "selection_explanation": (
            "Every connected bright region is retained in per-date candidates.csv. Artifact rules and ranking produce "
            "the review-candidate tables. first_pass_review_plan.py then selects a manageable 106-row validation and "
            "review batch; 106 is not the number of detections and not a confirmed-lightning count."
        ),
        "training_policy": {
            "automatic_retraining": False,
            "current_action": "Store human labels without changing detector parameters.",
            "future_action": "A project owner manually starts a versioned training experiment after label quality review.",
        },
    }


def write_manifest(manifest: dict[str, object]) -> None:
    json_path = OUTPUT_DIR / "detector_run_manifest.json"
    markdown_path = OUTPUT_DIR / "detector_run_manifest.md"
    json_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    measured = manifest["measured_outputs"]
    parameters = manifest["parameters"]
    lines = [
        "# Detector run manifest",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## What ran",
        "",
        "A custom classical computer-vision detector written in Python with NumPy and Pillow. YOLO, reinforcement "
        "learning, deep learning, and OpenCV are not used in the current detector.",
        "",
        "## Measured outputs",
        "",
        f"- Date windows: {measured['date_windows']}",
        f"- Images processed: {measured['images_processed']}",
        f"- Connected bright regions retained: {measured['candidate_regions']}",
        f"- Review candidates after artifact/ranking rules: {measured['review_candidates']}",
        f"- Prioritized first-pass review rows: {measured['first_pass_review_rows']}",
        f"- Published validation rows in that first pass: {measured['known_validation_rows_in_first_pass']}",
        "",
        "## Fixed parameters",
        "",
        *[f"- `{key}`: {value}" for key, value in parameters.items()],
        "",
        "## Interpretation",
        "",
        str(manifest["selection_explanation"]),
        "",
        "Human labels are stored as evidence. They do not silently retrain or modify this detector.",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    manifest = build_manifest()
    write_manifest(manifest)
    print(json.dumps(manifest["measured_outputs"], indent=2))


if __name__ == "__main__":
    main()
