from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
SUMMARY_CSV = OUTPUT_DIR / "processed_date_coverage_summary.csv"
SUMMARY_MD = OUTPUT_DIR / "processed_date_coverage_summary.md"


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


def to_int(value: str) -> int:
    if value == "":
        return 0
    return int(float(value))


def build_summary_rows() -> list[dict[str, object]]:
    detection = {row["run_date"]: row for row in read_csv(OUTPUT_DIR / "detection_summary.csv")}
    coverage = {row["date"]: row for row in read_csv(OUTPUT_DIR / "opus_nearby_date_coverage.csv")}
    rows: list[dict[str, object]] = []
    for run_date in sorted(detection):
        det = detection[run_date]
        cov = coverage.get(run_date, {})
        matches = to_int(det.get("published_matches", "0"))
        unmatched = to_int(det.get("unmatched_review_candidates", "0"))
        review_candidates = to_int(det.get("review_candidates", "0"))
        if matches:
            interpretation = "published validation date"
        elif review_candidates:
            interpretation = "screened date with review candidates, not confirmed lightning"
        else:
            interpretation = "screened date with no review candidates"
        rows.append({
            "run_date": run_date,
            "opus_available_frames": cov.get("available_frames", ""),
            "exposure_durations_seconds": str(cov.get("duration_seconds", "")).replace("|", ", "),
            "images_processed": det.get("images_processed", ""),
            "candidates_found": det.get("candidates_found", ""),
            "review_candidates": review_candidates,
            "published_matches": matches,
            "unmatched_review_candidates": unmatched,
            "interpretation": interpretation,
        })
    return rows


def write_markdown(rows: list[dict[str, object]]) -> None:
    total_images = sum(to_int(str(row["images_processed"])) for row in rows)
    total_review = sum(int(row["review_candidates"]) for row in rows)
    total_matches = sum(int(row["published_matches"]) for row in rows)
    total_unmatched = sum(int(row["unmatched_review_candidates"]) for row in rows)
    lines = [
        "# Processed Date Coverage Summary",
        "",
        "This is the meeting-friendly view of what dates have actually been processed. It summarizes detector outputs; it does not turn unmatched candidates into discoveries.",
        "",
        "## Totals",
        "",
        f"- Processed date windows: {len(rows)}",
        f"- Images processed: {total_images}",
        f"- Review candidates after artifact filters: {total_review}",
        f"- Published validation matches recovered: {total_matches}",
        f"- Unmatched review candidates kept for review: {total_unmatched}",
        "",
        "## Date Table",
        "",
        "| Date | OPUS frames | Durations | Images processed | Review candidates | Published matches | Unmatched review | Interpretation |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['run_date']} | {row['opus_available_frames']} | {row['exposure_durations_seconds']} | "
            f"{row['images_processed']} | {row['review_candidates']} | {row['published_matches']} | "
            f"{row['unmatched_review_candidates']} | {row['interpretation']} |"
        )
    lines.extend([
        "",
        "## Safe Meeting Language",
        "",
        "I processed nine Cassini ISS NAC/H-alpha date windows around the Jupiter flyby, totaling 221 images. The detector recovers the six published validation marks across Jan 1, Jan 10, and Jan 11. It also keeps unmatched candidates for review, but those are not new lightning claims until human review, temporal behavior, and geometry checks support them.",
    ])
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_summary_rows()
    write_csv(
        SUMMARY_CSV,
        rows,
        [
            "run_date",
            "opus_available_frames",
            "exposure_durations_seconds",
            "images_processed",
            "candidates_found",
            "review_candidates",
            "published_matches",
            "unmatched_review_candidates",
            "interpretation",
        ],
    )
    write_markdown(rows)
    print(f"Wrote {SUMMARY_CSV}")
    print(f"Wrote {SUMMARY_MD}")


if __name__ == "__main__":
    main()
