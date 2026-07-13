from __future__ import annotations

import io
import base64
import csv
import json
import math
import mimetypes
import os
import sqlite3
import sys
import traceback
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
from PIL import Image, ImageDraw

import jupiter_pipeline as pipeline
import label_tools


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
NOTES_PATH = ROOT / "research_notes.json"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))
PUBLIC_URL = os.environ.get("PUBLIC_URL")
OPEN_BROWSER = os.environ.get("OPEN_BROWSER", "1").lower() not in {"0", "false", "no"}
REVIEW_KEY = os.environ.get("REVIEW_KEY", "")
DETECTION_DIR = ROOT / "outputs" / "detection"
DETECTION_STATUS_PATH = DETECTION_DIR / "status.json"
LABELS_PATH = DETECTION_DIR / "candidate_labels.json"
LABELS_CSV_PATH = DETECTION_DIR / "candidate_labels.csv"
LABELS_GROUPED_CSV_PATH = DETECTION_DIR / "candidate_labels_grouped.csv"
LABEL_SUMMARY_CSV_PATH = DETECTION_DIR / "candidate_label_summary.csv"
DETECTION_LOCK = threading.Lock()
DETECTION_DATES = ("2000-12-31", "2001-01-01", "2001-01-04", "2001-01-05", "2001-01-08", "2001-01-09", "2001-01-10", "2001-01-11", "2001-01-13")
DEFAULT_DETECTION_DATE = "2001-01-01"
LABEL_VALUES = {
    "known-lightning",
    "possible-lightning",
    "artifact",
    "cosmic-ray-hot-pixel",
    "uncertain",
}


def read_notes() -> dict:
    if not NOTES_PATH.exists():
        return {"notes": {}}
    return json.loads(NOTES_PATH.read_text(encoding="utf-8"))


def write_notes(payload: dict) -> None:
    NOTES_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_candidate_labels() -> dict:
    if not LABELS_PATH.exists():
        return {"labels": {}}
    return json.loads(LABELS_PATH.read_text(encoding="utf-8"))


def write_candidate_labels(payload: dict) -> None:
    DETECTION_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rows = sorted(payload.get("labels", {}).values(), key=lambda item: (item.get("run_date", ""), item.get("candidate_id", "")))
    with LABELS_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=label_tools.LABEL_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in label_tools.LABEL_FIELDNAMES})
    label_tools.write_derived_label_exports(rows, LABELS_GROUPED_CSV_PATH, LABEL_SUMMARY_CSV_PATH)


def labels_by_candidate_id() -> dict[str, dict]:
    return read_candidate_labels().get("labels", {})


def observation_payload() -> dict:
    with sqlite3.connect(pipeline.DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        observations = connection.execute(
            """
            SELECT opus_id, image_number, start_time, exposure_seconds, camera,
                   filter_name, gain_mode, center_resolution_km, preview_image
            FROM observations ORDER BY start_time
            """
        ).fetchall()
        candidates = connection.execute(
            """
            SELECT opus_id, label, x, y, published_power_w, peak_snr,
                   bright_pixel_count
            FROM candidates ORDER BY id
            """
        ).fetchall()
    grouped: dict[str, list[dict]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate["opus_id"], []).append(dict(candidate))
    return {
        "observations": [
            {
                **dict(row),
                "candidates": grouped.get(row["opus_id"], []),
                "opus_detail_url": (
                    "https://opus.pds-rings.seti.org/#/"
                    f"detail={row['opus_id']}"
                ),
            }
            for row in observations
        ],
        "notes": read_notes().get("notes", {}),
    }


def safe_detection_date(value: str | None) -> str:
    return value if value in DETECTION_DATES else DEFAULT_DETECTION_DATE


def detection_date_dir(run_date: str) -> Path:
    return DETECTION_DIR / run_date


def preview_url_for_image(image_number: str) -> str:
    matches = sorted((ROOT / "data" / "previews").glob(f"N{image_number}_*_full.png"))
    if matches:
        return f"/data/previews/{matches[0].name}"
    return f"/data/previews/N{image_number}_2_full.png"


def read_detection_rows(run_date: str = DEFAULT_DETECTION_DATE, limit: int = 150) -> dict:
    directory = detection_date_dir(run_date)
    review_path = directory / "review_candidates.csv"
    summary_path = directory / "summary.json"
    if not review_path.exists():
        return {
            "available": False,
            "run_date": run_date,
            "summary": {},
            "tracks": [],
            "message": f"Run detector for {run_date} to generate candidate detections.",
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    labels = labels_by_candidate_id()
    with review_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows = rows[:limit]
    tracks: dict[str, dict] = {}
    for row in rows:
        track = tracks.setdefault(
            row["track_id"],
            {
                "track_id": row["track_id"],
                "confidence": float(row["confidence"]),
                "track_length": int(row["track_length"]),
                "reason": row["reason"],
                "items": [],
            },
        )
        candidate_label = labels.get(row["candidate_id"], {})
        track["items"].append({
            **row,
            "confidence": float(row["confidence"]),
            "track_length": int(row["track_length"]),
            "frame_index": int(row["frame_index"]),
            "x": float(row["x"]),
            "y": float(row["y"]),
            "area_px": int(row["area_px"]),
            "peak_snr": float(row["peak_snr"]),
            "mean_snr": float(row["mean_snr"]),
            "integrated_snr": float(row["integrated_snr"]),
            "sharpness": float(row["sharpness"]),
            "elongation": float(row["elongation"]),
            "preview_image": preview_url_for_image(row["image_number"]),
            "opus_detail_url": f"https://opus.pds-rings.seti.org/#/detail={row['opus_id']}",
            "human_label": candidate_label.get("human_label", ""),
            "review_note": candidate_label.get("review_note", ""),
        })
    return {
        "available": True,
        "run_date": run_date,
        "summary": summary,
        "tracks": sorted(tracks.values(), key=lambda item: item["confidence"], reverse=True),
        "csv_url": f"/outputs/detection/{run_date}/review_candidates.csv",
        "all_csv_url": f"/outputs/detection/{run_date}/candidates.csv",
        "contact_sheet_url": f"/outputs/detection/{run_date}/candidate_contact_sheet.png",
    }


def read_detection_status() -> dict:
    if DETECTION_STATUS_PATH.exists():
        return json.loads(DETECTION_STATUS_PATH.read_text(encoding="utf-8"))
    return {"running": False, "message": "Detector has not been run from this session."}


def write_detection_status(payload: dict) -> None:
    DETECTION_DIR.mkdir(parents=True, exist_ok=True)
    DETECTION_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_detection_job(run_date: str) -> None:
    with DETECTION_LOCK:
        try:
            write_detection_status({
                "running": True,
                "run_date": run_date,
                "message": f"Running detector for {run_date}: loading OPUS sequence, enhancing frames, finding blobs, filtering artifacts, and linking tracks.",
            })
            import detection_pipeline

            candidates = detection_pipeline.run_detection(run_date=run_date)
            write_detection_status({
                "running": False,
                "ok": True,
                "run_date": run_date,
                "message": f"Detector finished for {run_date}. Found {len(candidates)} bright regions; refreshed that date's review cards and contact sheet.",
            })
        except Exception as exc:
            write_detection_status({
                "running": False,
                "ok": False,
                "run_date": run_date,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            })


def start_detection_job(run_date: str) -> dict:
    current = read_detection_status()
    if current.get("running"):
        return current
    thread = threading.Thread(target=run_detection_job, args=(run_date,), daemon=True)
    thread.start()
    return {"running": True, "run_date": run_date, "message": f"Detector started for {run_date}."}


def load_all_candidate_rows() -> list[dict]:
    rows = []
    for run_date in DETECTION_DATES:
        candidates_path = detection_date_dir(run_date) / "candidates.csv"
        if not candidates_path.exists():
            continue
        with candidates_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row["run_date"] = run_date
                rows.append(row)
    return rows


def validation_payload() -> dict:
    known_path = ROOT / "known_events.json"
    if not known_path.exists():
        return {"available": False, "message": "Known lightning reference file is missing."}

    candidates = load_all_candidate_rows()
    if not candidates:
        return {"available": False, "message": "Run the detector for at least one published date before validating known lightning recovery."}
    known = json.loads(known_path.read_text(encoding="utf-8"))
    results = []
    for observation in known["observations"]:
        image_rows = [row for row in candidates if row["image_number"] == observation["image_number"]]
        for event in observation["events"]:
            best = None
            best_distance = float("inf")
            for row in image_rows:
                dx = float(row["x"]) - float(event["x"])
                dy = float(row["y"]) - float(event["y"])
                distance = float((dx * dx + dy * dy) ** 0.5)
                if distance < best_distance:
                    best = row
                    best_distance = distance
            results.append({
                "image_number": observation["image_number"],
                "label": event["label"],
                "published_x": event["x"],
                "published_y": event["y"],
                "recovered": best is not None and best_distance <= 8.0,
                "distance_px": round(best_distance, 2) if best else None,
                "detected_x": round(float(best["x"]), 2) if best else None,
                "detected_y": round(float(best["y"]), 2) if best else None,
                "candidate_id": best["candidate_id"] if best else "",
                "peak_snr": round(float(best["peak_snr"]), 2) if best else None,
                "run_date": best["run_date"] if best else "",
                "note": "In detector output" if image_rows else "Date has not been run yet",
            })
    recovered = sum(1 for row in results if row["recovered"])
    return {
        "available": True,
        "source": known["source"],
        "results": results,
        "summary": f"{recovered} of {len(results)} published marks recovered across generated detector outputs.",
    }


def detector_characteristics_payload() -> dict:
    known_path = ROOT / "known_events.json"
    known_points = []
    if known_path.exists():
        known = json.loads(known_path.read_text(encoding="utf-8"))
        for observation in known["observations"]:
            for event in observation["events"]:
                known_points.append({
                    "image_number": observation["image_number"],
                    "x": float(event["x"]),
                    "y": float(event["y"]),
                })

    dates = []
    totals = {
        "frames": 0,
        "raw_candidates": 0,
        "review_candidates": 0,
        "known_recovered": 0,
        "known_total": len(known_points),
        "unmatched_review": 0,
    }
    flag_counts: dict[str, int] = {}

    for run_date in DETECTION_DATES:
        directory = detection_date_dir(run_date)
        summary_path = directory / "summary.json"
        candidates_path = directory / "candidates.csv"
        review_path = directory / "review_candidates.csv"
        if not summary_path.exists() or not candidates_path.exists():
            dates.append({
                "date": run_date,
                "available": False,
                "message": "Detector has not been run for this date.",
            })
            continue

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        with candidates_path.open(newline="", encoding="utf-8") as handle:
            candidates = list(csv.DictReader(handle))
        if review_path.exists():
            with review_path.open(newline="", encoding="utf-8") as handle:
                review_rows = list(csv.DictReader(handle))
        else:
            review_rows = []

        recovered_ids = set()
        for point in known_points:
            image_rows = [row for row in candidates if row["image_number"] == point["image_number"]]
            if not image_rows:
                continue
            best = min(
                image_rows,
                key=lambda row: math.hypot(float(row["x"]) - point["x"], float(row["y"]) - point["y"]),
            )
            distance = math.hypot(float(best["x"]) - point["x"], float(best["y"]) - point["y"])
            if distance <= 8.0:
                recovered_ids.add(best["candidate_id"])

        for row in candidates:
            for flag in filter(None, row.get("flags", "").split("|")):
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

        unmatched_review = sum(1 for row in review_rows if row["candidate_id"] not in recovered_ids)
        date_payload = {
            "date": run_date,
            "available": True,
            "frames": int(summary.get("frames", 0)),
            "raw_candidates": int(summary.get("candidates", 0)),
            "review_candidates": int(summary.get("review_candidates", 0)),
            "known_recovered": len(recovered_ids),
            "unmatched_review": unmatched_review,
        }
        dates.append(date_payload)
        totals["frames"] += date_payload["frames"]
        totals["raw_candidates"] += date_payload["raw_candidates"]
        totals["review_candidates"] += date_payload["review_candidates"]
        totals["known_recovered"] += date_payload["known_recovered"]
        totals["unmatched_review"] += date_payload["unmatched_review"]

    return {
        "rules": [
            "Use calibrated Cassini ISS NAC/H-alpha images, not screenshot photometry.",
            "Subtract a smooth local background and measure high-pass SNR.",
            "Detect connected bright regions above SNR 7.",
            "Flag single-pixel, too-small, sharp cosmic-ray-like, and streak-like detections.",
            "Promote review candidates only when area >= 3 pixels, peak SNR >= 8, and no artifact flags.",
            "Link reviewable candidates across nearby frames within 85 pixels and 12 minutes.",
        ],
        "classification": {
            "positive": "A detection within 8 pixels of a published Dyudina et al. lightning coordinate.",
            "negative_or_uncertain": "A detection that does not match the paper. It is not automatically wrong; it needs review as artifact, cosmic ray, uncertain, or possible new candidate.",
            "not_claimed": "The detector has not confirmed new lightning yet.",
        },
        "dates": dates,
        "totals": totals,
        "flag_counts": sorted(
            [{"flag": flag, "count": count} for flag, count in flag_counts.items()],
            key=lambda item: item["count"],
            reverse=True,
        ),
    }


def candidate_labels_payload() -> dict:
    payload = read_candidate_labels()
    if not LABELS_PATH.exists() or not LABELS_CSV_PATH.exists():
        write_candidate_labels(payload)
    labels = payload.get("labels", {})
    false_positives = [
        row for row in labels.values()
        if row.get("human_label") in {"artifact", "cosmic-ray-hot-pixel"}
    ]
    possible = [
        row for row in labels.values()
        if row.get("human_label") in {"known-lightning", "possible-lightning", "uncertain"}
    ]
    return {
        "labels": labels,
        "counts": {
            "labeled": len(labels),
            "false_positives": len(false_positives),
            "possible_or_uncertain": len(possible),
        },
        "json_url": "/outputs/detection/candidate_labels.json",
        "csv_url": "/outputs/detection/candidate_labels.csv",
        "grouped_csv_url": "/outputs/detection/candidate_labels_grouped.csv",
        "summary_csv_url": "/outputs/detection/candidate_label_summary.csv",
    }


def save_candidate_label(payload: dict) -> dict:
    candidate_id = str(payload["candidate_id"])
    human_label = str(payload.get("human_label", "uncertain"))
    if human_label not in LABEL_VALUES:
        raise ValueError(f"Unknown label: {human_label}")
    reviewed_at = str(payload.get("reviewed_at") or payload.get("updated_at") or datetime.now(timezone.utc).isoformat())
    labels = read_candidate_labels()
    labels.setdefault("labels", {})[candidate_id] = {
        "run_date": str(payload.get("run_date", "")),
        "candidate_id": candidate_id,
        "image_id": str(payload.get("image_id", "")),
        "image_number": str(payload.get("image_number", "")),
        "x": payload.get("x", ""),
        "y": payload.get("y", ""),
        "jupiter_latitude": payload.get("jupiter_latitude", ""),
        "jupiter_longitude": payload.get("jupiter_longitude", ""),
        "geometry_status": payload.get("geometry_status", ""),
        "brightness": payload.get("brightness", payload.get("peak_snr", "")),
        "blob_size": payload.get("blob_size", payload.get("area_px", "")),
        "snr": payload.get("snr", payload.get("peak_snr", "")),
        "artifact_flags": str(payload.get("artifact_flags", payload.get("flags", ""))),
        "candidate_score": payload.get("candidate_score", payload.get("confidence", "")),
        "human_label": human_label,
        "label": human_label,
        "confidence": str(payload.get("confidence", "medium")),
        "reviewer": str(payload.get("reviewer", "local-reviewer")),
        "review_note": str(payload.get("review_note", ""))[:2000],
        "review_stage": str(payload.get("review_stage", "first-review")),
        "needs_second_review": "yes" if label_tools.truthy(payload.get("needs_second_review")) else "no",
        "reviewed_at": reviewed_at,
        "updated_at": reviewed_at,
    }
    write_candidate_labels(labels)
    return {"saved": True, "candidate_id": candidate_id, **candidate_labels_payload()}


def query_float(query: dict[str, list[str]], key: str, default: float) -> float:
    try:
        return float(query.get(key, [str(default)])[0])
    except ValueError:
        return default


def query_int(query: dict[str, list[str]], key: str, default: int) -> int:
    try:
        return int(query.get(key, [str(default)])[0])
    except ValueError:
        return default


def render_processed(query: dict[str, list[str]]) -> tuple[bytes, str]:
    image_number = query.get("image", ["1357029177"])[0]
    low_pct = max(0.0, min(50.0, query_float(query, "low", 2.0)))
    high_pct = max(low_pct + 0.1, min(100.0, query_float(query, "high", 99.8)))
    gamma = max(0.2, min(4.0, query_float(query, "gamma", 1.0)))
    scale = max(0.1, min(1.0, query_float(query, "scale", 0.5)))
    crop_size = max(32, min(1024, query_int(query, "crop", 1024)))
    center_x = query_int(query, "x", 512)
    center_y = query_int(query, "y", 512)
    mark = query.get("mark", ["0"])[0] == "1"

    image_path, label_path = pipeline.image_paths_for_number(image_number)
    array = pipeline.load_calibrated_image(image_path, label_path)
    half = crop_size // 2
    x0 = max(0, min(array.shape[1] - crop_size, center_x - half))
    y0 = max(0, min(array.shape[0] - crop_size, center_y - half))
    x1 = min(array.shape[1], x0 + crop_size)
    y1 = min(array.shape[0], y0 + crop_size)
    patch = np.asarray(array[y0:y1, x0:x1])
    values = patch[pipeline.valid_mask(patch)]
    if values.size == 0:
        raise ValueError("Selected crop has no valid pixels")
    low = float(np.percentile(values, low_pct))
    high = float(np.percentile(values, high_pct))
    normalized = pipeline.normalize_to_u8(patch, low, high).astype(np.float64) / 255.0
    normalized = np.power(normalized, 1.0 / gamma)
    rendered = Image.fromarray(np.rint(normalized * 255).astype(np.uint8), mode="L").convert("RGB")

    if mark and x0 <= center_x < x1 and y0 <= center_y < y1:
        draw = ImageDraw.Draw(rendered)
        px, py = center_x - x0, center_y - y0
        radius = max(5, crop_size // 40)
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), outline=(177, 38, 29), width=2)

    output_size = (
        max(1, round(rendered.width * scale)),
        max(1, round(rendered.height * scale)),
    )
    rendered = rendered.resize(output_size, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    rendered.save(buffer, format="PNG", optimize=True)
    filename = (
        f"N{image_number}_crop-{crop_size}_scale-{scale:g}_"
        f"stretch-{low_pct:g}-{high_pct:g}.png"
    )
    return buffer.getvalue(), filename


def render_detection_crop(query: dict[str, list[str]]) -> bytes:
    image_number = query.get("image", ["1357029177"])[0]
    center_x = query_int(query, "x", 512)
    center_y = query_int(query, "y", 512)
    crop_size = max(48, min(256, query_int(query, "crop", 128)))
    image_path, label_path = pipeline.image_paths_for_number(image_number)
    array = pipeline.load_calibrated_image(image_path, label_path)
    half = crop_size // 2
    x0 = max(0, min(array.shape[1] - crop_size, center_x - half))
    y0 = max(0, min(array.shape[0] - crop_size, center_y - half))
    patch = np.asarray(array[y0:y0 + crop_size, x0:x0 + crop_size])
    values = patch[pipeline.valid_mask(patch)]
    if values.size == 0:
        raise ValueError("Selected crop has no valid pixels")
    low = float(np.percentile(values, 2.0))
    high = float(np.percentile(values, 99.8))
    rendered = Image.fromarray(pipeline.normalize_to_u8(patch, low, high), mode="L").convert("RGB")
    draw = ImageDraw.Draw(rendered)
    px, py = center_x - x0, center_y - y0
    radius = max(6, crop_size // 22)
    draw.ellipse((px - radius, py - radius, px + radius, py + radius), outline=(177, 38, 29), width=2)
    rendered = rendered.resize((176, 176), Image.Resampling.NEAREST)
    buffer = io.BytesIO()
    rendered.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    server_version = "JupiterWorkbench/1.0"

    def log_message(self, format: str, *args) -> None:
        return

    def is_authorized(self) -> bool:
        if not REVIEW_KEY:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header.removeprefix("Basic ").strip()).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return False
        _, _, provided_key = decoded.partition(":")
        return provided_key == REVIEW_KEY

    def send_auth_required(self) -> None:
        payload = json.dumps({"error": "Review key required"}).encode("utf-8")
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="Jupiter Lightning Review"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def send_bytes(
        self,
        payload: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        disposition: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_bytes(
            json.dumps(payload).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def do_GET(self) -> None:
        if not self.is_authorized():
            self.send_auth_required()
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/observations":
            self.send_json(observation_payload())
            return
        if parsed.path == "/api/detection":
            query = parse_qs(parsed.query)
            self.send_json(read_detection_rows(safe_detection_date(query.get("date", [None])[0])))
            return
        if parsed.path == "/api/detection-status":
            self.send_json(read_detection_status())
            return
        if parsed.path == "/api/validation":
            self.send_json(validation_payload())
            return
        if parsed.path == "/api/detector-characteristics":
            self.send_json(detector_characteristics_payload())
            return
        if parsed.path == "/api/candidate-labels":
            self.send_json(candidate_labels_payload())
            return
        if parsed.path == "/api/detection-crop":
            try:
                payload = render_detection_crop(parse_qs(parsed.query))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            self.send_bytes(payload, "image/png")
            return
        if parsed.path in ("/api/process", "/api/export"):
            try:
                payload, filename = render_processed(parse_qs(parsed.query))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            disposition = None
            if parsed.path == "/api/export":
                disposition = f'attachment; filename="{filename}"'
            self.send_bytes(payload, "image/png", disposition=disposition)
            return
        if parsed.path.startswith("/data/previews/"):
            self.serve_file(ROOT / parsed.path.lstrip("/"))
            return
        if parsed.path.startswith("/outputs/"):
            self.serve_file(ROOT / parsed.path.lstrip("/"))
            return
        if parsed.path.startswith("/static-data/") or parsed.path.startswith("/static-assets/"):
            self.serve_file(ROOT / "public_site" / parsed.path.lstrip("/"))
            return
        relative = "index.html" if parsed.path in ("", "/") else parsed.path.lstrip("/")
        self.serve_file(WEB / relative)

    def do_POST(self) -> None:
        if not self.is_authorized():
            self.send_auth_required()
            return
        parsed = urlparse(self.path)
        if parsed.path == "/api/run-detection":
            query = parse_qs(parsed.query)
            self.send_json(start_detection_job(safe_detection_date(query.get("date", [None])[0])))
            return
        if parsed.path == "/api/candidate-label":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                self.send_json(save_candidate_label(payload))
            except Exception as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if parsed.path != "/api/notes":
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            opus_id = str(payload["opus_id"])
            notes = read_notes()
            notes.setdefault("notes", {})[opus_id] = {
                "classification": str(payload.get("classification", "review")),
                "text": str(payload.get("text", ""))[:4000],
                "x": int(payload.get("x", 512)),
                "y": int(payload.get("y", 512)),
            }
            write_notes(notes)
            self.send_json({"saved": True})
        except Exception as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def serve_file(self, path: Path) -> None:
        try:
            resolved = path.resolve()
            allowed = (
                WEB.resolve(),
                (ROOT / "data").resolve(),
                (ROOT / "outputs").resolve(),
                (ROOT / "public_site" / "static-data").resolve(),
                (ROOT / "public_site" / "static-assets").resolve(),
            )
            if not any(resolved == root or root in resolved.parents for root in allowed):
                raise FileNotFoundError
            payload = resolved.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self.send_bytes(payload, content_type)


def run(open_browser: bool = True) -> None:
    if not pipeline.DB_PATH.exists():
        pipeline.run_all()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    display_url = PUBLIC_URL or f"http://{HOST}:{PORT}"
    if open_browser and OPEN_BROWSER and HOST in {"127.0.0.1", "localhost"}:
        threading.Timer(0.7, lambda: webbrowser.open(display_url)).start()
    print(f"Jupiter Lightning Workbench: {display_url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run(open_browser="--no-browser" not in sys.argv)
