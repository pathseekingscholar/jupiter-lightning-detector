from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_validation() -> tuple[list[dict[str, str]], dict[str, int]]:
    geometry = {row["candidate_id"]: row for row in read_csv(OUTPUT_DIR / "candidate_geometry.csv")}
    matches = read_csv(OUTPUT_DIR / "known_match_report.csv")
    validation_rows: list[dict[str, str]] = []
    for match in matches:
        projected = geometry.get(match["nearest_candidate_id"], {})
        validation_rows.append(
            {
                "published_label": match["published_label"],
                "image_id": match["image_id"],
                "published_x": match["published_x"],
                "published_y": match["published_y"],
                "detector_candidate_id": match["nearest_candidate_id"],
                "detector_x": match["nearest_x"],
                "detector_y": match["nearest_y"],
                "pixel_offset": match["offset_px"],
                "recovered_within_8_px": match["recovered_within_8_px"],
                "jupiter_planetographic_latitude": projected.get("jupiter_latitude", ""),
                "jupiter_positive_west_longitude": projected.get("jupiter_longitude", ""),
                "geometry_status": projected.get("geometry_status", "not-in-projected-queue"),
                "geometry_group_id": projected.get("geometry_group_id", ""),
            }
        )

    all_geometry = list(geometry.values())
    group_images: dict[str, set[str]] = defaultdict(set)
    group_rows = Counter()
    for row in all_geometry:
        group_id = row.get("geometry_group_id", "")
        if group_id:
            group_rows[group_id] += 1
            group_images[group_id].add(row["image_id"])
    metrics = {
        "queue_rows": len(all_geometry),
        "coordinates_computed": sum(row.get("geometry_status") == "computed" for row in all_geometry),
        "no_surface_intersections": sum(row.get("geometry_status") == "no-surface-intersection" for row in all_geometry),
        "projection_failures": sum(row.get("geometry_status") == "projection-failed" for row in all_geometry),
        "published_matches": len(validation_rows),
        "published_matches_projected": sum(row["geometry_status"] == "computed" for row in validation_rows),
        "surface_groups": len(group_rows),
        "multi_candidate_groups": sum(size > 1 for size in group_rows.values()),
        "multi_image_groups": sum(len(images) > 1 for images in group_images.values()),
    }
    return validation_rows, metrics


def write_report(rows: list[dict[str, str]], metrics: dict[str, int]) -> None:
    write_csv(OUTPUT_DIR / "geometry_validation.csv", rows)
    lines = [
        "# Candidate geometry validation",
        "",
        "## Batch result",
        "",
        *[f"- {key.replace('_', ' ').capitalize()}: {value}" for key, value in metrics.items()],
        "",
        "## Published-reference candidates",
        "",
        "| Label | Image | Paper x/y | Detector x/y | Offset px | Latitude | Longitude W | Status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['published_label']} | {row['image_id']} | {row['published_x']}, {row['published_y']} | "
            f"{row['detector_x']}, {row['detector_y']} | {row['pixel_offset']} | "
            f"{row['jupiter_planetographic_latitude'] or 'n/a'} | "
            f"{row['jupiter_positive_west_longitude'] or 'n/a'} | {row['geometry_status']} |"
        )
    lines.extend(
        [
            "",
            "The paper validates image-pixel recovery. It does not provide a latitude/longitude table for these six "
            "marks. The surface coordinates above are new derived metadata from the ISIS camera model and must retain "
            "their method and coordinate-convention fields.",
            "",
            "A shared one-degree surface group is a review aid, not proof that candidates are the same storm.",
        ]
    )
    (OUTPUT_DIR / "geometry_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, metrics = build_validation()
    write_report(rows, metrics)
    print(metrics)


if __name__ == "__main__":
    main()
