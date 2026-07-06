from __future__ import annotations

import csv
import json
import urllib.error
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
OPUS_DATA = "https://opus.pds-rings.seti.org/opus/api/data.json"
CONTEXT_CSV = OUTPUT_DIR / "nearby_filter_context.csv"
CONTEXT_MD = OUTPUT_DIR / "nearby_filter_context_report.md"
WINDOW_MINUTES = 20


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


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", ""))


def format_time(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def manifest_by_image() -> dict[str, dict[str, str]]:
    return {row["image_id"]: row for row in read_csv(OUTPUT_DIR / "dataset_manifest.csv")}


def query_nearby(start: datetime, end: datetime) -> list[dict[str, str]]:
    params = {
        "instrument": "Cassini ISS",
        "planet": "Jupiter",
        "target": "Jupiter",
        "COISScamera": "Narrow Angle",
        "time1": format_time(start),
        "time2": format_time(end),
        "cols": "opusid,time1,observationduration,COISScamera,COISSfilter,COISSimagenumber,SURFACEGEOjupiter_centerresolution",
        "order": "time1,opusid",
        "limit": "300",
    }
    try:
        with urlopen(f"{OPUS_DATA}?{urlencode(params)}", timeout=30) as handle:
            payload = json.load(handle)
    except (OSError, urllib.error.URLError) as exc:
        return [{
            "query_error": str(exc),
        }]
    rows = []
    for item in payload.get("page", []):
        rows.append({
            "opus_id": item[0],
            "time": item[1],
            "duration_seconds": item[2],
            "camera": item[3],
            "filter": item[4],
            "image_number": item[5],
            "center_resolution_km_px": item[6],
            "query_error": "",
        })
    return rows


def build_context(limit_candidates: int = 106) -> list[dict[str, object]]:
    dossier = read_csv(OUTPUT_DIR / "candidate_review_dossier.csv")[:limit_candidates]
    manifest = manifest_by_image()
    query_cache: dict[str, list[dict[str, str]]] = {}
    rows = []
    for candidate in dossier:
        image = manifest.get(candidate["image_id"], {})
        candidate_time_text = image.get("time", "")
        if not candidate_time_text:
            rows.append(base_row(candidate, "", "", "", "", "", "", "", "missing_candidate_time"))
            continue
        candidate_time = parse_time(candidate_time_text)
        start = candidate_time - timedelta(minutes=WINDOW_MINUTES)
        end = candidate_time + timedelta(minutes=WINDOW_MINUTES)
        cache_key = f"{format_time(start)}|{format_time(end)}"
        nearby = query_cache.setdefault(cache_key, query_nearby(start, end))
        context = [
            row for row in nearby
            if not row.get("query_error")
            and row.get("filter") != "HAL"
            and row.get("image_number") != candidate["image_id"].lstrip("N")
        ]
        if nearby and nearby[0].get("query_error"):
            rows.append(base_row(candidate, candidate_time_text, "", "", "", "", "", "", f"query_error: {nearby[0]['query_error']}"))
            continue
        if not context:
            rows.append(base_row(candidate, candidate_time_text, "", "", "", "", "", "", "no_non_hal_context_in_window"))
            continue
        for item in context:
            delta = abs((parse_time(item["time"]) - candidate_time).total_seconds()) / 60.0
            rows.append(base_row(
                candidate,
                candidate_time_text,
                item["opus_id"],
                item["time"],
                item["filter"],
                item["duration_seconds"],
                f"{delta:.2f}",
                item["center_resolution_km_px"],
                "nearby_non_hal_context",
            ))
    rows.sort(key=lambda row: (int(row["review_rank"]), float(row["delta_minutes"] or 9999), str(row["context_filter"])))
    return rows


def base_row(
    candidate: dict[str, str],
    candidate_time: str,
    context_opus_id: str,
    context_time: str,
    context_filter: str,
    context_duration: str,
    delta_minutes: str,
    center_resolution: str,
    context_status: str,
) -> dict[str, object]:
    return {
        "review_rank": candidate.get("review_rank", ""),
        "candidate_id": candidate.get("candidate_id", ""),
        "image_id": candidate.get("image_id", ""),
        "run_date": candidate.get("run_date", ""),
        "candidate_time": candidate_time,
        "candidate_x": candidate.get("x", ""),
        "candidate_y": candidate.get("y", ""),
        "next_action": candidate.get("next_action", ""),
        "suggested_label": candidate.get("suggested_label", ""),
        "context_status": context_status,
        "context_opus_id": context_opus_id,
        "context_time": context_time,
        "context_filter": context_filter,
        "context_duration_seconds": context_duration,
        "delta_minutes": delta_minutes,
        "context_center_resolution_km_px": center_resolution,
    }


def write_report(rows: list[dict[str, object]]) -> None:
    by_candidate: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_candidate[str(row["candidate_id"])].append(row)
    candidates_with_context = sum(
        1 for items in by_candidate.values()
        if any(item["context_status"] == "nearby_non_hal_context" for item in items)
    )
    filter_counts: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        if row["context_status"] == "nearby_non_hal_context":
            filter_counts[str(row["context_filter"])] += 1
    lines = [
        "# Nearby Filter Context Report",
        "",
        f"Search window: +/- {WINDOW_MINUTES} minutes around each candidate's HAL image time.",
        "",
        "This report looks for nearby Cassini ISS Narrow Angle Camera images in non-HAL filters. It does not prove color or spectrum behavior; it only identifies context frames worth future inspection.",
        "",
        "## Summary",
        "",
        f"- Candidate rows checked: {len(by_candidate)}",
        f"- Candidates with at least one nearby non-HAL context image: {candidates_with_context}",
        f"- Context rows found: {sum(1 for row in rows if row['context_status'] == 'nearby_non_hal_context')}",
        "",
        "## Filters Found",
        "",
        "| Filter | Context rows |",
        "|---|---:|",
    ]
    for filter_name, count in sorted(filter_counts.items()):
        lines.append(f"| {filter_name} | {count} |")
    lines.extend([
        "",
        "## First Candidate Context Rows",
        "",
        "| Rank | Candidate | HAL image | Context filter | Delta min | Context OPUS ID |",
        "|---:|---|---|---|---:|---|",
    ])
    for row in rows[:40]:
        lines.append(
            f"| {row['review_rank']} | {row['candidate_id']} | {row['image_id']} | "
            f"{row['context_filter']} | {row['delta_minutes']} | {row['context_opus_id']} |"
        )
    lines.extend([
        "",
        "## Scientific Boundary",
        "",
        "Nearby filter context is a follow-up queue. A candidate still needs human review, temporal/geometric checks, and source-image inspection before any color or spectrum statement is safe.",
    ])
    CONTEXT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_context()
    fields = [
        "review_rank",
        "candidate_id",
        "image_id",
        "run_date",
        "candidate_time",
        "candidate_x",
        "candidate_y",
        "next_action",
        "suggested_label",
        "context_status",
        "context_opus_id",
        "context_time",
        "context_filter",
        "context_duration_seconds",
        "delta_minutes",
        "context_center_resolution_km_px",
    ]
    write_csv(CONTEXT_CSV, rows, fields)
    write_report(rows)
    print(f"Wrote {CONTEXT_CSV}")
    print(f"Wrote {CONTEXT_MD}")


if __name__ == "__main__":
    main()
