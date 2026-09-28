#!/usr/bin/env python3
"""Regression tests for fetch_third_party.py -- provenance verification must fail closed.

These exist because the original script had a fail-open bug: with `--check`, a MISSING
file printed MISSING and still exited 0 with "all present and verified", so the
documented provenance check could certify sources that were never read.

Each case below is a real end-to-end CLI invocation (subprocess, real exit code) against
a temporary root and a synthetic source table, so it tests the operator-visible
behaviour, not an internal helper.

    required file missing                -> RED  (exit != 0, no success banner)
    wrong hash                           -> RED
    size mismatch (right hash, wrong len)-> RED   [unreachable in practice, but asserted]
    hash mismatch on --check             -> RED
    --code-inputs-only with missing input-> RED
    download failure (bad url)           -> RED
    correct file present                 -> GREEN (exit 0, banner printed)
    --check with everything present      -> GREEN

Run:  python test_fetch_third_party.py            (human-readable)
      python test_fetch_third_party.py -v         (unittest verbosity)
Exits non-zero if any case fails.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "fetch_third_party.py")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write_sources(root: str, entries: dict[str, tuple[str, int, str]]) -> str:
    p = os.path.join(root, "sources.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({k: {"url": u, "bytes": n, "sha256": h} for k, (u, n, h) in entries.items()}, fh)
    return p


def _run(root: str, sources_json: str | None, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, SCRIPT, "--root", root]
    if sources_json:
        cmd += ["--sources-json", sources_json]
    cmd += list(extra)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


BANNER = "RESULT: all present and verified"
BAD = "RESULT: PROBLEMS FOUND"


class TestProvenanceFailClosed(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.payload = b"contents-of-the-third-party-file\n"
        self.good_hash = _sha(self.payload)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # ---- RED cases ----

    def test_required_file_missing_check_mode_is_red(self) -> None:
        """The exact bug the reviewer found: --check must not pass on a missing file."""
        sj = _write_sources(self.root, {"req.txt": ("https://example.invalid/req.txt",
                                                   len(self.payload), self.good_hash)})
        r = _run(self.root, sj, "--check")
        self.assertNotEqual(r.returncode, 0, "missing file must exit non-zero")
        self.assertNotIn(BANNER, r.stdout, "must not print the success banner")
        self.assertIn("MISSING", r.stdout)

    def test_required_file_missing_without_download_failure_url_is_red(self) -> None:
        """--code-inputs-only with the code inputs absent must be RED."""
        sj = _write_sources(self.root, {
            "known_solutions_1997.txt": ("https://example.invalid/x", len(self.payload), self.good_hash),
        })
        r = _run(self.root, sj, "--check", "--code-inputs-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(BANNER, r.stdout)
        self.assertIn("MISSING", r.stdout)

    def test_wrong_hash_on_disk_is_red(self) -> None:
        p = os.path.join(self.root, "req.txt")
        with open(p, "wb") as fh:
            fh.write(b"different-content\n")
        sj = _write_sources(self.root, {"req.txt": ("https://example.invalid/req.txt",
                                                   len(self.payload), self.good_hash)})
        r = _run(self.root, sj, "--check")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(BANNER, r.stdout)
        self.assertIn("MISMATCH", r.stdout)

    def test_size_mismatch_on_disk_is_red(self) -> None:
        # write a file whose size differs from the declared size but whose hash matches
        # the declared hash: impossible for one file, so declare a wrong size with the
        # correct hash of the actual bytes -- size check must still trip.
        p = os.path.join(self.root, "req.txt")
        with open(p, "wb") as fh:
            fh.write(self.payload)
        sj = _write_sources(self.root, {"req.txt": ("https://example.invalid/req.txt",
                                                   len(self.payload) + 1, self.good_hash)})
        r = _run(self.root, sj, "--check")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("size", r.stdout.lower())

    def test_download_failure_is_red(self) -> None:
        """No --check: the file is absent and the url cannot be reached."""
        sj = _write_sources(self.root, {"req.txt": ("https://127.0.0.1:9/definitely-not-listening",
                                                   len(self.payload), self.good_hash)})
        r = _run(self.root, sj)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(BANNER, r.stdout)
        self.assertIn("FAILED", r.stdout)

    # ---- GREEN cases ----

    def test_correct_file_is_green(self) -> None:
        p = os.path.join(self.root, "req.txt")
        with open(p, "wb") as fh:
            fh.write(self.payload)
        sj = _write_sources(self.root, {"req.txt": ("https://example.invalid/req.txt",
                                                   len(self.payload), self.good_hash)})
        r = _run(self.root, sj, "--check")
        self.assertEqual(r.returncode, 0, f"expected green, got:\n{r.stdout}\n{r.stderr}")
        self.assertIn(BANNER, r.stdout)

    def test_fetched_file_then_check_is_green(self) -> None:
        """Fetch from a file:// url (no network), which must verify and go green."""
        src = os.path.join(self.root, "origin.bin")
        with open(src, "wb") as fh:
            fh.write(self.payload)
        url = "file:///" + src.replace("\\", "/").lstrip("/")
        sj = _write_sources(self.root, {"dl/req.txt": (url, len(self.payload), self.good_hash)})
        r = _run(self.root, sj)
        self.assertEqual(r.returncode, 0, f"fetch expected green, got:\n{r.stdout}\n{r.stderr}")
        r2 = _run(self.root, sj, "--check")
        self.assertEqual(r2.returncode, 0, f"re-check expected green, got:\n{r2.stdout}")
        self.assertIn(BANNER, r2.stdout)

    def test_empty_selection_is_red(self) -> None:
        """A selection that matches nothing must not report success."""
        sj = _write_sources(self.root, {"not_a_code_input.txt": ("https://example.invalid/x",
                                                               1, _sha(b"x"))})
        r = _run(self.root, sj, "--check", "--code-inputs-only")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn(BANNER, r.stdout)

    # ---- real table ----

    def test_real_table_present_and_verified(self) -> None:
        """Against the actual on-disk corpus (skipped if it was not fetched)."""
        r = subprocess.run([sys.executable, SCRIPT, "--check"], capture_output=True,
                           text=True, timeout=600)
        if "MISSING" in r.stdout:
            self.skipTest("corpus not fetched on this machine; run fetch_third_party.py first")
        self.assertEqual(r.returncode, 0, f"real table not green:\n{r.stdout[-2000:]}")
        self.assertIn(BANNER, r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=True)
