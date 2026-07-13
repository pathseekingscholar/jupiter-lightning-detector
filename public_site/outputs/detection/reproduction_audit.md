# Reproduction Audit

This audit checks whether the documented reproduction surface is internally consistent. It is a fast gate: it checks command drift and key artifact presence, but it does not rerun the full detector.

## Summary

- Ready checks: 7
- Not-ready checks: 0

## Checks

| Check | Category | Status | Value | Expected | Evidence | Next action |
|---|---|---|---|---|---|---|
| `RA-001` | `command_surface` | `ready` | 42 | run.ps1 exposes a ValidateSet command list | `run.ps1` | Fix run.ps1 command declaration if command discovery fails. |
| `RA-002` | `provenance_commands` | `ready` | 30 | Provenance lists reproduction commands | `outputs/detection/provenance_manifest.json` | Regenerate provenance with .\run.ps1 provenance. |
| `RA-003` | `command_drift` | `ready` |  | Every provenance command exists in run.ps1 | `run.ps1; outputs/detection/provenance_manifest.json` | Add missing commands to run.ps1 or remove stale provenance commands. |
| `RA-004` | `key_artifacts` | `ready` |  | All key evidence artifacts exist and appear in provenance | `outputs/detection/provenance_manifest.json` | Regenerate the relevant artifact and then regenerate provenance. |
| `RA-005` | `key_artifact_size` | `ready` |  | Key evidence artifacts are non-empty | `outputs/detection` | Regenerate any empty artifact. |
| `RA-006` | `evidence_index` | `ready` | 95 | Evidence index tracks at least 9 artifacts | `outputs/detection/evidence_index.json` | Run .\run.ps1 evidence-index after provenance is regenerated. |
| `RA-007` | `validation_command` | `ready` | validate-outputs | A fast output validator exists | `run.ps1` | Keep .\run.ps1 validate-outputs available as the fast reproduction gate. |

## Recommended Fast Verification

```powershell
.\run.ps1 provenance
.\run.ps1 evidence-index
.\run.ps1 reproduction-audit
.\run.ps1 validate-outputs
.\run.ps1 test
```

## Safe Interpretation

A ready reproduction audit means the documented commands and key evidence files are internally consistent. It does not mean the detector has confirmed new lightning.