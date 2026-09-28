#!/usr/bin/env python3
"""Regression tests for the CNF completeness audit (encoder.audit_cnf_covers_lines).

The audit originally accepted a maximal line as "covered" if ANY ONE negative triple
clause for that line was present. The reviewer's counterexample: the n=5 main diagonal
has 5 cells, hence C(5,3) = 10 triples; keeping only ONE of those clauses still made the
audit report covers_all_lines: true, so G2 could approve an underconstrained formula and
make a later UNSAT meaningless.

Cases (each must behave as labelled):
  1. intact n=5 cell encoding                          -> GREEN (complete)
  2. only 1 of the 10 diagonal triples retained        -> RED
  3. 9 of the 10 diagonal triples retained             -> RED
  4. a triple on a different line removed              -> RED
  5. a network-encoded line whose semantics are intact -> GREEN via layer 2
  6. a network-encoded line with a weakened network    -> RED via layer 2
  7. n=4 and n=6 intact encodings                      -> GREEN

Run:  python test_cnf_audit_completeness.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "independent_verifier_r1")))

from encoder import (  # noqa: E402
    audit_cnf_covers_lines,
    encode_cells,
    maximal_lines,
)


def write_dimacs(cnf, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(cnf.dimacs())


def cell_var(n: int, x: int, y: int) -> int:
    """Cell variable numbering used by encode_cells: row-major over x then y."""
    order = [(xx, yy) for yy in range(1, n + 1) for xx in range(1, n + 1)]
    return order.index((x, y)) + 1


def drop_clauses_for_triples(cnf, triples_vars: set[tuple[int, int, int]]) -> int:
    """Remove the explicit negative triple clauses for the given var-triples. Returns count."""
    keep, removed = [], 0
    for cl in cnf.clauses:
        if len(cl) == 3 and all(v < 0 for v in cl):
            key = tuple(sorted(-v for v in cl))
            if key in triples_vars:
                removed += 1
                continue
        keep.append(cl)
    cnf.clauses = keep
    return removed


class TestCnfAuditCompleteness(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _audit(self, n: int, cnf) -> dict:
        path = os.path.join(self.root, f"n{n}.cnf")
        write_dimacs(cnf, path)
        return audit_cnf_covers_lines(n, path)

    # ---- GREEN ----

    def test_intact_n5_is_green(self) -> None:
        rep = self._audit(5, encode_cells(5, 2))
        self.assertTrue(rep["complete"], rep)
        self.assertEqual(rep["layer1_lines_with_missing_triple"], 0)
        self.assertEqual(rep["layer1_triples_present"], rep["layer1_triples_expected"])
        self.assertGreater(rep["layer1_triples_expected"], 0)

    def test_intact_n4_and_n6_are_green(self) -> None:
        for n in (4, 6):
            with self.subTest(n=n):
                rep = self._audit(n, encode_cells(n, 2))
                self.assertTrue(rep["complete"], rep)

    # ---- the reviewer's exact counterexample ----

    def test_n5_diagonal_keeping_only_one_triple_is_red(self) -> None:
        n = 5
        diag = [(i, i) for i in range(1, n + 1)]
        self.assertEqual(len(diag), 5, "the n=5 diagonal must have 5 cells")
        triples = list(combinations(diag, 3))
        self.assertEqual(len(triples), 10, "C(5,3) must be 10")

        cnf = encode_cells(n, 2)
        all_vars = {tuple(sorted(cell_var(n, x, y) for x, y in t)) for t in triples}
        # keep exactly ONE diagonal triple clause, drop the other nine
        keep_one = {sorted(all_vars)[0]}
        removed = drop_clauses_for_triples(cnf, all_vars - keep_one)
        self.assertEqual(removed, 9, "exactly nine of the ten diagonal triples must be removed")

        rep = self._audit(n, cnf)
        self.assertFalse(rep["complete"], "underconstrained formula must NOT pass the audit")
        self.assertEqual(rep["layer1_lines_with_missing_triple"], 1,
                         "the diagonal must be the line reported as incomplete")
        ex = rep["layer1_missing_examples"]
        self.assertEqual(len(ex), 1)
        self.assertEqual(ex[0]["n_expected"], 10)
        self.assertEqual(ex[0]["n_missing"], 9)

    def test_n5_diagonal_keeping_nine_triples_is_still_red(self) -> None:
        """Nine out of ten is still incomplete -- completeness is not a majority vote."""
        n = 5
        diag = [(i, i) for i in range(1, n + 1)]
        cnf = encode_cells(n, 2)
        all_vars = {tuple(sorted(cell_var(n, x, y) for x, y in t))
                    for t in combinations(diag, 3)}
        drop_clauses_for_triples(cnf, {sorted(all_vars)[0]})  # remove only one
        rep = self._audit(n, cnf)
        self.assertFalse(rep["complete"])
        self.assertEqual(rep["layer1_lines_with_missing_triple"], 1)
        self.assertEqual(rep["layer1_missing_examples"][0]["n_missing"], 1)

    def test_removing_a_triple_on_another_line_is_red(self) -> None:
        n = 5
        lines = maximal_lines(n, 3)
        # pick the first line that is not the main diagonal
        target = None
        for L in lines:
            if L != [(i, i) for i in range(1, n + 1)]:
                target = L
                break
        self.assertIsNotNone(target)
        cnf = encode_cells(n, 2)
        vs = {tuple(sorted(cell_var(n, x, y) for x, y in t)) for t in combinations(target, 3)}
        self.assertGreaterEqual(drop_clauses_for_triples(cnf, {sorted(vs)[0]}), 1)
        rep = self._audit(n, cnf)
        self.assertFalse(rep["complete"])

    # ---- layer 2: network-encoded lines ----

    def test_network_encoded_line_intact_is_green_via_layer2(self) -> None:
        """Force the network path by lowering explicit_limit, then check semantics."""
        n = 5
        cnf = encode_cells(n, 2)
        path = os.path.join(self.root, "n5_net.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0)
        # everything now goes through layer 2
        self.assertEqual(rep["layer1_explicit_lines"], 0)
        self.assertGreater(rep["layer2"]["lines_checked"], 0)
        self.assertEqual(rep["layer2"]["not_refuted"], [])
        self.assertTrue(rep["complete"], rep)

    def test_weakened_network_line_is_red_via_layer2(self) -> None:
        """Delete a whole line's constraint and confirm layer 2 refutes it.

        With explicit_limit=0 all lines go to layer 2, and removing the diagonal's ten
        clauses leaves the diagonal unconstrained, so at least one of its triples must be
        reported as satisfiable.
        """
        n = 5
        diag = [(i, i) for i in range(1, n + 1)]
        cnf = encode_cells(n, 2)
        all_vars = {tuple(sorted(cell_var(n, x, y) for x, y in t))
                    for t in combinations(diag, 3)}
        drop_clauses_for_triples(cnf, all_vars)
        path = os.path.join(self.root, "n5_broken_net.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0)
        self.assertFalse(rep["complete"])
        self.assertTrue(rep["layer2"]["not_refuted"], "a satisfiable triple must be reported")

    def test_unchecked_network_lines_make_audit_incomplete(self) -> None:
        """A bound that leaves network lines unchecked must not report completeness."""
        n = 5
        cnf = encode_cells(n, 2)
        path = os.path.join(self.root, "n5_partial.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0, semantic_max_lines=1)
        self.assertFalse(rep["complete"], "unchecked lines must not be certified")
        self.assertGreater(rep["layer2"]["lines_unchecked"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=True)
