#!/usr/bin/env python3
"""MATH-001 r2: reusable SAT bench for the no-three-in-line problem (2n target).

CNF encodings (DIMACS-ready clause lists):
  vars   x_{r,c} for cells 1..n x 1..n  (1-indexed; var id = (r-1)*n + c)
  rows/cols exactly-2:
     at-least-2 : for each cell, clause of ALL OTHER cells (rules out <=1)
     at-most-2  : (-a v -b v -c) per 3-subset            [triples mode]
                  or Sinz sequential counter, O(len)      [seq mode]
  every grid line with >=3 cells over ALL primitive directions (any slope):
     at-most-2 via the chosen mode.

Modes must AGREE on small n. Controls (pre-registered in round.json):
  n=2..5 -> SAT, model passes the round-1 exact integer verifier
  n=1    -> UNSAT (D(1)=1 < 2)
  pigeonhole: row 1 capped at 1 occupied cell => UNSAT for n>=2
n=75 is NOT solved here; --estimate prints exact variable/clause counts by
constructing all constraints in memory-free counters (no DIMACS emitted).
Solver: pysat (CaDiCaL) installed in-repo at n75_bench/.deps.
"""
from __future__ import annotations
import argparse
import json
import sys
from itertools import combinations
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / ".deps"))
sys.path.insert(0, str(HERE.parent / "baseline_r1"))

from pysat.solvers import Cadical153  # noqa: E402
import verifier  # noqa: E402


def var(r: int, c: int, n: int) -> int:
    return (r - 1) * n + c


def primitive_lines(n: int) -> list[list[tuple[int, int]]]:
    """All grid lines (as cell lists) containing >=3 cells, any slope."""
    lines = []
    seen_starts = set()
    for dy in range(0, n):
        for dx in range(-n + 1, n):
            if (dx, dy) == (0, 0) or gcd(abs(dx), abs(dy)) != 1:
                continue
            if (dx, dy) in seen_starts:
                continue  # canonical: skip mirrored duplicates below
            seen_starts.add((dx, dy))
            for r in range(1, n + 1):
                for c in range(1, n + 1):
                    if 1 <= r - dy <= n and 1 <= c - dx <= n:
                        continue  # not the line's first cell in this direction
                    cells = []
                    rr, cc = r, c
                    while 1 <= rr <= n and 1 <= cc <= n:
                        cells.append((rr, cc))
                        rr, cc = rr + dy, cc + dx
                    if len(cells) >= 3:
                        lines.append(cells)
    return lines


class CnfBuilder:
    def __init__(self, n: int, first_free: int):
        self.n = n
        self.clauses: list[list[int]] = []
        self.nvars = first_free - 1

    def newvar(self) -> int:
        self.nvars += 1
        return self.nvars

    def add(self, clause: list[int]) -> None:
        self.clauses.append(clause)

    def at_least_2(self, lits: list[int]) -> None:
        for i in range(len(lits)):
            self.add([lits[j] for j in range(len(lits)) if j != i])

    def at_most_2_triples(self, lits: list[int]) -> None:
        for a, b, c in combinations(lits, 3):
            self.add([-a, -b, -c])

    def at_most_2_sinz(self, lits: list[int]) -> None:
        """Sequential counter enforcing <=2 (Sinz 2005, k=2).

        ge1_i = ">=1 true among first i", ge2_i = ">=2 true among first i".
        Only forward (sound) clauses are emitted: over-approximating the ge
        vars is harmless, and the hard clause (-x_i v -ge2_{i-1}) kills any
        assignment with >=3 true. No exactness clauses, no final unit.
        """
        prev_ge1 = prev_ge2 = None
        for x in lits:
            ge1 = self.newvar()
            self.add([-x, ge1])
            if prev_ge1 is not None:
                self.add([-prev_ge1, ge1])
            if prev_ge1 is not None:
                ge2 = self.newvar()
                self.add([-x, -prev_ge1, ge2])
                if prev_ge2 is not None:
                    self.add([-prev_ge2, ge2])
                self.add([-x, -prev_ge2]) if prev_ge2 is not None else None
                prev_ge2 = ge2
            prev_ge1 = ge1


def build(n: int, mode: str, row1_cap: int = 2):
    b = CnfBuilder(n, n * n + 1)
    for r in range(1, n + 1):
        cap = row1_cap if r == 1 else 2
        row = [var(r, c, n) for c in range(1, n + 1)]
        # at-least-cap via all-but-(cap-1) clauses
        for combo in combinations(range(len(row)), cap - 1):
            b.add([row[i] for i in range(len(row)) if i not in combo])
        # at-most-cap
        if cap == 2:
            if mode == "triples":
                b.at_most_2_triples(row)
            else:
                b.at_most_2_sinz(row)
        else:
            for x in row:
                b.add([-x])
    for c in range(1, n + 1):
        col = [var(r, c, n) for r in range(1, n + 1)]
        for i in range(n):
            b.add([col[j] for j in range(n) if j != i])
        if mode == "triples":
            b.at_most_2_triples(col)
        else:
            b.at_most_2_sinz(col)
    for cells in primitive_lines(n):
        lits = [var(r, c, n) for r, c in cells]
        if mode == "triples":
            b.at_most_2_triples(lits)
        else:
            b.at_most_2_sinz(lits)
    return b.clauses, b.nvars


def solve(n: int, mode: str, row1_cap: int = 2):
    clauses, nvars = build(n, mode, row1_cap)
    with Cadical153(bootstrap_with=clauses) as s:
        sat = s.solve()
        model = s.get_model() if sat else None
    return sat, model, nvars, len(clauses)


def model_to_points(model: list[int], n: int) -> list[list[int]]:
    occ = {abs(v) for v in model if v > 0}
    return [[c, r] for r in range(1, n + 1) for c in range(1, n + 1)
            if var(r, c, n) in occ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--estimate", type=int, default=0)
    ap.add_argument("--mode", choices=["triples", "seq"], default="triples")
    args = ap.parse_args()
    if args.estimate:
        n = args.estimate
        lines = primitive_lines(n)
        incid = sum(len(l) for l in lines)
        trip = sum(len(l) * (len(l) - 1) * (len(l) - 2) // 6 for l in lines)
        print(json.dumps({"n": n, "lines_ge3": len(lines),
                          "cell_line_incidences": incid,
                          "triple_clauses_lines_only": trip,
                          "seq_aux_vars_lines_only": 2 * incid,
                          "vars_cells": n * n}, indent=2))
        return 0
    out = {"results": []}
    for n in (1, 2, 3, 4, 5):
        modes = ["triples", "seq"] if n in (3, 4) else [args.mode]
        for mode in modes:
            sat, model, nv, nc = solve(n, mode)
            entry = {"n": n, "mode": mode, "sat": sat, "vars": nv, "clauses": nc,
                     "verifier_ok": None}
            if sat:
                pts = model_to_points(model, n)
                errs = verifier.verify({"n": n, "target": 2 * n, "points": pts,
                                        "source": "cnf-" + mode})
                entry["verifier_ok"] = not errs
            out["results"].append(entry)
    for n in (3, 4):
        sat, _, _, _ = solve(n, "triples", row1_cap=1)
        out["results"].append({"n": n, "mode": "triples+pigeonhole", "sat": sat})
    by = {(r["n"], r["mode"]): r for r in out["results"]}
    checks = {
        "C1_small_n_sat_and_verified": all(
            by[(n, "triples")]["sat"] and by[(n, "triples")]["verifier_ok"]
            for n in (2, 3, 4, 5)),
        "C2_n1_unsat": by[(1, "triples")]["sat"] is False,
        "C3_pigeonhole_unsat": all(r["sat"] is False for r in out["results"]
                                   if "pigeonhole" in r["mode"]),
        "C4_modes_agree": all(by[(n, "triples")]["sat"] == by[(n, "seq")]["sat"]
                              for n in (3, 4)),
    }
    out["checks"] = checks
    out["verdict"] = "BENCH_SOUND" if all(checks.values()) else "BENCH_UNSOUND"
    dest = HERE.parent.parent / "results" / "r2"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "n75_bench_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "verdict": out["verdict"],
                      "results": [{k: r.get(k) for k in ("n", "mode", "sat",
                                                         "clauses", "verifier_ok")}
                                  for r in out["results"]]},
                     ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
