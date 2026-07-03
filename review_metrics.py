from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
REVIEW_METRICS_CSV = OUTPUT_DIR / "review_metrics_summary.csv"
REVIEW_DECISION_CSV = OUTPUT_DIR / "review_decision_matrix.csv"
TRACK_QUALITY_CSV = OUTPUT_DIR / "temporal_track_quality.csv"
THRESHOLD_RECOMMENDATIONS_CSV = OUTPUT_DIR / "threshold_recommendations.csv"
REVIEW_REPORT_MD = OUTPUT_DIR / "review_metrics_report.md"
REVIEW_REPORT_HTML = OUTPUT_DIR / "review_metrics_report.html"


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


def load_labels() -> dict[str, dict[str, object]]:
    path = OUTPUT_DIR / "candidate_labels.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("labels", {})


def build_review_metrics() -> list[dict[str, object]]:
    summary = read_csv(OUTPUT_DIR / "detection_summary.csv")
    training = read_csv(OUTPUT_DIR / "training_manifest.csv")
    queue = read_csv(OUTPUT_DIR / "scientific_review_queue.csv")
    labels = load_labels()

    label_counts = Counter(str(row.get("human_label") or "unlabeled") for row in training)
    suggested_counts = Counter(str(row.get("suggested_label") or "") for row in training)
    category_counts = Counter(str(row.get("review_category") or "") for row in queue)
    split_counts = Counter(str(row.get("training_split") or "") for row in training)
    artifact_flags = Counter()
    for row in queue:
        for flag in str(row.get("artifact_flags") or "").split("|"):
            if flag:
                artifact_flags[flag] += 1

    total_images = sum(int(numeric(row.get("images_processed"))) for row in summary)
    total_candidates = sum(int(numeric(row.get("candidates_found"))) for row in summary)
    total_review = sum(int(numeric(row.get("review_candidates"))) for row in summary)
    total_matches = sum(int(numeric(row.get("published_matches"))) for row in summary)
    total_unmatched = sum(int(numeric(row.get("unmatched_review_candidates"))) for row in summary)
    label_total = len(labels)

    if total_candidates:
        review_fraction = total_review / total_candidates
    else:
        review_fraction = 0.0

    rows = [
        {"metric": "images_processed", "value": total_images, "meaning": "Cassini frames processed by generated detector outputs."},
        {"metric": "raw_bright_regions", "value": total_candidates, "meaning": "All first-pass bright regions saved before strict review filtering."},
        {"metric": "review_candidates", "value": total_review, "meaning": "Candidates after artifact filters; still not confirmed lightning."},
        {"metric": "review_fraction", "value": f"{review_fraction:.4f}", "meaning": "Fraction of raw bright regions that remain review candidates."},
        {"metric": "published_matches_recovered", "value": total_matches, "meaning": "Published validation marks recovered by detector outputs."},
        {"metric": "unmatched_review_candidates", "value": total_unmatched, "meaning": "Review candidates not matching published validation marks."},
        {"metric": "scientific_review_queue_rows", "value": len(queue), "meaning": "Curated first human-review queue."},
        {"metric": "saved_human_labels", "value": label_total, "meaning": "Labels currently saved by human reviewers."},
    ]
    for label, count in sorted(label_counts.items()):
        rows.append({"metric": f"human_label_{label}", "value": count, "meaning": "Training manifest rows by current saved human label."})
    for label, count in sorted(suggested_counts.items()):
        rows.append({"metric": f"suggested_label_{label}", "value": count, "meaning": "Suggested label before human review."})
    for category, count in sorted(category_counts.items()):
        rows.append({"metric": f"review_category_{category}", "value": count, "meaning": "Scientific review queue category."})
    for split, count in sorted(split_counts.items()):
        rows.append({"metric": f"training_split_{split}", "value": count, "meaning": "Training/review split assignment."})
    for flag, count in artifact_flags.most_common():
        rows.append({"metric": f"artifact_flag_{flag}", "value": count, "meaning": "Artifact flag frequency in curated review queue."})
    return rows


def build_decision_matrix() -> list[dict[str, object]]:
    training = read_csv(OUTPUT_DIR / "training_manifest.csv")
    tracks = read_csv(OUTPUT_DIR / "temporal_track_summary.csv")
    labels = load_labels()
    track_by_candidate: dict[str, dict[str, str]] = {}
    for track in tracks:
        for candidate_id in str(track.get("candidate_ids") or "").split("|"):
            if candidate_id:
                track_by_candidate[candidate_id] = track

    rows = []
    for row in training:
        candidate_id = str(row.get("candidate_id", ""))
        track = track_by_candidate.get(candidate_id, {})
        human = labels.get(candidate_id, {})
        category = str(row.get("review_category", ""))
        artifact_flags = str(row.get("artifact_flags") or "")
        frame_count = int(numeric(track.get("frame_count"), numeric(row.get("track_length"), 1)))
        snr = numeric(row.get("snr"))
        blob_size = int(numeric(row.get("blob_size")))
        motion = numeric(track.get("motion_consistency"), 0.0)

        if human.get("human_label"):
            next_action = "use_human_label"
        elif category == "published_match":
            next_action = "confirm_known_validation_mark"
        elif artifact_flags:
            next_action = "review_as_negative_example"
        elif frame_count >= 3 and motion >= 0.75:
            next_action = "priority_temporal_review"
        elif frame_count >= 2:
            next_action = "temporal_review"
        elif snr >= 20 and blob_size >= 3:
            next_action = "single_frame_visual_review"
        else:
            next_action = "low_priority_review"

        rows.append({
            "candidate_id": candidate_id,
            "image_id": row.get("image_id", ""),
            "run_date": row.get("run_date", ""),
            "review_category": category,
            "suggested_label": row.get("suggested_label", ""),
            "human_label": human.get("human_label", ""),
            "label_status": "labeled" if human.get("human_label") else "unlabeled",
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "snr": row.get("snr", ""),
            "blob_size": row.get("blob_size", ""),
            "artifact_flags": artifact_flags,
            "frame_count": frame_count,
            "motion_consistency": f"{motion:.3f}" if track else "",
            "candidate_score": row.get("candidate_score", ""),
            "next_action": next_action,
            "reason": reason_for_action(next_action),
        })

    action_priority = {
        "confirm_known_validation_mark": 0,
        "priority_temporal_review": 1,
        "temporal_review": 2,
        "single_frame_visual_review": 3,
        "review_as_negative_example": 4,
        "use_human_label": 5,
        "low_priority_review": 6,
    }
    rows.sort(key=lambda row: (action_priority.get(str(row["next_action"]), 99), -numeric(row.get("candidate_score")), -numeric(row.get("snr"))))
    for index, row in enumerate(rows, start=1):
        row["review_rank"] = index
    return rows


def classify_track(row: dict[str, str]) -> tuple[str, str]:
    frame_count = int(numeric(row.get("frame_count")))
    snr = numeric(row.get("median_peak_snr"))
    motion = numeric(row.get("motion_consistency"))
    mean_step = numeric(row.get("mean_step_px"))
    score = numeric(row.get("candidate_score"))
    reason_parts = []

    if frame_count <= 1:
        return "single_frame_not_temporal", "Only one frame; cannot support temporal persistence."
    if frame_count >= 3:
        reason_parts.append("appears in 3+ frames")
    else:
        reason_parts.append("appears in 2 frames")
    if motion >= 0.8:
        reason_parts.append("consistent step size")
    elif motion >= 0.5:
        reason_parts.append("moderate step consistency")
    else:
        reason_parts.append("irregular step size")
    if snr >= 20:
        reason_parts.append("high SNR")
    elif snr >= 10:
        reason_parts.append("moderate SNR")
    else:
        reason_parts.append("low SNR")

    if frame_count >= 3 and motion >= 0.75 and snr >= 10 and 5 <= mean_step <= 160:
        label = "strong_temporal_review"
    elif frame_count >= 2 and motion >= 0.5 and snr >= 7:
        label = "moderate_temporal_review"
    elif frame_count >= 2:
        label = "weak_temporal_review"
    else:
        label = "single_frame_not_temporal"

    if score <= 0:
        reason_parts.append("low detector score")
    return label, "; ".join(reason_parts)


def build_track_quality() -> list[dict[str, object]]:
    tracks = read_csv(OUTPUT_DIR / "temporal_track_summary.csv")
    rows = []
    for track in tracks:
        quality, reason = classify_track(track)
        rows.append({
            "run_date": track.get("run_date", ""),
            "track_id": track.get("track_id", ""),
            "frame_count": track.get("frame_count", ""),
            "first_image_id": track.get("first_image_id", ""),
            "last_image_id": track.get("last_image_id", ""),
            "median_peak_snr": track.get("median_peak_snr", ""),
            "mean_step_px": track.get("mean_step_px", ""),
            "motion_consistency": track.get("motion_consistency", ""),
            "candidate_score": track.get("candidate_score", ""),
            "temporal_quality": quality,
            "quality_reason": reason,
            "candidate_ids": track.get("candidate_ids", ""),
        })
    quality_order = {
        "strong_temporal_review": 0,
        "moderate_temporal_review": 1,
        "weak_temporal_review": 2,
        "single_frame_not_temporal": 3,
    }
    rows.sort(
        key=lambda row: (
            quality_order.get(str(row["temporal_quality"]), 99),
            -int(numeric(row.get("frame_count"))),
            -numeric(row.get("candidate_score")),
            -numeric(row.get("median_peak_snr")),
        )
    )
    return rows


def build_threshold_recommendations() -> list[dict[str, object]]:
    sweep = read_csv(OUTPUT_DIR / "threshold_sweep.csv")
    by_threshold: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in sweep:
        by_threshold[(row.get("snr_threshold", ""), row.get("min_blob_size", ""))].append(row)

    rows = []
    for (snr_threshold, min_blob_size), items in by_threshold.items():
        total_candidates = sum(int(numeric(row.get("candidate_count"))) for row in items)
        total_review = sum(int(numeric(row.get("review_candidate_count"))) for row in items)
        total_artifacts = sum(int(numeric(row.get("artifact_flagged_count"))) for row in items)
        total_matches = sum(int(numeric(row.get("published_matches"))) for row in items)
        total_unmatched = sum(int(numeric(row.get("unmatched_review_candidates"))) for row in items)
        recall = total_matches / 6.0 if total_matches <= 6 else 1.0
        review_fraction = total_review / total_candidates if total_candidates else 0.0
        if total_matches == 6:
            interpretation = "keeps all published marks in this validation set"
        elif total_matches >= 4:
            interpretation = "misses at least one published mark; risky without review"
        else:
            interpretation = "too strict for current validation set"
        rows.append({
            "snr_threshold": snr_threshold,
            "min_blob_size": min_blob_size,
            "candidate_count": total_candidates,
            "review_candidate_count": total_review,
            "artifact_flagged_count": total_artifacts,
            "published_matches": total_matches,
            "published_recall": f"{recall:.3f}",
            "unmatched_review_candidates": total_unmatched,
            "review_fraction": f"{review_fraction:.4f}",
            "interpretation": interpretation,
        })
    rows.sort(
        key=lambda row: (
            -int(numeric(row.get("published_matches"))),
            int(numeric(row.get("review_candidate_count"))),
            -float(row.get("snr_threshold", 0) or 0),
            -float(row.get("min_blob_size", 0) or 0),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def reason_for_action(action: str) -> str:
    return {
        "use_human_label": "Already labeled; preserve as training or validation evidence.",
        "confirm_known_validation_mark": "Published validation target should be checked and labeled first.",
        "review_as_negative_example": "Artifact-flagged rows are useful false-positive/negative-training examples.",
        "priority_temporal_review": "Repeated candidate with strong pixel-motion consistency.",
        "temporal_review": "Repeated candidate needs visual and geometry review.",
        "single_frame_visual_review": "Strong bright blob, but single-frame evidence is weak by itself.",
        "low_priority_review": "Lower evidence row; keep saved but review after stronger examples.",
    }.get(action, "")


def write_markdown_report(
    metrics: list[dict[str, object]],
    matrix: list[dict[str, object]],
    track_quality: list[dict[str, object]],
    threshold_recommendations: list[dict[str, object]],
) -> None:
    metric_lookup = {row["metric"]: row["value"] for row in metrics}
    action_counts = Counter(str(row["next_action"]) for row in matrix)
    quality_counts = Counter(str(row["temporal_quality"]) for row in track_quality)
    lines = [
        "# Review Metrics Report",
        "",
        "This report summarizes the current candidate-review state. It does not confirm new lightning.",
        "",
        "## Core Numbers",
        "",
        f"- Images processed: {metric_lookup.get('images_processed', 0)}",
        f"- Raw bright regions: {metric_lookup.get('raw_bright_regions', 0)}",
        f"- Review candidates: {metric_lookup.get('review_candidates', 0)}",
        f"- Published validation marks recovered: {metric_lookup.get('published_matches_recovered', 0)}",
        f"- Unmatched review candidates: {metric_lookup.get('unmatched_review_candidates', 0)}",
        f"- Scientific review queue rows: {metric_lookup.get('scientific_review_queue_rows', 0)}",
        f"- Saved human labels: {metric_lookup.get('saved_human_labels', 0)}",
        "",
        "## Decision Queue",
        "",
        "| Next action | Count | Meaning |",
        "|---|---:|---|",
    ]
    for action, count in sorted(action_counts.items()):
        lines.append(f"| {action} | {count} | {reason_for_action(action)} |")
    lines.extend([
        "",
        "## Temporal Track Quality",
        "",
        "| Temporal quality | Count | Meaning |",
        "|---|---:|---|",
    ])
    quality_meanings = {
        "strong_temporal_review": "Best temporal-review targets, still not confirmed lightning.",
        "moderate_temporal_review": "Repeated candidates that may be useful after visual inspection.",
        "weak_temporal_review": "Repeated candidates with weak or irregular evidence.",
        "single_frame_not_temporal": "Single-frame candidates; useful visually but not temporal evidence.",
    }
    for quality, count in sorted(quality_counts.items()):
        lines.append(f"| {quality} | {count} | {quality_meanings.get(quality, '')} |")
    lines.extend([
        "",
        "## Threshold Tradeoff",
        "",
        "These rows summarize stricter detector settings after artifact filtering. The current sweep shows an important warning: the stricter reviewable-only filters do not keep all six published marks. That means strict automatic rejection can create false negatives and must not replace human review.",
        "",
        "| Rank | SNR threshold | Min blob | Review candidates | Published matches | Recall | Interpretation |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in threshold_recommendations[:10]:
        lines.append(
            f"| {row['rank']} | {row['snr_threshold']} | {row['min_blob_size']} | "
            f"{row['review_candidate_count']} | {row['published_matches']} | {row['published_recall']} | "
            f"{row['interpretation']} |"
        )
    lines.extend([
        "",
        "## Top Review Rows",
        "",
        "| Rank | Candidate | Image | Date | Action | x/y | SNR | Blob | Score |",
        "|---:|---|---|---|---|---|---:|---:|---:|",
    ])
    for row in matrix[:25]:
        lines.append(
            f"| {row['review_rank']} | {row['candidate_id']} | {row['image_id']} | {row['run_date']} | "
            f"{row['next_action']} | {row['x']}, {row['y']} | {row['snr']} | {row['blob_size']} | {row['candidate_score']} |"
        )
    lines.extend([
        "",
        "## Safe Interpretation",
        "",
        "The detector has recovered the known validation marks and produced a prioritized review queue. "
        "Unmatched candidates remain review targets, not discoveries.",
    ])
    REVIEW_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_html_report(
    metrics: list[dict[str, object]],
    matrix: list[dict[str, object]],
    track_quality: list[dict[str, object]],
    threshold_recommendations: list[dict[str, object]],
) -> None:
    metric_rows = "\n".join(
        f"<tr><td>{html.escape(str(row['metric']))}</td><td>{html.escape(str(row['value']))}</td><td>{html.escape(str(row['meaning']))}</td></tr>"
        for row in metrics
    )
    matrix_rows = "\n".join(
        "<tr>"
        f"<td>{row['review_rank']}</td>"
        f"<td>{html.escape(str(row['candidate_id']))}</td>"
        f"<td>{html.escape(str(row['image_id']))}</td>"
        f"<td>{html.escape(str(row['run_date']))}</td>"
        f"<td>{html.escape(str(row['next_action']))}</td>"
        f"<td>{html.escape(str(row['x']))}, {html.escape(str(row['y']))}</td>"
        f"<td>{html.escape(str(row['snr']))}</td>"
        f"<td>{html.escape(str(row['blob_size']))}</td>"
        f"<td>{html.escape(str(row['candidate_score']))}</td>"
        "</tr>"
        for row in matrix[:100]
    )
    quality_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['temporal_quality']))}</td>"
        f"<td>{html.escape(str(row['run_date']))}</td>"
        f"<td>{html.escape(str(row['track_id']))}</td>"
        f"<td>{html.escape(str(row['frame_count']))}</td>"
        f"<td>{html.escape(str(row['motion_consistency']))}</td>"
        f"<td>{html.escape(str(row['median_peak_snr']))}</td>"
        f"<td>{html.escape(str(row['quality_reason']))}</td>"
        "</tr>"
        for row in track_quality[:100]
    )
    threshold_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['rank']))}</td>"
        f"<td>{html.escape(str(row['snr_threshold']))}</td>"
        f"<td>{html.escape(str(row['min_blob_size']))}</td>"
        f"<td>{html.escape(str(row['review_candidate_count']))}</td>"
        f"<td>{html.escape(str(row['published_matches']))}</td>"
        f"<td>{html.escape(str(row['published_recall']))}</td>"
        f"<td>{html.escape(str(row['interpretation']))}</td>"
        "</tr>"
        for row in threshold_recommendations[:25]
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Jupiter Lightning Review Metrics</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; color: #1d1b16; background: #f7f4ec; }}
    h1, h2 {{ font-family: Georgia, serif; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; background: white; }}
    th, td {{ border: 1px solid #d8d0c0; padding: 7px 9px; text-align: left; font-size: 14px; }}
    th {{ background: #eee5d4; }}
    .warning {{ background: #fff2c7; border: 1px solid #e2c15c; padding: 12px; }}
  </style>
</head>
<body>
  <h1>Jupiter Lightning Review Metrics</h1>
  <p class="warning">This report summarizes detector evidence and review priority. It does not confirm new lightning. Strict artifact-filtered thresholds can miss published validation marks, so stricter is not automatically better.</p>
  <h2>Metrics</h2>
  <table><thead><tr><th>Metric</th><th>Value</th><th>Meaning</th></tr></thead><tbody>{metric_rows}</tbody></table>
  <h2>Top Review Queue</h2>
  <table><thead><tr><th>Rank</th><th>Candidate</th><th>Image</th><th>Date</th><th>Next action</th><th>x/y</th><th>SNR</th><th>Blob</th><th>Score</th></tr></thead><tbody>{matrix_rows}</tbody></table>
  <h2>Temporal Track Quality</h2>
  <table><thead><tr><th>Quality</th><th>Date</th><th>Track</th><th>Frames</th><th>Motion consistency</th><th>Median SNR</th><th>Reason</th></tr></thead><tbody>{quality_rows}</tbody></table>
  <h2>Threshold Tradeoff</h2>
  <table><thead><tr><th>Rank</th><th>SNR threshold</th><th>Min blob</th><th>Review candidates</th><th>Published matches</th><th>Recall</th><th>Interpretation</th></tr></thead><tbody>{threshold_rows}</tbody></table>
</body>
</html>
"""
    REVIEW_REPORT_HTML.write_text(document, encoding="utf-8")


def main() -> None:
    metrics = build_review_metrics()
    matrix = build_decision_matrix()
    track_quality = build_track_quality()
    threshold_recommendations = build_threshold_recommendations()
    write_csv(REVIEW_METRICS_CSV, metrics, ["metric", "value", "meaning"])
    write_csv(
        REVIEW_DECISION_CSV,
        matrix,
        [
            "review_rank",
            "candidate_id",
            "image_id",
            "run_date",
            "review_category",
            "suggested_label",
            "human_label",
            "label_status",
            "x",
            "y",
            "snr",
            "blob_size",
            "artifact_flags",
            "frame_count",
            "motion_consistency",
            "candidate_score",
            "next_action",
            "reason",
        ],
    )
    write_csv(
        TRACK_QUALITY_CSV,
        track_quality,
        [
            "run_date",
            "track_id",
            "frame_count",
            "first_image_id",
            "last_image_id",
            "median_peak_snr",
            "mean_step_px",
            "motion_consistency",
            "candidate_score",
            "temporal_quality",
            "quality_reason",
            "candidate_ids",
        ],
    )
    write_csv(
        THRESHOLD_RECOMMENDATIONS_CSV,
        threshold_recommendations,
        [
            "rank",
            "snr_threshold",
            "min_blob_size",
            "candidate_count",
            "review_candidate_count",
            "artifact_flagged_count",
            "published_matches",
            "published_recall",
            "unmatched_review_candidates",
            "review_fraction",
            "interpretation",
        ],
    )
    write_markdown_report(metrics, matrix, track_quality, threshold_recommendations)
    write_html_report(metrics, matrix, track_quality, threshold_recommendations)
    print(f"Wrote {REVIEW_METRICS_CSV}")
    print(f"Wrote {REVIEW_DECISION_CSV}")
    print(f"Wrote {TRACK_QUALITY_CSV}")
    print(f"Wrote {THRESHOLD_RECOMMENDATIONS_CSV}")
    print(f"Wrote {REVIEW_REPORT_MD}")
    print(f"Wrote {REVIEW_REPORT_HTML}")


if __name__ == "__main__":
    main()
