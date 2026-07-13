# Documentation Claim Audit

This audit scans project-facing Markdown and HTML for stale or unsafe wording. It is not a proof of scientific correctness; it is a guardrail against accidentally saying more than the evidence supports.

## Summary

- Needs attention: 1
- Unsafe wording requiring review: 0
- Safe boundary statements found: 7

## How To Read This

- `needs_attention` means the wording describes a known gap or stale state that should be kept current.
- `review` means the wording could sound like an unsupported claim unless manually checked.
- `ok_boundary` means a risky phrase appears inside a negated/safe boundary statement.

## Findings

| Status | Severity | File | Line | Pattern | Context |
|---|---|---|---:|---|---|
| `needs_attention` | `needs_work` | `docs/evidence_packet_2026-07-06.md` | 82 | `0 of 6` | \| Published validation marks human-labeled positive \| 0 of 6 \| |
| `ok_boundary` | `unsafe` | `docs/evidence_packet_2026-07-06.md` | 11 | `confirmed new lightning` | curated human-review queue. I do not yet have human-confirmed new lightning. |
| `ok_boundary` | `unsafe` | `docs/evidence_packet_2026-07-06.md` | 115 | `confirmed new lightning` | review workflow, not confirmed new lightning yet. |
| `ok_boundary` | `unsafe` | `docs/jupiter_detector_two_minute_overview.html` | 412 | `trained yolo` | <li>The detector is not yet a trained YOLO model or any other deep-learning object detector.</li> |
| `ok_boundary` | `unsafe` | `docs/jupiter_detector_two_minute_overview.md` | 61 | `trained yolo` | - The detector is not yet a trained YOLO model or any other deep-learning object detector. |
| `ok_boundary` | `unsafe` | `docs/paper_readiness_matrix.md` | 11 | `found new lightning` | \| The detector found new lightning \| Not ready \| Unmatched candidates still need review and validation \| |
| `ok_boundary` | `unsafe` | `docs/reproducibility_checklist.md` | 65 | `confirmed new lightning` | - The detector has not confirmed new lightning. |
| `ok_boundary` | `unsafe` | `docs/reviewer_quickstart.md` | 82 | `found new lightning` | The detector found new lightning. |