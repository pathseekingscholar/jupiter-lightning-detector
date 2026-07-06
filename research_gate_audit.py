from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
GATE_CSV = OUTPUT_DIR / "research_gate_audit.csv"
GATE_MD = OUTPUT_DIR / "research_gate_audit.md"


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


def summary_value(rows: list[dict[str, str]], item: str) -> float:
    for row in rows:
        if row.get("summary_item") == item or row.get("audit_item") == item:
            return numeric(row.get("count") or row.get("value"))
    return 0.0


def row_by_key(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def build_gate_audit() -> list[dict[str, object]]:
    detection = read_csv(OUTPUT_DIR / "detection_summary.csv")
    known = read_csv(OUTPUT_DIR / "known_match_report.csv")
    label_summary = read_csv(OUTPUT_DIR / "candidate_label_summary.csv")
    human_audit = read_csv(OUTPUT_DIR / "human_review_audit.csv")
    claim_audit = read_csv(OUTPUT_DIR / "doc_claim_audit.csv")
    geometry = read_csv(OUTPUT_DIR / "geometry_readiness.csv")
    filter_context = read_csv(OUTPUT_DIR / "nearby_filter_context.csv")
    review_plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    training_readiness = read_csv(OUTPUT_DIR / "training_readiness.csv")
    evidence_integrity = read_csv(OUTPUT_DIR / "evidence_integrity_audit.csv")

    images_processed = sum(int(numeric(row.get("images_processed"))) for row in detection)
    published_matches = sum(int(numeric(row.get("published_matches"))) for row in detection)
    known_recovered = sum(1 for row in known if row.get("recovered_within_8_px") == "yes")
    positive_labels = summary_value(label_summary, "group_positive")
    negative_labels = summary_value(label_summary, "group_negative")
    total_labels = summary_value(label_summary, "total_labels")
    unsafe_claims = sum(1 for row in claim_audit if row.get("severity") == "unsafe" and row.get("status") == "review")
    image_level_bounds = sum(1 for row in geometry if row.get("latitude_min") and row.get("longitude_w_min"))
    candidate_map_ready = sum(
        1 for row in geometry
        if row.get("candidate_latlon_ready") == "yes"
        and "per-candidate mapping still needs" not in row.get("readiness_note", "")
    )
    context_rows = sum(1 for row in filter_context if row.get("context_status") == "nearby_non_hal_context")
    review_rows = len(review_plan)
    model_gate = row_by_key(training_readiness, "gate", "model_comparison_allowed")
    model_status = model_gate.get("status", "not_ready")
    model_value = model_gate.get("value", "not evaluated")
    model_next_action = model_gate.get("next_action", "Generate training readiness and finish human labels before model comparison.")
    integrity_not_ready = sum(1 for row in evidence_integrity if row.get("status") == "not_ready")
    integrity_in_progress = sum(1 for row in evidence_integrity if row.get("status") == "in_progress")
    integrity_ready = sum(1 for row in evidence_integrity if row.get("status") == "ready")
    if integrity_not_ready:
        integrity_status = "not_ready"
    elif integrity_in_progress:
        integrity_status = "in_progress"
    elif integrity_ready:
        integrity_status = "ready"
    else:
        integrity_status = "not_ready"

    published_human_value = ""
    for row in human_audit:
        if row.get("audit_item") == "published_validation_marks_labeled":
            published_human_value = row.get("value", "")

    return [
        gate(
            "data_processed",
            "ready" if images_processed >= 221 else "not_ready",
            images_processed,
            "outputs/detection/detection_summary.csv",
            "Detector outputs exist for the current 221-image processed set.",
            "Regenerate detector outputs if this drops below the expected processed-image count.",
        ),
        gate(
            "published_match_recovery",
            "ready" if published_matches == 6 and known_recovered == 6 else "not_ready",
            f"{known_recovered} of 6",
            "outputs/detection/known_match_report.csv",
            "The detector recovers the published validation marks in the generated outputs.",
            "Do not tune thresholds in a way that loses known validation marks.",
        ),
        gate(
            "first_pass_review_queue",
            "ready" if review_rows == 106 else "not_ready",
            review_rows,
            "outputs/detection/first_pass_review_plan.csv",
            "A manageable first-pass human-review queue exists.",
            "Regenerate review-plan exports and preserve every curated candidate.",
        ),
        gate(
            "human_positive_labels",
            "not_ready" if positive_labels < 6 else "ready",
            int(positive_labels),
            "outputs/detection/candidate_label_summary.csv",
            "Positive labels are needed before training or claiming reviewed positives.",
            "Label the six published validation matches first.",
        ),
        gate(
            "human_negative_labels",
            "not_ready" if negative_labels < 20 else "ready",
            int(negative_labels),
            "outputs/detection/candidate_label_summary.csv",
            "Negative labels are needed for false-positive analysis and later model comparison.",
            "Label at least 20 clear artifacts or cosmic-ray/hot-pixel examples.",
        ),
        gate(
            "saved_human_labels",
            "not_ready" if total_labels == 0 else "in_progress",
            int(total_labels),
            "outputs/detection/candidate_labels.csv",
            "Saved labels convert detector candidates into review evidence.",
            "Use the workbench or CSV import to save labels with reviewer notes.",
        ),
        gate(
            "published_marks_human_confirmed",
            "not_ready" if published_human_value != "6 of 6" else "ready",
            published_human_value or "0 of 6",
            "outputs/detection/human_review_audit.csv",
            "Published matches should be explicitly confirmed by human labels.",
            "Mark the six validation candidates as known-lightning after visual check.",
        ),
        gate(
            "documentation_claim_safety",
            "ready" if unsafe_claims == 0 else "not_ready",
            unsafe_claims,
            "outputs/detection/doc_claim_audit.csv",
            "Project-facing docs should not overclaim unsupported discoveries.",
            "Fix any unsafe claim-audit rows before presenting or publishing.",
        ),
        gate(
            "nearby_filter_followup",
            "in_progress" if context_rows > 0 else "not_ready",
            context_rows,
            "outputs/detection/nearby_filter_context.csv",
            "Nearby non-HAL context exists for follow-up color/spectrum review.",
            "Use this only after candidates survive human and temporal validation.",
        ),
        gate(
            "candidate_geometry",
            "ready" if candidate_map_ready > 0 else "not_ready",
            f"{image_level_bounds} image-bound rows; {candidate_map_ready} candidate maps",
            "outputs/detection/geometry_readiness.csv",
            "Image-level latitude/longitude bounds exist for some rows, but candidate-level x/y-to-Jupiter mapping is not ready yet.",
            "Add navigation/geometry mapping before making location-based storm claims.",
        ),
        gate(
            "model_training_readiness",
            "ready" if model_status == "ready" else "not_ready",
            model_value,
            "outputs/detection/training_readiness.csv",
            "Learned detector comparison is allowed only after human-confirmed positives, negatives, notes, and confidence fields exist.",
            model_next_action,
        ),
        gate(
            "evidence_integrity",
            integrity_status,
            f"{integrity_ready} ready; {integrity_in_progress} in progress; {integrity_not_ready} not ready",
            "outputs/detection/evidence_integrity_audit.csv",
            "Reviewer-facing evidence files should be internally consistent before review or presentation.",
            "Fix any not-ready evidence-integrity checks before relying on the review packet.",
        ),
    ]


def gate(
    name: str,
    status: str,
    value: object,
    evidence_file: str,
    interpretation: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "gate": name,
        "status": status,
        "value": value,
        "evidence_file": evidence_file,
        "interpretation": interpretation,
        "next_action": next_action,
    }


def write_report(rows: list[dict[str, object]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["status"])] = counts.get(str(row["status"]), 0) + 1
    lines = [
        "# Research Gate Audit",
        "",
        "This report summarizes what is ready for scientific use and what still blocks stronger claims. It is generated from current output files, not from memory.",
        "",
        "## Summary",
        "",
        f"- Ready gates: {counts.get('ready', 0)}",
        f"- In-progress gates: {counts.get('in_progress', 0)}",
        f"- Not-ready gates: {counts.get('not_ready', 0)}",
        "",
        "## Gates",
        "",
        "| Gate | Status | Value | Evidence | Interpretation | Next action |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate']}` | `{row['status']}` | {row['value']} | `{row['evidence_file']}` | {row['interpretation']} | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Safe Conclusion",
        "",
        "The detector/review workflow is reproducible and validation-oriented. It is not yet a confirmed new-lightning discovery workflow because human labels, negative examples, and candidate-level geometry remain incomplete.",
    ])
    GATE_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_gate_audit()
    write_csv(GATE_CSV, rows, ["gate", "status", "value", "evidence_file", "interpretation", "next_action"])
    write_report(rows)
    print(f"Wrote {GATE_CSV}")
    print(f"Wrote {GATE_MD}")


if __name__ == "__main__":
    main()
