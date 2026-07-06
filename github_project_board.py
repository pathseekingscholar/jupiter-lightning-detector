from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
BACKLOG_CSV = OUTPUT_DIR / "github_issue_backlog.csv"
BOARD_CSV = OUTPUT_DIR / "github_project_board.csv"
BOARD_MD = OUTPUT_DIR / "github_project_board.md"


BOARD_FIELDS = [
    "issue_id",
    "title",
    "lane",
    "priority",
    "gate",
    "gate_status",
    "dependency",
    "blocked_by",
    "proof_command",
    "proof_artifact",
    "owner_role",
    "definition_of_done",
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


def lane_for(row: dict[str, str]) -> str:
    gate = row.get("gate", "")
    status = row.get("gate_status", "")
    if gate in {"human_positive_labels", "human_negative_labels", "saved_human_labels", "published_marks_human_confirmed"}:
        return "Human Review"
    if gate == "candidate_geometry":
        return "Geometry / SPICE"
    if gate == "model_training_readiness":
        return "Model Readiness"
    if gate == "nearby_filter_followup":
        return "Spectrum Follow-Up"
    if status == "ready":
        return "Maintenance"
    return "Validation"


def dependency_for(row: dict[str, str]) -> tuple[str, str]:
    gate = row.get("gate", "")
    if gate == "human_positive_labels":
        return "review_sessions", "S001 known validation session must be reviewed"
    if gate == "human_negative_labels":
        return "review_sessions", "S005 and S006 negative sessions must be reviewed"
    if gate == "saved_human_labels":
        return "label_import", "At least one completed review session CSV"
    if gate == "published_marks_human_confirmed":
        return "human_positive_labels", "Six known validation candidates need labels"
    if gate == "candidate_geometry":
        return "spice_inputs", "NAIF Cassini kernels and ISS camera assumptions"
    if gate == "model_training_readiness":
        return "human_labels", "6 positives, 20 negatives, confidence, notes, no unresolved second-review flags"
    if gate == "nearby_filter_followup":
        return "candidate_validation", "Reviewed candidate labels before spectrum/color follow-up"
    return "none", ""


def proof_for(row: dict[str, str]) -> tuple[str, str]:
    gate = row.get("gate", "")
    if gate in {"human_positive_labels", "human_negative_labels", "saved_human_labels", "published_marks_human_confirmed"}:
        return ".\\run.ps1 label-summary; .\\run.ps1 label-audit; .\\run.ps1 research-gates", "outputs/detection/human_review_audit.md"
    if gate == "candidate_geometry":
        return ".\\run.ps1 geometry-inputs; .\\run.ps1 geometry-acquisition; .\\run.ps1 research-gates", "outputs/detection/geometry_input_inventory.md"
    if gate == "model_training_readiness":
        return ".\\run.ps1 training-readiness; .\\run.ps1 research-gates", "outputs/detection/training_readiness.md"
    if gate == "nearby_filter_followup":
        return ".\\run.ps1 filters; .\\run.ps1 research-gates", "outputs/detection/nearby_filter_context_report.md"
    if gate == "documentation_claim_safety":
        return ".\\run.ps1 claim-audit; .\\run.ps1 research-gates", "outputs/detection/doc_claim_audit.md"
    return ".\\run.ps1 validate-outputs", row.get("evidence_file", "")


def owner_role_for(row: dict[str, str]) -> str:
    gate = row.get("gate", "")
    if gate in {"human_positive_labels", "human_negative_labels", "saved_human_labels", "published_marks_human_confirmed"}:
        return "human reviewer"
    if gate == "candidate_geometry":
        return "geometry/SPICE implementer"
    if gate == "model_training_readiness":
        return "modeling lead after labels exist"
    if gate == "nearby_filter_followup":
        return "science reviewer"
    return "maintainer"


def definition_of_done(row: dict[str, str]) -> str:
    criteria = str(row.get("acceptance_criteria", "")).replace(" | ", "; ")
    return criteria or "The evidence artifact proves the gate is ready."


def build_board_rows() -> list[dict[str, object]]:
    backlog = read_csv(BACKLOG_CSV)
    rows: list[dict[str, object]] = []
    for row in backlog:
        dependency, blocked_by = dependency_for(row)
        proof_command, proof_artifact = proof_for(row)
        rows.append({
            "issue_id": row.get("issue_id", ""),
            "title": row.get("title", ""),
            "lane": lane_for(row),
            "priority": row.get("priority", ""),
            "gate": row.get("gate", ""),
            "gate_status": row.get("gate_status", ""),
            "dependency": dependency,
            "blocked_by": blocked_by,
            "proof_command": proof_command,
            "proof_artifact": proof_artifact,
            "owner_role": owner_role_for(row),
            "definition_of_done": definition_of_done(row),
        })
    rows.sort(key=lambda row: (str(row["priority"]), str(row["lane"]), str(row["issue_id"])))
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    lane_counts = Counter(str(row["lane"]) for row in rows)
    lines = [
        "# GitHub Project Board",
        "",
        "This generated board converts the research-gate backlog into contributor-facing work lanes. It is not proof that GitHub issues were created remotely; it is the reproducible project-board source for the repo.",
        "",
        "## Board Summary",
        "",
        f"- Total cards: {len(rows)}",
    ]
    for lane, count in sorted(lane_counts.items()):
        lines.append(f"- {lane}: {count}")
    lines.extend([
        "",
        "## Lanes",
        "",
        "| Lane | Issue | Priority | Dependency | Proof artifact | Owner role |",
        "|---|---|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row['lane']} | `{row['issue_id']}` {row['title']} | `{row['priority']}` | "
            f"{row['dependency']} | `{row['proof_artifact']}` | {row['owner_role']} |"
        )
    lines.extend([
        "",
        "## Card Details",
        "",
    ])
    for row in rows:
        lines.extend([
            f"### {row['issue_id']} - {row['title']}",
            "",
            f"- Lane: {row['lane']}",
            f"- Gate: `{row['gate']}` (`{row['gate_status']}`)",
            f"- Dependency: `{row['dependency']}`",
            f"- Blocked by: {row['blocked_by'] or 'nothing explicit'}",
            f"- Proof command: `{row['proof_command']}`",
            f"- Proof artifact: `{row['proof_artifact']}`",
            f"- Owner role: {row['owner_role']}",
            "",
            "Definition of done:",
            "",
        ])
        for item in str(row["definition_of_done"]).split("; "):
            lines.append(f"- [ ] {item}")
        lines.append("")
    lines.extend([
        "## Safe Interpretation",
        "",
        "A board card moving to done means the cited evidence file proves that gate improved. It does not mean new Jupiter lightning has been confirmed.",
    ])
    BOARD_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_board_rows()
    write_csv(BOARD_CSV, rows, BOARD_FIELDS)
    write_report(rows)
    print(f"Wrote {BOARD_CSV}")
    print(f"Wrote {BOARD_MD}")


if __name__ == "__main__":
    main()
