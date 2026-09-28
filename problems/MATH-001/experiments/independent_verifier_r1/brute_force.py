#!/usr/bin/env python3
"""Exact D(n) ground truth for small n (DeepSeek r1).

Two independent exhaustive methods:

  A) FULL POWERSET enumeration of G(n) = {1..n}^2 for n = 1..4.
     Returns the true maximum legal subset size directly. This does NOT use the
     D(n) <= 2n row-pigeonhole argument at all, so it independently corroborates
     (or refutes) that bound on the small instances.

  B) ROW-PAIR exhaustive enumeration for n = 2..8 (configurable).
     Every legal S with |S| = 2n has exactly 2 points in each of the n rows
     (proof: rows are lines, so each holds <= 2 points; summing over n rows gives
     |S| <= 2n; equality forces exactly 2 per row). So enumerating all choices of
     one unordered column-pair per row enumerates every candidate for a 2n
     certificate. Combined with the row bound this decides "D(n) = 2n?" exactly:
       * >= 1 legal configuration found  =>  D(n) = 2n
       * 0 legal configurations found     =>  D(n) < 2n

The point of method B is to be exhaustive where the r1 self-certificates were
merely witnesses: a witness shows D(n) >= 2n, exhaustiveness shows how many there
are and lets us compare against the literature's enumeration counts.

Usage:
    python brute_force.py --powerset-max 4 --rowpair-max 8 --json out.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from itertools import combinations
from typing import Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ntil_verify import Point, check_pair_line_injective  # noqa: E402


def grid(n: int) -> list[Point]:
    return [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]


def is_legal(pts: Sequence[Point]) -> bool:
    return check_pair_line_injective(pts)[0]


# --------------------------------------------------------------------------- #
# A) full powerset
# --------------------------------------------------------------------------- #


def powerset_D(n: int) -> tuple[int, list[Point] | None, int]:
    """Return (D(n), a maximum legal set, number of legal sets of that size)."""
    cells = grid(n)
    N = len(cells)  # n^2
    masks_by_popcount: list[int] = sorted(range(1 << N), key=lambda m: -bin(m).count("1"))
    best: int | None = None
    witness: list[Point] | None = None
    count_at_best = 0
    for mask in masks_by_popcount:
        pc = bin(mask).count("1")
        if best is not None and pc < best:
            break
        pts = [cells[i] for i in range(N) if mask >> i & 1]
        if is_legal(pts):
            if best is None:
                best = pc
            if pc == best:
                count_at_best += 1
                if witness is None:
                    witness = pts
    return best if best is not None else 0, witness, count_at_best


# --------------------------------------------------------------------------- #
# B) row-pair exhaustive enumeration
# --------------------------------------------------------------------------- #


def rowpair_enumerate(n: int) -> dict:
    """Exhaustively enumerate all legal {2 points in each of n rows} configurations.

    Returns a dict with the number of legal configurations and a few witnesses.
    """
    pairs = list(combinations(range(1, n + 1), 2))
    legal = 0
    witnesses: list[list[Point]] = []
    t0 = time.time()
    nodes = 0

    # DFS with prefix pruning: a partial assignment that already contains a
    # collinear triple can never be extended to a legal configuration.
    chosen: list[tuple[int, int]] = []

    def rec(row: int) -> None:
        nonlocal legal, nodes
        if row == n:
            legal += 1
            if len(witnesses) < 5:
                witnesses.append([(c, r + 1) for r, pr in enumerate(chosen) for c in pr])
            return
        for pr in pairs:
            nodes += 1
            pts = [(c, r + 1) for r, p in enumerate(chosen) for c in p]
            pts += [(pr[0], row + 1), (pr[1], row + 1)]
            if not is_legal(pts):
                continue
            chosen.append(pr)
            rec(row + 1)
            chosen.pop()

    rec(0)
    return {
        "n": n,
        "candidate_space": len(pairs) ** n,
        "nodes_explored": nodes,
        "legal_configurations": legal,
        "D_is_2n": legal >= 1,
        "witnesses": witnesses,
        "seconds": round(time.time() - t0, 3),
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--powerset-max", type=int, default=4)
    ap.add_argument("--rowpair-max", type=int, default=8)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    out: dict = {"powerset": [], "rowpair": []}

    print("== A) full powerset enumeration (no use of the 2n row bound) ==")
    for n in range(1, args.powerset_max + 1):
        t0 = time.time()
        d, wit, cnt = powerset_D(n)
        rec = {
            "n": n,
            "D_n": d,
            "is_2n": d == 2 * n,
            "n_legal_max_sets": cnt,
            "witness": [list(p) for p in wit] if wit else None,
            "seconds": round(time.time() - t0, 3),
        }
        out["powerset"].append(rec)
        flag = "==" if d == 2 * n else "!="
        print(f"  n={n}: D(n)={d}  ({'2n' if d == 2*n else f'2n={2*n}'}) {flag}  legal-max-sets={cnt}  {rec['seconds']}s")

    print("== B) exhaustive row-pair enumeration (decides D(n)=2n exactly) ==")
    for n in range(1, args.rowpair_max + 1):
        if n == 1:
            # |S| = 2 > |G(1)| = 1, so no 2n certificate exists.
            rec = {"n": 1, "candidate_space": 0, "legal_configurations": 0, "D_is_2n": False, "witnesses": [], "seconds": 0.0}
            out["rowpair"].append(rec)
            print("  n=1: 0 legal configurations (grid has 1 cell < 2) -> D(1) != 2n")
            continue
        rec = rowpair_enumerate(n)
        out["rowpair"].append(rec)
        print(
            f"  n={n}: legal configs={rec['legal_configurations']} of {rec['candidate_space']} "
            f"-> D(n)=2n : {rec['D_is_2n']}   ({rec['seconds']}s, {rec['nodes_explored']} nodes)"
        )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
