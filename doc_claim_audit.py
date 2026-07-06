from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
AUDIT_CSV = OUTPUT_DIR / "doc_claim_audit.csv"
AUDIT_MD = OUTPUT_DIR / "doc_claim_audit.md"


SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "docs",
]


PATTERNS = [
    {
        "pattern": "temporal tracking planned",
        "severity": "stale",
        "meaning": "Temporal-track outputs now exist; docs should say temporal review is working or explain the remaining geometry gap.",
    },
    {
        "pattern": "found new lightning",
        "severity": "unsafe",
        "meaning": "New-lightning claims require human review plus temporal/geometric validation.",
    },
    {
        "pattern": "confirmed new lightning",
        "severity": "unsafe",
        "meaning": "Confirmed discovery language should only appear as a negated boundary unless reviewed evidence exists.",
    },
    {
        "pattern": "trained yolo",
        "severity": "unsafe",
        "meaning": "YOLO has not been trained for this project yet.",
    },
    {
        "pattern": "0 of 6",
        "severity": "needs_work",
        "meaning": "Published validation marks still need human labels in the current label set.",
    },
    {
        "pattern": "0 human labels",
        "severity": "needs_work",
        "meaning": "The review workflow exists, but labeling has not started in the saved manifest.",
    },
]


SAFE_NEGATION_TERMS = {
    "not",
    "no",
    "without",
    "unsafe",
    "do not",
    "do not write",
    "not claiming",
    "not confirmed",
}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in SCAN_PATHS:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
            files.extend(sorted(path.rglob("*.html")))
    return sorted(set(files))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def context_for_line(line: str) -> str:
    return " ".join(line.strip().split())[:220]


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def is_negated_context(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in SAFE_NEGATION_TERMS)


def audit_docs() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in iter_text_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            lowered = line.lower()
            for rule in PATTERNS:
                pattern = rule["pattern"]
                if pattern not in lowered:
                    continue
                severity = rule["severity"]
                context = context_for_line(line)
                window = " ".join(lines[max(0, line_number - 5): min(len(lines), line_number + 2)])
                negated = is_negated_context(f"{window} {context}")
                status = "ok_boundary" if severity == "unsafe" and negated else "review"
                if severity in {"stale", "needs_work"}:
                    status = "needs_attention"
                rows.append({
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line": line_number,
                    "pattern": pattern,
                    "severity": severity,
                    "status": status,
                    "context": context,
                    "meaning": rule["meaning"],
                })
    rows.sort(key=lambda row: (str(row["status"]), str(row["severity"]), str(row["file"]), int(row["line"])))
    if not rows:
        rows.append({
            "file": "",
            "line": "",
            "pattern": "",
            "severity": "ok",
            "status": "ok",
            "context": "No watched stale or unsafe claim patterns found.",
            "meaning": "Documentation scan did not find the configured risk phrases.",
        })
    return rows


def write_report(rows: list[dict[str, object]]) -> None:
    review_rows = [row for row in rows if row["status"] == "review"]
    attention_rows = [row for row in rows if row["status"] == "needs_attention"]
    boundary_rows = [row for row in rows if row["status"] == "ok_boundary"]

    lines = [
        "# Documentation Claim Audit",
        "",
        "This audit scans project-facing Markdown and HTML for stale or unsafe wording. It is not a proof of scientific correctness; it is a guardrail against accidentally saying more than the evidence supports.",
        "",
        "## Summary",
        "",
        f"- Needs attention: {len(attention_rows)}",
        f"- Unsafe wording requiring review: {len(review_rows)}",
        f"- Safe boundary statements found: {len(boundary_rows)}",
        "",
        "## How To Read This",
        "",
        "- `needs_attention` means the wording describes a known gap or stale state that should be kept current.",
        "- `review` means the wording could sound like an unsupported claim unless manually checked.",
        "- `ok_boundary` means a risky phrase appears inside a negated/safe boundary statement.",
        "",
        "## Findings",
        "",
        "| Status | Severity | File | Line | Pattern | Context |",
        "|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['status']}` | `{row['severity']}` | `{row['file']}` | {row['line']} | `{row['pattern']}` | {markdown_cell(row['context'])} |"
        )
    AUDIT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = audit_docs()
    write_csv(AUDIT_CSV, rows, ["file", "line", "pattern", "severity", "status", "context", "meaning"])
    write_report(rows)
    print(f"Wrote {AUDIT_CSV}")
    print(f"Wrote {AUDIT_MD}")


if __name__ == "__main__":
    main()
