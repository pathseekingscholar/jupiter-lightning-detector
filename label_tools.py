from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
LABELS_JSON = OUTPUT_DIR / "candidate_labels.json"
LABELS_CSV = OUTPUT_DIR / "candidate_labels.csv"
TEMPLATE_CSV = OUTPUT_DIR / "candidate_label_template.csv"
VALID_LABELS = {
    "known-lightning",
    "possible-lightning",
    "artifact",
    "cosmic-ray-hot-pixel",
    "uncertain",
}
VALID_CONFIDENCE = {"low", "medium", "high"}


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


def load_label_payload() -> dict[str, object]:
    if not LABELS_JSON.exists():
        return {"labels": {}}
    return json.loads(LABELS_JSON.read_text(encoding="utf-8"))


def write_label_payload(payload: dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LABELS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    labels = sorted(
        payload.get("labels", {}).values(),
        key=lambda row: (row.get("run_date", ""), row.get("candidate_id", "")),
    )
    write_csv(
        LABELS_CSV,
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
            "label",
            "confidence",
            "reviewer",
            "review_note",
            "reviewed_at",
            "updated_at",
        ],
    )


def build_template() -> list[dict[str, object]]:
    matrix = read_csv(OUTPUT_DIR / "review_decision_matrix.csv")
    rows = []
    for row in matrix:
        suggested = row.get("suggested_label", "")
        if row.get("next_action") == "confirm_known_validation_mark":
            suggested = "known-lightning"
        rows.append({
            "review_rank": row.get("review_rank", ""),
            "candidate_id": row.get("candidate_id", ""),
            "image_id": row.get("image_id", ""),
            "image_number": row.get("image_id", "").lstrip("N"),
            "run_date": row.get("run_date", ""),
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "snr": row.get("snr", ""),
            "blob_size": row.get("blob_size", ""),
            "artifact_flags": row.get("artifact_flags", ""),
            "candidate_score": row.get("candidate_score", ""),
            "next_action": row.get("next_action", ""),
            "suggested_label": suggested,
            "human_label": "",
            "confidence": "",
            "reviewer": "",
            "review_note": "",
            "reviewed_at": "",
        })
    return rows


def export_template(path: Path = TEMPLATE_CSV) -> None:
    rows = build_template()
    write_csv(
        path,
        rows,
        [
            "review_rank",
            "candidate_id",
            "image_id",
            "image_number",
            "run_date",
            "x",
            "y",
            "snr",
            "blob_size",
            "artifact_flags",
            "candidate_score",
            "next_action",
            "suggested_label",
            "human_label",
            "confidence",
            "reviewer",
            "review_note",
            "reviewed_at",
        ],
    )
    print(f"Wrote {path}")


def import_labels(path: Path) -> None:
    rows = read_csv(path)
    payload = load_label_payload()
    labels = payload.setdefault("labels", {})
    imported = 0
    skipped = 0
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        human_label = str(row.get("human_label", "")).strip()
        if not human_label:
            skipped += 1
            continue
        if human_label not in VALID_LABELS:
            raise ValueError(f"Invalid label for {row.get('candidate_id')}: {human_label}")
        confidence = str(row.get("confidence", "")).strip() or "medium"
        if confidence not in VALID_CONFIDENCE:
            raise ValueError(f"Invalid confidence for {row.get('candidate_id')}: {confidence}")
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            raise ValueError("Every labeled row must have candidate_id")
        reviewed_at = str(row.get("reviewed_at", "")).strip() or now
        labels[candidate_id] = {
            "run_date": row.get("run_date", ""),
            "candidate_id": candidate_id,
            "image_id": row.get("image_id", ""),
            "image_number": row.get("image_number", str(row.get("image_id", "")).lstrip("N")),
            "x": row.get("x", ""),
            "y": row.get("y", ""),
            "brightness": row.get("snr", ""),
            "blob_size": row.get("blob_size", ""),
            "snr": row.get("snr", ""),
            "artifact_flags": row.get("artifact_flags", ""),
            "candidate_score": row.get("candidate_score", ""),
            "human_label": human_label,
            "label": human_label,
            "confidence": confidence,
            "reviewer": str(row.get("reviewer", "")).strip() or "csv-reviewer",
            "review_note": str(row.get("review_note", ""))[:2000],
            "reviewed_at": reviewed_at,
            "updated_at": reviewed_at,
        }
        imported += 1
    write_label_payload(payload)
    print(f"Imported {imported} labels from {path}; skipped {skipped} unlabeled rows")
    print(f"Wrote {LABELS_JSON}")
    print(f"Wrote {LABELS_CSV}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export or import Jupiter candidate human-review labels.")
    parser.add_argument("command", choices=["template", "import"])
    parser.add_argument("--path", default=str(TEMPLATE_CSV), help="CSV path for template export or label import.")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    if args.command == "template":
        export_template(path)
    else:
        import_labels(path)


if __name__ == "__main__":
    main()
