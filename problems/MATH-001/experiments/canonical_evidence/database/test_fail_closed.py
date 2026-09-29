"""Bounded exit-contract regressions; no solver or downloaded corpus required."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import audit_r1_artifacts as audit

HERE = Path(__file__).resolve().parent


class DatabaseCliTests(unittest.TestCase):
    def invoke(self, content, sample=0):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "corpus.txt"
            output = root / "result.json"
            source.write_text(content, encoding="ascii")
            result = subprocess.run(
                [sys.executable, str(HERE / "verify_all_known.py"), "--file", str(source),
                 "--sample", str(sample), "--progress", "0", "--json", str(output)],
                capture_output=True, text=True, timeout=15)
            return result.returncode, json.loads(output.read_text())

    def test_empty_and_blank_corpus_fail_in_full_and_sample_modes(self):
        for content in ("", "\n \n"):
            for sample in (0, 1):
                with self.subTest(content=content, sample=sample):
                    rc, result = self.invoke(content, sample)
                    self.assertEqual(rc, 1)
                    self.assertFalse(result["passed"])

    def test_each_nonblank_malformed_record_fails(self):
        for bad in ("abc", ".012", ".", ".00", ".010?", ".0011"):
            with self.subTest(bad=bad):
                rc, result = self.invoke("*0101\n" + bad + "\n", 2)
                self.assertEqual(rc, 1)
                self.assertEqual(result["n_decode_errors"], 1)

    def test_valid_sample_is_explicitly_not_full_verification(self):
        rc, result = self.invoke("*0101\n", 1)
        self.assertEqual(rc, 0)
        self.assertEqual(result["scope"], "SAMPLE_ONLY")
        self.assertEqual(result["decoded"], 1)
        self.assertIsNone(result["expected_records"])

    def test_truncated_legal_corpus_cannot_pass_full_mode(self):
        rc, result = self.invoke("*0101\n")
        self.assertEqual(rc, 1)
        self.assertEqual(result["decoded"], 1)
        self.assertTrue(any("431008" in reason for reason in result["exit_reasons"]))
        self.assertTrue(any("SHA-256" in reason for reason in result["exit_reasons"]))

    def test_decodable_collinear_certificate_fails(self):
        rc, result = self.invoke(".010202\n", 1)
        self.assertEqual(rc, 1)
        self.assertEqual(result["n_decode_errors"], 0)
        self.assertEqual(result["verify_fail"], 1)


class SelfCertificateExitTests(unittest.TestCase):
    """Use the real self checker; isolate expensive corpus work to test its exit gate."""

    def invoke(self, certificate=None, corpus_only=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            if certificate is not None:
                (root / "self").mkdir()
                content = certificate if isinstance(certificate, str) else json.dumps(certificate)
                (root / "self" / "certificate.json").write_text(content)
            corpus = root / "corpus.txt"
            corpus.write_text("*0101\n")
            output = root / "result.json"
            corpus_ok = {"stats": {"decoded": 36912, "verify_pass": 36912},
                         "n_min": 2, "n_max": 52, "n_decode_errors": 0, "seconds": 0}
            teeth_ok = {"mutated_lines_still_decode": 371, "teeth_fraction_illegal": 1.0}
            args = ["--corpus", str(corpus), "--json", str(output)]
            args += ["--corpus-only"] if corpus_only else ["--r1", str(root)]
            with patch.object(audit, "audit_flammenkamp", return_value=corpus_ok), \
                    patch.object(audit, "corpus_teeth_check", return_value=teeth_ok), \
                    contextlib.redirect_stdout(io.StringIO()):
                rc = audit.main(args)
            return rc, json.loads(output.read_text())

    def test_real_legal_self_certificate_passes(self):
        rc, result = self.invoke({"n": 2, "target": 4,
                                  "points": [[1, 1], [1, 2], [2, 1], [2, 2]]})
        self.assertEqual(rc, 0)
        self.assertTrue(result["self_certs"]["all_pass"])

    def test_real_collinear_self_certificate_forces_nonzero_exit(self):
        rc, result = self.invoke({"n": 3, "target": 6,
                                  "points": [[1, 1], [2, 1], [1, 2], [3, 2], [1, 3], [3, 3]]})
        self.assertEqual(rc, 1)
        self.assertFalse(result["self_certs"]["all_pass"])
        self.assertIn("required self-certificates missing or failed", result["exit_reasons"])

    def test_wrong_declared_target_is_rejected(self):
        rc, _ = self.invoke({"n": 2, "target": 5,
                             "points": [[1, 1], [1, 2], [2, 1], [2, 2]]})
        self.assertEqual(rc, 1)

    def test_empty_required_set_and_malformed_json_fail(self):
        for certificate in (None, "{broken", {"n": "2", "points": []}):
            with self.subTest(certificate=certificate):
                rc, result = self.invoke(certificate)
                self.assertEqual(rc, 1)
                self.assertFalse(result["self_certs"]["all_pass"])

    def test_explicit_corpus_only_has_no_vacuous_self_pass(self):
        rc, result = self.invoke(corpus_only=True)
        self.assertEqual(rc, 0)
        self.assertEqual(result["self_certs"]["status"], "NOT_REQUESTED")
        self.assertIsNone(result["self_certs"]["all_pass"])

    def test_corpus_only_cannot_silently_ignore_r1_argument(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            audit.main(["--corpus-only", "--r1", "ignored"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
