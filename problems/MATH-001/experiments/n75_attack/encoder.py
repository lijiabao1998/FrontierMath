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


def audit_cnf_covers_lines(n: int, dimacs_path: str, var_of_cell=None) -> dict:
    """Link (1) of certification: check the formula expresses the problem.

    Reads a DIMACS file produced by encode_cells (cell variables numbered in the
    documented order) and verifies that for EVERY maximal line with >= 3 grid
    points there is at least one clause of the form (¬a ∨ ¬b ∨ ¬c) with a,b,c the
    three cells of a collinear triple on that line. A missing line family is the
    single most likely silent encoder bug, and this check catches it directly.
    """
    order = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]
    var_of = {cell: i + 1 for i, cell in enumerate(order)}
    if var_of_cell is not None:
        var_of = var_of_cell

    neg_triples: set[tuple[int, int, int]] = set()
    with open(dimacs_path, "r", encoding="utf-8") as fh:
        for ln in fh:
            if not ln or ln[0] in "cp":
                continue
            lits = [int(t) for t in ln.split() if t != "0"]
            if len(lits) == 3 and all(v < 0 for v in lits):
                neg_triples.add(tuple(sorted(-v for v in lits)))

    missing: list[list[tuple[int, int]]] = []
    lines = maximal_lines(n, 3)
    for cells in lines:
        covered = False
        for sub in combinations(cells, 3):
            key = tuple(sorted(var_of[c] for c in sub))
            if key in neg_triples:
                covered = True
                break
        if not covered:
            missing.append(cells)
    return {
        "n": n,
        "dimacs": os.path.basename(dimacs_path),
        "maximal_lines_checked": len(lines),
        "lines_not_covered": len(missing),
        "first_missing_examples": missing[:5],
        "covers_all_lines": not missing,
        "negative_triple_clauses": len(neg_triples),
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
