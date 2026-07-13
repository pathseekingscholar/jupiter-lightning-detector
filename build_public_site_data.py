from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

from PIL import Image


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
OUTPUT_DIR = ROOT / "outputs" / "detection"
PUBLIC_DIR = ROOT / "public_site"
PUBLIC_DATA_DIR = PUBLIC_DIR / "static-data"
PUBLIC_API_DIR = PUBLIC_DATA_DIR / "api"
PUBLIC_ASSET_DIR = PUBLIC_DIR / "static-assets"
PUBLIC_PREVIEW_DIR = PUBLIC_ASSET_DIR / "previews"
PUBLIC_CROP_DIR = PUBLIC_ASSET_DIR / "candidate-crops"
PUBLIC_OUTPUT_DIR = PUBLIC_DIR / "outputs" / "detection"

DETECTION_DATES = [
    "2000-12-31",
    "2001-01-01",
    "2001-01-04",
    "2001-01-05",
    "2001-01-08",
    "2001-01-09",
    "2001-01-10",
    "2001-01-11",
    "2001-01-13",
]
FRONTEND_FILES = ["index.html", "styles.css", "app.js", "review.js"]
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


def synchronize_frontend() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    for name in FRONTEND_FILES:
        shutil.copy2(WEB_DIR / name, PUBLIC_DIR / name)


def geometry_by_image() -> dict[str, dict[str, str]]:
    rows = read_csv(OUTPUT_DIR / "geometry_readiness.csv")
    return {row["image_id"]: row for row in rows if row.get("image_id")}


def geometry_by_candidate() -> dict[str, dict[str, str]]:
    rows = read_csv(OUTPUT_DIR / "candidate_geometry.csv")
    return {row["candidate_id"]: row for row in rows if row.get("candidate_id")}


def manifest_by_image() -> dict[str, dict[str, str]]:
    rows = read_csv(OUTPUT_DIR / "dataset_manifest.csv")
    return {row["image_id"]: row for row in rows if row.get("image_id")}


def render_candidate_crop(image_number: str, x: str | float, y: str | float, candidate_id: str) -> str:
    import app_server

    destination = PUBLIC_CROP_DIR / f"{candidate_id}.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        query = parse_qs(f"image={image_number}&x={round(float(x))}&y={round(float(y))}&crop=128")
        destination.write_bytes(app_server.render_detection_crop(query))
    return f"/static-assets/candidate-crops/{destination.name}"


def copy_preview(image_number: str) -> str:
    matches = sorted((ROOT / "data" / "previews").glob(f"N{image_number}_*_full.png"))
    if not matches:
        return ""
    destination = PUBLIC_PREVIEW_DIR / f"N{image_number}.webp"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or destination.stat().st_mtime < matches[0].stat().st_mtime:
        with Image.open(matches[0]) as image:
            image.convert("L").save(destination, "WEBP", quality=82, method=6)
    return f"/static-assets/previews/{destination.name}"


def build_queue(include_assets: bool = False) -> None:
    review_rows = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    image_geometry = geometry_by_image()
    candidate_geometry = geometry_by_candidate()
    image_manifest = manifest_by_image()
    rows: list[dict[str, str]] = []
    for row in review_rows:
        geometry = image_geometry.get(row["image_id"], {})
        backplane = candidate_geometry.get(row["candidate_id"], {})
        manifest = image_manifest.get(row["image_id"], {})
        geometry_status = backplane.get("geometry_status") or "pending-backplane"
        crop_url = row.get("crop_url", "")
        if include_assets:
            try:
                crop_url = render_candidate_crop(
                    row["image_id"].removeprefix("N"),
                    row.get("x", "512"),
                    row.get("y", "512"),
                    row["candidate_id"],
                )
            except (FileNotFoundError, ValueError):
                crop_url = ""
        preview_url = copy_preview(row["image_id"].removeprefix("N")) if include_assets else ""
        rows.append(
            {
                "review_order": row.get("review_order", ""),
                "review_batch": row.get("review_batch", ""),
                "candidate_id": row.get("candidate_id", ""),
                "image_id": row.get("image_id", ""),
                "run_date": row.get("run_date", ""),
                "opus_id": manifest.get("opus_id", ""),
                "opus_detail_url": f"https://opus.pds-rings.seti.org/#/detail={manifest.get('opus_id', '')}" if manifest.get("opus_id") else "",
                "timestamp_utc": manifest.get("time", ""),
                "exposure_seconds": manifest.get("duration_seconds", ""),
                "camera": manifest.get("camera", ""),
                "filter_name": manifest.get("filter", ""),
                "preview_url": preview_url,
                "x": row.get("x", ""),
                "y": row.get("y", ""),
                "jupiter_latitude": backplane.get("jupiter_latitude", ""),
                "jupiter_longitude": backplane.get("jupiter_longitude", ""),
                "geometry_status": geometry_status,
                "geometry_method": backplane.get("geometry_method", ""),
                "geometry_group_id": backplane.get("geometry_group_id", ""),
                "geometry_group_size": backplane.get("geometry_group_size", ""),
                "image_geometry_context_available": geometry.get("geometry_context_available", ""),
                "image_subobserver_lat": geometry.get("subobserver_lat", ""),
                "image_subobserver_lon_w": geometry.get("subobserver_lon_w", ""),
                "image_subsolar_lat": geometry.get("subsolar_lat", ""),
                "image_subsolar_lon_w": geometry.get("subsolar_lon_w", ""),
                "image_center_resolution_km_px": geometry.get("center_resolution_km_px", ""),
                "image_center_phase_angle": geometry.get("center_phase_angle", ""),
                "image_geometry_note": geometry.get("readiness_note", ""),
                "crop_url": crop_url,
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
    computed = sum(1 for row in rows if row["jupiter_latitude"] and row["jupiter_longitude"])
    no_intersection = sum(row["geometry_status"] == "no-surface-intersection" for row in rows)
    failures = sum(row["geometry_status"] == "projection-failed" for row in rows)
    payload = {
        "generated_at": generated_at(),
        "source": "outputs/detection/first_pass_review_plan.csv",
        "row_count": len(rows),
        "static_note": "Generated public evidence snapshot. The same frontend uses live Python APIs when opened locally.",
        "geometry_note": (
            f"ISIS found Jupiter surface intersections for {computed} of {len(rows)} rows; "
            f"{no_intersection} rows were evaluated but fall outside the modeled surface; {failures} projection failures."
        ),
        "geometry_status": "computed-with-no-intersections" if computed and not failures else "partial" if computed else "pending-backplane",
        "default_lat_lon_tolerance_degrees": 1.0,
        "label_values": LABEL_VALUES,
        "rows": rows,
        "summary": read_json(OUTPUT_DIR / "summary.json"),
        "coverage": read_csv(OUTPUT_DIR / "processed_date_coverage_summary.csv"),
    }
    write_json(PUBLIC_DATA_DIR / "first_pass_review_queue.json", payload)


def publicize_observations() -> None:
    import app_server

    payload = app_server.observation_payload()
    payload["notes"] = {}
    for observation in payload.get("observations", []):
        observation["preview_image"] = copy_preview(str(observation["image_number"]))
    write_json(PUBLIC_API_DIR / "observations.json", payload)


def publicize_detection_outputs() -> None:
    import app_server

    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for run_date in DETECTION_DATES:
        payload = app_server.read_detection_rows(run_date)
        for track_index, track in enumerate(payload.get("tracks", [])):
            for item in track.get("items", []):
                item["preview_image"] = copy_preview(str(item["image_number"]))
            if track_index < 20 and track.get("items"):
                lead = track["items"][0]
                try:
                    lead["crop_url"] = render_candidate_crop(
                        str(lead["image_number"]), lead["x"], lead["y"], lead["candidate_id"]
                    )
                except (FileNotFoundError, ValueError):
                    lead["crop_url"] = ""

        source_dir = OUTPUT_DIR / run_date
        public_date_dir = PUBLIC_OUTPUT_DIR / run_date
        public_date_dir.mkdir(parents=True, exist_ok=True)
        for name in ["summary.json", "review_candidates.csv", "candidate_contact_sheet.png"]:
            source = source_dir / name
            if source.exists():
                shutil.copy2(source, public_date_dir / name)
        payload["csv_url"] = f"/outputs/detection/{run_date}/review_candidates.csv"
        payload["all_csv_url"] = f"/outputs/detection/{run_date}/review_candidates.csv"
        payload["contact_sheet_url"] = f"/outputs/detection/{run_date}/candidate_contact_sheet.png"
        payload["public_limitation"] = (
            "The public bundle includes the review candidate table. The much larger all-pixel-region "
            "table remains a reproducible local output."
        )
        write_json(PUBLIC_API_DIR / f"detection-{run_date}.json", payload)

    write_json(PUBLIC_API_DIR / "validation.json", app_server.validation_payload())
    write_json(PUBLIC_API_DIR / "detector-characteristics.json", app_server.detector_characteristics_payload())


def copy_review_outputs() -> None:
    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source in OUTPUT_DIR.iterdir():
        if source.is_file() and source.stat().st_size <= 5_000_000:
            shutil.copy2(source, PUBLIC_OUTPUT_DIR / source.name)
    for directory_name in ["review_artifacts", "review_batches", "review_sessions"]:
        source_dir = OUTPUT_DIR / directory_name
        destination = PUBLIC_OUTPUT_DIR / directory_name
        if not source_dir.exists():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        for source in source_dir.rglob("*"):
            if source.is_file() and source.stat().st_size <= 5_000_000:
                relative = source.relative_to(source_dir)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def build_geometry_readiness() -> None:
    inventory = read_csv(OUTPUT_DIR / "geometry_input_inventory.csv")
    checklist = read_csv(OUTPUT_DIR / "geometry_acquisition_checklist.csv")
    readiness = read_csv(OUTPUT_DIR / "geometry_readiness.csv")
    candidate_geometry = geometry_by_candidate()
    computed = sum(
        1 for row in candidate_geometry.values()
        if row.get("jupiter_latitude") and row.get("jupiter_longitude")
    )
    run_status = read_json(OUTPUT_DIR / "geometry_run_status.json") or {}
    requested = int(run_status.get("candidates_requested", 0) or 0)
    failures = len(run_status.get("image_failures", []))
    no_intersection = max(0, requested - computed) if requested else 0
    blockers: dict[str, int] = {}
    for row in inventory:
        for field, value in row.items():
            if field.startswith("missing_") and value == "yes":
                blockers[field] = blockers.get(field, 0) + 1
    payload = {
        "generated_at": generated_at(),
        "status": "complete-with-no-intersections" if requested and not failures else "partial" if computed else "pending-backplane",
        "images_inventoried": len(inventory),
        "candidate_rows_checked": len(readiness),
        "candidate_coordinates_computed": computed,
        "default_tolerance_degrees": 1.0,
        "blocker_counts": blockers,
        "required_inputs": [] if computed else [
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
            f"ISIS found Jupiter surface intersections for {computed} candidates. "
            f"{no_intersection} candidates were evaluated and have no modeled surface intersection. "
            "A surface coordinate or shared group remains a review aid, not confirmation of lightning."
        ),
        "implementation": {
            "preferred": "USGS ISIS 10.0.0 ciss2isis + spiceinit web=true + campt",
            "runner": "python candidate_backplanes.py",
            "output": "outputs/detection/candidate_geometry.csv",
            "validation_gate": "six published-reference candidates projected with zero software failures",
        },
        "next_steps": [
            "Review the 42 candidates that intersect Jupiter.",
            "Treat the 64 no-surface rows as geometry-informed negative or artifact examples unless image registration shows otherwise.",
            "Inspect multi-image one-degree groups with temporal and visual context.",
            "Do not call any unmatched group new lightning until independent scientific review is complete.",
        ],
    }
    write_json(PUBLIC_DATA_DIR / "geometry_readiness.json", payload)


def main(include_assets: bool = False) -> None:
    synchronize_frontend()
    build_queue(include_assets=include_assets)
    build_geometry_readiness()
    if include_assets:
        publicize_observations()
        publicize_detection_outputs()
        copy_review_outputs()
    print(f"Wrote canonical frontend to {PUBLIC_DIR}")
    print(f"Wrote {PUBLIC_DATA_DIR / 'first_pass_review_queue.json'}")
    print(f"Wrote {PUBLIC_DATA_DIR / 'geometry_readiness.json'}")


if __name__ == "__main__":
    main(include_assets=True)
