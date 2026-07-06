from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PACKET_CSV = OUTPUT_DIR / "blind_review_packet.csv"
KEY_CSV = OUTPUT_DIR / "blind_review_key.csv"
PACKET_MD = OUTPUT_DIR / "blind_review_packet.md"


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


def blind_sort_key(candidate_id: str) -> str:
    return hashlib.sha256(f"jupiter-lightning-blind-review:{candidate_id}".encode("utf-8")).hexdigest()


def build_packet_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    sorted_rows = sorted(plan, key=lambda row: blind_sort_key(row.get("candidate_id", "")))
    packet_rows: list[dict[str, object]] = []
    key_rows: list[dict[str, object]] = []
    for index, row in enumerate(sorted_rows, start=1):
        blind_id = f"BR-{index:03d}"
        packet_rows.append({
            "blind_id": blind_id,
            "image_id": row.get("image_id", ""),
            "run_date": row.get("run_date", ""),
            "crop_url": row.get("crop_url", ""),
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "snr": row.get("snr", ""),
            "blob_size": row.get("blob_size", ""),
            "artifact_flags_visible": row.get("artifact_flags", ""),
            "frame_count": row.get("frame_count", ""),
            "motion_consistency": row.get("motion_consistency", ""),
            "reviewer_label": "",
            "reviewer_confidence": "",
            "reviewer_note": "",
            "needs_second_review": "",
        })
        key_rows.append({
            "blind_id": blind_id,
            "candidate_id": row.get("candidate_id", ""),
            "review_order": row.get("review_order", ""),
            "review_batch": row.get("review_batch", ""),
            "next_action": row.get("next_action", ""),
            "suggested_human_label": row.get("suggested_human_label", ""),
            "reviewer_task": row.get("reviewer_task", ""),
            "review_note_prompt": row.get("review_note_prompt", ""),
        })
    return packet_rows, key_rows


def write_report(packet_rows: list[dict[str, object]], key_rows: list[dict[str, object]]) -> None:
    batch_counts: dict[str, int] = {}
    for row in key_rows:
        batch = str(row.get("review_batch", ""))
        batch_counts[batch] = batch_counts.get(batch, 0) + 1

    lines = [
        "# Single-Blind Review Packet",
        "",
        "This packet lets a reviewer label candidates without seeing the detector's suggested label, review batch, or next action. It is single-blind, not double-blind: the candidate image/crop, coordinates, and measured detector numbers are still visible.",
        "",
        "## Files",
        "",
        "- Reviewer file: `outputs/detection/blind_review_packet.csv`",
        "- Answer key: `outputs/detection/blind_review_key.csv`",
        "",
        "## Review Rules",
        "",
        "- Do not open the answer key until the first-pass blind labels are finished.",
        "- Use `reviewer_label` values from the normal label set: `known-lightning`, `possible-lightning`, `artifact`, `cosmic-ray-hot-pixel`, or `uncertain`.",
        "- Use `reviewer_confidence`: `low`, `medium`, or `high`.",
        "- Write a short `reviewer_note` explaining the visual reason for the label.",
        "- Set `needs_second_review` to `yes` for ambiguous rows.",
        "",
        "## Packet Summary",
        "",
        f"- Blind rows: {len(packet_rows)}",
        f"- Answer-key rows: {len(key_rows)}",
        "",
        "| Hidden review batch | Rows |",
        "|---|---:|",
    ]
    for batch, count in sorted(batch_counts.items()):
        lines.append(f"| `{batch}` | {count} |")
    lines.extend([
        "",
        "## Why This Exists",
        "",
        "The normal review plan is efficient because it tells the reviewer which rows are published matches, likely artifacts, or temporal candidates. The blind packet is slower but less biased. It is useful when the project needs a cleaner estimate of human agreement, false positives, and whether detector categories are visually convincing.",
        "",
        "## After Review",
        "",
        "Join `blind_review_packet.csv` to `blind_review_key.csv` by `blind_id`, then compare reviewer labels against the hidden suggested labels and batches. Do not treat disagreement as failure automatically; disagreement is evidence that the candidate needs clearer criteria or second review.",
    ])
    PACKET_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    packet_rows, key_rows = build_packet_rows()
    write_csv(
        PACKET_CSV,
        packet_rows,
        [
            "blind_id",
            "image_id",
            "run_date",
            "crop_url",
            "x",
            "y",
            "snr",
            "blob_size",
            "artifact_flags_visible",
            "frame_count",
            "motion_consistency",
            "reviewer_label",
            "reviewer_confidence",
            "reviewer_note",
            "needs_second_review",
        ],
    )
    write_csv(
        KEY_CSV,
        key_rows,
        [
            "blind_id",
            "candidate_id",
            "review_order",
            "review_batch",
            "next_action",
            "suggested_human_label",
            "reviewer_task",
            "review_note_prompt",
        ],
    )
    write_report(packet_rows, key_rows)
    print(f"Wrote {PACKET_CSV}")
    print(f"Wrote {KEY_CSV}")
    print(f"Wrote {PACKET_MD}")


if __name__ == "__main__":
    main()
