from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs" / "detection"
PROVENANCE_JSON = OUTPUT_DIR / "provenance_manifest.json"
EVIDENCE_INDEX_JSON = OUTPUT_DIR / "evidence_index.json"
EVIDENCE_INDEX_MD = OUTPUT_DIR / "evidence_index.md"


PURPOSE_RULES = [
    ("key_findings", ["key_findings", "current_key_findings"]),
    ("validation", ["known_match", "detection_summary", "threshold"]),
    ("candidate_review", ["scientific_review_queue", "review_decision", "candidate_review_dossier", "first_pass_review", "review_batches"]),
    ("human_labels", ["candidate_label", "human_review", "review_session", "blind_review", "review_agreement", "review_labeling"]),
    ("temporal_validation", ["temporal_track", "temporal_validation"]),
    ("geometry", ["geometry"]),
    ("filter_context", ["nearby_filter", "opus_nearby"]),
    ("training_readiness", ["training", "active_learning"]),
    ("claim_safety", ["claim", "research_gate", "manuscript"]),
    ("project_management", ["github_issue", "github_project"]),
    ("visual_artifacts", ["review_artifacts"]),
    ("coverage", ["coverage", "dataset_manifest", "processed_date"]),
    ("provenance", ["provenance"]),
]


PURPOSE_DESCRIPTIONS = {
    "validation": "Published-match recovery, threshold sensitivity, and detector run summaries.",
    "key_findings": "Meeting-ready current findings generated from the evidence CSVs.",
    "candidate_review": "Curated candidates and reviewer-facing tables.",
    "human_labels": "Human label templates, sessions, audits, blind review, and agreement checks.",
    "temporal_validation": "Frame-to-frame track evidence and temporal-review questions.",
    "geometry": "What is needed before pixel candidates can become Jupiter locations.",
    "filter_context": "Nearby non-H-alpha context for future color/spectrum follow-up.",
    "training_readiness": "Whether reviewed labels are sufficient for learned-model comparison.",
    "claim_safety": "What can be safely said in a report or manuscript.",
    "project_management": "Issue/project-board exports for collaborators.",
    "visual_artifacts": "PNG contact sheets and visual review aids.",
    "coverage": "Processed dates and input dataset scope.",
    "provenance": "Hashes, row counts, branch, commit, and reproduction commands.",
    "other": "Artifacts not matched to a specific purpose bucket.",
}


def load_manifest() -> dict[str, object]:
    if not PROVENANCE_JSON.exists():
        return {"artifacts": [], "recommended_reproduction_commands": []}
    return json.loads(PROVENANCE_JSON.read_text(encoding="utf-8"))


def purpose_for(path: str) -> str:
    lowered = path.lower()
    for purpose, needles in PURPOSE_RULES:
        if any(needle in lowered for needle in needles):
            return purpose
    return "other"


def safe_use_for(purpose: str) -> str:
    return {
        "validation": "Use to state detector recovery of published marks and current run counts.",
        "key_findings": "Use as the first meeting brief; still follow linked evidence files for proof.",
        "candidate_review": "Use to decide what a human should inspect; do not call rows confirmed lightning.",
        "human_labels": "Use to track human review progress and training readiness.",
        "temporal_validation": "Use to prioritize repeated tracks for review; not enough for discovery alone.",
        "geometry": "Use to explain why location claims are blocked or ready.",
        "filter_context": "Use as follow-up context only after candidate validation.",
        "training_readiness": "Use to decide whether model comparison is allowed.",
        "claim_safety": "Use when writing reports, abstracts, README text, or meeting summaries.",
        "project_management": "Use to coordinate next work; not scientific evidence by itself.",
        "visual_artifacts": "Use for visual inspection and meeting explanation.",
        "coverage": "Use to explain dataset scope and processed dates.",
        "provenance": "Use to verify hashes, row counts, branch, and reproduction commands.",
    }.get(purpose, "Inspect before using; purpose was not classified automatically.")


def build_index() -> dict[str, object]:
    manifest = load_manifest()
    artifacts = []
    for artifact in manifest.get("artifacts", []):
        path = str(artifact.get("path", ""))
        purpose = purpose_for(path)
        artifacts.append({
            "path": path,
            "purpose": purpose,
            "rows": artifact.get("rows"),
            "bytes": artifact.get("bytes"),
            "sha256": artifact.get("sha256"),
            "safe_use": safe_use_for(purpose),
        })
    counts = Counter(row["purpose"] for row in artifacts)
    return {
        "generated_from": str(PROVENANCE_JSON.relative_to(ROOT)).replace("\\", "/"),
        "git_branch": manifest.get("git_branch", ""),
        "git_commit": manifest.get("git_commit", ""),
        "artifact_count": len(artifacts),
        "purpose_counts": dict(sorted(counts.items())),
        "recommended_reproduction_commands": manifest.get("recommended_reproduction_commands", []),
        "artifacts": artifacts,
    }


def write_report(index: dict[str, object]) -> None:
    lines = [
        "# Evidence Index",
        "",
        "This generated index groups the local evidence artifacts by research purpose. It is the first file to open when deciding what a result proves and what it does not prove.",
        "",
        "## Summary",
        "",
        f"- Source manifest: `{index['generated_from']}`",
        f"- Git branch: `{index['git_branch']}`",
        f"- Git commit: `{index['git_commit']}`",
        f"- Indexed artifacts: {index['artifact_count']}",
        "",
        "## Purpose Counts",
        "",
        "| Purpose | Artifacts | What it is for |",
        "|---|---:|---|",
    ]
    for purpose, count in index["purpose_counts"].items():
        lines.append(f"| `{purpose}` | {count} | {PURPOSE_DESCRIPTIONS.get(purpose, PURPOSE_DESCRIPTIONS['other'])} |")
    lines.extend([
        "",
        "## Open These First",
        "",
        "| Question | Start with | Why |",
        "|---|---|---|",
        "| What did the detector process? | `outputs/detection/detection_summary.csv` | Run counts and published-match totals. |",
        "| What are the current key findings? | `outputs/detection/current_key_findings.md` | Generated meeting brief tied to evidence files. |",
        "| Did it recover known lightning? | `outputs/detection/known_match_report.csv` | Six published validation rows with offsets. |",
        "| What should a human review? | `outputs/detection/first_pass_review_plan.md` | Small, ordered review batches. |",
        "| Are review sessions complete? | `outputs/detection/review_session_audit.md` | Shows missing labels, notes, confidence, and import readiness. |",
        "| Which temporal tracks matter? | `outputs/detection/temporal_validation_plan.md` | Prioritized repeated tracks with review questions. |",
        "| Can we claim Jupiter coordinates? | `outputs/detection/geometry_acquisition_checklist.md` | Lists missing SPICE/camera inputs. |",
        "| What can a paper safely say? | `outputs/detection/manuscript_claim_matrix.md` | Supported, limited, and not-supported claims. |",
        "",
        "## Artifact Index",
        "",
        "| Purpose | Path | Rows | Bytes | Safe use |",
        "|---|---|---:|---:|---|",
    ])
    for artifact in index["artifacts"]:
        rows = "" if artifact["rows"] is None else artifact["rows"]
        lines.append(
            f"| `{artifact['purpose']}` | `{artifact['path']}` | {rows} | {artifact['bytes']} | {artifact['safe_use']} |"
        )
    lines.extend([
        "",
        "## Safe Bottom Line",
        "",
        "The evidence package supports a reproducible detector and review workflow. It does not, by itself, confirm new Jupiter lightning.",
    ])
    EVIDENCE_INDEX_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    index = build_index()
    EVIDENCE_INDEX_JSON.write_text(json.dumps(index, indent=2), encoding="utf-8")
    write_report(index)
    print(f"Wrote {EVIDENCE_INDEX_JSON}")
    print(f"Wrote {EVIDENCE_INDEX_MD}")


if __name__ == "__main__":
    main()
