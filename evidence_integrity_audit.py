from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image

import jupiter_pipeline as pipeline


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
AUDIT_CSV = OUTPUT_DIR / "evidence_integrity_audit.csv"
AUDIT_MD = OUTPUT_DIR / "evidence_integrity_audit.md"


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


def audit_row(check: str, status: str, value: object, expected: object, evidence: str, next_action: str) -> dict[str, object]:
    return {
        "check": check,
        "status": status,
        "value": value,
        "expected": expected,
        "evidence_file": evidence,
        "next_action": next_action,
    }


def parse_crop_url(crop_url: str) -> dict[str, str]:
    parsed = urlparse(crop_url)
    query = parse_qs(parsed.query)
    return {key: values[0] for key, values in query.items() if values}


def image_exists(image_id: str) -> bool:
    image_number = image_id.lstrip("N")
    image_path, label_path = pipeline.image_paths_for_number(image_number)
    return image_path.exists() and label_path.exists()


def artifact_valid(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except OSError:
        return False


def build_audit_rows() -> list[dict[str, object]]:
    dossier = read_csv(OUTPUT_DIR / "candidate_review_dossier.csv")
    plan = read_csv(OUTPUT_DIR / "first_pass_review_plan.csv")
    blind_packet = read_csv(OUTPUT_DIR / "blind_review_packet.csv")
    blind_key = read_csv(OUTPUT_DIR / "blind_review_key.csv")
    blind_reconciliation = read_csv(OUTPUT_DIR / "blind_review_reconciliation.csv")
    blind_import = read_csv(OUTPUT_DIR / "blind_review_label_import.csv")
    known_batch = read_csv(OUTPUT_DIR / "review_batches" / "01_known_validation_positive.csv")
    negative_batch = read_csv(OUTPUT_DIR / "review_batches" / "03_negative_artifact_examples.csv")

    rows: list[dict[str, object]] = []
    rows.append(audit_row(
        "review_plan_dossier_row_match",
        "ready" if len(plan) == len(dossier) and len(plan) > 0 else "not_ready",
        f"{len(plan)} plan; {len(dossier)} dossier",
        "matching nonzero counts",
        "outputs/detection/first_pass_review_plan.csv",
        "Regenerate review and review-plan exports if counts differ.",
    ))
    rows.append(audit_row(
        "blind_packet_key_row_match",
        "ready" if len(blind_packet) == len(blind_key) == len(plan) and len(blind_packet) > 0 else "not_ready",
        f"{len(blind_packet)} packet; {len(blind_key)} key; {len(plan)} plan",
        "all equal to first-pass review count",
        "outputs/detection/blind_review_packet.csv",
        "Regenerate blind-review packet if packet/key counts differ.",
    ))
    rows.append(audit_row(
        "blind_reconciliation_row_match",
        "ready" if len(blind_reconciliation) == len(blind_packet) and len(blind_reconciliation) > 0 else "not_ready",
        f"{len(blind_reconciliation)} reconciliation; {len(blind_packet)} packet",
        "reconciliation count equals packet count",
        "outputs/detection/blind_review_reconciliation.csv",
        "Run .\\run.ps1 blind-reconcile after changing the blind packet.",
    ))

    blind_ids = [row.get("blind_id", "") for row in blind_packet]
    duplicate_blind = [blind_id for blind_id, count in Counter(blind_ids).items() if blind_id and count > 1]
    missing_key = sorted(set(blind_ids) - {row.get("blind_id", "") for row in blind_key})
    rows.append(audit_row(
        "blind_id_integrity",
        "ready" if not duplicate_blind and not missing_key and blind_ids else "not_ready",
        f"{len(duplicate_blind)} duplicate blind IDs; {len(missing_key)} missing keys",
        "0 duplicates and 0 missing keys",
        "outputs/detection/blind_review_key.csv",
        "Regenerate blind review packet and key together.",
    ))

    crop_rows = [row for row in plan if row.get("crop_url")]
    bad_crop_urls = []
    for row in crop_rows:
        parts = parse_crop_url(row.get("crop_url", ""))
        if not {"image", "x", "y", "crop"}.issubset(parts):
            bad_crop_urls.append(row.get("candidate_id", ""))
    rows.append(audit_row(
        "review_crop_url_shape",
        "ready" if crop_rows and not bad_crop_urls else "not_ready",
        f"{len(crop_rows)} crop URLs; {len(bad_crop_urls)} malformed",
        "all crop URLs contain image, x, y, and crop",
        "outputs/detection/first_pass_review_plan.csv",
        "Fix crop URL generation before reviewer use.",
    ))

    referenced_images = sorted({row.get("image_id", "") for row in plan if row.get("image_id")})
    missing_images = [image_id for image_id in referenced_images if not image_exists(image_id)]
    rows.append(audit_row(
        "review_image_products_exist",
        "ready" if referenced_images and not missing_images else "not_ready",
        f"{len(referenced_images)} referenced images; {len(missing_images)} missing calibrated products",
        "all referenced images have local calibrated image and label",
        "outputs/detection/first_pass_review_plan.csv",
        "Download/regenerate missing OPUS calibrated products before review.",
    ))

    artifacts = [
        OUTPUT_DIR / "review_artifacts" / "published_match.png",
        OUTPUT_DIR / "review_artifacts" / "top_unmatched_temporal_track.png",
        OUTPUT_DIR / "review_artifacts" / "temporal_track_strips.png",
        OUTPUT_DIR / "review_artifacts" / "likely_artifact.png",
        OUTPUT_DIR / "review_artifacts" / "strong_single_frame_candidate.png",
    ]
    invalid_artifacts = [path.name for path in artifacts if not artifact_valid(path)]
    rows.append(audit_row(
        "review_artifact_images_valid",
        "ready" if not invalid_artifacts else "not_ready",
        f"{len(artifacts) - len(invalid_artifacts)} valid; {len(invalid_artifacts)} invalid",
        "all review artifact PNGs open successfully",
        "outputs/detection/review_artifacts",
        "Regenerate review metrics/artifact contact sheets.",
    ))

    rows.append(audit_row(
        "known_positive_batch_size",
        "ready" if len(known_batch) == 6 else "not_ready",
        len(known_batch),
        6,
        "outputs/detection/review_batches/01_known_validation_positive.csv",
        "Regenerate first-pass review plan; keep all six known validation marks.",
    ))
    rows.append(audit_row(
        "negative_batch_size",
        "ready" if len(negative_batch) >= 20 else "not_ready",
        len(negative_batch),
        "at least 20",
        "outputs/detection/review_batches/03_negative_artifact_examples.csv",
        "Regenerate first-pass review plan with enough clear negative examples.",
    ))
    rows.append(audit_row(
        "blind_import_currently_empty",
        "ready" if len(blind_import) == 0 else "in_progress",
        len(blind_import),
        "0 until blind reviewer labels are filled",
        "outputs/detection/blind_review_label_import.csv",
        "If nonzero, inspect reconciliation before importing labels.",
    ))
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    counts = Counter(str(row["status"]) for row in rows)
    lines = [
        "# Evidence Integrity Audit",
        "",
        "This audit checks that reviewer-facing evidence files are internally consistent. It does not decide whether a candidate is lightning.",
        "",
        "## Summary",
        "",
        f"- Ready checks: {counts.get('ready', 0)}",
        f"- In-progress checks: {counts.get('in_progress', 0)}",
        f"- Not-ready checks: {counts.get('not_ready', 0)}",
        "",
        "## Checks",
        "",
        "| Check | Status | Value | Expected | Evidence | Next action |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['check']}` | `{row['status']}` | {row['value']} | {row['expected']} | "
            f"`{row['evidence_file']}` | {row['next_action']} |"
        )
    lines.extend([
        "",
        "## Safe Interpretation",
        "",
        "A ready integrity audit means the evidence package is coherent enough for review. It is not a scientific validation result and does not confirm new lightning.",
    ])
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_audit_rows()
    write_csv(AUDIT_CSV, rows, ["check", "status", "value", "expected", "evidence_file", "next_action"])
    write_report(rows)
    print(f"Wrote {AUDIT_CSV}")
    print(f"Wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
