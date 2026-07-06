from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import jupiter_pipeline as pipeline


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
INVENTORY_CSV = OUTPUT_DIR / "geometry_input_inventory.csv"
INVENTORY_MD = OUTPUT_DIR / "geometry_input_inventory.md"

LABEL_FIELDS = [
    "IMAGE_NUMBER",
    "START_TIME",
    "STOP_TIME",
    "IMAGE_MID_TIME",
    "IMAGE_TIME",
    "SPACECRAFT_CLOCK_START_COUNT",
    "SPACECRAFT_CLOCK_STOP_COUNT",
    "INSTRUMENT_ID",
    "INSTRUMENT_MODE_ID",
    "FILTER_NAME",
    "EXPOSURE_DURATION",
]

GEOMETRY_FIELDS = [
    "SURFACEGEOjupiter_subobserverIAUlongitude1",
    "SURFACEGEOjupiter_subsolarIAUlongitude1",
    "SURFACEGEOjupiter_subobserverplanetographiclatitude1",
    "SURFACEGEOjupiter_subsolarplanetographiclatitude1",
    "SURFACEGEOjupiter_rangetobody1",
    "SURFACEGEOjupiter_centerresolution1",
    "SURFACEGEOjupiter_centerphaseangle1",
    "SURFACEGEOjupiter_incidence1",
    "SURFACEGEOjupiter_incidence2",
    "SURFACEGEOjupiter_emission1",
    "SURFACEGEOjupiter_emission2",
]

SPICE_GLOBS = [
    "*.bsp",
    "*.bc",
    "*.tf",
    "*.ti",
    "*.tls",
    "*.tsc",
    "*.tpc",
]


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


def parse_label_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, str] = {}
    for field in LABEL_FIELDS:
        match = re.search(rf"^{re.escape(field)}\s*=\s*(.+)$", text, flags=re.MULTILINE)
        if match:
            values[field] = match.group(1).strip().strip('"')
    line_match = re.search(r"^\s*LINES\s*=\s*(\d+)", text, flags=re.MULTILINE)
    sample_match = re.search(r"^\s*LINE_SAMPLES\s*=\s*(\d+)", text, flags=re.MULTILINE)
    if line_match:
        values["LINES"] = line_match.group(1)
    if sample_match:
        values["LINE_SAMPLES"] = sample_match.group(1)
    return values


def flattened_metadata(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    flat: dict[str, object] = {}
    for section in payload.values():
        if isinstance(section, dict):
            flat.update(section)
    return flat


def local_spice_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SPICE_GLOBS:
        files.extend(ROOT.glob(f"**/{pattern}"))
    return sorted({path for path in files if "node_modules" not in path.parts and ".git" not in path.parts})


def build_inventory_rows() -> list[dict[str, object]]:
    manifest = read_csv(OUTPUT_DIR / "dataset_manifest.csv")
    spice_files = local_spice_files()
    rows: list[dict[str, object]] = []
    for item in manifest:
        image_id = item.get("image_id", "")
        image_number = item.get("image_number", image_id.lstrip("N"))
        image_path, label_path = pipeline.image_paths_for_number(image_number)
        metadata_path = ROOT / "data" / "metadata" / f"{item.get('opus_id', '').lower()}.json"
        label_values = parse_label_values(label_path)
        metadata = flattened_metadata(metadata_path)
        present_label_fields = sum(1 for field in LABEL_FIELDS if label_values.get(field))
        present_geometry_fields = sum(1 for field in GEOMETRY_FIELDS if metadata.get(field) not in {"", None})
        image_dimensions_ready = label_values.get("LINES") == "1024" and label_values.get("LINE_SAMPLES") == "1024"
        pds_timing_ready = all(label_values.get(field) for field in ["START_TIME", "STOP_TIME", "IMAGE_MID_TIME", "SPACECRAFT_CLOCK_START_COUNT"])
        image_level_geometry_ready = present_geometry_fields >= 8
        camera_model_ready = False
        spice_ready = bool(spice_files)
        blockers = []
        if not image_path.exists() or not label_path.exists():
            blockers.append("missing_calibrated_product")
        if not pds_timing_ready:
            blockers.append("missing_label_timing_or_sclk")
        if not image_level_geometry_ready:
            blockers.append("missing_opus_image_geometry")
        if not camera_model_ready:
            blockers.append("missing_documented_iss_camera_model")
        if not spice_ready:
            blockers.append("missing_local_spice_kernels")
        status = "projection_inputs_ready" if not blockers else "blocked"
        rows.append({
            "run_date": item.get("run_date", ""),
            "image_id": image_id,
            "opus_id": item.get("opus_id", ""),
            "calibrated_image_exists": "yes" if image_path.exists() else "no",
            "calibrated_label_exists": "yes" if label_path.exists() else "no",
            "metadata_exists": "yes" if metadata_path.exists() else "no",
            "image_lines": label_values.get("LINES", ""),
            "line_samples": label_values.get("LINE_SAMPLES", ""),
            "image_dimensions_ready": "yes" if image_dimensions_ready else "no",
            "label_fields_present": present_label_fields,
            "pds_timing_ready": "yes" if pds_timing_ready else "no",
            "image_mid_time": label_values.get("IMAGE_MID_TIME", ""),
            "spacecraft_clock_start": label_values.get("SPACECRAFT_CLOCK_START_COUNT", ""),
            "instrument_id": label_values.get("INSTRUMENT_ID", ""),
            "filter_name": label_values.get("FILTER_NAME", ""),
            "opus_geometry_fields_present": present_geometry_fields,
            "image_level_geometry_ready": "yes" if image_level_geometry_ready else "no",
            "subobserver_lon_w": metadata.get("SURFACEGEOjupiter_subobserverIAUlongitude1", ""),
            "subsolar_lon_w": metadata.get("SURFACEGEOjupiter_subsolarIAUlongitude1", ""),
            "center_resolution_km_px": metadata.get("SURFACEGEOjupiter_centerresolution1", ""),
            "camera_model_ready": "no",
            "local_spice_kernels_found": len(spice_files),
            "spice_ready": "yes" if spice_ready else "no",
            "projection_input_status": status,
            "blocking_inputs": "|".join(blockers),
        })
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    status_counts = Counter(str(row["projection_input_status"]) for row in rows)
    blockers = Counter()
    for row in rows:
        for blocker in str(row.get("blocking_inputs", "")).split("|"):
            if blocker:
                blockers[blocker] += 1
    lines = [
        "# Geometry Input Inventory",
        "",
        "This inventory checks whether the local project has the inputs needed to convert detector x/y pixels into Jupiter latitude/longitude. It does not perform that projection.",
        "",
        "## Summary",
        "",
        f"- Images inventoried: {len(rows)}",
        f"- Projection-input-ready images: {status_counts.get('projection_inputs_ready', 0)}",
        f"- Blocked images: {status_counts.get('blocked', 0)}",
        "",
        "## Blocking Inputs",
        "",
        "| Blocker | Images |",
        "|---|---:|",
    ]
    for blocker, count in sorted(blockers.items()):
        lines.append(f"| `{blocker}` | {count} |")
    lines.extend([
        "",
        "## What Is Present",
        "",
        "- Calibrated PDS image and label products exist for the processed frames.",
        "- PDS labels provide timing, spacecraft clock counts, instrument ID, filter name, image dimensions, and exposure metadata.",
        "- OPUS metadata provides image-level viewing geometry such as subobserver/subsolar longitude, range, phase, incidence, emission, and center resolution.",
        "",
        "## What Is Missing",
        "",
        "- A documented Cassini ISS camera model usable for pixel-to-ray projection.",
        "- Local SPICE kernels for spacecraft trajectory, pointing, frame definitions, leapseconds, and spacecraft clock conversion.",
        "",
        "## Safe Interpretation",
        "",
        "The project has enough local metadata to explain why candidate geometry is blocked, but not enough to claim candidate latitude/longitude. The next implementation step is to collect/document camera and SPICE inputs, then project a small validation set before applying geometry to all candidates.",
    ])
    INVENTORY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_inventory_rows()
    write_csv(
        INVENTORY_CSV,
        rows,
        [
            "run_date",
            "image_id",
            "opus_id",
            "calibrated_image_exists",
            "calibrated_label_exists",
            "metadata_exists",
            "image_lines",
            "line_samples",
            "image_dimensions_ready",
            "label_fields_present",
            "pds_timing_ready",
            "image_mid_time",
            "spacecraft_clock_start",
            "instrument_id",
            "filter_name",
            "opus_geometry_fields_present",
            "image_level_geometry_ready",
            "subobserver_lon_w",
            "subsolar_lon_w",
            "center_resolution_km_px",
            "camera_model_ready",
            "local_spice_kernels_found",
            "spice_ready",
            "projection_input_status",
            "blocking_inputs",
        ],
    )
    write_report(rows)
    print(f"Wrote {INVENTORY_CSV}")
    print(f"Wrote {INVENTORY_MD}")


if __name__ == "__main__":
    main()
