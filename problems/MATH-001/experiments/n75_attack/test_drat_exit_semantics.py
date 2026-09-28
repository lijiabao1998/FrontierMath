#!/usr/bin/env python3
"""Regression tests for the DRAT round-trip EXIT SEMANTICS.

The reviewer found the exit condition inverted: the blocked state exited 0 while a
working checked proof would have exited 1, so any shell or CI gate would read an
uncertifiable UNSAT pipeline as successful. These tests pin the semantics down.

Two layers:
  * unit tests on compute_final_status(), which is the single place the rule lives;
  * subprocess tests on the real CLI, asserting the exit code a shell would see.

Required behaviour:
    checker self-test fails                    -> CHECKER_SELFTEST_FAIL        -> RED
    no trace at all                            -> PROOF_PIPELINE_BLOCKED       -> RED
    trace emitted, no independent checker      -> PROOF_TRACE_SELF_CHECKED_ONLY-> RED
    trace emitted, checked by an INDEPENDENT checker -> SOLVED_WITH_CHECKED_PROOF -> GREEN
    malformed proof                            -> rejected by check_drat       -> RED
    proof that never closes (no empty clause)  -> rejected by check_drat       -> RED

Run:  python test_drat_exit_semantics.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "independent_verifier_r1")))

import drat_roundtrip_test as D  # noqa: E402


class TestFinalStatusRule(unittest.TestCase):
    def test_green_requires_independent_checker(self) -> None:
        self.assertEqual(
            D.compute_final_status(True, 1, 1, True), "SOLVED_WITH_CHECKED_PROOF")

    def test_self_checked_only_is_not_green(self) -> None:
        self.assertNotEqual(
            D.compute_final_status(True, 1, 1, False), D.GREEN_STATUS)
        self.assertEqual(
            D.compute_final_status(True, 1, 1, False), "PROOF_TRACE_SELF_CHECKED_ONLY")

    def test_no_trace_is_blocked(self) -> None:
        self.assertEqual(D.compute_final_status(True, 0, 0, False), "PROOF_PIPELINE_BLOCKED")
        self.assertNotEqual(D.compute_final_status(True, 0, 0, False), D.GREEN_STATUS)

    def test_trace_without_verified_empty_clause_is_blocked(self) -> None:
        """The PHP control emits 1932 lines but never closes the proof."""
        st = D.compute_final_status(True, 0, 1, False)
        self.assertNotEqual(st, D.GREEN_STATUS)
        self.assertEqual(st, "PROOF_TRACE_DID_NOT_CLOSE")

    def test_checker_selftest_failure_is_red_even_with_checked_count(self) -> None:
        self.assertEqual(D.compute_final_status(False, 1, 1, True), "CHECKER_SELFTEST_FAIL")

    def test_only_green_status_is_the_green_string(self) -> None:
        combos = [(c, n, e, i)
                  for c in (True, False) for n in (0, 1) for e in (0, 1) for i in (True, False)]
        greens = [D.compute_final_status(*c) for c in combos
                  if D.compute_final_status(*c) == D.GREEN_STATUS]
        self.assertEqual(len(greens), 1, "exactly one combination may be green")
        self.assertEqual(greens[0], "SOLVED_WITH_CHECKED_PROOF")


class TestCheckerRejects(unittest.TestCase):
    """The checker must reject bad traces, not merely fail to accept them."""

    def _check(self, proof):
        return D.check_drat(D.SELFTEST_NVARS, D.SELFTEST_CLAUSES, proof)

    def test_valid_proof_is_checked(self) -> None:
        r = self._check(D.SELFTEST_VALID)
        self.assertTrue(r["empty_clause_verified"])
        self.assertEqual(r["status"], "SOLVED_WITH_CHECKED_PROOF")

    def test_wrong_step_is_rejected(self) -> None:
        r = self._check(D.SELFTEST_BAD_STEP)
        self.assertFalse(r["empty_clause_verified"])
        self.assertEqual(r["status"], "PROOF_NOT_CHECKED")

    def test_missing_empty_clause_is_rejected(self) -> None:
        r = self._check(D.SELFTEST_NO_EMPTY)
        self.assertFalse(r["empty_clause_verified"])

    def test_malformed_proof_is_rejected(self) -> None:
        r = self._check(D.SELFTEST_MALFORMED)
        self.assertEqual(r["status"], "MALFORMED_PROOF")
        self.assertIsNotNone(r["parse_error"])

    def test_unterminated_addition_line_is_rejected(self) -> None:
        with self.assertRaises(D.MalformedProof):
            D.parse_proof_line("2 3")


class TestCliExitCodes(unittest.TestCase):
    """What a shell actually observes."""

    def _run(self, *extra):
        fd, out = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, "drat_roundtrip_test.py"),
                                "--json", out, *extra],
                               capture_output=True, text=True, timeout=3600)
            data = None
            if os.path.exists(out) and os.path.getsize(out):
                with open(out, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            return r.returncode, r.stdout, data
        finally:
            try:
                os.remove(out)
            except OSError:
                pass

    def test_skip_pipeline_is_red_and_carries_the_status(self) -> None:
        code, out, data = self._run("--skip-pipeline")
        self.assertNotEqual(code, 0, "no checked proof => non-zero exit")
        self.assertIsNotNone(data)
        self.assertNotEqual(data["summary"]["final_status"], D.GREEN_STATUS)
        self.assertTrue(data["summary"]["checker_selftest_ok"],
                        "the checker self-test itself must pass")

    def test_full_run_is_red_while_carrying_the_blocked_status(self) -> None:
        code, out, data = self._run()
        self.assertNotEqual(code, 0, "the blocked pipeline must not exit 0")
        self.assertIsNotNone(data)
        summary = data["summary"]
        self.assertNotEqual(summary["final_status"], D.GREEN_STATUS)
        self.assertEqual(summary["overall_certification"], "BLOCKED")
        self.assertFalse(summary["independent_drat_checker_available"])
        # and the honest evidence for the block is present
        self.assertTrue(summary["environment_observations"])

    def test_a_child_crash_is_recorded_not_swallowed(self) -> None:
        code, out, data = self._run()
        obs = " ".join(data["summary"]["environment_observations"])
        self.assertIn("child process exited with code", obs)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=True)
