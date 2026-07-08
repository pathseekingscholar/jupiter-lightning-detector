from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PUBLIC_DATA_DIR = ROOT / "public_site" / "static-data"

LABEL_VALUES = [
    "known-lightning",
    "possible-lightning",
    "artifact",
    "cosmic-ray-hot-pixel",
    "uncertain",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> object:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generated_at() -> str:
    return os.environ.get("PUBLIC_SITE_DATA_GENERATED_AT") or datetime.now(timezone.utc).isoformat()


def geometry_by_image() -> dict[str, dict[str, str]]:
    rows = read_csv(OUTPUT_DIR / "geometry_readiness.csv")
    return {row["image_id"]: row for row in rows if row.get("image_id")}


def build_queue() -> None:
    review_rows = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    geometry_rows = geometry_by_image()
    rows: list[dict[str, str]] = []
    for row in review_rows:
        geometry = geometry_rows.get(row["image_id"], {})
        rows.append(
            {
                "review_order": row.get("review_order", ""),
                "review_batch": row.get("review_batch", ""),
                "candidate_id": row.get("candidate_id", ""),
                "image_id": row.get("image_id", ""),
                "run_date": row.get("run_date", ""),
                "x": row.get("x", ""),
                "y": row.get("y", ""),
                "jupiter_latitude": "",
                "jupiter_longitude": "",
                "geometry_status": "pending-backplane",
                "geometry_group_id": "",
                "image_geometry_context_available": geometry.get("geometry_context_available", ""),
                "image_subobserver_lat": geometry.get("subobserver_lat", ""),
                "image_subobserver_lon_w": geometry.get("subobserver_lon_w", ""),
                "image_subsolar_lat": geometry.get("subsolar_lat", ""),
                "image_subsolar_lon_w": geometry.get("subsolar_lon_w", ""),
                "image_center_resolution_km_px": geometry.get("center_resolution_km_px", ""),
                "image_center_phase_angle": geometry.get("center_phase_angle", ""),
                "image_geometry_note": geometry.get("readiness_note", ""),
                "crop_url": row.get("crop_url", ""),
                "next_action": row.get("next_action", ""),
                "suggested_human_label": row.get("suggested_human_label", ""),
                "reviewer_task": row.get("reviewer_task", ""),
                "snr": row.get("snr", ""),
                "blob_size": row.get("blob_size", ""),
                "artifact_flags": row.get("artifact_flags", ""),
                "frame_count": row.get("frame_count", ""),
                "motion_consistency": row.get("motion_consistency", ""),
                "candidate_score": row.get("candidate_score", ""),
                "review_note_prompt": row.get("review_note_prompt", ""),
            }
        )
    payload = {
        "generated_at": generated_at(),
        "source": "outputs/detection/first_pass_review_plan.csv",
        "row_count": len(rows),
        "static_note": "Static public snapshot. Crop URLs that start with /api require the Python backend and local data.",
        "geometry_note": "Jupiter candidate latitude/longitude are reserved fields and remain blank until SPICE/backplane geometry is added. Image-level OPUS geometry context is included where available.",
        "geometry_status": "pending-backplane",
        "default_lat_lon_tolerance_degrees": 1.0,
        "label_values": LABEL_VALUES,
        "rows": rows,
        "summary": read_json(OUTPUT_DIR / "summary.json"),
        "coverage": read_csv(OUTPUT_DIR / "processed_date_coverage_summary.csv"),
    }
    write_json(PUBLIC_DATA_DIR / "first_pass_review_queue.json", payload)


def build_geometry_readiness() -> None:
    inventory = read_csv(OUTPUT_DIR / "geometry_input_inventory.csv")
    checklist = read_csv(OUTPUT_DIR / "geometry_acquisition_checklist.csv")
    readiness = read_csv(OUTPUT_DIR / "geometry_readiness.csv")
    blockers: dict[str, int] = {}
    for row in inventory:
        for field, value in row.items():
            if field.startswith("missing_") and value == "yes":
                blockers[field] = blockers.get(field, 0) + 1
    payload = {
        "generated_at": generated_at(),
        "status": "pending-backplane",
        "images_inventoried": len(inventory),
        "candidate_rows_checked": len(readiness),
        "default_tolerance_degrees": 1.0,
        "blocker_counts": blockers,
        "required_inputs": [
            {
                "input": row.get("input", ""),
                "kind": row.get("kind", ""),
                "status": row.get("status", ""),
                "local_matches": row.get("local_matches", ""),
                "required_for": row.get("required_for", ""),
            }
            for row in checklist
        ],
        "safe_interpretation": (
            "Candidate latitude/longitude are not computed yet. Current candidates can be reviewed "
            "in image x/y coordinates. Geometry requires Cassini ISS camera model plus SPICE kernels "
            "before storm-location claims."
        ),
        "next_steps": [
            "Download/document Cassini ISS IK/FK/CK/SPK/SCLK/LSK/PCK kernels outside Git.",
            "Create a local metakernel and coverage report for the 221 processed frames.",
            "Validate pixel-to-lat/lon projection on the six published detections.",
            "Only then populate jupiter_latitude/jupiter_longitude in public review rows.",
        ],
    }
    write_json(PUBLIC_DATA_DIR / "geometry_readiness.json", payload)


def main() -> None:
    build_queue()
    build_geometry_readiness()
    print(f"Wrote {PUBLIC_DATA_DIR / 'first_pass_review_queue.json'}")
    print(f"Wrote {PUBLIC_DATA_DIR / 'geometry_readiness.json'}")


if __name__ == "__main__":
    main()
