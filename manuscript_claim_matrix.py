from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
CLAIM_CSV = OUTPUT_DIR / "manuscript_claim_matrix.csv"
CLAIM_MD = OUTPUT_DIR / "manuscript_claim_matrix.md"


FIELDS = [
    "claim_id",
    "paper_section",
    "claim",
    "status",
    "safe_wording",
    "unsafe_wording",
    "evidence_file",
    "proof_command",
    "current_value",
    "remaining_work",
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


def numeric(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def gate_lookup() -> dict[str, dict[str, str]]:
    return {row.get("gate", ""): row for row in read_csv(OUTPUT_DIR / "research_gate_audit.csv")}


def summary_totals() -> dict[str, int]:
    rows = read_csv(OUTPUT_DIR / "detection_summary.csv")
    return {
        "images_processed": sum(int(numeric(row.get("images_processed"))) for row in rows),
        "candidates_found": sum(int(numeric(row.get("candidates_found"))) for row in rows),
        "review_candidates": sum(int(numeric(row.get("review_candidates"))) for row in rows),
        "published_matches": sum(int(numeric(row.get("published_matches"))) for row in rows),
        "unmatched_review_candidates": sum(int(numeric(row.get("unmatched_review_candidates"))) for row in rows),
    }


def label_summary_value(item: str) -> int:
    for row in read_csv(OUTPUT_DIR / "candidate_label_summary.csv"):
        if row.get("summary_item") == item:
            return int(numeric(row.get("count")))
    return 0


def status_from_gate(gates: dict[str, dict[str, str]], gate: str) -> str:
    status = gates.get(gate, {}).get("status", "not_ready")
    return {
        "ready": "supported",
        "in_progress": "limited",
        "not_ready": "not_supported",
    }.get(status, "not_supported")


def claim(
    claim_id: str,
    paper_section: str,
    claim_text: str,
    status: str,
    safe_wording: str,
    unsafe_wording: str,
    evidence_file: str,
    proof_command: str,
    current_value: object,
    remaining_work: str,
) -> dict[str, object]:
    return {
        "claim_id": claim_id,
        "paper_section": paper_section,
        "claim": claim_text,
        "status": status,
        "safe_wording": safe_wording,
        "unsafe_wording": unsafe_wording,
        "evidence_file": evidence_file,
        "proof_command": proof_command,
        "current_value": current_value,
        "remaining_work": remaining_work,
    }


def build_claim_rows() -> list[dict[str, object]]:
    gates = gate_lookup()
    totals = summary_totals()
    positive_labels = label_summary_value("group_positive")
    negative_labels = label_summary_value("group_negative")
    saved_labels = label_summary_value("total_labels")
    rows = [
        claim(
            "C01",
            "Data",
            "The pipeline processes the current Cassini ISS NAC/H-alpha Jupiter image set.",
            status_from_gate(gates, "data_processed"),
            f"The current reproducible run processes {totals['images_processed']} Cassini ISS NAC/H-alpha frames.",
            "The pipeline processes every relevant Cassini Jupiter image.",
            "outputs/detection/detection_summary.csv",
            ".\\run.ps1 detect-all; .\\run.ps1 exports; .\\run.ps1 research-gates",
            f"{totals['images_processed']} images",
            "Expand OPUS coverage only with documented query criteria and regenerated manifests.",
        ),
        claim(
            "C02",
            "Validation",
            "The detector recovers the published lightning validation marks.",
            status_from_gate(gates, "published_match_recovery"),
            f"The detector recovers {totals['published_matches']} of 6 published validation marks within the configured matching radius.",
            "The detector proves all lightning has been found.",
            "outputs/detection/known_match_report.csv",
            ".\\run.ps1 exports; .\\run.ps1 research-gates",
            f"{totals['published_matches']} of 6 published matches",
            "Keep threshold changes tied to known-match recall and report any missed validation mark.",
        ),
        claim(
            "C03",
            "Candidate Review",
            "The detector generates a review queue rather than a confirmed discovery catalog.",
            status_from_gate(gates, "first_pass_review_queue"),
            f"The workflow curates {totals['review_candidates']} review candidates and a 106-row first-pass review plan.",
            "The detector found thousands of lightning events.",
            "outputs/detection/first_pass_review_plan.csv",
            ".\\run.ps1 review; .\\run.ps1 review-plan; .\\run.ps1 review-sessions",
            f"{totals['review_candidates']} review candidates; 106 first-pass rows",
            "Complete human review sessions and preserve false positives for analysis.",
        ),
        claim(
            "C04",
            "Human Review",
            "Human labels are not yet sufficient for training or scientific discovery claims.",
            "not_supported" if saved_labels == 0 else "limited",
            f"Current saved labels: {saved_labels}; positives: {positive_labels}; negatives: {negative_labels}.",
            "The model has been trained on reviewed labels.",
            "outputs/detection/candidate_label_summary.csv",
            ".\\run.ps1 label-summary; .\\run.ps1 label-audit; .\\run.ps1 training-readiness",
            f"{saved_labels} saved labels; {positive_labels} positive; {negative_labels} negative",
            "Review S001 for known positives and S005-S006 for negative examples, then import labels.",
        ),
        claim(
            "C05",
            "Geometry",
            "Candidate-level Jupiter latitude/longitude is not ready yet.",
            status_from_gate(gates, "candidate_geometry"),
            gates.get("candidate_geometry", {}).get("value", "Geometry gate not evaluated."),
            "The detector already maps each candidate to a Jovian storm location.",
            "outputs/detection/geometry_input_inventory.csv",
            ".\\run.ps1 geometry-inputs; .\\run.ps1 geometry-acquisition; .\\run.ps1 research-gates",
            gates.get("candidate_geometry", {}).get("value", ""),
            "Acquire/document NAIF Cassini SPICE kernels and ISS camera model assumptions before location claims.",
        ),
        claim(
            "C06",
            "Spectrum",
            "Nearby filter context is a follow-up queue, not a color/spectrum result.",
            status_from_gate(gates, "nearby_filter_followup"),
            f"The workflow has {gates.get('nearby_filter_followup', {}).get('value', '0')} nearby non-HAL context rows for follow-up review after candidate validation.",
            "The project measured the color spectrum of new lightning events.",
            "outputs/detection/nearby_filter_context.csv",
            ".\\run.ps1 filters; .\\run.ps1 research-gates",
            f"{gates.get('nearby_filter_followup', {}).get('value', '0')} nearby context rows",
            "Use nearby-filter products only after candidates survive human, temporal, and geometry review.",
        ),
        claim(
            "C07",
            "Modeling",
            "YOLO or learned-model comparison is not ready until reviewed labels exist.",
            status_from_gate(gates, "model_training_readiness"),
            gates.get("model_training_readiness", {}).get("value", "Model readiness not evaluated."),
            "YOLO has been trained and outperforms the classical detector.",
            "outputs/detection/training_readiness.csv",
            ".\\run.ps1 training-readiness; .\\run.ps1 research-gates",
            gates.get("model_training_readiness", {}).get("value", ""),
            "Create at least 6 positive and 20 negative high-confidence reviewed labels with notes.",
        ),
        claim(
            "C08",
            "Limitations",
            "No new Jovian lightning discovery is confirmed by the current output alone.",
            "supported",
            "Unmatched candidates are review targets until human, temporal, and geometry checks support a stronger claim.",
            "The pipeline discovered new lightning.",
            "outputs/detection/research_gate_audit.csv",
            ".\\run.ps1 research-gates; .\\run.ps1 claim-audit",
            f"{totals['unmatched_review_candidates']} unmatched review candidates",
            "Manually review and validate candidates before moving any unmatched row into a discovery table.",
        ),
    ]
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[str(row["status"])] = status_counts.get(str(row["status"]), 0) + 1
    lines = [
        "# Manuscript Claim Matrix",
        "",
        "This generated matrix keeps paper-facing language tied to current evidence. It is meant to stop accidental overclaiming while still making the useful results easy to state.",
        "",
        "## Summary",
        "",
        f"- Supported claims: {status_counts.get('supported', 0)}",
        f"- Limited claims: {status_counts.get('limited', 0)}",
        f"- Not-supported claims: {status_counts.get('not_supported', 0)}",
        "",
        "## Claim Table",
        "",
        "| ID | Section | Status | Safe wording | Evidence | Proof command |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['claim_id']}` | {row['paper_section']} | `{row['status']}` | {row['safe_wording']} | "
            f"`{row['evidence_file']}` | `{row['proof_command']}` |"
        )
    lines.extend([
        "",
        "## Unsafe Wording To Avoid",
        "",
        "| ID | Do not say | Why not |",
        "|---|---|---|",
    ])
    for row in rows:
        lines.append(f"| `{row['claim_id']}` | {row['unsafe_wording']} | {row['remaining_work']} |")
    lines.extend([
        "",
        "## Safe Bottom Line",
        "",
        "The current project supports a reproducible detector and review workflow that recovers published validation marks. It does not yet support a confirmed new-lightning, Jovian-location, spectrum, or trained-model claim.",
    ])
    CLAIM_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_claim_rows()
    write_csv(CLAIM_CSV, rows, FIELDS)
    write_report(rows)
    print(f"Wrote {CLAIM_CSV}")
    print(f"Wrote {CLAIM_MD}")


if __name__ == "__main__":
    main()
