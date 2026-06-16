from __future__ import annotations

import io
import csv
import json
import mimetypes
import sqlite3
import sys
import traceback
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
from PIL import Image, ImageDraw

import jupiter_pipeline as pipeline


ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
NOTES_PATH = ROOT / "research_notes.json"
HOST = "127.0.0.1"
PORT = 8765
DETECTION_DIR = ROOT / "outputs" / "detection"
DETECTION_STATUS_PATH = DETECTION_DIR / "status.json"
DETECTION_LOCK = threading.Lock()


def read_notes() -> dict:
    if not NOTES_PATH.exists():
        return {"notes": {}}
    return json.loads(NOTES_PATH.read_text(encoding="utf-8"))


def write_notes(payload: dict) -> None:
    NOTES_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def read_detection_rows(limit: int = 150) -> dict:
    review_path = DETECTION_DIR / "review_candidates.csv"
    summary_path = DETECTION_DIR / "summary.json"
    if not review_path.exists():
        return {
            "available": False,
            "summary": {},
            "tracks": [],
            "message": "Run .\\run.ps1 detect to generate candidate detections.",
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
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
            "preview_image": f"/data/previews/N{row['image_number']}_2_full.png",
            "opus_detail_url": f"https://opus.pds-rings.seti.org/#/detail={row['opus_id']}",
        })
    return {
        "available": True,
        "summary": summary,
        "tracks": sorted(tracks.values(), key=lambda item: item["confidence"], reverse=True),
        "csv_url": "/outputs/detection/review_candidates.csv",
        "contact_sheet_url": "/outputs/detection/candidate_contact_sheet.png",
    }


def read_detection_status() -> dict:
    if DETECTION_STATUS_PATH.exists():
        return json.loads(DETECTION_STATUS_PATH.read_text(encoding="utf-8"))
    return {"running": False, "message": "Detector has not been run from this session."}


def write_detection_status(payload: dict) -> None:
    DETECTION_DIR.mkdir(parents=True, exist_ok=True)
    DETECTION_STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_detection_job() -> None:
    with DETECTION_LOCK:
        try:
            write_detection_status({
                "running": True,
                "message": "Running detector: loading OPUS sequence, enhancing frames, finding blobs, filtering artifacts, and linking tracks.",
            })
            import detection_pipeline

            candidates = detection_pipeline.run_detection()
            write_detection_status({
                "running": False,
                "ok": True,
                "message": f"Detector finished. Found {len(candidates)} bright regions; refreshed review cards and contact sheet.",
            })
        except Exception as exc:
            write_detection_status({
                "running": False,
                "ok": False,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            })


def start_detection_job() -> dict:
    current = read_detection_status()
    if current.get("running"):
        return current
    thread = threading.Thread(target=run_detection_job, daemon=True)
    thread.start()
    return {"running": True, "message": "Detector started."}


def validation_payload() -> dict:
    candidates_path = DETECTION_DIR / "candidates.csv"
    known_path = ROOT / "known_events.json"
    if not candidates_path.exists() or not known_path.exists():
        return {"available": False, "message": "Run .\\run.ps1 detect before validating known lightning recovery."}

    with candidates_path.open(newline="", encoding="utf-8") as handle:
        candidates = list(csv.DictReader(handle))
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
                "note": "In current detector sequence" if image_rows else "Not in the January 1 detector sequence",
            })
    recovered = sum(1 for row in results if row["recovered"])
    return {
        "available": True,
        "source": known["source"],
        "results": results,
        "summary": f"{recovered} of {len(results)} published marks recovered in the current detector output.",
    }


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
        parsed = urlparse(self.path)
        if parsed.path == "/api/observations":
            self.send_json(observation_payload())
            return
        if parsed.path == "/api/detection":
            self.send_json(read_detection_rows())
            return
        if parsed.path == "/api/detection-status":
            self.send_json(read_detection_status())
            return
        if parsed.path == "/api/validation":
            self.send_json(validation_payload())
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
        relative = "index.html" if parsed.path in ("", "/") else parsed.path.lstrip("/")
        self.serve_file(WEB / relative)

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/api/run-detection":
            self.send_json(start_detection_job())
            return
        if urlparse(self.path).path != "/api/notes":
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
            allowed = (WEB.resolve(), (ROOT / "data").resolve(), (ROOT / "outputs").resolve())
            if not any(resolved == root or root in resolved.parents for root in allowed):
                raise FileNotFoundError
            payload = resolved.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self.send_bytes(payload, content_type)


def run(open_browser: bool = True) -> None:
    pipeline.run_all()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    if open_browser:
        threading.Timer(0.7, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()
    print(f"Jupiter Lightning Workbench: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run(open_browser="--no-browser" not in sys.argv)
