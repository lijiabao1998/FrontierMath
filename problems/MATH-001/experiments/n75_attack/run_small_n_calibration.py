#!/usr/bin/env python3
"""n=75 attack bench -- small-n calibration against exhaustive ground truth.

For each n this round already decided D(n) = 2n by EXHAUSTIVE enumeration (see
../independent_verifier_r1/brute_force.py: every set with exactly 2 points in
each of the n rows is enumerated, which is exhaustive for 2n-certificates because
the row bound forces exactly 2 per row). Here the same ground truth is used to
calibrate the two SAT formulations:

  1. cell-based formulation  : SAT <=> D(n) = 2n                     (n = 2..7)
  2. orbit-based formulation : SAT <=> some 2n-certificate is invariant
                               under the named group                  (n = 2..7)
  3. UNSAT controls          : instances that must be UNSAT for reasons that are
                               independently provable, so an UNSAT is checkable
                               rather than merely believed.

Every SAT model is decoded back into a point set and re-verified for
no-three-in-line by this round's own checker, and its symmetry group is measured.
A model that decodes to an invalid set, or that lacks the symmetry the instance
imposed, is a hard failure of this calibration.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from itertools import combinations
from typing import Callable, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "independent_verifier_r1")))

from encoder import (  # noqa: E402
    SYMMETRY_GROUPS,
    encode_cells,
    encode_orbits,
    maximal_lines,
    orbit_feasibility,
    orbits,
    sym_maps,
)
from ntil_verify import verify  # noqa: E402


# --------------------------------------------------------------------------- #
# exhaustive ground truth
# --------------------------------------------------------------------------- #


def enumerate_legal_2n(n: int, on_solution: Callable[[list[tuple[int, int]]], None]) -> int:
    """Enumerate EVERY legal set with exactly 2 points in each row.

    Exhaustive for 2n-certificates: the row bound forces exactly 2 per row.
    """
    if n < 2:
        return 0
    pairs = list(combinations(range(1, n + 1), 2))
    chosen: list[tuple[int, int]] = []
    count = 0

    def rec(row: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            on_solution([(c, r + 1) for r, p in enumerate(chosen) for c in p])
            return
        for pr in pairs:
            pts = [(c, r + 1) for r, p in enumerate(chosen) for c in p]
            pts += [(pr[0], row + 1), (pr[1], row + 1)]
            ok = True
            seen = set()
            for i, p in enumerate(pts):
                for q in pts[i + 1:]:
                    a, b = p
                    c2, d2 = q
                    aa = d2 - b
                    bb = a - c2
                    cc = c2 * b - a * d2
                    from math import gcd as _gcd

                    g = _gcd(_gcd(abs(aa), abs(bb)), abs(cc))
                    if g > 1:
                        aa //= g
                        bb //= g
                        cc //= g
                    if aa < 0 or (aa == 0 and bb < 0):
                        aa, bb, cc = -aa, -bb, -cc
                    k = (aa, bb, cc)
                    if k in seen:
                        ok = False
                        break
                    seen.add(k)
                if not ok:
                    break
            if not ok:
                continue
            chosen.append(pr)
            rec(row + 1)
            chosen.pop()

    rec(0)
    return count


def invariance_counts(n: int, pts_list: list[list[tuple[int, int]]]) -> dict:
    maps = sym_maps(n)
    out = {}
    for gname, gens in SYMMETRY_GROUPS.items():
        cnt = 0
        for S in pts_list:
            Sset = set(S)
            if all(maps[g](*cell) in Sset for g in gens for cell in S):
                cnt += 1
        out[gname] = cnt
    return out


# --------------------------------------------------------------------------- #
# SAT helpers
# --------------------------------------------------------------------------- #


def solve_cnf(cnf, timeout_s: int | None = None) -> dict:
    from pysat.solvers import Cadical153
    from pysat.card import CardEnc  # noqa: F401  (not used; kept for parity with notes)

    t0 = time.time()
    with Cadical153(bootstrap_with=cnf.clauses) as s:
        sat = s.solve()
        model = s.get_model() if sat else None
    return {
        "status": "SAT" if sat else "UNSAT",
        "seconds": round(time.time() - t0, 3),
        "model": model,
        "solver": "cadical153 (via python-sat)",
    }


def decode_cell_model(cnf, model, n: int) -> list[tuple[int, int]]:
    pos = {v for v in model if v > 0}
    order = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]
    return [cell for i, cell in enumerate(order) if (i + 1) in pos]


def decode_orbit_model(cnf, model, n: int, group: str) -> tuple[list[tuple[int, int]], dict]:
    pos = {v for v in model if v > 0}
    orbs = orbits(n, SYMMETRY_GROUPS[group])
    pts: list[tuple[int, int]] = []
    chosen = []
    for idx, o in enumerate(orbs):
        if cnf.var_of[("y", idx)] in pos:
            chosen.append(idx)
            pts.extend(o)
    return pts, {"selected_orbits": len(chosen), "of_orbits": len(orbs)}


def symmetry_agrees(n: int, pts: list[tuple[int, int]], group: str) -> bool:
    maps = sym_maps(n)
    Sset = set(pts)
    return all(maps[g](*cell) in Sset for g in SYMMETRY_GROUPS[group] for cell in pts)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-max", type=int, default=7)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(list(argv) if argv is not None else None)

    results: dict = {"ground_truth": {}, "cell_formulation": [], "orbit_formulation": [],
                     "unsat_controls": [], "failures": []}
    fails: list[str] = results["failures"]

    # ---- ground truth ----
    print("== exhaustive ground truth: all legal sets with 2 points per row ==")
    gt: dict[int, dict] = {}
    for n in range(2, args.n_max + 1):
        sols: list[list[tuple[int, int]]] = []
        t0 = time.time()
        total = enumerate_legal_2n(n, sols.append)
        inv = invariance_counts(n, sols)
        gt[n] = {"n_legal_2n_sets": total, "invariance_counts": inv, "seconds": round(time.time() - t0, 2)}
        results["ground_truth"][str(n)] = gt[n]
        print(f"  n={n}: {total} legal 2n-sets   invariant-under: {inv}   ({gt[n]['seconds']}s)")

    # ---- cell formulation ----
    print("== formulation A: cell-based CNF, exactly 2 per row, at most 2 per line ==")
    for n in range(2, args.n_max + 1):
        cnf = encode_cells(n, 2)
        r = solve_cnf(cnf)
        expect_sat = gt[n]["n_legal_2n_sets"] > 0
        rec = {"n": n, "vars": cnf.nvars, "clauses": len(cnf.clauses), "status": r["status"],
               "seconds": r["seconds"], "expect_sat": expect_sat, "sha256": cnf.sha256()[:16]}
        if r["status"] == "SAT":
            pts = decode_cell_model(cnf, r["model"], n)
            rep = verify(pts, n, expect_count=2 * n)
            rec["decoded_points"] = len(pts)
            rec["certificate_valid"] = rep["ok"]
            if not rep["ok"]:
                fails.append(f"cell n={n}: SAT model is not a valid 2n certificate: {rep['violations'][:2]}")
        if (r["status"] == "SAT") != expect_sat:
            fails.append(f"cell n={n}: solver {r['status']} but exhaustive ground truth says sat={expect_sat}")
        results["cell_formulation"].append(rec)
        print(f"  n={n}: {r['status']} (expected {'SAT' if expect_sat else 'UNSAT'}) "
              f"vars={cnf.nvars} clauses={len(cnf.clauses)} {r['seconds']}s")

    # ---- orbit formulation ----
    print("== formulation B: orbit-based CNF per symmetry group ==")
    for n in range(2, args.n_max + 1):
        for g in SYMMETRY_GROUPS:
            feas = orbit_feasibility(n, SYMMETRY_GROUPS[g], 2 * n)
            expect_sat = gt[n]["invariance_counts"][g] > 0
            rec = {"n": n, "group": g, "orbit_feasible": feas["feasible"],
                   "orbit_size_multiset": feas["orbit_size_multiset"], "expect_sat": expect_sat,
                   "exhaustive_invariant_count": gt[n]["invariance_counts"][g]}
            if not feas["feasible"]:
                rec["status"] = "UNSAT_BY_ORBIT_PARITY"
                rec["reason"] = feas["reason"]
                if expect_sat:
                    fails.append(f"orbit n={n} {g}: parity says infeasible but exhaustive found "
                                 f"{gt[n]['invariance_counts'][g]} invariant sets")
            else:
                cnf = encode_orbits(n, g, 2 * n)
                r = solve_cnf(cnf)
                rec.update({"vars": cnf.nvars, "clauses": len(cnf.clauses),
                            "status": r["status"], "seconds": r["seconds"],
                            "sha256": cnf.sha256()[:16]})
                if r["status"] == "SAT":
                    pts, meta = decode_orbit_model(cnf, r["model"], n, g)
                    rep = verify(pts, n, expect_count=2 * n)
                    rec["decoded_points"] = len(pts)
                    rec["certificate_valid"] = rep["ok"]
                    rec["has_declared_symmetry"] = symmetry_agrees(n, pts, g)
                    rec.update(meta)
                    if not rep["ok"]:
                        fails.append(f"orbit n={n} {g}: SAT model is not a valid certificate")
                    if not rec["has_declared_symmetry"]:
                        fails.append(f"orbit n={n} {g}: SAT model lacks the imposed symmetry")
                if (r["status"] == "SAT") != expect_sat:
                    fails.append(f"orbit n={n} {g}: solver {r['status']} but exhaustive says sat={expect_sat}")
            results["orbit_formulation"].append(rec)
        line = [r for r in results["orbit_formulation"] if r["n"] == n]
        print(f"  n={n}: " + "  ".join(f"{r['group']}={r['status']}" for r in line))

    # ---- UNSAT controls ----
    print("== UNSAT controls (each must be UNSAT for an independently provable reason) ==")
    # C1: ask for 2n points but forbid the third point of any row (at most 1 per row).
    #     Rows are lines, so at most 1 per row bounds |S| <= n < 2n. Provable.
    for n in (3, 4, 5):
        cnf = encode_cells(n, 1)  # exactly 1 per row -> |S| = n < 2n
        r = solve_cnf(cnf)
        # now assert there are 2n points: add 2n unit clauses on distinct cells
        c2 = encode_cells(n, 1)
        order = [(x, y) for y in range(1, n + 1) for x in range(1, n + 1)]
        for cell in order[: 2 * n]:
            c2.add_clause([c2.var_of[("x", *cell)]])
        r2 = solve_cnf(c2)
        rec = {"control": f"C1_at_most_1_per_row_n{n}", "status": r["status"],
               "status_with_2n_forced": r2["status"], "seconds": r["seconds"],
               "provable_reason": "each row is a line, so |S| <= n < 2n"}
        results["unsat_controls"].append(rec)
        print(f"  {rec['control']}: {r['status']} (with 2n forced: {r2['status']})")
        if r2["status"] != "UNSAT":
            fails.append(f"{rec['control']}: expected UNSAT with 2n points forced")
    # C2: rot4 orbit parity at odd n -- no solver needed, decided by counting.
    for n in (3, 5, 7):
        feas = orbit_feasibility(n, SYMMETRY_GROUPS["rot4"], 2 * n)
        rec = {"control": f"C2_rot4_parity_n{n}", "orbit_size_multiset": feas["orbit_size_multiset"],
               "feasible": feas["feasible"], "reason": feas["reason"],
               "provable_reason": "orbit sizes {1,4} allow only sizes 0 or 1 mod 4; 2n = 2 mod 4 for odd n"}
        results["unsat_controls"].append(rec)
        print(f"  {rec['control']}: feasible={feas['feasible']} -- {feas['reason']}")
        if feas["feasible"]:
            fails.append(f"{rec['control']}: expected parity infeasibility at n={n}")

    results["calibration_ok"] = not fails
    print(json.dumps({"calibration_ok": results["calibration_ok"], "failures": fails,
                      "n_checks": len(results["cell_formulation"]) + len(results["orbit_formulation"])
                      + len(results["unsat_controls"])}, indent=2))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, sort_keys=True)
        print(f"[written] {args.json}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
