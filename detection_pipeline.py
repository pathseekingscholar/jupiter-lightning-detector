from __future__ import annotations

import argparse
import csv
import json
import math
import time
import urllib.error
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import jupiter_pipeline as jp


DETECTION_DIR = jp.OUTPUTS / "detection"
SEQUENCES_DIR = jp.DATA / "sequences"
DETECTION_RUNS = {
    "2001-01-01": {
        "label": "January 1, 2001 NAC/H-alpha",
        "time1": "2001-01-01T00:00:00",
        "time2": "2001-01-01T23:59:59",
    },
    "2001-01-10": {
        "label": "January 10, 2001 NAC/H-alpha",
        "time1": "2001-01-10T00:00:00",
        "time2": "2001-01-10T23:59:59",
    },
    "2001-01-11": {
        "label": "January 11, 2001 NAC/H-alpha",
        "time1": "2001-01-11T00:00:00",
        "time2": "2001-01-11T23:59:59",
    },
}
DEFAULT_RUN_DATE = "2001-01-01"


@dataclass
class Candidate:
    candidate_id: str
    frame_index: int
    opus_id: str
    image_number: str
    time: str
    x: float
    y: float
    area: int
    peak_snr: float
    mean_snr: float
    integrated_snr: float
    sharpness: float
    elongation: float
    flags: list[str]
    track_id: str = ""
    track_length: int = 1
    confidence: float = 0.0
    reason: str = ""


def ensure_dirs() -> None:
    for path in (DETECTION_DIR, SEQUENCES_DIR, jp.CALIBRATED, jp.PREVIEWS, jp.METADATA):
        path.mkdir(parents=True, exist_ok=True)


def fetch_json(url: str, attempts: int = 4) -> Any:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return jp.fetch_json(url)
        except (urllib.error.URLError, ConnectionResetError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError(f"Could not fetch {url}")


def download_file(url: str, destination: Path, attempts: int = 4) -> None:
    if destination.exists():
        return
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            jp.download_file(url, destination)
            return
        except (urllib.error.URLError, ConnectionResetError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError(f"Could not download {url}")


def run_config(run_date: str) -> dict[str, str]:
    if run_date not in DETECTION_RUNS:
        raise ValueError(f"Unknown detector run date: {run_date}")
    return DETECTION_RUNS[run_date]


def sequence_path(run_date: str) -> Path:
    return SEQUENCES_DIR / f"{run_date}_nac_hal.json"


def output_dir(run_date: str) -> Path:
    return DETECTION_DIR / run_date


def query_sequence(run_date: str = DEFAULT_RUN_DATE) -> list[dict[str, str]]:
    ensure_dirs()
    config = run_config(run_date)
    params = {
        "instrument": "Cassini ISS",
        "planet": "Jupiter",
        "target": "Jupiter",
        "COISScamera": "Narrow Angle",
        "COISSfilter": "HAL",
        "time1": config["time1"],
        "time2": config["time2"],
        "cols": "opusid,time1,observationduration,COISScamera,COISSfilter,COISSimagenumber,SURFACEGEOjupiter_centerresolution",
        "order": "time1,opusid",
        "limit": "200",
    }
    payload = fetch_json(f"{jp.OPUS_API}/data.json?{urlencode(params)}")
    keys = [
        "opus_id",
        "time",
        "duration_seconds",
        "camera",
        "filter",
        "image_number",
        "center_resolution_km_px",
    ]
    sequence = [dict(zip(keys, row)) for row in payload["page"]]
    sequence_path(run_date).write_text(json.dumps(sequence, indent=2), encoding="utf-8")
    return sequence


def load_sequence(run_date: str = DEFAULT_RUN_DATE) -> list[dict[str, str]]:
    path = sequence_path(run_date)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return query_sequence(run_date)


def download_sequence(sequence: list[dict[str, str]]) -> None:
    ensure_dirs()
    for item in sequence:
        opus_id = item["opus_id"]
        metadata_path = jp.METADATA / f"{opus_id}.json"
        files_path = jp.METADATA / f"{opus_id}-files.json"
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else fetch_json(f"{jp.OPUS_API}/metadata/{opus_id}.json")
        )
        files = (
            json.loads(files_path.read_text(encoding="utf-8"))
            if files_path.exists()
            else fetch_json(f"{jp.OPUS_API}/files/{opus_id}.json")
        )
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        files_path.write_text(json.dumps(files, indent=2), encoding="utf-8")
        image_url, label_url, preview_url = jp.find_urls(files, opus_id)
        for url, directory in (
            (image_url, jp.CALIBRATED),
            (label_url, jp.CALIBRATED),
            (preview_url, jp.PREVIEWS),
        ):
            download_file(url, directory / Path(url).name)


def paths_for_item(item: dict[str, str]) -> tuple[Path, Path]:
    return jp.image_paths_for_number(item["image_number"])


def highpass_snr(array: np.ndarray, blur_radius: float = 18.0) -> tuple[np.ndarray, np.ndarray]:
    valid = jp.valid_mask(array)
    values = array[valid]
    lo, hi = np.percentile(values, [2, 99.8])
    norm = np.clip((array.astype(np.float64) - lo) / max(hi - lo, np.finfo(float).eps), 0, 1)
    fill = float(np.median(norm[valid]))
    norm[~valid] = fill
    image = Image.fromarray(np.rint(norm * 255).astype(np.uint8), mode="L")
    background = np.asarray(image.filter(ImageFilter.GaussianBlur(radius=blur_radius)), dtype=np.float64) / 255.0
    residual = norm - background
    residual_valid = residual[valid]
    center = float(np.median(residual_valid))
    mad = float(np.median(np.abs(residual_valid - center)))
    sigma = max(1.4826 * mad, np.finfo(float).eps)
    return (residual - center) / sigma, valid


def connected_components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    seen = np.zeros(mask.shape, dtype=bool)
    components: list[list[tuple[int, int]]] = []
    height, width = mask.shape
    for row, col in zip(*np.where(mask)):
        if seen[row, col]:
            continue
        queue = deque([(int(row), int(col))])
        seen[row, col] = True
        component: list[tuple[int, int]] = []
        while queue:
            y, x = queue.popleft()
            component.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < height and 0 <= xx < width and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        queue.append((yy, xx))
        components.append(component)
    return components


def component_candidate(
    item: dict[str, str],
    frame_index: int,
    component: list[tuple[int, int]],
    snr: np.ndarray,
    serial: int,
) -> Candidate:
    coords = np.array(component)
    rows = coords[:, 0]
    cols = coords[:, 1]
    weights = np.clip(snr[rows, cols], 0.1, None)
    y = float(np.average(rows + 1, weights=weights))
    x = float(np.average(cols + 1, weights=weights))
    peak_snr = float(np.max(snr[rows, cols]))
    mean_snr = float(np.mean(snr[rows, cols]))
    integrated_snr = float(np.sum(snr[rows, cols]))
    area = int(len(component))
    sharpness = float(peak_snr / max(mean_snr, np.finfo(float).eps))

    centered = np.column_stack([cols - np.mean(cols), rows - np.mean(rows)])
    if area >= 3:
        covariance = np.cov(centered, rowvar=False)
        eig = np.linalg.eigvalsh(covariance)
        elongation = float(math.sqrt(max(eig[-1], 0.0) / max(eig[0], 1e-6)))
    else:
        elongation = 99.0

    flags = []
    if area <= 1:
        flags.append("single_pixel")
    if area < 3:
        flags.append("too_small")
    if sharpness > 3.5 and area <= 3:
        flags.append("sharp_cosmic_ray_like")
    if elongation > 8 and area >= 3:
        flags.append("streak_like")

    return Candidate(
        candidate_id=f"{item['image_number']}-{serial:04d}",
        frame_index=frame_index,
        opus_id=item["opus_id"],
        image_number=item["image_number"],
        time=item["time"],
        x=x,
        y=y,
        area=area,
        peak_snr=peak_snr,
        mean_snr=mean_snr,
        integrated_snr=integrated_snr,
        sharpness=sharpness,
        elongation=elongation,
        flags=flags,
    )


def detect_frame(item: dict[str, str], frame_index: int, threshold: float = 7.0) -> list[Candidate]:
    image_path, label_path = paths_for_item(item)
    array = jp.load_calibrated_image(image_path, label_path)
    snr, valid = highpass_snr(array)
    mask = (snr >= threshold) & valid
    # Avoid the border, where missing lines and browse artifacts dominate.
    mask[:3, :] = False
    mask[-3:, :] = False
    mask[:, :3] = False
    mask[:, -3:] = False
    candidates = []
    for serial, component in enumerate(connected_components(mask), start=1):
        if len(component) > 500:
            continue
        candidate = component_candidate(item, frame_index, component, snr, serial)
        # Keep small events but mark them; single-pixel events are useful as negatives.
        if candidate.peak_snr >= threshold:
            candidates.append(candidate)
    return candidates


def is_reviewable(candidate: Candidate) -> bool:
    bad_flags = {"single_pixel", "too_small", "sharp_cosmic_ray_like", "streak_like"}
    return candidate.area >= 3 and candidate.peak_snr >= 8 and not bad_flags.intersection(candidate.flags)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def link_tracks(candidates: list[Candidate], max_displacement: float = 85.0, max_minutes: float = 12.0) -> None:
    by_frame: dict[int, list[Candidate]] = {}
    for candidate in candidates:
        if not is_reviewable(candidate):
            candidate.track_id = f"U{candidate.frame_index:03d}"
            candidate.track_length = 1
            candidate.confidence = score_track([candidate])
            candidate.reason = explain_track([candidate])
            continue
        by_frame.setdefault(candidate.frame_index, []).append(candidate)

    tracks: list[list[Candidate]] = []
    for frame_index in sorted(by_frame):
        for candidate in by_frame[frame_index]:
            best_track = None
            best_distance = max_displacement
            for track in tracks:
                last = track[-1]
                gap = candidate.frame_index - last.frame_index
                if gap < 1:
                    continue
                minutes = (parse_time(candidate.time) - parse_time(last.time)).total_seconds() / 60.0
                if minutes <= 0 or minutes > max_minutes:
                    continue
                distance = math.hypot(candidate.x - last.x, candidate.y - last.y)
                if distance <= best_distance:
                    best_track = track
                    best_distance = distance
            if best_track is None:
                tracks.append([candidate])
            else:
                best_track.append(candidate)

    for track_index, track in enumerate(tracks, start=1):
        track_id = f"T{track_index:04d}"
        score = score_track(track)
        reason = explain_track(track)
        for candidate in track:
            candidate.track_id = track_id
            candidate.track_length = len(track)
            candidate.confidence = score
            candidate.reason = reason


def score_track(track: list[Candidate]) -> float:
    persistence = min(len(track) / 4.0, 1.0)
    areas = [candidate.area for candidate in track]
    diffuse = min(np.median(areas) / 8.0, 1.0)
    snr_score = min(np.median([candidate.peak_snr for candidate in track]) / 25.0, 1.0)
    artifact_penalty = np.mean([0.0 if is_reviewable(candidate) else 1.0 for candidate in track])
    if len(track) >= 3:
        dx = np.diff([candidate.x for candidate in track])
        dy = np.diff([candidate.y for candidate in track])
        speed = np.hypot(dx, dy)
        motion = 1.0 - min(float(np.std(speed)) / max(float(np.mean(speed)), 1.0), 1.0)
    elif len(track) == 2:
        motion = 0.45
    else:
        motion = 0.0
    score = 0.35 * persistence + 0.25 * motion + 0.20 * diffuse + 0.15 * snr_score - 0.45 * artifact_penalty
    return float(max(0.0, min(1.0, score)))


def explain_track(track: list[Candidate]) -> str:
    bits = [f"{len(track)} frame(s)"]
    median_area = float(np.median([candidate.area for candidate in track]))
    bits.append(f"median area {median_area:.1f} px")
    if len(track) >= 2:
        dx = track[-1].x - track[0].x
        dy = track[-1].y - track[0].y
        bits.append(f"net motion dx={dx:.1f}, dy={dy:.1f}")
    all_flags = sorted({flag for candidate in track for flag in candidate.flags})
    bits.append("flags: " + (", ".join(all_flags) if all_flags else "none"))
    return "; ".join(bits)


def draw_candidate_sheet(sequence: list[dict[str, str]], candidates: list[Candidate], directory: Path) -> None:
    ranked = [candidate for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True) if is_reviewable(candidate)][:24]
    cards = []
    for candidate in ranked:
        preview = jp.PREVIEWS / f"N{candidate.image_number}_2_full.png"
        if not preview.exists():
            continue
        image = Image.open(preview).convert("RGB")
        radius = 42
        cx, cy = int(round(candidate.x)) - 1, int(round(candidate.y)) - 1
        crop = image.crop((max(0, cx - radius), max(0, cy - radius), min(1024, cx + radius), min(1024, cy + radius)))
        crop = crop.resize((160, 160), Image.Resampling.NEAREST)
        card = Image.new("RGB", (260, 220), "white")
        card.paste(crop, (0, 0))
        draw = ImageDraw.Draw(card)
        draw.ellipse((75, 75, 85, 85), outline=(190, 0, 0), width=2)
        text = [
            f"{candidate.track_id} {candidate.candidate_id}",
            f"conf {candidate.confidence:.2f} len {candidate.track_length}",
            f"x={candidate.x:.1f} y={candidate.y:.1f}",
            f"area={candidate.area} snr={candidate.peak_snr:.1f}",
        ]
        y = 164
        for line in text:
            draw.text((5, y), line, fill=(0, 0, 0), font=ImageFont.load_default())
            y += 13
        cards.append(card)
    if not cards:
        return
    cols = 4
    rows = math.ceil(len(cards) / cols)
    sheet = Image.new("RGB", (cols * 260, rows * 220), (235, 232, 222))
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % cols) * 260, (index // cols) * 220))
    sheet.save(directory / "candidate_contact_sheet.png")


def write_outputs(run_date: str, sequence: list[dict[str, str]], candidates: list[Candidate]) -> None:
    directory = output_dir(run_date)
    directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for candidate in sorted(candidates, key=lambda item: item.confidence, reverse=True):
        rows.append({
            "track_id": candidate.track_id,
            "candidate_id": candidate.candidate_id,
            "confidence": f"{candidate.confidence:.4f}",
            "track_length": candidate.track_length,
            "frame_index": candidate.frame_index,
            "opus_id": candidate.opus_id,
            "image_number": candidate.image_number,
            "time": candidate.time,
            "x": f"{candidate.x:.2f}",
            "y": f"{candidate.y:.2f}",
            "area_px": candidate.area,
            "peak_snr": f"{candidate.peak_snr:.2f}",
            "mean_snr": f"{candidate.mean_snr:.2f}",
            "integrated_snr": f"{candidate.integrated_snr:.2f}",
            "sharpness": f"{candidate.sharpness:.2f}",
            "elongation": f"{candidate.elongation:.2f}",
            "flags": "|".join(candidate.flags),
            "reason": candidate.reason,
        })
    with (directory / "candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["track_id"])
        writer.writeheader()
        writer.writerows(rows)
    review_rows = [row for row in rows if not row["flags"] and float(row["confidence"]) >= 0.25]
    with (directory / "review_candidates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["track_id"])
        writer.writeheader()
        writer.writerows(review_rows)
    summary = {
        "sequence": f"Cassini ISS NAC/HAL Jupiter, {run_date}",
        "run_date": run_date,
        "label": run_config(run_date)["label"],
        "frames": len(sequence),
        "candidates": len(candidates),
        "review_candidates": len(review_rows),
        "tracks": len({candidate.track_id for candidate in candidates}),
        "top_candidates": rows[:12],
        "top_review_candidates": review_rows[:12],
        "note": "This is a first-pass classical CV ranking, not a confirmed lightning catalog.",
    }
    (directory / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    draw_candidate_sheet(sequence, candidates, directory)


def run_detection(run_date: str = DEFAULT_RUN_DATE, limit: int | None = None) -> list[Candidate]:
    ensure_dirs()
    sequence = load_sequence(run_date)
    if limit:
        sequence = sequence[:limit]
    download_sequence(sequence)
    candidates: list[Candidate] = []
    for frame_index, item in enumerate(sequence):
        candidates.extend(detect_frame(item, frame_index))
    link_tracks(candidates)
    write_outputs(run_date, sequence, candidates)
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["query", "download", "detect"], nargs="?", default="detect")
    parser.add_argument("--date", choices=list(DETECTION_RUNS), default=DEFAULT_RUN_DATE)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    sequence = query_sequence(args.date) if args.command == "query" else load_sequence(args.date)
    if args.command == "download":
        if args.limit:
            sequence = sequence[: args.limit]
        download_sequence(sequence)
        print(f"Downloaded {len(sequence)} observations")
    elif args.command == "detect":
        candidates = run_detection(run_date=args.date, limit=args.limit)
        print(f"Detected {len(candidates)} candidate regions")
        print(output_dir(args.date) / "candidates.csv")
    else:
        print(f"Wrote {sequence_path(args.date)} with {len(sequence)} observations")


if __name__ == "__main__":
    main()
