from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
DEFAULT_REVIEW_PLAN = OUTPUT_DIR / "first_pass_review_plan.csv"
DEFAULT_OUTPUT = OUTPUT_DIR / "candidate_geometry.csv"
DEFAULT_STATUS = OUTPUT_DIR / "geometry_run_status.json"
DEFAULT_WORK_DIR = ROOT / "geometry_work"
RAW_DIR = ROOT / "data" / "raw"
METADATA_DIR = ROOT / "data" / "metadata"
DEFAULT_ISIS_DATA = Path(os.environ.get("JUPITER_ISIS_DATA", Path.home() / "AppData" / "Local" / "JupiterLightning" / "isisdata"))
DEFAULT_DOCKER_IMAGE = os.environ.get("JUPITER_ISIS_IMAGE", "jupiter-lightning-isis:10.0.0")
ISIS_COMMANDS = ("ciss2isis", "spiceinit", "campt")

OUTPUT_FIELDS = [
    "candidate_id",
    "image_id",
    "run_date",
    "observation_time",
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
    "geometry_group_size",
]


def docker_executable() -> str:
    discovered = shutil.which("docker")
    if discovered:
        return discovered
    windows_default = Path("C:/Program Files/Docker/Docker/resources/bin/docker.exe")
    return str(windows_default) if windows_default.exists() else ""


class IsisRunner:
    def __init__(
        self,
        runtime: str = "auto",
        docker_image: str = DEFAULT_DOCKER_IMAGE,
        isis_data: Path = DEFAULT_ISIS_DATA,
    ) -> None:
        native_ready = all(shutil.which(command) for command in ISIS_COMMANDS)
        docker = docker_executable()
        if runtime == "auto":
            runtime = "native" if native_ready else "docker" if docker else "unavailable"
        self.runtime = runtime
        self.docker_image = docker_image
        self.isis_data = isis_data.resolve()
        self.docker = docker

    def readiness(self) -> dict[str, object]:
        if self.runtime == "native":
            commands = {command: shutil.which(command) or "" for command in ISIS_COMMANDS}
            return {"ready": all(commands.values()), "runtime": "native", "commands": commands}
        if self.runtime == "docker":
            if not self.docker:
                return {"ready": False, "runtime": "docker", "error": "Docker executable not found."}
            engine = subprocess.run([self.docker, "info"], check=False, capture_output=True, text=True)
            if engine.returncode:
                return {"ready": False, "runtime": "docker", "error": "Docker engine is not running."}
            image = subprocess.run(
                [self.docker, "image", "inspect", self.docker_image],
                check=False,
                capture_output=True,
                text=True,
            )
            return {
                "ready": image.returncode == 0,
                "runtime": "docker",
                "docker": self.docker,
                "image": self.docker_image,
                "isis_data": str(self.isis_data),
                "error": "" if image.returncode == 0 else f"Docker image {self.docker_image} is not installed.",
            }
        return {"ready": False, "runtime": self.runtime, "error": "No native ISIS or Docker runtime is available."}

    def container_path(self, path: Path) -> str:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(ROOT.resolve())
        except ValueError as error:
            raise ValueError(f"ISIS input/output path must be inside the project: {resolved}") from error
        return "/workspace/" + relative.as_posix()

    def run(self, arguments: list[str]) -> None:
        if self.runtime == "native":
            command = arguments
        elif self.runtime == "docker":
            self.isis_data.mkdir(parents=True, exist_ok=True)
            command = [
                self.docker,
                "run",
                "--rm",
                "--mount",
                f"type=bind,source={ROOT.resolve()},target=/workspace",
                "--mount",
                f"type=bind,source={self.isis_data},target=/isisdata",
                "--env",
                "ISISROOT=/opt/isis",
                "--env",
                "ISISDATA=/isisdata",
                "--workdir",
                "/workspace",
                self.docker_image,
                *arguments,
            ]
        else:
            raise RuntimeError("No ISIS runtime is available.")
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"{arguments[0]} failed: {detail[-4000:]}")


def command_readiness(runtime: str = "auto", docker_image: str = DEFAULT_DOCKER_IMAGE) -> dict[str, object]:
    return IsisRunner(runtime=runtime, docker_image=docker_image).readiness()


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

        west_longitude = first_value(row, "PositiveWest360Longitude", "PositiveWestLongitude")
        if west_longitude:
            longitude_convention = "positive-west-0-360-degrees"
        else:
            east_longitude = first_value(row, "PositiveEast360Longitude", "PositiveEastLongitude", "Longitude")
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


def download_file(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "JupiterLightningResearch/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def raw_products(image_id: str) -> tuple[Path, Path]:
    image_number = image_id.removeprefix("N")
    labels = sorted(RAW_DIR.glob(f"N{image_number}_*.LBL"))
    images = sorted(RAW_DIR.glob(f"N{image_number}_*.IMG"))
    if labels and images:
        return images[0], labels[0]

    files_path = METADATA_DIR / f"co-iss-n{image_number}-files.json"
    if not files_path.exists():
        payload_url = f"https://opus.pds-rings.seti.org/opus/api/files/co-iss-n{image_number}.json"
        download_file(payload_url, files_path)
    payload = json.loads(files_path.read_text(encoding="utf-8"))
    urls = payload.get("data", {}).get(f"co-iss-n{image_number}", {}).get("coiss_raw", [])
    for url in urls:
        download_file(url, RAW_DIR / Path(url).name)
    labels = sorted(RAW_DIR.glob(f"N{image_number}_*.LBL"))
    images = sorted(RAW_DIR.glob(f"N{image_number}_*.IMG"))
    if not labels or not images:
        raise FileNotFoundError(f"Raw Cassini EDR IMG/LBL pair missing for {image_id}")
    return images[0], labels[0]


def prepare_cube(image_id: str, work_dir: Path, runner: IsisRunner) -> Path:
    _, label_path = raw_products(image_id)
    cube_path = work_dir / "cubes" / f"{image_id}.cub"
    cube_path.parent.mkdir(parents=True, exist_ok=True)
    if not cube_path.exists():
        runner.run(
            [
                "ciss2isis",
                f"from={runner.container_path(label_path) if runner.runtime == 'docker' else label_path}",
                f"to={runner.container_path(cube_path) if runner.runtime == 'docker' else cube_path}",
            ]
        )
    runner.run(
        [
            "spiceinit",
            f"from={runner.container_path(cube_path) if runner.runtime == 'docker' else cube_path}",
            "web=true",
        ]
    )
    return cube_path


def project_image(
    image_id: str,
    rows: list[dict[str, str]],
    work_dir: Path,
    runner: IsisRunner,
) -> list[dict[str, object]]:
    cube_path = prepare_cube(image_id, work_dir, runner)
    coordinate_path = work_dir / "coordinates" / f"{image_id}.csv"
    output_path = work_dir / "campt" / f"{image_id}.csv"
    coordinate_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with coordinate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow([row["x"], row["y"]])
    runner.run(
        [
            "campt",
            f"from={runner.container_path(cube_path) if runner.runtime == 'docker' else cube_path}",
            f"coordlist={runner.container_path(coordinate_path) if runner.runtime == 'docker' else coordinate_path}",
            "coordtype=image",
            f"to={runner.container_path(output_path) if runner.runtime == 'docker' else output_path}",
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
                "geometry_group_size": "",
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
    for group in groups:
        size = len(group["rows"])
        for row in group["rows"]:
            row["geometry_group_size"] = size


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
    runtime: str = "auto",
    docker_image: str = DEFAULT_DOCKER_IMAGE,
    isis_data: Path = DEFAULT_ISIS_DATA,
) -> list[dict[str, object]]:
    runner = IsisRunner(runtime=runtime, docker_image=docker_image, isis_data=isis_data)
    readiness = runner.readiness()
    source_rows = read_rows(review_plan)
    if limit is not None:
        source_rows = source_rows[:limit]
    if not readiness.get("ready"):
        write_status(
            status_path,
            status="blocked-missing-isis-runtime",
            runtime_readiness=readiness,
            candidates_requested=len(source_rows),
            safe_interpretation="No latitude/longitude was computed.",
        )
        raise RuntimeError(str(readiness.get("error") or "USGS ISIS runtime is unavailable."))

    manifest_path = OUTPUT_DIR / "dataset_manifest.csv"
    manifest_rows = read_rows(manifest_path) if manifest_path.exists() else []
    time_by_image = {row["image_id"]: row.get("time", "") for row in manifest_rows}
    for row in source_rows:
        row["observation_time"] = time_by_image.get(row["image_id"], "")

    rows_by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        rows_by_image[row["image_id"]].append(row)

    results: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for image_id, rows in rows_by_image.items():
        try:
            results.extend(project_image(image_id, rows, work_dir, runner))
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
                    "geometry_group_size": "",
                }
                for row in rows
            )

    assign_geometry_groups(results, tolerance)
    write_rows(output_path, results)
    computed = sum(row.get("geometry_status") == "computed" for row in results)
    no_surface = sum(
        row.get("geometry_status") == "no-surface-intersection" for row in results
    )
    write_status(
        status_path,
        status=(
            "complete-with-no-intersections"
            if not failures and no_surface
            else "complete"
            if not failures
            else "partial-with-projection-failures"
        ),
        candidates_requested=len(source_rows),
        candidates_computed=computed,
        candidates_no_surface_intersection=no_surface,
        projection_failures=len(failures),
        runtime=runner.runtime,
        docker_image=runner.docker_image if runner.runtime == "docker" else "",
        image_failures=failures,
        coordinate_convention={
            "latitude": "planetographic degrees when available",
            "longitude": "positive west, 0-360 degrees",
        },
        validation_next_step="Run .\\run.ps1 geometry-validate after projection.",
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
    parser.add_argument("--runtime", choices=("auto", "native", "docker"), default="auto")
    parser.add_argument("--docker-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--isis-data", type=Path, default=DEFAULT_ISIS_DATA)
    parser.add_argument("--check", action="store_true", help="Report ISIS command readiness without projecting candidates.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.check:
        readiness = command_readiness(runtime=args.runtime, docker_image=args.docker_image)
        print(json.dumps(readiness, indent=2))
        return
    rows = run_geometry(
        review_plan=args.review_plan,
        output_path=args.output,
        status_path=args.status,
        work_dir=args.work_dir,
        tolerance=args.tolerance,
        limit=args.limit,
        keep_cubes=not args.remove_cubes,
        runtime=args.runtime,
        docker_image=args.docker_image,
        isis_data=args.isis_data,
    )
    print(f"Wrote {len(rows)} candidate geometry rows to {args.output}")


if __name__ == "__main__":
    main()
