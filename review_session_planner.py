from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PLAN_CSV = OUTPUT_DIR / "first_pass_review_plan.csv"
SESSIONS_DIR = OUTPUT_DIR / "review_sessions"
SESSION_PLAN_CSV = OUTPUT_DIR / "review_session_plan.csv"
SESSION_PLAN_MD = OUTPUT_DIR / "review_session_plan.md"


SESSION_LIMITS = {
    "01_known_validation_positive": 6,
    "02_temporal_persistence_check": 10,
    "03_negative_artifact_examples": 10,
    "04_strong_single_frame_check": 10,
    "05_low_priority_hold": 15,
}


SESSION_FIELDS = [
    "session_id",
    "session_order",
    "session_row",
    "review_batch",
    "candidate_id",
    "image_id",
    "run_date",
    "x",
    "y",
    "crop_url",
    "suggested_human_label",
    "reviewer_task",
    "snr",
    "blob_size",
    "artifact_flags",
    "frame_count",
    "motion_consistency",
    "candidate_score",
    "review_note_prompt",
    "human_label",
    "confidence",
    "reviewer",
    "review_note",
    "review_stage",
    "needs_second_review",
    "reviewed_at",
]


SUMMARY_FIELDS = [
    "session_id",
    "session_order",
    "review_batch",
    "candidate_count",
    "candidate_ids",
    "output_csv",
    "review_goal",
    "allowed_labels",
    "pass_condition",
    "training_use",
    "status",
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


def batch_instructions(batch: str) -> dict[str, str]:
    return {
        "01_known_validation_positive": {
            "review_goal": "Confirm the published validation matches first.",
            "allowed_labels": "known-lightning, uncertain",
            "pass_condition": "Every row has reviewer, confidence, note, and visual confirmation or uncertainty reason.",
            "training_use": "Positive validation only after human confirmation.",
        },
        "02_temporal_persistence_check": {
            "review_goal": "Decide whether repeated candidates look physically plausible across frames.",
            "allowed_labels": "possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain",
            "pass_condition": "Every note mentions repeat behavior, motion, or why temporal evidence is weak.",
            "training_use": "Hold as possible positives until second review or geometry support exists.",
        },
        "03_negative_artifact_examples": {
            "review_goal": "Collect clear artifact and cosmic-ray/hot-pixel negatives.",
            "allowed_labels": "artifact, cosmic-ray-hot-pixel, uncertain",
            "pass_condition": "At least 20 high-confidence negative labels across negative sessions.",
            "training_use": "Negative examples if high confidence and note explains artifact reason.",
        },
        "04_strong_single_frame_check": {
            "review_goal": "Inspect strong one-frame detections without calling them discoveries.",
            "allowed_labels": "possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain",
            "pass_condition": "Each note explains diffuse/multi-pixel evidence or why the row should stay uncertain.",
            "training_use": "Do not use for positive training unless second review agrees.",
        },
        "05_low_priority_hold": {
            "review_goal": "Preserve lower-priority rows for later review.",
            "allowed_labels": "artifact, cosmic-ray-hot-pixel, uncertain",
            "pass_condition": "No scientific claim is made from this session alone.",
            "training_use": "Not for first training pass unless explicitly reviewed.",
        },
    }.get(batch, {
        "review_goal": "Review candidate carefully.",
        "allowed_labels": "known-lightning, possible-lightning, artifact, cosmic-ray-hot-pixel, uncertain",
        "pass_condition": "Reviewer records label, confidence, and note.",
        "training_use": "Requires human note before use.",
    })


def build_session_rows() -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]]]:
    plan_rows = read_csv(PLAN_CSV)
    by_batch: dict[str, list[dict[str, str]]] = {}
    for row in plan_rows:
        by_batch.setdefault(row.get("review_batch", "05_low_priority_hold"), []).append(row)

    session_summaries: list[dict[str, object]] = []
    session_files: dict[str, list[dict[str, object]]] = {}
    session_order = 1

    for batch in sorted(by_batch):
        rows = sorted(by_batch[batch], key=lambda row: int(float(row.get("review_order", "999999") or 999999)))
        limit = SESSION_LIMITS.get(batch, 10)
        instructions = batch_instructions(batch)
        for chunk_index, start in enumerate(range(0, len(rows), limit), start=1):
            chunk = rows[start:start + limit]
            session_id = f"S{session_order:03d}_{batch}"
            output_csv = f"review_sessions/{session_id}.csv"
            session_file_rows = []
            for session_row, row in enumerate(chunk, start=1):
                session_file_rows.append({
                    "session_id": session_id,
                    "session_order": session_order,
                    "session_row": session_row,
                    "review_batch": batch,
                    "candidate_id": row.get("candidate_id", ""),
                    "image_id": row.get("image_id", ""),
                    "run_date": row.get("run_date", ""),
                    "x": row.get("x", ""),
                    "y": row.get("y", ""),
                    "crop_url": row.get("crop_url", ""),
                    "suggested_human_label": row.get("suggested_human_label", ""),
                    "reviewer_task": row.get("reviewer_task", ""),
                    "snr": row.get("snr", ""),
                    "blob_size": row.get("blob_size", ""),
                    "artifact_flags": row.get("artifact_flags", ""),
                    "frame_count": row.get("frame_count", ""),
                    "motion_consistency": row.get("motion_consistency", ""),
                    "candidate_score": row.get("candidate_score", ""),
                    "review_note_prompt": row.get("review_note_prompt", ""),
                    "human_label": "",
                    "confidence": "",
                    "reviewer": "",
                    "review_note": "",
                    "review_stage": "first-review",
                    "needs_second_review": "",
                    "reviewed_at": "",
                })
            session_files[session_id] = session_file_rows
            session_summaries.append({
                "session_id": session_id,
                "session_order": session_order,
                "review_batch": batch,
                "candidate_count": len(chunk),
                "candidate_ids": "|".join(row.get("candidate_id", "") for row in chunk),
                "output_csv": output_csv,
                "review_goal": instructions["review_goal"],
                "allowed_labels": instructions["allowed_labels"],
                "pass_condition": instructions["pass_condition"],
                "training_use": instructions["training_use"],
                "status": "ready_for_human_review",
            })
            session_order += 1
    return session_summaries, session_files


def write_session_files(session_files: dict[str, list[dict[str, object]]]) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    for old_path in SESSIONS_DIR.glob("S*.csv"):
        old_path.unlink()
    for session_id, rows in session_files.items():
        write_csv(SESSIONS_DIR / f"{session_id}.csv", rows, SESSION_FIELDS)


def write_report(session_summaries: list[dict[str, object]]) -> None:
    by_batch = Counter(row["review_batch"] for row in session_summaries)
    total_candidates = sum(int(row["candidate_count"]) for row in session_summaries)
    lines = [
        "# Review Session Plan",
        "",
        "This turns the first-pass review queue into small CSV packets that a reviewer can label in one sitting. It is a workflow artifact, not a discovery catalog.",
        "",
        "## How To Use",
        "",
        "1. Open the next session CSV in `outputs/detection/review_sessions/`.",
        "2. Inspect each crop and original context in the workbench.",
        "3. Fill `human_label`, `confidence`, `reviewer`, `review_note`, `needs_second_review`, and optionally `reviewed_at`.",
        "4. Import the completed CSV with `.\\run.ps1 label-import -LabelCsv outputs\\detection\\review_sessions\\SESSION_FILE.csv`.",
        "5. Regenerate label summaries with `.\\run.ps1 label-summary`, then rerun `.\\run.ps1 training-readiness`.",
        "",
        "## Summary",
        "",
        f"- Review sessions: {len(session_summaries)}",
        f"- Candidates assigned to sessions: {total_candidates}",
        "",
        "| Batch | Sessions | Purpose |",
        "|---|---:|---|",
    ]
    for batch, count in sorted(by_batch.items()):
        lines.append(f"| `{batch}` | {count} | {batch_instructions(batch)['review_goal']} |")
    lines.extend([
        "",
        "## Sessions",
        "",
        "| Session | Rows | CSV | Allowed labels | Pass condition |",
        "|---|---:|---|---|---|",
    ])
    for row in session_summaries:
        lines.append(
            f"| `{row['session_id']}` | {row['candidate_count']} | `{row['output_csv']}` | "
            f"{row['allowed_labels']} | {row['pass_condition']} |"
        )
    lines.extend([
        "",
        "## Safe Interpretation",
        "",
        "A completed session creates human review evidence. It still does not confirm new lightning unless the labels, temporal behavior, geometry, and scientific review all support the claim.",
    ])
    SESSION_PLAN_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    session_summaries, session_files = build_session_rows()
    write_csv(SESSION_PLAN_CSV, session_summaries, SUMMARY_FIELDS)
    write_session_files(session_files)
    write_report(session_summaries)
    print(f"Wrote {SESSION_PLAN_CSV}")
    print(f"Wrote {SESSION_PLAN_MD}")
    print(f"Wrote {len(session_files)} review session CSVs in {SESSIONS_DIR}")


if __name__ == "__main__":
    main()
