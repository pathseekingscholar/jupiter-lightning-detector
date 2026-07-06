from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PLAN_CSV = OUTPUT_DIR / "candidate_geometry_plan.csv"
PLAN_MD = OUTPUT_DIR / "candidate_geometry_plan.md"


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


def build_plan_rows() -> list[dict[str, object]]:
    geometry = {row.get("image_id", ""): row for row in read_csv(OUTPUT_DIR / "geometry_readiness.csv")}
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    rows: list[dict[str, object]] = []
    for candidate in review_plan:
        image_id = candidate.get("image_id", "")
        geom = geometry.get(image_id, {})
        has_frame_context = geom.get("geometry_context_available") == "yes"
        has_image_bounds = all(geom.get(field) for field in ["latitude_min", "latitude_max", "longitude_w_min", "longitude_w_max"])
        if not has_frame_context:
            readiness = "blocked_missing_frame_geometry"
            next_step = "Download or regenerate OPUS geometry metadata for this image."
        elif has_image_bounds:
            readiness = "image_bounds_only"
            next_step = "Use camera/SPICE projection to map candidate x/y inside the image bounds."
        else:
            readiness = "frame_context_only"
            next_step = "Use camera/SPICE projection; OPUS bounds are unavailable locally for this frame."
        rows.append({
            "candidate_id": candidate.get("candidate_id", ""),
            "image_id": image_id,
            "run_date": candidate.get("run_date", ""),
            "review_batch": candidate.get("review_batch", ""),
            "x": candidate.get("x", ""),
            "y": candidate.get("y", ""),
            "geometry_readiness": readiness,
            "subobserver_lon_w": geom.get("subobserver_lon_w", ""),
            "subsolar_lon_w": geom.get("subsolar_lon_w", ""),
            "center_resolution_km_px": geom.get("center_resolution_km_px", ""),
            "latitude_bounds": bounds(geom.get("latitude_min", ""), geom.get("latitude_max", "")),
            "longitude_w_bounds": bounds(geom.get("longitude_w_min", ""), geom.get("longitude_w_max", "")),
            "required_method": "camera_spice_projection",
            "next_step": next_step,
        })
    return rows


def bounds(minimum: str, maximum: str) -> str:
    if not minimum or not maximum:
        return ""
    return f"{minimum}..{maximum}"


def workplan_steps() -> list[dict[str, object]]:
    return [
        {
            "step": 1,
            "name": "Collect camera geometry inputs",
            "purpose": "Identify the files needed for pixel-to-ray projection.",
            "deliverable": "Documented ISS camera model, focal length/pixel scale, image center, and distortion assumptions.",
        },
        {
            "step": 2,
            "name": "Collect SPICE/navigation inputs",
            "purpose": "Locate spacecraft position, camera pointing, Jupiter body frame, and time kernels for each image.",
            "deliverable": "Kernel list or documented fallback if exact kernels are unavailable.",
        },
        {
            "step": 3,
            "name": "Project candidate pixels to Jupiter",
            "purpose": "Convert detector x/y into a camera ray and intersect it with a Jupiter spheroid.",
            "deliverable": "candidate_geometry.csv with latitude, west longitude, incidence, emission, and projection status.",
        },
        {
            "step": 4,
            "name": "Validate against OPUS bounds",
            "purpose": "Check that projected points land within image-level OPUS latitude/longitude ranges when those ranges exist.",
            "deliverable": "geometry_validation_report.md showing pass/fail counts and outliers.",
        },
        {
            "step": 5,
            "name": "Use geometry for temporal tracks",
            "purpose": "Test whether repeated candidates move consistently in Jupiter coordinates, not just image pixels.",
            "deliverable": "track_geometry_summary.csv with same-storm plausibility flags.",
        },
    ]


def write_report(rows: list[dict[str, object]]) -> None:
    readiness = Counter(row["geometry_readiness"] for row in rows)
    batches = Counter(row["review_batch"] for row in rows)
    lines = [
        "# Candidate Geometry Implementation Plan",
        "",
        "This plan turns the current geometry blocker into an implementation checklist. It does not claim candidate latitude/longitude is solved yet.",
        "",
        "## Current Candidate Geometry State",
        "",
        f"- Review candidates planned for geometry: {len(rows)}",
        f"- Candidates with image-level bounds only: {readiness['image_bounds_only']}",
        f"- Candidates with frame context only: {readiness['frame_context_only']}",
        f"- Candidates blocked by missing frame geometry: {readiness['blocked_missing_frame_geometry']}",
        "",
        "Image-level bounds are useful context, but they are not candidate-level coordinates. A true candidate map requires camera/SPICE projection from pixel x/y to Jupiter.",
        "",
        "## Review Batches",
        "",
        "| Batch | Candidates |",
        "|---|---:|",
    ]
    for batch, count in sorted(batches.items()):
        lines.append(f"| `{batch}` | {count} |")
    lines.extend([
        "",
        "## Implementation Steps",
        "",
        "| Step | Name | Purpose | Deliverable |",
        "|---:|---|---|---|",
    ])
    for step in workplan_steps():
        lines.append(f"| {step['step']} | {step['name']} | {step['purpose']} | {step['deliverable']} |")
    lines.extend([
        "",
        "## Validation Rules",
        "",
        "- Do not use image-level latitude/longitude bounds as candidate coordinates.",
        "- Every projected candidate must include a projection status such as `intersects_jupiter`, `off_limb`, `missing_kernel`, or `projection_failed`.",
        "- Published validation candidates should be projected first because they are the safest geometry sanity check.",
        "- Temporal-track geometry should be judged after projection, not before.",
        "",
        "## First Rows To Attempt",
        "",
        "| Candidate | Image | Batch | x/y | Readiness | Next step |",
        "|---|---|---|---|---|---|",
    ])
    for row in rows[:12]:
        lines.append(
            f"| `{row['candidate_id']}` | `{row['image_id']}` | `{row['review_batch']}` | "
            f"{row['x']}, {row['y']} | `{row['geometry_readiness']}` | {row['next_step']} |"
        )
    PLAN_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_plan_rows()
    write_csv(
        PLAN_CSV,
        rows,
        [
            "candidate_id",
            "image_id",
            "run_date",
            "review_batch",
            "x",
            "y",
            "geometry_readiness",
            "subobserver_lon_w",
            "subsolar_lon_w",
            "center_resolution_km_px",
            "latitude_bounds",
            "longitude_w_bounds",
            "required_method",
            "next_step",
        ],
    )
    write_report(rows)
    print(f"Wrote {PLAN_CSV}")
    print(f"Wrote {PLAN_MD}")


if __name__ == "__main__":
    main()
