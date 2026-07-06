from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
BACKLOG_CSV = OUTPUT_DIR / "github_issue_backlog.csv"
BACKLOG_MD = OUTPUT_DIR / "github_issue_backlog.md"
ISSUE_BODY_DIR = ROOT / ".github" / "issue_backlog"


LABELS_BY_GATE = {
    "human_positive_labels": "candidate-review,validation",
    "human_negative_labels": "candidate-review,false-positive-analysis",
    "saved_human_labels": "candidate-review,data-management",
    "published_marks_human_confirmed": "candidate-review,validation",
    "candidate_geometry": "geometry,science-validation",
    "model_training_readiness": "model-comparison,human-labels,validation",
    "evidence_integrity": "evidence,review-workflow,reproducibility",
    "nearby_filter_followup": "data-provenance,spectrum-followup",
    "documentation_claim_safety": "documentation,science-validation",
}


PRIORITY_BY_STATUS = {
    "not_ready": "P1",
    "in_progress": "P2",
    "ready": "P3",
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


def issue_title(gate: str, status: str) -> str:
    titles = {
        "human_positive_labels": "Label published validation matches as positive examples",
        "human_negative_labels": "Label negative artifact and hot-pixel examples",
        "saved_human_labels": "Run first human label import or workbench labeling pass",
        "published_marks_human_confirmed": "Human-confirm all six published validation marks",
        "candidate_geometry": "Add candidate pixel-to-Jupiter geometry mapping",
        "model_training_readiness": "Hold YOLO/model comparison until reviewed labels exist",
        "evidence_integrity": "Fix reviewer evidence package integrity checks",
        "nearby_filter_followup": "Review nearby non-HAL filter context after candidate validation",
        "documentation_claim_safety": "Keep documentation claim audit clean",
    }
    return titles.get(gate, f"Resolve research gate: {gate} ({status})")


def acceptance_criteria(gate: str) -> list[str]:
    criteria = {
        "human_positive_labels": [
            "All six published validation candidates are labeled `known-lightning` after visual review.",
            "`outputs/detection/candidate_label_summary.csv` reports at least 6 positive labels.",
            "`outputs/detection/human_review_audit.md` no longer reports `0 of 6` published marks labeled.",
        ],
        "human_negative_labels": [
            "At least 20 clear artifacts or cosmic-ray/hot-pixel examples are labeled.",
            "`candidate_label_summary.csv` reports at least 20 negative labels.",
            "Review notes explain why each negative is not lightning.",
        ],
        "saved_human_labels": [
            "Labels are saved through the workbench or imported from CSV.",
            "`candidate_labels.csv`, `candidate_labels_grouped.csv`, and `candidate_label_summary.csv` are regenerated.",
            "Each saved row has reviewer, confidence, and review note.",
        ],
        "published_marks_human_confirmed": [
            "The six validation candidates are inspected in context.",
            "Each row is labeled `known-lightning` with high confidence unless there is a documented reason not to.",
            "`research_gate_audit.md` marks `published_marks_human_confirmed` ready.",
        ],
        "candidate_geometry": [
            "`outputs/detection/geometry_input_inventory.csv` reports projection inputs ready for the target frames.",
            "Cassini ISS camera model assumptions are documented.",
            "Required local SPICE kernels are present and listed.",
            "Candidate x/y coordinates can be mapped to Jupiter latitude/longitude or a documented projection failure.",
            "No location-based storm claim is made until this gate is ready.",
        ],
        "model_training_readiness": [
            "`outputs/detection/training_readiness.csv` marks `model_comparison_allowed` ready.",
            "At least 6 human-confirmed positive labels and 20 human-confirmed negative labels exist.",
            "Training-ready labels include confidence, reviewer notes, and no unresolved second-review flag.",
            "Any YOLO or learned model comparison is evaluated against the classical detector baseline.",
        ],
        "evidence_integrity": [
            "`outputs/detection/evidence_integrity_audit.csv` has zero `not_ready` checks.",
            "Review plan, dossier, blind packet, blind key, and reconciliation row counts agree.",
            "Reviewer crop URLs are well formed and referenced calibrated products exist locally.",
            "Review artifact PNGs open successfully.",
        ],
        "nearby_filter_followup": [
            "Only human-reviewed candidate rows are linked to nearby non-HAL context.",
            "Context images are used as follow-up evidence, not as spectrum proof by themselves.",
            "Any color/spectrum claim cites the exact candidate and context images.",
        ],
        "documentation_claim_safety": [
            "`outputs/detection/doc_claim_audit.csv` has zero `unsafe` rows with status `review`.",
            "Generated docs do not say new lightning is confirmed before review.",
        ],
    }
    return criteria.get(gate, ["Gate-specific acceptance criteria should be added before work starts."])


def build_backlog() -> list[dict[str, object]]:
    gates = read_csv(OUTPUT_DIR / "research_gate_audit.csv")
    rows: list[dict[str, object]] = []
    for gate in gates:
        status = gate.get("status", "")
        gate_name = gate.get("gate", "")
        if status == "ready" and gate_name != "documentation_claim_safety":
            continue
        priority = PRIORITY_BY_STATUS.get(status, "P3")
        labels = LABELS_BY_GATE.get(gate_name, "research-gate")
        rows.append({
            "issue_id": "",
            "priority": priority,
            "title": issue_title(gate_name, status),
            "gate": gate_name,
            "gate_status": status,
            "labels": labels,
            "evidence_file": gate.get("evidence_file", ""),
            "current_value": gate.get("value", ""),
            "why_it_matters": gate.get("interpretation", ""),
            "next_action": gate.get("next_action", ""),
            "acceptance_criteria": " | ".join(acceptance_criteria(gate_name)),
        })
    rows.sort(key=lambda row: (str(row["priority"]), str(row["issue_id"])))
    for issue_number, row in enumerate(rows, start=1):
        row["issue_id"] = f"JLD-{issue_number:03d}"
    return rows


def write_markdown(rows: list[dict[str, object]]) -> None:
    lines = [
        "# GitHub Issue Backlog",
        "",
        "This generated backlog turns the current research gate audit into concrete GitHub-ready issues. It should be regenerated after labels, geometry, or validation outputs change.",
        "",
        "| ID | Priority | Title | Gate | Status | Labels | Evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['issue_id']}` | `{row['priority']}` | {row['title']} | `{row['gate']}` | `{row['gate_status']}` | `{row['labels']}` | `{row['evidence_file']}` |"
        )
    lines.extend([
        "",
        "## Issue Bodies",
        "",
    ])
    for row in rows:
        lines.extend([
            f"### {row['issue_id']}: {row['title']}",
            "",
            f"- Gate: `{row['gate']}`",
            f"- Current status: `{row['gate_status']}`",
            f"- Current value: {row['current_value']}",
            f"- Evidence file: `{row['evidence_file']}`",
            f"- Labels: `{row['labels']}`",
            "",
            "Why it matters:",
            "",
            str(row["why_it_matters"]),
            "",
            "Next action:",
            "",
            str(row["next_action"]),
            "",
            "Acceptance criteria:",
            "",
        ])
        for criterion in str(row["acceptance_criteria"]).split(" | "):
            lines.append(f"- [ ] {criterion}")
        lines.append("")
    BACKLOG_MD.write_text("\n".join(lines), encoding="utf-8")


def write_issue_body_files(rows: list[dict[str, object]]) -> None:
    ISSUE_BODY_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in ISSUE_BODY_DIR.glob("jld-*.md"):
        old_file.unlink()
    for row in rows:
        slug = str(row["issue_id"]).lower()
        path = ISSUE_BODY_DIR / f"{slug}.md"
        lines = [
            f"# {row['title']}",
            "",
            f"- Gate: `{row['gate']}`",
            f"- Priority: `{row['priority']}`",
            f"- Labels: `{row['labels']}`",
            f"- Evidence file: `{row['evidence_file']}`",
            f"- Current value: {row['current_value']}",
            "",
            "## Why This Matters",
            "",
            str(row["why_it_matters"]),
            "",
            "## Next Action",
            "",
            str(row["next_action"]),
            "",
            "## Acceptance Criteria",
            "",
        ]
        for criterion in str(row["acceptance_criteria"]).split(" | "):
            lines.append(f"- [ ] {criterion}")
        path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_backlog()
    write_csv(
        BACKLOG_CSV,
        rows,
        [
            "issue_id",
            "priority",
            "title",
            "gate",
            "gate_status",
            "labels",
            "evidence_file",
            "current_value",
            "why_it_matters",
            "next_action",
            "acceptance_criteria",
        ],
    )
    write_markdown(rows)
    write_issue_body_files(rows)
    print(f"Wrote {BACKLOG_CSV}")
    print(f"Wrote {BACKLOG_MD}")
    print(f"Wrote issue body files in {ISSUE_BODY_DIR}")


if __name__ == "__main__":
    main()
