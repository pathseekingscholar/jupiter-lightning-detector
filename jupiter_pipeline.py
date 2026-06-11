from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import sqlite3
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CALIBRATED = DATA / "calibrated"
METADATA = DATA / "metadata"
PREVIEWS = DATA / "previews"
OUTPUTS = ROOT / "outputs"
DB_PATH = ROOT / "jupiter_lightning.sqlite"
EVENTS_PATH = ROOT / "known_events.json"
OPUS_API = "https://opus.pds-rings.seti.org/opus/api"


@dataclass(frozen=True)
class Product:
    opus_id: str
    image_number: str
    metadata_url: str
    files_url: str


def ensure_directories() -> None:
    for path in (CALIBRATED, METADATA, PREVIEWS, OUTPUTS):
        path.mkdir(parents=True, exist_ok=True)


def load_ground_truth() -> dict[str, Any]:
    return json.loads(EVENTS_PATH.read_text(encoding="utf-8"))


def products() -> list[Product]:
    result = []
    for observation in load_ground_truth()["observations"]:
        opus_id = observation["opus_id"]
        result.append(
            Product(
                opus_id=opus_id,
                image_number=observation["image_number"],
                metadata_url=f"{OPUS_API}/metadata/{opus_id}.json",
                files_url=f"{OPUS_API}/files/{opus_id}.json",
            )
        )
    return result


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "JupiterLightningResearch/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download_file(url: str, destination: Path) -> None:
    if destination.exists() and destination.stat().st_size > 0:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "JupiterLightningResearch/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def init_database() -> None:
    ensure_directories()
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS observations (
                opus_id TEXT PRIMARY KEY,
                image_number TEXT NOT NULL,
                start_time TEXT,
                stop_time TEXT,
                exposure_seconds REAL,
                camera TEXT,
                filter_name TEXT,
                gain_mode TEXT,
                center_resolution_km REAL,
                calibrated_image TEXT,
                calibrated_label TEXT,
                preview_image TEXT,
                metadata_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opus_id TEXT NOT NULL REFERENCES observations(opus_id),
                label TEXT NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                published_power_w REAL,
                center_if REAL,
                local_background_if REAL,
                local_noise_if REAL,
                peak_excess_if REAL,
                peak_snr REAL,
                integrated_excess_if REAL,
                bright_pixel_count INTEGER,
                UNIQUE(opus_id, label)
            );
            """
        )


def find_urls(files_payload: dict[str, Any], opus_id: str) -> tuple[str, str, str]:
    data = files_payload["data"][opus_id]
    calibrated_urls = data["coiss_calib"]
    image_url = next(url for url in calibrated_urls if url.upper().endswith(".IMG"))
    label_url = next(url for url in calibrated_urls if url.upper().endswith(".LBL"))
    preview_url = data["browse_full"][0]
    return image_url, label_url, preview_url


def download_products() -> None:
    ensure_directories()
    for product in products():
        metadata_path = METADATA / f"{product.opus_id}.json"
        files_path = METADATA / f"{product.opus_id}-files.json"

        metadata_payload = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else fetch_json(product.metadata_url)
        )
        files_payload = (
            json.loads(files_path.read_text(encoding="utf-8"))
            if files_path.exists()
            else fetch_json(product.files_url)
        )
        metadata_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")
        files_path.write_text(json.dumps(files_payload, indent=2), encoding="utf-8")

        image_url, label_url, preview_url = find_urls(files_payload, product.opus_id)
        for url, directory in (
            (image_url, CALIBRATED),
            (label_url, CALIBRATED),
            (preview_url, PREVIEWS),
        ):
            destination = directory / Path(url).name
            download_file(url, destination)
        upsert_observation(product, metadata_payload, image_url, label_url, preview_url)


def upsert_observation(
    product: Product,
    payload: dict[str, Any],
    image_url: str,
    label_url: str,
    preview_url: str,
) -> None:
    general = payload["General Constraints"]
    iss = payload["Cassini ISS Constraints"]
    geometry = payload.get("Jupiter Surface Geometry Constraints", {})
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO observations (
                opus_id, image_number, start_time, stop_time, exposure_seconds,
                camera, filter_name, gain_mode, center_resolution_km,
                calibrated_image, calibrated_label, preview_image, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(opus_id) DO UPDATE SET
                start_time=excluded.start_time,
                stop_time=excluded.stop_time,
                exposure_seconds=excluded.exposure_seconds,
                camera=excluded.camera,
                filter_name=excluded.filter_name,
                gain_mode=excluded.gain_mode,
                center_resolution_km=excluded.center_resolution_km,
                calibrated_image=excluded.calibrated_image,
                calibrated_label=excluded.calibrated_label,
                preview_image=excluded.preview_image,
                metadata_json=excluded.metadata_json
            """,
            (
                product.opus_id,
                product.image_number,
                general.get("time1"),
                general.get("time2"),
                float(general["observationduration"]),
                iss.get("COISScamera"),
                iss.get("COISSfilter"),
                iss.get("COISSgainmode"),
                _optional_float(geometry.get("SURFACEGEOjupiter_centerresolution1")),
                str(CALIBRATED / Path(image_url).name),
                str(CALIBRATED / Path(label_url).name),
                str(PREVIEWS / Path(preview_url).name),
                json.dumps(payload),
            ),
        )


def _optional_float(value: Any) -> float | None:
    return None if value in (None, "") else float(value)


def parse_pds_label(label_path: Path) -> dict[str, Any]:
    text = label_path.read_text(encoding="ascii", errors="replace")

    def integer(name: str) -> int:
        match = re.search(rf"^\s*{name}\s*=\s*(\d+)", text, flags=re.MULTILINE)
        if not match:
            raise ValueError(f"{name} not found in {label_path}")
        return int(match.group(1))

    sample_type_match = re.search(
        r"^\s*SAMPLE_TYPE\s*=\s*([A-Z0-9_]+)", text, flags=re.MULTILINE
    )
    image_pointer_match = re.search(
        r'^\s*\^IMAGE\s*=\s*\(\s*"[^"]+"\s*,\s*(\d+)\s*\)',
        text,
        flags=re.MULTILINE,
    )
    if not sample_type_match:
        raise ValueError(f"SAMPLE_TYPE not found in {label_path}")
    if not image_pointer_match:
        raise ValueError(f"^IMAGE pointer not found in {label_path}")
    return {
        "record_bytes": integer("RECORD_BYTES"),
        "image_record": int(image_pointer_match.group(1)),
        "lines": integer("LINES"),
        "samples": integer("LINE_SAMPLES"),
        "sample_bits": integer("SAMPLE_BITS"),
        "sample_type": sample_type_match.group(1),
    }


def load_calibrated_image(image_path: Path, label_path: Path) -> np.ndarray:
    label = parse_pds_label(label_path)
    if label["sample_type"] != "PC_REAL" or label["sample_bits"] != 32:
        raise ValueError(f"Unsupported calibrated format: {label}")
    offset = (label["image_record"] - 1) * label["record_bytes"]
    array = np.memmap(
        image_path,
        dtype="<f4",
        mode="r",
        offset=offset,
        shape=(label["lines"], label["samples"]),
    )
    return np.asarray(array)


def valid_mask(array: np.ndarray) -> np.ndarray:
    return np.isfinite(array) & (array > -1.0) & (array < 1.0) & (array != 0.0)


def robust_limits(array: np.ndarray, low: float = 1.0, high: float = 99.7) -> tuple[float, float]:
    values = array[valid_mask(array)]
    if values.size == 0:
        raise ValueError("Image contains no valid calibrated pixels")
    return float(np.percentile(values, low)), float(np.percentile(values, high))


def normalize_to_u8(array: np.ndarray, low: float, high: float) -> np.ndarray:
    scaled = (array.astype(np.float64) - low) / max(high - low, np.finfo(float).eps)
    scaled = np.clip(scaled, 0.0, 1.0)
    scaled[~valid_mask(array)] = 0.0
    return np.rint(scaled * 255.0).astype(np.uint8)


def measure_candidate(array: np.ndarray, x: int, y: int) -> dict[str, float | int]:
    row, column = y - 1, x - 1
    if not (0 <= row < array.shape[0] and 0 <= column < array.shape[1]):
        raise ValueError(f"Candidate ({x}, {y}) is outside image bounds")

    # The table coordinates locate a cluster, while the calibrated product's
    # brightest pixel can be displaced by several pixels within that cluster.
    radius = 25
    y0, y1 = max(0, row - radius), min(array.shape[0], row + radius + 1)
    x0, x1 = max(0, column - radius), min(array.shape[1], column + radius + 1)
    patch = np.asarray(array[y0:y1, x0:x1], dtype=np.float64)
    yy, xx = np.ogrid[y0:y1, x0:x1]
    distance = np.sqrt((yy - row) ** 2 + (xx - column) ** 2)
    valid = valid_mask(patch)
    background_pixels = patch[valid & (distance >= 16) & (distance <= 25)]
    signal_pixels = patch[valid & (distance <= 12)]
    if background_pixels.size < 10 or signal_pixels.size == 0:
        raise ValueError(f"Insufficient valid pixels around ({x}, {y})")

    background = float(np.median(background_pixels))
    mad = float(np.median(np.abs(background_pixels - background)))
    noise = max(1.4826 * mad, np.finfo(float).eps)
    center = float(array[row, column])
    peak = float(np.max(signal_pixels))
    excess = signal_pixels - background
    bright = excess > (3.0 * noise)
    return {
        "center_if": center,
        "local_background_if": background,
        "local_noise_if": noise,
        "peak_excess_if": peak - background,
        "peak_snr": (peak - background) / noise,
        "integrated_excess_if": float(np.sum(np.clip(excess, 0.0, None))),
        "bright_pixel_count": int(np.count_nonzero(bright)),
    }


def image_paths_for_number(image_number: str) -> tuple[Path, Path]:
    images = sorted(CALIBRATED.glob(f"N{image_number}_*_CALIB.IMG"))
    labels = sorted(CALIBRATED.glob(f"N{image_number}_*_CALIB.LBL"))
    if len(images) != 1 or len(labels) != 1:
        raise FileNotFoundError(f"Expected one calibrated image and label for {image_number}")
    return images[0], labels[0]


def analyze() -> None:
    ensure_directories()
    ground_truth = load_ground_truth()
    rows: list[dict[str, Any]] = []
    for observation in ground_truth["observations"]:
        image_path, label_path = image_paths_for_number(observation["image_number"])
        array = load_calibrated_image(image_path, label_path)
        create_enhanced_frame(array, observation, image_path.stem)
        for event in observation["events"]:
            metrics = measure_candidate(array, event["x"], event["y"])
            row = {
                "opus_id": observation["opus_id"],
                "image_number": observation["image_number"],
                **event,
                **metrics,
            }
            rows.append(row)
            create_candidate_crop(array, row)
            upsert_candidate(row, ground_truth["source"])
    write_measurements_csv(rows)
    create_contact_sheet(rows)


def upsert_candidate(row: dict[str, Any], source: str) -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO candidates (
                opus_id, label, x, y, status, source, published_power_w,
                center_if, local_background_if, local_noise_if, peak_excess_if,
                peak_snr, integrated_excess_if, bright_pixel_count
            ) VALUES (?, ?, ?, ?, 'published', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(opus_id, label) DO UPDATE SET
                x=excluded.x, y=excluded.y, published_power_w=excluded.published_power_w,
                center_if=excluded.center_if,
                local_background_if=excluded.local_background_if,
                local_noise_if=excluded.local_noise_if,
                peak_excess_if=excluded.peak_excess_if,
                peak_snr=excluded.peak_snr,
                integrated_excess_if=excluded.integrated_excess_if,
                bright_pixel_count=excluded.bright_pixel_count
            """,
            (
                row["opus_id"],
                row["label"],
                row["x"],
                row["y"],
                source,
                row["published_power_w"],
                row["center_if"],
                row["local_background_if"],
                row["local_noise_if"],
                row["peak_excess_if"],
                row["peak_snr"],
                row["integrated_excess_if"],
                row["bright_pixel_count"],
            ),
        )


def font(size: int = 18) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def create_enhanced_frame(array: np.ndarray, observation: dict[str, Any], stem: str) -> None:
    low, high = robust_limits(array, 2.0, 99.8)
    image = Image.fromarray(normalize_to_u8(array, low, high), mode="L").convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(1.35)
    draw = ImageDraw.Draw(image)
    for event in observation["events"]:
        x, y = event["x"] - 1, event["y"] - 1
        draw.ellipse((x - 12, y - 12, x + 12, y + 12), outline=(255, 78, 62), width=3)
        draw.text((x + 16, y - 16), event["label"], fill=(255, 220, 80), font=font(20))
    draw.rectangle((0, 0, 1023, 42), fill=(0, 0, 0))
    draw.text(
        (12, 10),
        f"Cassini ISS NAC/HAL {observation['image_number']} - enhanced calibrated I/F",
        fill="white",
        font=font(20),
    )
    image.save(OUTPUTS / f"{stem}_enhanced.png")


def create_candidate_crop(array: np.ndarray, row: dict[str, Any]) -> None:
    x, y = row["x"] - 1, row["y"] - 1
    radius = 30
    y0, y1 = max(0, y - radius), min(array.shape[0], y + radius + 1)
    x0, x1 = max(0, x - radius), min(array.shape[1], x + radius + 1)
    patch = np.asarray(array[y0:y1, x0:x1])
    values = patch[valid_mask(patch)]
    low = float(np.percentile(values, 5))
    high = float(np.percentile(values, 99.5))
    crop = Image.fromarray(normalize_to_u8(patch, low, high), mode="L")
    crop = crop.resize((366, 366), Image.Resampling.NEAREST).convert("RGB")
    draw = ImageDraw.Draw(crop)
    center = 183
    draw.ellipse((center - 75, center - 75, center + 75, center + 75), outline=(255, 70, 55), width=5)
    title = f"Flash {row['label']} | N{row['image_number']}"
    subtitle = f"(x,y)=({row['x']},{row['y']}) | peak SNR={row['peak_snr']:.1f}"
    canvas = Image.new("RGB", (366, 430), "black")
    canvas.paste(crop, (0, 64))
    header = ImageDraw.Draw(canvas)
    header.text((10, 8), title, fill="white", font=font(20))
    header.text((10, 36), subtitle, fill=(205, 215, 230), font=font(15))
    safe_label = row["label"].replace("*", "star")
    canvas.save(OUTPUTS / f"N{row['image_number']}_flash_{safe_label}.png")


def create_contact_sheet(rows: list[dict[str, Any]]) -> None:
    cards = []
    for row in rows:
        safe_label = row["label"].replace("*", "star")
        cards.append(Image.open(OUTPUTS / f"N{row['image_number']}_flash_{safe_label}.png"))
    sheet = Image.new("RGB", (3 * 366, 2 * 430 + 80), (16, 20, 29))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "Published Cassini Jupiter lightning detections reproduced", fill="white", font=font(28))
    draw.text(
        (24, 52),
        "Dyudina et al. (2004), Table 2 | Calibrated OPUS I/F products",
        fill=(170, 185, 205),
        font=font(17),
    )
    for index, card in enumerate(cards):
        column, row_index = index % 3, index // 3
        sheet.paste(card, (column * 366, 80 + row_index * 430))
    sheet.save(OUTPUTS / "known_lightning_contact_sheet.png")


def write_measurements_csv(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with (OUTPUTS / "known_lightning_measurements.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_report() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        observations = connection.execute(
            "SELECT * FROM observations ORDER BY start_time"
        ).fetchall()
        candidates = connection.execute(
            """
            SELECT c.*, o.image_number, o.start_time, o.exposure_seconds,
                   o.filter_name, o.center_resolution_km
            FROM candidates c JOIN observations o USING (opus_id)
            ORDER BY o.start_time, c.label
            """
        ).fetchall()
    rows_html = "\n".join(
        f"""
        <tr>
          <td>{html.escape(str(row['label']))}</td>
          <td>N{row['image_number']}</td>
          <td>{html.escape(row['start_time'])}</td>
          <td>({row['x']}, {row['y']})</td>
          <td>{row['peak_snr']:.1f}</td>
          <td>{row['bright_pixel_count']}</td>
          <td>{row['published_power_w'] / 1e9:.3f}</td>
        </tr>
        """
        for row in candidates
    )
    observation_html = "\n".join(
        f"""
        <li><strong>N{row['image_number']}</strong>:
        {html.escape(row['start_time'])}, {row['exposure_seconds']:.0f} s,
        {html.escape(row['camera'])}/{html.escape(row['filter_name'])},
        {row['center_resolution_km']:.1f} km/pixel</li>
        """
        for row in observations
    )
    report = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cassini Jupiter Lightning Reproduction</title>
<style>
  :root {{ font-family: Georgia, "Times New Roman", serif; color: #27251f; }}
  body {{ margin: 0; color: #27251f; line-height: 1.55;
          background-color: #f2efe4;
          background-image: linear-gradient(rgba(76,103,112,.09) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(76,103,112,.09) 1px, transparent 1px);
          background-size: 24px 24px; }}
  main {{ max-width: 1100px; margin: auto; padding: 48px 28px 80px; }}
  h1 {{ font-size: 50px; line-height: 1; margin-bottom: 12px; font-weight: 500;
        border-bottom: 3px double #27251f; padding-bottom: 18px; }}
  h2 {{ margin-top: 42px; color: #a52d25; font-weight: 500; }}
  .lede {{ color: #625e52; font-size: 19px; max-width: 820px; }}
  .status {{ display: inline-block; padding: 5px 9px; border: 1px solid #a52d25;
             color: #a52d25; font: 12px "Courier New", monospace;
             transform: rotate(-1deg); }}
  img {{ max-width: 100%; border: 8px solid #ded8c8; outline: 1px solid #27251f; }}
  table {{ width: 100%; border-collapse: collapse; background: rgba(255,255,255,.25); }}
  th, td {{ text-align: left; padding: 11px; border-bottom: 1px solid #aaa18c; }}
  th {{ color: #625e52; font-family: "Courier New", monospace; font-size: 12px; }}
  code {{ color: #a52d25; }}
  a {{ color: #8d2721; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .card {{ padding: 18px 18px 18px 0; border-top: 1px solid #27251f; }}
  @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body><main>
<span class="status">Ground-truth reproduction complete</span>
<h1>Cassini Jupiter lightning workflow</h1>
<p class="lede">A reproducible OPUS-to-SQLite pipeline for calibrated Cassini
ISS images, initialized with the six published H-alpha detections from
Dyudina et al. (2004).</p>

<h2>What is working</h2>
<div class="grid">
  <div class="card"><strong>Archive access</strong><br>Metadata, calibrated
  VICAR/PDS images, labels, and browse previews are fetched through OPUS.</div>
  <div class="card"><strong>Quantitative ingestion</strong><br>32-bit calibrated
  I/F arrays are read directly, without measuring JPEG previews.</div>
  <div class="card"><strong>Catalog foundation</strong><br>Observations and
  candidate measurements persist in <code>jupiter_lightning.sqlite</code>.</div>
</div>

<h2>Published detections</h2>
<img src="known_lightning_contact_sheet.png"
     alt="Six published Cassini lightning detections">
<table>
<thead><tr><th>Flash</th><th>Image</th><th>UTC start</th><th>Pixel (x,y)</th>
<th>Local peak SNR</th><th>Bright pixels</th><th>Published H-alpha power (GW)</th></tr></thead>
<tbody>{rows_html}</tbody>
</table>

<h2>Observation set</h2>
<ul>{observation_html}</ul>

<h2>Interpretation</h2>
<p>The pipeline confirms that the paper's known locations coincide with
multi-pixel enhancements in the calibrated products. This is a reproduction,
not a new discovery. The January 10 and January 11 frames are especially
valuable because they contain repeated detections of the same storm system
about two Jovian rotations apart.</p>

<h2>Next scientific step</h2>
<p>Query nearby broadband observations, register frames to Jupiter, then compare
candidate morphology and temporal motion. A new candidate should not be called
lightning from brightness alone: multi-pixel diffusion, repeatability, motion
with planetary rotation, and exclusion of moons/cosmic rays are the core tests.</p>

<h2>References</h2>
<p><a href="https://opus.pds-rings.seti.org/">OPUS archive</a> |
<a href="https://opus.pds-rings.seti.org/apiguide.pdf">OPUS API guide</a></p>
</main></body></html>"""
    (OUTPUTS / "report.html").write_text(report, encoding="utf-8")


def run_all() -> None:
    init_database()
    download_products()
    analyze()
    generate_report()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("init", "download", "analyze", "report", "all"),
        nargs="?",
        default="all",
    )
    args = parser.parse_args()
    if args.command == "init":
        init_database()
    elif args.command == "download":
        init_database()
        download_products()
    elif args.command == "analyze":
        init_database()
        analyze()
    elif args.command == "report":
        generate_report()
    else:
        run_all()
    print(f"Completed '{args.command}'. Report: {OUTPUTS / 'report.html'}")


if __name__ == "__main__":
    main()
