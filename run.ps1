param(
    [ValidateSet("init", "download", "analyze", "report", "all", "test", "app", "detect", "detect-all", "exports", "coverage", "coverage-summary", "review", "geometry", "geometry-plan", "geometry-inputs", "geometry-acquisition", "filters", "label-audit", "review-plan", "review-sessions", "review-session-audit", "temporal-validation", "blind-review", "blind-reconcile", "evidence-integrity", "label-protocol", "training-readiness", "claim-audit", "research-gates", "manuscript-claims", "issue-backlog", "project-board", "agreement-audit", "evidence-index", "reproduction-audit", "label-template", "label-import", "label-summary", "provenance", "validate-outputs")]
    [string]$Command = "all",
    [ValidateSet("2000-12-31", "2001-01-01", "2001-01-04", "2001-01-05", "2001-01-08", "2001-01-09", "2001-01-10", "2001-01-11", "2001-01-13")]
    [string]$Date = "2001-01-01",
    [string]$LabelCsv = "outputs\detection\candidate_label_template.csv"
)

$ErrorActionPreference = "Stop"
$workspacePython = "C:\Users\vedar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path $workspacePython) {
    $python = $workspacePython
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} else {
    throw "Python 3 was not found. Install Python 3 with numpy and Pillow."
}

if ($Command -eq "test") {
    & $python -m unittest discover -s tests -v
} elseif ($Command -eq "app") {
    & $python app_server.py
} elseif ($Command -eq "detect") {
    & $python detection_pipeline.py detect --date $Date
} elseif ($Command -eq "detect-all") {
    foreach ($runDate in @("2000-12-31", "2001-01-01", "2001-01-04", "2001-01-05", "2001-01-08", "2001-01-09", "2001-01-10", "2001-01-11", "2001-01-13")) {
        Write-Host "Running detector for $runDate"
        & $python detection_pipeline.py detect --date $runDate
    }
} elseif ($Command -eq "exports") {
    & $python research_exports.py
} elseif ($Command -eq "coverage") {
    & $python opus_coverage.py
} elseif ($Command -eq "coverage-summary") {
    & $python date_coverage_summary.py
} elseif ($Command -eq "review") {
    & $python review_metrics.py
} elseif ($Command -eq "geometry") {
    & $python geometry_audit.py
} elseif ($Command -eq "geometry-plan") {
    & $python candidate_geometry_plan.py
} elseif ($Command -eq "geometry-inputs") {
    & $python geometry_input_inventory.py
} elseif ($Command -eq "geometry-acquisition") {
    & $python geometry_acquisition_checklist.py
} elseif ($Command -eq "filters") {
    & $python nearby_filter_context.py
} elseif ($Command -eq "label-audit") {
    & $python human_review_audit.py
} elseif ($Command -eq "review-plan") {
    & $python first_pass_review_plan.py
} elseif ($Command -eq "review-sessions") {
    & $python review_session_planner.py
} elseif ($Command -eq "review-session-audit") {
    & $python review_session_audit.py
} elseif ($Command -eq "temporal-validation") {
    & $python temporal_validation_plan.py
} elseif ($Command -eq "blind-review") {
    & $python blind_review_packet.py
} elseif ($Command -eq "blind-reconcile") {
    & $python blind_review_reconcile.py
} elseif ($Command -eq "evidence-integrity") {
    & $python evidence_integrity_audit.py
} elseif ($Command -eq "label-protocol") {
    & $python review_labeling_protocol.py
} elseif ($Command -eq "training-readiness") {
    & $python training_readiness.py
} elseif ($Command -eq "claim-audit") {
    & $python doc_claim_audit.py
} elseif ($Command -eq "research-gates") {
    & $python research_gate_audit.py
} elseif ($Command -eq "manuscript-claims") {
    & $python manuscript_claim_matrix.py
} elseif ($Command -eq "issue-backlog") {
    & $python github_issue_backlog.py
} elseif ($Command -eq "project-board") {
    & $python github_project_board.py
} elseif ($Command -eq "agreement-audit") {
    & $python review_agreement_audit.py
} elseif ($Command -eq "evidence-index") {
    & $python evidence_index.py
} elseif ($Command -eq "reproduction-audit") {
    & $python reproduction_audit.py
} elseif ($Command -eq "label-template") {
    & $python label_tools.py template --path $LabelCsv
} elseif ($Command -eq "label-import") {
    & $python label_tools.py import --path $LabelCsv
} elseif ($Command -eq "label-summary") {
    & $python label_tools.py summary
} elseif ($Command -eq "provenance") {
    & $python provenance_manifest.py
} elseif ($Command -eq "validate-outputs") {
    & $python validate_outputs.py
} else {
    & $python jupiter_pipeline.py $Command
}
