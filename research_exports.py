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
KNOWN_MATCH_RADIUS_PX = 8.0


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
            if distance <= KNOWN_MATCH_RADIUS_PX:
                recovered.add(best["candidate_id"])
    return recovered


def load_known_events() -> list[dict[str, object]]:
    if not KNOWN_EVENTS.exists():
        return []
    known = json.loads(KNOWN_EVENTS.read_text(encoding="utf-8"))
    rows = []
    for observation in known["observations"]:
        for event in observation["events"]:
            rows.append({
                "image_number": observation["image_number"],
                "image_id": f"N{observation['image_number']}",
                "label": event["label"],
                "published_x": float(event["x"]),
                "published_y": float(event["y"]),
                "published_power_w": event.get("published_power_w", ""),
                "source": known.get("source", ""),
            })
    return rows


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


def build_threshold_sweep() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    snr_thresholds = [7.0, 8.0, 10.0, 12.0, 15.0, 20.0]
    min_blob_sizes = [1, 3, 5, 8]
    for run_date in detector.DETECTION_RUNS:
        candidates = read_csv(OUTPUT_DIR / run_date / "candidates.csv")
        if not candidates:
            continue
        for snr_threshold in snr_thresholds:
            for min_blob_size in min_blob_sizes:
                passing = [
                    row for row in candidates
                    if float(row.get("peak_snr", row.get("brightness", 0)) or 0) >= snr_threshold
                    and int(float(row.get("blob_size", row.get("area_px", 0)) or 0)) >= min_blob_size
                ]
                reviewable = [row for row in passing if not row.get("flags", "")]
                recovered = known_recovery_ids(reviewable)
                rows.append({
                    "run_date": run_date,
                    "run_label": detector.DETECTION_RUNS[run_date]["label"],
                    "snr_threshold": snr_threshold,
                    "min_blob_size": min_blob_size,
                    "candidate_count": len(passing),
                    "review_candidate_count": len(reviewable),
                    "artifact_flagged_count": len(passing) - len(reviewable),
                    "published_matches": len(recovered),
                    "unmatched_review_candidates": max(0, len(reviewable) - len(recovered)),
                })
    return rows


def build_known_match_report() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    known_rows = load_known_events()
    all_candidates: list[dict[str, str]] = []
    for run_date in detector.DETECTION_RUNS:
        for row in read_csv(OUTPUT_DIR / run_date / "candidates.csv"):
            row["run_date"] = run_date
            all_candidates.append(row)

    by_image: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_candidates:
        by_image[row.get("image_number", "")].append(row)

    for known in known_rows:
        image_rows = by_image.get(str(known["image_number"]), [])
        best = None
        best_distance = None
        for row in image_rows:
            distance = math.hypot(
                float(row["x"]) - float(known["published_x"]),
                float(row["y"]) - float(known["published_y"]),
            )
            if best_distance is None or distance < best_distance:
                best = row
                best_distance = distance
        recovered = best is not None and best_distance is not None and best_distance <= KNOWN_MATCH_RADIUS_PX
        rows.append({
            "image_id": known["image_id"],
            "image_number": known["image_number"],
            "published_label": known["label"],
            "published_x": known["published_x"],
            "published_y": known["published_y"],
            "published_power_w": known["published_power_w"],
            "nearest_candidate_id": best.get("candidate_id", "") if best else "",
            "nearest_track_id": best.get("track_id", "") if best else "",
            "nearest_run_date": best.get("run_date", "") if best else "",
            "nearest_x": best.get("x", "") if best else "",
            "nearest_y": best.get("y", "") if best else "",
            "offset_px": f"{best_distance:.2f}" if best_distance is not None else "",
            "recovered_within_8_px": "yes" if recovered else "no",
            "nearest_peak_snr": best.get("peak_snr", "") if best else "",
            "nearest_blob_size": best.get("blob_size", best.get("area_px", "")) if best else "",
            "nearest_artifact_flags": best.get("flags", "") if best else "",
            "nearest_candidate_score": best.get("confidence", "") if best else "",
            "source": known["source"],
        })
    return rows


def build_temporal_track_summary() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run_date in detector.DETECTION_RUNS:
        review_rows = read_csv(OUTPUT_DIR / run_date / "review_candidates.csv")
        if not review_rows:
            continue
        by_track: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in review_rows:
            by_track[row["track_id"]].append(row)
        for track_id, track_rows in by_track.items():
            track_rows.sort(key=lambda row: int(row["frame_index"]))
            first = track_rows[0]
            last = track_rows[-1]
            x_values = [float(row["x"]) for row in track_rows]
            y_values = [float(row["y"]) for row in track_rows]
            snr_values = [float(row["peak_snr"]) for row in track_rows]
            rows.append({
                "run_date": run_date,
                "track_id": track_id,
                "frame_count": len(track_rows),
                "first_frame_index": first["frame_index"],
                "last_frame_index": last["frame_index"],
                "first_image_id": f"N{first['image_number']}",
                "last_image_id": f"N{last['image_number']}",
                "start_time": first["time"],
                "end_time": last["time"],
                "start_x": first["x"],
                "start_y": first["y"],
                "end_x": last["x"],
                "end_y": last["y"],
                "net_dx_px": f"{float(last['x']) - float(first['x']):.2f}",
                "net_dy_px": f"{float(last['y']) - float(first['y']):.2f}",
                "median_x": f"{float(np_median(x_values)):.2f}",
                "median_y": f"{float(np_median(y_values)):.2f}",
                "median_peak_snr": f"{float(np_median(snr_values)):.2f}",
                "candidate_score": first["confidence"],
                "reason": first["reason"],
                "candidate_ids": "|".join(row["candidate_id"] for row in track_rows),
            })
    rows.sort(key=lambda row: (row["run_date"], -float(row["candidate_score"]), row["track_id"]))
    return rows


def np_median(values: list[float]) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def build_label_summary() -> list[dict[str, object]]:
    if not LABELS_JSON.exists():
        return []
    payload = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    rows = list(payload.get("labels", {}).values())
    rows.sort(key=lambda row: (row.get("human_label", ""), row.get("run_date", ""), row.get("candidate_id", "")))
    return rows


def write_review_packet(
    manifest: list[dict[str, object]],
    summary: list[dict[str, object]],
    sweep: list[dict[str, object]],
    matches: list[dict[str, object]],
    tracks: list[dict[str, object]],
) -> None:
    recovered = sum(1 for row in matches if row.get("recovered_within_8_px") == "yes")
    known_total = len(matches)
    total_images = sum(int(row.get("images_processed", 0) or 0) for row in summary)
    total_candidates = sum(int(row.get("candidates_found", 0) or 0) for row in summary)
    total_review = sum(int(row.get("review_candidates", 0) or 0) for row in summary)
    strongest_tracks = sorted(tracks, key=lambda row: float(row["candidate_score"]), reverse=True)[:10]
    packet = [
        "# Cassini Jupiter Lightning Review Packet",
        "",
        "## Current Safe Claim",
        "",
        "I have a reproducible candidate-detection and review workflow for Cassini Jupiter night-side images. The detector recovers the published validation detections and saves matched, unmatched, and artifact-flagged candidates for review.",
        "",
        "I am not claiming new lightning yet. Unmatched candidates are a review pool.",
        "",
        "## Current Numbers",
        "",
        f"- Images processed: {total_images}",
        f"- Raw bright regions saved: {total_candidates}",
        f"- Review candidates after artifact filters: {total_review}",
        f"- Published marks recovered: {recovered} of {known_total}",
        f"- Dataset manifest rows: {len(manifest)}",
        "",
        "## Date Summary",
        "",
        "| Date | Images | Raw candidates | Review candidates | Published matches | Unmatched review |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        packet.append(
            f"| {row['run_date']} | {row['images_processed']} | {row['candidates_found']} | "
            f"{row['review_candidates']} | {row['published_matches']} | {row['unmatched_review_candidates']} |"
        )
    packet.extend([
        "",
        "## Known-Match Evidence",
        "",
        "| Image | Published x/y | Nearest detector x/y | Offset px | Recovered? | Candidate |",
        "|---|---:|---:|---:|---|---|",
    ])
    for row in matches:
        packet.append(
            f"| {row['image_id']} | {row['published_x']}, {row['published_y']} | "
            f"{row['nearest_x']}, {row['nearest_y']} | {row['offset_px']} | "
            f"{row['recovered_within_8_px']} | {row['nearest_candidate_id']} |"
        )
    packet.extend([
        "",
        "## Strongest Temporal Tracks",
        "",
        "These are still review targets, not confirmed storms. Frame repetition is useful because cosmic rays usually do not persist across multiple nearby frames.",
        "",
        "| Date | Track | Frames | Start image | End image | Net motion px | Score |",
        "|---|---|---:|---|---|---:|---:|",
    ])
    for row in strongest_tracks:
        packet.append(
            f"| {row['run_date']} | {row['track_id']} | {row['frame_count']} | "
            f"{row['first_image_id']} | {row['last_image_id']} | "
            f"{row['net_dx_px']}, {row['net_dy_px']} | {row['candidate_score']} |"
        )
    packet.extend([
        "",
        "## Threshold Sensitivity",
        "",
        "The threshold sweep is a false-positive control table. It shows how many candidates remain when SNR and blob-size requirements are tightened. A stricter rule can reduce the review queue, but it must not erase the published validation detections.",
        "",
        "Key output file: `outputs/detection/threshold_sweep.csv`.",
        "",
        "## Files To Open During Review",
        "",
        "- `outputs/detection/dataset_manifest.csv`",
        "- `outputs/detection/detection_summary.csv`",
        "- `outputs/detection/known_match_report.csv`",
        "- `outputs/detection/temporal_track_summary.csv`",
        "- `outputs/detection/threshold_sweep.csv`",
        "- `outputs/detection/<date>/candidate_contact_sheet.png`",
        "",
    ])
    (OUTPUT_DIR / "review_packet.md").write_text("\n".join(packet), encoding="utf-8")


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

    sweep = build_threshold_sweep()
    write_csv(
        OUTPUT_DIR / "threshold_sweep.csv",
        sweep,
        [
            "run_date",
            "run_label",
            "snr_threshold",
            "min_blob_size",
            "candidate_count",
            "review_candidate_count",
            "artifact_flagged_count",
            "published_matches",
            "unmatched_review_candidates",
        ],
    )

    matches = build_known_match_report()
    write_csv(
        OUTPUT_DIR / "known_match_report.csv",
        matches,
        [
            "image_id",
            "image_number",
            "published_label",
            "published_x",
            "published_y",
            "published_power_w",
            "nearest_candidate_id",
            "nearest_track_id",
            "nearest_run_date",
            "nearest_x",
            "nearest_y",
            "offset_px",
            "recovered_within_8_px",
            "nearest_peak_snr",
            "nearest_blob_size",
            "nearest_artifact_flags",
            "nearest_candidate_score",
            "source",
        ],
    )

    tracks = build_temporal_track_summary()
    write_csv(
        OUTPUT_DIR / "temporal_track_summary.csv",
        tracks,
        [
            "run_date",
            "track_id",
            "frame_count",
            "first_frame_index",
            "last_frame_index",
            "first_image_id",
            "last_image_id",
            "start_time",
            "end_time",
            "start_x",
            "start_y",
            "end_x",
            "end_y",
            "net_dx_px",
            "net_dy_px",
            "median_x",
            "median_y",
            "median_peak_snr",
            "candidate_score",
            "reason",
            "candidate_ids",
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
    print(f"Wrote {OUTPUT_DIR / 'threshold_sweep.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'known_match_report.csv'}")
    print(f"Wrote {OUTPUT_DIR / 'temporal_track_summary.csv'}")
    write_review_packet(manifest, summary, sweep, matches, tracks)
    print(f"Wrote {OUTPUT_DIR / 'review_packet.md'}")
    if labels:
        print(f"Wrote {OUTPUT_DIR / 'candidate_labels_grouped.csv'}")


if __name__ == "__main__":
    main()
