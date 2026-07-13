from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
DEFAULT_REVIEW_PLAN = OUTPUT_DIR / "first_pass_review_plan.csv"
DEFAULT_OUTPUT = OUTPUT_DIR / "candidate_geometry.csv"
DEFAULT_STATUS = OUTPUT_DIR / "geometry_run_status.json"
DEFAULT_WORK_DIR = ROOT / "geometry_work"
ISIS_COMMANDS = ("ciss2isis", "spiceinit", "campt")

OUTPUT_FIELDS = [
    "candidate_id",
    "image_id",
    "run_date",
    "x",
    "y",
    "jupiter_latitude",
    "jupiter_longitude",
    "latitude_convention",
    "longitude_convention",
    "geometry_status",
    "geometry_method",
    "geometry_error",
    "geometry_group_id",
]


def command_readiness() -> dict[str, str]:
    return {command: shutil.which(command) or "" for command in ISIS_COMMANDS}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in OUTPUT_FIELDS} for row in rows)


def normalized_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def normalized_record(row: dict[str, str]) -> dict[str, str]:
    return {normalized_key(key): value for key, value in row.items()}


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(normalized_key(key), "")
        if value not in ("", "NULL", "N/A"):
            return value
    return ""


def parse_campt_flat(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        records = [normalized_record(row) for row in csv.DictReader(handle)]
    parsed: list[dict[str, str]] = []
    for row in records:
        latitude = first_value(row, "PlanetographicLatitude")
        latitude_convention = "planetographic-degrees"
        if not latitude:
            latitude = first_value(row, "PlanetocentricLatitude", "Latitude")
            latitude_convention = "planetocentric-degrees"

        west_longitude = first_value(row, "PositiveWestLongitude")
        if west_longitude:
            longitude_convention = "positive-west-0-360-degrees"
        else:
            east_longitude = first_value(row, "PositiveEastLongitude", "Longitude")
            west_longitude = f"{(360.0 - float(east_longitude)) % 360.0:.8f}" if east_longitude else ""
            longitude_convention = "positive-west-0-360-degrees-converted-from-east"

        error = first_value(row, "Error")
        parsed.append(
            {
                "sample": first_value(row, "Sample"),
                "line": first_value(row, "Line"),
                "jupiter_latitude": latitude,
                "jupiter_longitude": west_longitude,
                "latitude_convention": latitude_convention,
                "longitude_convention": longitude_convention,
                "geometry_error": "" if error == "NULL" else error,
            }
        )
    return parsed


def run_command(arguments: list[str]) -> None:
    completed = subprocess.run(arguments, check=False, capture_output=True, text=True)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"{' '.join(arguments[:1])} failed: {detail[-2000:]}")


def image_products(image_id: str) -> tuple[Path, Path]:
    image_number = image_id.removeprefix("N")
    labels = sorted((ROOT / "data" / "calibrated").glob(f"N{image_number}_*_CALIB.LBL"))
    images = sorted((ROOT / "data" / "calibrated").glob(f"N{image_number}_*_CALIB.IMG"))
    if not labels or not images:
        raise FileNotFoundError(f"Calibrated IMG/LBL pair missing for {image_id}")
    return images[0], labels[0]


def prepare_cube(image_id: str, work_dir: Path) -> Path:
    _, label_path = image_products(image_id)
    cube_path = work_dir / "cubes" / f"{image_id}.cub"
    cube_path.parent.mkdir(parents=True, exist_ok=True)
    if not cube_path.exists():
        run_command(["ciss2isis", f"from={label_path}", f"to={cube_path}"])
        run_command(["spiceinit", f"from={cube_path}"])
    return cube_path


def project_image(image_id: str, rows: list[dict[str, str]], work_dir: Path) -> list[dict[str, object]]:
    cube_path = prepare_cube(image_id, work_dir)
    coordinate_path = work_dir / "coordinates" / f"{image_id}.csv"
    output_path = work_dir / "campt" / f"{image_id}.csv"
    coordinate_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with coordinate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow([row["x"], row["y"]])
    run_command(
        [
            "campt",
            f"from={cube_path}",
            f"coordlist={coordinate_path}",
            "coordtype=image",
            f"to={output_path}",
            "format=flat",
            "append=no",
            "allowoutside=no",
            "allowerror=yes",
        ]
    )
    projected = parse_campt_flat(output_path)
    if len(projected) != len(rows):
        raise RuntimeError(f"campt returned {len(projected)} rows for {len(rows)} coordinates in {image_id}")

    results: list[dict[str, object]] = []
    for source, geometry in zip(rows, projected, strict=True):
        complete = bool(geometry["jupiter_latitude"] and geometry["jupiter_longitude"] and not geometry["geometry_error"])
        results.append(
            {
                **source,
                **geometry,
                "geometry_status": "computed" if complete else "no-surface-intersection",
                "geometry_method": "usgs-isis-ciss2isis-spiceinit-campt",
                "geometry_group_id": "",
            }
        )
    return results


def longitude_distance(left: float, right: float) -> float:
    delta = abs(left - right) % 360.0
    return min(delta, 360.0 - delta)


def assign_geometry_groups(rows: list[dict[str, object]], tolerance: float) -> None:
    groups: list[dict[str, object]] = []
    for row in rows:
        if row.get("geometry_status") != "computed":
            continue
        latitude = float(row["jupiter_latitude"])
        longitude = float(row["jupiter_longitude"])
        group = next(
            (
                candidate for candidate in groups
                if abs(float(candidate["latitude"]) - latitude) <= tolerance
                and longitude_distance(float(candidate["longitude"]), longitude) <= tolerance
            ),
            None,
        )
        if group is None:
            group = {
                "id": f"G{len(groups) + 1:04d}",
                "latitude": latitude,
                "longitude": longitude,
                "rows": [],
            }
            groups.append(group)
        group["rows"].append(row)
        row["geometry_group_id"] = group["id"]


def write_status(path: Path, **values: object) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **values,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_geometry(
    review_plan: Path = DEFAULT_REVIEW_PLAN,
    output_path: Path = DEFAULT_OUTPUT,
    status_path: Path = DEFAULT_STATUS,
    work_dir: Path = DEFAULT_WORK_DIR,
    tolerance: float = 1.0,
    limit: int | None = None,
    keep_cubes: bool = True,
) -> list[dict[str, object]]:
    commands = command_readiness()
    missing = [name for name, path in commands.items() if not path]
    source_rows = read_rows(review_plan)
    if limit is not None:
        source_rows = source_rows[:limit]
    if missing:
        write_status(
            status_path,
            status="blocked-missing-isis",
            missing_commands=missing,
            candidates_requested=len(source_rows),
            safe_interpretation="No latitude/longitude was computed.",
        )
        raise RuntimeError(f"USGS ISIS commands are missing: {', '.join(missing)}")

    rows_by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        rows_by_image[row["image_id"]].append(row)

    results: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for image_id, rows in rows_by_image.items():
        try:
            results.extend(project_image(image_id, rows, work_dir))
        except (FileNotFoundError, RuntimeError, ValueError) as error:
            failures.append({"image_id": image_id, "error": str(error)})
            results.extend(
                {
                    **row,
                    "jupiter_latitude": "",
                    "jupiter_longitude": "",
                    "latitude_convention": "planetographic-degrees",
                    "longitude_convention": "positive-west-0-360-degrees",
                    "geometry_status": "projection-failed",
                    "geometry_method": "usgs-isis-ciss2isis-spiceinit-campt",
                    "geometry_error": str(error),
                    "geometry_group_id": "",
                }
                for row in rows
            )

    assign_geometry_groups(results, tolerance)
    write_rows(output_path, results)
    computed = sum(row.get("geometry_status") == "computed" for row in results)
    write_status(
        status_path,
        status="complete" if computed == len(results) else "partial",
        candidates_requested=len(source_rows),
        candidates_computed=computed,
        image_failures=failures,
        coordinate_convention={
            "latitude": "planetographic degrees when available",
            "longitude": "positive west, 0-360 degrees",
        },
        validation_required="Compare the six published detections before scientific use.",
    )
    if not keep_cubes and (work_dir / "cubes").exists():
        for cube in (work_dir / "cubes").glob("*.cub"):
            cube.unlink()
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Cassini ISS candidate pixels to Jupiter coordinates with USGS ISIS.")
    parser.add_argument("--review-plan", type=Path, default=DEFAULT_REVIEW_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--tolerance", type=float, default=1.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--remove-cubes", action="store_true")
    parser.add_argument("--check", action="store_true", help="Report ISIS command readiness without projecting candidates.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.check:
        readiness = command_readiness()
        print(json.dumps({"ready": all(readiness.values()), "commands": readiness}, indent=2))
        return
    rows = run_geometry(
        review_plan=args.review_plan,
        output_path=args.output,
        status_path=args.status,
        work_dir=args.work_dir,
        tolerance=args.tolerance,
        limit=args.limit,
        keep_cubes=not args.remove_cubes,
    )
    print(f"Wrote {len(rows)} candidate geometry rows to {args.output}")


if __name__ == "__main__":
    main()
