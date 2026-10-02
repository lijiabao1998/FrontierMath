"""Negative tests for the reproduction gate. Stdlib only.

RED means exit 2. GREEN means exit 0.
"""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

import full_scan
from gate import failure_reasons, reproduction_ok


VALID = ".0101\n"
COLLINEAR = ".011202\n"
BAD = "abc\n"


class GateTests(unittest.TestCase):
    def test_time_limit_shape_from_run1_is_red(self):
        report = {
            "stopped": "time_limit",
            "decode_fail": [],
            "math_fail": [],
            "disagree": [],
            "scanned": 412675,
            "eof": False,
        }
        self.assertFalse(reproduction_ok(report))
        self.assertIn("stopped:time_limit", failure_reasons(report))
        self.assertIn("incomplete", failure_reasons(report))

    def test_decode_list_is_red_even_without_stopped(self):
        report = {"stopped": "", "decode_fail": [{"line": 1}], "math_fail": [], "disagree": [], "eof": True, "scanned": 1, "record_count": 1}
        self.assertIn("decode_fail", failure_reasons(report))

    def test_math_and_disagree_counts_are_red(self):
        report = {"stopped": "", "decode_fail_count": 0, "math_fail_count": 1, "disagree_count": 0, "eof": True, "scanned": 1, "record_count": 1}
        self.assertIn("math_fail", failure_reasons(report))
        report["math_fail_count"] = 0
        report["disagree_count"] = 1
        self.assertIn("disagree", failure_reasons(report))


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dataset = self.root / "codes.txt"
        self.checkpoint = self.root / "checkpoint.json"
        self.manifest_path = self.root / "manifest.json"

    def _run(self, deadline):
        argv = [
            "--dataset", str(self.dataset),
            "--checkpoint", str(self.checkpoint),
            "--manifest-out", str(self.manifest_path),
            "--git-start", str(Path(__file__).resolve().parents[3]),
        ]
        if deadline is not None:
            argv += ["--deadline", str(deadline)]
        return full_scan.main(argv)

    def test_time_limit_is_red(self):
        self.dataset.write_text(VALID * 30, encoding="ascii")
        code = self._run(0)
        self.assertEqual(code, 2)
        state = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(state["stopped"], "time_limit")
        self.assertFalse(state["eof"])
        self.assertTrue(self.manifest_path.exists())
        frozen = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertIn("git_head", frozen)
        self.assertEqual(len(frozen["git_head"]), 40)
        self.assertIn("decode_flam.py", frozen["sources"])
        self.assertEqual(frozen["dataset_sha256"], full_scan.sha256_file(self.dataset))

    def test_decode_failure_is_red(self):
        self.dataset.write_text(BAD, encoding="ascii")
        self.assertEqual(self._run(None), 2)
        state = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertGreaterEqual(state["decode_fail_count"], 1)
        self.assertTrue(state["eof"])

    def test_math_failure_is_red(self):
        self.dataset.write_text(COLLINEAR, encoding="ascii")
        self.assertEqual(self._run(None), 2)
        state = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertGreaterEqual(state["math_fail_count"], 1)
        self.assertEqual(state["disagree_count"], 0)

    def test_incomplete_resume_is_red_and_complete_resume_is_green(self):
        self.dataset.write_text(VALID * 4, encoding="ascii")
        self.assertEqual(self._run(0), 2)
        self.assertEqual(self._run(0), 2)
        self.assertEqual(self._run(None), 0)
        state = json.loads(self.checkpoint.read_text(encoding="utf-8"))
        self.assertEqual(state["scanned"], 4)
        self.assertEqual(state["pass_count"], 4)
        self.assertTrue(state["eof"])
        self.assertEqual(self._run(None), 0)


if __name__ == "__main__":
    unittest.main()
