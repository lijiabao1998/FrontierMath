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
    audit_orbit_cnf,
    encode_cells,
    encode_orbits,
    maximal_lines,
    orbits,
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

    def test_vacuous_formula_with_unrelated_contradiction_is_red(self) -> None:
        """The reviewer's exact counterexample for the semantic layer.

        Delete all ten n=5 diagonal constraints AND add an unrelated contradictory unit pair
        [1], [-1]. Before the vacuity guard, unit propagation on the whole formula reported a
        conflict for every assumed triple, so the audit returned complete: true while the
        diagonal was entirely unconstrained. It must now be RED and must report vacuity.
        """
        n = 5
        diag = [(i, i) for i in range(1, n + 1)]
        cnf = encode_cells(n, 2)
        all_vars = {tuple(sorted(cell_var(n, x, y) for x, y in t))
                    for t in combinations(diag, 3)}
        drop_clauses_for_triples(cnf, all_vars)
        cnf.add_clause([1])
        cnf.add_clause([-1])
        path = os.path.join(self.root, "n5_vacuous.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0)   # force everything to layer 2
        self.assertFalse(rep["complete"], "a vacuously refuted formula must not pass")
        self.assertIs(rep["layer2"].get("vacuous"), True)
        self.assertIs(rep["layer2"].get("formula_satisfiable"), False)
        self.assertIn("vacuous", rep["layer2"].get("vacuous_reason", "").lower())

    def test_satisfiable_formula_is_not_reported_vacuous(self) -> None:
        """The guard must not fire on a well-formed instance."""
        n = 5
        cnf = encode_cells(n, 2)
        path = os.path.join(self.root, "n5_ok.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0)
        self.assertIs(rep["layer2"].get("vacuous"), False)
        self.assertIs(rep["layer2"].get("formula_satisfiable"), True)
        self.assertTrue(rep["complete"])

    def test_unchecked_network_lines_make_audit_incomplete(self) -> None:
        """A bound that leaves network lines unchecked must not report completeness."""
        n = 5
        cnf = encode_cells(n, 2)
        path = os.path.join(self.root, "n5_partial.cnf")
        write_dimacs(cnf, path)
        rep = audit_cnf_covers_lines(n, path, explicit_limit=0, semantic_max_lines=1)
        self.assertFalse(rep["complete"], "unchecked lines must not be certified")
        self.assertGreater(rep["layer2"]["lines_unchecked"], 0)


class TestOrbitAudit(unittest.TestCase):
    """The orbit formulation needs its own audit.

    A reviewer showed that the cell audit misreads an orbit CNF: in `encode_orbits` many
    cells share one y[o] variable and the line constraints are weighted over orbit ids, so
    the cell variable mapping and the explicit/network classification are both wrong. On an
    intact n=3 rot2 instance the cell audit reported 7 of 8 lines missing.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, cnf, name):
        path = os.path.join(self.root, name)
        write_dimacs(cnf, path)
        return path

    def test_intact_n3_rot2_is_complete(self) -> None:
        """The reviewer's exact reproduction case."""
        path = self._write(encode_orbits(3, "rot2", 6), "n3_rot2.cnf")
        rep = audit_orbit_cnf(3, path, "rot2")
        self.assertTrue(rep["complete"], rep)
        self.assertEqual(rep["lines_with_unrefuted_violation"], 0)
        self.assertEqual(rep["local_vacuous_lines"], [])
        self.assertGreater(rep["lines_checked"], 0)

    def test_intact_n5_rot2_is_complete(self) -> None:
        path = self._write(encode_orbits(5, "rot2", 10), "n5_rot2.cnf")
        rep = audit_orbit_cnf(5, path, "rot2")
        self.assertTrue(rep["complete"], rep)

    def test_intact_n4_rot4_is_complete(self) -> None:
        path = self._write(encode_orbits(4, "rot4", 8), "n4_rot4.cnf")
        rep = audit_orbit_cnf(4, path, "rot4")
        self.assertTrue(rep["complete"], rep)

    def test_removing_a_line_gadget_makes_the_orbit_audit_red(self) -> None:
        """Delete every clause mentioning one line's orbit variables -> must be RED."""
        n, group = 5, "rot2"
        cnf = encode_orbits(n, group, 2 * n)
        orbs = orbits(n, __import__("encoder").SYMMETRY_GROUPS[group])
        cell_to_orb = {}
        for idx, o in enumerate(orbs):
            for cell in o:
                cell_to_orb[cell] = idx
        L = maximal_lines(n, 3)[0]
        lvars = {cell_to_orb[c] + 1 for c in L}
        before = len(cnf.clauses)
        cnf.clauses = [cl for cl in cnf.clauses if not any(abs(v) in lvars for v in cl)]
        removed = before - len(cnf.clauses)
        self.assertGreater(removed, 0, "the chosen line must have had a gadget")
        path = self._write(cnf, "n5_rot2_broken.cnf")
        rep = audit_orbit_cnf(n, path, group)
        self.assertFalse(rep["complete"], "a removed line gadget must be detected")
        self.assertTrue(rep["not_refuted"] or rep["local_vacuous_lines"])

    def test_unrelated_global_contradiction_does_not_make_the_orbit_audit_vacuous(self) -> None:
        """The local check must not be defeated by a contradiction elsewhere.

        This is the counterpart of the cell-audit vacuity bug: a global guard would mark
        everything vacuous, and no guard at all would mark everything refuted. The local
        sub-formula check is unaffected by clauses outside the line.
        """
        n, group = 5, "rot2"
        cnf = encode_orbits(n, group, 2 * n)
        # add a contradiction on a variable no line touches: introduce a fresh var via an
        # unused literal pair. Variable nvars+1 is fresh and appears in no line gadget.
        fresh = cnf.nvars + 1
        cnf.nvars = fresh
        cnf.add_clause([fresh])
        cnf.add_clause([-fresh])
        path = self._write(cnf, "n5_rot2_extra.cnf")
        rep = audit_orbit_cnf(n, path, group)
        # the line gadgets are untouched, so completeness is preserved and the audit is not
        # marked vacuous by the unrelated contradiction
        self.assertTrue(rep["complete"], rep)
        self.assertEqual(rep["local_vacuous_lines"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=True)
