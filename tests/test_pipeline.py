import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import jupiter_pipeline as pipeline


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


if __name__ == "__main__":
    unittest.main()
