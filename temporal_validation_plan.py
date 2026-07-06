from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
TRACK_QUALITY_CSV = OUTPUT_DIR / "temporal_track_quality.csv"
TRACK_SUMMARY_CSV = OUTPUT_DIR / "temporal_track_summary.csv"
GEOMETRY_INVENTORY_CSV = OUTPUT_DIR / "geometry_input_inventory.csv"
TEMPORAL_VALIDATION_CSV = OUTPUT_DIR / "temporal_validation_plan.csv"
TEMPORAL_VALIDATION_MD = OUTPUT_DIR / "temporal_validation_plan.md"


FIELDS = [
    "review_rank",
    "track_id",
    "run_date",
    "temporal_quality",
    "frame_count",
    "first_image_id",
    "last_image_id",
    "median_peak_snr",
    "mean_step_px",
    "motion_consistency",
    "candidate_score",
    "candidate_ids",
    "geometry_status",
    "review_priority",
    "review_questions",
    "possible_lightning_if",
    "likely_artifact_if",
    "required_next_evidence",
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


def track_summary_lookup() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row.get("run_date", ""), row.get("track_id", "")): row
        for row in read_csv(TRACK_SUMMARY_CSV)
    }


def geometry_status_by_image() -> dict[str, str]:
    status: dict[str, str] = {}
    for row in read_csv(GEOMETRY_INVENTORY_CSV):
        status[row.get("image_id", "")] = row.get("projection_input_status", "unknown")
    return status


def review_priority(row: dict[str, str]) -> str:
    quality = row.get("temporal_quality", "")
    frame_count = int(numeric(row.get("frame_count")))
    snr = numeric(row.get("median_peak_snr"))
    motion = numeric(row.get("motion_consistency"))
    if quality == "strong_temporal_review" and frame_count >= 3 and snr >= 20 and motion >= 0.8:
        return "A_top_temporal_review"
    if quality == "strong_temporal_review":
        return "B_strong_temporal_review"
    if quality == "moderate_temporal_review":
        return "C_moderate_temporal_review"
    return "D_hold"


def questions_for(row: dict[str, str]) -> str:
    return " | ".join([
        "Does the bright region appear in each listed frame?",
        "Is the motion direction and step size visually plausible?",
        "Is the source diffuse or multi-pixel rather than a single hot pixel?",
        "Does the crop avoid edges, line artifacts, and obvious streaks?",
        "Should this track receive second review before any positive label?",
    ])


def possible_if() -> str:
    return "Appears in 3+ frames, stays multi-pixel/diffuse, motion looks consistent, and no clear artifact explanation is found."


def artifact_if() -> str:
    return "Single-pixel/sharp events, streaks, edge effects, inconsistent jumps, repeated detector artifact shape, or no visual persistence."


def next_evidence(row: dict[str, str], geometry_status: str) -> str:
    if geometry_status != "projection_inputs_ready":
        return "Human temporal review first; candidate-level geometry still blocked by missing projection inputs."
    return "Human temporal review plus pixel-to-Jupiter projection check."


def build_plan_rows(limit: int = 120) -> list[dict[str, object]]:
    quality_rows = read_csv(TRACK_QUALITY_CSV)
    summaries = track_summary_lookup()
    geometry = geometry_status_by_image()
    candidates: list[dict[str, object]] = []
    for row in quality_rows:
        if row.get("temporal_quality") == "single_frame_not_temporal":
            continue
        summary = summaries.get((row.get("run_date", ""), row.get("track_id", "")), {})
        first_image = row.get("first_image_id", "")
        last_image = row.get("last_image_id", "")
        first_status = geometry.get(first_image, "unknown")
        last_status = geometry.get(last_image, "unknown")
        geometry_status = first_status if first_status == last_status else f"{first_status}|{last_status}"
        enriched = {
            "track_id": row.get("track_id", ""),
            "run_date": row.get("run_date", ""),
            "temporal_quality": row.get("temporal_quality", ""),
            "frame_count": row.get("frame_count", ""),
            "first_image_id": first_image,
            "last_image_id": last_image,
            "median_peak_snr": row.get("median_peak_snr", ""),
            "mean_step_px": row.get("mean_step_px", ""),
            "motion_consistency": row.get("motion_consistency", ""),
            "candidate_score": row.get("candidate_score", ""),
            "candidate_ids": row.get("candidate_ids", ""),
            "geometry_status": geometry_status,
            "review_priority": review_priority(row),
            "review_questions": questions_for(row),
            "possible_lightning_if": possible_if(),
            "likely_artifact_if": artifact_if(),
            "required_next_evidence": next_evidence(row, geometry_status),
            "_sort": (
                review_priority(row),
                -numeric(row.get("candidate_score")),
                -numeric(row.get("motion_consistency")),
                -numeric(row.get("median_peak_snr")),
            ),
            "_summary": summary,
        }
        candidates.append(enriched)
    candidates.sort(key=lambda row: row["_sort"])
    rows: list[dict[str, object]] = []
    for rank, row in enumerate(candidates[:limit], start=1):
        clean = {key: value for key, value in row.items() if not key.startswith("_")}
        clean["review_rank"] = rank
        rows.append(clean)
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["review_priority"]) for row in rows)
    quality_counts = Counter(str(row["temporal_quality"]) for row in rows)
    lines = [
        "# Temporal Validation Plan",
        "",
        "This plan turns temporal tracks into an explicit human-review checklist. It does not confirm lightning; it identifies repeated detections that deserve structured review.",
        "",
        "## Summary",
        "",
        f"- Tracks selected for temporal review: {len(rows)}",
    ]
    for priority, count in sorted(counts.items()):
        lines.append(f"- {priority}: {count}")
    lines.extend([
        "",
        "## Temporal Quality Mix",
        "",
        "| Temporal quality | Selected tracks |",
        "|---|---:|",
    ])
    for quality, count in sorted(quality_counts.items()):
        lines.append(f"| `{quality}` | {count} |")
    lines.extend([
        "",
        "## Review Rule",
        "",
        "A track becomes a possible lightning candidate only after human review confirms persistence, diffuse/multi-pixel appearance, plausible motion, and no obvious artifact explanation. Geometry remains a separate gate.",
        "",
        "## Selected Tracks",
        "",
        "| Rank | Track | Date | Priority | Frames | SNR | Motion | Geometry | Required next evidence |",
        "|---:|---|---|---|---:|---:|---:|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row['review_rank']} | `{row['track_id']}` | {row['run_date']} | `{row['review_priority']}` | "
            f"{row['frame_count']} | {row['median_peak_snr']} | {row['motion_consistency']} | "
            f"`{row['geometry_status']}` | {row['required_next_evidence']} |"
        )
    lines.extend([
        "",
        "## Questions For Every Track",
        "",
        "1. Does the bright region appear in each listed frame?",
        "2. Is the motion direction and step size visually plausible?",
        "3. Is the source diffuse or multi-pixel rather than a single hot pixel?",
        "4. Does the crop avoid edges, line artifacts, and obvious streaks?",
        "5. Should this track receive second review before any positive label?",
        "",
        "## Safe Interpretation",
        "",
        "Temporal persistence is stronger evidence than a single bright spot, but it is not enough by itself. Human review and geometry are still required before any new-lightning claim.",
    ])
    TEMPORAL_VALIDATION_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_plan_rows()
    write_csv(TEMPORAL_VALIDATION_CSV, rows, FIELDS)
    write_report(rows)
    print(f"Wrote {TEMPORAL_VALIDATION_CSV}")
    print(f"Wrote {TEMPORAL_VALIDATION_MD}")


if __name__ == "__main__":
    main()
