from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
MANIFEST_JSON = OUTPUT_DIR / "provenance_manifest.json"
MANIFEST_MD = OUTPUT_DIR / "provenance_manifest.md"


TRACKED_OUTPUTS = [
    "dataset_manifest.csv",
    "detection_summary.csv",
    "threshold_sweep.csv",
    "known_match_report.csv",
    "temporal_track_summary.csv",
    "scientific_review_queue.csv",
    "training_manifest.csv",
    "active_learning_queue.csv",
    "review_metrics_summary.csv",
    "review_decision_matrix.csv",
    "temporal_track_quality.csv",
    "candidate_label_template.csv",
    "review_packet.md",
    "review_metrics_report.md",
    "review_metrics_report.html",
    "opus_nearby_date_coverage.csv",
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_row_count(path: Path) -> int | None:
    if path.suffix.lower() != ".csv" or not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def build_manifest() -> dict[str, object]:
    artifacts = []
    for relative in TRACKED_OUTPUTS:
        path = OUTPUT_DIR / relative
        if not path.exists():
            continue
        artifacts.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
            "rows": csv_row_count(path),
        })
    for path in sorted((OUTPUT_DIR / "review_artifacts").glob("*.png")):
        artifacts.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": file_sha256(path),
            "rows": None,
        })

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_value("rev-parse", "HEAD"),
        "git_branch": git_value("branch", "--show-current"),
        "git_remote": git_value("remote", "get-url", "origin"),
        "recommended_reproduction_commands": [
            ".\\run.ps1 detect-all",
            ".\\run.ps1 exports",
            ".\\run.ps1 coverage",
            ".\\run.ps1 review",
            ".\\run.ps1 label-template",
            ".\\run.ps1 provenance",
        ],
        "artifacts": artifacts,
    }


def write_markdown(manifest: dict[str, object]) -> None:
    lines = [
        "# Provenance Manifest",
        "",
        f"- Generated UTC: {manifest['generated_at_utc']}",
        f"- Git branch: {manifest['git_branch']}",
        f"- Git commit: {manifest['git_commit']}",
        f"- Git remote: {manifest['git_remote']}",
        "",
        "## Reproduction Commands",
        "",
    ]
    for command in manifest["recommended_reproduction_commands"]:
        lines.append(f"- `{command}`")
    lines.extend([
        "",
        "## Generated Artifacts",
        "",
        "| Path | Rows | Bytes | SHA-256 |",
        "|---|---:|---:|---|",
    ])
    for artifact in manifest["artifacts"]:
        rows = "" if artifact["rows"] is None else artifact["rows"]
        lines.append(f"| `{artifact['path']}` | {rows} | {artifact['bytes']} | `{artifact['sha256']}` |")
    MANIFEST_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    manifest = build_manifest()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_markdown(manifest)
    print(f"Wrote {MANIFEST_JSON}")
    print(f"Wrote {MANIFEST_MD}")


if __name__ == "__main__":
    main()
