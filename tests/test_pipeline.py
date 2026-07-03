import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

import jupiter_pipeline as pipeline
import app_server
import label_tools
import provenance_manifest
import research_exports
import review_metrics


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
        with tempfile.TemporaryDirectory() as directory:
            app_server.LABELS_PATH = Path(directory) / "candidate_labels.json"
            app_server.LABELS_CSV_PATH = Path(directory) / "candidate_labels.csv"
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
                self.assertIn("reviewer", saved["labels"]["1357029177-0001"])
                self.assertIn("reviewed_at", saved["labels"]["1357029177-0001"])
                self.assertIn("candidate_id", app_server.LABELS_CSV_PATH.read_text(encoding="utf-8"))
            finally:
                app_server.LABELS_PATH = original_json
                app_server.LABELS_CSV_PATH = original_csv

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

    def test_review_metrics_build_decision_matrix(self):
        summary_path = review_metrics.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Research exports have not been generated")
        metrics = review_metrics.build_review_metrics()
        matrix = review_metrics.build_decision_matrix()
        track_quality = review_metrics.build_track_quality()
        recommendations = review_metrics.build_threshold_recommendations()
        self.assertTrue(metrics)
        self.assertTrue(matrix)
        self.assertTrue(track_quality)
        self.assertTrue(recommendations)
        metric_names = {row["metric"] for row in metrics}
        self.assertIn("images_processed", metric_names)
        self.assertIn("published_matches_recovered", metric_names)
        self.assertIn("next_action", matrix[0])
        self.assertIn("review_rank", matrix[0])
        self.assertIn("temporal_quality", track_quality[0])
        self.assertIn("published_recall", recommendations[0])
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
        with tempfile.TemporaryDirectory() as directory:
            label_tools.LABELS_JSON = Path(directory) / "candidate_labels.json"
            label_tools.LABELS_CSV = Path(directory) / "candidate_labels.csv"
            import_path = Path(directory) / "labels.csv"
            row = dict(template[0])
            row["human_label"] = "known-lightning"
            row["confidence"] = "high"
            row["reviewer"] = "unit-test"
            row["review_note"] = "known validation mark"
            label_tools.write_csv(import_path, [row], list(row.keys()))
            try:
                label_tools.import_labels(import_path)
                payload = json.loads(label_tools.LABELS_JSON.read_text(encoding="utf-8"))
                saved = payload["labels"][row["candidate_id"]]
                self.assertEqual(saved["human_label"], "known-lightning")
                self.assertEqual(saved["confidence"], "high")
                self.assertEqual(saved["reviewer"], "unit-test")
            finally:
                label_tools.LABELS_JSON = original_json
                label_tools.LABELS_CSV = original_csv

    def test_provenance_manifest_lists_artifacts(self):
        summary_path = provenance_manifest.OUTPUT_DIR / "detection_summary.csv"
        if not summary_path.exists():
            self.skipTest("Research exports have not been generated")
        manifest = provenance_manifest.build_manifest()
        self.assertIn("git_commit", manifest)
        self.assertTrue(manifest["artifacts"])
        artifact_paths = {row["path"] for row in manifest["artifacts"]}
        self.assertIn("outputs/detection/detection_summary.csv", artifact_paths)


if __name__ == "__main__":
    unittest.main()
