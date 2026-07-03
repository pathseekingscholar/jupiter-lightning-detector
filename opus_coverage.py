from __future__ import annotations

import csv
import json
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import detection_pipeline as detector


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
OPUS_DATA = "https://opus.pds-rings.seti.org/opus/api/data.json"


def iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def query_day(day: date) -> dict[str, object]:
    day_text = day.isoformat()
    params = {
        "instrument": "Cassini ISS",
        "planet": "Jupiter",
        "target": "Jupiter",
        "COISScamera": "Narrow Angle",
        "COISSfilter": "HAL",
        "time1": f"{day_text}T00:00:00",
        "time2": f"{day_text}T23:59:59",
        "cols": "opusid,time1,observationduration,COISScamera,COISSfilter,COISSimagenumber,SURFACEGEOjupiter_centerresolution",
        "order": "time1,opusid",
        "limit": "500",
    }
    try:
        with urlopen(f"{OPUS_DATA}?{urlencode(params)}", timeout=30) as handle:
            payload = json.load(handle)
    except (OSError, urllib.error.URLError) as exc:
        return {
            "date": day_text,
            "status": "query_error",
            "available_frames": 0,
            "duration_seconds": "",
            "first_time": "",
            "last_time": "",
            "processed": "no",
            "notes": str(exc),
        }
    page = payload.get("page", [])
    durations = sorted({str(row[2]) for row in page})
    return {
        "date": day_text,
        "status": "available" if page else "no_hal_nac_results",
        "available_frames": len(page),
        "duration_seconds": "|".join(durations),
        "first_time": page[0][1] if page else "",
        "last_time": page[-1][1] if page else "",
        "processed": "yes" if day_text in detector.DETECTION_RUNS else "no",
        "notes": "Cassini ISS NAC/HAL Jupiter query",
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "status", "available_frames", "duration_seconds", "first_time", "last_time", "processed", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    available = [row for row in rows if row["status"] == "available"]
    processed = [row for row in available if row["processed"] == "yes"]
    not_processed = [row for row in available if row["processed"] != "yes"]
    lines = [
        "# OPUS Nearby-Date Coverage Scan",
        "",
        "Query: Cassini ISS, Jupiter target, Narrow Angle Camera, H-alpha/HAL filter.",
        "",
        f"- Dates scanned: {len(rows)}",
        f"- Dates with NAC/HAL results: {len(available)}",
        f"- Dates already processed by the detector: {len(processed)}",
        f"- Dates available but not yet processed: {len(not_processed)}",
        "",
        "| Date | Status | Frames | Durations | Processed |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        durations = str(row["duration_seconds"]).replace("|", ", ")
        lines.append(
            f"| {row['date']} | {row['status']} | {row['available_frames']} | "
            f"{durations} | {row['processed']} |"
        )
    lines.extend([
        "",
        "This scan documents why the current detector dates were chosen. Empty dates are not failures; they simply returned no Cassini ISS NAC/HAL Jupiter results for this query.",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [query_day(day) for day in iter_dates(date(2000, 12, 28), date(2001, 1, 16))]
    write_csv(OUTPUT_DIR / "opus_nearby_date_coverage.csv", rows)
    write_markdown(ROOT / "docs" / "opus_nearby_date_coverage.md", rows)
    print(f"Wrote {OUTPUT_DIR / 'opus_nearby_date_coverage.csv'}")
    print(f"Wrote {ROOT / 'docs' / 'opus_nearby_date_coverage.md'}")


if __name__ == "__main__":
    main()
