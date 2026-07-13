# Blind Review Reconciliation

This report joins completed blind-review labels back to the hidden answer key. It does not import labels automatically; it writes an import-ready CSV that can be reviewed before use.

## Files

- Input reviewer file: `outputs/detection/blind_review_packet.csv`
- Input answer key: `outputs/detection/blind_review_key.csv`
- Import-ready output: `outputs/detection/blind_review_label_import.csv`
- Reconciliation output: `outputs/detection/blind_review_reconciliation.csv`

## Summary

- Blind rows checked: 106
- Labeled rows ready for import review: 0
- Invalid labels: 0
- Invalid confidence values: 0

## Agreement Counts

| Agreement | Rows |
|---|---:|
| `unlabeled` | 106 |

## Reviewer Label Counts

| Reviewer label | Rows |
|---|---:|
| `unlabeled` | 106 |

## How To Import After Review

After checking `blind_review_reconciliation.csv` for invalid labels/confidence and disagreement cases, run:

```powershell
.\run.ps1 label-import -LabelCsv outputs\detection\blind_review_label_import.csv
.\run.ps1 label-summary
```

Rows without `reviewer_label` are intentionally skipped from the import CSV. Disagreement is not automatically bad; it is evidence for second review or clearer labeling rules.