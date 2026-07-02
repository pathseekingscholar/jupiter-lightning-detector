from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import detection_pipeline as detector


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
KNOWN_EVENTS = ROOT / "known_events.json"
LABELS_JSON = OUTPUT_DIR / "candidate_labels.json"


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


def local_paths_for_image(image_number: str) -> tuple[str, str, str]:
    image_path, label_path = detector.jp.image_paths_for_number(image_number)
    previews = sorted(detector.jp.PREVIEWS.glob(f"N{image_number}_*_full.png"))
    preview = previews[0] if previews else detector.jp.PREVIEWS / f"N{image_number}_2_full.png"
    return (
        str(image_path.relative_to(ROOT)) if image_path.exists() else "",
        str(label_path.relative_to(ROOT)) if label_path.exists() else "",
        str(preview.relative_to(ROOT)) if preview.exists() else "",
    )


def known_recovery_ids(candidates: list[dict[str, str]]) -> set[str]:
    if not KNOWN_EVENTS.exists():
        return set()
    known = json.loads(KNOWN_EVENTS.read_text(encoding="utf-8"))
    recovered = set()
    by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        by_image[row.get("image_number", "")].append(row)
    for observation in known["observations"]:
        image_rows = by_image.get(observation["image_number"], [])
        for event in observation["events"]:
            if not image_rows:
                continue
            best = min(
                image_rows,
                key=lambda row: math.hypot(float(row["x"]) - event["x"], float(row["y"]) - event["y"]),
            )
            distance = math.hypot(float(best["x"]) - event["x"], float(best["y"]) - event["y"])
            if distance <= 8.0:
                recovered.add(best["candidate_id"])
    return recovered


def build_dataset_manifest() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run_date in detector.DETECTION_RUNS:
        sequence = detector.load_sequence(run_date)
        candidates = read_csv(OUTPUT_DIR / run_date / "candidates.csv")
        review = read_csv(OUTPUT_DIR / run_date / "review_candidates.csv")
        candidate_counts = Counter(row["image_number"] for row in candidates)
        review_counts = Counter(row["image_number"] for row in review)
        for frame_index, item in enumerate(sequence):
            image_path, label_path, preview_path = local_paths_for_image(item["image_number"])
            rows.append({
                "run_date": run_date,
                "run_label": detector.DETECTION_RUNS[run_date]["label"],
                "frame_index": frame_index,
                "opus_id": item["opus_id"],
                "image_id": f"N{item['image_number']}",
                "image_number": item["image_number"],
                "time": item["time"],
                "duration_seconds": item.get("duration_seconds", ""),
                "camera": item.get("camera", ""),
                "filter": item.get("filter", ""),
                "center_resolution_km_px": item.get("center_resolution_km_px", ""),
                "candidate_count": candidate_counts[item["image_number"]],
                "review_candidate_count": review_counts[item["image_number"]],
                "calibrated_image": image_path,
                "calibrated_label": label_path,
                "preview_image": preview_path,
            })
    return rows


def build_detection_summary() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run_date in detector.DETECTION_RUNS:
        summary_path = OUTPUT_DIR / run_date / "summary.json"
        candidates = read_csv(OUTPUT_DIR / run_date / "candidates.csv")
        review = read_csv(OUTPUT_DIR / run_date / "review_candidates.csv")
        summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
        recovered = known_recovery_ids(candidates)
        rows.append({
            "run_date": run_date,
            "run_label": detector.DETECTION_RUNS[run_date]["label"],
            "images_processed": summary.get("frames", 0),
            "candidates_found": summary.get("candidates", len(candidates)),
            "review_candidates": summary.get("review_candidates", len(review)),
            "rejected_or_artifact_flagged": max(0, int(summary.get("candidates", len(candidates))) - int(summary.get("review_candidates", len(review)))),
            "tracks": summary.get("tracks", ""),
            "published_matches": len(recovered),
            "unmatched_review_candidates": max(0, len(review) - len(recovered)),
        })
    return rows


def build_label_summary() -> list[dict[str, object]]:
    if not LABELS_JSON.exists():
        return []
    payload = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    rows = list(payload.get("labels", {}).values())
    rows.sort(key=lambda row: (row.get("human_label", ""), row.get("run_date", ""), row.get("candidate_id", "")))
    return rows


def main() -> None:
    manifest = build_dataset_manifest()
    write_csv(
        OUTPUT_DIR / "dataset_manifest.csv",
        manifest,
        [
            "run_date",
            "run_label",
            "frame_index",
            "opus_id",
            "image_id",
            "image_number",
            "time",
            "duration_seconds",
            "camera",
            "filter",
            "center_resolution_km_px",
            "candidate_count",
            "review_candidate_count",
            "calibrated_image",
            "calibrated_label",
            "preview_image",
        ],
    )

    summary = build_detection_summary()
    write_csv(
        OUTPUT_DIR / "detection_summary.csv",
        summary,
        [
            "run_date",
            "run_label",
            "images_processed",
            "candidates_found",
            "review_candidates",
            "rejected_or_artifact_flagged",
            "tracks",
            "published_matches",
            "unmatched_review_candidates",
        ],
    )

    labels = build_label_summary()
    if labels:
        write_csv(
            OUTPUT_DIR / "candidate_labels_grouped.csv",
            labels,
            [
                "run_date",
                "candidate_id",
                "image_id",
                "image_number",
                "x",
                "y",
                "brightness",
                "blob_size",
                "snr",
                "artifact_flags",
                "candidate_score",
                "human_label",
                "review_note",
                "updated_at",
            ],
        )
    print(f"Wrote {OUTPUT_DIR / 'dataset_manifest.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'detection_summary.csv'}")
    if labels:
        print(f"Wrote {OUTPUT_DIR / 'candidate_labels_grouped.csv'}")


if __name__ == "__main__":
    main()
