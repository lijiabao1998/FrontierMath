#!/usr/bin/env python3
"""MATH-001 / n=75 attack bench -- encoders (DeepSeek r1).

Two formulations of  D(n) = 2n  as a decision problem, plus symmetry machinery.
Everything here is generated from first principles; see formulation.md for the
derivations and the soundness proofs.

Formulation A -- cell-based Boolean model
    variables   x[r][c]  (1 iff cell (r,c) is selected),  1-indexed, 1..n
    (A1) exactly 2 selected per row                 (rows are lines)
    (A2) at most 2 selected on every maximal line with >= 3 grid points
    (A1)+(A2) already force |S| = 2n, so no separate cardinality is needed.

Formulation B -- orbit-based Boolean model
    Fix a subgroup G <= D4. Variables y[o] for each G-orbit o.
    (B1) each orbit is either fully selected or empty
    (B2) weighted at-most-2 on every maximal line
    (B3) centre fixed-cell parity (odd n, rotation subgroups)
    Sound ONLY as a restricted search: a model here is a real 2n-set, but UNSAT
    here does NOT refute D(n). This distinction is enforced in limitations.md.

Sound symmetry breaking (Formulation A)
    (A3) the solution matrix is lexicographically <= its transpose.
    Theorem: every D4-orbit of subsets contains at least one S with S <= S^T, so
    (A3) never removes all representatives of an orbit -- it is sound for the
    existence question.  See formulation.md section 5 for the proof.

NOT implemented here on purpose: any claim of n=75 UNSAT. No DRAT/LRAT proof is
produced, so no UNSAT result from this file may be reported as a theorem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from itertools import combinations
from math import comb, gcd
from typing import Iterable, Sequence

# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #


def maximal_lines(n: int, minpts: int = 3) -> list[list[tuple[int, int]]]:
    """All maximal sets of >= minpts collinear grid points, as 1-indexed cells.

    A set is a candidate for a collinear triple iff it lies on a line meeting the
    grid in >= 3 points; such a line is exactly { a*x + b*y = c } for a primitive
    direction (a,b) and an offset c. We enumerate offsets by grouping cells.
    """
    out: list[list[tuple[int, int]]] = []
    seen_dirs: set[tuple[int, int]] = set()
    for a in range(-(n - 1), n):
        for b in range(-(n - 1), n):
            if a == 0 and b == 0:
                continue
            if gcd(abs(a), abs(b)) != 1:
                continue
            key = (-a, -b) if (a < 0 or (a == 0 and b < 0)) else (a, b)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)

            groups: dict[int, list[tuple[int, int]]] = {}
            for x in range(1, n + 1):
                for y in range(1, n + 1):
                    groups.setdefault(a * x + b * y, []).append((x, y))
            for cells in groups.values():
                if len(cells) >= minpts:
                    cells.sort()
                    out.append(cells)
    return out


# --------------------------------------------------------------------------- #
# symmetry
# --------------------------------------------------------------------------- #


def sym_maps(n: int) -> dict[str, "callable"]:
    """The 8 elements of D4 acting on 1-indexed cell coordinates."""
    r = n + 1
    return {
        "iden": lambda x, y: (x, y),
        "rot2": lambda x, y: (r - x, r - y),
        "rot4": lambda x, y: (r - y, x),
        "rot4i": lambda x, y: (y, r - x),
        "dia1": lambda x, y: (y, x),
        "dia2": lambda x, y: (r - y, r - x),
        "ort1": lambda x, y: (x, r - y),
        "ort2": lambda x, y: (r - x, y),
    }


# named classes as used by Flammenkamp's database.  `rct4` is deliberately absent
# from the generator list: it is a SEARCH SPACE (rotation orbits off the diagonals,
# free choice on them), not a group of the plane, exactly as the source page says
# ("This new class, which is not a symmetry class of the grid").  This round
# verified as a property of the published records that the `c` entries realize
# exactly the 180-degree rotation (see symmetry_probe.py), while the `o` entries
# realize the full 90-degree rotation.
SYMMETRY_GROUPS: dict[str, list[str]] = {
    "iden": ["iden"],
    "rot2": ["iden", "rot2"],
    "rot4": ["iden", "rot2", "rot4", "rot4i"],
    "dia1": ["iden", "dia1"],
    "dia2": ["iden", "dia2"],
    "ort1": ["iden", "ort1"],
    "ort2": ["iden", "ort2"],
    "full": ["iden", "rot2", "rot4", "rot4i", "dia1", "dia2", "ort1", "ort2"],
}


def orbits(n: int, gens: Sequence[str]) -> list[list[tuple[int, int]]]:
    maps = sym_maps(n)
    fs = [maps[g] for g in gens]
    cells = [(x, y) for x in range(1, n + 1) for y in range(1, n + 1)]
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for start in cells:
        if start in seen:
            continue
        orb = {start}
        frontier = [start]
        while frontier:
            cur = frontier.pop()
            for f in fs:
                img = f(*cur)
                if img not in orb:
                    orb.add(img)
                    frontier.append(img)
        seen |= orb
        out.append(sorted(orb))
    return out


def orbit_feasibility(n: int, gens: Sequence[str], target: int) -> dict:
    """Can a target-size set be invariant under <gens>?  Decided by orbit sizes.

    A <gens>-invariant set is a union of orbits, so its size is a sum of the sizes
    of the orbits it contains. Crucially each orbit may be used AT MOST ONCE, so
    this is a bounded knapsack, not an unbounded coin problem: for odd n under a
    rotation there is exactly one orbit of size 1 (the centre), and allowing two
    copies of it would wrongly make 2n reachable.
    """
    orbs = orbits(n, gens)
    sizes = [len(o) for o in orbs]
    avail: dict[int, int] = {}
    for s in sizes:
        avail[s] = avail.get(s, 0) + 1

    # bounded reachability over orbit sizes with their multiplicities
    reachable: set[int] = {0}
    for s, count in sorted(avail.items()):
        nxt = set(reachable)
        for r in list(reachable):
            for c in range(1, count + 1):
                if r + c * s <= target:
                    nxt.add(r + c * s)
        reachable = nxt
    feasible = target in reachable

    hs = sorted(avail)
    reason = None
    if not feasible:
        if set(hs) == {1, 4} and avail.get(1, 0) == 1:
            if target % 4 not in (0, 1):
                reason = (
                    f"exactly one orbit of size 1 (the centre) and the rest of size 4: "
                    f"any invariant set has size in {{0,1}} mod 4, but target={target} ≡ {target % 4}"
                )
        elif set(hs) == {4}:
            if target % 4 != 0:
                reason = f"all orbits have size 4, so size ≡ 0 (mod 4), but target={target} ≡ {target % 4}"
        if reason is None:
            reason = (
                f"target {target} is not a sum of the available orbit sizes "
                f"{sorted(avail.items())}"
            )
    return {
        "n": n,
        "group": list(gens),
        "orbit_size_multiset": {str(k): v for k, v in sorted(avail.items())},
        "n_orbits": len(orbs),
        "target": target,
        "feasible": feasible,
        "reason": reason,
    }


# --------------------------------------------------------------------------- #
# CNF construction
# --------------------------------------------------------------------------- #


class CNF:
    """Tseitin-free CNF builder with a human-readable variable map."""

    def __init__(self, n: int, name: str) -> None:
        self.n = n
        self.name = name
        self.nvars = 0
        self.clauses: list[list[int]] = []
        self.var_of: dict = {}
        self.comments: list[str] = []

    def new_var(self, key) -> int:
        if key not in self.var_of:
            self.nvars += 1
            self.var_of[key] = self.nvars
        return self.var_of[key]

    def add_clause(self, lits: Iterable[int]) -> None:
        cl = list(lits)
        if not cl:
            raise ValueError("empty clause would make the instance trivially UNSAT")
        self.clauses.append(cl)

    def add_at_most(self, lits: Sequence[int], k: int, big: bool = False) -> None:
        """At most k of `lits` true.

        Two encodings, chosen by cost:
          * explicit (k+1)-subset clauses when that is small. This is exact and,
            importantly, for k=2 and |lits|=3 it yields the single clause
            (¬a ∨ ¬b ∨ ¬c), which is what audit_cnf_covers_lines looks for.
          * otherwise a sequential-counter cardinality network from pysat.card
            (pure-Python, part of the already-present python-sat; no new
            dependency is installed by this round).
        `big=True` forces the network encoding.
        """
        m = len(lits) - k
        if m <= 0:
            return
        n_enum_clauses = comb(len(lits), k + 1)
        if not big and n_enum_clauses <= 4096:
            for sub in combinations(lits, k + 1):
                self.add_clause([-v for v in sub])
            return
        from pysat.card import CardEnc, EncType

        enc = CardEnc.atmost(lits=list(lits), bound=k, top_id=self.nvars, encoding=EncType.seqcounter)
        self.nvars = enc.nv
        for cl in enc.clauses:
            self.clauses.append(list(cl))

    def add_at_least(self, lits: Sequence[int], k: int) -> None:
        if k <= 0:
            return
        need = len(lits) - k + 1
        if need <= 0:
            return
        if comb(len(lits), need) <= 4096:
            for sub in combinations(lits, need):
                self.add_clause(list(sub))
            return
        from pysat.card import CardEnc, EncType

        enc = CardEnc.atleast(lits=list(lits), bound=k, top_id=self.nvars, encoding=EncType.seqcounter)
        self.nvars = enc.nv
        for cl in enc.clauses:
            self.clauses.append(list(cl))

    def add_exactly(self, lits: Sequence[int], k: int) -> None:
        self.add_at_most(lits, k)
        self.add_at_least(lits, k)

    def add_equiv_and(self, out: int, lits: Sequence[int]) -> None:
        """out <-> AND(lits)."""
        for v in lits:
            self.add_clause([-out, v])
        self.add_clause([out] + [-v for v in lits])

    def dimacs(self) -> str:
        lines = [f"p cnf {self.nvars} {len(self.clauses)}"]
        for cl in self.clauses:
            lines.append(" ".join(str(v) for v in cl) + " 0")
        return "\n".join(lines) + "\n"

    def sha256(self) -> str:
        return hashlib.sha256(self.dimacs().encode()).hexdigest()


# --------------------------------------------------------------------------- #
# Formulation A: cell-based
# --------------------------------------------------------------------------- #


def encode_cells(n: int, per_row: int = 2, lex_break: bool = False,
                 extra_lines: list[list[tuple[int, int]]] | None = None) -> CNF:
    """Cell-based CNF: exactly `per_row` per row, at most 2 on every maximal line.

    `per_row=2` (default) is the D(n)=2n question.  `per_row=0` is used for
    controls. `extra_lines` lets a caller inject additional forbidden line
    families (used by the negative tests).
    """
    cnf = CNF(n, f"cell_n{n}_perrow{per_row}")
    cnf.comments.append(f"Formulation A (cell-based), n={n}, per_row={per_row}")

    for x in range(1, n + 1):
        for y in range(1, n + 1):
            cnf.new_var(("x", x, y))

    # (A1) exactly per_row selected per row
    for y in range(1, n + 1):
        cnf.add_exactly([cnf.var_of[("x", x, y)] for x in range(1, n + 1)], per_row)

    # (A2) at most 2 selected on every maximal line with >= 3 points
    lines = maximal_lines(n, 3)
    if extra_lines:
        lines = lines + extra_lines
    for cells in lines:
        cnf.add_at_most([cnf.var_of[("x", x, y)] for (x, y) in cells], 2)

    if lex_break:
        # (A3) S <=lex S^T, i.e. row-major(S) <= row-major(transpose(S)).
        # Sound for existence: see formulation.md section 5.
        # Compare the two equal-length bit vectors a = (x[1][*],...,x[n][*]) and
        # b = (x[*][1],...,x[*][n]) lexicographically with a <= b.
        a = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]   # row-major
        b = [(y, x) for y in range(1, n + 1) for x in range(1, n + 1)]   # transposed order
        # p_i <-> (a_j == b_j for all j < i)
        prev_eq: list[int] = []
        eq_prefix: list[int] = []
        for i in range(len(a)):
            if i == 0:
                eq_prefix.append(True)  # sentinel: empty prefix is equal
                continue
            va = cnf.var_of[("x", *a[i - 1])]
            vb = cnf.var_of[("x", *b[i - 1])]
            # eq of this position: (va and vb) or (not va and not vb)
            if i == 1:
                e = cnf.new_var(("eq", 0))
                cnf.add_clause([-e, va, -vb])
                cnf.add_clause([-e, -va, vb])
                cnf.add_clause([e, va, vb])
                cnf.add_clause([e, -va, -vb])
                eq_prefix.append(e)
            else:
                e = cnf.new_var(("eq", i - 1))
                p = eq_prefix[i - 1]
                # e <-> p and (va == vb)
                same_hi = cnf.new_var(("same", i - 1))
                cnf.add_clause([-same_hi, va, -vb])
                cnf.add_clause([-same_hi, -va, vb])
                cnf.add_clause([same_hi, va, vb])
                cnf.add_clause([same_hi, -va, -vb])
                cnf.add_clause([-e, p])
                cnf.add_clause([-e, same_hi])
                cnf.add_clause([e, -p, -same_hi])
                eq_prefix.append(e)
        # For every position i: (prefix equal up to i) => a_i <= b_i, i.e.
        # not(prefix_eq and a_i=1 and b_i=0)
        for i in range(len(a)):
            va = cnf.var_of[("x", *a[i])]
            vb = cnf.var_of[("x", *b[i])]
            if i == 0:
                cnf.add_clause([-va, vb])
            else:
                p = eq_prefix[i]
                cnf.add_clause([-p, -va, vb])
        cnf.comments.append("(A3) lex-leader S <= S^T symmetry breaking (sound)")

    return cnf


# --------------------------------------------------------------------------- #
# Formulation B: orbit-based
# --------------------------------------------------------------------------- #


def encode_orbits(n: int, group: str, target: int) -> CNF:
    """Orbit-based CNF for a named symmetry group.

    Variables y[o]: the whole orbit is selected. A line's weighted count is
    sum_o |o ∩ line| * y_o, which must be <= 2.
    """
    gens = SYMMETRY_GROUPS[group]
    orbs = orbits(n, gens)
    cnf = CNF(n, f"orbit_n{n}_{group}")
    cnf.comments.append(f"Formulation B (orbit-based), n={n}, group={group}, target={target}")
    for idx, _ in enumerate(orbs):
        cnf.new_var(("y", idx))
    yv = [cnf.var_of[("y", i)] for i in range(len(orbs))]

    # (B3) exact weighted size, encoded in one uniform way.
    # A <gens>-invariant set is a union of orbits, so its size is sum_o |o| * y_o.
    # "sum_o |o| y_o = target" is a weighted cardinality equality. We avoid needing
    # a weighted encoder by replicating each orbit variable |o| times, tying the
    # copies to their original by equivalence, and using one ordinary cardinality
    # equality over the replicated literals. Weights 1/2/4 are small, so the
    # replica count is at most 4 * (#orbits) = O(n^2).
    replicated: list[int] = []
    for idx, o in enumerate(orbs):
        orig = yv[idx]
        for k in range(len(o)):
            if k == 0:
                replicated.append(orig)
                continue
            copy = cnf.new_var(("ycopy", idx, k))
            cnf.add_clause([-orig, copy])   # orig -> copy
            cnf.add_clause([-copy, orig])   # copy -> orig
            replicated.append(copy)
    cnf.add_exactly(replicated, target)
    cnf.comments.append(
        f"(B3) weighted size sum_o |o|*y_o = {target}, encoded as an ordinary "
        f"cardinality equality over {len(replicated)} replicated literals"
    )
    if target % 4 == 2 and max(len(o) for o in orbs) == 4:
        cnf.comments.append(
            "(B3 parity) orbit sizes here are 1 and 4, so any invariant set has size "
            "0 or 1 (mod 4); target 2n = 2 (mod 4) is unreachable -- the instance is "
            "UNSAT by orbit counting alone, before any geometry constraint"
        )

    # (B2) weighted at-most-2 per line, via a cell -> orbit index
    cell_to_orb: dict[tuple[int, int], int] = {}
    for idx, o in enumerate(orbs):
        for cell in o:
            cell_to_orb[cell] = idx
    for cells in maximal_lines(n, 3):
        touched: dict[int, int] = {}
        for cell in cells:
            idx = cell_to_orb[cell]
            touched[idx] = touched.get(idx, 0) + 1
        items = [(cnf.var_of[("y", i)], w) for i, w in touched.items()]
        heavy = [v for v, w in items if w >= 2]
        light = [v for v, w in items if w == 1]
        # any two of the heavy orbits already give >= 4 points on the line
        for i, v in enumerate(heavy):
            for u in heavy[i + 1:]:
                cnf.add_clause([-v, -u])
        # a heavy orbit plus any other orbit already exceeds 2
        for v in heavy:
            for u in light:
                cnf.add_clause([-v, -u])
        # three light orbits reach 3 points
        for sub in combinations(light, 3):
            cnf.add_clause([-v for v in sub])
    return cnf


# --------------------------------------------------------------------------- #
# DIMACS audit: does the formula actually express the problem?
# --------------------------------------------------------------------------- #


def unit_propagation_conflict(clauses: Sequence[Sequence[int]],
                              assumptions: Sequence[int]) -> bool:
    """True iff unit propagation on `clauses` under `assumptions` reaches a conflict.

    Used by the CNF audit's layer 2 (semantic completeness). Deliberately simple -- it
    rescans the clause list until a fixed point -- because the audit's job is to be
    obviously correct rather than fast. A False result is NOT a verdict that the triple
    is allowed; layer 2 escalates to a real SAT call in that case.
    """
    assign: dict[int, bool] = {}
    for lit in assumptions:
        v, val = abs(lit), lit > 0
        if v in assign and assign[v] != val:
            return True
        assign[v] = val
    changed = True
    while changed:
        changed = False
        for cl in clauses:
            unassigned = []
            satisfied = False
            for lit in cl:
                v = abs(lit)
                if v in assign:
                    if assign[v] == (lit > 0):
                        satisfied = True
                        break
                else:
                    unassigned.append(lit)
            if satisfied:
                continue
            if not unassigned:
                return True
            if len(unassigned) == 1:
                lit = unassigned[0]
                v, val = abs(lit), lit > 0
                if v in assign:
                    if assign[v] != val:
                        return True
                else:
                    assign[v] = val
                    changed = True
    return False


def audit_cnf_covers_lines(n: int, dimacs_path: str, var_of_cell=None,
                           semantic_check: bool = True,
                           semantic_max_lines: int | None = None,
                           explicit_limit: int = 4096) -> dict:
    """Link (1) of certification: does the formula actually express the problem?

    A previous version of this audit accepted a line as covered if AT LEAST ONE
    negative triple clause for it was present. That is unsound: for a line with
    k > 3 cells the other triples may still be selectable, so an underconstrained
    formula would pass. This version requires COMPLETENESS, in two layers:

    LAYER 1 -- explicit completeness (exact, no solver, no propagation).
      For every maximal line L that the encoder represents with explicit triple
      clauses (that is, C(|L|,3) <= explicit_limit, matching CNF.add_at_most), the
      DIMACS must contain ALL C(|L|,3) clauses (¬a ∨ ¬b ∨ ¬c) over the triples of L.
      A line with any missing triple is reported, with examples.

    LAYER 2 -- semantic completeness for lines encoded by a cardinality network.
      A network-encoded at-most-2 has no explicit triples, so layer 1 cannot speak
      for it. For those lines the audit verifies the SEMANTICS directly: for every
      3-subset T of L, the formula conjoined with the unit assumptions T must be
      UNSATISFIABLE. Unit propagation is tried first; anything it cannot refute is
      escalated to a real SAT call. This is encoding-agnostic and is what makes the
      audit meaningful for large k.

      `semantic_max_lines` bounds how many network lines are checked this way; if the
      bound bites, `semantic_lines_unchecked` is non-zero and `covers_all_lines` is
      reported as False with `complete: false`, rather than silently passing.

    `covers_all_lines` is True only when layer 1 found no missing triple AND every
    network line was semantically verified (or there were none).
    """
    order = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]
    var_of = {cell: i + 1 for i, cell in enumerate(order)}
    if var_of_cell is not None:
        var_of = var_of_cell

    neg_triples: set[tuple[int, int, int]] = set()
    clauses: list[list[int]] = []
    nvars_declared = 0
    with open(dimacs_path, "r", encoding="utf-8") as fh:
        for ln in fh:
            if not ln:
                continue
            if ln[0] == "c":
                continue
            if ln[0] == "p":
                parts = ln.split()
                nvars_declared = int(parts[2])
                continue
            lits = [int(t) for t in ln.split() if t != "0"]
            clauses.append(lits)
            if len(lits) == 3 and all(v < 0 for v in lits):
                neg_triples.add(tuple(sorted(-v for v in lits)))

    lines = maximal_lines(n, 3)
    explicit_lines = [L for L in lines if comb(len(L), 3) <= explicit_limit]
    network_lines = [L for L in lines if comb(len(L), 3) > explicit_limit]

    # ---- layer 1 ----
    missing_examples: list[dict] = []
    lines_with_missing = 0
    triples_expected = 0
    triples_present = 0
    for L in explicit_lines:
        want = [tuple(sorted(var_of[c] for c in sub)) for sub in combinations(L, 3)]
        triples_expected += len(want)
        miss = [w for w in want if w not in neg_triples]
        triples_present += len(want) - len(miss)
        if miss:
            lines_with_missing += 1
            if len(missing_examples) < 5:
                missing_examples.append({"line": L, "n_expected": len(want),
                                         "n_missing": len(miss), "missing": miss[:5]})

    # ---- layer 2 ----
    sem = {
        "lines_total": len(network_lines),
        "lines_checked": 0,
        "lines_unchecked": 0,
        "triples_checked": 0,
        "refuted_by_unit_propagation": 0,
        "refuted_by_sat": 0,
        "not_refuted": [],
    }
    if semantic_check and network_lines:
        # VACUITY GUARD. The semantic layer asks whether F AND T is UNSAT for each triple T.
        # If F itself is UNSAT -- for any reason, including a contradiction unrelated to the
        # line constraints -- then F AND T is UNSAT for EVERY T and the layer passes
        # vacuously. A reviewer demonstrated exactly this by deleting all ten n=5 diagonal
        # constraints and adding the units [1] and [-1]: the audit still returned
        # complete: true. The guard below establishes that F is satisfiable before any
        # triple is tested, and reports the layer as vacuous rather than complete if it is not.
        try:
            from pysat.solvers import Cadical153 as _C
            with _C(bootstrap_with=clauses) as _s:
                formula_satisfiable = bool(_s.solve())
        except Exception:  # noqa: BLE001
            formula_satisfiable = None
        sem["formula_satisfiable"] = formula_satisfiable
        if formula_satisfiable is False:
            sem["vacuous"] = True
            sem["vacuous_reason"] = (
                "the formula is UNSATISFIABLE, so every triple would be reported as refuted "
                "regardless of the line constraints. The semantic layer is vacuous and does "
                "NOT establish anything about at-most-2 on the lines.")
            sem["lines_unchecked"] = len(network_lines)
            network_lines = []
        elif formula_satisfiable is None:
            sem["vacuous"] = True
            sem["vacuous_reason"] = ("no solver available to establish that the formula is "
                                     "satisfiable, so the semantic layer cannot be trusted")
            sem["lines_unchecked"] = len(network_lines)
            network_lines = []
        else:
            sem["vacuous"] = False
        todo = network_lines
        if semantic_max_lines is not None and len(todo) > semantic_max_lines:
            sem["lines_unchecked"] = len(todo) - semantic_max_lines
            todo = todo[:semantic_max_lines]
        try:
            from pysat.solvers import Cadical153
            have_solver = True
        except Exception:  # noqa: BLE001
            have_solver = False
        for L in todo:
            sem["lines_checked"] += 1
            lits3 = [[var_of[c] for c in sub] for sub in combinations(L, 3)]
            bad = None
            for T in lits3:
                sem["triples_checked"] += 1
                if unit_propagation_conflict(clauses, list(T)):
                    sem["refuted_by_unit_propagation"] += 1
                    continue
                if not have_solver:
                    bad = {"line": L, "triple": T, "reason": "no solver available to escalate"}
                    break
                with Cadical153(bootstrap_with=clauses) as s:
                    sat = s.solve(assumptions=list(T))
                if sat:
                    bad = {"line": L, "triple": T, "reason": "triple is satisfiable: at-most-2 NOT enforced"}
                    break
                sem["refuted_by_sat"] += 1
            if bad is not None and len(sem["not_refuted"]) < 5:
                sem["not_refuted"].append(bad)
    elif network_lines:
        sem["lines_unchecked"] = len(network_lines)

    complete = (
        lines_with_missing == 0
        and sem["lines_unchecked"] == 0
        and not sem["not_refuted"]
        and sem.get("vacuous") is not True
    )
    return {
        "n": n,
        "dimacs": os.path.basename(dimacs_path),
        "nvars_declared": nvars_declared,
        "clauses_read": len(clauses),
        "maximal_lines_checked": len(lines),
        "negative_triple_clauses": len(neg_triples),
        "layer1_explicit_lines": len(explicit_lines),
        "layer1_triples_expected": triples_expected,
        "layer1_triples_present": triples_present,
        "layer1_lines_with_missing_triple": lines_with_missing,
        "layer1_missing_examples": missing_examples,
        "layer2_network_lines": len(network_lines),
        "layer2": sem,
        "layer2_vacuity_guard": (
            "layer 2 first requires the formula to be SATISFIABLE; if it is not, every triple "
            "would be vacuously refuted and the layer reports vacuous=true with complete=false. "
            "This closes a hole a reviewer demonstrated by adding an unrelated contradictory "
            "unit pair to an instance whose line constraints had been deleted."),
        "complete": complete,
        "covers_all_lines": complete,
        "completeness_scope": (
            "layer 1 requires ALL C(k,3) negative triples on every explicitly encoded line; "
            "layer 2 requires F AND T to be UNSAT for every 3-subset T of every network-encoded "
            "line. covers_all_lines is True only when both hold with nothing unchecked."
        ),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MATH-001 n=75 attack bench :: encoder")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--formulation", choices=["cells", "orbits"], default="cells")
    ap.add_argument("--group", default="iden", help="symmetry group for the orbit formulation")
    ap.add_argument("--lex-break", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stats", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    t_stats: dict = {"n": args.n, "formulation": args.formulation}
    if args.formulation == "cells":
        cnf = encode_cells(args.n, 2, lex_break=args.lex_break)
        t_stats["lex_break"] = args.lex_break
    else:
        feas = orbit_feasibility(args.n, SYMMETRY_GROUPS[args.group], 2 * args.n)
        t_stats["orbit_feasibility"] = feas
        if not feas["feasible"]:
            print(f"[parity] infeasible by orbit sizes: {feas['reason']}")
            t_stats["parity_infeasible"] = True
            if args.stats:
                with open(args.stats, "w", encoding="utf-8") as fh:
                    json.dump(t_stats, fh, indent=2, sort_keys=True)
            return 0
        cnf = encode_orbits(args.n, args.group, 2 * args.n)

    doc = cnf.dimacs()
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    t_stats.update(
        {
            "vars": cnf.nvars,
            "clauses": len(cnf.clauses),
            "dimacs_bytes": len(doc),
            "sha256": cnf.sha256(),
            "path": os.path.basename(args.out),
        }
    )
    print(json.dumps(t_stats, indent=2, sort_keys=True))
    if args.stats:
        with open(args.stats, "w", encoding="utf-8") as fh:
            json.dump(t_stats, fh, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
