from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
CHECKLIST_CSV = OUTPUT_DIR / "geometry_acquisition_checklist.csv"
CHECKLIST_MD = OUTPUT_DIR / "geometry_acquisition_checklist.md"

NAIF_CASSINI_ROOT = "https://naif.jpl.nasa.gov/pub/naif/CASSINI/kernels/"
NAIF_PDS_ARCHIVE = "https://naif.jpl.nasa.gov/pub/naif/pds/data/co-s_j_e_v-spice-6-v1.0/cosp_1000/aareadme.htm"
ISS_IK_URL = "https://naif.jpl.nasa.gov/pub/naif/CASSINI/kernels/ik/release.10/cas_iss_v09.ti"


REQUIRED_INPUTS = [
    {
        "input_id": "iss_camera_model",
        "kind": "IK",
        "purpose": "Cassini ISS NAC field-of-view, focal length, boresight, and instrument geometry.",
        "source_url": ISS_IK_URL,
        "local_glob": "**/cas_iss*.ti",
        "required_for": "pixel_to_camera_ray",
        "minimum_acceptance": "ISS NAC instrument kernel is present and camera assumptions are documented.",
    },
    {
        "input_id": "cassini_frames",
        "kind": "FK",
        "purpose": "Cassini spacecraft and instrument frame definitions.",
        "source_url": f"{NAIF_CASSINI_ROOT}fk/",
        "local_glob": "**/*.tf",
        "required_for": "camera_frame_to_spacecraft_frame",
        "minimum_acceptance": "Cassini frame kernel is present and loaded with the ISS IK.",
    },
    {
        "input_id": "cassini_pointing",
        "kind": "CK",
        "purpose": "Cassini spacecraft/instrument orientation for each image time.",
        "source_url": f"{NAIF_CASSINI_ROOT}ck/",
        "local_glob": "**/*.bc",
        "required_for": "spacecraft_pointing_at_image_time",
        "minimum_acceptance": "CK coverage includes all processed image times or each missing interval is documented.",
    },
    {
        "input_id": "cassini_trajectory",
        "kind": "SPK",
        "purpose": "Cassini spacecraft and solar-system body ephemerides.",
        "source_url": f"{NAIF_CASSINI_ROOT}spk/",
        "local_glob": "**/*.bsp",
        "required_for": "spacecraft_and_jupiter_position",
        "minimum_acceptance": "SPK coverage includes the processed Jupiter flyby image times.",
    },
    {
        "input_id": "spacecraft_clock",
        "kind": "SCLK",
        "purpose": "Convert Cassini spacecraft clock counts to ephemeris time.",
        "source_url": f"{NAIF_CASSINI_ROOT}sclk/",
        "local_glob": "**/*.tsc",
        "required_for": "image_sclk_to_et",
        "minimum_acceptance": "SCLK kernel supports the spacecraft clock counts in PDS labels.",
    },
    {
        "input_id": "leapseconds",
        "kind": "LSK",
        "purpose": "UTC/ephemeris-time conversion.",
        "source_url": f"{NAIF_CASSINI_ROOT}lsk/",
        "local_glob": "**/*.tls",
        "required_for": "utc_to_et",
        "minimum_acceptance": "Leapseconds kernel is present and loadable by SPICE.",
    },
    {
        "input_id": "jupiter_body_model",
        "kind": "PCK",
        "purpose": "Jupiter body orientation and reference ellipsoid/radii.",
        "source_url": f"{NAIF_CASSINI_ROOT}pck/",
        "local_glob": "**/*.tpc",
        "required_for": "ray_jupiter_intercept",
        "minimum_acceptance": "PCK is present and Jupiter radii/orientation are available.",
    },
]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def local_matches(pattern: str) -> list[Path]:
    ignored_parts = {".git", "node_modules", "__pycache__"}
    matches = []
    for path in ROOT.glob(pattern):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        matches.append(path)
    return sorted(matches)


def build_checklist_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in REQUIRED_INPUTS:
        matches = local_matches(item["local_glob"])
        rows.append({
            "input_id": item["input_id"],
            "kernel_kind": item["kind"],
            "purpose": item["purpose"],
            "source_url": item["source_url"],
            "local_glob": item["local_glob"],
            "local_matches": "|".join(str(path.relative_to(ROOT)).replace("\\", "/") for path in matches),
            "local_match_count": len(matches),
            "status": "present" if matches else "missing",
            "required_for": item["required_for"],
            "minimum_acceptance": item["minimum_acceptance"],
        })
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    present = sum(1 for row in rows if row["status"] == "present")
    missing = sum(1 for row in rows if row["status"] == "missing")
    lines = [
        "# Geometry Acquisition Checklist",
        "",
        "This checklist lists the camera and SPICE inputs needed before candidate x/y pixels can be projected to Jupiter latitude/longitude. It does not download kernels and it does not perform projection.",
        "",
        "## Official Sources",
        "",
        f"- NAIF Cassini kernels root: {NAIF_CASSINI_ROOT}",
        f"- NAIF/PDS Cassini SPICE archive readme: {NAIF_PDS_ARCHIVE}",
        f"- Cassini ISS instrument kernel example: {ISS_IK_URL}",
        "",
        "## Summary",
        "",
        f"- Required input groups: {len(rows)}",
        f"- Present locally: {present}",
        f"- Missing locally: {missing}",
        "",
        "## Required Inputs",
        "",
        "| Input | Kind | Status | Local matches | Required for |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['input_id']}` | `{row['kernel_kind']}` | `{row['status']}` | "
            f"{row['local_match_count']} | {row['required_for']} |"
        )
    lines.extend([
        "",
        "## Acquisition Notes",
        "",
        "- Keep downloaded kernels out of Git unless a tiny text kernel is explicitly approved for source control.",
        "- Record every downloaded file in this checklist or a future metakernel before running projection code.",
        "- Coverage must be checked against the image times in `outputs/detection/geometry_input_inventory.csv`.",
        "- The first projection test should use the six published validation candidates before applying geometry to unmatched candidates.",
        "",
        "## Safe Interpretation",
        "",
        "When this checklist is mostly missing, candidate-level geometry is not ready. The detector can still work in image coordinates, but it cannot make storm-location claims on Jupiter.",
    ])
    CHECKLIST_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_checklist_rows()
    write_csv(
        CHECKLIST_CSV,
        rows,
        [
            "input_id",
            "kernel_kind",
            "purpose",
            "source_url",
            "local_glob",
            "local_matches",
            "local_match_count",
            "status",
            "required_for",
            "minimum_acceptance",
        ],
    )
    write_report(rows)
    print(f"Wrote {CHECKLIST_CSV}")
    print(f"Wrote {CHECKLIST_MD}")


if __name__ == "__main__":
    main()
