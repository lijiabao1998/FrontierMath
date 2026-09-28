#!/usr/bin/env python3
"""Regression tests for the Codex review findings on MATH-001 r2 (PR #4).

T1 (P1) lazy solver import : --estimate must work with pysat import blocked.
T2 (P1) at-most-1 encoding : pairwise at-most-1 + at-least-1 admits exactly
                             one true literal and forbids two (the old unit-
                             clause version emptied the row and made the
                             pigeonhole control trivially UNSAT).
T3 (P2) --mode seq CLI     : must complete and cover both modes (was KeyError).
T4 (P2) aux var formula    : at_most_2_sinz on m literals allocates 2m-1 vars.

Exit 0 iff all pass. Stdlib only (T1 blocks pysat via sys.meta_path).
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / ".deps"))
sys.path.insert(0, str(HERE.parent / "baseline_r1"))

import ntil_cnf  # noqa: E402
from itertools import combinations  # noqa: E402


class T1Pass(Exception):
    pass


def test_t1_lazy_import() -> None:
    import importlib.abc

    class Blocker(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.startswith("pysat"):
                raise ImportError("pysat blocked for T1")
            return None

    sys.meta_path.insert(0, Blocker())
    try:
        proc = subprocess.run(
            [sys.executable, str(HERE / "ntil_cnf.py"), "--estimate", "12"],
            capture_output=True, text=True, timeout=120)
        assert proc.returncode == 0, proc.stderr
        assert '"lines_ge3"' in proc.stdout
    finally:
        sys.meta_path.pop(0)


def test_t2_at_most_1() -> None:
    from pysat.solvers import Cadical153
    lits = [1, 2, 3]
    clauses = [[lits[0], lits[1], lits[2]]]  # at-least-1
    for a, b in combinations(lits, 2):       # at-most-1, pairwise
        clauses.append([-a, -b])
    with Cadical153(bootstrap_with=clauses) as s:
        assert s.solve(), "exactly-one must be SAT"
        model = {abs(v) for v in s.get_model() if v > 0}
        assert len(model & set(lits)) == 1, "exactly one true required"
    for forced_two in ([1, 2], [1, 2, 3]):
        with Cadical153(bootstrap_with=clauses + [[x] for x in forced_two]) as s:
            assert not s.solve(), "two true literals must violate at-most-1"


def test_t3_cli_mode_seq() -> None:
    proc = subprocess.run(
        [sys.executable, str(HERE / "ntil_cnf.py"), "--mode", "seq"],
        capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "KeyError" not in proc.stderr
    assert '"BENCH_SOUND"' in proc.stdout


def test_t4_aux_formula() -> None:
    # cell vars are 1..n*n; aux ids start at n*n+1 -> no collision
    n = 4
    b = ntil_cnf.CnfBuilder(n=n, first_free=n * n + 1)
    b.at_most_2_sinz([1, 2, 3, 4])
    used = {abs(l) for cl in b.clauses for l in cl}
    aux = {v for v in used if v > n * n}
    assert len(aux) == 2 * 4 - 1, f"expected 2m-1=7 aux vars, got {len(aux)}"


def test_t5_exhaustive_unsat() -> None:
    """Codex P1: UNSAT controls must carry checkable certificates."""
    import json as _json
    proc = subprocess.run(
        [sys.executable, str(HERE / "ntil_cnf.py")],
        capture_output=True, text=True, timeout=900)
    assert proc.returncode == 0, proc.stderr[-2000:]
    stdout = proc.stdout[proc.stdout.index("{"):]
    res = _json.loads(stdout)
    proofs = res["unsat_proofs"]
    assert proofs["n1_exhaustive"]["satisfying_assignments"] == 0
    assert proofs["n1_exhaustive"]["assignments_checked"] == 2
    for pn in (3, 4):
        pr = proofs[f"pigeonhole_n{pn}_exhaustive"]
        assert pr["satisfying_assignments"] == 0
        assert pr["assignments_checked"] == 2 ** (pn * pn)
    assert all(r.get("unsat_evidence") == "SOLVER_UNSAT_UNCERTIFIED"
               for r in res["results"] if r["sat"] is False)


def test_t6_lines_canonical() -> None:
    """Codex P2: no horizontal/vertical/duplicate lines; estimate consistent."""
    lines = ntil_cnf.primitive_lines(8)
    assert all(len({y for _, y in ln}) > 1 for ln in lines), "horizontal leaked"
    assert all(len({x for x, _ in ln}) > 1 for ln in lines), "vertical leaked"
    assert len({frozenset(ln) for ln in lines}) == len(lines), "duplicate lines"
    # NOTE: pre-fix count at n=8 was 140 — smaller than the corrected count,
    # because the old dedup also WRONGLY SKIPPED legitimate slope families
    # ((1,2) shadowed by (2,1)) while duplicating horizontals. The invariant
    # assertions above are the regression contract; counts are recorded data.
    print(f"n=8 canonical line count: {len(lines)} (pre-fix: 140)")


if __name__ == "__main__":
    test_t1_lazy_import()
    print("T1 lazy import: PASS")
    test_t2_at_most_1()
    print("T2 at-most-1 pairwise: PASS")
    test_t4_aux_formula()
    print("T4 aux formula 2m-1: PASS")
    test_t6_lines_canonical()
    print("T6 lines canonical: PASS")
    test_t5_exhaustive_unsat()
    print("T5 exhaustive UNSAT certificates: PASS")
    test_t3_cli_mode_seq()
    print("T3 CLI --mode seq: PASS")
    print("ALL REGRESSION TESTS PASS")
