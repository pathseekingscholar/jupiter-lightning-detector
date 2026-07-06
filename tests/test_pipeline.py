import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

import jupiter_pipeline as pipeline
import app_server
import doc_claim_audit
import first_pass_review_plan
import github_issue_backlog
import geometry_audit
import human_review_audit
import candidate_geometry_plan
import date_coverage_summary
import label_tools
import nearby_filter_context
import provenance_manifest
import research_exports
import research_gate_audit
import review_labeling_protocol
import review_agreement_audit
import review_metrics
import training_readiness
import validate_outputs


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_parse_pds_label(self):
        text = """
RECORD_BYTES = 4096
^IMAGE = ("EXAMPLE.IMG",2)
OBJECT = IMAGE
  LINES = 1024
  LINE_SAMPLES = 1024
  SAMPLE_BITS = 32
  SAMPLE_TYPE = PC_REAL
END_OBJECT = IMAGE
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.lbl"
            path.write_text(text, encoding="ascii")
            parsed = pipeline.parse_pds_label(path)
        self.assertEqual(parsed["record_bytes"], 4096)
        self.assertEqual(parsed["image_record"], 2)
        self.assertEqual(parsed["sample_type"], "PC_REAL")

    def test_measurement_uses_display_xy_convention(self):
        image = np.full((80, 90), 0.1, dtype=np.float32)
        image[39:42, 49:52] = 0.5
        measurement = pipeline.measure_candidate(image, x=51, y=41)
        self.assertGreater(measurement["peak_snr"], 1e6)
        self.assertGreaterEqual(measurement["bright_pixel_count"], 9)

    def test_ground_truth_has_six_published_events(self):
        payload = json.loads(pipeline.EVENTS_PATH.read_text(encoding="utf-8"))
        events = sum(len(item["events"]) for item in payload["observations"])
        self.assertEqual(events, 6)

    def test_app_processes_and_resizes_calibrated_image(self):
        if not pipeline.DB_PATH.exists():
            self.skipTest("Research products have not been initialized")
        payload, filename = app_server.render_processed(
            {
                "image": ["1357029177"],
                "crop": ["128"],
                "scale": ["0.5"],
                "x": ["731"],
                "y": ["211"],
                "low": ["2"],
                "high": ["99.8"],
                "gamma": ["1"],
            }
        )
        with Image.open(io.BytesIO(payload)) as image:
            self.assertEqual(image.size, (64, 64))
        self.assertIn("N1357029177", filename)

    def test_app_observations_include_opus_provenance(self):
        if not pipeline.DB_PATH.exists():
            self.skipTest("Research products have not been initialized")
        payload = app_server.observation_payload()
        self.assertEqual(len(payload["observations"]), 3)
        for observation in payload["observations"]:
            self.assertIn(observation["opus_id"], observation["opus_detail_url"])

    def test_candidate_label_writes_json_and_csv(self):
        original_json = app_server.LABELS_PATH
        original_csv = app_server.LABELS_CSV_PATH
        original_grouped = app_server.LABELS_GROUPED_CSV_PATH
        original_summary = app_server.LABEL_SUMMARY_CSV_PATH
        with tempfile.TemporaryDirectory() as directory:
            app_server.LABELS_PATH = Path(directory) / "candidate_labels.json"
            app_server.LABELS_CSV_PATH = Path(directory) / "candidate_labels.csv"
            app_server.LABELS_GROUPED_CSV_PATH = Path(directory) / "candidate_labels_grouped.csv"
            app_server.LABEL_SUMMARY_CSV_PATH = Path(directory) / "candidate_label_summary.csv"
            try:
                payload = app_server.save_candidate_label({
                    "run_date": "2001-01-01",
                    "candidate_id": "1357029177-0001",
                    "image_id": "N1357029177",
                    "image_number": "1357029177",
                    "x": "731.0",
                    "y": "211.0",
                    "brightness": "12.3",
                    "blob_size": 4,
                    "snr": "12.3",
                    "artifact_flags": "",
                    "candidate_score": "0.42",
                    "human_label": "possible-lightning",
                    "review_note": "multi-pixel bright spot",
                    "updated_at": "2026-07-02T00:00:00Z",
                })
                self.assertTrue(payload["saved"])
                self.assertTrue(app_server.LABELS_PATH.exists())
                self.assertTrue(app_server.LABELS_CSV_PATH.exists())
                saved = json.loads(app_server.LABELS_PATH.read_text(encoding="utf-8"))
                self.assertEqual(saved["labels"]["1357029177-0001"]["human_label"], "possible-lightning")
                self.assertEqual(saved["labels"]["1357029177-0001"]["label"], "possible-lightning")
                self.assertEqual(saved["labels"]["1357029177-0001"]["review_stage"], "first-review")
                self.assertEqual(saved["labels"]["1357029177-0001"]["needs_second_review"], "no")
                self.assertIn("reviewer", saved["labels"]["1357029177-0001"])
                self.assertIn("reviewed_at", saved["labels"]["1357029177-0001"])
                self.assertIn("candidate_id", app_server.LABELS_CSV_PATH.read_text(encoding="utf-8"))
                self.assertIn("positive", app_server.LABELS_GROUPED_CSV_PATH.read_text(encoding="utf-8"))
                self.assertIn("group_positive", app_server.LABEL_SUMMARY_CSV_PATH.read_text(encoding="utf-8"))
            finally:
                app_server.LABELS_PATH = original_json
                app_server.LABELS_CSV_PATH = original_csv
                app_server.LABELS_GROUPED_CSV_PATH = original_grouped
                app_server.LABEL_SUMMARY_CSV_PATH = original_summary

    def test_research_exports_have_expected_columns(self):
        summary_path = research_exports.OUTPUT_DIR / "2001-01-01" / "summary.json"
        if not summary_path.exists():
            self.skipTest("Detector outputs have not been generated")
        manifest = research_exports.build_dataset_manifest()
        summary = research_exports.build_detection_summary()
        sweep = research_exports.build_threshold_sweep()
        matches = research_exports.build_known_match_report()
        tracks = research_exports.build_temporal_track_summary()
        review_queue = research_exports.build_scientific_review_queue(matches, tracks)
        training_manifest = research_exports.build_training_manifest(review_queue)
        active_learning = research_exports.build_active_learning_queue(training_manifest)
        self.assertTrue(manifest)
        self.assertTrue(summary)
        self.assertTrue(sweep)
        self.assertTrue(matches)
        self.assertTrue(tracks)
        self.assertTrue(review_queue)
        self.assertTrue(training_manifest)
        self.assertTrue(active_learning)
        self.assertIn("opus_id", manifest[0])
        self.assertIn("candidate_count", manifest[0])
        self.assertIn("images_processed", summary[0])
        self.assertIn("unmatched_review_candidates", summary[0])
        self.assertIn("snr_threshold", sweep[0])
        self.assertIn("published_matches", sweep[0])
        self.assertIn("offset_px", matches[0])
        self.assertIn("frame_count", tracks[0])
        self.assertIn("motion_consistency", tracks[0])
        self.assertIn("review_category", review_queue[0])
        self.assertIn("training_split", training_manifest[0])
        self.assertIn("review_priority", active_learning[0])
        schema = json.loads((ROOT / "schemas" / "training_manifest.schema.json").read_text(encoding="utf-8"))
        allowed_splits = set(schema["properties"]["training_split"]["enum"])
        produced_splits = {row["training_split"] for row in training_manifest}
        self.assertTrue(produced_splits.issubset(allowed_splits))

    def test_date_coverage_summary_outputs(self):
        summary_path = date_coverage_summary.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Detection summary has not been generated")
        rows = date_coverage_summary.build_summary_rows()
        self.assertTrue(rows)
        self.assertIn("interpretation", rows[0])
        self.assertEqual(sum(int(float(row["images_processed"])) for row in rows), 221)
        self.assertEqual(sum(int(row["published_matches"]) for row in rows), 6)

    def test_review_metrics_build_decision_matrix(self):
        summary_path = review_metrics.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Research exports have not been generated")
        metrics = review_metrics.build_review_metrics()
        matrix = review_metrics.build_decision_matrix()
        track_quality = review_metrics.build_track_quality()
        recommendations = review_metrics.build_threshold_recommendations()
        dossier = review_metrics.build_candidate_dossier(matrix)
        self.assertTrue(metrics)
        self.assertTrue(matrix)
        self.assertTrue(track_quality)
        self.assertTrue(recommendations)
        self.assertTrue(dossier)
        metric_names = {row["metric"] for row in metrics}
        self.assertIn("images_processed", metric_names)
        self.assertIn("published_matches_recovered", metric_names)
        self.assertIn("next_action", matrix[0])
        self.assertIn("review_rank", matrix[0])
        self.assertIn("temporal_quality", track_quality[0])
        self.assertIn("published_recall", recommendations[0])
        self.assertIn("crop_url", dossier[0])
        self.assertIn("next_action", dossier[0])
        self.assertTrue(any(row["next_action"] == "confirm_known_validation_mark" for row in matrix))
        self.assertTrue(any(row["temporal_quality"] == "strong_temporal_review" for row in track_quality))

    def test_label_template_and_import(self):
        matrix_path = label_tools.OUTPUT_DIR / "review_decision_matrix.csv"
        if not matrix_path.exists():
            self.skipTest("Review decision matrix has not been generated")
        template = label_tools.build_template()
        self.assertTrue(template)
        self.assertIn("candidate_id", template[0])
        self.assertIn("suggested_label", template[0])

        original_json = label_tools.LABELS_JSON
        original_csv = label_tools.LABELS_CSV
        original_grouped = label_tools.LABELS_GROUPED_CSV
        original_summary = label_tools.LABEL_SUMMARY_CSV
        with tempfile.TemporaryDirectory() as directory:
            label_tools.LABELS_JSON = Path(directory) / "candidate_labels.json"
            label_tools.LABELS_CSV = Path(directory) / "candidate_labels.csv"
            label_tools.LABELS_GROUPED_CSV = Path(directory) / "candidate_labels_grouped.csv"
            label_tools.LABEL_SUMMARY_CSV = Path(directory) / "candidate_label_summary.csv"
            import_path = Path(directory) / "labels.csv"
            row = dict(template[0])
            row["human_label"] = "known-lightning"
            row["confidence"] = "high"
            row["reviewer"] = "unit-test"
            row["review_note"] = "known validation mark"
            row["review_stage"] = "first-review"
            row["needs_second_review"] = "yes"
            label_tools.write_csv(import_path, [row], list(row.keys()))
            try:
                label_tools.import_labels(import_path)
                payload = json.loads(label_tools.LABELS_JSON.read_text(encoding="utf-8"))
                saved = payload["labels"][row["candidate_id"]]
                self.assertEqual(saved["human_label"], "known-lightning")
                self.assertEqual(saved["confidence"], "high")
                self.assertEqual(saved["reviewer"], "unit-test")
                self.assertEqual(saved["needs_second_review"], "yes")
                self.assertIn("positive", label_tools.LABELS_GROUPED_CSV.read_text(encoding="utf-8"))
                self.assertIn("label_known-lightning", label_tools.LABEL_SUMMARY_CSV.read_text(encoding="utf-8"))
            finally:
                label_tools.LABELS_JSON = original_json
                label_tools.LABELS_CSV = original_csv
                label_tools.LABELS_GROUPED_CSV = original_grouped
                label_tools.LABEL_SUMMARY_CSV = original_summary

    def test_provenance_manifest_lists_artifacts(self):
        summary_path = provenance_manifest.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Research exports have not been generated")
        manifest = provenance_manifest.build_manifest()
        self.assertIn("git_commit", manifest)
        self.assertTrue(manifest["artifacts"])
        artifact_paths = {row["path"] for row in manifest["artifacts"]}
        self.assertIn("outputs/detection/detection_summary.csv", artifact_paths)

    def test_generated_outputs_validate(self):
        summary_path = validate_outputs.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Generated outputs have not been produced")
        errors = validate_outputs.validate()
        self.assertEqual(errors, [])

    def test_geometry_readiness_audit(self):
        manifest_path = geometry_audit.OUTPUT_DIR / "dataset_manifest.csv"
        if not manifest_path.exists():
            self.skipTest("Dataset manifest has not been generated")
        rows = geometry_audit.build_geometry_readiness()
        self.assertTrue(rows)
        self.assertIn("geometry_context_available", rows[0])
        self.assertIn("candidate_latlon_ready", rows[0])
        self.assertTrue(any(row["geometry_context_available"] == "yes" for row in rows))

    def test_candidate_geometry_plan_outputs(self):
        review_plan_path = candidate_geometry_plan.OUTPUT_DIR / "first_pass_review_plan.csv"
        if not review_plan_path.exists():
            self.skipTest("First-pass review plan has not been generated")
        rows = candidate_geometry_plan.build_plan_rows()
        self.assertTrue(rows)
        self.assertIn("geometry_readiness", rows[0])
        self.assertTrue(all(row["required_method"] == "camera_spice_projection" for row in rows))
        self.assertTrue(any(row["x"] and row["y"] for row in rows))

    def test_nearby_filter_context_outputs(self):
        context_path = nearby_filter_context.CONTEXT_CSV
        if not context_path.exists():
            self.skipTest("Nearby filter context has not been generated")
        rows = nearby_filter_context.read_csv(context_path)
        self.assertTrue(rows)
        self.assertIn("context_status", rows[0])
        self.assertIn("context_filter", rows[0])
        self.assertTrue(any(row["context_status"] == "nearby_non_hal_context" for row in rows))

    def test_human_review_audit_outputs(self):
        training_path = human_review_audit.OUTPUT_DIR / "training_manifest.csv"
        if not training_path.exists():
            self.skipTest("Training manifest has not been generated")
        rows = human_review_audit.build_audit()
        self.assertTrue(rows)
        items = {row["audit_item"] for row in rows}
        self.assertIn("positive_training_examples", items)
        self.assertIn("negative_training_examples", items)
        self.assertIn("published_validation_marks_labeled", items)

    def test_first_pass_review_plan_outputs(self):
        dossier_path = first_pass_review_plan.OUTPUT_DIR / "candidate_review_dossier.csv"
        if not dossier_path.exists():
            self.skipTest("Candidate review dossier has not been generated")
        rows = first_pass_review_plan.build_plan()
        self.assertTrue(rows)
        batches = {row["review_batch"] for row in rows}
        self.assertIn("01_known_validation_positive", batches)
        self.assertIn("03_negative_artifact_examples", batches)
        self.assertTrue(all(row["review_note_prompt"] for row in rows))
        with self.subTest("html_report_constant"):
            self.assertEqual(first_pass_review_plan.PLAN_HTML.name, "first_pass_review_plan.html")
        with self.subTest("batch_dir_constant"):
            self.assertEqual(first_pass_review_plan.BATCH_DIR.name, "review_batches")

    def test_review_labeling_protocol_outputs(self):
        review_plan_path = review_labeling_protocol.OUTPUT_DIR / "first_pass_review_plan.csv"
        if not review_plan_path.exists():
            self.skipTest("First-pass review plan has not been generated")
        rows = review_labeling_protocol.build_checklist_rows()
        self.assertTrue(rows)
        self.assertIn("preferred_labels", rows[0])
        batches = {row["review_batch"] for row in rows}
        self.assertIn("01_known_validation_positive", batches)
        self.assertIn("03_negative_artifact_examples", batches)

    def test_training_readiness_outputs(self):
        manifest_path = training_readiness.OUTPUT_DIR / "training_manifest.csv"
        if not manifest_path.exists():
            self.skipTest("Training manifest has not been generated")
        rows = training_readiness.build_readiness_rows()
        self.assertTrue(rows)
        gates = {row["gate"]: row for row in rows}
        self.assertIn("model_comparison_allowed", gates)
        self.assertIn(gates["model_comparison_allowed"]["status"], {"ready", "not_ready"})
        self.assertEqual(gates["positive_examples"]["minimum"], training_readiness.MIN_POSITIVES)

    def test_doc_claim_audit_outputs(self):
        rows = doc_claim_audit.audit_docs()
        self.assertTrue(rows)
        self.assertIn("status", rows[0])
        stale_temporal = [
            row for row in rows
            if row.get("pattern") == "temporal tracking planned" and row.get("status") == "needs_attention"
        ]
        self.assertEqual(stale_temporal, [])

    def test_research_gate_audit_outputs(self):
        if not (research_gate_audit.OUTPUT_DIR / "detection_summary.csv").exists():
            self.skipTest("Generated outputs have not been produced")
        rows = research_gate_audit.build_gate_audit()
        self.assertTrue(rows)
        gates = {row["gate"]: row for row in rows}
        self.assertEqual(gates["published_match_recovery"]["status"], "ready")
        self.assertIn(gates["human_positive_labels"]["status"], {"not_ready", "ready"})
        self.assertIn("model_training_readiness", gates)
        self.assertEqual(gates["model_training_readiness"]["evidence_file"], "outputs/detection/training_readiness.csv")
        self.assertIn("evidence_file", rows[0])

    def test_github_issue_backlog_outputs(self):
        if not (github_issue_backlog.OUTPUT_DIR / "research_gate_audit.csv").exists():
            self.skipTest("Research gate audit has not been generated")
        rows = github_issue_backlog.build_backlog()
        self.assertTrue(rows)
        self.assertIn("issue_id", rows[0])
        self.assertTrue(any(row["gate"] == "human_positive_labels" for row in rows))
        self.assertTrue(any(row["gate"] == "model_training_readiness" for row in rows))
        self.assertTrue(all(row["acceptance_criteria"] for row in rows))

    def test_review_agreement_audit_outputs(self):
        rows = review_agreement_audit.build_agreement_audit()
        self.assertTrue(rows)
        metrics = {row["metric"] for row in rows}
        self.assertIn("total_saved_labels", metrics)
        self.assertIn("training_ready_labels", metrics)


if __name__ == "__main__":
    unittest.main()
