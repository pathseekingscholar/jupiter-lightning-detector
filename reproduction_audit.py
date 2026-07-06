from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
RUN_PS1 = ROOT / "run.ps1"
PROVENANCE_JSON = OUTPUT_DIR / "provenance_manifest.json"
EVIDENCE_INDEX_JSON = OUTPUT_DIR / "evidence_index.json"
AUDIT_CSV = OUTPUT_DIR / "reproduction_audit.csv"
AUDIT_MD = OUTPUT_DIR / "reproduction_audit.md"


FIELDS = [
    "check_id",
    "category",
    "status",
    "value",
    "expected",
    "evidence",
    "next_action",
]


KEY_ARTIFACTS = [
    "outputs/detection/detection_summary.csv",
    "outputs/detection/known_match_report.csv",
    "outputs/detection/first_pass_review_plan.csv",
    "outputs/detection/review_session_audit.md",
    "outputs/detection/temporal_validation_plan.md",
    "outputs/detection/geometry_acquisition_checklist.md",
    "outputs/detection/manuscript_claim_matrix.md",
    "outputs/detection/evidence_index.md",
    "outputs/detection/provenance_manifest.json",
]


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_set_commands() -> set[str]:
    text = RUN_PS1.read_text(encoding="utf-8")
    match = re.search(r"\[ValidateSet\((.*?)\)\]\s*\n\s*\[string\]\$Command", text, re.S)
    if not match:
        return set()
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def command_name(command: str) -> str:
    parts = command.strip().split()
    if len(parts) < 2:
        return ""
    if parts[0].lower().endswith("run.ps1"):
        return parts[1]
    if parts[0].lower() == ".\\run.ps1":
        return parts[1]
    return parts[1] if "run.ps1" in parts[0].lower() else ""


def artifact_paths_from_manifest() -> set[str]:
    manifest = load_json(PROVENANCE_JSON)
    return {str(row.get("path", "")) for row in manifest.get("artifacts", [])}


def audit_row(
    check_id: str,
    category: str,
    status: str,
    value: object,
    expected: object,
    evidence: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "category": category,
        "status": status,
        "value": value,
        "expected": expected,
        "evidence": evidence,
        "next_action": next_action,
    }


def build_audit_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    commands = validate_set_commands()
    manifest = load_json(PROVENANCE_JSON)
    evidence_index = load_json(EVIDENCE_INDEX_JSON)
    recommended = [str(cmd) for cmd in manifest.get("recommended_reproduction_commands", [])]
    missing_commands = sorted({command_name(cmd) for cmd in recommended if command_name(cmd) and command_name(cmd) not in commands})
    artifact_paths = artifact_paths_from_manifest()
    missing_key_artifacts = [
        path
        for path in KEY_ARTIFACTS
        if not (ROOT / path).exists() or (path != "outputs/detection/provenance_manifest.json" and path not in artifact_paths)
    ]
    empty_key_artifacts = [path for path in KEY_ARTIFACTS if (ROOT / path).exists() and (ROOT / path).stat().st_size == 0]

    rows.append(audit_row(
        "RA-001",
        "command_surface",
        "ready" if commands else "not_ready",
        len(commands),
        "run.ps1 exposes a ValidateSet command list",
        "run.ps1",
        "Fix run.ps1 command declaration if command discovery fails.",
    ))
    rows.append(audit_row(
        "RA-002",
        "provenance_commands",
        "ready" if recommended else "not_ready",
        len(recommended),
        "Provenance lists reproduction commands",
        "outputs/detection/provenance_manifest.json",
        "Regenerate provenance with .\\run.ps1 provenance.",
    ))
    rows.append(audit_row(
        "RA-003",
        "command_drift",
        "ready" if not missing_commands else "not_ready",
        "|".join(missing_commands),
        "Every provenance command exists in run.ps1",
        "run.ps1; outputs/detection/provenance_manifest.json",
        "Add missing commands to run.ps1 or remove stale provenance commands.",
    ))
    rows.append(audit_row(
        "RA-004",
        "key_artifacts",
        "ready" if not missing_key_artifacts else "not_ready",
        "|".join(missing_key_artifacts),
        "All key evidence artifacts exist and appear in provenance",
        "outputs/detection/provenance_manifest.json",
        "Regenerate the relevant artifact and then regenerate provenance.",
    ))
    rows.append(audit_row(
        "RA-005",
        "key_artifact_size",
        "ready" if not empty_key_artifacts else "not_ready",
        "|".join(empty_key_artifacts),
        "Key evidence artifacts are non-empty",
        "outputs/detection",
        "Regenerate any empty artifact.",
    ))
    rows.append(audit_row(
        "RA-006",
        "evidence_index",
        "ready" if evidence_index.get("artifact_count", 0) >= len(KEY_ARTIFACTS) else "not_ready",
        evidence_index.get("artifact_count", 0),
        f"Evidence index tracks at least {len(KEY_ARTIFACTS)} artifacts",
        "outputs/detection/evidence_index.json",
        "Run .\\run.ps1 evidence-index after provenance is regenerated.",
    ))
    rows.append(audit_row(
        "RA-007",
        "validation_command",
        "ready" if "validate-outputs" in commands else "not_ready",
        "validate-outputs" if "validate-outputs" in commands else "",
        "A fast output validator exists",
        "run.ps1",
        "Keep .\\run.ps1 validate-outputs available as the fast reproduction gate.",
    ))
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    ready = sum(1 for row in rows if row["status"] == "ready")
    not_ready = sum(1 for row in rows if row["status"] != "ready")
    lines = [
        "# Reproduction Audit",
        "",
        "This audit checks whether the documented reproduction surface is internally consistent. It is a fast gate: it checks command drift and key artifact presence, but it does not rerun the full detector.",
        "",
        "## Summary",
        "",
        f"- Ready checks: {ready}",
        f"- Not-ready checks: {not_ready}",
        "",
        "## Checks",
        "",
        "| Check | Category | Status | Value | Expected | Evidence | Next action |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['check_id']}` | `{row['category']}` | `{row['status']}` | "
            f"{row['value']} | {row['expected']} | `{row['evidence']}` | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Recommended Fast Verification",
        "",
        "```powershell",
        ".\\run.ps1 provenance",
        ".\\run.ps1 evidence-index",
        ".\\run.ps1 reproduction-audit",
        ".\\run.ps1 validate-outputs",
        ".\\run.ps1 test",
        "```",
        "",
        "## Safe Interpretation",
        "",
        "A ready reproduction audit means the documented commands and key evidence files are internally consistent. It does not mean the detector has confirmed new lightning.",
    ])
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_audit_rows()
    write_csv(AUDIT_CSV, rows, FIELDS)
    write_report(rows)
    print(f"Wrote {AUDIT_CSV}")
    print(f"Wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
