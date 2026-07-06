from __future__ import annotations

import csv
from pathlib import Path

import label_tools


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
SESSIONS_DIR = OUTPUT_DIR / "review_sessions"
SESSION_PLAN_CSV = OUTPUT_DIR / "review_session_plan.csv"
AUDIT_CSV = OUTPUT_DIR / "review_session_audit.csv"
AUDIT_MD = OUTPUT_DIR / "review_session_audit.md"


AUDIT_FIELDS = [
    "session_id",
    "review_batch",
    "candidate_count",
    "filled_labels",
    "valid_labels",
    "invalid_labels",
    "missing_confidence",
    "invalid_confidence",
    "missing_reviewer",
    "missing_review_note",
    "needs_second_review",
    "import_ready_rows",
    "training_ready_rows",
    "session_status",
    "next_action",
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


def session_files() -> list[Path]:
    if not SESSIONS_DIR.exists():
        return []
    return sorted(SESSIONS_DIR.glob("S*.csv"))


def row_label(row: dict[str, str]) -> str:
    return str(row.get("human_label", "")).strip()


def row_confidence(row: dict[str, str]) -> str:
    return str(row.get("confidence", "")).strip()


def has_note(row: dict[str, str]) -> bool:
    return bool(str(row.get("review_note", "")).strip())


def has_reviewer(row: dict[str, str]) -> bool:
    return bool(str(row.get("reviewer", "")).strip())


def is_valid_label(row: dict[str, str]) -> bool:
    label = row_label(row)
    return bool(label) and label in label_tools.VALID_LABELS


def is_valid_confidence(row: dict[str, str]) -> bool:
    confidence = row_confidence(row)
    return bool(confidence) and confidence in label_tools.VALID_CONFIDENCE


def is_import_ready(row: dict[str, str]) -> bool:
    return is_valid_label(row) and is_valid_confidence(row) and has_reviewer(row) and has_note(row)


def is_training_ready(row: dict[str, str]) -> bool:
    return is_import_ready(row) and row_confidence(row) == "high" and not label_tools.truthy(row.get("needs_second_review"))


def status_for(
    candidate_count: int,
    filled_labels: int,
    invalid_labels: int,
    missing_confidence: int,
    missing_reviewer: int,
    missing_review_note: int,
) -> str:
    if candidate_count == 0:
        return "missing_session_rows"
    if filled_labels == 0:
        return "not_started"
    if invalid_labels or missing_confidence or missing_reviewer or missing_review_note:
        return "needs_cleanup"
    if filled_labels < candidate_count:
        return "partial_review"
    return "import_ready"


def next_action_for(status: str, session_id: str) -> str:
    if status == "not_started":
        return f"Open outputs/detection/review_sessions/{session_id}.csv and fill reviewer labels."
    if status == "needs_cleanup":
        return "Fix invalid labels or missing confidence, reviewer, and review_note fields before importing."
    if status == "partial_review":
        return "Finish remaining unlabeled rows, then import the completed session CSV."
    if status == "import_ready":
        return f"Import with .\\run.ps1 label-import -LabelCsv outputs\\detection\\review_sessions\\{session_id}.csv"
    return "Regenerate review sessions with .\\run.ps1 review-sessions."


def build_audit_rows() -> list[dict[str, object]]:
    plan = {row.get("session_id", ""): row for row in read_csv(SESSION_PLAN_CSV)}
    rows: list[dict[str, object]] = []
    for path in session_files():
        session_rows = read_csv(path)
        session_id = path.stem
        plan_row = plan.get(session_id, {})
        candidate_count = len(session_rows)
        filled_labels = sum(1 for row in session_rows if row_label(row))
        valid_labels = sum(1 for row in session_rows if is_valid_label(row))
        invalid_labels = sum(1 for row in session_rows if row_label(row) and not is_valid_label(row))
        missing_confidence = sum(1 for row in session_rows if row_label(row) and not row_confidence(row))
        invalid_confidence = sum(1 for row in session_rows if row_confidence(row) and not is_valid_confidence(row))
        missing_reviewer = sum(1 for row in session_rows if row_label(row) and not has_reviewer(row))
        missing_review_note = sum(1 for row in session_rows if row_label(row) and not has_note(row))
        needs_second_review = sum(1 for row in session_rows if label_tools.truthy(row.get("needs_second_review")))
        import_ready_rows = sum(1 for row in session_rows if is_import_ready(row))
        training_ready_rows = sum(1 for row in session_rows if is_training_ready(row))
        status = status_for(
            candidate_count,
            filled_labels,
            invalid_labels + invalid_confidence,
            missing_confidence,
            missing_reviewer,
            missing_review_note,
        )
        rows.append({
            "session_id": session_id,
            "review_batch": plan_row.get("review_batch") or (session_rows[0].get("review_batch", "") if session_rows else ""),
            "candidate_count": candidate_count,
            "filled_labels": filled_labels,
            "valid_labels": valid_labels,
            "invalid_labels": invalid_labels,
            "missing_confidence": missing_confidence,
            "invalid_confidence": invalid_confidence,
            "missing_reviewer": missing_reviewer,
            "missing_review_note": missing_review_note,
            "needs_second_review": needs_second_review,
            "import_ready_rows": import_ready_rows,
            "training_ready_rows": training_ready_rows,
            "session_status": status,
            "next_action": next_action_for(status, session_id),
        })
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    total_sessions = len(rows)
    total_candidates = sum(int(row["candidate_count"]) for row in rows)
    filled = sum(int(row["filled_labels"]) for row in rows)
    import_ready = sum(1 for row in rows if row["session_status"] == "import_ready")
    not_started = sum(1 for row in rows if row["session_status"] == "not_started")
    lines = [
        "# Review Session Audit",
        "",
        "This audit checks whether the generated review-session CSVs have enough human-review information to import safely. It does not create labels and it does not judge lightning by itself.",
        "",
        "## Summary",
        "",
        f"- Sessions found: {total_sessions}",
        f"- Candidate rows across sessions: {total_candidates}",
        f"- Filled human labels: {filled}",
        f"- Import-ready sessions: {import_ready}",
        f"- Not-started sessions: {not_started}",
        "",
        "## Required For Import",
        "",
        "A reviewed row should have a valid `human_label`, valid `confidence`, `reviewer`, and `review_note`. Training-ready rows must also be high confidence and not marked as needing second review.",
        "",
        "## Sessions",
        "",
        "| Session | Batch | Status | Rows | Filled | Import-ready rows | Training-ready rows | Next action |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['session_id']}` | `{row['review_batch']}` | `{row['session_status']}` | "
            f"{row['candidate_count']} | {row['filled_labels']} | {row['import_ready_rows']} | "
            f"{row['training_ready_rows']} | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Safe Interpretation",
        "",
        "A session marked `import_ready` can be imported into the label store. It still does not confirm new lightning unless the resulting labels, temporal evidence, geometry, and scientific review support that claim.",
    ])
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_audit_rows()
    write_csv(AUDIT_CSV, rows, AUDIT_FIELDS)
    write_report(rows)
    print(f"Wrote {AUDIT_CSV}")
    print(f"Wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
