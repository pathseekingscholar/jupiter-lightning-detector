from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
METADATA_DIR = ROOT / "data" / "metadata"
GEOMETRY_CSV = OUTPUT_DIR / "geometry_readiness.csv"
GEOMETRY_MD = OUTPUT_DIR / "geometry_readiness_report.md"


GEOMETRY_SECTION = "Jupiter Surface Geometry Constraints"
FIELDS = {
    "subobserver_lat": "SURFACEGEOjupiter_subobserverplanetographiclatitude1",
    "subobserver_lon_w": "SURFACEGEOjupiter_subobserverIAUlongitude1",
    "subsolar_lat": "SURFACEGEOjupiter_subsolarplanetographiclatitude1",
    "subsolar_lon_w": "SURFACEGEOjupiter_subsolarIAUlongitude1",
    "range_to_body_km": "SURFACEGEOjupiter_rangetobody1",
    "center_resolution_km_px": "SURFACEGEOjupiter_centerresolution1",
    "center_phase_angle": "SURFACEGEOjupiter_centerphaseangle1",
    "incidence_min": "SURFACEGEOjupiter_incidence1",
    "incidence_max": "SURFACEGEOjupiter_incidence2",
    "emission_min": "SURFACEGEOjupiter_emission1",
    "emission_max": "SURFACEGEOjupiter_emission2",
    "latitude_min": "SURFACEGEOjupiter_planetographiclatitude1",
    "latitude_max": "SURFACEGEOjupiter_planetographiclatitude2",
    "longitude_w_min": "SURFACEGEOjupiter_IAUwestlongitude1",
    "longitude_w_max": "SURFACEGEOjupiter_IAUwestlongitude2",
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


def metadata_for(opus_id: str) -> dict[str, object]:
    path = METADATA_DIR / f"{opus_id}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def value_status(value: object) -> str:
    return "available" if value not in (None, "") else "missing"


def build_geometry_readiness() -> list[dict[str, object]]:
    manifest = read_csv(OUTPUT_DIR / "dataset_manifest.csv")
    rows = []
    for image in manifest:
        opus_id = image.get("opus_id", "")
        metadata = metadata_for(opus_id)
        geometry = metadata.get(GEOMETRY_SECTION, {}) if metadata else {}
        row: dict[str, object] = {
            "run_date": image.get("run_date", ""),
            "image_id": image.get("image_id", ""),
            "opus_id": opus_id,
            "time": image.get("time", ""),
            "metadata_file": f"data/metadata/{opus_id}.json" if metadata else "",
            "metadata_available": "yes" if metadata else "no",
        }
        available = 0
        for output_name, source_name in FIELDS.items():
            value = geometry.get(source_name, "")
            row[output_name] = value if value is not None else ""
            if value_status(value) == "available":
                available += 1
        has_context = all(row.get(name) not in ("", None) for name in [
            "subobserver_lat",
            "subobserver_lon_w",
            "subsolar_lat",
            "subsolar_lon_w",
            "center_resolution_km_px",
        ])
        has_pixel_bounds = all(row.get(name) not in ("", None) for name in [
            "latitude_min",
            "latitude_max",
            "longitude_w_min",
            "longitude_w_max",
        ])
        row["geometry_context_available"] = "yes" if has_context else "no"
        row["candidate_latlon_ready"] = "yes" if has_pixel_bounds else "no"
        if has_pixel_bounds:
            row["readiness_note"] = "OPUS image-level latitude/longitude bounds exist, but per-candidate mapping still needs camera geometry."
        elif has_context:
            row["readiness_note"] = "Image-level viewing geometry exists; per-candidate latitude/longitude requires camera/SPICE mapping."
        else:
            row["readiness_note"] = "Insufficient local geometry metadata for this frame."
        row["available_geometry_fields"] = available
        rows.append(row)
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    counts = Counter(row["readiness_note"] for row in rows)
    context_yes = sum(1 for row in rows if row["geometry_context_available"] == "yes")
    latlon_yes = sum(1 for row in rows if row["candidate_latlon_ready"] == "yes")
    lines = [
        "# Geometry Readiness Report",
        "",
        "This audit checks whether the processed Cassini images have enough local OPUS geometry metadata to support future candidate latitude/longitude mapping.",
        "",
        "## Summary",
        "",
        f"- Images checked: {len(rows)}",
        f"- Images with image-level viewing geometry context: {context_yes}",
        f"- Images with OPUS latitude/longitude bounds available locally: {latlon_yes}",
        "",
        "## Interpretation",
        "",
        "The current detector works in image x/y coordinates. Local OPUS metadata provides useful frame-level context such as subobserver longitude, subsolar longitude, center resolution, phase angle, incidence range, and emission range. However, the candidate-level latitude/longitude fields needed to say where a bright blob sits on Jupiter are not available as direct per-candidate values in the current local outputs.",
        "",
        "That means x/y-to-Jupiter mapping is not solved yet. The next scientific step is camera geometry or SPICE-style projection from candidate pixel coordinates to Jupiter coordinates.",
        "",
        "## Readiness Buckets",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    for note, count in counts.most_common():
        lines.append(f"| {note} | {count} |")
    lines.extend([
        "",
        "## Sample Rows",
        "",
        "| Image | Date | Subobserver lon W | Center resolution km/px | Candidate lat/lon ready | Note |",
        "|---|---|---:|---:|---|---|",
    ])
    for row in rows[:20]:
        lines.append(
            f"| {row['image_id']} | {row['run_date']} | {row['subobserver_lon_w']} | "
            f"{row['center_resolution_km_px']} | {row['candidate_latlon_ready']} | {row['readiness_note']} |"
        )
    GEOMETRY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_geometry_readiness()
    fieldnames = [
        "run_date",
        "image_id",
        "opus_id",
        "time",
        "metadata_file",
        "metadata_available",
        *FIELDS.keys(),
        "geometry_context_available",
        "candidate_latlon_ready",
        "available_geometry_fields",
        "readiness_note",
    ]
    write_csv(GEOMETRY_CSV, rows, fieldnames)
    write_report(rows)
    print(f"Wrote {GEOMETRY_CSV}")
    print(f"Wrote {GEOMETRY_MD}")


if __name__ == "__main__":
    main()
